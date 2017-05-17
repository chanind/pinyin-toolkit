#!/usr/bin/env python
# -*- coding: utf-8 -*-

from aqt.qt import *
from aqt.utils import showInfo
from anki.find import Finder

import pinyin.anki.keys
import pinyin.factproxy
import pinyin.media
import pinyin.transformations
import pinyin.utils

from pinyin.logger import log
from pinyin.config import getconfig, saveconfig

from copy import deepcopy

#
# A base class for hooks added using the addHook routine.
# Add each hook to the hookbuilders list below to be installed on startup.
#
class Hook(object):
    def __init__(self, mw, notifier, mediamanager, updaters):
        self.mw = mw
        self.notifier = notifier
        self.mediamanager = mediamanager
        self.updaters = updaters
        self.config = getconfig()
   
class ToolMenuHook(Hook):
    pinyinToolkitMenu = None
    
    def install(self):
        # Install menu item
        log.info("Installing a menu hook (%s)", type(self))

class FocusHook(Hook):

    # Called by anki editor (aqt.editor)
    # Requires boolean return value: true if note was updated
    def onFocusLost(self, flag, note, fldIdx):
        savedNoteValues = deepcopy(list(note.values()))

        fieldNames = self.mw.col.models.fieldNames(note.model())
        currentFieldName = fieldNames[fldIdx]
        log.info("User moved focus from the field %s", currentFieldName)
        
        # Are we not in a Mandarin model?
        if not(pinyin.utils.ismandarinmodel(note.model()['name'])):
            return flag
        
        # Need a fact proxy because the updater works on dictionary-like objects
        factproxy = pinyin.factproxy.FactProxy(self.config.candidateFieldNamesByKey, note)
        
        # Find which kind of field we have just moved off
        updater = None
        for key, fieldname in list(factproxy.fieldnames.items()):
            if currentFieldName == fieldname:
                updater = self.updaters.get(key)
                break

        # Update the card, ignoring any errors
        fieldValue = note.fields[fldIdx]
        if not updater:
            return flag

        updater.updatefact(factproxy, fieldValue)
        # pinyin.utils.suppressexceptions(
        #     lambda: updater.updatefact(factproxy, fieldValue))

        noteChanged = (savedNoteValues != list(note.values()))

        return noteChanged
    
    def install(self):
        from anki.hooks import addHook, remHook
        
        # Install hook into focus event of Anki: we regenerate the model information when
        # the cursor moves from the Expression/Reading/whatever field to another field
        log.info("Installing focus hook")
        
        # Unconditionally add our new hook to Anki
        addHook('editFocusLost', self.onFocusLost)

class FieldShrinkingHook(Hook):
    def adjustFieldHeight(self, widget, field):
        for wanttoshrink in ["mw", "audio", "mwaudio"]:
            if field.name in self.config.candidateFieldNamesByKey[wanttoshrink]:
                log.info("Shrinking field %s", field.name)
                widget.setFixedHeight(30)
    
    def install(self):
        from anki.hooks import addHook
        
        log.info("Installing field height adjustment hook")
        addHook("makeField", self.adjustFieldHeight)

# Shrunk version of color shortcut plugin merged with Pinyin Toolkit to give that functionality without the seperate download.
# Original version by Damien Elmes <anki@ichi2.net>
class ColorShortcutKeysHook(Hook):
    def setColor(self, editor, i, sandhify):
        log.info("Got color change event for color %d, sandhify %s", i, sandhify)
        
        color = (self.config.tonecolors + self.config.extraquickaccesscolors)[i - 1]
        if sandhify:
            color = pinyin.transformations.sandhifycolor(color)
        
        focusededit = editor.focusedEdit()
        
        cursor = focusededit.textCursor()
        focusededit.setTextColor(QColor(color))
        cursor.clearSelection()
        focusededit.setTextCursor(cursor)
    
    def setupShortcuts(self, editor):
        # Loop through the 8 F[x] keys, setting each one up
        # Note: Ctrl-F9 is the HTML editor. Don't do this as it causes a conflict
        log.info("Setting up shortcut keys on fact editor")
        for i in range(1, 9):
            for sandhify in [True, False]:
                keysequence = (sandhify and pinyin.anki.keys.sandhiModifier + "+" or "") + pinyin.anki.keys.shortcutKeyFor(i)
                QShortcut(QKeySequence(keysequence), editor.widget,
                                lambda i=i, sandhify=sandhify: self.setColor(editor, i, sandhify))
    
    def install(self):
        from anki.hooks import wrap
        import ankiqt.ui.facteditor
        
        log.info("Installing color shortcut keys hook")
        ankiqt.ui.facteditor.FactEditor.setupFields = wrap(ankiqt.ui.facteditor.FactEditor.setupFields, self.setupShortcuts, "after")
        self.setupShortcuts(self.mw.editor)

class HelpHook(Hook):
    def install(self):
        # Store the action on the class.  Storing a reference to it is necessary to avoid it getting garbage collected.
        self.action = QAction(self.mw)
        self.action.setText("Pinyin Toolkit")
        self.action.setStatusTip("Help for the Pinyin Toolkit available at our website")
        self.action.setEnabled(True)
        
        helpUrl = QUrl("http://batterseapower.github.com/pinyin-toolkit/")
        self.mw.form.menuHelp.addAction(self.action)
        self.action.triggered.connect(lambda: QDesktopServices.openUrl(helpUrl))
   
class TagRemovingHook(Hook):
    def filterHtml(self, html, _card):
        return pinyin.factproxy.unmarkhtmlgeneratedfields(html)
    
    def install(self):
        from anki.hooks import addHook
        
        log.info("Installing tag removing hook")
        addHook("drawAnswer", self.filterHtml)
        addHook("drawQuestion", self.filterHtml)

# NB: this must go at the end of the file, after all the definitions are in scope
hookbuilders = [
    # Focus hook
    FocusHook,

    # Widget adjusting hooks
    #FieldShrinkingHook,

    # Keybord hooks
    #ColorShortcutKeysHook,
  ]


#
# Build hooks that are invoked from the menu.
#
def buildHooks(menu, mw, config, notifier, mediamanager, updaters):
    buildHookMissingInformation(menu, mw, config, notifier, updaters)
    buildHookReformatReadings(menu, mw, config, notifier, updaters)
    menu.addSeparator()
    buildHookPreferences(menu, mw, config, notifier, mediamanager)
    buildHookHelp(menu, mw)

def buildHookHelp(menu, mw):
    title = "About" 
    tip = "Help for the Pinyin Toolkit available at our website"
    helpUrl = QUrl("http://batterseapower.github.com/pinyin-toolkit/")
    function = lambda: QDesktopServices.openUrl(helpUrl)
    createAction(menu, mw, title, tip, function)

def buildHookPreferences(menu, mw, config, notifier, mediamanager):
    title = "Preferences"
    tip = "Configure the Pinyin Toolkit"
    function = lambda: openPreferences(mw, config, notifier, mediamanager)
    createAction(menu, mw, title, tip, function)

def buildHookMissingInformation(menu, mw, config, notifier, updaters):
    title = 'Fill missing card data'
    tip = 'Update all the cards in the deck with any missing information the Pinyin Toolkit can provide.'
    field = "expression"
    updatehow = "updatefact"
    notification = "All missing information has been successfully added to your deck."
    function = lambda: runBulkFill(mw, config, notifier, updaters, field, updatehow, notification)
    createBulkFillAction(menu, mw, title, tip, function)

def buildHookReformatReadings(menu, mw, config, notifier, updaters):
    title = 'Reformat readings'
    tip = 'Update all the readings in your deck with colorisation and tones according to your preferences.'
    field = "reading"
    updatehow = "updatefactalways"
    notification = "All readings have been successfully reformatted."
    function = lambda: runBulkFill(mw, config, notifier, updaters, field, updatehow, notification)
    createBulkFillAction(menu, mw, title, tip, function)

# Create action with details and add to menu
def createAction(menu, mw, title, statusTip, function):
    action = QAction(mw)
    action.setText(title)
    action.setStatusTip(statusTip)
    action.setEnabled(True)
    action.triggered.connect(function)
    menu.addAction(action)
    return action

def createBulkFillAction(menu, mw, title, tip, function):
    return createAction(menu, mw, title, tip, function)

def openPreferences(mw, config, notifier, mediamanager):
    # NB: must import these lazily to break a loop between preferencescontroller and here
    import pinyin.forms.preferences
    import pinyin.forms.preferencescontroller
    log.info("User opened preferences dialog")
    
    # Instantiate and show the preferences dialog modally
    preferences = pinyin.forms.preferences.Preferences(mw)
    controller = pinyin.forms.preferencescontroller.PreferencesController(preferences, notifier, mediamanager, config)
    result = preferences.exec_()
    
    if result == QDialog.Accepted:
        config.settings = controller.model.settings
        saveconfig()

def runBulkFill(mw, config, notifier, updaters, field, updatehow, notification):
    if mw.web.key == "deckBrowser":
        return showInfo("No deck selected 同志!")

    log.info("User triggered missing information fill for %s" % field)
    
    queryStr = "deck:current "
    for tag in config.getmodeltagslist():
        queryStr += " or note:*" + tag + "* "
    notes = Finder(mw.col).findNotes(queryStr)

    for noteId in notes:
        note = mw.col.getNote(noteId)
        # Need a fact proxy because the updater works on dictionary-like objects
        factproxy = pinyin.factproxy.FactProxy(config.candidateFieldNamesByKey, note)
        if field not in factproxy:
            continue
        
        getattr(updaters[field], updatehow)(factproxy, factproxy[field])
        
        # NB: very important to mark the fact as modified (see #105) because otherwise
        # the HTML etc won't be regenerated by Anki, so users may not e.g. get working
        # sounds that have just been filled in by the updater.
        note.flush()
    
    # For good measure, mark the deck as modified as well (see #105)
    mw.col.setMod()

    # DEBUG consider future feature to add missing measure words cards after doing so (not now)
    notifier.info(notification)


