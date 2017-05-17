# -*- coding: utf-8 -*-

import unittest

from pinyin.db import database
import pinyin.dictionary
from pinyin.media import MediaPack
from pinyin.transformations import *


# Shared dictionary
englishdict = pinyin.dictionary.PinyinDictionary.loadall()('en')

# Default tone color list for tests
colorlist = [
    "#ff0000",
    "#ffaa00",
    "#00aa00",
    "#0000ff",
    "#545454"
  ]

class PinyinColorizerTest(unittest.TestCase):
    def testRSuffix(self):
        self.assertEqual(self.colorize("哪兒"), '<span style="color:#00aa00">na3</span><span style="color:#545454">r</span>')
    
    def testColorize(self):
        # Need to call .lower() here because we have a dictionary entry for this character with Ma3
        self.assertEqual(self.colorize("妈麻马骂吗").lower(),
            '<span style="color:#ff0000">ma1</span> <span style="color:#ffaa00">ma2</span> ' +
            '<span style="color:#00aa00">ma3</span> <span style="color:#0000ff">ma4</span> ' +
            '<span style="color:#545454">ma</span>')

    def testMixedEnglishChinese(self):
        self.assertEqual(self.colorize('Small 小 - Horse'),
            'Small <span style="color:#00aa00">xiao3</span> - Horse')
    
    def testPunctuation(self):
        self.assertEqual(self.colorize('小小!'),
            '<span style="color:#00aa00">xiao3</span> <span style="color:#00aa00">xiao3</span>!')

    def testUseSpokenToneRatherThanWrittenOne(self):
        self.assertEqual(flatten(colorize(colorlist, [Word(Pinyin("xiao", ToneInfo(written=3, spoken=2)))])),
            '<span style="color:#66cc66">xiao3</span>')

    # Test helpers
    def colorize(self, what):
        return flatten(colorize(colorlist, englishdict.reading(what)))

class CharacterColorizerTest(unittest.TestCase):
    def testColorize(self):
        self.assertEqual(self.colorize("妈麻马骂吗"),
            '<span style="color:#ff0000">妈</span><span style="color:#ffaa00">麻</span>' +
            '<span style="color:#00aa00">马</span><span style="color:#0000ff">骂</span>' +
            '<span style="color:#545454">吗</span>')

    def testMixedEnglishChinese(self):
        self.assertEqual(self.colorize('Small 小 - Horse'),
            'Small <span style="color:#00aa00">小</span> - Horse')
    
    def testPunctuation(self):
        self.assertEqual(self.colorize('小小!'),
            '<span style="color:#00aa00">小</span><span style="color:#00aa00">小</span>!')

    def testUseSpokenToneRatherThanWrittenOne(self):
        self.assertEqual(flatten(colorize(colorlist, [Word(TonedCharacter("小", ToneInfo(written=3, spoken=2)))])),
            '<span style="color:#66cc66">小</span>')

    # Test helpers
    def colorize(self, what):
        return flatten(colorize(colorlist, englishdict.tonedchars(what)))

class PinyinAudioReadingsTest(unittest.TestCase):
    default_raw_available_media = ["na3.mp3", "ma4.mp3", "xiao3.mp3", "ma3.mp3", "ci2.mp3", "dian3.mp3",
                                   "wu3.mp3", "nin2.mp3", "ni3.ogg", "hao3.ogg", "gen1.ogg", "gen1.mp3"]
    
    def testRSuffix(self):
        self.assertHasReading("哪兒", ["na3.mp3"])
        self.assertHasReading("哪儿", ["na3.mp3"])
    
    def testFifthTone(self):
        self.assertHasReading("的", ["de5.mp3"], raw_available_media=["de5.mp3", "de.mp3", "de4.mp3"])
        self.assertHasReading("了", ["le.mp3"], raw_available_media=["le4.mp3", "le.mp3"])
        self.assertHasReading("吗", ["ma4.mp3"], raw_available_media=["ma4.mp3"])
    
    def testNv(self):
        self.assertHasReading("女", ["nu:3.mp3"], raw_available_media=["nu:3.mp3", "nu3.mp3"])
        self.assertHasReading("女", ["nv3.mp3"], raw_available_media=["nu3.mp3", "nu:3.mp3", "nv3.mp3"])
        self.assertMediaMissing("女", raw_available_media=["nu3.mp3"])
        
    def testLv(self):
        self.assertHasReading("侣", ["lv3.mp3"], raw_available_media=["lv3.mp3"])
        self.assertMediaMissing("侣", raw_available_media=["lu3.mp3"])
        self.assertHasReading("掠", ["lve4.mp3"], raw_available_media=["lve4.mp3"])
        self.assertMediaMissing("掠", raw_available_media=["lue4.mp3"])
    
    def testJunkSkipping(self):
        # NB: NOT a partial reading, because none of the tokens here are Pinyin it doesn't know about
        self.assertHasReading("Washington ! ! !", [])
    
    def testMultipleCharacters(self):
        self.assertHasReading("小马词典", ["xiao3.mp3", "ma3.mp3", "ci2.mp3","dian3.mp3"])
    
    def testMixedEnglishChinese(self):
        self.assertHasReading("啎 The Small 马 Dictionary", ["wu3.mp3", "ma3.mp3"])
    
    def testPunctuation(self):
        self.assertHasReading("您 (pr.)", ["nin2.mp3"])
    
    def testSecondaryExtension(self):
        self.assertHasReading("你好", ["ni3.ogg", "hao3.ogg"])

    def testMixedExtensions(self):
        self.assertHasReading("你马", ["ni3.ogg", "ma3.mp3"])

    def testPriority(self):
        self.assertHasReading("根", ["gen1.mp3"])

    def testMediaMissing(self):
        self.assertMediaMissing("根", raw_available_media=[".mp3"])

    def testCaptializationInPinyin(self):
        # NB: 上海 is in the dictionary with capitalized pinyin (Shang4 hai3)
        self.assertHasReading("上海", ["shang4.mp3", "hai3.mp3"], raw_available_media=["shang4.mp3", "hai3.mp3"])
    
    def testCapitializationInFilesystem(self):
        self.assertHasReading("根", ["GeN1.mP3"], available_media={"GeN1.mP3" : "GeN1.mP3" })

    def testDontMixPacks(self):
        packs = [MediaPack("Foo", {"ni3.mp3" : "ni3.mp3", "ma3.mp3" : "ma3.mp3"}), MediaPack("Bar", {"hao3.mp3" : "hao3.mp3"})]
        self.assertHasPartialReading("你好马", ["ni3.mp3", "ma3.mp3"], bestpackshouldbe=packs[0], mediapacks=packs)

    def testUseBestPack(self):
        packs = [MediaPack("Foo", {"xiao3.mp3" : "xiao3.mp3", "ma3.mp3" : "ma3.mp3"}),
                 MediaPack("Bar", {"ma3.mp3" : "ma3.mp3", "ci2.mp3" : "ci2.mp3", "dian3.mp3" : "dian3.mp3"})]
        self.assertHasPartialReading("小马词典", ["ma3.mp3", "ci2.mp3", "dian3.mp3"], bestpackshouldbe=packs[1], mediapacks=packs)

    def testRandomizeBestPackOnTie(self):
        pack1 = MediaPack("Foo", {"ni3.mp3" : "PACK1.mp3"})
        pack2 = MediaPack("Bar", {"ni3.mp3" : "PACK2.mp3"})

        gotpacks = []
        for n in range(1, 10):
            gotpack, _, _ = PinyinAudioReadings([pack1, pack2], [".mp3", ".ogg"]).audioreading(englishdict.reading("你"))
            gotpacks.append(gotpack)
        
        # This test will nondeterministically fail (1/2)^10 = 0.01% of the time
        self.assertTrue(pack1 in gotpacks)
        self.assertTrue(pack2 in gotpacks)

    def testUseSpokenToneRatherThanWrittenOne(self):
        mediapacks = [MediaPack("Foo", { "ma2.mp3" : "ma2.mp3", "ma3.mp3" : "ma3.mp3" })]
        mediapack, output, mediamissing = PinyinAudioReadings(mediapacks, [".mp3"]).audioreading([Word(Pinyin("ma", ToneInfo(written=2, spoken=3)))])
        self.assertEqual(mediapack, mediapacks[0])
        self.assertFalse(mediamissing)
        self.assertEqual(output, ["ma3.mp3"])

    # Test helpers
    def assertHasReading(self, what, shouldbe, **kwargs):
        bestpackshouldbe, mediapack, output, mediamissing = self.audioreading(what, **kwargs)
        self.assertEqual(bestpackshouldbe, mediapack)
        self.assertEqual(output, shouldbe)
        self.assertFalse(mediamissing)
    
    def assertHasPartialReading(self, what, shouldbe, **kwargs):
        bestpackshouldbe, mediapack, output, mediamissing = self.audioreading(what, **kwargs)
        self.assertEqual(bestpackshouldbe, mediapack)
        self.assertEqual(output, shouldbe)
        self.assertTrue(mediamissing)
        
    def assertMediaMissing(self, what, **kwargs):
        bestpackshouldbe, mediapack, output, mediamissing = self.audioreading(what, **kwargs)
        self.assertTrue(mediamissing)
    
    def audioreading(self, what, **kwargs):
        bestpackshouldbe, mediapacks = self.expandmediapacks(**kwargs)
        mediapack, output, mediamissing = PinyinAudioReadings(mediapacks, [".mp3", ".ogg"]).audioreading(englishdict.reading(what))
        return bestpackshouldbe, mediapack, output, mediamissing
    
    def expandmediapacks(self, mediapacks=None, available_media=None, raw_available_media=default_raw_available_media, bestpackshouldbe=None):
        if mediapacks:
            return bestpackshouldbe, mediapacks
        elif available_media:
            pack = MediaPack("Test", available_media)
            return pack, [pack]
        else:
            pack = MediaPack("Test", dict([(filename, filename) for filename in raw_available_media]))
            return pack, [pack]

class ToneSandhiTest(unittest.TestCase):
    def testDoesntAffectWrittenTones(self):
        self.assertEqual(flatten(tonesandhi([Word(Pinyin.parse("hen3")), Word(Pinyin.parse("hao3"))])), "hen3hao3")
    
    def testText(self):
        self.assertSandhi(Word(Text("howdy")), "howdy")
    
    def testSingleThirdTone(self):
        self.assertSandhi(Word(Pinyin.parse("hen3")), "hen3")
    
    def testSimple(self):
        self.assertSandhi(Word(Pinyin.parse("hen3")), Word(Pinyin.parse("hao3")), "hen2hao3")
        self.assertSandhi(Word(Pinyin.parse("hen3"), Pinyin.parse("hao3")), "hen2hao3")
    
    def testIgnoresWhitespace(self):
        self.assertSandhi(Word(Pinyin.parse("hen3")), Word(Text(" ")), Word(Pinyin.parse("hao3")), "hen2 hao3")
        self.assertSandhi(Word(Pinyin.parse("hen3"), Text(" "), Pinyin.parse("hao3")), "hen2 hao3")
    
    def testMultiMono(self):
        self.assertSandhi(Word(Pinyin.parse("bao3"), Pinyin.parse("guan3")), Word(Pinyin.parse("hao3")), "bao2guan2hao3")
    
    def testMonoMulti(self):
        self.assertSandhi(Word(Pinyin.parse("lao3")), Word(Pinyin.parse("bao3"), Pinyin.parse("guan3")), "lao3bao2guan3")
    
    def testBugWithWordContour(self):
        # The original bug:
        self.assertSandhi(Word(Pinyin('jiu', ToneInfo(written=3, spoken=3))), Word(Text(' ')), Word(Pinyin('shui', ToneInfo(written=3, spoken=3))), Word(Text(' ')),
                          Word(Pinyin('yin', ToneInfo(written=3, spoken=3)), Text(' '), Pinyin('liao', ToneInfo(written=4, spoken=4))),
                          "jiu2 shui3 yin3 liao4")
        # A test that used to find it, before the dictionary was updated with the
        # compound 饮料 - modified to take the new information into account:
        self.assertSandhi(*(englishdict.reading("酒水饮料") + ["jiu2 shui2 yin3 liao4"]))
    
    # TODO: improve tone sandhi such that the following tests pass:
    #
    # def testYiFollowedByFour(self):
    #     self.assertSandhi(Word(Pinyin.parse("yi1")), Word(Pinyin.parse("ding4")), "yi2ding4")
    # 
    # def testYiFollowedByOther(self):
    #     self.assertSandhi(Word(Pinyin.parse("yi1")), Word(Pinyin.parse("tian1")), "yi4tian1")
    #     self.assertSandhi(Word(Pinyin.parse("yi1")), Word(Pinyin.parse("nian2")), "yi4nian2")
    #     self.assertSandhi(Word(Pinyin.parse("yi1")), Word(Pinyin.parse("qi3")), "yi4qi3")
    # 
    # def testYiBetweenTwoWords(self):
    #     self.assertSandhi(Word(Pinyin.parse("kan4")), Word(Pinyin.parse("yi1")), Word(Pinyin.parse("kan4")), "kan4yikan4")
    # 
    # # NB: don't bother to implement yi1 sandhi that depends on context such as whether we are
    # # counting sequentially or using yi1 as an ordinal number
    # 
    # def testBuFollowedByFourth(self):
    #     self.assertSandhi(Word(Pinyin.parse("bu4")), Word(Pinyin.parse("shi4")), "bu2shi4")
    # 
    # def testBuBetweenTwoWords(self):
    #     self.assertSandhi(Word(Pinyin.parse("shi4")), Word(Pinyin.parse("bu4")), Word(Pinyin.parse("shi4")), "shi4bushi4")
    
    # Test helpers
    def assertSandhi(self, *args):
        self.assertEqual(flatten(self.copySpokenToWritten(tonesandhi(args[:-1]))), args[-1])
    
    def copySpokenToWritten(self, words):
        class CopySpokenToWrittenVisitor(TokenVisitor):
            def visitText(self, text):
                return text
            
            def visitPinyin(self, pinyin):
                return Pinyin(pinyin.word, ToneInfo(written=pinyin.toneinfo.spoken))
            
            def visitTonedCharacter(self, tonedcharacter):
                return TonedCharacter(str(tonedcharacter), ToneInfo(written=tonedcharacter.toneinfo.spoken))
        
        return [word.map(CopySpokenToWrittenVisitor()) for word in words]

class TrimErhuaTest(unittest.TestCase):
    def testTrimErhuaEmpty(self):
        self.assertEqual(flatten(trimerhua([])), '')

    def testTrimErhuaCharacters(self):
        self.assertEqual(flatten(trimerhua([Word(TonedCharacter("一", 1), TonedCharacter("瓶", 2), TonedCharacter("儿", 5))])), "一瓶")

    def testTrimErhuaPinyin(self):
        self.assertEqual(flatten(trimerhua([Word(Pinyin.parse("yi1"), Pinyin.parse("ping2"), Pinyin.parse("r5"))])), "yi1ping2")
        self.assertEqual(flatten(trimerhua([Word(Pinyin.parse("yi1")), Word(Pinyin.parse("ping2"), Pinyin.parse("r5"))])), "yi1ping2")

    def testDontTrimNonErhua(self):
        self.assertEqual(flatten(trimerhua([Word(TonedCharacter("一", 1), TonedCharacter("瓶", 2))])), "一瓶")

    def testTrimSingleErHua(self):
        self.assertEqual(flatten(trimerhua([Word(Pinyin.parse('r5'))])), '')
        self.assertEqual(flatten(trimerhua([Word(TonedCharacter('儿', 5))])), '')
        self.assertEqual(flatten(trimerhua([Word(Pinyin.parse('r5'))])), '')
        self.assertEqual(flatten(trimerhua([Word(TonedCharacter('儿', 5))])), '')
        self.assertEqual(flatten(trimerhua([Word(Pinyin.parse('r5'))])), '')
        self.assertEqual(flatten(trimerhua([Word(TonedCharacter('儿', 5))])), '')

class MaskHanziTest(unittest.TestCase):
    def testMaskText(self):
        self.assertEqual(maskhanzi("爱", "mask", [Word(Text("World")), Word(Text("H爱!")), Word(Text(" "), Text("J爱"))]),
                          [Word(Text("World")), Word(Text("Hmask!")), Word(Text(" "), Text("Jmask"))])
    
    def testMaskCharacter(self):
        self.assertEqual(maskhanzi("狠", "chicken", [Word(Pinyin.parse("hen3")), Word(TonedCharacter("狠", 3)), Word(TonedCharacter("mhh", 2))]),
                          [Word(Pinyin.parse("hen3")), Word(Text("chicken")), Word(TonedCharacter("mhh", 2))])

    def testMaskMultiCharacter(self):
        self.assertEqual(maskhanzi("没有", "XXX", [Word(TonedCharacter("没", 2)), Word(TonedCharacter("没", 2)), Word(TonedCharacter("有", 2)), Word(TonedCharacter("有", 2)), Word(Text("没有 le he said 有 to me! 没有!"))]),
                          [Word(Text("XXX")), Word(Text("XXX")), Word(Text("XXX")), Word(Text("XXX")), Word(Text("XXX le he said XXX to me! XXX!"))])

    def testDontMaskWesternForms(self):
        self.assertEqual(maskhanzi("1000AD", "XXX", [Word(Text("In 1000AD..."))]), [Word(Text("In 1000AD..."))])

if __name__ == '__main__':
    unittest.main()

