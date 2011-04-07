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

from supybot.test import *
import re

madlib = plugin.loadPluginModule('Madlib')

class MadlibGeneratorLoadingTestCase(SupyTestCase):
    def setUp(self):
        SupyTestCase.setUp(self)
        self.words = madlib.plugin.MadlibGenerator().loadWords()

    def testNounsLoaded(self):
        self.assertEqual(len(self.words['noun']), 3262)

    def testColorsLoaded(self):
        self.assertEqual(len(self.words['color']), 259)

    def testDigitsLoaded(self):
        self.assertEqual(len(self.words['digit']), 10)

    def testLettersLoaded(self):
        self.assertEqual(len(self.words['letter']), 26)

    def testMonthsLoaded(self):
        self.assertEqual(len(self.words['month']), 12)

    def testSwearsLoaded(self):
        self.assertEqual(len(self.words['swear']), 7)

    def testNumberIsFunction(self):
        self.assertTrue(hasattr(self.words['number'], '__call__'))

class MadlibGeneratorNumberGeneratorTestCase(SupyTestCase):
    def setUp(self):
        SupyTestCase.setUp(self)
        self.number = madlib.plugin.MadlibGenerator().number

    def testReturnsNumberString(self):
        num = self.number()
        self.assertTrue(re.match('^\d+$', num))

    def testReturnsRandomNumbers(self):
        # 100 times should be enough to get more than one random number!
        # since there's a nonzero chance that the same number could be
        # returned twice.
        numbers = [ self.number() for _ in range(0,100) ]
        self.assertTrue( len(set(numbers)) > 1 )

class MadlibGeneratorSubtitionTestCase(SupyTestCase):
    def setUp(self):
        SupyTestCase.setUp(self)
        self.generator = madlib.plugin.MadlibGenerator()

    def testSubtitutesNoun(self):
        self.assertNotEqual('$noun', self.generator.madlib('$noun'))

    def testMultipleNounSubstitutions(self):
        self.assertFalse(
            re.search('\$noun', self.generator.madlib('$noun $noun') ) )

    def testSubstitutionWithFunction(self):
        self.assertTrue(
                re.match('^hello\d+goodbye$',
                    self.generator.madlib('hello$numbergoodbye')))

    def testPreservesCapitalizedPlaceholders(self):
        self.generator.words['noun'] = ['item']
        self.assertEqual('Item', self.generator.madlib('$Noun'))

    def testPreservesAllUppercase(self):
        self.generator.words['noun'] = ['item']
        self.assertEqual('xxITEMxx', self.generator.madlib('xx$NOUNxx'))


class MadlibTestCase(PluginTestCase):
    plugins = ('Madlib',)

    def testMadlib(self):
        self.assertNotError('madlib $noun $verb')

    def testSubstitution(self):
        response = self.getMsg('madlib $noun $verb').args[1]
        self.assertNotEqual('$noun $verb', response)

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
