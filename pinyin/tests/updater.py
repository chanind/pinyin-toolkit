# -*- coding: utf-8 -*-

import copy
import unittest

from pinyin.config import *
from pinyin.db import database
from pinyin.updater import *
from pinyin.utils import Thunk
from pinyin.mocks import *


englishdict = dictionary.PinyinDictionary.loadall()('en')

class FieldUpdaterFromAudioTest(unittest.TestCase):
    def testDoesntDoAnythingWhenDisabled(self):
        self.assertEqual(self.updatefact("hen3 hao3", { "audio" : "", "expression" : "junk" }, forcepinyininaudiotosoundtags = False),
                          { "audio" : "", "expression" : "junk" })
    
    def testWorksIfFieldMissing(self):
        self.assertEqual(self.updatefact("hen3 hao3", { "expression" : "junk" }, forcepinyininaudiotosoundtags = True),
                          { "expression" : "junk" })

    def testLeavesOtherFieldsAlone(self):
        self.assertEqual(self.updatefact("", { "audio" : "junk", "expression" : "junk" }, forcepinyininaudiotosoundtags = True),
                          { "audio" : "", "expression" : "junk" })

    def testReformatsAccordingToConfig(self):
        henhaoaudio = "[sound:" + os.path.join("Test", "hen3.mp3") + "][sound:" + os.path.join("Test", "hao3.mp3") + "]"

        self.assertEqual(
            self.updatefact("hen3 hao3", { "audio" : "junky" }, forcepinyininaudiotosoundtags = True),
            { "audio" : henhaoaudio })
        self.assertEqual(
            self.updatefact("hen3,hǎo", { "audio" : "junky" }, forcepinyininaudiotosoundtags = True),
            { "audio" : henhaoaudio })
    
    def testDoesntModifySoundTags(self):
        self.assertEqual(
            self.updatefact("[sound:aeuth34t0914bnu.mp3][sound:ae390n32uh2ub.mp3]", { "audio" : "" }, forcepinyininaudiotosoundtags = True),
            { "audio" : "[sound:aeuth34t0914bnu.mp3][sound:ae390n32uh2ub.mp3]" })
        self.assertEqual(
            self.updatefact("[sound:hen3.mp3][sound:hao3.mp3]", { "audio" : "" }, forcepinyininaudiotosoundtags = True),
            { "audio" : "[sound:hen3.mp3][sound:hao3.mp3]" })
    
    # Test helpers
    def updatefact(self, *args, **kwargs):
        infos, fact = self.updatefactwithinfos(*args, **kwargs)
        return fact

    def updatefactwithinfos(self, audio, fact, mediapacks = None, **kwargs):
        notifier = MockNotifier()

        if mediapacks == None:
            mediapacks = [media.MediaPack("Test", { "shu1.mp3" : "shu1.mp3", "shu1.ogg" : "shu1.ogg",
                                                    "san1.mp3" : "san1.mp3", "qi1.ogg" : "qi1.ogg", "Kai1.mp3" : "location/Kai1.mp3",
                                                    "hen3.mp3" : "hen3.mp3", "hen2.mp3" : "hen2.mp3", "hao3.mp3" : "hao3.mp3" })]
        mediamanager = MockMediaManager(mediapacks)

        factclone = copy.deepcopy(fact)
        FieldUpdaterFromAudio(notifier, mediamanager, Config(kwargs)).updatefact(factclone, audio)

        return notifier.infos, factclone

class FieldUpdaterFromMeaningTest(unittest.TestCase):
    def testDoesntDoAnythingWhenDisabled(self):
        self.assertEqual(self.updatefact("(1) yes (2) no", { "meaning" : "", "expression" : "junk" }, forcemeaningnumberstobeformatted = False),
                          { "meaning" : "", "expression" : "junk" })
    
    def testWorksIfFieldMissing(self):
        self.assertEqual(self.updatefact("(1) yes (2) no", { "expression" : "junk" }, forcemeaningnumberstobeformatted = True),
                          { "expression" : "junk" })

    def testLeavesOtherFieldsAlone(self):
        self.assertEqual(self.updatefact("", { "meaning" : "junk", "expression" : "junk" }, forcemeaningnumberstobeformatted = True),
                          { "meaning" : "", "expression" : "junk" })

    def testReformatsAccordingToConfig(self):
        self.assertEqual(
            self.updatefact("(1) yes (2) no", { "meaning" : "junky" },
                forcemeaningnumberstobeformatted = True, meaningnumbering = "circledArabic", colormeaningnumbers = False),
                { "meaning" : "① yes ② no" })
        self.assertEqual(
            self.updatefact("(10) yes 2 no", { "meaning" : "junky" },
                forcemeaningnumberstobeformatted = True, meaningnumbering = "none", colormeaningnumbers = False),
                { "meaning" : " yes 2 no" })
    
    # Test helpers
    def updatefact(self, reading, fact, **kwargs):
        factclone = copy.deepcopy(fact)
        FieldUpdaterFromMeaning(Config(kwargs)).updatefact(factclone, reading)
        return factclone

class FieldUpdaterFromReadingTest(unittest.TestCase):
    def testDoesntDoAnythingWhenDisabled(self):
        self.assertEqual(self.updatefact("hen3 hǎo", { "reading" : "", "expression" : "junk" }, forcereadingtobeformatted = False),
                          { "reading" : "", "expression" : "junk" })
    
    def testDoesSomethingWhenDisabledIfAlways(self):
        fact = { "reading" : "", "expression" : "junk" }
        FieldUpdaterFromReading(Config({ "forcereadingtobeformatted" : False })).updatefactalways(fact, "also junk")
        self.assertEqual(fact, { "reading" : "also junk", "expression" : "junk" })
    
    def testWorksIfFieldMissing(self):
        self.assertEqual(self.updatefact("hen3 hǎo", { "expression" : "junk" }, forcereadingtobeformatted = True),
                          { "expression" : "junk" })

    def testLeavesOtherFieldsAlone(self):
        self.assertEqual(self.updatefact("", { "reading" : "junk", "expression" : "junk" }, forcereadingtobeformatted = True),
                          { "reading" : "", "expression" : "junk" })

    def testReformatsAccordingToConfig(self):
        self.assertEqual(
            self.updatefact("hen3 hǎo", { "reading" : "junky" },
                forcereadingtobeformatted = True, tonedisplay = "tonified",
                colorizedpinyingeneration = True, tonecolors = ["#111111", "#222222", "#333333", "#444444", "#555555"]),
                { "reading" : '<span style="color:#333333">hěn</span> <span style="color:#333333">hǎo</span>' })
    
    def testReformattingRespectsExistingColorization(self):
        self.assertEqual(
            self.updatefact("<span style='color: red'>hen3</span> hǎo", { "reading" : "junky" },
                forcereadingtobeformatted = True, tonedisplay = "numeric",
                colorizedpinyingeneration = True, tonecolors = ["#111111", "#222222", "#333333", "#444444", "#555555"]),
                { "reading" : '<span style=\"\"><span style="color: red">hen3</span></span> <span style="color:#333333">hao3</span>' })

    # Test helpers
    def updatefact(self, reading, fact, **kwargs):
        factclone = copy.deepcopy(fact)
        FieldUpdaterFromReading(Config(kwargs)).updatefact(factclone, reading)
        return factclone

class FieldUpdaterFromExpressionTest(unittest.TestCase):
    def testAutoBlanking(self):
        self.assertEqual(self.updatefact("", { "reading" : "blather", "meaning" : "junk", "color" : "yes!", "trad" : "meh", "simp" : "yay" }),
                          { "reading" : "", "meaning" : "", "color" : "", "trad" : "", "simp" : "" })
    
    def testAutoBlankingAudioMeasureWord(self):
        # TODO: test behaviour for audio and measure word, once we know what it should be
        pass
    
    def testFullUpdate(self):
        self.assertEqual(
            self.updatefact("书", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "", "trad" : "", "simp" : "" },
                colorizedpinyingeneration = True, colorizedcharactergeneration = True, meaninggeneration = True, detectmeasurewords = True, emphasisemainmeaning = False,
                tonedisplay = "tonified", meaningnumbering = "circledChinese", colormeaningnumbers = False, meaningseperator = "lines", prefersimptrad = "simp",
                audiogeneration = True, audioextensions = [".mp3"], tonecolors = ["#ff0000", "#ffaa00", "#00aa00", "#0000ff", "#545454"], weblinkgeneration = False, hanzimasking = False,
                tradgeneration = True, simpgeneration = True, forceexpressiontobesimptrad = False), {
                    "reading" : '<span style="color:#ff0000">shū</span>',
                    "meaning" : '㊀ book<br />㊁ letter<br />㊂ see also <span style="color:#ff0000">\u4e66</span><span style="color:#ff0000">\u7ecf</span> Book of History',
                    "mw" : '<span style="color:#00aa00">本</span> - <span style="color:#00aa00">běn</span>, <span style="color:#0000ff">册</span> - <span style="color:#0000ff">cè</span>, <span style="color:#0000ff">部</span> - <span style="color:#0000ff">bù</span>',
                    "audio" : "[sound:" + os.path.join("Test", "shu1.mp3") + "]",
                    "color" : '<span style="color:#ff0000">书</span>',
                    "trad" : "書", "simp" : "书"
                  })
    
    def testFullUpdateGerman(self):
        self.assertEqual(
            self.updatefact("书", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "", "trad" : "", "simp" : "" },
                dictlanguage = "de",
                colorizedpinyingeneration = True, colorizedcharactergeneration = True, meaninggeneration = True, detectmeasurewords = True,
                tonedisplay = "tonified", audiogeneration = True, audioextensions = [".ogg"], tonecolors = ["#ff0000", "#ffaa00", "#00aa00", "#0000ff", "#545454"],
                tradgeneration = True, simpgeneration = True, forceexpressiontobesimptrad = False), {
                    "reading" : '<span style="color:#ff0000">shū</span>',
                    "meaning" : 'Buch, Geschriebenes (S)',
                    "mw" : '',
                    "audio" : "[sound:" + os.path.join("Test", "shu1.ogg") + "]",
                    "color" : '<span style="color:#ff0000">书</span>',
                    "trad" : "書", "simp" : "书"
                  })
    
    def testUpdatePreservesWhitespace(self):
        self.assertEqual(
            self.updatefact("\t书", { "reading" : "", "color" : "", "trad" : "", "simp" : "" },
                dictlanguage = "en",
                colorizedpinyingeneration = False, colorizedcharactergeneration = True, meaninggeneration = False,
                tonedisplay = "tonified", audiogeneration = False, tradgeneration = True, simpgeneration = True, forceexpressiontobesimptrad = False), {
                    "reading" : '\tshū',
                    "color" : '\t<span style="color:#ff0000">书</span>',
                    # TODO: make the simp and trad fields preserve whitespace more reliably by moving away
                    # from Google Translate as the translator. Currently this flips between preserving and
                    # not preserving seemingly nondeterministically!
                    "trad" : "書", "simp" : "书"
                  })
    
    def testDontOverwriteFields(self):
        self.assertEqual(
            self.updatefact("书", { "reading" : "a", "meaning" : "b", "mw" : "c", "audio" : "d", "color" : "e", "trad" : "f", "simp" : "g" },
                colorizedpinyingeneration = True, colorizedcharactergeneration = True, meaninggeneration = True, detectmeasurewords = True,
                tonedisplay = "tonified", meaningnumbering = "circledChinese", meaningseperator = "lines", prefersimptrad = "simp",
                audiogeneration = True, audioextensions = [".mp3"], tonecolors = ["#ff0000", "#ffaa00", "#00aa00", "#0000ff", "#545454"], weblinkgeneration = True,
                tradgeneration = True, simpgeneration = True), {
                    "reading" : "a", "meaning" : "b", "mw" : "c", "audio" : "d", "color" : "e", "trad" : "f", "simp" : "g"
                  })
    
    def testUpdateExpressionItself(self):
        self.assertEqual(
            self.updatefact("啤酒", { "expression" : "" },
                colorizedpinyingeneration = False, colorizedcharactergeneration = False, meaninggeneration = False,
                detectmeasurewords = False, audiogeneration = False, weblinkgeneration = False), { "expression" : "啤酒" })
    
    def testUpdateMeaningAndMWWithoutMWField(self):
        self.assertEqual(
            self.updatefact("啤酒", { "expression" : "", "meaning" : "" },
                colorizedpinyingeneration = False, colorizedcharactergeneration = False, meaninggeneration = True, emphasisemainmeaning = False,
                meaningnumbering = "circledChinese", colormeaningnumbers = False, detectmeasurewords = True, audiogeneration = False, weblinkgeneration = False,
                forceexpressiontobesimptrad = False), {
                    "expression" : "啤酒", "meaning" : "㊀ beer<br />㊁ MW: 杯 - b\u0113i, 瓶 - p\xedng, 罐 - gu\xe0n, 桶 - t\u01d2ng, 缸 - g\u0101ng"
                  })

    def testMeaningHanziMasking(self):
        self.assertEqual(
            self.updatefact("书", { "meaning" : "" },
                colorizedpinyingeneration = True, colorizedcharactergeneration = False, meaninggeneration = True, detectmeasurewords = False, emphasisemainmeaning = False,
                tonedisplay = "tonified", meaningnumbering = "circledArabic", colormeaningnumbers = True, meaningnumberingcolor="#123456", meaningseperator = "custom", custommeaningseperator = " | ", prefersimptrad = "simp",
                audiogeneration = True, audioextensions = [".mp3"], tonecolors = ["#ff0000", "#ffaa00", "#00aa00", "#0000ff", "#545454"], weblinkgeneration = False, hanzimasking = True, hanzimaskingcharacter = "MASKED"), {
                    "meaning" : '<span style="color:#123456">①</span> book | <span style="color:#123456">②</span> letter | <span style="color:#123456">③</span> see also <span style="color:#123456">MASKED</span><span style="color:#ff0000">\u7ecf</span> Book of History | <span style="color:#123456">④</span> MW: <span style="color:#00aa00">本</span> - <span style="color:#00aa00">běn</span>, <span style="color:#0000ff">册</span> - <span style="color:#0000ff">cè</span>, <span style="color:#0000ff">部</span> - <span style="color:#0000ff">bù</span>',
                  })

    def testMeaningSurnameMasking(self):
        self.assertEqual(
            self.updatefact("汪", { "meaning" : "" },
                meaninggeneration = True, meaningnumbering = "arabicParens", colormeaningnumbers = False, meaningseperator = "lines", emphasisemainmeaning = False), {
                    "meaning" : '(1) expanse of water<br />(2) ooze<br />(3) (a surname)',
                  })

    def testMeaningChineseNumbers(self):
        self.assertEqual(self.updatefact("九千零二十五", { "meaning" : "" }, meaninggeneration = True), { "meaning" : '9025' })

    def testMeaningWesternNumbersYear(self):
        self.assertEqual(self.updatefact("2001年", { "meaning" : "" }, meaninggeneration = True), { "meaning" : '2001AD' })

    def testUpdateReadingOnly(self):
        self.assertEqual(
            self.updatefact("啤酒", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "" },
                colorizedpinyingeneration = False, colorizedcharactergeneration = False, meaninggeneration = False,
                detectmeasurewords = False, audiogeneration = False, tonedisplay = "numeric", weblinkgeneration = False), {
                    "reading" : 'pi2 jiu3', "meaning" : "", "mw" : "", "audio" : "", "color" : ""
                  })
    
    def testUpdateReadingAndMeaning(self):
        self.maxDiff = None
        self.assertEqual(
            self.updatefact("㝵", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "", "weblinks" : "" },
                colorizedpinyingeneration = True, colorizedcharactergeneration = False, meaninggeneration = True, detectmeasurewords = False, tonedisplay = "numeric", emphasisemainmeaning = False,
                meaningnumbering = "arabicParens", colormeaningnumbers = True, meaningnumberingcolor = "#123456", meaningseperator = "commas", prefersimptrad = "trad",
                audiogeneration = False, tonecolors = ["#ff0000", "#ffaa00", "#00aa00", "#0000ff", "#545454"], weblinkgeneration = False), {
                    "reading" : '<span style="color:#ffaa00">de2</span>',
                    "meaning" : '<span style="color:#123456">(1)</span> to obtain, <span style="color:#123456">(2)</span> archaic variant of <span style="color:#ffaa00">得</span> - <span style="color:#ffaa00">de2</span>',
                    "mw" : "", "audio" : "", "color" : "", "weblinks" : ""
                  })
    
    def testUpdateReadingAndMeasureWord(self):
        self.assertEqual(
            self.updatefact("丈夫", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "", "weblinks" : "" },
                colorizedpinyingeneration = False, colorizedcharactergeneration = False, meaninggeneration = False, detectmeasurewords = True,
                tonedisplay = "numeric", prefersimptrad = "trad", audiogeneration = False, weblinkgeneration = False), {
                    "reading" : 'zhang4 fu', "meaning" : '',
                    "mw" : "個 - ge4", "audio" : "", "color" : "", "weblinks" : ""
                  })
    
    def testUpdateReadingAndAudio(self):
        self.assertEqual(
            self.updatefact("三七開", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "", "weblinks" : "" },
                colorizedpinyingeneration = False, colorizedcharactergeneration = False, meaninggeneration = False, detectmeasurewords = False,
                tonedisplay = "tonified", audiogeneration = True, audioextensions = [".mp3", ".ogg"], weblinkgeneration = False), {
                    "reading" : 'sān qī kāi', "meaning" : '', "mw" : "",
                    "audio" : "[sound:" + os.path.join("Test", "san1.mp3") + "]" +
                              "[sound:" + os.path.join("Test", "qi1.ogg") + "]" +
                              "[sound:" + os.path.join("Test", "location/Kai1.mp3") + "]",
                    "color" : "", "weblinks" : ""
                  })
    
    def testUpdateReadingAndColoredHanzi(self):
        self.assertEqual(
            self.updatefact("三峽水库", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "", "weblinks" : "" },
                dictlanguage = "pinyin", colorizedpinyingeneration = False, colorizedcharactergeneration = True, meaninggeneration = False, detectmeasurewords = False,
                tonedisplay = "numeric", audiogeneration = False, tonecolors = ["#111111", "#222222", "#333333", "#444444", "#555555"], weblinkgeneration = False), {
                    "reading" : 'san1 xia2 shui3 ku4', "meaning" : '', "mw" : "", "audio" : "",
                    "color" : '<span style="color:#111111">三</span><span style="color:#222222">峽</span><span style="color:#333333">水</span><span style="color:#444444">库</span>', "weblinks" : ""
                  })
    
    def testUpdateReadingAndLinks(self):
        self.assertEqual(
            self.updatefact("一概", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "", "weblinks" : "Yes, I get overwritten!" },
                colorizedpinyingeneration = False, colorizedcharactergeneration = False, meaninggeneration = False, detectmeasurewords = False,
                tonedisplay = "numeric", audiogeneration = False, tonecolors = ["#111111", "#222222", "#333333", "#444444", "#555555"],
                weblinkgeneration = True, weblinks = [("YEAH!", "mytitle", "silly{searchTerms}url"), ("NAY!", "myothertitle", "verysilly{searchTerms}url")]), {
                    "reading" : 'yi1 gai4', "meaning" : '', "mw" : "", "audio" : "", "color" : '',
                    "weblinks" : '[<a href="silly%E4%B8%80%E6%A6%82url" title="mytitle">YEAH!</a>] [<a href="verysilly%E4%B8%80%E6%A6%82url" title="myothertitle">NAY!</a>]'
                  })

    def testWebLinkFieldCanBeMissingAndStaysMissing(self):
        self.assertEqual(self.updatefact("一概", { }, weblinkgeneration = True), { })
    
    def testWebLinksNotBlankedIfDisabled(self):
        self.assertEqual(self.updatefact("一概", { "weblinks": "Nope!" }, weblinkgeneration = False), { "weblinks" : "Nope!" })
    
    def testReadingFromWesternNumbers(self):
        self.assertEqual(self.updatefact("111", { "reading" : "" }, colorizedpinyingeneration = True, tonecolors = ["#111111", "#222222", "#333333", "#444444", "#555555"]),
                                                  { "reading" : '<span style="color:#333333">b\u01cei</span> <span style="color:#111111">y\u012b</span> <span style="color:#222222">sh\xed</span> <span style="color:#111111">y\u012b</span>' })
    
    def testNotifiedUponAudioGenerationWithNoPacks(self):
        infos, fact = self.updatefactwithinfos("三月", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "" },
                            mediapacks = [],
                            colorizedpinyingeneration = False, colorizedcharactergeneration = False, meaninggeneration = False, detectmeasurewords = False,
                            tonedisplay = "numeric", audiogeneration = True)
        
        self.assertEqual(fact, { "reading" : 'san1 yue4', "meaning" : '', "mw" : "", "audio" : "", "color" : "" })
        self.assertEqual(len(infos), 1)
        self.assertTrue("cannot" in infos[0])
    
    def testUpdateMeasureWordAudio(self):
        quantitydigitpinyin = ["yi1", "liang3", "liang2", "san1", "si4", "wu3", "wu2", "liu4", "qi1", "ba1", "jiu3", "jiu2", "ji3", "ji2"]
        allpinyin = quantitydigitpinyin + ["pi2", "bei1", "ping2", "guan4", "tong3", "tong2", "gang1"]
        
        pack = media.MediaPack("MWAudio", dict([(pinyin + ".mp3", pinyin + ".mp3") for pinyin in allpinyin]))
        
        # NB: turning off meaninggeneration here triggers a bug that happened in 0.6 where
        # we wouldn't set up the dictmeasurewords for the mwaudio
        mwaudio = self.updatefact("啤酒", { "mwaudio" : "" }, meaninggeneration = False, detectmeasurewords = False, mwaudiogeneration = True, audioextensions = [".mp3", ".ogg"], mediapacks = [pack])["mwaudio"]
        for quantitydigit in quantitydigitpinyin:
            mwaudio = mwaudio.replace(quantitydigit, "X")
        
        # jiu3 in the numbers aliases with jiu3 in the characters :(
        sounds = ["X", "bei1", "pi2", "X",
                  "X", "ping2", "pi2", "X",
                  "X", "guan4", "pi2", "X",
                  "X", "tong3", "pi2", "X",
                  "X", "gang1", "pi2", "X"]
        self.assertEqual(mwaudio, "".join(["[sound:" + os.path.join("MWAudio", sound + ".mp3") + "]" for sound in sounds]))

    def testFallBackOnGoogleForPhrase(self):
        self.assertEqual(
            self.updatefact("你好，你是我的朋友吗", { "reading" : "", "meaning" : "", "mw" : "", "audio" : "", "color" : "" },
                fallbackongoogletranslate = True,
                colorizedpinyingeneration = False, colorizedcharactergeneration = False, meaninggeneration = True, detectmeasurewords = False,
                tonedisplay = "numeric", audiogeneration = False, hanzimasking = False), {
                    "reading" : 'ni3 hao3, ni3 shi4 wo3 de peng2 you ma',
                    "meaning" : 'Hello, you\'re my friend.<br /><span style="color:gray"><small>[Google Translate]</small></span><span> </span>',
                    "mw" : "", "audio" : "", "color" : ""
                  })

    def testUpdateSimplifiedTraditional(self):
        self.assertEqual(
            self.updatefact("个個", { "simp" : "", "trad" : "" },
                simpgeneration = True, tradgeneration = True), {
                    "simp"  : "个个",
                    "trad" : "個個"
                  })

    def testUpdateSimplifiedTraditionalDoesNothingIfSimpTradIdentical(self):
        self.assertEqual(
            self.updatefact("鼠", { "simp" : "", "trad" : "" }, simpgeneration = True, tradgeneration = True), { "simp"  : "", "trad" : "" })

    def testOverwriteExpressionWithSimpTrad(self):
        self.assertEqual(self.updatefact("个個", { "expression" : "" }, forceexpressiontobesimptrad = True, prefersimptrad = "trad"),
                                                 { "expression"  : "個個" })

        self.assertEqual(self.updatefact("个個", { "expression" : "" }, forceexpressiontobesimptrad = True, prefersimptrad = "simp"),
                                                 { "expression"  : "个个" })

    def testOverwriteExpressionWithSimpTradEvenWorksIfFieldFilled(self):
        self.assertEqual(self.updatefact("个個", { "expression" : "I'm Filled!" }, forceexpressiontobesimptrad = True, prefersimptrad = "trad"),
                                                 { "expression"  : "個個" })

    def testOverwriteExpressionWithSimpTradCausesColoredCharsToUpdateEvenIfFilled(self):
        self.assertEqual(
            self.updatefact("个個", { "expression" : "I'm Filled!", "color" : "dummy" },
                            forceexpressiontobesimptrad = True, prefersimptrad = "trad", tonecolors = ["#111111", "#222222", "#333333", "#444444", "#555555"]),
                            { "expression"  : "個個", "color" : '<span style="color:#444444">個</span><span style="color:#444444">個</span>' })

    def testDontOverwriteFilledColoredCharactersIfSimpTradDoesntChange(self):
        self.assertEqual(
            self.updatefact("個個", { "expression" : "I'm Filled!", "color" : "dummy" },
                            forceexpressiontobesimptrad = True, prefersimptrad = "trad", tonecolors = ["#111111", "#222222", "#333333", "#444444", "#555555"]),
                            { "expression"  : "個個", "color" : "dummy" })

    def testUpdateReadingAndColoredHanziAndAudioWithSandhi(self):
        self.assertEqual(
            self.updatefact("很好", { "reading" : "", "color" : "", "audio" : "" },
                colorizedpinyingeneration = True, colorizedcharactergeneration = True, meaninggeneration = False,
                detectmeasurewords = False, audiogeneration = True, audioextensions = [".mp3"], tonedisplay = "numeric",
                tonecolors = ["#ff0000", "#ffaa00", "#00aa00", "#0000ff", "#545454"], weblinkgeneration = False), {
                    "reading" : '<span style="color:#66cc66">hen3</span> <span style="color:#00aa00">hao3</span>',
                    "color" : '<span style="color:#66cc66">很</span><span style="color:#00aa00">好</span>',
                    "audio" : "[sound:" + os.path.join("Test", "hen2.mp3") + "]" +
                              "[sound:" + os.path.join("Test", "hao3.mp3") + "]"
                  })
    
    # Test helpers
    def updatefact(self, *args, **kwargs):
        infos, fact = self.updatefactwithinfos(*args, **kwargs)
        return fact
    
    def updatefactwithinfos(self, expression, fact, mediapacks = None, **kwargs):
        notifier = MockNotifier()
        
        if mediapacks == None:
            mediapacks = [media.MediaPack("Test", { "shu1.mp3" : "shu1.mp3", "shu1.ogg" : "shu1.ogg",
                                                    "san1.mp3" : "san1.mp3", "qi1.ogg" : "qi1.ogg", "Kai1.mp3" : "location/Kai1.mp3",
                                                    "hen3.mp3" : "hen3.mp3", "hen2.mp3" : "hen2.mp3", "hao3.mp3" : "hao3.mp3" })]
        mediamanager = MockMediaManager(mediapacks)
        
        factclone = copy.deepcopy(fact)
        FieldUpdaterFromExpression(notifier, mediamanager, Config(utils.updated({ "dictlanguage" : "en" }, kwargs))).updatefact(factclone, expression)
        
        return notifier.infos, factclone

if __name__ == '__main__':
    unittest.main()

