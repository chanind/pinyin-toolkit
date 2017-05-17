# -*- coding: utf-8 -*-

import unittest

from pinyin.config import *


class ConfigTest(unittest.TestCase):
    def testAttribute(self):
        self.assertEqual(Config({ "tonedisplay" : "value" }).tonedisplay, "value")
    
    def testIndexedAttribute(self):
        self.assertEqual(Config({ "tonecolors" : ["100"] }).tonecolors[0], "100")

    def testMissingAttribute(self):
        self.assertRaises(AttributeError, lambda: Config({ "key" : ["value"] }).kay)
    
    def testNonExistentKeysDiscarded(self):
        self.assertRaises(AttributeError, lambda: Config({ "idontexist" : "value" }).idontexist)
    
    def testNonExistentFieldNamesDiscarded(self):
        self.assertRaises(KeyError, lambda: Config({ "candidateFieldNamesByKey" : { "silly" : ["Fish"] } }).candidateFieldNamesByKey["silly"])
    
    def testPositionalListLengthNotChanged(self):
        config = Config({ "tonecolors" : ["hi"] })
        self.assertEqual(config.tonecolors[0], "hi")
        self.assertEqual(len(config.tonecolors), len(Config({}).tonecolors))
    
    def testCopiesInput(self):
        inputSettings = {}
        
        config = Config(inputSettings)
        config.dictlanguage = "foobar"
        
        self.assertEqual(inputSettings, {})
    
    def testDeepCopiesInput(self):
        inputSettings = { "dictlanguage" : [["deep!"]] }
        
        config = Config(inputSettings)
        config.dictlanguage[0][0] = "changed :("
        
        self.assertEqual(inputSettings, { "dictlanguage" : [["deep!"]] })

    def testNoUserSettings(self):
        self.assertNotEqual(Config(None).dictlanguage, None)
    
    def testSupplyDefaultSettings(self):
        self.assertNotEqual(Config({}).dictlanguage, None)
    
    def testDontOverwriteSuppliedSettings(self):
        self.assertEqual(Config({ "dictlanguage" : "foobar" }).dictlanguage, "foobar")
    
    def testPrivateStuffStaysPrivate(self):
        for key in list(Config({}).settings.keys()):
            self.assertFalse("__" in key, "Private stuff called %s leaked" % key)
    
    def testTonified(self):
        self.assertTrue(Config({ "tonedisplay" : "tonified" }).shouldtonify)
        self.assertFalse(Config({ "tonedisplay" : "numeric" }).shouldtonify)
    
    def testNeedMeanings(self):
        def row(mg, dmw, mwag, res):
            self.assertEqual(Config({ "meaninggeneration" : mg, "detectmeasurewords" : dmw, "mwaudiogeneration" : mwag }).needmeanings, res)
        
        row(True, True, True, True)
        row(True, True, False, True)
        row(True, False, True, True)
        row(True, False, False, True)
        row(False, True, True, True)
        row(False, True, False, True)
        row(False, False, True, True)
        row(False, False, False, False)
    
    def testMeaningNumber(self):
        self.assertEqual([Config({ "meaningnumbering" : "arabicParens", "colormeaningnumbers" : False, "emphasisemainmeaning" : False }).meaningnumber(n) for n in [2, 10, 21]],
                          ["(2)", "(10)", "(21)"])
        self.assertEqual([Config({ "meaningnumbering" : "circledChinese", "colormeaningnumbers" : False, "emphasisemainmeaning" : False }).meaningnumber(n) for n in [2, 10, 21]],
                          ["㊁", "㊉", "(21)"])
        self.assertEqual([Config({ "meaningnumbering" : "circledArabic", "colormeaningnumbers" : False, "emphasisemainmeaning" : False }).meaningnumber(n) for n in [2, 10, 21]],
                          ["②", "⑩", "(21)"])
        self.assertEqual([Config({ "meaningnumbering" : "none", "colormeaningnumbers" : False, "emphasisemainmeaning" : False }).meaningnumber(n) for n in [2, 10, 21]],
                          ["", "", ""])
        self.assertEqual([Config({ "meaningnumbering" : "arabicParens", "colormeaningnumbers" : True, "meaningnumberingcolor" : "#aabbcc", "emphasisemainmeaning" : False }).meaningnumber(n) for n in [2, 10, 21]],
                          ['<span style="color:#aabbcc">(2)</span>', '<span style="color:#aabbcc">(10)</span>', '<span style="color:#aabbcc">(21)</span>'])

    def testFormatMeaningsOptions(self):
        self.assertEqual(Config({ "meaningnumbering" : "arabicParens", "meaningseperator" : "lines", "colormeaningnumbers" : False, "emphasisemainmeaning" : False }).formatmeanings(["a", "b"]),
                          "(1) a<br />(2) b")
        self.assertEqual(Config({ "meaningnumbering" : "circledChinese", "meaningseperator" : "commas", "colormeaningnumbers" : False, "emphasisemainmeaning" : False }).formatmeanings(["a", "b"]),
                          "㊀ a, ㊁ b")
        self.assertEqual(Config({ "meaningnumbering" : "circledArabic", "meaningseperator" : "custom", "custommeaningseperator" : " | ", "colormeaningnumbers" : False, "emphasisemainmeaning" : False }).formatmeanings(["a", "b"]),
                          "① a | ② b")
        self.assertEqual(Config({ "meaningnumbering" : "none", "meaningseperator" : "custom", "custommeaningseperator" : " ^_^ ", "colormeaningnumbers" : False, "emphasisemainmeaning" : False }).formatmeanings(["a", "b"]),
                          "a ^_^ b")
        self.assertEqual(Config({ "meaningnumbering" : "arabicParens", "meaningseperator" : "lines", "colormeaningnumbers" : True, "meaningnumberingcolor" : "#aabbcc", "emphasisemainmeaning" : False }).formatmeanings(["a", "b"]),
                        '<span style="color:#aabbcc">(1)</span> a<br /><span style="color:#aabbcc">(2)</span> b')
    
    def testFormatMeaningsSingleMeaning(self):
        self.assertEqual(Config({ "meaningnumbering" : "arabicParens", "meaningseperator" : "lines", "emphasisemainmeaning" : False }).formatmeanings(["a"]), "a")
    
    def testFormatTooManyMeanings(self):
        self.assertEqual(Config({ "meaningnumbering" : "circledChinese", "meaningseperator" : "commas", "colormeaningnumbers" : False, "emphasisemainmeaning" : False }).formatmeanings([str(n) for n in range(1, 22)]),
                          "㊀ 1, ㊁ 2, ㊂ 3, ㊃ 4, ㊄ 5, ㊅ 6, ㊆ 7, ㊇ 8, ㊈ 9, ㊉ 10, ⑪ 11, ⑫ 12, ⑬ 13, ⑭ 14, ⑮ 15, ⑯ 16, ⑰ 17, ⑱ 18, ⑲ 19, ⑳ 20, (21) 21")

    def testFormatMeaningsWithEmphasis(self):
        self.assertEqual(Config({ "meaningnumbering" : "circledChinese", "meaningseperator" : "commas", "colormeaningnumbers" : False,
                                   "emphasisemainmeaning" : True, "mainmeaningemphasistag" : "br/" }).formatmeanings(["a", "b", "c"]),
                          "a, <br />㊁ b, ㊂ c")
        self.assertEqual(Config({ "meaningnumbering" : "none", "meaningseperator" : "custom", "custommeaningseperator" : " ^_^ ", "colormeaningnumbers" : False,
                                   "emphasisemainmeaning" : True, "mainmeaningemphasistag" : "small" }).formatmeanings(["a", "b", "c", "d"]),
                          "a ^_^ <small>b ^_^ c ^_^ d</small>")
        self.assertEqual(Config({ "meaningnumbering" : "arabicParens", "meaningseperator" : "lines", "colormeaningnumbers" : True, "meaningnumberingcolor" : "#aabbcc",
                                   "emphasisemainmeaning" : True, "mainmeaningemphasistag" : "mehhh/" }).formatmeanings(["a", "b", "c"]),
                          'a<br /><mehhh /><span style="color:#aabbcc">(2)</span> b<br /><span style="color:#aabbcc">(3)</span> c')
    
    def testFormatMeaningsWithEmphasisSingleNonMainMeaning(self):
        self.assertEqual(Config({ "meaningnumbering" : "arabicParens", "meaningseperator" : "commas", "colormeaningnumbers" : False,
                                   "emphasisemainmeaning" : True, "mainmeaningemphasistag" : "br/" }).formatmeanings(["a", "b"]),
                          "a, <br />b")
    
    def testFormatMeaningsWithEmphasisSingleMeaning(self):
        self.assertEqual(Config({ "meaningnumbering" : "arabicParens", "meaningseperator" : "commas", "colormeaningnumbers" : False,
                                   "emphasisemainmeaning" : True, "mainmeaningemphasistag" : "br/" }).formatmeanings(["a"]),
                          "a")

    def testFormatHanziMaskingCharacter(self):
        self.assertEqual(Config({ "hanzimasking" : True, "hanzimaskingcharacter": "MASKED", "colormeaningnumbers" : True, "meaningnumberingcolor" : "#abcdef", "emphasisemainmeaning" : False }).formathanzimaskingcharacter(),
                          '<span style="color:#abcdef">MASKED</span>')
        self.assertEqual(Config({ "hanzimasking" : True, "hanzimaskingcharacter": "MASKED", "colormeaningnumbers" : False, "emphasisemainmeaning" : False }).formathanzimaskingcharacter(),
                          'MASKED')

    def testShouldUseGoogleTranslateDontUse(self):
        self.assertFalse(Config({ "fallbackongoogletranslate" : False }).shouldusegoogletranslate)
        
    def testShouldUseGoogleTranslateShouldUse(self):
        self.assertTrue(Config({ "fallbackongoogletranslate" : True }).shouldusegoogletranslate)

    def testPickle(self):
        import pickle
        config = Config({ "setting" : "value", "cheese" : "mice" })
        self.assertEqual(pickle.loads(pickle.dumps(config)).settings, config.settings)

    def testPersist(self):
        # clean up persisted settings are here remove first
        if (os.path.exists(SETTINGS_FILE)):
            os.unlink(SETTINGS_FILE)

        config = getconfig()
        self.assertEqual("simp", config.prefersimptrad)
        self.assertEqual("en", config.dictlanguage)

        config.prefersimptrad = "trad"
        config.dictlanguage = "fr"
        saveconfig()
        
        config = getconfig()
        self.assertEqual("trad", config.prefersimptrad)
        self.assertEqual("fr", config.dictlanguage)

        # clean up persisted settings
        os.unlink(SETTINGS_FILE)


if __name__ == '__main__':
    unittest.main()
