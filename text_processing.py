# -*- coding: utf-8 -*-

import re
import os
import Levenshtein as lev
from subprocess import Popen, PIPE

from django.core.files import File
from django.core.mail import send_mail
from django.core.files.storage import FileSystemStorage
from django.conf import settings

from rules import MODIFIERS, VOCABULARY

def clean_str_word(word, split=False, hard=True):
    """Cleans a given word to prepare it for the further calculations

    Parameters
    ----------
    word : string
        Give the word that needs to be modified

    split : bool, (default=False)
        When given True, disregards the alternative word given as secondary.
        For instance, in "laau - flaau", "flaau" is removed.

    hard : bool, (default=True)
        When given True, removes all occurrances of -, -, –, ., and empty space

    Returns
    -------
    word : string
        Returns the modified versio of the word
    """
    # Clean from chars that makes compound letters
    for comp_chr in ['\u0300', '\u0302', '\u0303', '\u0304', '\u0306', '\u0308', '\u030c']:
        word = word.replace(comp_chr, '')

    # Clean html tags (<u>, <i>, <b>)
    word = re.sub(r'<.*?>', '', word).strip()

    # Clean some of chars if they start with
    word = re.sub(r'^[’|`|\'|ʼ]*[t|n|s]\s', '', word).strip()

    # Clean some of chars if they end with
    word = re.sub(r',\s[’|`|\'|ʼ][t|n|s]$', '', word).strip()

    # Clean em/zich at the end
    word = re.sub(r'em/zich$', '', word).strip()

    # Remove - and - in paranthesis, at the beginning or at the end
    word = re.sub(r'^[-|‑]|\([-|‑]\)|[-|‑]$', '', word).strip()

    # Clean some chars
    word = re.sub(r'\*|!|\?|,|`|’|‘|\'|ʼ|/|\(|\)|[0-9]', '', word).strip()

    if split and ' - ' in word:
        # Split dialectopgave and choose the first one, if two alternatives given
        word = word.split(' - ')[0].strip()

    if hard:
        # Remove -, -, –, ., and \s
        word = re.sub(r'-|‑|–|\.|\s', '', word).strip()

    return word

def get_closest(dialect_word, vocabulary, distance_limit=1):
    """Calculates and returns the most similar keyword from the vocabulary
       for a given dialect word

    Parameters
    ----------
    dialect_word : string
        Give the dialect word that needs to be checked agains the vocabulary

    vocabulary : list of dictionaries
        Give the list of known "dictionary" versions of the words.
        The vocabulary should contain both 'modified' and the original 'trefwoord'
        versions under the keys named the same. The 'modified' versions should
        be created with :func:`clean_str_word()` function.

    distance_limit : integer, (default=1)
        When given, limits the number of keyword predictions should be returned
        to the given number.

    Returns
    -------
    vocab_ : list of dictionaries
        Returns the list of closest keywords in the vocabulary

    min_distance : integer
        The minimum distance calculated when dialect word is compared to the vocabulary
    """
    # Following line is proven faster than running the usual deepcopy() function
    # If this is not done, the added values are kept in the memory
    vocab_ = [{'modified': w['modified'],
               'trefwoord': w['trefwoord']}
              for w in vocabulary]

    # Calculate the Levenshtein distance
    # between the modified version of the given dialect word
    # and for each the modified version of the keywords in the vocabulary
    for item in vocab_:
        item['distance'] = lev.distance(dialect_word, item['modified'])

    if distance_limit:
        # Keep only the highest scoring 'distance_limit' number of keywords
        limit_to = sorted(list({c['distance'] for c in vocab_}))[:distance_limit]
        vocab_ = [x for x in vocab_ if x['distance'] in limit_to]

    vocab_ = list({c['trefwoord']: c for c in vocab_}.values())
    vocab_ = sorted(vocab_, key=lambda k: k['distance'])

    return vocab_, min({c['distance'] for c in vocab_})

def alternate_dialect(dialect_word, combinations, vocabulary, modifiers, step=0, min_distance=None):

    input_ = {'dialect': dialect_word}
    input_['estimates'], input_['distance'] = get_closest(input_['dialect'], vocabulary)
    combinations.append(input_)

    if not min_distance:
        min_distance = input_['distance']

    for comb in combinations:

        dialect = comb['dialect']
        curr_dist = comb['distance']

        if curr_dist > min_distance:
            continue

        for fr, to_list in modifiers[step].items():

            if fr in dialect:

                for to in to_list:

                    alternated_word = re.sub(fr, to, dialect).strip()
                    estimates, alt_dist = get_closest(alternated_word, vocabulary)

                    if alt_dist < curr_dist:

                        # Add the new alternated word to the list of combinations.
                        # Append adds the value to the end of the list.
                        # This newly added item will also be alternated
                        # in next steps the same loop.
                        combinations.append({
                            'dialect': alternated_word,
                            'estimates': estimates,
                            'distance': alt_dist
                        })

                        if alt_dist < min_distance:
                            min_distance = alt_dist

    combinations = [c for c in combinations if c['distance'] == min_distance]
    combinations = list({c['dialect']: c for c in combinations}.values())
    combinations = sorted(combinations, key=lambda k: k['distance'])

    if min_distance > 0:
        step += 1
        if step < len(modifiers):
            combinations = alternate_dialect(dialect_word, combinations,
                                             vocabulary, modifiers,
                                             step, min_distance)

    return combinations

def process_single_word(dialect_word, max_return=1, **kwargs):
    """Apply the rule-based prediction algorithm on a single word at once

    Parameters
    <..>
    """
    estimates = []
    keywords = []

    # Run the prediction algorithm
    combs = alternate_dialect(dialect_word, [], **kwargs)

    if combs:
        if 'estimates' in combs[0]:
            estimates = combs[0]['estimates']

    if estimates:
        for e in estimates[:max_return]:
            estimate = {'trefwoord': e['trefwoord']}
            # If the edit distance is larger than 5, it is a long shot
            # Thus the score should be zero
            if e['distance'] > 5:
                estimate['score'] = 0
            else:
                # If edit distance smaller than 5,
                # the score is inversly proportioned
                estimate['score'] = 5 - e['distance']
            keywords.append(estimate)

    return keywords

def apply_phonetisaurus(dialect_words_list, model_path='./models/phonetisaurus-model.fst'):
    """
    """
    # Currently phonetisaurus in our system is a script that accepts files as input
    # Hence, we write our input into a temporary file first
    tmp_path = os.path.join(settings.BASE_DIR, 'tmp.txt')
    with open(tmp_path, 'w') as tm:
        for dwc in dialect_words_list:
            tm.write(dwc + '\n')

    # Phonetisaurus script called in a subprocess
    popen_job = Popen(['phonetisaurus-apply',
                       '--model', model_path,
                       '--word_list', tmp_path,
                       '-n', '1'],
                      stdout=PIPE,
                      cwd=settings.BASE_DIR)
    popen_job.wait()

    # Temporary file is removed after usage
    os.remove(tmp_path)

    # Read the output from the subprocess
    popen_output = str(popen_job.stdout.read(), 'utf-8')

    # The output is similar to a tab-separated file,
    # so we first split the lines and align input-output words in a set
    phonetisaurus_result_dict = {line.split('\t')[0]: line.split('\t')[1]
                                 for line in popen_output.split('\n')
                                 if len(line) > 0 and '\t' in line}

    # Phonetisaurus does not return anything for the words it could not process.
    # To be able to align the results with the original list,
    # we loop over the original list and fill the blanks with a placeholder
    phonetisaurus_keyword_list = [phonetisaurus_result_dict[dwc]
                                  if dwc in phonetisaurus_result_dict.keys() else '-'
                                  for dwc in dialect_words_list]

    return phonetisaurus_keyword_list

def process_file(file_name, email_address):
    """
    """
    fs = FileSystemStorage()

    # Read the uploaded file from the file system
    # and load the dialect keywords into a list
    with open(fs.path(file_name + '.txt'), 'r') as f:
        dialect_words_list = sorted(list({line.strip() for line in f.readlines()}))

    # Apply the preprocessing. Currently needed both for rule-based and phonetisaurus systems
    dialect_words_list_clean = [clean_str_word(dw, split=True, hard=True)
                                for dw in dialect_words_list]

    # Give the list of preprocessed strings to the phonetisaurus algorithm
    phonetisaurus_keyword_list = apply_phonetisaurus(dialect_words_list_clean)

    # Prepare the string to be written to the file
    to_write = 'Dialect Word\tFirst Estimate\tSecond Estimate\n'
    for dialect_word, dialect_word_clean, phonetisaurus_keyword in zip(dialect_words_list,
                                                                       dialect_words_list_clean,
                                                                       phonetisaurus_keyword_list):
        # Rule-based system is currently designed to process a single keyword at once
        # Hence it is callsed here inside the loop (unlike apply_phonetisaurus())
        rulebased_keywords = process_single_word(dialect_word_clean, vocabulary=VOCABULARY, modifiers=MODIFIERS)
        to_write += dialect_word + '\t'
        to_write += rulebased_keywords[0]['trefwoord'] + ' (' + str(rulebased_keywords[0]['score']) + ')' + '\t' if len(rulebased_keywords) > 0 else '-\t'
        to_write += phonetisaurus_keyword + ' (3)' + '\t' if phonetisaurus_keyword != '-' else '- (-)\t'
        to_write += '\n'

    # Write the string to the file
    with open('media/' + file_name + '_processed.tsv', 'w') as fn:
        myfile = File(fn)
        myfile.write(to_write)

    send_mail(
        'Text processing is done. Dialect words are converted.',
        ('Dear user,\n\n'
         'We have completed processing your data. '
         'Please visit the following link to check it on or website.\n'
         'http://localhost:8000/words/' + file_name + '_processed/ \n\n'
         'Kind regards,\n\nSite admin\nCentre for Language and Speech Technologies\n'
         'Radboud University Nijmegen\n\nEmail: h.vandenheuvel@let.ru.nl'),
        'relevancerr@gmail.com',
        [email_address],
        fail_silently=False,
    )
