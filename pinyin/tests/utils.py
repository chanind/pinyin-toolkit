# -*- coding: utf-8 -*-

import unittest

from pinyin.utils import *


class LetTest(unittest.TestCase):
    def testLet(self):
        self.assertEqual(let(1, "hello", lambda x, y: str(x) + y), "1hello")

class ConcatTest(unittest.TestCase):
    def testConcatNothing(self):
        self.assertEqual(concat([]), [])
        self.assertEqual(concat([[], []]), [])
    
    def testConcat(self):
        self.assertEqual(concat([[1, 2], [3, 4], [], [5]]), [1, 2, 3, 4, 5])

class UrlEscapeTest(unittest.TestCase):
    def testEscapeUrlEncode(self):
        self.assertEqual(urlescape("Hello World"), "Hello%20World")
    
    def testEscapeUTF8(self):
        self.assertEqual(urlescape("你"), "%E4%BD%A0")

class StripHtmlTest(unittest.TestCase):
    def testStripNothingFromText(self):
        self.assertEqual(striphtml("Hello World"), "Hello World")
    
    def testStripTags(self):
        self.assertEqual(striphtml("Hello <b>World</b>"), "Hello World")

class CumulativeTest(unittest.TestCase):
    def testCumulativeEmpty(self):
        self.assertEqual(list(cumulative([])), [])
        
    def testCumulative(self):
        self.assertEqual(list(cumulative([1, 2, 3, 2, 1])), [1, 3, 6, 8, 9])

class SortingTest(unittest.TestCase):
    def testSortedByFirst(self):
        self.assertEqual(sorted([(5, "1"), (2, "4"), (3, "2"), (1, "5"), (4, "3")], byFirst), [(1, "5"), (2, "4"), (3, "2"), (4, "3"), (5, "1")])
    
    def testSortedBySecond(self):
        self.assertEqual(sorted([(5, "1"), (2, "4"), (3, "2"), (1, "5"), (4, "3")], bySecond), [(5, "1"), (3, "2"), (4, "3"), (2, "4"), (1, "5")])

    def testSortedInReverse(self):
        self.assertEqual(sorted([5, 2, 3, 1, 4], inReverse()), [5, 4, 3, 2, 1])
        self.assertEqual(sorted([5, 2, 3, 1, 4], inReverse(inReverse())), [1, 2, 3, 4, 5])
    
    def testSortedLexically(self):
        self.assertEqual(sorted([(3, 2), (1, 2), (1, 1), (3, 1), (2, 0)], lexically()), [(1, 1), (1, 2), (2, 0), (3, 1), (3, 2)])
        self.assertEqual(sorted([(3, 2), (1, 2), (1, 1), (3, 1), (2, 0)], lexically(inReverse())), [(3, 1), (3, 2), (2, 0), (1, 1), (1, 2)])
        self.assertEqual(sorted([(3, 2), (1, 2), (1, 1), (3, 1), (2, 0)], lexically(inReverse(), inReverse())), [(3, 2), (3, 1), (2, 0), (1, 2), (1, 1)])

class HeadOrTest(unittest.TestCase):
    def testHeadOrNonEmpty(self):
        self.assertEqual(heador([1], "Another"), 1)
        self.assertEqual(heador([1, 2], "Another"), 1)

    def testHeadOrEmpty(self):
        self.assertEqual(heador([], "Another"), "Another")

class SubstringsTest(unittest.TestCase):
    def testVanilla(self):
        self.assertEqual(list(substrings("hello")), ["hello", "hell", "ello", "hel", "ell", "llo", "he", "el", "ll", "lo", "h", "e", "l", "l", "o"])

    def testBoundaryConditions(self):
        self.assertEqual(list(substrings("a")), ["a"])
        self.assertEqual(list(substrings("")), [])

class HtmlColorTest(unittest.TestCase):
    def testParseBadLength(self):
        self.assertRaises(ValueError, lambda: parseHtmlColor(""))
        self.assertRaises(ValueError, lambda: parseHtmlColor("#aabbc"))
        self.assertRaises(ValueError, lambda: parseHtmlColor("#aabbccd"))
    
    def testParseBadStart(self):
        self.assertRaises(ValueError, lambda: parseHtmlColor("?aabbcc"))
    
    def testParseCorrectly(self):
        self.assertEqual(parseHtmlColor("#0156af"), (1, 86, 175))

    def testToHtmlColor(self):
        self.assertEqual(toHtmlColor(1, 2, 3), "#010203")
        self.assertEqual(toHtmlColor(1, 86, 175), "#0156af")

class MkdirFallbackTest(unittest.TestCase):
    def testDirectoryForNameThatIsFree(self):
        def do(path):
            self.assertEqual(mkdirfallback(path, "Hello"), os.path.join(path, "Hello"))

        withtempdir(do)

    def testDirectoryForNameThatIsNotFree(self):
        def do(path):
            os.mkdir(os.path.join(path, "Hello"))
            self.assertEqual(mkdirfallback(path, "Hello"), os.path.join(path, "Hello 1"))

        withtempdir(do)

    def testDirectoryForNameHigherNumbers(self):
        def do(path):
            os.mkdir(os.path.join(path, "Hello"))
            os.mkdir(os.path.join(path, "Hello 1"))
            os.mkdir(os.path.join(path, "Hello 2"))
            self.assertEqual(mkdirfallback(path, "Hello"), os.path.join(path, "Hello 3"))

        withtempdir(do)

class TouchTest(unittest.TestCase):
    def testTouch(self):
        def do(path):
            filepath = os.path.join(path, "Dumb")
            
            self.assertFalse(os.path.exists(filepath))
            touch(filepath)
            self.assertTrue(os.path.exists(filepath))
        
        withtempdir(do)

class ThunkTest(unittest.TestCase):
    def testCall(self):
        self.assertEqual(Thunk(lambda: 5)(), 5)
    
    def testTransparency(self):
        self.assertEqual(Thunk(lambda: "hello!").rstrip("!"), "hello")

class RegexParseTest(unittest.TestCase):
    def testParseSimple(self):
        self.assertEqual(self.parse(re.compile("foo"), "foo bar foo bar"),
                          [(True, "foo"), (False, " bar "), (True, "foo"), (False, " bar")])
    
    def testParseEmpty(self):
        self.assertEqual(self.parse(re.compile(""), "abc"),
                          [(True, ""), (False, "a"), (True, ""), (False, "b"), (True, ""), (False, "c")])
    
    def testParseNeedStuffAtEnd(self):
        self.assertEqual(self.parse(re.compile("foo"), "foo foo, foo!"),
                          [(True, "foo"), (False, " "), (True, "foo"), (False, ", "), (True, "foo"), (False, "!")])
    
    # Test helpers
    def parse(self, re, text):
        result = []
        for ismatch, thing in regexparse(re, text):
            if ismatch:
                result.append((ismatch, thing.group(0)))
            else:
                result.append((ismatch, thing))
        
        return result

class FactoryDictTest(unittest.TestCase):
    def testFactory(self):
        dict = FactoryDict(lambda x: x + 1)
        self.assertEqual(dict[3], 4)
    
    def testNormalOperation(self):
        dict = FactoryDict(lambda x: x + 1)
        
        dict[2] = "Hello"
        self.assertEqual(dict[2], "Hello")
        
        dict[3] = "Bye"
        self.assertEqual(dict[2], "Hello")
        self.assertEqual(dict[3], "Bye")

class isMandarinModelTest(unittest.TestCase):
    def testCheck(self):
        self.assertTrue(ismandarinmodel("Mandarin"))
        self.assertTrue(ismandarinmodel(" Mandarin "))
        self.assertTrue(ismandarinmodel("HSK 1 Mandarin"))
        self.assertFalse(ismandarinmodel("Japanese Deck"))
    
if __name__ == '__main__':
    unittest.main()
