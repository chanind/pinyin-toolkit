#!/usr/bin/env python
# -*- coding: utf-8 -*-

from aqt.qt import *
from aqt.utils import showInfo

import anki.hooks
import anki.utils
import sqlalchemy

import weakref

import pinyin.anki.keys
import pinyin.factproxy
from pinyin.logger import log
import pinyin.media
import pinyin.transformations
import pinyin.utils

import utils

class Hook(object):
    def __init__(self, mw, notifier, mediamanager, config, updaterbuilders):
        self.mw = mw
        self.notifier = notifier
        self.mediamanager = mediamanager
        self.config = config
        self.updaterbuilders = updaterbuilders

    def buildupdater(self, field):
        builder = self.updaterbuilders.get(field)
        return (builder is not None) and builder(self.notifier, self.mediamanager, self.config) or None

class FocusHook(Hook):
    def __init__(self, *args):
        Hook.__init__(self, *args)
        
        # The fact editor Anki currently has open: used for the code determining when a field has changed
        self.knownfactedit = None
    
    def sessionExistsFor(self, field):
        # If there is no current deck, DO NOT ask about the field name or
        # value. This is because the session may be dead, so asking will
        # generate a sqlalchemy.exc.UnboundExecutionError
        if self.mw.deck is None or self.mw.deck.s is None:
            return False
        
        try:
            field.name
            return True
        except sqlalchemy.exc.UnboundExecutionError, e:
            return False
    
    def makeField(self, fieldwidget, field):
        # Detect the creation of a brang new fact editor
        if self.knownfactedit != fieldwidget.parent:
            self.knownfactedit = fieldwidget.parent
            
            # Reset modified state of each field after losing focus to any field (and
            # after executing the standard onFocusLost hook)
            def afterOnFocusLost(widget):
                for _, fieldwidget in self.knownfactedit.fields.values():
                    fieldwidget.document().setModified(False)
            
            self.knownfactedit.onFocusLost = anki.hooks.wrap(self.knownfactedit.onFocusLost, afterOnFocusLost)
        
        # We're going to use the document modified state to detect when the user made a change,
        # so make sure that the field is initially unmodified
        fieldwidget.document().setModified(False)
    
    def onFocusLost(self, fact, field):
        if not self.sessionExistsFor(field):
            return
        
        log.info("User moved focus from the field %s", field.name)
        
        # Determine whether the field was modified by checking the document modified status
        fieldwidget = self.knownfactedit.fields[field.name][1]
        fieldchanged = fieldwidget.document().isModified()
        
        # Changed fields have their "generated" tag stripped. NB: ALWAYS update the fact (even if the
        # field hasn't changed) because we might have changed ANOTHER field to e.g. blank it, and now
        # by moving focus from the expression field we indicate that we want to fill it out.
        #
        # NB: be careful with this ternary statement! It's perfectly OK for field.value to be "", and if
        # that happens we CAN'T let fieldvalue in updatefact be None, or autoblanking gets broken.
        self.updatefact(fact, field.name, (fieldchanged and [pinyin.factproxy.unmarkgeneratedfield(field.value)] or [None])[0])
    
    def updatefact(self, fact, fieldname, fieldvalue):
        # Are we not in a Mandarin model?
        if not(anki.utils.findTag(self.config.modelTag, fact.model.tags)):
            return
        
        # Need a fact proxy because the updater works on dictionary-like objects
        factproxy = pinyin.factproxy.FactProxy(self.config.candidateFieldNamesByKey, fact)
        
        # Find which kind of field we have just moved off
        updater = None
        for key, updateablefieldname in factproxy.fieldnames.items():
            if fieldname == updateablefieldname:
                updater = self.buildupdater(key)
                break

        # Update the card, ignoring any errors
        if updater:
            pinyin.utils.suppressexceptions(lambda: updater.updatefact(factproxy, fieldvalue))
    
    def install(self):
        from anki.hooks import addHook, remHook
        
        # Install hook into focus event of Anki: we regenerate the model information when
        # the cursor moves from the Expression/Reading/whatever field to another field
        log.info("Installing focus hook")
        
        try:
            # On versions of Anki that still had Chinese support baked in, remove the
            # provided hook from this event before we replace it with our own:
            from anki.features.chinese import onFocusLost as oldHook
            remHook('fact.focusLost', oldHook)
        except ImportError:
            pass
        
        # Unconditionally add our new hooks to Anki
        addHook('makeField', self.makeField)
        addHook('fact.focusLost', self.onFocusLost)

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

#class FactEditorShortcutKeysHook(Hook):
#    def install(self):
#        from anki.hooks import wrap
#        import ankiqt.ui.facteditor
#
#        log.info("Installing a fact editor shortcut key hook")
#        ankiqt.ui.facteditor.FactEditor.setupFields = wrap(ankiqt.ui.facteditor.FactEditor.setupFields, self.setupShortcuts, "after")
#        self.setupShortcuts(self.mw.editor)

# Shrunk version of color shortcut plugin merged with Pinyin Toolkit to give that functionality without the seperate download.
# Original version by Damien Elmes <anki@ichi2.net>
#class ColorShortcutKeysHook(FactEditorShortcutKeysHook):
#    def setColor(self, editor, i, sandhify):
#        log.info("Got color change event for color %d, sandhify %s", i, sandhify)
#        
#        color = (self.config.tonecolors + self.config.extraquickaccesscolors)[i - 1]
#        if sandhify:
#            color = pinyin.transformations.sandhifycolor(color)
#        
#        focusededit = editor.focusedEdit()
#        
#        cursor = focusededit.textCursor()
#        focusededit.setTextColor(QColor(color))
#        cursor.clearSelection()
#        focusededit.setTextCursor(cursor)
#    
#    def setupShortcuts(self, editor):
#        # Loop through the 8 F[x] keys, setting each one up
#        # Note: Ctrl-F9 is the HTML editor. Don't do this as it causes a conflict
#        log.info("Setting up color shortcut keys on fact editor")
#        for i in range(1, 9):
#            for sandhify in [True, False]:
#                keysequence = (sandhify and pinyin.anki.keys.sandhiModifier + "+" or "") + pinyin.anki.keys.shortcutKeyFor(i)
#                QShortcut(QKeySequence(keysequence), editor.widget,
#                                lambda i=i, sandhify=sandhify: self.setColor(editor, i, sandhify))
#
#class BlankFactShortcutKeyHook(FactEditorShortcutKeysHook):
#    def blankFields(self, editor):
#        # Bit of an abuse of the FactProxy - but it works, since the fields are keyed off the field name,
#        # and the fact proxy doesn't actually care about the domain type at all
#        factproxy = pinyin.factproxy.FactProxy(self.config.candidateFieldNamesByKey, editor.fields)
#        for k in factproxy:
#            # Nick doesn't want expression to be blanked. We could hack it in:
#            #if k == "expression":
#            #    continue
#            # BUT if we do this then you need to explicitly change the expression to something else before
#            # the toolkit will regenerate the fields (because the remember value for the expression == the new one).
#            
#            _field, widget = factproxy[k]
#            widget.setText(u"")
#        
#        # FIXME: there is actually a bug here. If the user:
#        #  1) Has the Expression field selected
#        #  2) Blanks the fact
#        #  3) Reenters the same expression
#        #
#        # Then some of the fields may not be refreshed. The reason is that the knownfieldcontents in the
#        # FocusHook will be out of date and still contain the value from before the refresh. When we compare
#        # it with the new value, they will look the same.
#        #
#        # It's not that easy to fix this, and it's not likely to be a common use case anyway, so I'm ignoring it.
#    
#    def setupShortcuts(self, editor):
#        log.info("Setting up fact blanking shortcut key on fact editor")
#        QShortcut(QKeySequence("Ctrl+Alt+b"), editor.widget, lambda editor=editor: self.blankFields(editor))


   
class ToolMenuHook(Hook):
    pinyinToolkitMenu = None
    
    def install(self):
        # Install menu item
        log.info("Installing a menu hook (%s)", type(self))
        
        # Build and install the top level menu if it doesn't already exist
        if ToolMenuHook.pinyinToolkitMenu is None:
            ToolMenuHook.pinyinToolkitMenu = QMenu("Pinyin Toolkit", self.mw.form.menuTools)
            self.mw.form.menuTools.addMenu(ToolMenuHook.pinyinToolkitMenu)

        
        # Store the action on the class.  Storing a reference to it is necessary to avoid it getting garbage collected.
        self.action = QAction(self.__class__.menutext, self.mw)
        self.action.setStatusTip(self.__class__.menutooltip)
        self.action.setEnabled(True)
        
        if self.__class__.menutext == "About" or self.__class__.menutext == "Preferences":
            ToolMenuHook.pinyinToolkitMenu.addSeparator()

        # HACK ALERT: must use lambda here, or the signal never gets raised! I think this is due to garbage collection...
        # We try and make sure that we don't run the action if there is no deck presently, to at least suppress some errors
        # in situations where the users select the menu items (this is possible on e.g. OS X). It would be better to disable
        # the menu items entirely in these situations, but there is no suitable hook for that presently.
        self.mw.connect(self.action, SIGNAL('triggered()'), lambda: self.triggered())
        ToolMenuHook.pinyinToolkitMenu.addAction(self.action)

class MassFillHook(ToolMenuHook):
    def triggered(self):
        if not hasattr(self.mw, 'deck'):
            return showInfo(unicode("No deck selected 同志!", "UTF-8"))

        field = self.__class__.field
        log.info("User triggered missing information fill for %s" % field)
        
        for fact in utils.suitableFacts(self.config.modelTag, self.mw.deck):
            # Need a fact proxy because the updater works on dictionary-like objects
            factproxy = pinyin.factproxy.FactProxy(self.config.candidateFieldNamesByKey, fact)
            if field not in factproxy:
                continue
            
            self.buildupdater(field).updatefact(factproxy, None, **self.__class__.updatefactkwargs)
            
            # NB: very important to mark the fact as modified (see #105) because otherwise
            # the HTML etc won't be regenerated by Anki, so users may not e.g. get working
            # sounds that have just been filled in by the updater.
            fact.setModified(textChanged=True)
        
        # For good measure, mark the deck as modified as well (see #105)
        self.mw.deck.setModified()
    
        # DEBUG consider future feature to add missing measure words cards after doing so (not now)
        self.notifier.info(self.__class__.notification)

class MissingInformationHook(MassFillHook):
    menutext = 'Fill missing card data'
    menutooltip = 'Update all the cards in the deck with any missing information the Pinyin Toolkit can provide.'
    
    field = "expression"
    updatefactkwargs = {}
    
    notification = "All missing information has been successfully added to your deck."

class ReformatReadingsHook(MassFillHook):
    menutext = 'Reformat readings'
    menutooltip = 'Update all the readings in your deck with colorisation and tones according to your preferences.'
    
    field = "reading"
    updatefactkwargs = dict(alwaysreformat = True)
    
    notification = "All readings have been successfully reformatted."


class PreferencesHook(ToolMenuHook):
    menutext = "Preferences"
    menutooltip = "Configure the Pinyin Toolkit"
    
    def triggered(self):
        # NB: must import these lazily to break a loop between preferencescontroller and here
        import pinyin.forms.preferences
        import pinyin.forms.preferencescontroller

        log.info("User opened preferences dialog")
        
        # Instantiate and show the preferences dialog modally
        preferences = pinyin.forms.preferences.Preferences(self.mw)
        controller = pinyin.forms.preferencescontroller.PreferencesController(preferences, self.notifier, self.mediamanager, self.config)
        result = preferences.exec_()
        
        # We only need to change the configuration if the user accepted the dialog
        if result == QDialog.Accepted:
            # Update by the simple method of replacing the settings dictionaries: better make sure that no
            # other part of the code has cached parts of the configuration
            self.config.settings = controller.model.settings
            
            # Ensure this is saved in Anki's configuration
            utils.persistconfig(self.mw, self.config)

 
class HelpOnToolsHook(ToolMenuHook):
    menutext = 'About'
    menutooltip = 'Help for the Pinyin Toolkit available at our website.'

    def triggered(self):
        helpUrl = QUrl(u"http://batterseapower.github.com/pinyin-toolkit/")
        QDesktopServices.openUrl(helpUrl)


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
    FieldShrinkingHook,

    # Keybord hooks
     # ColorShortcutKeysHook,
     # BlankFactShortcutKeyHook,

    # Menu hooks
    MissingInformationHook,
    ReformatReadingsHook,
    PreferencesHook,
    HelpOnToolsHook,

    # Card display hooks
    TagRemovingHook
  ]
