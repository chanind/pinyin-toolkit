# -*- coding: utf-8 -*-

import unittest

from pinyin.factproxy import *


class FactProxyTest(unittest.TestCase):
    def testDontContainMissingFields(self):
        self.assertFalse("key" in FactProxy({"key" : ["Foo", "Bar"]}, { "Baz" : "Hi" }))

    def testContainsPresentFields(self):
        self.assertTrue("key" in FactProxy({"key" : ["Foo", "Bar"]}, { "Bar" : "Hi" }))

    def testSet(self):
        fact = { "Baz" : "Hi" }
        FactProxy({"key" : ["Foo", "Baz"]}, fact)["key"] = "Bye"
        self.assertEqual(fact["Baz"], "Bye")

    def testGet(self):
        fact = { "Baz" : "Hi" }
        self.assertEqual(FactProxy({"key" : ["Foo", "Baz"]}, fact)["key"], "Hi")

    def testPriority(self):
        fact = { "Baz" : "Hi", "Foo" : "Meh" }
        FactProxy({"key" : ["Foo", "Baz"]}, fact)["key"] = "Bye"
        self.assertEqual(fact, { "Baz" : "Hi", "Foo" : "Bye" })
        
        fact = { "Baz" : "Hi", "Foo" : "Meh" }
        FactProxy({"key" : ["Baz", "Foo"]}, fact)["key"] = "Bye"
        self.assertEqual(fact, { "Baz" : "Bye", "Foo" : "Meh" })
    
    def testCase(self):
        fact = { "Foo" : "Meh" }
        FactProxy({"key" : ["foo"]}, fact)["key"] = "Bye"
        self.assertEqual(fact, { "Foo" : "Bye" })

if __name__ == '__main__':
    unittest.main()

