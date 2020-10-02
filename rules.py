# -*- coding: utf-8 -*-
"""Contains the rules that are used to modify the dialect words to create alternatives"""

import json
from django.core.files.storage import FileSystemStorage

fs = FileSystemStorage()

# Loads the list of known "dictionary" versions of the words
with open(fs.path('vocabulary.json'), 'r') as jf:
    VOCABULARY = json.load(jf)

# Contains the subword strings and their possible alternative versions
# Currently consists of 3 categories: 3 and more letters, 2 letters, 1 letters
# Each key value is replaced with the given alternative versions in the lists
# WARNING!: The set of modifiers are currently optimizied to work on Saxonian dialects
MODIFIERS = [
    {
        'tien': ['tje'],
        'fien': ['fje'],
        'dôn': ['doen'],
        'dôk': ['doek'],
        'êln': ['elen'],
        'eln': ['elen'],
        'êrn': ['eren'],
        'ern': ['eren'],
        'nie': ['nieuw'],
        'nij': ['nieuw'],
        'oet': ['uit'],
        'erg': ['erig'],
        'iee': ['ie', 'ij']
    },
    {
        'üü': ['uu', 'eu', 'ui', 'oo', 'oe', 'ie', 'u', 'o'],
        'ůů': ['uu', 'ui', 'oe', 'eu'],
        'uu': ['ui', 'eu', 'oe', 'u'],
        'öö': ['oe', 'aa', 'ee', 'eu', 'oo', 'u', 'o'],
        'òl': ['ol', 'ou'],
        'ôê': ['oe', 'uu', 'ui', 'oo'],
        'óó': ['o'],
        'ån': ['aan'],
        'îê': ['ij', 'ie', 'ee'],
        'ïe': ['ij'],
        'iè': ['ee', 'ie', 'e', 'i'],
        'ie': ['ij', 'ee', 'e', 'i'],
        'èe': ['aa', 'ee', 'oo', 'ei', 'e', 'a'],
        'eè': ['aa', 'ee', 'oo', 'ei', 'e', 'a'],
        'èu': ['eu', 'aa', 'oo', 'oe', 'o'],
        'oa': ['aa', 'oo', 'a', 'o'],
        'oe': ['ui'],
        'eu': ['oo', 'oe', 'ui', 'a', 'o'],
        'ij': ['ee', 'ie', 'ei'],
    },
    {
        'ﬂ': ['fl'],
        'ﬁ': ['fi'],
        'à': ['a', 'e'],
        'á': ['a', 'e'],
        'â': ['a', 'e'],
        'ä': ['ee', 'a', 'e', 'o', 'u', 'ë'],
        'å': ['aa', 'a', 'e'],
        'é': ['ee', 'a', 'e', 'i'],
        'ê': ['e', 'a', 'i'],
        'ë': ['e', 'i'],
        'ē': ['a'],
        'è': ['ee', 'e', 'a'],
        'ì': ['i'],
        'í': ['i', 'a'],
        'î': ['ie', 'ij', 'i', 'a'],
        'ï': ['i'],
        'ȋ': ['i'],
        'ñ': ['n'],
        'ò': ['oe', 'oo', 'ou', 'eu', 'o', 'a', 'u'],
        'ó': ['oo', 'o', 'u'],
        'ô': ['oe', 'o', 'e', 'a'],
        'ö': ['oeu', 'oe', 'eu', 'ee', 'aa', 'a', 'e', 'i', 'o', 'u'],
        'ō': ['oe', 'a', 'e', 'o', 'u'],
        'ǒ': ['o'],
        'ȫ': ['o'],
        'ù': ['u', 'e'],
        'ú': ['ui', 'ie', 'u'],
        'û': ['oe', 'eu', 'ui', 'uu', 'u', 'e', 'o'],
        'ü': ['ui', 'oe', 'eu', 'u', 'o', 'i', 'e'],
        'ů': ['ui', 'o', 'u'],
    }
]
