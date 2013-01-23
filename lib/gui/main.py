# encoding=UTF-8
# Copyright © 2008, 2009, 2010, 2011 Jakub Wilk <jwilk@jwilk.net>
# Copyright © 2009 Mateusz Turcza <mturcza@mimuw.edu.pl>
# Copyright © 2011, 2012 Tomasz Olejniczak <tomek.87@poczta.onet.pl>
#
# This package is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This package is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

from __future__ import with_statement

APPLICATION_NAME = 'maleks'
LICENSE = 'GPL-2'

import sys
import itertools
import locale
import os.path
import threading
import tempfile
from Queue import Queue, Empty as QueueEmpty

import maleks.dependencies as __dependencies

import wx
import wx.lib.ogl
import wx.lib.newevent
import wx.lib.scrolledpanel
from wx.lib import splitter

import djvu.decode
import djvu.const

#from djvusmooth.djvused import StreamEditor
from maleks.gui.page import PageWidget, PercentZoom, OneToOneZoom, StretchZoom, FitWidthZoom, FitPageZoom
#from djvusmooth.gui.page import RENDER_NONRASTER_TEXT, RENDER_NONRASTER_MAPAREA
#from djvusmooth.gui.metadata import MetadataDialog
#from djvusmooth.gui.flatten_text import FlattenTextDialog
#from djvusmooth.gui.text_browser import TextBrowser
#from djvusmooth.gui.outline_browser import OutlineBrowser
#from djvusmooth.gui.maparea_browser import MapAreaBrowser
from maleks.gui.reg_browser import RegisterBrowser
from maleks.gui.window_reg_browser import WindowRegisterBrowser
from maleks.gui.struc_browser import StructureRegisterBrowser
from maleks.gui.entry_browser import EntryRegisterBrowser
from maleks.gui.new_entry_browser2 import NewEntryRegisterBrowser
from maleks.gui.hint_browser import HintRegisterBrowser
from maleks.gui.toppanel import TopPanel
from maleks.gui.msg_panel import MessagePanel
from maleks.gui.regbar import RegisterToolbar
from maleks.gui import dialogs
from maleks.gui.dialogs import CloneDialog
from maleks.gui.left_panel import MainIndicesPanel, SecondaryIndicesPanel, ControlPanel
#from djvusmooth.text import mangle as text_mangle
#import djvusmooth.models.metadata
#import djvusmooth.models.annotations
#import djvusmooth.models.text
#from djvusmooth import models
#from djvusmooth import external_editor
from maleks import config
from maleks.maleks import log
from maleks.maleks.fiche import StructureIndex, Configuration
from maleks.maleks.registers import HintRegister
from maleks.maleks.useful import stru, ustr, Counter, nvl
from maleks.gui.mode import Mode
from maleks.db.db import DBController

from maleks import __version__, __author__

from maleks.i18n import _

MENU_ICON_SIZE = (16, 16)
#DJVU_WILDCARD = _('DjVu files (*.djvu, *.djv)|*.djvu;*.djv|All files|*')

WxDjVuMessage, wx.EVT_DJVU_MESSAGE = wx.lib.newevent.NewEvent()

system_encoding = locale.getpreferredencoding()

if wx.__version__.startswith('2.8.'):
    wx.Choicebook = wx.Notebook
    wx.EVT_CHOICEBOOK_PAGE_CHANGED = wx.EVT_NOTEBOOK_PAGE_CHANGED

class OpenDialog(wx.DirDialog):

    def __init__(self, parent):
        #wx.FileDialog.__init__(self, parent, style = wx.OPEN, wildcard=DJVU_WILDCARD, message = _('Open a DjVu document'))
        wx.DirDialog.__init__(self, parent, style = wx.OPEN, message = _('Open directory with lexicographic data'))

#class TextModel(models.text.Text):
#
#    def __init__(self, document):
#        models.text.Text.__init__(self)
#        self._document = document
#
#    def reset_document(self, document):
#        self._document = document
#
#    def acquire_data(self, n):
#        text = self._document.pages[n].text
#        text.wait()
#        return text.sexpr

#class OutlineModel(models.outline.Outline):
#
#    def __init__(self, document):
#        self._document = document
#        models.outline.Outline.__init__(self)
#
#    def reset_document(self, document):
#        self._document = document
#
#    def acquire_data(self):
#        outline = self._document.outline
#        outline.wait()
#        return outline.sexpr

class PageProxy(object):
    #def __init__(self, page, text_model, annotations_model):
    def __init__(self, page):
        self._page = page
        #self._text = text_model
        #self._annotations = annotations_model

    @property
    def page_job(self):
        return self._page.decode(wait = False)

    #@property
    #def text(self):
    #    return self._text

    #@property
    #def annotations(self):
    #    return self._annotations

    #def register_text_callback(self, callback):
    #    self._text.register_callback(callback)

    #def register_annotations_callback(self, callback):
    #    self._annotations.register_callback(callback)

class DocumentProxy(object):

    #def __init__(self, document, outline):
    def __init__(self, document):
        self._document = document
        #self._outline = outline

    #@property
    #def outline(self):
    #    return self._outline

    #def register_outline_callback(self, callback):
    #    self._outline.register_callback(callback)

#class AnnotationsModel(models.annotations.Annotations):
#
#    def __init__(self, document_path):
#        models.annotations.Annotations.__init__(self)
#        self.__djvused = StreamEditor(document_path)
#
#    def reset_document(self, document):
#        pass # Nothing to do
#
#    def acquire_data(self, n):
#        djvused = self.__djvused
#        if n == models.SHARED_ANNOTATIONS_PAGENO:
#            djvused.select_shared_annotations()
#        else:
#            djvused.select(n + 1)
#        djvused.print_annotations()
#        s = '(%s)' % djvused.commit() # FIXME: optimize
#        try:
#            return djvu.sexpr.Expression.from_string(s)
#        except djvu.sexpr.ExpressionSyntaxError:
#            raise # FIXME

#class MetadataModel(models.metadata.Metadata):
#
#    def __init__(self, document):
#        models.metadata.Metadata.__init__(self)
#        self._document = document
#
#    def reset_document(self, document):
#        self._document = document
#
#    def acquire_data(self, n):
#        document_annotations = self._document.annotations
#        document_annotations.wait()
#        document_metadata = document_annotations.metadata
#        if n == models.SHARED_ANNOTATIONS_PAGENO:
#            result = document_metadata
#        else:
#            page_annotations = self._document.pages[n].annotations
#            page_annotations.wait()
#            page_metadata = page_annotations.metadata
#            result = {}
#            for k, v in page_metadata.iteritems():
#                if k not in document_metadata:
#                    pass
#                elif v != document_metadata[k]:
#                    pass
#                else:
#                    continue
#                result[k] = v
#        return result

#class PageTextCallback(models.text.PageTextCallback):
#
#    def __init__(self, owner):
#        self._owner = owner
#
#    def notify_node_change(self, node):
#        self._owner.dirty = True
#
#    def notify_node_children_change(self, node):
#        self._owner.dirty = True
#
#    def notify_node_select(self, node):
#        type = str(node.type)
#        text = _('[Text layer]') + ' ' + _(type)
#        if node.is_leaf():
#            text += ': %s' % node.text
#        self._owner.SetStatusText(text)
#
#    def notify_node_deselect(self, node):
#        self._owner.SetStatusText('')
#
#    def notify_tree_change(self, node):
#        self._owner.dirty = True

#class OutlineCallback(models.outline.OutlineCallback):
#
#    def __init__(self, owner):
#        self._owner = owner
#
#    def notify_tree_change(self, node):
#        self._owner.dirty = True
#
#    def notify_node_change(self, node):
#        self._owner.dirty = True
#
#    def notify_node_children_change(self, node):
#        self._owner.dirty = True
#
#    def notify_node_select(self, node):
#        try:
#            self._owner.SetStatusText(_('Link: %s') % node.uri)
#        except AttributeError:
#            pass

#class PageAnnotationsCallback(models.annotations.PageAnnotationsCallback):
#
#    def __init__(self, owner):
#        self._owner = owner
#
#    def notify_node_change(self, node):
#        self._owner.dirty = True
#    def notify_node_add(self, node):
#        self._owner.dirty = True
#    def notify_node_delete(self, node):
#        self._owner.dirty = True
#    def notify_node_replace(self, node, other_node):
#        self._owner.dirty = True
#
#    def notify_node_select(self, node):
#        try:
#            self._owner.SetStatusText(_('Link: %s') % node.uri)
#        except AttributeError:
#            pass
#
#    def notify_node_deselect(self, node):
#        self._owner.SetStatusText('')

# TODO: D tutaj bo ma cykliczne zaleznosci wzgledem gui.main
class PreviewDialog(wx.Frame):

    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.__context = Context(self)
        self.Bind(wx.EVT_DJVU_MESSAGE, self.__handleMessage)
        self.SetSize((350, 475))
        panel = wx.Panel(self)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.__label = wx.StaticText(panel, wx.ID_ANY, _('Preview'))
        self.__scrolledPanel = ScrolledPanel(panel)
        mainSizer.Add(self.__label, 0, wx.ALIGN_CENTER | wx.EXPAND)
        mainSizer.Add(self.__scrolledPanel, 1, wx.ALIGN_CENTER | wx.EXPAND)
        panel.SetSizer(mainSizer)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.__scrolledPanel.SetSizer(sizer)
        self.__scrolledPanel.SetupScrolling()
        self.__widget = PageWidget(self.__scrolledPanel)
        self.__widget.render_mode = djvu.decode.RENDER_COLOR
        self.__scrolledPanel.Bind(wx.EVT_SIZE, self.__widget.on_parent_resize)
        sizer.Add(self.__widget, 0, wx.ALL, 0)
        self.Bind(wx.EVT_KEY_UP, self.__onKey)
        panel.Bind(wx.EVT_KEY_UP, self.__onKey)
        self.__widget.Bind(wx.EVT_KEY_UP, self.__onKey)
        self.__scrolledPanel.Bind(wx.EVT_KEY_UP, self.__onKey)
        self.__pageJob = None
        self.__pageProxy = None
        self.__widget.zoom = FitPageZoom()
        self.__index = None
        self.__ficheNo = 0
        li = []
        self.__installShortcut(li, wx.ACCEL_CTRL, ord('V'), self.__onClose)
        self.SetAcceleratorTable(wx.AcceleratorTable(li))

    def setTitle(self, title):
        self.__label.SetLabel(title)

    def __onClose(self, event):
        self.__parent.close_preview()

    def setParent(self, parent):
        self.__parent = parent

    def setIndex(self, index):
        self.__index = index

    def showFicheByNo(self, ficheNo):
        self.__ficheNo = ficheNo
        self.__show(self.__index.getFiche(self.__ficheNo).getDjVuPath())
        diff = self.__ficheNo - self.__original
        if diff > 0:
            self.setTitle(_('Preview') + u": " + str(diff) + u" " + _('after'))
        elif diff < 0:
            self.setTitle(_('Preview') + u": " + str(-diff) + u" " + _('before'))
        else:
            self.setTitle(_('Preview'))

    def __onKey(self, event):
        if event.GetKeyCode() == wx.WXK_UP:
            self.__ficheNo -= 1
            if self.__ficheNo < 0:
                self.__ficheNo = 0
            self.showFicheByNo(self.__ficheNo)
        elif event.GetKeyCode() == wx.WXK_DOWN:
            self.__ficheNo += 1
            if self.__ficheNo == self.__index.getFicheNo():
                self.__ficheNo -= 1
            self.showFicheByNo(self.__ficheNo)
        elif event.GetKeyCode() == wx.WXK_ESCAPE:
            self.__parent.close_preview()
    
    def show(self, ficheNo):
        self.Show()
        self.__original = ficheNo
        self.showFicheByNo(ficheNo)
        self.__widget.SetFocus()

    def __handleMessage(self, event):
        message = event.message
        if isinstance(message, (djvu.decode.RedisplayMessage, djvu.decode.RelayoutMessage)):
            if self.__pageJob is message.page_job:
                self.updatePageWidget()
    
    def __installShortcut(self, li, accel, key, method):
        idd = wx.NewId()
        self.Bind(wx.EVT_MENU, method, id=idd)
        li.append((accel, key, idd))
        return li

    def __show(self, url):
        try:
            self.__document = self.__context.new_document(djvu.decode.FileURI(url))
            self.updatePageWidget(newPage=True)
            for i in range(0, 200):
                self.updatePageWidget()
        except djvu.decode.JobFailed:
            pass # TODO: !A co tutaj?

    def updatePageWidget(self, newPage=False):
        if self.__pageJob == None or newPage:
            self.__widget.Show()
            page = self.__document.pages[0]
            self.__pageJob = page.decode(wait=True)
            self.__pageProxy = PageProxy(page=page)
        self.__widget.page = self.__pageProxy

class ScrolledPanel(wx.lib.scrolledpanel.ScrolledPanel):

    def OnChildFocus(self, event):
        # We *don't* want to scroll to the child window which just got the focus.
        # So just skip the event:
        event.Skip()

class MainWindow(wx.Frame):

    def _menu_item(self, menu, caption, help, method, style = wx.ITEM_NORMAL, icon = None, id = wx.ID_ANY, check=False):
        item = wx.MenuItem(menu, id, caption, help, style)        
        self.menu_items.setdefault(method, item)
        if icon is not None:
            bitmap = wx.ArtProvider_GetBitmap(icon, wx.ART_MENU, MENU_ICON_SIZE)
            item.SetBitmap(bitmap)
        self.Bind(wx.EVT_MENU, method, item)
        menu.AppendItem(item)
        if check:
            item.Check()
        return item

    @apply
    def default_xywh():
        def get(self):
            return tuple(
                self._config.read_int('main_window_%s' % key, value)
                for key, value
                in (('x', -1), ('y', -1), ('width', 640), ('height', 480))
            )
        def set(self, (x, y, w, h)):
            for key, value in dict(x=x, y=y, width=w, height=h).iteritems():
                self._config['main_window_%s' % key] = value
        return property(get, set)

    @apply
    def default_splitter_sash():
        def get(self):
            return self._config.read_int('main_window_splitter_sash', 160)
        def set(self, value):
            #self._config['main_window_splitter_sash'] = value
            pass
        return property(get, set)

    @apply
    def default_left_splitter_sash():
        def get(self):
            return self._config.read_int('main_window_splitter_sash_left', 660)
        def set(self, value):
            #self._config['main_window_splitter_sash_left'] = value
            pass
        return property(get, set)

    @apply
    def default_top_splitter_sash():
        def get(self):
            return self._config.read_int('main_window_splitter_sash_top', 100)
        def set(self, value):
            #self._config['main_window_splitter_sash_left'] = value
            pass
        return property(get, set)

    @apply
    def default_sidebar_shown():
        def get(self):
            return self._config.read_bool('main_window_sidebar_shown', True)
        def set(self, value):
            self._config['main_window_sidebar_shown'] = value
        return property(get, set)

    @apply
    def default_topbar_shown():
        def get(self):
            return self._config.read_bool('main_window_topbar_shown', True)
        def set(self, value):
            self._config['main_window_topbar_shown'] = value
        return property(get, set)

    @apply
    def default_left_sidebar_shown():
        def get(self):
            return self._config.read_bool('main_window_left_sidebar_shown', True)
        def set(self, value):
            self._config['main_window_left_sidebar_shown'] = value
        return property(get, set)

    @apply
    def ficheId():
        def get(self):
            return self._ficheId
        def set(self, value):
            if (not self.goingBack) and (self.history == [] or self.history[-1] != self._ficheId) and self._ficheId != None:
                self.history.append(self._ficheId)
            self._ficheId = value
        return property(get, set)

    def __str(self, li):
        res = ''
        for el in li:
            el = stru(el).replace('\\', '\\\\').replace(',', '\\,')
            res += el + ','
        if res != '':
            res = res[:-1]
        return res

    @apply
    def recently_used():
        def get(self):
            return self._config.read_list('recently_used', [])
        def set(self, value):
            self._config['recently_used'] = self.__str(value)
        return property(get, set)

    #@apply
    #def default_editor_path():
    #    def get(self):
    #        return self._config.read('external_editor', '') or None
    #    def set(self, value):
    #        self._config['external_editor'] = value or ''
    #    return property(get, set)

    def save_defaults(self):
        self._config.flush()

    #def setup_external_editor(self):
    #    editor_path = self.default_editor_path
    #    if editor_path is None:
    #        self.external_editor = external_editor.RunMailcapEditor()
    #    else:
    #        self.external_editor = external_editor.CustomEditor(*editor_path.split())

    def __init__(self):
        self.recently_used_menu = {}
        self._config = wx.GetApp().config
        x, y, w, h = self.default_xywh
        wx.Frame.__init__(self, None, pos=(x, y), size=(w, h))
        #self.setup_external_editor()
        self.Bind(wx.EVT_DJVU_MESSAGE, self.handle_message)
        self.context = Context(self)
        #self._page_text_callback = PageTextCallback(self)
        #self._page_annotations_callback = PageAnnotationsCallback(self)
        #self._outline_callback = OutlineCallback(self)
        self.status_bar = self.CreateStatusBar(3, style = wx.ST_SIZEGRIP)
        log.setLevel(self._config.read("loglevel", "OP"))
        
        ##self.super_splitter = wx.SplitterWindow(self, style = wx.SP_LIVE_UPDATE)
        ##self.super_splitter.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.on_left_splitter_sash_changed)
        
        self.super_splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        self.super_splitter.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.on_top_splitter_sash_changed)
        
        #self.splitter = wx.SplitterWindow(self, style = wx.SP_LIVE_UPDATE)
        ##self.splitter = wx.SplitterWindow(self.super_splitter)#, style = wx.SP_LIVE_UPDATE)
        ##self.splitter.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.on_splitter_sash_changed)
        
        self.msg_panel = MessagePanel(self.super_splitter)
        self.msg_panel.setParent(self)
        
        self.splitter = splitter.MultiSplitterWindow(self.super_splitter, style = wx.SP_LIVE_UPDATE)
        #self.splitter = splitter.MultiSplitterWindow(self, style = wx.SP_LIVE_UPDATE)
        self.splitter.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.on_splitter_sash_changed)
        self.sidebar_shown = False

        self.dBController = DBController(self._config)
        if not self.dBController.valid():
            self.error_box(_('Wrong database configuration'))
            self.dBController = None

        ##self.left_sidepanel = wx.Panel(self.super_splitter, wx.ID_ANY)
        self.left_sidepanel = wx.Panel(self.splitter, wx.ID_ANY)
        self.left_sizer = wx.BoxSizer(wx.VERTICAL)
        self.left_sidebar = wx.Choicebook(self.left_sidepanel, wx.ID_ANY)
        self.left_control = ControlPanel(self.left_sidepanel, wx.ID_ANY)
        self.left_control.addListener(self)
        self.mainind_panel = MainIndicesPanel(self.left_sidebar)
        self.secind_panel = SecondaryIndicesPanel(self.left_sidebar)
        self.left_sidebar.AddPage(self.mainind_panel, _('Main Indices'))
        self.left_sidebar.AddPage(self.secind_panel, _('Secondary Indices'))
        self.left_sizer.Add(self.left_sidebar, 1, wx.EXPAND)
        self.left_sizer.Add(self.left_control, 0, wx.EXPAND)
        self.left_sidepanel.SetSizer(self.left_sizer)
        
        self.sidepanel = wx.Panel(self.splitter, wx.ID_ANY)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.register_search = wx.TextCtrl(self.sidepanel, wx.ID_ANY)
        self.register_search.Bind(wx.EVT_TEXT, self.register_search_input)
        self.register_search.Bind(wx.EVT_KEY_UP, self.register_search_key)
        self.regbar = RegisterToolbar(self.sidepanel, wx.ID_ANY)
        self.regbar.addListener(self) 
        
        #self.sidebar = wx.Choicebook(self.splitter, wx.ID_ANY)
        self.sidebar = wx.Choicebook(self.sidepanel, wx.ID_ANY)
        #self.text_browser = TextBrowser(self.sidebar)
        #self.outline_browser = OutlineBrowser(self.sidebar)
        #self.maparea_browser = MapAreaBrowser(self.sidebar)
        #self.taskreg_browser = TaskRegisterBrowser(self.sidebar)
        self.taskreg_browser = RegisterBrowser(self.sidebar, style=wx.LC_SINGLE_SEL | wx.LC_NO_HEADER | wx.LC_REPORT)
        self.strucreg_browser = StructureRegisterBrowser(self.sidebar, style=wx.LC_SINGLE_SEL | wx.LC_NO_HEADER | wx.LC_REPORT)
        self.entryreg_browser = EntryRegisterBrowser(self.sidebar, style=wx.LC_SINGLE_SEL | wx.LC_NO_HEADER | wx.LC_REPORT)
        self.new_entryreg_browser = NewEntryRegisterBrowser(self.sidebar, style=wx.LC_SINGLE_SEL | wx.LC_NO_HEADER | wx.LC_REPORT)
        self.entryreg_browser.setDBController(self.dBController)
        self.new_entryreg_browser.setDBController(self.dBController)
        self.new_entryreg_browser.setMessagePanel(self.msg_panel)
        self.hintreg_browser = HintRegisterBrowser(self.sidebar, style=wx.LC_SINGLE_SEL | wx.LC_NO_HEADER | wx.LC_REPORT)
        self.bookreg_browser = RegisterBrowser(self.sidebar, style=wx.LC_SINGLE_SEL | wx.LC_NO_HEADER | wx.LC_REPORT)
        #self.sidebar.AddPage(self.outline_browser, _('Outline'))
        #self.sidebar.AddPage(self.maparea_browser, _('Hyperlinks'))
        #self.sidebar.AddPage(self.text_browser, _('Text'))
        self.sidebar.AddPage(self.taskreg_browser, _('Task Register'))
        self.sidebar.AddPage(self.strucreg_browser, _('Structure Register'))
        self.sidebar.AddPage(self.entryreg_browser, _('Multilevel Register'))
        self.sidebar.AddPage(self.new_entryreg_browser, _('Entry Register'))
        self.sidebar.AddPage(self.hintreg_browser, _('Hint Register'))
        self.sidebar.AddPage(self.bookreg_browser, _('Bookmark Register'))
        self.sidebar.Bind(
            wx.EVT_CHOICEBOOK_PAGE_CHANGED,
            #self.on_sidebar_page_changed
            self._on_sidebar_page_changed(
                #self.on_display_no_nonraster,
                #self.on_display_maparea,
                #self.on_display_text)
                self.on_display_taskreg,
                self.on_display_strucreg,
                self.on_display_entryreg,
                self.on_display_new_entryreg,
                self.on_display_hintreg,
                self.on_display_bookreg
            )
        )
        for widget in [self.taskreg_browser, self.strucreg_browser, self.entryreg_browser, self.new_entryreg_browser, self.hintreg_browser, self.bookreg_browser]:
            widget.addListener(self)
        self.sidebar.ChangeSelection(1)
        
        self.main_panel = wx.Panel(self.splitter)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.top_panel = TopPanel(self.main_panel)
        self.top_panel.addListener(self)
        #self.top_panel = wx.TextCtrl(self.main_panel, wx.ID_ANY)
        
        #self.scrolled_panel = ScrolledPanel(self.splitter)
        self.scrolled_panel = ScrolledPanel(self.main_panel)
        #self.splitter.SetSashGravity(0.2)
        #self.super_splitter.SetSashGravity(0.9)
        self.active_register = self.strucreg_browser
        
        self.main_sizer.Add(self.top_panel, 0, wx.ALIGN_CENTER | wx.EXPAND)
        self.main_sizer.Add(self.scrolled_panel, 1, wx.ALIGN_CENTER | wx.EXPAND)
        self.main_panel.SetSizer(self.main_sizer)
        
        self.sizer.Add(self.register_search, 0, wx.ALIGN_CENTER | wx.EXPAND)
        self.sizer.Add(self.regbar, 0, wx.ALIGN_LEFT | wx.EXPAND)
        self.sizer.Add(self.sidebar, 1, wx.ALIGN_CENTER | wx.ALIGN_TOP | wx.EXPAND)
        self.sidepanel.SetSizer(self.sizer)
        
        #self.Bind(wx.EVT_KEY_DOWN, self.on_char)
        
        self.splitter.InsertWindow(0, self.main_panel)
        self.do_show_topbar()
        self.do_show_left_sidebar()
        self.do_show_sidebar()
        if not self.default_left_sidebar_shown:
            self.do_hide_left_sidebar()
        if not self.default_sidebar_shown:
            self.do_hide_sidebar()
        if not self.default_topbar_shown:
            self.do_hide_topbar()
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.scrolled_panel.SetSizer(sizer)
        self.scrolled_panel.SetupScrolling()
        self.page_widget = PageWidget(self.scrolled_panel)
        #self.page_widget.Bind(wx.EVT_CHAR, self.on_char)
        self.scrolled_panel.Bind(wx.EVT_SIZE, self.page_widget.on_parent_resize)
        sizer.Add(self.page_widget, 0, wx.ALL, 0)
        self.menu_items = {}
        self.editable_menu_items = []
        self.saveable_menu_items = []
        self._setup_menu()
        self.modes = []
        self._setup_modes()
        self._use_mode(self.modes[0])
        self.dirty = False # ta flaga informuje, czy do wykazu podpowiedzi
            # dodane zostaly jakies elementy
        self.do_open(None)
        self.Bind(wx.EVT_CLOSE, self.on_exit)
        self.register_search.Bind(wx.EVT_KEY_DOWN, self.on_regbar_enter, self.register_search)
        
        self.notify = True
        self.__closing = False # TODO: NOTE pomocne w zwalczaniu segmentation fault przy wyjsciu z aplikacji
        self._disable_page_change()
        
        self.page_widget.zoom = FitPageZoom()
        self.history = []
        self.actual_entry = None
        self.entry_history_index = 0
        self._ficheId = None
        self.goingBack = False
        self.fiche_for_locate = None
        self.locate = 0
        self.ignore_entries = False
        self.preview = None
        
        #self.taskreg_browser.Bind(wx.EVT_SET_FOCUS, self.defocus, self.taskreg_browser)

    #def defocus(self, event):
    #    #print "defocus"
    #    self.page_widget.SetFocus()

    def _setup_menu(self):
        menu_bar = wx.MenuBar()
        menu_bar.Append(self._create_file_menu(), _('&File'))
        #menu_bar.Append(self._create_edit_menu(), _('&Edit'))
        menu_bar.Append(self._create_view_menu(), _('&View'))
        menu_bar.Append(self._create_go_menu(), _('&Go'))
        menu_bar.Append(self._create_operations_menu(), _('&Operations'))
        menu_bar.Append(self._create_settings_menu(), _('&Settings'))
        menu_bar.Append(self._create_help_menu(), _('&Help'))
        self.SetMenuBar(menu_bar)

    def _create_file_menu(self):
        menu = wx.Menu()
        #self._menu_item(menu, _('&Open') + '\tCtrl+O', _('Open a DjVu document'), self.on_open, icon=wx.ART_FILE_OPEN)
        self._menu_item(menu, _('&Open'), _('Open a DjVu document'), self.on_open, icon=wx.ART_FILE_OPEN)
        #save_menu_item = self._menu_item(menu, _('&Save') + '\tCtrl+S', _('Save the document'), self.on_save, icon=wx.ART_FILE_SAVE)
        #close_menu_item = self._menu_item(menu, _('&Close') + '\tCtrl+W', _('Close the document'), self.on_close, id=wx.ID_CLOSE)
        close_menu_item = self._menu_item(menu, _('&Close'), _('Close the document'), self.on_close, id=wx.ID_CLOSE)
        menu.AppendSeparator()
        submenu = wx.Menu()
        for el in self.recently_used:
            idd = wx.NewId()
            self._menu_item(submenu, el, _(u'Open file: ') + ustr(el), self.on_recently_used, id=idd)
            self.recently_used_menu.setdefault(idd, el)
        menu.AppendMenu(wx.ID_ANY, _('&Recently used files'), submenu)    
        menu.AppendSeparator()
        export_bookmarks_menu_item = self._menu_item(menu, _('&Export bookmarks'), _('Export bookmarks as task register'), self.on_export_bookmarks)
        self.editable_menu_items += close_menu_item,
        #self.saveable_menu_items += save_menu_item,
        self.editable_menu_items += export_bookmarks_menu_item,
        menu.AppendSeparator()
        #self._menu_item(menu, _('&Quit') + '\tCtrl+Q', _('Quit the application'), self.on_exit, icon=wx.ART_QUIT)
        self._menu_item(menu, _('&Quit'), _('Quit the application'), self.on_exit, icon=wx.ART_QUIT)
        return menu

#    def _create_edit_menu(self):
#        menu = wx.Menu()
#        self._menu_item(menu, _('&Metadata') + '\tCtrl+M', _('Edit the document or page metadata'), self.on_edit_metadata)
#        submenu = wx.Menu()
#        self._menu_item(submenu, _('&External editor') + '\tCtrl+T', _('Edit page text in an external editor'), self.on_external_edit_text)
#        self._menu_item(submenu, _('&Flatten'), _('Remove details from page text'), self.on_flatten_text)
#        menu.AppendMenu(wx.ID_ANY, _('&Text'), submenu)
#        submenu = wx.Menu()
#        self._menu_item(submenu, _('&Bookmark this page') + '\tCtrl+B', _('Add the current to document outline'), self.on_bookmark_current_page)
#        self._menu_item(submenu, _('&External editor'), _('Edit document outline in an external editor'), self.on_external_edit_outline)
#        self._menu_item(submenu, _('&Remove'), _('Remove document outline'), self.on_remove_outline)
#        menu.AppendMenu(wx.ID_ANY, _('&Outline'), submenu)
#        return menu

    def _create_view_menu(self):
        menu = wx.Menu()
        submenu = wx.Menu()
        for caption, help, method, id in \
        [
            (_('Zoom &in'),  _('Increase the magnification'), self.on_zoom_in, wx.ID_ZOOM_IN),
            (_('Zoom &out'), _('Decrease the magnification'), self.on_zoom_out, wx.ID_ZOOM_OUT),
        ]:
            self._menu_item(submenu, caption, help, method, id = id or wx.ID_ANY)
        submenu.AppendSeparator()
        for caption, help, zoom, id, check in \
        [
            (_('Fit &width'),  _('Set magnification to fit page width'),  FitWidthZoom(), None, False),
            (_('Fit &page'),   _('Set magnification to fit page'),        FitPageZoom(),  wx.ID_ZOOM_FIT, True),
            (_('&Stretch'),    _('Stretch the image to the window size'), StretchZoom(),  None, False),
            (_('One &to one'), _('Set full resolution magnification.'),   OneToOneZoom(), wx.ID_ZOOM_100, False),
        ]:
            self._menu_item(submenu, caption, help, self.on_zoom(zoom), style=wx.ITEM_RADIO, id = id or wx.ID_ANY, check=check)
        submenu.AppendSeparator()
        self.zoom_menu_items = {}
        for percent in 300, 200, 150, 100, 75, 50, 25:
            item = self._menu_item(
                submenu,
                '%d%%' % percent,
                _('Magnify %d%%') % percent,
                self.on_zoom(PercentZoom(percent)),
                style=wx.ITEM_RADIO
            )
            #if percent == 100:
            #    item.Check()
            self.zoom_menu_items[percent] = item
        menu.AppendMenu(wx.ID_ANY, _('&Zoom'), submenu)
        submenu = wx.Menu()
        for caption, help, method in \
        [
            (_('&Color') + '\tAlt+C', _('Display everything'),                                            self.on_display_everything),
            (_('&Stencil'),           _('Display only the document bitonal stencil'),                     self.on_display_stencil),
            (_('&Foreground'),        _('Display only the foreground layer'),                             self.on_display_foreground),
            (_('&Background'),        _('Display only the background layer'),                             self.on_display_background),
            (_('&None') + '\tAlt+N',  _('Neither display the foreground layer nor the background layer'), self.on_display_none)
        ]:
            self._menu_item(submenu, caption, help, method, style=wx.ITEM_RADIO)
        menu.AppendMenu(wx.ID_ANY, _('&Image'), submenu)
        #submenu = wx.Menu()
        #_tmp_items = []
        #for caption, help, method in \
        #[
        #    (_('&None'),                   _('Don\'t display non-raster data'),   self.on_display_no_nonraster),
        #    (_('&Hyperlinks') + '\tAlt+H', _('Display overprinted annotations'), self.on_display_maparea),
        #    (_('&Text') + '\tAlt+T',       _('Display the text layer'),          self.on_display_text),
        #]:
        #    _tmp_items += self._menu_item(submenu, caption, help, method, style=wx.ITEM_RADIO),
        #self._menu_item_display_no_nonraster, self._menu_item_display_maparea, self._menu_item_display_text = _tmp_items
        #del _tmp_items
        #self._menu_item_display_no_nonraster.Check()
        #menu.AppendMenu(wx.ID_ANY, _('&Non-raster data'), submenu)
        #self._menu_item(menu, _('&Refresh') + '\tCtrl+L', _('Refresh the window'), self.on_refresh)
        return menu

    def _create_go_menu(self):
        menu = wx.Menu()
        for caption, help, method, icon in \
        [
            #(_('&First page') + '\tCtrl-Home', _('Jump to first document page'),    self.on_first_page,    None),
            #(_('&Previous page') + '\tPgUp',   _('Jump to previous document page'), self.on_previous_page, wx.ART_GO_UP),
            #(_('&Next page') + '\tPgDn',       _('Jump to next document page'),     self.on_next_page,     wx.ART_GO_DOWN),
            #(_('&Last page') + '\tCtrl-End',   _('Jump to last document page'),     self.on_last_page,     None),
            #(_(u'&Go to page…') + '\tCtrl-G',  _(u'Jump to page…'),                 self.on_goto_page,     None)
            (_('&First page'), _('Jump to first document page'),    self.on_first_page,    None),
            (_('&Previous page'),   _('Jump to previous document page'), self.on_previous_page, wx.ART_GO_UP),
            (_('&Next page'),       _('Jump to next document page'),     self.on_next_page,     wx.ART_GO_DOWN),
            (_('&Last page'),   _('Jump to last document page'),     self.on_last_page,     None),
            (_(u'&Go to page…'),  _(u'Jump to page…'),                 self.on_goto_page,     None)
        ]:
            self._menu_item(menu, caption, help, method, icon = icon)
        return menu

    def _create_operations_menu(self):
        menu = wx.Menu()
        for caption, help, method, icon in \
        [
            #(_(u'&Reset database'), _(u'Remove entries from database'), self.on_reset_db, None),
            (_(u'&Dump log to file'), _(u'Dump current log to file'), self.on_dump_log, None),
            (_(u'Delete &logs'), _(u'Delete log files'), self.on_delete_logs, None),
            (_(u'&Clone fiche'), _(u'Clones fiche'), self.on_clone_fiche, None),
            (_(u'&Load task register'), _(u'Load task register from file'), self.on_choose_register, None)
        ]:
            self._menu_item(menu, caption, help, method, icon = icon)
        return menu

    def _create_settings_menu(self):
        menu = wx.Menu()
        #sidebar_menu_item = self._menu_item(menu, _('Show &sidebar') + '\tF9', _('Show/hide the sidebar'), self.on_show_sidebar, style=wx.ITEM_CHECK)
        sidebar_menu_item = self._menu_item(menu, _('Show &register panel'), _('Show/hide the register panel'), self.on_show_sidebar, style=wx.ITEM_CHECK)
        if self.default_sidebar_shown:
            sidebar_menu_item.Check()
        #self._menu_item(menu, _(u'External editor…'), _('Setup an external editor'), self.on_setup_external_editor)
        self._menu_item(menu, _('&Work mode'), _('Set work mode'), self.on_set_work_mode)
        return menu

    def _create_help_menu(self):
        menu = wx.Menu()
        #self._menu_item(menu, _('&About') + '\tF1', _('More information about this program'), self.on_about, id=wx.ID_ABOUT)
        self._menu_item(menu, '&Skróty klawiaturowe', 'Lista skrótów klawiaturowych', self.on_shortcuts)
        self._menu_item(menu, _('&About'), _('More information about this program'), self.on_about, id=wx.ID_ABOUT)
        return menu

    #def on_setup_external_editor(self, event):
    #    dialog = wx.TextEntryDialog(self,
    #        caption=_('Setup an external editor'),
    #        message=_('Enter path to your favourite text editor.')
    #    )
    #    try:
    #        dialog.SetValue(self.default_editor_path or '')
    #        if dialog.ShowModal() == wx.ID_OK:
    #            self.default_editor_path = dialog.GetValue()
    #            self.setup_external_editor()
    #    finally:
    #        dialog.Destroy()
    
    def _disable_page_change(self):
        if not self.__closing:
            self.menu_items[self.on_first_page].Enable(False)
            self.menu_items[self.on_previous_page].Enable(False)
            self.menu_items[self.on_next_page].Enable(False)
            self.menu_items[self.on_last_page].Enable(False)
            self.menu_items[self.on_goto_page].Enable(False)

    def _enable_page_change(self):
        self.menu_items[self.on_first_page].Enable(True)
        self.menu_items[self.on_previous_page].Enable(True)
        self.menu_items[self.on_next_page].Enable(True)
        self.menu_items[self.on_last_page].Enable(True)
        self.menu_items[self.on_goto_page].Enable(True)
    
    def _install_shortcut(self, li, accel, key, method):
        idd = wx.NewId()
        self.Bind(wx.EVT_MENU, method, id=idd)
        li.append((accel, key, idd))
        return li

    ENTRY_HISTORY_LIMIT = 100

    def addToHistory(self, entry):
        log.log("addToHistory", [entry, self.entry_history], 0)
        if (len(self.entry_history) == 0) or (len(self.entry_history) > 0 and self.entry_history[-1] != ustr(entry)):
            if len(self.entry_history) > MainWindow.ENTRY_HISTORY_LIMIT:
                self.entry_history = self.entry_history[1:]
            self.entry_history.append(ustr(entry))
        log.log("addToHistory return", [self.entry_history], 1)

    def on_nav_history_prev(self, event):
        log.op("on_nav_history_prev", [self.entry_history, self.entry_history_index, self.top_panel.getEditPanelContent()], 0)
        if len(self.entry_history) != 0:
            if not self.browsing_entry_history:
                self.browsing_entry_history = True
                self.actual_entry = self.top_panel.getEditPanelContent()
                self.entry_history_index = len(self.entry_history) - 1
                #print "started", "show", self.entry_history_index, "of", self.entry_history, self.actual_entry
            elif self.entry_history_index > 0:
                #print "decrease", self.entry_history_index
                self.entry_history_index -= 1
                #print "show", self.entry_history_index, "of", self.entry_history, self.actual_entry
            self.top_panel.setEntry(self.entry_history[self.entry_history_index], browsingHistory=True)
        log.opr("on_nav_history_prev return", [self.entry_history, self.entry_history_index], 1)

    def on_nav_history_next(self, event):
        log.op("on_nav_history_next", [self.entry_history, self.entry_history_index, self.top_panel.getEditPanelContent()], 0)
        if len(self.entry_history) != 0 and self.browsing_entry_history:
            if self.entry_history_index < len(self.entry_history):
                #print "increase", self.entry_history_index
                self.entry_history_index += 1
            if self.entry_history_index < len(self.entry_history):
                #print "show", self.entry_history_index, "of", self.entry_history, self.actual_entry
                self.top_panel.setEntry(self.entry_history[self.entry_history_index], browsingHistory=True)
            else:
                #print "show actual entry", self.entry_history, self.actual_entry
                self.top_panel.setEntry(self.actual_entry, browsingHistory=True)
        log.opr("on_nav_history_next return", [self.entry_history, self.entry_history_index], 1)
            

    def stop_browsing_entry_history(self, event):
        log.log("stop_browsing_entry_history", [event], 0)
        if self.browsing_entry_history:
            self.browsing_entry_history = False
        log.log("stop_browsing_entry_history return", [], 1)
        #print "invalidated"

    # TODO: NOTE przeniesione do skryptu
    #def on_reset_db(self, event):
    #    log.op("on_reset_db", [event], 0)
    #    if self.dBController != None:
    #        if wx.MessageDialog(self, _("Are you sure?"), _("Database reset"), wx.YES_NO).ShowModal() == wx.ID_YES:
    #            self.dBController.reset()
    #    log.opr("on_reset_db return", [], 1)

    def on_dump_log(self, event):
        if self.dBController != None:
            log.dumpDatabase(self.dBController.dumpDatabase())
            dialog = wx.FileDialog(self, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT, message = _('Dump log to file'))
            dialog.SetDirectory(os.getcwd())#self._config.read('save_dir', ''))
            try:
                if dialog.ShowModal() == wx.ID_OK:
                    #self._config['save_dir'] = os.path.dirname(dialog.GetPath()) or ''
                    fileToSave = os.path.abspath(dialog.GetPath())
                    os.system("cp " + log.path + " " + fileToSave)
            #except IOError:
            #    wx.MessageBox()
            finally:
                dialog.Destroy()
            self.page_widget.SetFocus()

    def on_delete_logs(self, event):
        for filee in os.listdir(log.dirPath):
            if len(filee) > 8 and filee[:4] == "log_" and filee[-4:] == ".txt":
                os.remove(log.dirPath + os.sep + filee)
        self.msg_panel.showMessage(_('Logs deleted'))
        #os.system("rm -f " + log.dirPath + "/log_*")

    # TODO: A rozne przypadki bledow:
    
    def entry_for_message(self, ignored, target):
        if self.top_panel.getEditPanelContent() == '':
            if self.active_register == self.new_entryreg_browser and self.active_register.binarySearchActive() and self.active_register.hasTarget():
                return self.active_register.getTarget()
            else:
                return None
        else:
            return self.top_panel.getEditPanelContent()
    
    def on_edit_accept(self, event, binaryOK=False, target=None):
        #print "edit"
        #if self.active_register.binarySearchActive() and not binaryOK:
        #    return
        #from maleks.maleks.useful import Counter
        #c = Counter()
        log.op("on_edit_accept", [event, binaryOK, target, self.top_panel.getEditPanelContent()], 0)
        # TODO: C entryForMessage zostalo dodane o wiele pozniej na szybko, mozna to zrefaktoryzowac zeby
        # polaczyc je ze zmienna entry i tylko raz obliczac haslo
        entryForMessage = self.entry_for_message(binaryOK, target)
        if not binaryOK:
            self.acceptedFicheId = self.ficheId
        if entryForMessage != None and (not binaryOK):
            self.msg_panel.submit(self.acceptedFicheId, entryForMessage)
        import time
        if self.top_panel.getEditPanelContent() == '':
            if self.active_register == self.new_entryreg_browser and self.active_register.binarySearchActive() and (not binaryOK) and self.active_register.hasTarget():
                self.on_automatic_binary_accept(emptyPanel=True)
                if not binaryOK:
                    self.msg_panel.accept(self.acceptedFicheId, entryForMessage)
                log.opr("on_edit_accept return", [], 1)
                return
            elif binaryOK:
                entry = target if target != None else self.active_register.getTarget()
            else:
                self.error_box(_('Empty edit panel'))
                log.opr("on_edit_accept return", [], 2)
                return
        else:
            entry = self.top_panel.getEditPanelContent()
        log.opr("on_edit_accept entry", [entry], 3)
        ok = False
        #print "ok"
        if self.active_register == self.new_entryreg_browser and self.active_register.binarySearchActive():
            #print "A"
            if binaryOK or (not self.active_register.hasTarget()):
                (thisWrong, othersWrong) = self.active_register.wrongOrder(entry)
                if thisWrong:
                    self.msg_panel.wrongFiche(entry)
                elif othersWrong:
                    self.msg_panel.wrongOrder(entry)
            if not binaryOK:
                #print "B"
                if self.active_register.hasTarget():
                    #print "C"
                    self.on_automatic_binary_accept()
                    #print "D"
                    if not binaryOK:
                        self.msg_panel.accept(self.acceptedFicheId, entryForMessage)
                    log.opr("on_edit_accept return", [], 5)
                    return
                #print "E"
                self.active_register.prepareForActiveBinary()
                #print "F"
        #print "po"
        #print "poczatek", c
        elif self.active_register == self.new_entryreg_browser and not self.active_register.binarySearchActive():
            self.active_register.prepareForUpdateAfterAccept(self.ficheId) # TODO: A (***) to moze zajac troche czasu a
                # czy jest konieczne jezeli on_edit_accept zostalo wywolane z on_automatic_binary_accept zaraz po
                # zakonczeniu binarnego (jak w logu:
                # OP: ON_AUTOMATIC_BINARY_ACCEPT (0) Sun Feb 12 16:20:51 2012: False: <type 'bool'>; False: <type 'bool'>; (1, 'dwojako\xc5\x9b\xc4\x87', 'dziub'): <type 'tuple'>; 
                # ...
                # stop_binary_search (0) Sun Feb 12 16:20:51 2012: False: <type 'bool'>; 
                # ...
                # stop_binary_search return (1) Sun Feb 12 16:20:51 2012: 
                # OP: ON_EDIT_ACCEPT (0) Sun Feb 12 16:20:51 2012: None: <type 'NoneType'>; True: <type 'bool'>; dzielić: <type 'str'>; dwojdroże: <type 'unicode'>;
                # ...
                # NewEntryRegisterBrowser.prepareForUpdateAfterAccept ...
                # ) - bo binarne chyba samo odswieza wczesniej wykaz w incremental_update
        if self.dBController != None:
            msg = self.dBController.addFicheToEntriesIndex(self.ficheId, entry)
            if msg != None:
                self.error_box(msg)
                if not binaryOK:
                    self.msg_panel.error(self.acceptedFicheId, entryForMessage)
                log.opr("on_edit_accept return", [], 6)
                return
            else:
                self.addToHistory(entry)
                ok = True
        #print "add fiches", c
        if self.hintRegister.addHint(entry):
            #c = Counter()
            self.hintreg_browser.incrementalAdd(entry)
            #print "po", c
            # TODO: A typy (np. ponizej jest unicode ktore jest uzywane do znajdywania stringow itemowych)
            self.hintreg_browser.hintChanged(entry)
            self.top_panel.editPanelChanged(None)
        self.dirty = True # TODO: NOTE bo mozemy musiec np. zapisac do pliku dodana powyzej podpowiedz
        self.ignore_entries = True
        #print "add hint", c
        self.lastEntry = None
        if self.active_register.allowsNextFiche() and self.active_register.hasSelection() and not self.active_register.binarySearchActive():
            if ok:
                self.lastEntry = entry
                self.wasEditAccept = True
            self.active_register.getNextFiche(entry)
        else:
            if not binaryOK and self.active_register == self.new_entryreg_browser:
                if self.active_register.binarySearchActive():
                    self.active_register.initializeForActiveBinary(entry)
                    self.active_register.selectElementContaining(self.ficheId)
                else:
                    self.active_register.updateAfterAccept(entry)
            self.update_indices()
        self.ignore_entries = False
        #print "koncowka", c
        #pass
        if not binaryOK:
            self.msg_panel.accept(self.acceptedFicheId, entryForMessage)
        log.opr("on_edit_accept return", [], 4)

    def on_edit_prefix_accept(self, event):
        log.op("on_edit_prefix_accept", [event, self.top_panel.getEditPanelContent()], 0)
        if self.active_register.binarySearchActive():
            return
            log.opr("on_edit_prefix_accept return", [], 1)
        if self.top_panel.getEditPanelContent() == '':
            self.error_box(_('Empty edit panel'))
            log.opr("on_edit_prefix_accept return", [], 2)
            return
        if self.dBController != None:
            msg = self.dBController.addFicheToPrefixesIndex(self.ficheId, self.top_panel.getEditPanelContent())
            if msg != None:
                self.error_box(msg)
                log.opr("on_edit_prefix_accept return", [], 3)
                return
        log.opr("on_edit_prefix_accept return", [], 4)

    def on_structure_element_selected(self, path):
        log.log("on_structure_element_selected", [path], 0)
        self.regbar.setPath(path)
        log.log("on_strucutre_element_selected return", [], 1)

    def hint_for_message(self, ignored, target):
        if self.top_panel.getHint() == '':
            if self.active_register == self.new_entryreg_browser and self.active_register.binarySearchActive() and self.active_register.hasTarget():
                return self.active_register.getTarget()
            else:
                return None
        else:
            return self.top_panel.getHint()

    def on_hint_accept(self, event, binaryOK=False, target=None):
        #if self.active_register.binarySearchActive():
        #    return
        log.op("on_hint_accept", [event, binaryOK, target, self.top_panel.getHint()], 0)
        entryForMessage = self.hint_for_message(binaryOK, target)
        if not binaryOK:
            self.acceptedFicheId = self.ficheId
        if entryForMessage != None and (not binaryOK):
            self.msg_panel.submit(self.acceptedFicheId, entryForMessage)
        if self.top_panel.getHint() == '':
            if self.active_register == self.new_entryreg_browser and self.active_register.binarySearchActive() and (not binaryOK) and self.active_register.hasTarget():
                self.on_automatic_binary_accept(hint=True, emptyPanel=True)
                if not binaryOK:
                    self.msg_panel.accept(self.acceptedFicheId, entryForMessage)
                log.opr("on_hint_accept return", [], 1)
                return
            elif binaryOK:
                entry = target if target != None else self.active_register.getTarget()
            else:
                self.error_box(_('Empty hint panel'))
                log.opr("on_hint_accept return", [], 2)
                return
        else:
            entry = self.top_panel.getHint()
        log.opr("on_hint_accept entry", [entry], 3)
        ok = False
        if self.active_register == self.new_entryreg_browser and self.active_register.binarySearchActive():
            if binaryOK or (not self.active_register.hasTarget()):
                (thisWrong, othersWrong) = self.active_register.wrongOrder(entry)
                if thisWrong:
                    self.msg_panel.wrongFiche(entry)
                elif othersWrong:
                    self.msg_panel.wrongOrder(entry)
            if not binaryOK:
                if self.active_register.hasTarget():
                    self.on_automatic_binary_accept(hint=True)
                    log.opr("on_hint_accept return", [], 4)
                    if not binaryOK:
                        self.msg_panel.accept(self.acceptedFicheId, entryForMessage)
                    return
                self.active_register.prepareForActiveBinary()
        elif self.active_register == self.new_entryreg_browser and not self.active_register.binarySearchActive():
            self.active_register.prepareForUpdateAfterAccept(self.ficheId) # TODO: A patrz komentarz do on_edit_accept
        if self.dBController != None:
            msg = self.dBController.addFicheToEntriesIndex(self.ficheId, entry)
            if msg != None:
                self.error_box(msg)
                if not binaryOK:
                    self.msg_panel.error(self.acceptedFicheId, entryForMessage)
                log.opr("on_hint_accept return", [], 5)
                return
            else:
                self.addToHistory(entry)
                ok = True
        self.ignore_entries = True
        self.lastEntry = None
        if self.active_register.allowsNextFiche() and self.active_register.hasSelection() and not self.active_register.binarySearchActive():
            if ok:
                self.lastEntry = entry
                self.wasEditAccept = True
            self.active_register.getNextFiche() # TODO: C dlaczego w on_edit_accept jest entry a tu nie?
        else:
            if self.active_register == self.new_entryreg_browser:
                if self.active_register.binarySearchActive():
                    self.active_register.initializeForActiveBinary(entry)
                    self.active_register.selectElementContaining(self.ficheId)
                else:
                    self.active_register.updateAfterAccept(entry)
            self.update_indices()
        self.ignore_entries = False
        if not binaryOK:
            self.msg_panel.accept(self.acceptedFicheId, entryForMessage)
        log.opr("on_hint_accept return", [], 6)

    def on_up(self, event):
        log.op("on_up", [event], 0)
        #print self.active_register == self.entryreg_browser
        if self.active_register in [self.strucreg_browser, self.entryreg_browser, self.new_entryreg_browser] and not self.active_register.topLevel():
            self.active_register.onUp(event)
            self.update_indices()
            if self.active_register == self.new_entryreg_browser:
                self.active_register.initialize()
        log.opr("on_up return", [], 1)

    def on_bookmark(self, event):
        log.op("on_bookmark", [event, self.ficheId], 0)
        if self.dBController != None:
            self.dBController.bookmarkFiche(self.ficheId)
            #if self.active_register == self.bookreg_browser:
            self.bookreg_browser.setRegister(self.dBController.getBookmarksTaskRegister(), self.dBController.getActualEntryForFiche if self.dBController != None else None)
            self.bookreg_browser.select(self.ficheId)
        log.opr("on_bookmark return", [], 1)

    def on_default_register(self, event):
        log.op("on_default_register", [event], 0)
        self.taskreg_browser.setRegister(self.taskRegister, self.dBController.getActualEntryForFiche if self.dBController != None else None)
        self.taskreg_browser.select(self.ficheId)
        log.opr("on_default_register return", [], 1)

    def on_choose_register(self, event):
        log.op("on_choose_register", [event], 0)
        if self.active_register == self.taskreg_browser:
            dg = wx.FileDialog(self, _('Open task register'), os.getcwd(), style=wx.FD_OPEN)
            if dg.ShowModal() == wx.ID_OK:
                register = self.index.getTaskRegisterFromFile(dg.GetPath())
                self.taskreg_browser.setRegister(register, self.dBController.getActualEntryForFiche if self.dBController != None else None)
                self.taskreg_browser.select(self.ficheId)
            self.page_widget.SetFocus()
        log.opr("on_choose_register return", [], 1)
        
    # TODO: A flage __fileOpen i sprawdzanie we wszystkich istotnych metodach

    #def on_me(self, evt):
    #    #self.hintreg_browser.reinitialize()
    #    if self.hintRegister.addHint(u"inneHaslo"):
    #        self.hintreg_browser.incrementalAdd(u"inneHaslo")

    def _setup_modes(self):
        li = []
        self._install_shortcut(li, wx.ACCEL_CTRL, ord('E'), self.on_edit_accept)
        self._install_shortcut(li, wx.ACCEL_CTRL, ord('P'), self.on_edit_prefix_accept)
        self._install_shortcut(li, wx.ACCEL_CTRL, ord('H'), self.on_hint_accept)
        self._install_shortcut(li, wx.ACCEL_CTRL, ord('D'), self.on_bookmark)
        self._install_shortcut(li, wx.ACCEL_CTRL, ord('R'), self.on_choose_register)
        self._install_shortcut(li, wx.ACCEL_CTRL, wx.WXK_RETURN, self.on_level_down)
        self._install_shortcut(li, wx.ACCEL_CTRL, wx.WXK_UP, self.scroll_begin)
        self._install_shortcut(li, wx.ACCEL_CTRL, wx.WXK_DOWN, self.scroll_end)
        #self._install_shortcut(li, wx.ACCEL_NORMAL, wx.WXK_DOWN, self.on_next_fiche)
        #self._install_shortcut(li, wx.ACCEL_NORMAL, wx.WXK_UP, self.on_prev_fiche)
        self._install_shortcut(li, wx.ACCEL_CTRL, ord('.'), self.on_next_binary)
        self._install_shortcut(li, wx.ACCEL_CTRL, ord(','), self.on_prev_binary)
        self._install_shortcut(li, wx.ACCEL_CTRL, ord(']'), self.on_next_binary_accept)
        self._install_shortcut(li, wx.ACCEL_CTRL, ord('['), self.on_prev_binary_accept)
        self._install_shortcut(li, wx.ACCEL_CTRL, ord('B'), self.on_stop_binary)
        self._install_shortcut(li, wx.ACCEL_CTRL, ord('K'), self.on_clone_fiche)
        self._install_shortcut(li, wx.ACCEL_CTRL, ord('V'), self.on_preview)
        self._install_shortcut(li, wx.ACCEL_CTRL, wx.WXK_LEFT, self.on_nav_history_prev)
        self._install_shortcut(li, wx.ACCEL_CTRL, wx.WXK_RIGHT, self.on_nav_history_next)
        #self._install_shortcut(li, wx.ACCEL_CTRL, ord('J'), self.on_me)
        mode = Mode(_('Default mode'), accel=wx.AcceleratorTable(li))
        mode.addMenuShortcut(self.on_open, "Ctrl+O")
        mode.addMenuShortcut(self.on_close, "Ctrl+W")
        mode.addMenuShortcut(self.on_exit, "Ctrl+Q")
        mode.addMenuShortcut(self.on_first_page, "Ctrl-Home")
        mode.addMenuShortcut(self.on_previous_page, "PgUp")
        mode.addMenuShortcut(self.on_next_page, "PgDn")
        mode.addMenuShortcut(self.on_last_page, "Ctrl-End")
        mode.addMenuShortcut(self.on_goto_page, "Ctrl-G")
        mode.addMenuShortcut(self.on_show_sidebar, "F9")
        mode.addMenuShortcut(self.on_about, "F1")
        mode.addMenuShortcut(self.on_set_work_mode, "Ctrl-M")
        self.modes.append(mode)
        #li = []
        #mode = Mode(_('Browsing mode'), accel=wx.AcceleratorTable(li))        
        #mode.addMenuShortcut(self.on_open, "Ctrl+O")
        #mode.addMenuShortcut(self.on_close, "Ctrl+W")
        #mode.addMenuShortcut(self.on_exit, "Ctrl+Q")
        #mode.addMenuShortcut(self.on_first_page, "Ctrl-Home")
        #mode.addMenuShortcut(self.on_last_page, "Ctrl-End")
        #mode.addMenuShortcut(self.on_goto_page, "Ctrl-G")
        #mode.addMenuShortcut(self.on_show_sidebar, "F9")
        #mode.addMenuShortcut(self.on_about, "F1")
        #mode.addMenuShortcut(self.on_set_work_mode, "Ctrl-M")
        #self.modes.append(mode)
    
    def _use_mode(self, mode):
        self.mode = mode.getName()
        for (method, item) in self.menu_items.iteritems():
            shortcut = mode.getMenuShortcut(method)
            if shortcut != None:
                item.SetText(item.GetLabel() + "\t" + shortcut)
            else:
                item.SetText(item.GetLabel())
        self.SetAcceleratorTable(mode.getAcceleratorTable())

    def stop_binary_search(self, user=False):
        #print ":", restart
        log.log("stop_binary_search", [user], 0)
        hasTarget = self.active_register.hasTarget()
        self.active_register.stopBinarySearch()
        if self.active_register in [self.strucreg_browser]: # TODO: A zmiany stron w innych wykazach: czy pozwalac?
            self._enable_page_change()
        self.SetStatusText("", 2)
        if self.active_register in [self.new_entryreg_browser]:
            self.regbar.setPath(self.active_register.getElementPath())
            if (not user) and (not hasTarget):
                self.msg_panel.binaryStopped(self.active_register.getSteps())
        self.active_register.SetFocus()
        log.log("stop_binary_search return", [], 1)
    
    def start_binary_search(self, target=None, restarting=False):
        log.log("start_binary_search", [target, restarting], 0)
        if self.active_register in [self.strucreg_browser]:
            self._disable_page_change()
        self.active_register.startBinarySearch(target=target, restarting=restarting)
        if self.active_register.binarySearchActive():
            if not restarting:
                self.SetStatusText(_("Binary search"), 2)
            if self.active_register == self.new_entryreg_browser and self.active_register.hasTarget():
                self.top_panel.refreshForAutomaticBinary(self.active_register.getTarget())
            elif self.active_register == self.new_entryreg_browser:
                self.top_panel.focus()
        log.log("start_binary_search return", [], 1)

    def next_step(self, steps):
        log.log("next_step", [steps], 0)
        self.SetStatusText(_("Binary search") + u", " + _("steps") + u":" + unicode(steps), 2)
        log.log("next_step return", [], 1)
    
    def on_toppanel_key_up(self, event):
        log.log("on_toppanel_key_up", [], 0)
        if self.active_register.allowsNextFiche():
            self.active_register.gotoPrevFiche()
        log.log("on_toppanel_key_up return", [], 1)

    def on_toppanel_key_down(self, event):
        log.log("on_toppanel_key_down", [], 0)
        if self.active_register.allowsNextFiche():
            self.active_register.gotoNextFiche()
        log.log("on_toppanel_key_down return", [], 1)
                
    def find_in_entry_register(self, entry):
        log.log("find_in_entry_register", [entry], 0)
        if self.new_entryreg_browser.allowsNextFiche():
            self.new_entryreg_browser.onUp(None)
        self.sidebar.SetSelection(3)
        self.new_entryreg_browser.find(entry)
        if self.new_entryreg_browser.gapSelected(): # TODO: C czy potrzebne sprawdzanie czy wyszukiwanie juz wlaczone?
            self.register_search.SetValue(entry)
            self.start_binary_search(target=entry)
        log.log("find_in_entry_register return", [], 1)

    def on_search_mode(self, event):
        if self.left_control.isSearchMode():
            self.mainind_panel.freezeValues()
            self.secind_panel.freezeValues()
        else:
            self.mainind_panel.disableInputEvent()
            self.mainind_panel.thawValues()
            self.mainind_panel.enableInputEvent()
            self.secind_panel.disableInputEvent()
            self.secind_panel.thawValues()
            self.secind_panel.enableInputEvent()
    
    def _dispose_modes(self):
        #if self.mode == _('Browsing mode') and self.taskreg_browser.binarySearchActive():
        #    self.stop_binary_search()
        pass

    def on_set_work_mode(self, event):
        self._dispose_modes()
        li = []
        for m in self.modes:
            li.append(m.getName())
        dg = wx.SingleChoiceDialog(self, _('Choose work mode'), _('Work mode'), li)
        if dg.ShowModal() == wx.ID_OK:
            i = dg.GetSelection()
            if i != -1:
                self._use_mode(self.modes[i])
        #print "work"
        self.page_widget.SetFocus()

    def on_level_down(self, event):
        log.log("on_level_down", [event], 0)
        if self.top_panel.editPanelHasFocus():
            self.top_panel.copyHintToEditPanel()
        elif self.active_register in [self.entryreg_browser, self.strucreg_browser, self.new_entryreg_browser, self.hintreg_browser]:
            self.active_register.levelDown()
        log.log("on_level_down return", [], 1)

    def on_splitter_sash_changed(self, event):
        #print event.GetSash
        if event.GetSashIdx() == 0:
            self.default_splitter_sash = event.GetSashPosition()
        else:
            self.default_left_splitter_sash = event.GetSashPosition()
        #print event.GetSashPosition()

    #def on_left_splitter_sash_changed(self, event):
    #    self.default_left_splitter_sash = event.GetSashPosition()

    def on_top_splitter_sash_changed(self, event):
        self.default_top_splitter_sash = event.GetSashPosition()
        
    #def on_sidebar_page_changed(self, event):
    #    pass

    def _on_sidebar_page_changed(self, *methods):
        def event_handler(event):
            methods[event.GetSelection()](event)
        return event_handler

    def on_char(self, event):
        key_code = event.GetKeyCode()
        #print key_code
        if key_code == ord('-'):
            self.on_zoom_out(event)
        elif key_code == ord('+'):
            self.on_zoom_in(event)
        else:
            event.Skip()

    def enable_edit(self, enable=True):
        for i in 1, 3:
            self.GetMenuBar().EnableTop(i, enable)
        for menu_item in self.editable_menu_items:
            menu_item.Enable(enable)

    #def enable_save(self, enable=True):
    #    for menu_item in self.saveable_menu_items:
    #        menu_item.Enable(enable)

    #@apply
    #def dirty():
    #    def get(self):
    #        return self._dirty
    #    def set(self, value):
    #        self._dirty = value
    #        self.enable_save(value)
    #    return property(get, set)

    def error_box(self, message, caption = _('Error')):
        wx.MessageBox(message = message, caption = caption, style = wx.OK | wx.ICON_ERROR, parent = self)
        #print "error"
        self.page_widget.SetFocus()

    def on_exit(self, event):
        self.__closing = True
        if self.do_open(None):
            x, y = self.GetPosition()
            w, h = self.GetSize()
            self.default_xywh = x, y, w, h
            self.save_defaults()
            self.Destroy()

    def on_recently_used(self, event):
        self.msg_panel.showMessage(_('Opening archive') + u' ' + ustr(self.recently_used_menu[event.GetId()]))
        self.do_open(self.recently_used_menu[event.GetId()])
        self.msg_panel.showMessage(_('Opened archive') + u' ' + ustr(self.recently_used_menu[event.GetId()]))

    def on_open(self, event):
        dialog = OpenDialog(self)
        dialog.SetPath(self._config.read('open_dir', ''))
        try:
            if dialog.ShowModal() == wx.ID_OK:
                self._config['open_dir'] = os.path.dirname(dialog.GetPath()) or ''
                try:
                    self.recently_used.index(os.path.abspath(dialog.GetPath()))
                except ValueError:
                    if len(self.recently_used) > 8: # TODO: D stala
                        self.recently_used = self.recently_used + [os.path.abspath(dialog.GetPath())]
                    else:
                        self.recently_used = self.recently_used + [os.path.abspath(dialog.GetPath())]
                self.msg_panel.showMessage(_('Opening archive') + u' ' + ustr(dialog.GetPath()))
                self.do_open(dialog.GetPath())
                self.msg_panel.showMessage(_('Opened archive') + u' ' + ustr(dialog.GetPath()))
        finally:
            dialog.Destroy()
        #print "open"
        self.page_widget.SetFocus()

    def on_close(self, event):
        self.do_open(None)

    #def on_save(self, event):
    #    self.do_save()

    #def on_save_failed(self, exception):
    #    self.error_box(_('Saving document failed:\n%s') % exception)

    #def do_save(self):
    #    if not self.dirty:
    #        return True
    #    queue = Queue()
    #    sed = StreamEditor(self.path, autosave=True)
    #    for model in self.models:
    #        model.export(sed)
    #    def job():
    #        try:
    #            sed.commit()
    #            self.document = self.context.new_document(djvu.decode.FileURI(self.path))
    #            for model in self.models:
    #                model.reset_document(self.document)
    #        except Exception, exception:
    #            pass
    #        else:
    #            exception = None
    #        queue.put(exception)
    #    thread = threading.Thread(target = job)
    #    thread.start()
    #    dialog = None
    #    try:
    #        try:
    #            exception = queue.get(block = True, timeout = 0.1)
    #            if exception is not None:
    #                self.on_save_failed(exception)
    #                return False
    #        except QueueEmpty:
    #            dialog = dialogs.ProgressDialog(
    #                title = _('Saving document'),
    #                message = _(u'Saving the document, please wait…'),
    #                parent = self,
    #                style = wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME
    #            )
    #        while dialog is not None:
    #            try:
    #                exception = queue.get(block = True, timeout = 0.1)
    #                if exception is not None:
    #                    self.on_save_failed(exception)
    #                    return False
    #                break
    #            except QueueEmpty:
    #                dialog.Pulse()
    #    finally:
    #        thread.join()
    #        if dialog is not None:
    #            dialog.Destroy()
    #    self.dirty = False
    #    return True

    def on_show_sidebar(self, event):
        if event.IsChecked():
            self.do_show_sidebar()
        else:
            self.do_hide_sidebar()

    def on_show_left_sidebar(self, event):
        if event.IsChecked():
            self.do_show_left_sidebar()
        else:
            self.do_hide_left_sidebar()

    def do_show_sidebar(self):
        #self.splitter.SplitVertically(self.sidebar, self.scrolled_panel, self.default_splitter_sash)
        #self.splitter.SplitVertically(self.sidepanel, self.scrolled_panel, self.default_splitter_sash)
        #self.splitter.SplitVertically(self.sidepanel, self.main_panel, self.default_splitter_sash)
        self.default_sidebar_shown = True
        self.sidebar_shown = True
        self.splitter.InsertWindow(0, self.sidepanel, self.default_splitter_sash)

    def do_show_topbar(self):
        self.default_topbar_shown = True
        self.topbar_shown = True
        self.super_splitter.SplitHorizontally(self.msg_panel, self.splitter, self.default_top_splitter_sash)

    def do_show_left_sidebar(self):
        #self.super_splitter.SplitVertically(self.splitter, self.left_sidepanel, self.default_left_splitter_sash)
        self.default_left_sidebar_shown = True
        self.splitter.AppendWindow(self.left_sidepanel)
        if self.sidebar_shown:
            self.splitter.SetSashPosition(1, self.default_left_splitter_sash)
        else:
            self.splitter.SetSashPosition(0, self.default_left_splitter_sash)

    def do_hide_sidebar(self):
        #self.splitter.Unsplit(self.sidebar)
        self.splitter.DetachWindow(self.sidepanel)
        self.default_sidebar_shown = False
        self.sidebar_shown = False

    def do_hide_topbar(self):
        self.super_splitter.Unsplit(self.msg_panel)
        self.default_topbar_shown = False
        self.topbar_shown = False

    def do_hide_left_sidebar(self):
        #self.super_splitter.Unsplit(self.left_sidebar)
        self.splitter.DetachWindow(self.sidepanel)
        self.default_left_sidebar_shown = False

    def register_search_input(self, event):
        log.op("register_search_input", [event, self.register_search.GetValue()], 0)
        self.active_register.find(self.register_search.GetValue())
        log.opr("register_search_input return", [], 1)

    def register_search_key(self, event):
        log.op("register_search_key", [event, event.GetKeyCode()], 0)
        if event.GetKeyCode() == wx.WXK_RETURN and self.active_register == self.hintreg_browser:
            self.active_register.levelDown()
        log.opr("register_search_key return", [], 1)
    
    def on_undisplay(self):
        log.op("on_undisplay", [], 0)
        if self.active_register.binarySearchActive():
            self.stop_binary_search()
        self.update_indices()
        if not self.__closing:
            if self.active_register == self.strucreg_browser:
                self.regbar.setPath("")
        log.opr("on_undisplay return", [], 1)
   
    def on_display_taskreg(self, event):
        log.op("on_display_taskreg", [event], 0)
        if not self.__closing:
            self.on_undisplay()
            self._disable_page_change()         
            self.active_register = self.taskreg_browser
            if self.ficheId != None: self.active_register.select(self.ficheId)
        log.opr("on_display_taskreg return", [], 1)            

    def on_display_strucreg(self, event):
        log.op("on_display_strucreg", [event], 0)
        if not self.__closing:
            self.on_undisplay()
            self.active_register = self.strucreg_browser
            if self.ficheId != None: self.active_register.select(self.ficheId)
            self.regbar.setPath(self.active_register.getPath())
            self._enable_page_change()
        log.opr("on_display_strucreg return", [], 1)

    def on_display_entryreg(self, event):
        log.op("on_display_entryreg", [event], 0)
        if not self.__closing:
            self.on_undisplay()
            self._disable_page_change()  
            self.active_register = self.entryreg_browser
            if self.ficheId != None: self.active_register.select(self.ficheId)
        log.opr("on_display_entryreg return", [], 1)            

    def on_display_new_entryreg(self, event):
        log.op("on_display_new_entryreg", [event], 0)
        if not self.__closing:
            self.on_undisplay()
            self._disable_page_change()
            self.active_register = self.new_entryreg_browser
            if self.ficheId != None:
                if self.active_register.isActive():
                    self.active_register.refresh(self.ficheId)
                self.active_register.selectAndShow(self.ficheId)
            else:
                if self.active_register.isActive():
                    self.active_register.initialize()
        log.opr("on_display_new_entryreg return", [], 1)

    def on_display_hintreg(self, event):
        log.op("on_display_hintreg", [event], 0)
        if not self.__closing:
            self.on_undisplay()
            self._disable_page_change()  
            self.active_register = self.hintreg_browser
        log.opr("on_display_hintreg return", [], 1)

    def on_display_bookreg(self, event):
        log.op("on_display_bookreg", [event], 0)
        if not self.__closing:
            self.on_undisplay()
            self._disable_page_change()
            self.active_register = self.bookreg_browser
            if self.ficheId != None: self.bookreg_browser.select(self.ficheId)
        log.opr("on_display_bookreg return", [], 1)

    def on_display_everything(self, event):
        self.page_widget.render_mode = djvu.decode.RENDER_COLOR

    def on_display_foreground(self, event):
        self.page_widget.render_mode = djvu.decode.RENDER_FOREGROUND

    def on_display_background(self, event):
        self.page_widget.render_mode = djvu.decode.RENDER_BACKGROUND

    def on_display_stencil(self, event):
        self.page_widget.render_mode = djvu.decode.RENDER_BLACK

    def on_display_none(self, event):
        self.page_widget.render_mode = None

    #def on_display_text(self, event):
    #    self.page_widget.render_nonraster = RENDER_NONRASTER_TEXT
    #    self._menu_item_display_text.Check()

    #def on_display_maparea(self, event):
    #    self.page_widget.render_nonraster = RENDER_NONRASTER_MAPAREA
    #    self._menu_item_display_maparea.Check()

    #def on_display_no_nonraster(self, event):
    #    self.page_widget.render_nonraster = None
    #    self._menu_item_display_no_nonraster.Check()

    #def on_refresh(self, event):
    #    self.Refresh()

    def get_page_uri(self, page_no = None):
        if page_no is None:
            page_no = self.page_no
        try:
            id = self.document.pages[page_no].file.id
        except djvu.decode.NotAvailable:
            id = str(page_no)
        return '#' + id

    @apply
    def page_no(): # numer aktualnie ogladanej fiszki w porzadku naturalnym
        def get(self):
            return self._page_no
        def set(self, n):
            log.log("set page_no", [n], 0)
            if self.index is None:
            #if self.document is None:
                self._page_no = 0
                self.status_bar.SetStatusText('', 1)
                log.log("set page_no return", [], 1)
                return
            #if n < 0 or n >= len(self.document.pages):
            if n < 0 or n >= self.index.getFicheNo():
                log.log("set page_no return", [], 2)
                return
            self._page_no = n
            self.status_bar.SetStatusText(_('Page %(pageno)d of %(npages)d') % {'pageno':(n + 1), 'npages':self.index.getFicheNo()}, 1)
            if self.preview != None:
                self.close_preview()
            self.switch_document(self._page_no)
            #self.update_page_widget(new_page = True)
            log.log("set page_no return", [], 3)
        return property(get, set)

    def on_back(self, event):
        log.op("on_back", [event], 0)
        if self.history != [] and not self.active_register.binarySearchActive():
            self.goingBack = True
            self.page_no = self.index.getFicheNoById(self.history.pop())
            self.goingBack = False
        log.opr("on_back return", [self.page_no], 1)

    def on_first_page(self, event):
        log.op("on_first_page", [event], 0)
        self.page_no = 0
        log.opr("on_first_page return", [], 1)

    def on_last_page(self, event):
        log.op("on_last_page", [event], 0)
        #self.page_no = len(self.document.pages) - 1
        self.page_no = self.index.getFicheNo() - 1
        log.opr("on_last_page return", [self.page_no], 1)

    def on_next_page(self, event):
        log.op("on_next_page", [event], 0)
        self.page_no += 1
        log.opr("on_next_page return", [self.page_no], 1)

    def on_previous_page(self, event):
        log.op("on_previous_page", [event], 0)
        self.page_no -= 1
        log.opr("on_previous_page return", [self.page_no], 1)
    
    def on_reg_select(self, elementId, notify=True):
        log.log("on_reg_select", [elementId, notify], 0)
        self.notify = notify
        self.page_no = self.index.getFicheNoById(elementId)
        self.notify = True
        log.log("on_reg_select return", [], 1)

    def request_selection(self):
        log.log("on_request_selection", [], 0)
        log.log("on_request_selection return", [self.ficheId], 1)
        return self.ficheId

    def scroll_begin(self, event):
        log.op("scroll_begin", [event], 0)
        self.active_register.showFirstElement()
        log.opr("scroll_begin return", [], 1)

    def scroll_end(self, event):
        log.op("scroll_end", [event], 0)
        self.active_register.showLastElement()
        log.opr("scroll_end return", [], 1)

    # TODO: D dac jednego globalnego handlera eventow z akceleratora:

    #def on_next_fiche(self, event):
    #    #print event
    #    if self.mode == _('Browsing mode'):
    #        self.taskreg_browser.selectNextElement()
    
    #def on_prev_fiche(self, event):
    #    #print event
    #    if self.mode == _('Browsing mode'):
    #        self.taskreg_browser.selectPrevElement()
    
    def on_next_binary(self, event):
    #    #if self.mode == _('Browsing mode'):
    #        #if not self.taskreg_browser.binarySearchActive():
    #        #    self.start_binary_search()
    #        #else:
        log.op("on_next_binary", [event, self.active_register.getSelectedElement()], 0)
        if self.active_register.binarySearchActive() and not self.active_register.hasTarget():
            self.active_register.nextBinary()
        log.opr("on_next_binary return", [], 1)

    def on_prev_binary(self, event):
    #    if self.mode == _('Browsing mode'):
    #        #if not self.taskreg_browser.binarySearchActive():
    #        #    self.start_binary_search()
    #        #else:
        log.op("on_prev_binary", [event, self.active_register.getSelectedElement()], 0)
        if self.active_register.binarySearchActive() and not self.active_register.hasTarget():
            self.active_register.prevBinary()
        log.opr("on_prev_binary return", [], 1)

    def on_automatic_binary_accept(self, hint=False, emptyPanel=False):
        #print "a"
        #from maleks.maleks.useful import Counter
        #c = Counter()
        log.op("on_automatic_binary_accept", [hint, emptyPanel, self.active_register.getSelectedElement()], 0)
        if emptyPanel:
            entry = self.active_register.getTarget()
        elif hint:
            entry = self.top_panel.getHint()
        else:
            entry = self.top_panel.getEditPanelContent()
        target = self.active_register.getTarget()
        #assert(target != None)
        if self.active_register.determineNextTarget(entry) == "LEFT":
            #print "determineNextTarget"#, c
            if not self.active_register.prevBinaryAcceptPrepare(automatic=True):
                #print "prevBinaryAcceptPrepare"#, c
                self.stop_binary_search()
                #print "stop_binary_search"#, c
                #print ":::", target
                #print "d"
                if hint:
                    self.on_hint_accept(None, binaryOK=True, target=target)
                    #print "on_hint_accept"#, c
                else:
                    self.on_edit_accept(None, binaryOK=True, target=target)
                    #print "on_edit_accept"#, c
                self.active_register.initialize(entry)
                #print "initialize"#, c
                if self.active_register.restartable(target):
                    #self.active_register.startBinarySearch(target=target, restarting=True)
                    self.start_binary_search(target=target, restarting=True)
                    #print "startBinarySearch"#, c
                    #print self.active_register.hasTarget()
                else:
                    self.msg_panel.automaticBinaryStopped(target, self.active_register.getSteps())
                    self.active_register.find(target)
                    #self.page_no = self.index.getFicheNoById(self.active_register.getLastFicheOfSelected())
                    self.page_no = self.index.getFicheNoById(self.active_register.getFirstFicheOfSelected())
                #print "j"
            else:
                #print "prevBinaryAcceptPrepare", c
                if hint:
                    self.on_hint_accept(None, binaryOK=True)
                    #print "on_hint_accept", c
                else:
                    self.on_edit_accept(None, binaryOK=True)
                    #print "on_edit_accept", c
                self.active_register.binaryAcceptFinalize(entry)
                #print "binaryAcceptFinalize", c
                self.top_panel.refreshForAutomaticBinary(target)
                #print "refreshForAutomaticBinary", c
        else:
            #print "else"
            #print "determineNextTarget", c
            if not self.active_register.nextBinaryAcceptPrepare(automatic=True):
                #print "stop_nextBinaryAcceptPrepare_search"#, c
                self.stop_binary_search()
                #print "stop_binary_search"#, c
                #print ":::", target
                if hint:
                    self.on_hint_accept(None, binaryOK=True, target=target)
                    #print "on_hint_accept"#, c
                else:
                    self.on_edit_accept(None, binaryOK=True, target=target)
                    #print "on_edit_accept"#, c
                self.active_register.initialize(entry)
                #print "initialize"#, c
                if self.active_register.restartable(target):
                    #self.active_register.startBinarySearch(target=target, restarting=True)
                    self.start_binary_search(target=target, restarting=True)
                    #print self.active_register.hasTarget()
                    #print "startBinarySearch"#, c
                else:
                    self.msg_panel.automaticBinaryStopped(target, self.active_register.getSteps())
                    self.active_register.find(target)
                    #self.page_no = self.index.getFicheNoById(self.active_register.getLastFicheOfSelected())
                    self.page_no = self.index.getFicheNoById(self.active_register.getFirstFicheOfSelected())
                #print "z"
            else:
                #print "stop_nextBinaryAcceptPrepare_search", c
                if hint:
                    self.on_hint_accept(None, binaryOK=True)
                    #print "on_hint_accept", c
                else:
                    self.on_edit_accept(None, binaryOK=True)
                    #print "on_edit_accept", c
                self.active_register.binaryAcceptFinalize(entry)
                #print "binaryAcceptFinalize", c
                self.top_panel.refreshForAutomaticBinary(target)
                #print "refreshForAutomaticBinary", c
        log.opr("on_automatic_binary_accept return", [], 1)

    def on_next_binary_accept(self, event):
        log.op("on_next_binary_accept", [event, self.active_register.getSelectedElement()], 0)
        if self.active_register != self.new_entryreg_browser:
            log.opr("on_next_binary_accept return", [], 1)
            return
        if self.active_register.binarySearchActive() and not self.active_register.hasTarget():
             entry = self.top_panel.getEditPanelContent()
             if not self.active_register.nextBinaryAcceptPrepare():
                #print "ojej"
                self.stop_binary_search()
                self.on_edit_accept(None, binaryOK=True)
                self.active_register.initialize(entry)
                self.active_register.selectElementContaining(self.ficheId)
             else:
                #print "ok"
                self.on_edit_accept(None, binaryOK=True)
                self.active_register.binaryAcceptFinalize(entry, True)
        log.opr("on_next_binary_accept return", [], 2)
    
    def on_prev_binary_accept(self, event):
        log.op("on_prev_binary_accept", [event, self.active_register.getSelectedElement()], 0)
        if self.active_register != self.new_entryreg_browser:
            log.opr("on_prev_binary_accept return", [], 1)
            return
        if self.active_register.binarySearchActive() and not self.active_register.hasTarget():
             entry = self.top_panel.getEditPanelContent()
             if not self.active_register.prevBinaryAcceptPrepare():
                #print "ojej"
                self.stop_binary_search()
                self.on_edit_accept(None, binaryOK=True)
                self.active_register.initialize(entry)
                self.active_register.selectElementContaining(self.ficheId)
             else:
                #print "ok"
                self.on_edit_accept(None, binaryOK=True)
                self.active_register.binaryAcceptFinalize(entry, True)
        log.opr("on_prev_binary_accept return", [], 2)

    def invisible_binary_search(self, ficheId):
        log.log("invisible_binary_search", [ficheId], 0)
        #c = Counter()
        self.notify = False
        self.page_no = self.index.getFicheNoById(ficheId)
        self.notify = True
        #print " invi", c
        log.log("invisible_binary_search return", [], 1)

    def on_regbar_enter(self, event):
        log.op("on_regbar_enter", [event.GetKeyCode(), self.active_register, self.active_register.binarySearchActive(), wx.WXK_RETURN], 0)
        if event.GetKeyCode() == wx.WXK_RETURN and (not event.ControlDown()) and self.active_register == self.new_entryreg_browser and (not self.active_register.binarySearchActive()):
            self.on_stop_binary(event)
        else:
            event.Skip()
        log.opr("on_regbar_enter return", [], 1)

    def on_stop_binary(self, event):
    #    if self.mode == _('Browsing mode'):
        log.op("on_stop_binary", [event, self.active_register.binarySearchActive()], 0)
        #print self.active_register.binaryAvailable(), self.active_register.binarySearchActive()
        if not self.active_register.isActive(): # TODO: C po co?, zdecydowac sie czy to sprawdzac explicite tu czy schowac w implementacji rejestru
            log.log("on_stop_binary return", [], 1)
            return
        if self.active_register == self.hintreg_browser:
            self.active_register.levelDown()
            log.log("on_stop_binary return", [], 2)
            return
        if self.active_register.binaryAvailable() and not self.active_register.binarySearchActive():
            if self.register_search.GetValue() != "":
                self.start_binary_search(self.register_search.GetValue())
            else:
                self.start_binary_search()
        else:
            self.stop_binary_search(user=True)
        log.opr("on_stop_binary return", [], 3)

    def on_hint_changed(self, hint):
        log.log("on_hint_changed", [hint], 0)
        self.hintreg_browser.hintChanged(hint)
        log.log("on_hint_changed return", [], 1)

    def on_hint_selected(self, hint):
        log.log("on_hint_selected", [hint], 0)
        self.top_panel.setHint(hint)
        log.log("on_hint_selected return", [], 1)

    def close_preview(self):
        self.preview.Close()
        self.preview = None

    def on_preview(self, event):
        log.op("on_preview", [event], 0)
        if self.preview != None:
            self.close_preview()
        else:
            # TODO: !A jezeli zostanie zaimplementowane chowanie panelu indeksow to to sie rozjedzie!
            height = self.GetSizeTuple()[1] - self.left_sidepanel.GetSizeTuple()[1]
            width = self.GetSizeTuple()[0] - self.left_sidepanel.GetSizeTuple()[0]
            #print width, height
            self.preview = PreviewDialog(self, wx.ID_ANY, _('Preview'), style=wx.FRAME_FLOAT_ON_PARENT, pos=(width, height))
            self.preview.setParent(self)
            self.preview.setIndex(self.index)
            self.preview.show(self.page_no)
        log.opr("on_preview return", [], 1)

    def on_goto_page(self, event):
        log.op("on_goto_page", [event], 0)
        dialog = dialogs.NumberEntryDialog(
            parent = self,
            message = _('Go to page') + ':',
            prompt = '',
            caption = _('Go to page'),
            value = self.page_no + 1,
            min = 1,
            #max = len(self.document.pages)
            max = self.index.getFicheNo()
        )
        try:
            rc = dialog.ShowModal()
            if rc == wx.ID_OK:
                self.page_no = dialog.GetValue() - 1
        finally:
            dialog.Destroy()
            self.page_widget.SetFocus()
        log.opr("on_goto_page return", [], 1)

    #def on_edit_metadata(self, event):
    #    document_metadata_model = self.metadata_model[models.SHARED_ANNOTATIONS_PAGENO].clone()
    #    document_metadata_model.title = _('Document metadata')
    #    page_metadata_model = self.metadata_model[self.page_no].clone()
    #    page_metadata_model.title = _('Page %d metadata') % (self.page_no + 1)
    #    dialog = MetadataDialog(self, models=(document_metadata_model, page_metadata_model), known_keys=djvu.const.METADATA_KEYS)
    #    try:
    #        if dialog.ShowModal() == wx.ID_OK:
    #            self.metadata_model[models.SHARED_ANNOTATIONS_PAGENO] = document_metadata_model
    #            self.metadata_model[self.page_no] = page_metadata_model
    #            self.dirty = True
    #    finally:
    #        dialog.Destroy()
    #
    #def on_flatten_text(self, event):
    #    dialog = FlattenTextDialog(self)
    #    zone = None
    #    try:
    #        if dialog.ShowModal() == wx.ID_OK:
    #            scope_all = dialog.get_scope()
    #            zone = dialog.get_zone()
    #    finally:
    #        dialog.Destroy()
    #    if zone is None:
    #        return
    #    if scope_all:
    #        page_nos = xrange(len(self.document.pages))
    #    else:
    #        page_nos = (self.page_no,)
    #    for page_no in page_nos:
    #        self.text_model[page_no].strip(zone)

    #def on_bookmark_current_page(self, event):
    #    uri = self.get_page_uri()
    #    node = models.outline.InnerNode(djvu.sexpr.Expression((_('(no title)'), uri)), self.outline_model)
    #    self.outline_model.root.add_child(node)
    #    node.notify_select()

    #def on_remove_outline(self, event):
    #    self.outline_model.remove()

    #def on_external_edit_outline(self, event):
    #    model = self.outline_model
    #    def job(disabler):
    #        new_repr = None
    #        try:
    #            with external_editor.temporary_file(suffix='.txt') as tmp_file:
    #                model.export_as_plaintext(tmp_file)
    #                tmp_file.flush()
    #                self.external_editor(tmp_file.name)
    #                tmp_file.seek(0)
    #                new_repr = map(str.expandtabs, itertools.imap(str.rstrip, tmp_file))
    #        except Exception, exception:
    #            pass
    #        else:
    #            exception = None
    #        wx.CallAfter(lambda: self.after_external_edit_outline(new_repr, disabler, exception))
    #    disabler = wx.WindowDisabler()
    #    thread = threading.Thread(target=job, args=(disabler,))
    #    thread.start()

    #def on_external_edit_failed(self, exception):
    #    self.error_box(_('External edit failed:\n%s') % exception)

    #def after_external_edit_outline(self, new_repr, disabler, exception):
    #    if exception is not None:
    #        self.on_external_edit_failed(exception)
    #        return
    #    # TODO: how to check if actually something changed?
    #    self.outline_model.import_plaintext(new_repr)

    #def on_external_edit_text(self, event):
    #    sexpr = self.text_model[self.page_no].raw_value
    #    if not sexpr:
    #        self.error_box(_('No text layer to edit.'))
    #        return
    #    def job(disabler):
    #        new_sexpr = None
    #        try:
    #            with external_editor.temporary_file(suffix='.txt') as tmp_file:
    #                text_mangle.export(sexpr, tmp_file)
    #                tmp_file.flush()
    #                self.external_editor(tmp_file.name)
    #                tmp_file.seek(0)
    #                try:
    #                    new_sexpr = text_mangle.import_(sexpr, tmp_file)
    #                except text_mangle.NothingChanged:
    #                    pass
    #        except Exception, exception:
    #            pass
    #        else:
    #            exception = None
    #        wx.CallAfter(lambda: self.after_external_edit_text(new_sexpr, disabler, exception))
    #    disabler = wx.WindowDisabler()
    #    thread = threading.Thread(target=job, args=(disabler,))
    #    thread.start()

    #def after_external_edit_text(self, sexpr, disabler, exception):
    #    if exception is not None:
    #        try:
    #            raise exception
    #        except text_mangle.CharacterZoneFound:
    #            self.error_box(_('Cannot edit text with character zones.'))
    #            return
    #        except text_mangle.LengthChanged:
    #            self.error_box(_('Number of lines changed.'))
    #            return
    #        except:
    #            self.on_external_edit_failed(exception)
    #            return
    #    if sexpr is None:
    #        # nothing changed
    #        return
    #    self.text_model[self.page_no].raw_value = sexpr

    def on_clone_fiche(self, event):
        log.op("on_clone_fiche", [self.ficheId], 0)
        if self.active_register.binarySearchActive():
            log.opr("on_clone_fiche return", [], 1)
            return
        if self.ficheId != None:
            if self.preview != None:
                self.close_preview()
            originalEntry = ""
            actualEntry = ""
            if self.dBController != None:
                actualEntry = self.dBController.getActualEntryForFiche(self.ficheId)
                originalEntry = self.dBController.getOriginalEntryForFiche(self.ficheId)
            dialog = CloneDialog(None, wx.ID_ANY, _('Fiche cloning'), size=(500, 110))
            dialog.setEntry(nvl(originalEntry), nvl(actualEntry))
            rc = dialog.ShowModal()
            if rc == wx.ID_OK:
                cloneId = self.index.clone(self.ficheId)
                if self.dBController != None:
                    (original, ficheActual, cloneActual) = dialog.GetValue()
                    self.dBController.cloneFiche(self.ficheId, cloneId, original, ficheActual, cloneActual)
                    if actualEntry == None or actualEntry == "":
                        self.new_entryreg_browser.handleClone([ficheActual, cloneActual], self.ficheId)
                    else:
                        self.new_entryreg_browser.handleClone([actualEntry, ficheActual, cloneActual], self.ficheId)
                self.strucreg_browser.handleClone(self.ficheId)
                # TODO: !A klonowanie wartosci indeksow - wtedy trzeba tez odswiezyc wykaz wielopoziomowy
                self.status_bar.SetStatusText(_('Page %(pageno)d of %(npages)d') % {'pageno':self.index.getFicheNoById(self.ficheId), 'npages':self.index.getFicheNo()}, 1)
                self.update_indices()
                self.update_panels()
        dialog.Destroy()
        log.opr("on_clone_fiche return", [], 2)

    def do_percent_zoom(self, percent):
        self.page_widget.zoom = PercentZoom(percent)
        self.zoom_menu_items[percent].Check()

    def on_zoom_out(self, event):
        try:
            percent = self.page_widget.zoom.percent
        except ValueError:
            return # FIXME
        candidates = [k for k in self.zoom_menu_items.iterkeys() if k < percent]
        if not candidates:
            return
        self.do_percent_zoom(max(candidates))

    def on_zoom_in(self, event):
        try:
            percent = self.page_widget.zoom.percent
        except ValueError:
            return # FIXME
        candidates = [k for k in self.zoom_menu_items.iterkeys() if k > percent]
        if not candidates:
            return
        self.do_percent_zoom(min(candidates))

    def on_zoom(self, zoom):
        def event_handler(event):
            self.page_widget.zoom = zoom
        return event_handler
    
    def reset(self):
        log.log("MainWindow.reset", [], 0)
        self.document = None
        self.index = None
        self.config = None
        self.taskRegister = None
        #self.bookmarksActive = False
        self.hintRegister = None
        self.top_panel.setHintRegister(None)
        self.history = []
        self._ficheId = None
        self.wasEditAccept = False
        self.lastEntry = None
        self.fiche_for_locate = None
        self.locate = 0
        self.entry_history = []
        self.entry_index = -1
        self.browsing_entry_history = False
        log.log("MainWindow.reset return", [], 1)

    # zamkniecie aktualnie otwartej karotetki i otwarcie nowej (jezeli path != None)
    def do_open(self, path):
        if isinstance(path, unicode):
            path = path.encode(system_encoding)
        if self.dirty: # do wykazu podpowiedzi dodano nowa podpowiedz - trzeba ja zapisac
            self.hintRegister.saveUserHints()
        #    dialog = wx.MessageDialog(self, _('Do you want to save your changes?'), '', wx.YES_NO | wx.YES_DEFAULT | wx.CANCEL | wx.ICON_QUESTION)
        #    try:
        #        rc = dialog.ShowModal()
        #        if rc == wx.ID_YES:
        #            return self.do_save()
        #        elif rc == wx.ID_NO:
        #            pass
        #        elif rc == wx.ID_CANCEL:
        #            return False
        #    finally:
        #        dialog.Destroy()
        self.path = path
        self.reset() # resetuje okno glowne do stanu takiego jak na poczatku
        self.taskreg_browser.reset() # j.w. dla poszczegolnych widokow wykazow
        self.strucreg_browser.reset() # TODO: C dlaczego resetu widokow wykazow
        self.entryreg_browser.reset() # nie mozna dac w MainWindow.reset (dotyczy
        self.new_entryreg_browser.reset() # tez ponizszego resetowania numeru
        self.hintreg_browser.reset() # aktualnej fiszki (page_no) na 0)?
        self.bookreg_browser.reset()
        self.page_no = 0
        self.dBController.setPerDocumentConnection(None, None, None, None, None) # resetuje
            # kontroler bazy danych do ustawien z globalnego pliku konfiguracyjnego
        #def clear_models():
        #    self.metadata_model = self.text_model = self.outline_model = self.annotations_model = None
        #    self.models = ()
        #    self.enable_edit(False)
        if path is None: # tylko zamykamy poprzednio otwarta kartoteke
            #clear_models()
            pass
        else: # otwieramy nowa kartoteke
            try:
                log.startLog(path)
                self.config = Configuration(path) # odczytaj plik konfiguracyjny kartoteki
                self.config.configureDatabase(self.dBController) # skonfiguruj
                    # kontroler bazy danych dla konkretnej kartoteki
                if self.dBController != None:
                    log.dumpDatabase(self.dBController.dumpDatabase())
                self.index = StructureIndex(path, self.dBController) # utworz indeks struktury
                # zainicjalizuj niektore widoki wykazow:
                # TODO: ! wyraznie napisac dlaczego nie moga byc w initialize_registers
                self.entryreg_browser.initialize() # TODO: C przeniesc do initialize_registers i dac
                    # flage czy udalo sie wczytac plik czy nie (self.document = None starczy? -
                    # - uzywane w update_indices)
                if self.index.isAlphabetic(): # wykaz hasel ma sens tylko dla fiszek w kolejnosci alfabetycznej
                    self.new_entryreg_browser.initialize() 
                #self.bookreg_browser.DeleteAllItems()
                self.bookreg_browser.setRegister(self.dBController.getBookmarksTaskRegister(), self.dBController.getActualEntryForFiche if self.dBController != None else None) # TODO: C j.w.,
                    # zamiast sprawdzania flagi sprawdzanie czy dBController jest null
                self.hintRegister = HintRegister(path) # zaladuj wykaz podpowiedzi
                self.hintRegister.readUserHints(path)
                #self.hintRegister.sort()
                self.top_panel.setHintRegister(self.hintRegister) # gorna czesc panelu
                    # glownego musi miec referencje do wykazu podpowiedzi zeby
                    # wyswietlac podpowiedzi w panelu podpowiedzi
                self.taskRegister = self.config.getDefaultTaskRegister(self.index)
                self.document = self.context.new_document(djvu.decode.FileURI(self.index.getFiche(0).getDjVuPath()))
                #try:
                #    self.ficheId = self.taskRegister[0].getId()
                #except IndexError:
                self.ficheId = self.index.getFiche(0).getId() # pierwsza fiszka w
                    # porzadku naturalnym
                self.update_indices() # wyswietla w indeksach zawartosc
                    # indeksow dla fiszki ficheId
                #self.metadata_model = MetadataModel(self.document)
                #self.text_model = TextModel(self.document)
                #self.outline_model = OutlineModel(self.document)
                #self.annotations_model = AnnotationsModel(path)
                #self.models = self.metadata_model, self.text_model, self.outline_model, self.annotations_model
                #self.enable_edit(True)
            except djvu.decode.JobFailed:
                #clear_models()
                self.reset()
                # TODO: A co zrobic tutaj?
                # Do *not* display error message here. It will be displayed by `handle_message()`.
        self.page_no = 0 # again, to set status bar text
        self.update_title()
        self.update_page_widget(new_document = True, new_page = True)
        self.initialize_registers() # zainicjalizuj widoki wykazow
        self.update_panels() # zainicjalizuj gorna czesc panelu glownego
        self.dirty = False
        return True

    # wyswielt fiszke o numerze kolejnym page_no
    def switch_document(self, page_no):
        log.log("switch_document", [page_no], 0)
        c = Counter()
        if self.wasEditAccept:
            self.wasEditAccept = False
        else:
            self.lastEntry = None
        self.document = None
        try:
            self.document = self.context.new_document(djvu.decode.FileURI(self.index.getFiche(page_no).getDjVuPath()))
            self.ficheId = self.index.getFiche(page_no).getId()
        except djvu.decode.JobFailed:
            # TODO: A to powinno powodowac blad!
            self.reset()
            self.page_no = 0
        #print "  loaded", c
        self.update_title()
        #print "  title", c
        self.update_page_widget(new_document = True, new_page = True)
        #print "  widget", c
        self.update_registers()
        #print "  registers", c
        self.update_indices()
        #print "  indices", c
        self.update_panels()
        #print "  panels", c
        #import time
        #time.sleep(0.5)
        for i in range(0, 200):
            self.update_page_widget()
        #print "  update", c
        #self.Refresh()
        #self.Update()
        log.log("switch_document return", [True], 1)
        return True

    def update_page_widget(self, new_document = False, new_page = False):
        if self.document is None:
            self.page_widget.Hide()
            self.page = self.page_job = self.page_proxy = self.document_proxy = None
        elif self.page_job is None or new_page:
            self.page_widget.Show()
            #self.page = self.document.pages[self.page_no]
            self.page = self.document.pages[0]
            self.page_job = self.page.decode(wait = False)
            self.page_proxy = PageProxy(
                page = self.page#,
                #text_model = self.text_model[self.page_no],
                #annotations_model = self.annotations_model[self.page_no]
            )
            #self.page_proxy.register_text_callback(self._page_text_callback)
            #self.page_proxy.register_annotations_callback(self._page_annotations_callback)
            if new_document:
                self.document_proxy = DocumentProxy(document = self.document)#, outline = self.outline_model)
                #self.document_proxy.register_outline_callback(self._outline_callback)
        self.page_widget.page = self.page_proxy
        #self.text_browser.page = self.page_proxy
        #self.maparea_browser.page = self.page_proxy
        #if new_document:
        #    self.outline_browser.document = self.document_proxy

    def initialize_registers(self):
        self.taskreg_browser.DeleteAllItems()
        if self.taskRegister != None:
            self.taskreg_browser.setRegister(self.taskRegister, self.dBController.getActualEntryForFiche if self.dBController != None else None)
            self.taskreg_browser.select(self.ficheId)
        self.strucreg_browser.DeleteAllItems()
        #if self.taskRegister != None:
        #    #self.strucreg_browser.setRegister(self.taskRegister)
        #    self.strucreg_browser.select(self.ficheId)
        self.regbar.setPath("")
        if self.index != None:
            self.strucreg_browser.setRegister(self.index)
            if self.active_register == self.strucreg_browser:
                self.regbar.setPath(self.strucreg_browser.getPath())
        self.hintreg_browser.DeleteAllItems()
        if self.hintRegister != None:
            #print "jest"
            self.hintreg_browser.setRegister(self.hintRegister)
        else:
            #print "niema"
            pass

    def update_registers(self):
        log.log("update_registers", [], 0)
        if self.notify and self.active_register != self.hintreg_browser:
            self.active_register.select(self.ficheId)
        log.log("update_registers return", [], 1)

    # TODO: A zapisywanie wartosci indeksow przy zamykaniu programu
    # TODO: A czyszczenie indeksow przy zamykaniu/otwieraniu nowego katalogu

    def request_entry_change(self):
        log.log("request_entry_change", [], 0)
        if self.dBController != None:
            if self.mainind_panel.isDirty():
                log.log("request_entry_change return", [self.mainind_panel.getEntryIndicesValue()[0]], 1)
                return self.mainind_panel.getEntryIndicesValue()[0]
        log.log("request_entry_change return", [None], 2)
        return None

    def locate_needed(self, ficheId):
        log.log("locate_nedded", [ficheId], 0)
        self.fiche_for_locate = ficheId
        self.locate = 1
        log.log("locate_nedded return", [], 1)

    def update_indices(self):
        log.log("update_indices", [], 0)
        if self.document == None:
            log.log("update_indices return", [], 1)
            return
        # TODO: C co jak dBController == None (co z thaw/freeze? w indeksach itp.)
        if self.dBController != None:
            #if self.left_control.isSearchMode(): # TODO: C j.w.
            #    self.left_control.stopSearch()
            log.log("update_indices inspect", [self.secind_panel.isDirty(), self.mainind_panel.isDirty()], 3)
            if self.secind_panel.isDirty():
                #assert(False)
                self.dBController.setSecondaryIndicesForFiche(self.secind_panel.getValues(), self.secind_panel.getFicheId())
            if self.mainind_panel.isDirty():
                if not self.ignore_entries:
                    self.dBController.setEntriesForFiche(self.mainind_panel.getEntryIndicesValue(), self.mainind_panel.getFicheId())
                self.dBController.setFiche(self.mainind_panel.getFicheIndexValue(), self.mainind_panel.getFicheId())
                self.dBController.setPageAndLineForFiche(self.mainind_panel.getPageAndLineIndicesValue(), self.mainind_panel.getFicheId())
                if self.locate > 0:
                    self.locate = 0
                    self.new_entryreg_browser.locate(self.fiche_for_locate)
            self.mainind_panel.disableInputEvent()
            self.mainind_panel.fillEntryIndices(self.dBController.getEntriesForFiche(self.ficheId), self.ficheId)
            self.mainind_panel.fillFicheIndex(self.dBController.getFiche(self.ficheId), self.ficheId)
            self.mainind_panel.fillPageAndLineIndices(self.dBController.getPageAndLineForFiche(self.ficheId), self.ficheId)
            self.mainind_panel.enableInputEvent()
            self.secind_panel.disableInputEvent()
            self.secind_panel.fill(self.dBController.getSecondaryIndicesForFiche(self.ficheId), self.ficheId)
            self.secind_panel.enableInputEvent()
        self.fiche_for_locate = None
        self.locate = 0
        log.log("update_indices return", [], 2)

    def update_panels(self):
        log.log("update_panels", [], 0)
        #c = Counter()
        if self.ficheId != None: # TODO: NOTE jest otwarty jakis dokument
            if self.dBController != None:
                entry = self.dBController.getOriginalEntryForFiche(self.ficheId)
                if entry == None:
                    if self.active_register == self.new_entryreg_browser and self.new_entryreg_browser.getHypothesis() != None:
                        hypothesis = self.new_entryreg_browser.getHypothesis()
                    else:
                        hypothesis = self.dBController.getHypothesisForFiche(self.ficheId, self.active_register in [self.strucreg_browser, self.new_entryreg_browser] and self.index.isAlphabetic())
                    #print "hypo", c
                    if hypothesis == None:
                        if self.lastEntry != None and self.index.isAlphabetic():
                            hypothesis = self.lastEntry
                        else:
                            hypothesis = self.index.getFicheById(self.ficheId).getHOCREntry(float(self.config.get("hocr_cut", default="0.1")))
                    #print "hyponone", c
                    if hypothesis != None:
                        self.top_panel.setHypothesis(hypothesis)
                    else:
                        self.top_panel.setHypothesis("")
                    #print "set", c
                    #print "entry", c
                else:
                    self.top_panel.setHypothesis("")
                    self.top_panel.setEntry(entry, unselect=True)
        #print "finish", c
        #print
        log.log("update_panels return", [], 1)

    def update_title(self):
        if self.path is None:
            title = APPLICATION_NAME
        else:
            base_path = os.path.basename(self.path)
            if isinstance(base_path, str):
                base_path = base_path.decode(system_encoding, 'replace')
            title = u'%s — %s' % (APPLICATION_NAME, base_path)
        self.SetTitle(title)

    def on_export_bookmarks(self, event):
        log.op("on_export_bookmarks", [], 0)
        if self.dBController != None:
            bookmarksTaskRegister = self.dBController.getBookmarksTaskRegister()
            dialog = wx.FileDialog(self, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT, message = _('Export bookmarks'))
            dialog.SetDirectory(os.getcwd())#self._config.read('save_dir', ''))
        try:
            if dialog.ShowModal() == wx.ID_OK:
                #self._config['save_dir'] = os.path.dirname(dialog.GetPath()) or ''
                fileToSave = dialog.GetPath()
                bookmarksTaskRegister.saveToFile(fileToSave)
        #except IOError:
        #    wx.MessageBox()
        finally:
            dialog.Destroy()
        self.page_widget.SetFocus()
        log.opr("on_export_bookmarks return", [], 1)

    def on_about(self, event):
        message = '%(APPLICATION_NAME)s %(__version__)s\n' + _('Author') + ': %(__author__)s\n' + _('License') + ': %(LICENSE)s'
        message = message % globals()
        wx.MessageBox(message = message, caption = _(u'About…'))

    def on_shortcuts(self, event):
        msg = u'CTRL-E: akceptacja napisu z panelu edycji i przejście do następnej fiszki\n'
        msg += u'CTRL-P: akceptacja napisu z panelu edycji jako prefiksu\n'
        msg += u'CTRL-H: akceptacja napisu z panelu podpowiedzi i przejście do następnej fiszki\n'
        msg += u'CTRL-D: dodanie fiszki do zakładek\n'
        msg += u'CTRL-R: otwarcie wykazu zadaniowego z pliku\n'
        msg += u'CTRL-K: klonowanie fiszki\n'
        msg += u'CTRL-V: podgląd sąsiednich fiszek\n'
        msg += u'CTRL-ENTER: • jeżeli widoczny jest wykaz struktury, haseł lub wielopoziomowy: przejście poziom niżej (do elementu zaznaczonego w wykazie)\n'
        msg += u'• jeżeli fokus jest w panelu edycji: skopiowanie do panelu edycji zawartości panelu podpowiedzi\n'
        msg += u'• jeżeli widoczny jest wykaz podpowiedzi: przejście do wykazu haseł z ewentualnym rozpoczęciem celowego wyszukiwania binarnego dla zaznaczonego elementu wykazu podpowiedzi\n'
        msg += u'CTRL-↑: przejście do pierwszej fiszki w wybranym elemencie wykazu haseł\n'
        msg += u'CTRL-↓: przejście do ostatniej fiszki w wybranym elemencie wykazu haseł\n'
        msg += u'CTRL-<: przejście w lewo w wyszukiwaniu binarnym\n'
        msg += u'CTRL->: przejście w prawo w wyszukiwaniu binarnym\n'
        msg += u'CTRL-[: przejście w lewo w wyszukiwaniu binarnym i akceptacja napisu z panelu edycji\n'
        msg += u'CTRL-]: przejście w prawo w wyszukiwaniu binarnym i akceptacja napisu z panelu edycji\n'
        msg += u'CTRL-B: włączanie/wyłączanie wyszukiwania binarnego; jeżeli widoczny jest wykaz podpowiedzi działa jak CTRL-ENTER\n'
        msg += u'CTRL-←: nawigacja w historii haseł - poprzedni element\n'
        msg += u'CTRL-→: nawigacja w historii haseł - następny element\n'
        msg += u'CTRL-PgDn: przewijanie wykazu haseł na poziomie fiszek\n'
        msg += u'CTRL-PgUp: przewijanie wykazu haseł na poziomie fiszek\n'
        msg += u'ENTER: • jeżeli fokus jest w wykazie podpowiedzi: przejście do wykazu haseł z ewentualnym rozpoczęciem celowego wyszukiwania binarnego dla zaznaczonego elementu wykazu podpowiedzi\n'
        msg += u'• jeżeli fokus jest w panelu edycji - akceptuje fiszkę z napisem z pola edycji jako hasłem; jezeli jest aktywne wyszukiwanie celowe puste pole edycji jest traktowane jako cel\n'
        msg += u'• jeżeli fokus jest w panelu wyszukiwania i aktywny jest wykaz haseł na poziomie haseł - jak CTRL-B\n'  
        msg += u'↑: przejście do poprzedniej fiszki w porządku wykazu jeżeli fokus jest w wykazie i wykaz pokazuje listę fiszek\n'
        msg += u'↓: przejście do następnej fiszki w porządku wykazu jeżeli fokus jest w wykazie i wykaz pokazuje listę fiszek'
        wx.MessageBox(message=msg, caption=u'Skróty klawiaturowe')

    def handle_message(self, event):
        message = event.message
        if isinstance(message, djvu.decode.ErrorMessage):
            self.error_box(message = str(message))
        elif message.document is not self.document:
            # Bogus, non-error message are ignored.
            pass
        self.update_title()
        if isinstance(message, (djvu.decode.RedisplayMessage, djvu.decode.RelayoutMessage)):
            if self.page_job is message.page_job:
                self.update_page_widget()

class Context(djvu.decode.Context):

    def __new__(cls, window):
        return djvu.decode.Context.__new__(cls)

    def __init__(self, window):
        djvu.decode.Context.__init__(self)
        self.window = window

    def handle_message(self, message):
        wx.PostEvent(self.window, WxDjVuMessage(message=message))

class Application(wx.App):

    @apply
    def config():
        def get(self):
            return self._config
        return property(get)

    def except_hook(self, *args):
        sys.__excepthook__(*args)
        wx.CallAfter(self.except_hook_after, *args)

    def except_hook_after(self, type_, value, traceback):
        from traceback import format_exception
        message = _('An unhandled exception occurred. Ideally, this should not happen. Please report the bug to the author.\n\n')
        log.op("ERROR", format_exception(type_, value, traceback), 0)
        message += ''.join(format_exception(type_, value, traceback))
        caption = _('Unhandled exception: %s' % type_.__name__)
        wx.MessageBox(message=message, caption=caption, style = wx.OK | wx.ICON_ERROR)

    def OnInit(self):
        wx.lib.ogl.OGLInitialize()
        self.SetAppName(APPLICATION_NAME)
        if os.name == 'posix':
            legacy_path = os.path.expanduser('~/.Maleks')
        else:
            legacy_path = None
        self._config = config.Config('maleks', legacy_path)
        sys.excepthook = self.except_hook
        return True

    def start(self, argv):
        print "SYSARGV[0]: " + sys.argv[0]
        print "DIRNAME: " + os.path.dirname(sys.argv[0])
        window = MainWindow()
        window.Show(True)
        if argv:
            window.do_open(argv[0])
        return self.MainLoop()

# vim:ts=4 sw=4 et
