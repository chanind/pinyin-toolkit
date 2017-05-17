# -*- coding: utf-8 -*-

import unittest

from pinyin.dictionary import *
from pinyin.db import database
from pinyin.model import ToneInfo, flatten, tokenizespaceseperatedtext


dictionaries = PinyinDictionary.loadall()
englishdict, frenchdict, germandict = dictionaries('en'), dictionaries('fr'), dictionaries('de')

class PinyinDictionaryTest(unittest.TestCase):
    def testTonedTokens(self):
        toned = englishdict.tonedchars("一个")
        self.assertEqual(flatten(toned), "一个")
        self.assertEqual(toned[0][0].toneinfo, ToneInfo(written=1))
        self.assertEqual(toned[0][1].toneinfo, ToneInfo(written=4))
    
    def testTonedCharactersPreservesWhitespace(self):
        self.assertEqual(flatten(englishdict.tonedchars("\t一个")), "\t一个")

    def testTonedTokensWithoutTone(self):
        toned = englishdict.tonedchars("Ｕ盤")
        self.assertEqual(flatten(toned), "Ｕ盤")
        self.assertEqual(toned[0][1].toneinfo, ToneInfo(written=2))

    def testTonedTokenNumbers(self):
        # Although it kind of makes sense to return the arabic numbers with tone colors, users don't expect it :-)
        toned = englishdict.tonedchars("1994")
        self.assertEqual(flatten(toned), "1994")
        self.assertFalse(any([hasattr(token, "tone") for token in toned]))

    def testNumbersWherePinyinLengthDoesntMatchCharacters(self):
        self.assertEqual(flatten(englishdict.tonedchars("1000000000")), "1000000000")
        # Invalidated by removal of numbers from the dictionary:
        # self.assertEquals(flatten(englishdict.reading(u"1000000000")), u"yi1 shi2 yi4")
        self.assertEqual(self.flatmeanings(englishdict, "1000000000"), None)

    def testPhraseMeanings(self):
        self.assertEqual(self.flatmeanings(englishdict, "一杯啤酒"), None)
        self.assertEqual(self.flatmeanings(englishdict, "U盘"), None)
    
    def testPhraseMeaningsNotFoundBecauseOfWhitespacePunctuation(self):
        self.assertNotEqual(self.flatmeanings(englishdict, "你好!"), None)
        self.assertNotEqual(self.flatmeanings(englishdict, "你好!!!"), None)
        self.assertNotEqual(self.flatmeanings(englishdict, "  你好  "), None)

    # Invalidated by fix to issue #71
    # def testMeaningsWithTrailingJunk(self):
    #             self.assertEquals(self.flatmeanings(englishdict, u"鼓聲 (junk!!)"), ["sound of a drum", "drumbeat"])
    
    def testMeaningless(self):
        self.assertEqual(self.flatmeanings(englishdict, "English"), None)

    def testMissingDictionary(self):
        self.assertEqual(fileSource('idontexist.txt'), None)
    
    def testMissingLanguage(self):
        dict = dictionaries('foobar')
        self.assertEqual(flatten(dict.reading("个")), "ge4")
        self.assertEqual(self.flatmeanings(dict, "个"), None)
    
    def testGermanDictionary(self):
        self.assertEqual(flatten(germandict.reading("请")), "qing3")
        self.assertEqual(flatten(germandict.reading("請")), "qing3")
        self.assertEqual(self.flatmeanings(germandict, "請"), ["Bitte ! (u.E.) (Int)", "bitten, einladen (u.E.) (V)"])

    def testEnglishDictionary(self):
        self.assertEqual(flatten(englishdict.reading("鼓聲")), "gu3 sheng1")
        self.assertEqual(flatten(englishdict.reading("鼓声")), "gu3 sheng1")
        self.assertEqual(self.flatmeanings(englishdict, "鼓聲"), ["sound of a drum", "drumbeat"])

    def testFrenchDictionary(self):
        self.assertEqual(flatten(frenchdict.reading("評論")), "ping2 lun4")
        self.assertEqual(flatten(frenchdict.reading("评论")), "ping2 lun4")
        self.assertEqual(self.flatmeanings(frenchdict, "评论"), ["commentaire (n.v.) (n)"])

    def testWordsWhosePrefixIsNotInDictionary(self):
        self.assertEqual(flatten(germandict.reading("生日")), "sheng1 ri4")
        self.assertEqual(self.flatmeanings(germandict, "生日"), ["Geburtstag (S)"])

    def testProperName(self):
        self.assertEqual(flatten(englishdict.reading("珍・奥斯汀")), "Zhen1 · Ao4 si1 ting1")
        self.assertEqual(self.flatmeanings(englishdict, "珍・奥斯汀"), ["Jane Austen (1775-1817), English novelist", "also written 简・奥斯汀 - Jian3 · Ao4 si1 ting1"])

    def testShortPinyin(self):
        self.assertEqual(flatten(englishdict.reading("股指")), "gu3 zhi3")
        self.assertEqual(self.flatmeanings(englishdict, "股指"), ["stock market index", "share price index", "abbr. for 股票指数 - gu3 piao4 zhi3 shu4"])
    
    def testPinyinFromUnihan(self):
        self.assertEqual(flatten(englishdict.reading("諓")), "jian4")
        self.assertEqual(self.flatmeanings(englishdict, "諓"), None)
    
    def testFallsBackOnCEDICTForMissingPinyinAndForeignLanguage(self):
        self.assertEqual(flatten(frenchdict.reading("数量积")), "shu4 liang4 ji1")
        self.assertEqual(self.flatmeanings(frenchdict, "数量积"), None)
    
    # TODO: need to think carefully about how to match up data from different sources.
    # def testFallsBackOnCEDICTForMissingMWAndForeignLanguage(self):
    #         self.assertEquals(germandict.meanings(u"奖项", "simp")[1], [(u"项", u"xiang4")])
    
    # I've changed my mind about this test. We can't really say that an occurance of 儿
    # was meant to be an erhua one without having an entry explicitly in the dictionary
    # for the erhua variant. This test used to pass with the old dictionary code because
    # it arbitrarily defaulted to the r5 reading rather than er4 as it does now.
    # def testErhuaNotSpacedInReadingEvenForUnknownWords(self):
    #         self.assertEquals(flatten(englishdict.reading(u"土豆条儿")), "tu3 dou4 tiao2r")

    # TODO: implement functionality
    # def testUsesFrequencyInformation(self):
    #         self.assertEquals(flatten(englishdict.reading(u"车")), "che1")
    #         self.assertEquals(flatten(englishdict.reading(u"教")), "jiao4")

    def testErhuaSpacedInReadingForKnownWords(self):
        self.assertEqual(flatten(englishdict.reading("两头儿")), "liang3 tou2r")

    def testSimpMeanings(self):
        self.assertEqual(self.flatmeanings(englishdict, "书", prefersimptrad="simp"), ["book", "letter", "see also 书经 Book of History", "MW: 本 - ben3, 册 - ce4, 部 - bu4"])
    
    def testTradMeanings(self):
        self.assertEqual(self.flatmeanings(englishdict, "书", prefersimptrad="trad"), ["book", "letter", "see also 書經 Book of History", "MW: 本 - ben3, 冊 - ce4, 部 - bu4"])
    
    def testNonFlatMeanings(self):
        dictmeanings, dictmeasurewords = englishdict.meanings("书", prefersimptrad="simp")
        self.assertEqual(self.flattenall(dictmeanings), ["book", "letter", "see also 书经 Book of History"])
        self.assertEqual([(self.flattenall(dictmwcharacters)[0], self.flattenall(dictmwpinyin)[0]) for dictmwcharacters, dictmwpinyin in dictmeasurewords],
                          [("本", "ben3"), ("册", "ce4"), ("部", "bu4")])
    
    # Test helper 
    def flatmeanings(self, dictionary, what, prefersimptrad="simp"):
        dictmeanings = combinemeaningsmws(*(dictionary.meanings(what, prefersimptrad)))
        return self.flattenall(dictmeanings)
    
    def flattenall(self, tokens):
        if tokens:
            return [flatten(token) for token in tokens]
        else:
            return None

class PinyinConverterTest(unittest.TestCase):
    # Test data:
    nihao_simp = '你好，我喜欢学习汉语。我的汉语水平很低。'
    nihao_trad = '你好，我喜歡學習漢語。我的漢語水平很低。'
    nihao_simp_western_punc = '你好, 我喜欢学习汉语. 我的汉语水平很低.'
    nihao_reading = "ni3 hao3, wo3 xi3 huan xue2 xi2 Han4 yu3. wo3 de Han4 yu3 shui3 ping2 hen3 di1."

    def testSimplifiedPinyin(self):
        self.assertEqual(self.reading(self.nihao_simp), self.nihao_reading)

    def testTraditionalPinyin(self):
        self.assertEqual(self.reading(self.nihao_trad), self.nihao_reading)

    def testWesternPunctuation(self):
        self.assertEqual(self.reading(self.nihao_simp_western_punc), self.nihao_reading)

    def testNoSpacesAfterBraces(self):
        self.assertEqual(self.reading("(你)好!"), "(ni3)hao3!")

    def testEmptyString(self):
        self.assertEqual(self.reading(""), "")

    def testMixedEnglishChinese(self):
        self.assertEqual(self.reading("你 (pr.)"), "ni3 (pr.)")

    def testNeutralRSuffix(self):
        self.assertEqual(self.reading("一塊兒"), "yi1 kuai4r")

    # Test helpers
    def reading(self, what):
        return flatten(englishdict.reading(what))

if __name__ == '__main__':
    unittest.main()

