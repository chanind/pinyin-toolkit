# -*- coding: utf-8 -*-

import unittest

from pinyin.meanings import *


class MeaningFormatterTest(unittest.TestCase):
    shangwu_def = "/morning/CL:個|个[ge4]/"
    shangwu_meanings = ["morning"]
    shangwu_simp_mws = [('个', 'ge4')]
    shangwu_trad_mws = [('個', 'ge4')]
    
    shu_def = "/book/letter/same as 書經|书经 Book of History/CL:本[ben3],冊|册[ce4],部[bu4],叢|丛[cong2]/"
    shu_simp_meanings = ["book", "letter", "same as 书经 Book of History"]
    shu_simp_mws = [("本", "ben3"), ("册", "ce4"), ("部", "bu4"), ("丛", "cong2")]
    shu_trad_meanings = ["book", "letter", "same as 書經 Book of History"]
    shu_trad_mws = [("本", "ben3"), ("冊", "ce4"), ("部", "bu4"), ("叢", "cong2")]
    
    def testDatesInMeaning(self):
        means, mws = self.parseunflat(1, "simp", "/Jane Austen (1775-1817), English novelist/also written 简・奧斯汀|简・奥斯汀[Jian3 · Ao4 si1 ting1]/")
        self.assertEqual(len(means), 2)
        self.assertEqual(mws, [])
        
        self.assertEqual(flatten(means[0]), "Jane Austen (1775-1817), English novelist")
        self.assertFalse(any([hasattr(token, "tone") for token in means[0]]))
    
    def testSplitNoMeasureWords(self):
        means, mws = self.parse(1, "simp", "/morning/junk junk")
        self.assertEqual(means, ["morning", "junk junk"])
        self.assertEqual(mws, [])
    
    def testSplitMeasureWordsSimp(self):
        means, mws = self.parse(1, "simp", self.shangwu_def)
        self.assertEqual(means, self.shangwu_meanings)
        self.assertEqual(mws, self.shangwu_simp_mws)
    
    def testSplitMeasureWordsTrad(self):
        means, mws = self.parse(1, "trad", self.shangwu_def)
        self.assertEqual(means, self.shangwu_meanings)
        self.assertEqual(mws, self.shangwu_trad_mws)
    
    def testSplitSeveralMeasureWordsSimp(self):
        means, mws = self.parse(1, "simp", self.shu_def)
        self.assertEqual(means, self.shu_simp_meanings)
        self.assertEqual(mws, self.shu_simp_mws)

    def testSplitSeveralMeasureWordsTrad(self):
        means, mws = self.parse(1, "trad", self.shu_def)
        self.assertEqual(means, self.shu_trad_meanings)
        self.assertEqual(mws, self.shu_trad_mws)

    def testSplitSeveralMeasureWordsDifferentIndex(self):
        means, mws = self.parse(0, "simp", self.shu_def)
        self.assertEqual(means, self.shu_trad_meanings)
        self.assertEqual(mws, self.shu_trad_mws)

    def testSplitMultiEmbeddedPinyin(self):
        means, mws = self.parse(1, "simp", "/dictionary (of Chinese compound words)/also written 辭典|辞典[ci2 dian3]/CL:部[bu4],本[ben3]/")
        self.assertEqual(means, ["dictionary (of Chinese compound words)", "also written 辞典 - ci2 dian3"])
        self.assertEqual(mws, [('部', 'bu4'), ('本', 'ben3')])

    def testCallback(self):
        means, mws = self.parse(1, "simp", self.shu_def, tonedchars_callback=lambda x: Word(Text("JUNK")))
        self.assertEqual(means, ['book', 'letter', 'same as JUNK Book of History'])

    def testColorsAttachedToBothHanziAndPinyin(self):
        means, mws = self.parseunflat(1, "simp", "/sound of breaking or snapping (onomatopoeia)/also written 喀嚓|喀嚓 [ka1 cha1]/")
        self.assertEqual(flatten(means[0]), "sound of breaking or snapping (onomatopoeia)")
        self.assertEqual(means[1][-3], Word(TonedCharacter("喀", 1), TonedCharacter("嚓", 1)))

    def testColorsAttachedToHangingPinyin(self):
        means, mws = self.parseunflat(1, "simp", "/silly hen3 definition hao3/a hen is not pinyin")
        self.assertEqual(means[0][0][2], Pinyin("hen", 3))
        self.assertEqual(means[0][0][-1], Pinyin("hao", 3))
        self.assertEqual(means[1][0][2], Text("hen"))
        
    # Test helpers
    def parse(self, *args, **kwargs):
        means, mws = self.parseunflat(*args, **kwargs)
        return [flatten(mean) for mean in means], [(flatten(mwcharwords), flatten(mwpinyinwords)) for (mwcharwords, mwpinyinwords) in mws]
    
    def parseunflat(self, simplifiedcharindex, prefersimptrad, definition, tonedchars_callback=None):
        return MeaningFormatter(simplifiedcharindex, prefersimptrad).parsedefinition(definition, tonedchars_callback=tonedchars_callback)

if __name__ == '__main__':
    unittest.main()

