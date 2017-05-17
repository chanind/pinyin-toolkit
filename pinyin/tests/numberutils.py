# -*- coding: utf-8 -*-

import unittest

import pinyin.db
from pinyin.numberutils import *


englishdict = dictionary.PinyinDictionary.loadall()('en')

class ReadingFromNumberlikeTest(unittest.TestCase):
    def testIntegerReading(self):
        self.assertReading("ba1 qian1 jiu3 Bai3 er4 shi2 yi1", "8921")
        self.assertReading("ba1 qian1 jiu3 Bai3 er4 shi2 yi1", "8,921")
        self.assertReading("san1 qian1 wan4 si4 bai3 wan4 san1 shi2 Wan4 er4 Wan4 si4 qian1 si4 Bai3 san1 shi2 er4", "34,324,432")
    
    def testDecimalReading(self):
        self.assertReading("er4 shi2 wu3 dian3 er4 wu3", "25.25")
        self.assertReading("yi1 qian1 dian3 jiu3", "1,000.9")
        self.assertReading(None, "25.253,2")
    
    def testYearReading(self):
        self.assertReading("yi1 jiu3 jiu3 ba1 nian2", "1998年")
        # This is not a very valid way of writing a year, but it's extra work to disallow it so what the hell
        self.assertReading("yi1 jiu3 jiu3 ba1 nian2", "1,998年")
    
    def testPercentageReading(self):
        self.assertReading("bai3 fen1 zhi1 qi1 shi2", "70%")
        self.assertReading("bai3 fen1 zhi1 qi1 shi2", "70％")
        self.assertReading("bai3 fen1 zhi1 yi1 qian1", "1000%")
        self.assertReading("bai3 fen1 zhi1 yi1 qian1", "1,000%")
    
    def testFractionReading(self):
        self.assertReading("san1 fen1 zhi1 yi1", "1/3")
        self.assertReading("san1 fen1 zhi1 yi1", "1\\3")
        self.assertReading("san1 qian1 fen1 zhi1 yi1 qian1", "1,000/3,000")
    
    def testNoReadingForPhrase(self):
        self.assertReading(None, "你好")
    
    def testNoReadingForBlank(self):
        self.assertReading(None, "")
        self.assertReading(None, "24.")
        self.assertReading(None, "24/")
    
    def testNoReadingsIfTrailingStuff(self):
        self.assertReading(None, "8921A")
        self.assertReading(None, "8,921A")
        self.assertReading(None, "25.25A")
        self.assertReading(None, "1,000.9A")
        self.assertReading(None, "1998年A")
        self.assertReading(None, "80%A")
        self.assertReading(None, "80％A")
        self.assertReading(None, "1000%A")
        self.assertReading(None, "1,000%A")
        self.assertReading(None, "1/3A")
        self.assertReading(None, "1\3A")
        self.assertReading(None, "1,000/3,000!")
    
    # Test helpers
    def assertReading(self, expected_reading, expression):
        self.assertEqual(expected_reading, utils.bind_none(readingfromnumberlike(expression, englishdict), lambda reading: model.flatten(reading)))

class MeaningFromNumberlikeTest(unittest.TestCase):
    def testIntegerMeaning(self):
        self.assertMeaning("8921", "8921")
        self.assertMeaning("8921", "8,921")
        self.assertMeaning("8921", "八千九百二十一")
    
    def testDecimalMeaning(self):
        self.assertMeaning("25.25", "25.25")
        self.assertMeaning("25.25", "25。25")
        self.assertMeaning("25.25", "二十五点二五")
        self.assertMeaning("1123.89", "1,123.89")
    
    def testYearMeaning(self):
        self.assertMeaning("1998AD", "1998年")
        self.assertMeaning("1998AD", "一九九八年")
    
    def testPercentageReading(self):
        self.assertMeaning("20%", "20%")
        self.assertMeaning("1000%", "1000%")
        self.assertMeaning("1000%", "1,000%")
        self.assertMeaning("20%", "百分之二十")
    
    def testFractionReading(self):
        self.assertMeaning("1/3", "1/3")
        self.assertMeaning("1000/3000", "1,000/3,000")
        self.assertMeaning("1/3", "三分之一")
    
    def testNoMeaningForPhrase(self):
        self.assertMeaning(None, "你好")
    
    def testNoMeaningForBlank(self):
        self.assertMeaning(None, "")
        self.assertMeaning(None, "24.")
    
    def testNoMeaningsIfTrailingStuff(self):
        self.assertMeaning(None, "8921A")
        self.assertMeaning(None, "8,921A")
        self.assertMeaning(None, "八千九百二十一A")
        self.assertMeaning(None, "25.25A")
        self.assertMeaning(None, "25。25A")
        self.assertMeaning(None, "二十五点二五A")
        self.assertMeaning(None, "1,123.89A")
        self.assertMeaning(None, "1998年A")
        self.assertMeaning(None, "一九九八年A")
        self.assertMeaning(None, "100%A")
        self.assertMeaning(None, "1000%Junk")
        self.assertMeaning(None, "1,000%!")
        self.assertMeaning(None, "百分之二十A")
        self.assertMeaning(None, "1/3A")
        self.assertMeaning(None, "1\3A")
        self.assertMeaning(None, "1,000/3,000Blah")
        self.assertMeaning(None, "三分之一A")
    
    # Test helpers
    def assertMeaning(self, expected_meaning, expression):
        self.assertEqual(expected_meaning, utils.bind_none(meaningfromnumberlike(expression, englishdict), lambda meanings: model.flatten(meanings[0])))

class NumberAsHanziTest(unittest.TestCase):
    def testSingleNumerals(self):
        self.assertEqual(numberashanzi(0), "零")
        self.assertEqual(numberashanzi(5), "五")
        self.assertEqual(numberashanzi(9), "九")
    
    def testTooLargeNumber(self):
        self.assertEqual(numberashanzi(100000000000000000), "100000000000000000")
    
    def testFullNumbers(self):
        self.assertEqual(numberashanzi(25), "二十五")
        self.assertEqual(numberashanzi(8921), "八千九百二十一")
    
    def testTruncationOfLowerUnits(self):
        self.assertEqual(numberashanzi(20), "二十")
        self.assertEqual(numberashanzi(9000), "九千")
        self.assertEqual(numberashanzi(9100), "九千一百")

    def testSkippedOnes(self):
        self.assertEqual(numberashanzi(1), "一")
        self.assertEqual(numberashanzi(10), "十")
        self.assertEqual(numberashanzi(100), "百")
        self.assertEqual(numberashanzi(1000), "一千")

    def testSkippedMagnitudes(self):
        self.assertEqual(numberashanzi(9025), "九千零二十五")
        self.assertEqual(numberashanzi(9020), "九千零二十")
        self.assertEqual(numberashanzi(9005), "九千零五")

class HanziAsNumberTest(unittest.TestCase):
    def testSingleNumerals(self):
        self.assertHanziAsNumber("零", 0)
        self.assertHanziAsNumber("五", 5)
        self.assertHanziAsNumber("九", 9)
    
    def testLing(self):
        self.assertHanziAsNumber("零", 0)
        self.assertHanziAsNumber("零个", 0, expected_rest_hanzi="个")
    
    def testLiang(self):
        self.assertHanziAsNumber("两", 2)
        self.assertHanziAsNumber("两个", 2, expected_rest_hanzi="个")
    
    def testFullNumbers(self):
        self.assertHanziAsNumber("二十五", 25)
        self.assertHanziAsNumber("八千九百二十一", 8921)
    
    def testTruncationOfLowerUnits(self):
        self.assertHanziAsNumber("二十", 20)
        self.assertHanziAsNumber("九千", 9000)
        self.assertHanziAsNumber("九千一百", 9100)

    def testSkippedOnes(self):
        self.assertHanziAsNumber("一", 1)
        self.assertHanziAsNumber("十", 10)
        self.assertHanziAsNumber("百", 100)
        self.assertHanziAsNumber("一千", 1000)

    def testSkippedMagnitudes(self):
        self.assertHanziAsNumber("九千零二十五", 9025)
        self.assertHanziAsNumber("九千零二十", 9020)
        self.assertHanziAsNumber("九千零五", 9005)
    
    def testNonNumber(self):
        self.assertHanziAsNumber("一个", 1, expected_rest_hanzi="个")
        self.assertHanziAsNumber("个", None, expected_rest_hanzi="个")

    # Test helpers
    def assertHanziAsNumber(self, hanzi, expect_number, expected_rest_hanzi=""):
        actual_number, actual_rest_hanzi = parsehanziasnumber(hanzi)
        self.assertEqual(actual_rest_hanzi, expected_rest_hanzi)
        self.assertEqual(actual_number, expect_number)

if __name__ == '__main__':
    unittest.main()

