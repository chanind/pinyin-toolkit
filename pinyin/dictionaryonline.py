#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib.request, urllib.error, urllib.parse
import re
import json

from .model import Text, Word
from .logger import log
from . import utils

# This module will takes a phrase and passes it to online services for translation
# For now this modle provides support for google translate. In the future more dictionaries may be added.


# Translate the parsed text from Chinese into target language using google translate:
def gTrans(query, destlanguage='en', prompterror=True):
    log.info("Using Google translate to determine the unknown translation of %s", query)

    # No meanings if we don't have a query
    if query == None:
        return None
    
    # No meanings if our query is blank after stripping HTML out
    query = utils.striphtml(query)
    if query.strip() == "":
        return None

    try:
        # Return the meanings (or lack of them) directly
        return lookup(query, destlanguage)
    except urllib.error.URLError as e:
        # The only 'meaning' should be an error telling the user that there was some problem
        log.exception("Error while trying to obtain Google response")
        if prompterror:
            return [[Word(Text('<span style="color:gray">[Internet Error]</span>'))]]
        else:
            return None
    except ValueError as e:
        # Not an internet problem
        log.exception("Error while interpreting translation response from Google")
        if prompterror:
            return [[Word(Text('<span style="color:gray">[Error In Google Translate Response]</span>'))]]
        else:
            return None

# This function will send a sample query to Google Translate and return true or false depending on success
# It is used to determine connectivity for the Anki session (and thus whether Pinyin Toolkit should use online services or not)
def gCheck(destlanguage='en'):
    try:
        lookup("好", destlanguage)
        return True
    except urllib.error.URLError:
        return False
    except ValueError:
        # Arguably could return True here, because it's not that the website is offline
        return False

# The lookup function is based on code from the Chinese Example Sentence Plugin by <aaron@lamelion.com>
def lookup(query, destlanguage):
    # Set up URL
    url = "http://translate.google.com/translate_a/t?client=j&text=%s&sl=%s&tl=%s" % (utils.urlescape(query), 'zh-CN', destlanguage)
    con = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11'}, origin_req_host='http://translate.google.com')
    
    # Open the connection
    log.info("Issuing Google query for %s to %s", query, url)
    req = urllib.request.urlopen(con)
    
    # Build the result literal from the request
    literal = ""
    for line in req:
        literal += line.decode('utf-8')
        
    # Parse the response:
    try:
        log.info("Parsing response %r from Google", literal)
        result = parsegoogleresponse(literal)
    except ValueError as e:
        # Give the exception a more precise error message for debugging
        raise ValueError("Error while parsing translation response from Google: %s" % str(e))
    
    # What sort of result did we get?
    if isinstance(result, str):
        if result == query:
            # The result was, unhelpfully, what we queried. Give up:
            return None
        else:
            # Simple strings can be returned directly
            return [[Word(Text(result))]]
    elif isinstance(result, list):
        # Otherwise, we get a result like this:
        # ["Well",
        #   [
        #     ["verb","like","love"],
        #     ["adjective","good"],
        #     ["adverb","fine","OK","okay","okey","okey dokey","well"],
        #     ["interjection","OK!","okay!","okey!"]
        #   ]
        # ]
        #
        # Or this:
        # [
        #   [
        #     ["Good","\u597d",""]
        #   ],
        #   [
        #     [
        #       "verb",
        #       ["Love","Like"]
        #     ],
        #     [
        #       "adjective",
        #       ["Good"]
        #     ],
        #     [
        #       "adverb",
        #       ["Well","Fine","OK","Okay","Okey","Okey dokey"]
        #     ],
        #     [
        #       "interjection",
        #       ["OK","Okay","Okey"]
        #     ]
        #   ],
        #   "zh-CN"
        # ]
        #
        # Or this even newer format:
        # [
        #   [
        #      [
        #        "Hello, you are my friend?",
        #        "\u4f60\u597d\uff0c\u4f60\u662f\u6211\u7684\u670b\u53cb\u5417\uff1f",
        #        ""
        #      ]
        #   ],
        #   ,
        #   "zh-CN"
        # ]
        try:
            if isinstance(result[0], list):
                if result[0][0][0] == result[0][0][1]:
                    # If no translation was performed, give up
                    return None
                else:
                    # Otherwise, extract response
                    return [[Word(Text(result[0][0][0]))]] + [[Word(Text(definition[0].capitalize() + ": " + ", ".join([d.lower() for d in definition[1]])))] for definition in result[1] or []]
            else:
                return [[Word(Text(result[0]))]] + [[Word(Text(definition[0].capitalize() + ": " + ", ".join(definition[1:])))] for definition in result[1]]
        except IndexError:
            raise ValueError("Result %s from Google Translate looked like a definition but was not in the expected list format" % str(result))
    elif isinstance(result, dict):
        # Oh dear, they have devised another method of returning results. This time, it looks like this:
        # {"sentences":[{"trans":"Hello, you are my friend?",
        #                "orig":"你好，你是我的朋友吗？",
        #                "translit":""}],
        #              "src":"zh-CN"}
        # {"sentences":[{"trans":"Well",
        #                "orig":"好",
        #                "translit":""}],
        #  "dict":[{"pos":"verb",
        #           "terms":["like","love"]},
        #          {"pos":"adjective",
        #           "terms":["good"]},
        #          {"pos":"adverb",
        #           "terms":["fine","OK","okay","okey","okey dokey","well"]},
        #          {"pos":"interjection",
        #           "terms":["OK!","okay!","okey!"]}],
        #  "src":"en"}
        try:
            sentences = " ".join([sentence["trans"] for sentence in result["sentences"]])
            if sentences == query:
                # The result was, unhelpfully, what we queried. Give up:
                return None
            else:
                return [[Word(Text(sentences))]] + [[Word(Text(definition["pos"].capitalize() + ": " + ", ".join(definition["terms"])))] for definition in result.get("dict", [])]
        except KeyError:
            raise ValueError("Result %s from Google Translate looked like a definition but was not in the expected dict format" % str(result))
    else:
        # Haven't seen any other case in the wild
        raise ValueError("Couldn't deal with the correctly-parsed response %s from Google" % str(result))

def parsegoogleresponse(response):
    return json.loads(response)

################################################################################
#Indicators
# Future interest in having icons above the facteditor representing various dictionaries
# Light up red/green indicators show if the entry is in the dictionary or not
# Can click-through to access online dictionary


################################################################################
# Future plans to impliment entries to CC-CEDICT, HanDeDict, and CFDICT from Anki.

# def submitSelector(self, Hanzi, Pinyin, language, translation):
#     log.info("User is attempting to submit an entry for %s [%s] to the %s dictionary", Hanzi, Pinyin, language)
# 
#     if language == "en":
#         submitCEDICT( Hanzi, Pinyin, translation) 
#     else:
#         log.warn("No %s dictionary available to submit entry to", language)
# 
# 
#     
# 
# def submitCEDICT(self, Hanzi, Pinyin, English ):
#     # Add function to use google translate to lookup traditional and simplfied (this way avoid handedict / ccedict swap problems
#     # need internet to make submittion anyway
#     hanziSimp = "" 
#     HanziTrad = ""
#     
#     # run hanzi thought lookup with tonify off to get pinyin + tones (need this format for CC-CEDICT) 
#     Pinyin = ""
#     
#     URL = "http://cc-cedict.org/editor/editor.php?return=&insertqueueentry_diff=+" + hanzisimp + "[" + pinyin +"]+/&popup=1&handler=InsertQueueEntry"
