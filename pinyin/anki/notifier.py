#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import traceback

from aqt.utils import showInfo, showWarning


"""
Notifier that actually displays the messages on screen.
"""
class AnkiNotifier(object):
    def __init__(self):
        # A list of those things we have already shown, if we're suppressing duplicate messages
        self.alreadyshown = []
    
    def info(self, what):
        showInfo(what)
    
    def infoOnce(self, what):
        if not(what in self.alreadyshown):
            self.info(what)
            self.alreadyshown.append(what)
    
    def exception(self, text, exception_info=None):
        if exception_info is None:
            exception_info = sys.exc_info()
        
        showWarning(text + "\r\nThe exception was:\r\n" + "".join(traceback.format_exception(*exception_info)))
