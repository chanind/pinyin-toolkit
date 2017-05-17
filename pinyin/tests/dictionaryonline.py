# -*- coding: utf-8 -*-

import unittest

from pinyin.dictionaryonline import *


class ParseGoogleResponseTest(unittest.TestCase):
    def testParseNumber(self):
        self.assertEqual(parsegoogleresponse('1'), 1)
    
    def testParseNegativeNumber(self):
        self.assertEqual(parsegoogleresponse('-1'), -1)
    
    def testParseString(self):
        self.assertEqual(parsegoogleresponse('"hello"'), "hello")
    
    def testParseStringWithEscapes(self):
        self.assertEqual(parsegoogleresponse('"hello\\t\\"world\\""'), 'hello\t"world"')
        self.assertEqual(parsegoogleresponse('"\\tleading whitespace"'), '\tleading whitespace')
    
    def testParseUnicodeString(self):
        self.assertEqual(parsegoogleresponse('"好"'), '好')
    
    def testParseList(self):
        self.assertEqual(parsegoogleresponse('[1, "hello", 10, "world", 1337]'), [1, "hello", 10, "world", 1337])
    
    def testParseListOfLists(self):
        self.assertEqual(parsegoogleresponse('[1, [2, [3, 4]], [5, 6]]'), [1, [2, [3, 4]], [5, 6]])
    
    def testParseDict(self):
        self.assertEqual(parsegoogleresponse('{"fruit" : "orange", "1" : 2, "buy" : 1337}'), {"fruit" : "orange", "1" : 2, "buy" : 1337})
    
    def testParseDictOfDicts(self):
        self.assertEqual(parsegoogleresponse('{"fruits" : {"orange" : 1, "banana" : 2}, "numbers" : {"1337" : ["cool"], "13" : ["bad", "unlucky"]}}'),
                                              {"fruits" : {"orange" : 1, "banana" : 2}, "numbers" : {"1337" : ["cool"], "13" : ["bad", "unlucky"]}})
    
    def testParseWhitespace(self):
        self.assertEqual(parsegoogleresponse('[ 1    ,"hello",[10, "barr rr"],   "world"   , 1337, {     "a" :   "dict"} ]'), [1, "hello", [10, "barr rr"], "world", 1337, { "a": "dict" }])
    
    def testParseErrorIfTrailingStuff(self):
        self.assertRaises(ValueError, lambda: parsegoogleresponse('1 1'))
        self.assertRaises(ValueError, lambda: parsegoogleresponse('"hello" 1'))
        self.assertRaises(ValueError, lambda: parsegoogleresponse('[1] 1'))
    
    def testParseErrorIfUnknownCharacters(self):
        self.assertRaises(ValueError, lambda: parsegoogleresponse('! "hello" !'))
    
    def testParseErrorIfListNotClosed(self):
        self.assertRaises(ValueError, lambda: parsegoogleresponse('[ "hello"'))
    
    def testParseErrorIfDictMissingValueNotClosed(self):
        self.assertRaises(ValueError, lambda: parsegoogleresponse('{ "hello" }'))
        # Not valid any more since we interpret missing values as None:
        #self.assertRaises(ValueError, lambda: parsegoogleresponse('{ "hello" : }'))
    
    def testParsingDictionaryWithEmptyField(self):
        self.assertEqual(parsegoogleresponse('{ "hello" : "" }'), { "hello" : "" })
        self.assertEqual(parsegoogleresponse('{ "hello" : null }'), { "hello" : None })
    
    def testParseErrorIfDictNotClosed(self):
        self.assertRaises(ValueError, lambda: parsegoogleresponse('{ "hello" : "world"'))
    
    # Not valid any more since we interpret missing values as None:
    #def testParseErrorIfEmpty(self):
    #    self.assertRaises(ValueError, lambda: parsegoogleresponse(''))
    
    def testParsingEmpty(self):
        self.assertEqual(parsegoogleresponse('{}'), {})

class GoogleTranslateTest(unittest.TestCase):
    def testTranslateNothing(self):
        self.assertEqual(gTrans(""), None)
    
    def testTranslateEnglish(self):
        self.assertEqual(gTrans("你好，你是我的朋友吗？"), [[Word(Text('Hello, you my friend?'))]])
    
    def testTranslateFrench(self):
        self.assertEqual(gTrans("你好，你是我的朋友吗？", "fr"), [[Word(Text('Bonjour, vous mon ami?'))]])
    
    def testTranslateIdentity(self):
        self.assertEqual(gTrans("canttranslatemefromchinese"), None)
    
    def testTranslateStripsHtml(self):
        self.assertEqual(gTrans("你好，你<b>是我的</b>朋友吗？"), [[Word(Text('Hello, you my friend?'))]])

    # Annoyingly, this fails. This means that simplified/traditional translation doesn't preserve whitespace:
    # def testTranslatePreservesWhitespace(self):
    #     self.assertEquals(gTrans(u"\t个个个\t个个\t", "zh-tw"), [[Word(Text(u'\t个个个\t个个\t'))]])
    
    def testTranslateDealsWithDefinition(self):
        self.assertEqual(gTrans("好"), [
            [Word(Text("Good"))],
            [Word(Text("Adjective: good"))],
            [Word(Text("Adverb: well, OK, fine, okay, okey, okey dokey"))],
            [Word(Text("Interjection: OK, okay, okey"))],
            [Word(Text("Verb: love, like"))]
          ])
        # [
        #    [Word(Text("Well"))],
        #    [Word(Text("Verb: like, love"))],
        #    [Word(Text("Adjective: good"))],
        #    [Word(Text("Adverb: fine, OK, okay, okey, okey dokey, well"))],
        #    [Word(Text("Interjection: OK!, okay!, okey!"))]
        #  ])
    
    def testCheck(self):
        self.assertEqual(gCheck(), True)

if __name__ == '__main__':
    unittest.main()

