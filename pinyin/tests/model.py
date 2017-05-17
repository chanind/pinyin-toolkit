# -*- coding: utf-8 -*-

import unittest

from pinyin.model import *


class ToneInfoTest(unittest.TestCase):
    def testAccessors(self):
        ti = ToneInfo(written=1, spoken=2)
        self.assertEqual(ti.written, 1)
        self.assertEqual(ti.spoken, 2)
    
    def testRepr(self):
        self.assertEqual(repr(ToneInfo(written=1, spoken=2)), "ToneInfo(written=1, spoken=2)")
    
    def testDefaulting(self):
        self.assertEqual(ToneInfo(written=1), ToneInfo(written=1, spoken=1))
        self.assertEqual(ToneInfo(spoken=1), ToneInfo(written=1, spoken=1))
    
    def testEq(self):
        self.assertEqual(ToneInfo(written=1, spoken=3), ToneInfo(written=1, spoken=3))
        self.assertNotEqual(ToneInfo(written=1, spoken=3), ToneInfo(written=2, spoken=3))
        self.assertNotEqual(ToneInfo(written=1, spoken=3), ToneInfo(written=1, spoken=5))
    
    def testEqDissimilar(self):
        self.assertNotEqual(ToneInfo(written=1, spoken=3), "ToneInfo(written=1, spoken=3)")
        self.assertNotEqual("ToneInfo(written=1, spoken=3)", ToneInfo(written=1, spoken=3))

    def testMustBeNonEmpty(self):
        self.assertRaises(ValueError, lambda: ToneInfo())

class PinyinTest(unittest.TestCase):
    def testConvenienceConstructor(self):
        self.assertEqual(Pinyin("hen", 3), Pinyin("hen", ToneInfo(written=3)))
    
    def testUnicode(self):
        self.assertEqual(str(Pinyin("hen", 3)), "hen3")
    
    def testStr(self):
        self.assertEqual(str(Pinyin("hen", 3)), "hen3")
    
    def testRepr(self):
        self.assertEqual(repr(Pinyin("hen", 3)), "Pinyin(u'hen', ToneInfo(written=3, spoken=3))")
        self.assertEqual(repr(Pinyin("hen", 3, { "attr" : "val" })), "Pinyin(u'hen', ToneInfo(written=3, spoken=3), {'attr': 'val'})")
    
    def testEq(self):
        self.assertEqual(Pinyin("hen", 3), Pinyin("hen", 3))
        self.assertEqual(Pinyin("hen", 3, { "moo" : "cow" }), Pinyin("hen", 3, { "moo" : "cow" }))
        self.assertNotEqual(Pinyin("hen", 3), Pinyin("hen", 2))
        self.assertNotEqual(Pinyin("hen", 3), Pinyin("han", 3))
        self.assertNotEqual(Pinyin("hen", 3), Pinyin("hen", 3, { "moo" : "cow" }))
        self.assertNotEqual(Pinyin("hen", 3, { "moo" : "cow" }), Pinyin("hen", 3, { "moo" : "sheep" }))
    
    def testEqDissimilar(self):
        self.assertNotEqual(Pinyin("hen", 3), "Pinyin(u'hen', 3)")
        self.assertNotEqual("Pinyin(u'hen', 3)", Pinyin("hen", 3))
    
    def testStrNeutralTone(self):
        py = Pinyin("ma", 5)
        self.assertEqual(str(py), "ma")
    
    def testNumericFormat(self):
        self.assertEqual(Pinyin("hen", 3).numericformat(), "hen3")
    
    def testNumericFormatSelectTone(self):
        self.assertEqual(Pinyin("hen", ToneInfo(written=1, spoken=2)).numericformat(tone="written"), "hen1")
        self.assertEqual(Pinyin("hen", ToneInfo(written=1, spoken=2)).numericformat(tone="spoken"), "hen2")
        
    def testNumericFormatNeutralTone(self):
        self.assertEqual(Pinyin("ma", 5).numericformat(), "ma5")
        self.assertEqual(Pinyin("ma", 5).numericformat(hideneutraltone=True), "ma")
    
    def testTonifiedFormat(self):
        self.assertEqual(Pinyin("hen", 3).tonifiedformat(), "hěn")
    
    def testTonifiedFormatNeutralTone(self):
        self.assertEqual(Pinyin("ma", 5).tonifiedformat(), "ma")
    
    def testIsEr(self):
        self.assertTrue(Pinyin("r", 5).iser)
        self.assertTrue(Pinyin("R", 5).iser)
        self.assertFalse(Pinyin("r", 4).iser)
        self.assertFalse(Pinyin("er", 5).iser)
    
    def testParse(self):
        self.assertEqual(Pinyin.parse("ma1"), Pinyin("ma", 1))
        self.assertEqual(Pinyin.parse("ma2"), Pinyin("ma", 2))
        self.assertEqual(Pinyin.parse("ma3"), Pinyin("ma", 3))
        self.assertEqual(Pinyin.parse("ma4"), Pinyin("ma", 4))
        self.assertEqual(Pinyin.parse("ma5"), Pinyin("ma", 5))
    
    def testParseAdditions(self):
        self.assertEqual(Pinyin.parse("er5"), Pinyin("er", 5))
        self.assertEqual(Pinyin.parse("r2"), Pinyin("r", 2))
    
    def testParseShort(self):
        self.assertEqual(Pinyin.parse("a1"), Pinyin("a", 1))
    
    def testParseLong(self):
        self.assertEqual(Pinyin.parse("zhuang1"), Pinyin("zhuang", 1))
    
    def testParseNormalisesUmlaut(self):
        self.assertEqual(Pinyin.parse("nu:3"), Pinyin.parse("nü3"))
        self.assertEqual(Pinyin.parse("nU:3"), Pinyin.parse("nÜ3"))
        self.assertEqual(Pinyin.parse("nv3"), Pinyin.parse("nü3"))
        self.assertEqual(Pinyin.parse("nV3"), Pinyin.parse("nÜ3"))
    
    def testParseTonified(self):
        self.assertEqual(Pinyin.parse("chi1"), Pinyin.parse("chī"))
        self.assertEqual(Pinyin.parse("shi2"), Pinyin.parse("shí"))
        self.assertEqual(Pinyin.parse("xiao3"), Pinyin.parse("xiǎo"))
        self.assertEqual(Pinyin.parse("dan4"), Pinyin.parse("dàn"))
        self.assertEqual(Pinyin.parse("huan"), Pinyin.parse("huan"))
    
    def testParseRespectsOtherCombiningMarks(self):
        self.assertEqual("nü", str(Pinyin.parse("nü5")))
        self.assertEqual("nü", str(Pinyin.parse("nü")))
    
    def testParseForceNumeric(self):
        Pinyin.parse("chi")
        self.assertRaises(ValueError, lambda: Pinyin.parse("chi", forcenumeric=True))
    
    def testParseUnicode(self):
        self.assertEqual(repr(Pinyin.parse("nü3")), "Pinyin(u'n\\xfc', ToneInfo(written=3, spoken=3))")
    
    def testParseAlternativeUUmlaut(self):
        self.assertEqual(Pinyin.parse("nü3"), Pinyin.parse("nu:3"))
        self.assertEqual(Pinyin.parse("nü3"), Pinyin.parse("nv3"))
        self.assertEqual(Pinyin.parse("lü3"), Pinyin.parse("lu:3"))
    
    # Bug #138 - kind of a relic of when we used a regex to recognise pinyin
    def testParsesXiong(self):
        self.assertEqual(Pinyin.parse("xiong1"), Pinyin("xiong", 1))
    
    def testRejectsPinyinWithMultipleToneMarks(self):
        self.assertRaises(ValueError, lambda: Pinyin.parse("xíǎo"))
    
    def testRejectsSingleNumbers(self):
        self.assertRaises(ValueError, lambda: Pinyin.parse("1"))
    
    def testRejectsNumbers(self):
        self.assertRaises(ValueError, lambda: Pinyin.parse("12345"))
    
    def testRejectsPinyinlikeEnglish(self):
        self.assertRaises(ValueError, lambda: Pinyin.parse("USB"))

class TextTest(unittest.TestCase):
    def testNonEmpty(self):
        self.assertRaises(ValueError, lambda: Text(""))
    
    def testRepr(self):
        self.assertEqual(repr(Text("hello")), "Text(u'hello')")
        self.assertEqual(repr(Text("hello", { "china" : "great" })), "Text(u'hello', {'china': 'great'})")
    
    def testUnicodeAndStr(self):
        self.assertEqual(str(Text("hello")), "hello")
        self.assertEqual(str(Text("hello")), "hello")
        self.assertEqual(type(str(Text("hello"))), str)
    
    def testEq(self):
        self.assertEqual(Text("hello"), Text("hello"))
        self.assertEqual(Text("hello", { "color" : "mah" }), Text("hello", { "color" : "mah" }))
        self.assertNotEqual(Text("hello"), Text("bye"))
        self.assertNotEqual(Text("hello", { "color" : "mah" }), Text("hello"))
        self.assertNotEqual(Text("hello", { "color" : "mah" }), Text("hello", { "color" : "meh" }))
    
    def testEqDissimilar(self):
        self.assertNotEqual(Text("hello"), 'Text(u"hello")')
        self.assertNotEqual('Text(u"hello")', Text("hello"))
    
    def testIsEr(self):
        self.assertFalse(Text("r5").iser)

class WordTest(unittest.TestCase):
    def testAppendSingleReading(self):
        self.assertEqual(flatten([Word.spacedwordfromunspacedtokens([Pinyin.parse("hen3")])]), "hen3")

    def testAppendMultipleReadings(self):
        self.assertEqual(flatten([Word.spacedwordfromunspacedtokens([Pinyin.parse("hen3"), Pinyin.parse("ma5")])]), "hen3 ma")
    
    def testAppendSingleReadingErhua(self):
        self.assertEqual(flatten([Word.spacedwordfromunspacedtokens([Pinyin.parse("r5")])]), "r")

    def testAppendMultipleReadingsErhua(self):
        self.assertEqual(flatten([Word.spacedwordfromunspacedtokens([Pinyin.parse("hen3"), Pinyin.parse("ma5"), Pinyin.parse("r5")])]), "hen3 mar")
    
    def testEquality(self):
        self.assertEqual(Word(Text("hello")), Word(Text("hello")))
        self.assertNotEqual(Word(Text("hello")), Word(Text("hallo")))
    
    def testRepr(self):
        self.assertEqual(repr(Word(Text("hello"))), "Word(Text(u'hello'))")
    
    def testStr(self):
        self.assertEqual(str(Word(Text("hello"))), "<hello>")
        self.assertEqual(str(Word(Text("hello"))), "<hello>")
        
    def testFilterNones(self):
        self.assertEqual(Word(None, Text("yes"), None, Text("no")), Word(Text("yes"), Text("no")))
    
    def testAppendNoneFiltered(self):
        word = Word(Text("yes"), Text("no"))
        word.append(None)
        self.assertEqual(word, Word(Text("yes"), Text("no")))
    
    def testAccept(self):
        output = []
        class Visitor(object):
            def visitText(self, text):
                output.append(text)
            
            def visitPinyin(self, pinyin):
                output.append(pinyin)
            
            def visitTonedCharacter(self, tonedcharacter):
                output.append(tonedcharacter)
        
        Word(Text("Hi"), Pinyin.parse("hen3"), TonedCharacter("a", 2), Text("Bye")).accept(Visitor())
        self.assertEqual(output, [Text("Hi"), Pinyin.parse("hen3"), TonedCharacter("a", 2), Text("Bye")])
    
    def testMap(self):
        class Visitor(object):
            def visitText(self, text):
                return Text("MEH")
            
            def visitPinyin(self, pinyin):
                return Pinyin.parse("hai3")
            
            def visitTonedCharacter(self, tonedcharacter):
                return TonedCharacter("M", 2)
        
        self.assertEqual(Word(Text("Hi"), Pinyin.parse("hen3"), TonedCharacter("a", 2), Text("Bye")).map(Visitor()),
                         Word(Text("MEH"), Pinyin.parse("hai3"), TonedCharacter("M", 2), Text("MEH")))
    
    def testConcatMap(self):
        class Visitor(object):
            def visitText(self, text):
                return []
            
            def visitPinyin(self, pinyin):
                return [pinyin, pinyin]
            
            def visitTonedCharacter(self, tonedcharacter):
                return [TonedCharacter("M", 2)]
        
        self.assertEqual(Word(Text("Hi"), Pinyin.parse("hen3"), TonedCharacter("a", 2), Text("Bye")).concatmap(Visitor()),
                         Word(Pinyin.parse("hen3"), Pinyin.parse("hen3"), TonedCharacter("M", 2)))

class TonedCharacterTest(unittest.TestCase):
    def testConvenienceConstructor(self):
        self.assertEqual(TonedCharacter("儿", 2), TonedCharacter("儿", ToneInfo(written=2)))
    
    def testRepr(self):
        self.assertEqual(repr(TonedCharacter("儿", 2)), "TonedCharacter(u'\\u513f', ToneInfo(written=2, spoken=2))")
        self.assertEqual(repr(TonedCharacter("儿", ToneInfo(written=2, spoken=3), { "foo" : "bar" })), "TonedCharacter(u'\\u513f', ToneInfo(written=2, spoken=3), {'foo': 'bar'})")
    
    def testEq(self):
        self.assertEqual(TonedCharacter("儿", 2), TonedCharacter("儿", 2))
        self.assertEqual(TonedCharacter("儿", 2, { "color" : "meh" }), TonedCharacter("儿", 2, { "color" : "meh" }))
        self.assertNotEqual(TonedCharacter("儿", 2), TonedCharacter("儿", 3))
        self.assertNotEqual(TonedCharacter("儿", 2), TonedCharacter("兒", 2))
        self.assertNotEqual(TonedCharacter("儿", 2), TonedCharacter("儿", 2, { "foo" : "bar" }))
        self.assertNotEqual(TonedCharacter("儿", 2, { "color" : "moo" }), TonedCharacter("儿", 2, { "color" : "meh" }))
    
    def testEqDissimilar(self):
        self.assertNotEqual(TonedCharacter("儿", 2), "TonedCharacter(u'儿', 2)")
        self.assertNotEqual("TonedCharacter(u'儿', 2)", TonedCharacter("儿", 2))
    
    def testIsEr(self):
        self.assertTrue(TonedCharacter("儿", 5).iser)
        self.assertTrue(TonedCharacter("兒", 5).iser)
        self.assertFalse(TonedCharacter("化", 2).iser)
        self.assertFalse(TonedCharacter("儿", 4).iser)

class TokenizeSpaceSeperatedTextTest(unittest.TestCase):
    def testFromSingleSpacedString(self):
        self.assertEqual([Pinyin.parse("hen3")], tokenizespaceseperatedtext("hen3"))

    def testFromMultipleSpacedString(self):
        self.assertEqual([Pinyin.parse("hen3"), Pinyin.parse("hao3")], tokenizespaceseperatedtext("hen3 hao3"))

    def testFromSpacedStringWithEnglish(self):
        self.assertEqual([Text("T"), Pinyin.parse("xu4")], tokenizespaceseperatedtext("T xu4"))

    def testFromSpacedStringWithPinyinlikeEnglish(self):
        self.assertEqual([Text("USB"), Pinyin.parse("xu4")], tokenizespaceseperatedtext("USB xu4"))

class TokenizeTest(unittest.TestCase):
    def testTokenizeSimple(self):
        self.assertEqual([Pinyin.parse("hen3"), Text(" "), Pinyin.parse("hao3")], tokenize("hen3 hao3"))
        self.assertEqual([Pinyin.parse("hen3"), Text(","), Pinyin.parse("hao3")], tokenize("hen3,hao3"))
        self.assertEqual([Pinyin.parse("hen3"), Text(" "), Pinyin.parse("hao3"), Text(", "), Text("my"), Text(" "), Pinyin.parse("xiǎo"), Text(" "), Text("one"), Text("!")],
                          tokenize("hen3 hao3, my xiǎo one!"))
    
    def testTokenizeUUmlaut(self):
        self.assertEqual([Pinyin.parse("lu:3")], tokenize("lu:3"))
    
    def testTokenizeErhua(self):
        self.assertEqual([Pinyin.parse("wan4"), Pinyin("r", 5)], tokenize("wan4r"))
        self.assertEqual([Text("color")], tokenize("color"))
    
    def testTokenizeForceNumeric(self):
        self.assertEqual([Pinyin.parse("hen3"), Text(" "), Pinyin.parse("hao3")], tokenize("hen3 hao3"))
        self.assertEqual([Pinyin.parse("hen3"), Text(" "), Pinyin.parse("hao3"), Text(", "), Text("my"), Text(" "), Text("xiǎo"), Text(" "), Text("one"), Text("!")],
                           tokenize("hen3 hao3, my xiǎo one!", forcenumeric=True))
    
    def testTokenizeHTML(self):
        self.assertEqual([Text('<b>'), Text("some"), Text(" "), Text("silly"), Text(" "), Text("text"), Text("</b>")],
                          tokenize('<b>some silly text</b>'))
        self.assertEqual([Text('<span style="">'), Pinyin('tou', 2, { "color" : "#123456" }), Text('</span>'), Text(' '), Text('<span style="">'), Pinyin('er', 4, { "color" : "#123456" }), Text('</span>')],
                          tokenize('<span style="color:#123456">tou2</span> <span style="color:#123456">er4</span>'))
    
    def testTokenizeUnrecognisedHTML(self):
        # TODO: enable this test and make it pass somehow... SGMLParser doesn't support self-closing tags :-(
        #self.assertEquals([Text(u'<b />')], tokenize(u'<b />'))
        self.assertEqual([Text('<span style="mehhhh!">'), Text("</span>")], tokenize('<span style="mehhhh!"></span>'))
        
class PinyinTonifierTest(unittest.TestCase):
    def testEasy(self):
        self.assertEqual(PinyinTonifier().tonify("Han4zi4 bu4 mie4, Zhong1guo2 bi4 wang2!"),
                          "Hànzì bù miè, Zhōngguó bì wáng!")

    def testObscure(self):
        self.assertEqual(PinyinTonifier().tonify("huai4"), "huài")

    def testUpperCase(self):
        self.assertEqual(PinyinTonifier().tonify("Huai4"), "Huài")
        self.assertEqual(PinyinTonifier().tonify("An1 hui1 sheng3"), "Ān huī shěng")
    
    def testGreeting(self):
        self.assertEqual(PinyinTonifier().tonify("ni3 hao3, wo3 xi3 huan xue2 xi2 Han4 yu3. wo3 de Han4 yu3 shui3 ping2 hen3 di1."),
                          "nǐ hǎo, wǒ xǐ huan xué xí Hàn yǔ. wǒ de Hàn yǔ shuǐ píng hěn dī.")

class FlattenTest(unittest.TestCase):
    def testFlatten(self):
        self.assertEqual(flatten([Word(Text('a ')), Word(Pinyin.parse("hen3"), Text(' b')), Word(Text("junk")), Word(Pinyin.parse("ma5"))]),
                          "a hen3 bjunkma")
        
    def testFlattenTonified(self):
        self.assertEqual(flatten([Word(Text('a ')), Word(Pinyin.parse("hen3"), Text(' b')), Word(Text("junk")), Word(Pinyin.parse("ma5"))], tonify=True),
                          "a hěn bjunkma")
    
    def testUsesWrittenTone(self):
        self.assertEqual(flatten([Word(Pinyin("hen", ToneInfo(written=2,spoken=3)))]), "hen2")

class NeedsSpaceBeforeAppendTest(unittest.TestCase):
    def testEmptyDoesntNeedSpace(self):
        self.assertFalse(needsspacebeforeappend([]))
    
    def testEndsWithWhitespace(self):
        self.assertFalse(needsspacebeforeappend([Word(Text("hello "))]))
        self.assertFalse(needsspacebeforeappend([Word(Text("hello"), Text(" "), Text("World"), Text(" "))]))
        self.assertFalse(needsspacebeforeappend([Word(Text("hello"), Text(" "), Text("World"), Text("!\t"))]))
    
    def testNeedsSpace(self):
        self.assertTrue(needsspacebeforeappend([Word(Text("hello"))]))
    
    def testPunctuation(self):
        self.assertTrue(needsspacebeforeappend([Word(Text("."))]))
        self.assertTrue(needsspacebeforeappend([Word(Text(","))]))
        self.assertFalse(needsspacebeforeappend([Word(Text("("))]))
        self.assertFalse(needsspacebeforeappend([Word(Text(")"))]))
        self.assertFalse(needsspacebeforeappend([Word(Text('"'))]))

class TonedCharactersFromReadingTest(unittest.TestCase):
    def testTonedTokens(self):
        self.assertEqual(tonedcharactersfromreading("一个", [Pinyin.parse("yi1"), Pinyin.parse("ge4")]),
                          [TonedCharacter("一", 1), TonedCharacter("个", 4)])

    def testTonedTokensWithoutTone(self):
        self.assertEqual(tonedcharactersfromreading("T恤", [Text("T"), Pinyin.parse("zhi4")]),
                          [Text("T"), TonedCharacter("恤", 4)])

    def testTonedTokenNumbers(self):
        self.assertEqual(tonedcharactersfromreading("1994", [Pinyin.parse("yi1"), Pinyin.parse("jiu3"), Pinyin.parse("jiu3"), Pinyin.parse("si4")]),
                          [Text("1"), Text("9"), Text("9"), Text("4")])
    
    def testTonesDontMatchChars(self):
        self.assertEqual(tonedcharactersfromreading("ABCD", [Word(Pinyin.parse("yi1"), Pinyin.parse("shi2"), Pinyin.parse("jiu3"), Pinyin.parse("jiu3"), Pinyin.parse("shi2"), Pinyin.parse("si4"))]),
                          [Text("ABCD")])
        self.assertEqual(tonedcharactersfromreading("ABCD", [Word(Pinyin.parse("yi1"))]),
                          [Text("ABCD")])

if __name__ == '__main__':
    unittest.main()

