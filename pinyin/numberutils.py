#!/usr/bin/env python
# -*- coding: utf-8 -*-

from . import dictionary
from . import model
from . import utils

#
# Raw data
#

hanzidigits = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九"]
hanziquantitypinyin = [model.Pinyin(c_p_t[1], c_p_t[2]) for c_p_t in [
    ("一", "yi", 1),
    ("两", "liang", 3),
    ("三", "san", 1),
    ("四", "si", 4),
    ("五", "wu", 3),
    ("六", "liu", 4),
    ("七", "qi", 1),
    ("八", "ba", 1),
    ("九", "jiu", 3),
    ("几", "ji", 3)
  ]]

magnitudes = list(enumerate([
    "",     # units
    "十",    # tens
    "百",    # hundreds
    "千",    # thousands
    "万",    # ten-thousands
    "十万",   # hundred thousand
    "百万",   # 10^6
    "千万",   # 10^7
    "亿",    # 10^8
    "十亿",   # 10^9
    "百亿",   # 10^10
    "千亿",   # 10^11
    "兆",    # 10^12
    "十兆",   # 10^13
    "百兆",   # 10^14
    "千兆"    # 10^15
  ]))

#
# These are the low-level functions that just convert between
# hanzi representing integers and Python integers
#

def skipcommas(whenparsingwhat):
    skips = [",", "，"]
    
    def inner(text):
        # We want to keep stripping stuff until we can't any longer
        skipped = True
        while skipped:
            skipped = False
            for skip in skips:
                if text.startswith(skip):
                    # Able to skip: trim and go around for another round
                    text = text[len(skip):]
                    skipped = True
                    break
        
        # Stripped as much as possible, try the inner parser now
        return whenparsingwhat(text)
    
    return inner

def parsemany(ofwhat):
    def inner(text):
        things = []
        while True:
            thing, text = ofwhat(text)
            if thing is None:
                return things, text
            
            things.append(thing)
    
    return inner

def parsedigit(text):
    if len(text) > 0 and text[0].isdigit():
        return text[0], text[1:]
    else:
        return None, text

parsedigitswithcommas = lambda text: parsemany(skipcommas(parsedigit))(text)

# Parsing a single digit: returns a digit (or None) and the rest of the string
def parsehanzidigit(hanzi):
    for digit, digittext in enumerate(hanzidigits):
        if hanzi.startswith(digittext):
            return digit, hanzi[len(digittext):]
    
    return None, hanzi

parsehanzidigits = lambda text: "".join(parsemany(parsehanzidigit)(text))

# Takes western numbers and converts them into Chinese characters so they can be use in the dictionary lookup
def numberashanzi(n):  
    if n < 10:
        # Special case: if we just have 0, return ling,
        # or the logic below will just return an empty string.
        # Likewise, for the number 1 - so we may as well
        # do this for all manifest digits.
        return hanzidigits[n]
    
    hanzi = ""
    needling = False
    for power, text in reversed(magnitudes):
        tenpower = pow(10, power)
        
        # This check will only have an effect the first time around the
        # loop: if the number turns out to be too big, return the Arabic
        if n >= 10 * tenpower:
            return str(n)
        
        # NB: use floor division instead of ``true division'' here
        digit = n // tenpower
        n = n % tenpower
        
        if digit == 0:
            # We record the fact that we need to insert a ling before the end
            # as long as there we already have some digits in the output
            if hanzi != "":
                needling = True
            
            # Don't display anything in the string right now
            continue
        
        if digit == 1 and power < 3 and hanzi == "":
            # We can omit the leading one for numbers on numbers 100 or less
            hanzi += text
            continue
        
        if needling:
            # Insert a ling marker before the digit
            hanzi += hanzidigits[0]
            needling = False
        
        hanzi += hanzidigits[digit] + text
    
    return hanzi

# Takes Chinese characters and attempts to convert them into an integer
def parsehanziasnumber(hanzi):
    # The only valid form for 0 is 'ling'
    if hanzi.startswith(hanzidigits[0]):
        return 0, hanzi[len(hanzidigits[0]):]
    
    # Special case for the irregular 'liang'
    if hanzi.startswith("两"):
        return 2, hanzi[len("两"):]
    
    # Main loop that parses the numeric text from the left
    number = 0
    for power, powertext in reversed(magnitudes):
        # Start off by trying to parse a digit
        digit, candidatehanzi = parsehanzidigit(hanzi)
        if digit is None:
            if power == 0:
                # Musn't make assumption about leading digit if we're on
                # the final magnitude, or we might get an extra 1
                continue
            else:
                # Assume the leading digit is 1 if we couldn't find one
                digit = 1
        
        # Zeroes tend to act as filler between things which really
        # contribute to the number. NB: also deals with ling by itself
        if digit == 0:
            hanzi = candidatehanzi
            continue
        
        # If the remaining stuff doesn't look like a power, move on to
        # the next order of magnitude to give that a chance
        if not(candidatehanzi.startswith(powertext)):
            continue
        
        # Starts with a power, so we can accumulate the resulting stuff
        hanzi = candidatehanzi[len(powertext):]
        number += digit * pow(10, power)
    
    # If we still have 0 in the accumulator at this point then there
    # was no valid number there at all
    if number == 0:
        number = None
    
    # Return the number and any remaining text
    return number, hanzi

#
# Higher level functions using the ability to go between Hanzi and integers
#

# TODO: currency support?
# TODO: the Western and Chinese parsers are substantially the same. Perhaps more code could be shared.

def parsewesternnumberlike(expression, integerhandler, decimalhandler, yearhandler, percenthandler, fractionhandler):
    # Every numberlike form starts with some leading digits
    leadingdigits, expression = parsedigitswithcommas(expression)
    expression = expression.strip()
    
    # Ensure we managed to get at least some digits
    if len(leadingdigits) == 0:
        return None
    
    # If that's followed by a decimal seperator and some digits we
    # can generate a Chinese decimal reading
    if expression.startswith(".") or expression.startswith("。"):
        trailingdigits, expression = parsemany(parsedigit)(expression[1:])
        if len(trailingdigits) == 0 or expression.strip() != "":
            # Something after the trailing digits that we don't understand
            # or we didn't get any digits after . at all
            return None
        
        return decimalhandler(leadingdigits, trailingdigits)
    
    # What suffixes the integer?
    if expression == "":
        # No suffix, return as a straight number
        return integerhandler(leadingdigits)
    elif expression == "年":
        # Followed by a nian, return as a year
        return yearhandler(leadingdigits)
    elif expression in ["%", "％"]:
        # Followed by a percentage symbol, return as a percentage
        return percenthandler(leadingdigits)
    elif expression.startswith("/") or expression.startswith("\\"):
        # Followed by a slash, so could be a fraction
        trailingdigits, expression = parsedigitswithcommas(expression[1:])
        if len(trailingdigits) == 0 or expression.strip() != "":
            # Something after the trailing digits that we don't understand
            # or we didn't get any digits after the slash at all
            return None
        
        return fractionhandler(leadingdigits, trailingdigits)
    else:
        # Unknown suffix, we have to give up for sanity
        return None

def parsechinesenumberlike(expression, integerhandler, decimalhandler, yearhandler, percenthandler, fractionhandler):
    # Every numberilke form starts with some leading digits
    leadingnumber, trailingexpression = parsehanziasnumber(expression)
    leadingwesterndigits = list(str(leadingnumber))
    
    # Ensure we managed to get at least some digits
    if leadingnumber is None:
        return None
    
    # If that's followed by a decimal seperator and some digits we
    # can generate a Chinese decimal meaning
    if trailingexpression.startswith("点"):
        trailingdigits, trailingexpression = parsemany(parsehanzidigit)(trailingexpression[len("点"):])
        if len(trailingdigits) == 0 or trailingexpression.strip() != "":
            # Something after the trailing digits that we don't understand
            # or we didn't get any digits after . at all
            return None
        
        return decimalhandler(leadingwesterndigits, trailingdigits)
    
    # What suffixes the integer?
    if trailingexpression == "":
        # No suffix, return as a straight number
        return integerhandler(leadingwesterndigits)
    elif trailingexpression.startswith("分之"):
        # A fraction! Get the numerator
        trailingnumber, trailingexpression = parsehanziasnumber(trailingexpression[len("分之"):])
        trailingwesterndigits = list(str(trailingnumber))
    
        # Bail out if that didn't consume the whole input
        if trailingexpression.strip() != "":
            return None
    
        if leadingnumber == 100:
            # Divisions out of 100 should be treated as percentages
            return percenthandler(trailingwesterndigits)
        else:
            # Otherwise treat as a straight fraction
            return fractionhandler(trailingwesterndigits, leadingwesterndigits)
    else:
        # Unknown suffix. We probably have to give up, but we MIGHT have had a year:
        leadingwesterndigits, trailingexpression = parsemany(parsehanzidigit)(expression)
        if trailingexpression == "年":
            # Followed by a nian, return as a year
            return yearhandler(leadingwesterndigits)
        else:
            # Give up
            return None

def readingfromnumberlike(expression, dictionary):
    intify = lambda digits: int("".join(digits))
    
    # Here, we need to be careful to turn Western number-like things into readings
    # the way a Chinese person would say them
    return parsewesternnumberlike(expression,
            lambda digits: dictionary.reading(numberashanzi(intify(digits))),
            lambda leadingdigits, trailingdigits: dictionary.reading(numberashanzi(intify(leadingdigits)) + "点" + "".join([numberashanzi(int(digit)) for digit in trailingdigits])),
            lambda digits: dictionary.reading("".join([numberashanzi(int(digit)) for digit in digits]) + "年"),
            lambda digits: dictionary.reading("百分之" + numberashanzi(intify(digits))),
            lambda numdigits, denomdigits: dictionary.reading(numberashanzi(intify(denomdigits)) + "分之" + numberashanzi(intify(numdigits))))

def meaningfromnumberlike(expression, dictionary):
    stringify = lambda digits: "".join([str(digit) for digit in digits])
    handlers = [
        lambda digits: stringify(digits),
        lambda leadingdigits, trailingdigits: stringify(leadingdigits) + "." + stringify(trailingdigits),
        lambda digits: stringify(digits) + "AD",
        lambda digits: stringify(digits) + "%",
        lambda numdigits, denomdigits: stringify(numdigits) + "/" + stringify(denomdigits)
      ]
    
    # Generates a meaning from approximately Western expressions (almost useless, but does handle nian suffix)
    text = parsewesternnumberlike(expression, *handlers)
    
    if not(text):
        # Generate a meaning from approximately Chinese expressions
        text = parsechinesenumberlike(expression, *handlers)
        
    # Wrap the result in the appropriate gumpf
    return utils.bind_none(text, lambda nonnulltext: [[model.Word(model.Text(nonnulltext))]])
