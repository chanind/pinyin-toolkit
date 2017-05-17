#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QBrush, QDesktopServices, QFont, QImage, QKeySequence, QPalette, QPixmap


# Substantially cribbed from Anki (main.py, onOpenPluginFolder):
def openFolder(path):
    import sys
    import subprocess
    
    if sys.platform == "win32":
        subprocess.Popen(["explorer", path.encode(sys.getfilesystemencoding())])
    else:
        QDesktopServices.openUrl(QUrl("file://" + path))


def nativeShortcutKeys(keys):
    return QKeySequence(keys).toString(QKeySequence.NativeText)
