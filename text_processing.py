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
    """Recursively creates alternatives to the dialect word by manipulating it based on the rules
    until it creates a dictionary version or exhausts the options.

    Parameters
    ----------
    dialect_word : string
        Give the dialect word that needs to be modified

    combinations : list of dictionaries
        Contains the candidate results. The variable modified during the recursion.

    vocabulary : list of dictionaries
        List of known "dictionary" versions of the words.
        The vocabulary should contain both 'modified' and the original 'trefwoord'
        versions under the keys named the same. The 'modified' versions should
        be created with :func:`clean_str_word()` function.

    modifiers : list of dictionaries
        The rule set that contains which modifications should be performed.
        Example can be found in rules.py file.

    step : integer, (default=0)
        The parameter set for the recursion. Inicates which of the sections in the
        rule set is up next for the processing

    min_distance : integer, (default=None)
        The parameter set for the recursion. Contains the minimum found edit distance
        from the comparisons to the vocabulary.

    Returns
    -------
    combinations : list of dictionaries
        Contains the closest detected dictionary versions after the modifications.
    """
    input_ = {'dialect': dialect_word}
    # Find the closest dictionary keyword to the given dialect word
    input_['estimates'], input_['distance'] = get_closest(input_['dialect'], vocabulary)
    # The comparison of the given dialect to the vocabualry is already a result;
    combinations.append(input_)

    # If the minimum distance is not given, take the minimum distance of the given dialect word
    if not min_distance:
        min_distance = input_['distance']

    for comb in combinations:

        dialect = comb['dialect']
        curr_dist = comb['distance']

        if curr_dist > min_distance:
            continue

        # Modifiers have different sections.
        # `step` variable here decides which set's turn it is currently.
        # `fr` variable here is the string candidate to be modified
        # `to_list` contains strings that the candidate will be modified into
        for fr, to_list in modifiers[step].items():

            # If the candidate string exists in the dialect word
            if fr in dialect:

                for to in to_list:

                    # Modify the dialect to create the alternative
                    alternated_word = re.sub(fr, to, dialect).strip()
                    # Find the closest dictionary keyword to the alternated version
                    estimates, alt_dist = get_closest(alternated_word, vocabulary)

                    # If the minimum possible distance of the alternated is smaller than
                    # the minimum calculated distance of the given dialect word
                    if alt_dist < curr_dist:

                        # Add the new alternated word to the list of combinations.
                        # Append adds the value to the end of the list.
                        # This newly added item will also be alternated
                        # in next steps in the same loop.
                        combinations.append({
                            'dialect': alternated_word,
                            'estimates': estimates,
                            'distance': alt_dist
                        })

                        # Check if the newly calculated distance is the minimum so far.
                        # If so, update the global minimum distance
                        if alt_dist < min_distance:
                            min_distance = alt_dist

    # Only leave the combinations with minimum distance calculated so far
    combinations = [c for c in combinations if c['distance'] == min_distance]
    # Duplicate elimination is needed since modifications may create the same alternatives
    combinations = list({c['dialect']: c for c in combinations}.values())
    # Sorted based on the distance
    combinations = sorted(combinations, key=lambda k: k['distance'])

    # If any of the alternatives reached to a dictionary version (min_distance==0),
    # stop the recursion and return. Otherwise, call the function one more time.
    # WARNING: Althouth ending the function here speeds up the processing,
    #          the downside is we cannot control whether it is the correct result.
    if min_distance > 0:
        step += 1
        # If the sections of the modifiers is not yet exhausted;
        if step < len(modifiers):
            # Call the function itself again to proceed to the next step
            combinations = alternate_dialect(dialect_word, combinations,
                                             vocabulary, modifiers,
                                             step, min_distance)

    return combinations

def process_single_word(dialect_word, max_return=1, **kwargs):
    """Apply the rule-based prediction algorithm on a single word at once

    Parameters
    ----------
    dialect_word : string
        Give the dialect word that needs to be processed

    max_return : integer, (default=1)
        Limits the number of predictions made by the algorithm.

    **kwargs
        Given to the :func:`alternate_dialect()` function.

    Returns
    -------
    keywords : list of dictionaries
        The predictions done by the algorithm.
    """
    estimates = []
    keywords = []

    # Obtain the predictions done by alternating the dialect word.
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
    """Runs the Phonetisaurus model and returns its predictions on a given list of dialect words

    Parameters
    ----------
    dialect_words_list : list of strings
        Give the list contains the dialect words that needs to be processed

    model_path : string, (default='./models/phonetisaurus-model.fst')
        The path of the desired Phonetisaurus model file.

    Returns
    -------
    phonetisaurus_keyword_list : list of strings
        The list of predictions done by the Phonetisaurus model.
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

def process_file(file_name, email_address=''):
    """A wrapper function that reads data from file, runs the algorithms, writes
    the results to a file, and sends a notification email to the given email address

    Parameters
    ----------
    file_name : string
        The path to the file taht should be processed. The function uses Django's
        :class:`FileSystemStorage()` to read the file.

    email_address : string, (default='')
        The email address that should be notified when the processing is completed.
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
         'https://dialect2keyword.cls.ru.nl/words/' + file_name + '_processed/ \n\n'
         'Kind regards,\n\nSite admin\nCentre for Language and Speech Technologies\n'
         'Radboud University Nijmegen\n\nEmail: h.vandenheuvel@let.ru.nl'),
        'relevancerr@gmail.com',
        [email_address],
        fail_silently=False,
    )
