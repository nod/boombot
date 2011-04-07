###
# Copyright (c) 2011, Nathan Witmer
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import os, sys, string, random

class MadlibGenerator:
    def __init__(self):
        self.words = self.loadWords()

    def loadWords(self):
        """
        loads from the lemmatized file from
        http://www.kilgarriff.co.uk/bnc-readme.html

            conj (conjunction)            34 items
            adv  (adverb)                427
            v    (verb)                 1281
            det  (determiner)             47
            pron (pronoun)                46
            interjection                  13
            a    (adjective)            1124
            n    (noun)                 3262
            prep (preposition)            71
            modal                         12
            infinitive-marker              1

        plus additional word classes:

            letter
            digit
            color
            month
            swear
        """
        words = {};
        posKeys = {
                'conj': 'conjunction',
                'adv': 'adverb',
                'v': 'verb',
                'det': 'determiner',
                'pron': 'pronoun',
                'interjection': 'interjection',
                'a': 'adjective',
                'n': 'noun',
                'prep': 'preposition',
                'modal': 'modal',
                'infinitive-marker': 'infinitive-marker'
            }
        for line in self.linesFromFile('lemma.al'):
            parts = line.split(' ')
            key = posKeys[parts[-1]]
            if not key in words:
                words[key] = [];
            words[key].append(parts[-2])

        words['letter'] = list(string.lowercase)
        words['digit'] = [str(i) for i in range(0,10)]
        words['color'] = [color for color in self.linesFromFile('colors.txt')]
        words['month'] = ['January', 'February', 'March',
                'April', 'May', 'June', 'July', 'August', 'September',
                'October', 'November', 'December']
        words['swear'] = ['shit', 'piss', 'fuck', 'cunt', 'cocksucker',
                'motherfucker', 'tits']
        words['number'] = self.number

        return words

    def madlib(self, text):
        """substitutes a given madlib string for randomly chosen words"""

        for pos in iter(self.words):
            text = self.replacePartOfSpeech(pos, text)

        return text

    def replacePartOfSpeech(self, pos, text):
        for transform in [string.lower, string.capitalize, string.upper]:
            search = '$' + transform(pos)
            while text.count(search):
                if hasattr(self.words[pos], '__call__'):
                    replace = self.words[pos]()
                else:
                    replace = random.choice(self.words[pos])
                replace = transform(replace)
                text = text.replace( search, replace, 1 )
        return text

    def number(self):
        """generates a random, reasonably sized number"""
        s = '' + str(random.randint(1,9))
        while random.random() < 0.4:
            s += str(random.randint(0,9))
        return s

    def linesFromFile(self, fileName):
        with open(os.path.join(os.path.dirname(__file__), fileName)) as f:
            for line in f:
                yield line.strip()

class Madlib(callbacks.Plugin):
    def __init__(self, irc):
        self.__parent = super(Madlib, self)
        self.__parent.__init__(irc)
        self.generator = MadlibGenerator()

    def madlib(self, irc, msg, args, text):
        """generates a madlib sentence

        e.g. "@madlib suddenly, a $noun appeared! $SWEAR!"

        Parts of speech:
            $conjunction $adverb $verb
            $determiner $pronoun $interjection $adjective $noun
            $preposition $modal $infinitive-marker
            $letter $digit $color $month $number $swear
        """
        irc.reply(self.generator.madlib(text))
    madlib = wrap(madlib, ['text'])

Class = Madlib


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
