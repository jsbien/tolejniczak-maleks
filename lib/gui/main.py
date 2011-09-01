# encoding=UTF-8
# Copyright © 2008, 2009, 2010, 2011 Jakub Wilk <jwilk@jwilk.net>
# Copyright © 2009 Mateusz Turcza <mturcza@mimuw.edu.pl>
# Copyright © 2011 Tomasz Olejniczak <tomek.87@poczta.onet.pl>
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

APPLICATION_NAME = 'djvusmooth'
LICENSE = 'GPL-2'

import sys
import itertools
import locale
import os.path
import threading
import tempfile
from Queue import Queue, Empty as QueueEmpty

import djvusmooth.dependencies as __dependencies

import wx
import wx.lib.ogl
import wx.lib.newevent
import wx.lib.scrolledpanel

import djvu.decode
import djvu.const

#from djvusmooth.djvused import StreamEditor
from djvusmooth.gui.page import PageWidget, PercentZoom, OneToOneZoom, StretchZoom, FitWidthZoom, FitPageZoom
#from djvusmooth.gui.page import RENDER_NONRASTER_TEXT, RENDER_NONRASTER_MAPAREA
#from djvusmooth.gui.metadata import MetadataDialog
#from djvusmooth.gui.flatten_text import FlattenTextDialog
#from djvusmooth.gui.text_browser import TextBrowser
#from djvusmooth.gui.outline_browser import OutlineBrowser
#from djvusmooth.gui.maparea_browser import MapAreaBrowser
from djvusmooth.gui.reg_browser import RegisterBrowser
from djvusmooth.gui.struc_browser import StructureRegisterBrowser
from djvusmooth.gui.toppanel import TopPanel
from djvusmooth.gui.regbar import RegisterToolbar
from djvusmooth.gui import dialogs
#from djvusmooth.text import mangle as text_mangle
#import djvusmooth.models.metadata
#import djvusmooth.models.annotations
#import djvusmooth.models.text
#from djvusmooth import models
#from djvusmooth import external_editor
from djvusmooth import config
from djvusmooth.maleks.fiche import StructureIndex, Configuration
from djvusmooth.maleks.registers import HintRegister
from djvusmooth.gui.mode import Mode
from djvusmooth.db.db import DBController

from djvusmooth import __version__, __author__

from djvusmooth.i18n import _

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

class ScrolledPanel(wx.lib.scrolledpanel.ScrolledPanel):

    def OnChildFocus(self, event):
        # We *don't* want to scroll to the child window which just got the focus.
        # So just skip the event:
        event.Skip()

class MainWindow(wx.Frame):

    def _menu_item(self, menu, caption, help, method, style = wx.ITEM_NORMAL, icon = None, id = wx.ID_ANY):
        item = wx.MenuItem(menu, id, caption, help, style)
        self.menu_items.setdefault(method, item)
        if icon is not None:
            bitmap = wx.ArtProvider_GetBitmap(icon, wx.ART_MENU, MENU_ICON_SIZE)
            item.SetBitmap(bitmap)
        self.Bind(wx.EVT_MENU, method, item)
        menu.AppendItem(item)
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
            self._config['main_window_splitter_sash'] = value
        return property(get, set)

    @apply
    def default_sidebar_shown():
        def get(self):
            return self._config.read_bool('main_window_sidebar_shown', True)
        def set(self, value):
            self._config['main_window_sidebar_shown'] = value
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
        self.splitter = wx.SplitterWindow(self, style = wx.SP_LIVE_UPDATE)
        self.splitter.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.on_splitter_sash_changed)

        self.dBController = DBController(self._config)
        if not self.dBController.valid():
            self.error_box(_('Wrong database configuration'))
            self.dBController = None
        
        self.sidepanel = wx.Panel(self.splitter, wx.ID_ANY)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.register_search = wx.TextCtrl(self.sidepanel, wx.ID_ANY)
        self.register_search.Bind(wx.EVT_TEXT, self.register_search_input)
        self.regbar = RegisterToolbar(self.sidepanel, wx.ID_ANY)
        
        #self.sidebar = wx.Choicebook(self.splitter, wx.ID_ANY)
        self.sidebar = wx.Choicebook(self.sidepanel, wx.ID_ANY)
        #self.text_browser = TextBrowser(self.sidebar)
        #self.outline_browser = OutlineBrowser(self.sidebar)
        #self.maparea_browser = MapAreaBrowser(self.sidebar)
        #self.taskreg_browser = TaskRegisterBrowser(self.sidebar)
        self.taskreg_browser = RegisterBrowser(self.sidebar, style=wx.LC_SINGLE_SEL | wx.LC_NO_HEADER)
        self.strucreg_browser = StructureRegisterBrowser(self.sidebar, style=wx.LC_SINGLE_SEL | wx.LC_NO_HEADER)
        self.regbar.addListener(self.strucreg_browser)
        #self.sidebar.AddPage(self.outline_browser, _('Outline'))
        #self.sidebar.AddPage(self.maparea_browser, _('Hyperlinks'))
        #self.sidebar.AddPage(self.text_browser, _('Text'))
        self.sidebar.AddPage(self.taskreg_browser, _('Task Register'))
        self.sidebar.AddPage(self.strucreg_browser, _('Structure Register'))
        self.sidebar.Bind(
            wx.EVT_CHOICEBOOK_PAGE_CHANGED,
            #self.on_sidebar_page_changed
            self._on_sidebar_page_changed(
                #self.on_display_no_nonraster,
                #self.on_display_maparea,
                #self.on_display_text)
                self.on_display_taskreg,
                self.on_display_strucreg
            )
        )
        for widget in [self.taskreg_browser, self.strucreg_browser]:
            widget.addListener(self)
        
        self.main_panel = wx.Panel(self.splitter)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.top_panel = TopPanel(self.main_panel)
        self.top_panel.toolbar.addListener(self)
        #self.top_panel = wx.TextCtrl(self.main_panel, wx.ID_ANY)
        
        #self.scrolled_panel = ScrolledPanel(self.splitter)
        self.scrolled_panel = ScrolledPanel(self.main_panel)
        self.splitter.SetSashGravity(0.1)
        self.active_register = self.taskreg_browser
        
        self.main_sizer.Add(self.top_panel, 0, wx.ALIGN_CENTER | wx.EXPAND)
        self.main_sizer.Add(self.scrolled_panel, 1, wx.ALIGN_CENTER | wx.EXPAND)
        self.main_panel.SetSizer(self.main_sizer)
        
        self.sizer.Add(self.register_search, 0, wx.ALIGN_CENTER | wx.EXPAND)
        self.sizer.Add(self.regbar, 0, wx.ALIGN_LEFT | wx.EXPAND)
        self.sizer.Add(self.sidebar, 1, wx.ALIGN_CENTER | wx.ALIGN_TOP | wx.EXPAND)
        self.sidepanel.SetSizer(self.sizer)
        
        #self.Bind(wx.EVT_KEY_DOWN, self.on_char)
        
        self.do_show_sidebar()
        if not self.default_sidebar_shown:
            self.do_hide_sidebar()
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
        self.dirty = False
        self.do_open(None)
        self.Bind(wx.EVT_CLOSE, self.on_exit)
        
        self.notify = True
        self.__closing = False # TODO: NOTE pomocne w zwalczaniu segmentation fault przy wyjsciu z aplikacji
        self._disable_page_change()
        
        #self.taskreg_browser.Bind(wx.EVT_SET_FOCUS, self.defocus, self.taskreg_browser)

    #def defocus(self, event):
    #    #print "defocus"
    #    self.page_widget.SetFocus()

    def _setup_menu(self):
        menu_bar = wx.MenuBar()
        menu_bar.Append(self._create_file_menu(), _('&File'))
        #menu_bar.Append(self._create_edit_menu(), _('&Edit'))
        menu_bar.Append(self._create_view_menu(), _('&View'))
        menu_bar.Append(self._create_go_menu(), _('&Go'));
        menu_bar.Append(self._create_settings_menu(), _('&Settings'));
        menu_bar.Append(self._create_help_menu(), _('&Help'));
        self.SetMenuBar(menu_bar)

    def _create_file_menu(self):
        menu = wx.Menu()
        #self._menu_item(menu, _('&Open') + '\tCtrl+O', _('Open a DjVu document'), self.on_open, icon=wx.ART_FILE_OPEN)
        self._menu_item(menu, _('&Open'), _('Open a DjVu document'), self.on_open, icon=wx.ART_FILE_OPEN)
        #save_menu_item = self._menu_item(menu, _('&Save') + '\tCtrl+S', _('Save the document'), self.on_save, icon=wx.ART_FILE_SAVE)
        #close_menu_item = self._menu_item(menu, _('&Close') + '\tCtrl+W', _('Close the document'), self.on_close, id=wx.ID_CLOSE)
        close_menu_item = self._menu_item(menu, _('&Close'), _('Close the document'), self.on_close, id=wx.ID_CLOSE)
        self.editable_menu_items += close_menu_item,
        #self.saveable_menu_items += save_menu_item,
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
        for caption, help, zoom, id in \
        [
            (_('Fit &width'),  _('Set magnification to fit page width'),  FitWidthZoom(), None),
            (_('Fit &page'),   _('Set magnification to fit page'),        FitPageZoom(),  wx.ID_ZOOM_FIT),
            (_('&Stretch'),    _('Stretch the image to the window size'), StretchZoom(),  None),
            (_('One &to one'), _('Set full resolution magnification.'),   OneToOneZoom(), wx.ID_ZOOM_100),
        ]:
            self._menu_item(submenu, caption, help, self.on_zoom(zoom), style=wx.ITEM_RADIO, id = id or wx.ID_ANY)
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
            if percent == 100:
                item.Check()
            self.zoom_menu_items[percent] = item
        menu.AppendMenu(wx.ID_ANY, _('&Zoom'), submenu)
        #submenu = wx.Menu()
        #for caption, help, method in \
        #[
        #    (_('&Color') + '\tAlt+C', _('Display everything'),                                            self.on_display_everything),
        #    (_('&Stencil'),           _('Display only the document bitonal stencil'),                     self.on_display_stencil),
        #    (_('&Foreground'),        _('Display only the foreground layer'),                             self.on_display_foreground),
        #    (_('&Background'),        _('Display only the background layer'),                             self.on_display_background),
        #    (_('&None') + '\tAlt+N',  _('Neither display the foreground layer nor the background layer'), self.on_display_none)
        #]:
        #    self._menu_item(submenu, caption, help, method, style=wx.ITEM_RADIO)
        #menu.AppendMenu(wx.ID_ANY, _('&Image'), submenu)
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

    def _create_settings_menu(self):
        menu = wx.Menu()
        #sidebar_menu_item = self._menu_item(menu, _('Show &sidebar') + '\tF9', _('Show/hide the sidebar'), self.on_show_sidebar, style=wx.ITEM_CHECK)
        sidebar_menu_item = self._menu_item(menu, _('Show &sidebar'), _('Show/hide the sidebar'), self.on_show_sidebar, style=wx.ITEM_CHECK)
        if self.default_sidebar_shown:
            sidebar_menu_item.Check()
        #self._menu_item(menu, _(u'External editor…'), _('Setup an external editor'), self.on_setup_external_editor)
        self._menu_item(menu, _('&Work mode'), _('Set work mode'), self.on_set_work_mode)
        return menu

    def _create_help_menu(self):
        menu = wx.Menu()
        #self._menu_item(menu, _('&About') + '\tF1', _('More information about this program'), self.on_about, id=wx.ID_ABOUT)
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

    # TODO: A rozne przypadki bledow:

    def on_edit_accept(self, event):
        if self.top_panel.getEditPanelContent() == '':
            self.error_box(_('Empty edit panel'))
            return
        if self.dBController != None:
            msg = self.dBController.addFicheToEntriesIndex(self.ficheId, self.top_panel.getEditPanelContent())
            if msg != None:
                self.error_box(msg)
                return
        self.hintRegister.addHint(self.top_panel.getEditPanelContent())
        self.dirty = True # TODO: NOTE bo mozemy musiec np. zapisac do pliku dodana powyzej podpowiedz
        if self.active_register.allowsNextFiche() and self.active_register.hasSelection():
            self.active_register.getNextFiche()
        #pass

    def on_edit_prefix_accept(self, event):
        if self.top_panel.getEditPanelContent() == '':
            self.error_box(_('Empty edit panel'))
            return
        if self.dBController != None:
            msg = self.dBController.addFicheToPrefixesIndex(self.ficheId, self.top_panel.getEditPanelContent())
            if msg != None:
                self.error_box(msg)
                return

    def on_structure_element_selected(self, element):
        self.regbar.setPath(element.getDescriptivePath())

    def on_hint_accept(self, event):
        if self.top_panel.getHint() == '':
            self.error_box(_('Empty hint panel'))
            return
        if self.dBController != None:
            msg = self.dBController.addFicheToEntriesIndex(self.ficheId, self.top_panel.getHint())
            if msg != None:
                self.error_box(msg)
                return
        if self.active_register.allowsNextFiche() and self.active_register.hasSelection():
            self.active_register.getNextFiche()
        
    # TODO: A flage __fileOpen i sprawdzanie we wszystkich istotnych metodach

    def _setup_modes(self):
        li = []
        self._install_shortcut(li, wx.ACCEL_CTRL, ord('E'), self.on_edit_accept)
        self._install_shortcut(li, wx.ACCEL_CTRL, ord('P'), self.on_edit_prefix_accept)
        self._install_shortcut(li, wx.ACCEL_CTRL, ord('H'), self.on_hint_accept)
        #self._install_shortcut(li, wx.ACCEL_NORMAL, wx.WXK_PAGEDOWN, self.on_next_fiche)
        #self._install_shortcut(li, wx.ACCEL_NORMAL, wx.WXK_PAGEUP, self.on_prev_fiche)
        self._install_shortcut(li, wx.ACCEL_CTRL, ord('.'), self.on_next_binary)
        self._install_shortcut(li, wx.ACCEL_CTRL, ord(','), self.on_prev_binary)
        self._install_shortcut(li, wx.ACCEL_CTRL, ord('B'), self.on_stop_binary)
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

    def stop_binary_search(self):
        self.active_register.stopBinarySearch()
        if self.active_register in [self.strucreg_browser]:
            self._enable_page_change()
        self.SetStatusText("", 2)
    
    def _start_binary_search(self):
        if self.active_register in [self.strucreg_browser]:    
            self._disable_page_change()
        self.active_register.startBinarySearch()
        self.SetStatusText(_("Binary search"), 2)
    
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

    def on_splitter_sash_changed(self, event):
        self.default_splitter_sash = event.GetSashPosition()
        
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

    def on_open(self, event):
        dialog = OpenDialog(self)
        dialog.SetPath(self._config.read('open_dir', ''))
        try:
            if dialog.ShowModal() == wx.ID_OK:
                self._config['open_dir'] = os.path.dirname(dialog.GetPath()) or ''
                self.do_open(dialog.GetPath())
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

    def do_show_sidebar(self):
        #self.splitter.SplitVertically(self.sidebar, self.scrolled_panel, self.default_splitter_sash)
        #self.splitter.SplitVertically(self.sidepanel, self.scrolled_panel, self.default_splitter_sash)
        self.splitter.SplitVertically(self.sidepanel, self.main_panel, self.default_splitter_sash)
        self.default_sidebar_shown = True

    def do_hide_sidebar(self):
        self.splitter.Unsplit(self.sidebar)
        self.default_sidebar_shown = False

    def register_search_input(self, event):
        self.active_register.find(self.register_search.GetValue())
    
    def on_undisplay(self):
        if self.active_register.binarySearchActive():
            self.stop_binary_search()
        if not self.__closing:
            if self.active_register == self.strucreg_browser:
                self.regbar.setPath("")
   
    def on_display_taskreg(self, event):
        self.on_undisplay()
        self._disable_page_change()           
        self.active_register = self.taskreg_browser
        if self.ficheId != None: self.active_register.select(self.ficheId)

    def on_display_strucreg(self, event):
        self.on_undisplay()
        self.active_register = self.strucreg_browser
        if self.ficheId != None: self.active_register.select(self.ficheId)
        self.regbar.setPath(self.active_register.getPath())
        self._enable_page_change()

    #def on_display_everything(self, event):
    #    self.page_widget.render_mode = djvu.decode.RENDER_COLOR

    #def on_display_foreground(self, event):
    #    self.page_widget.render_mode = djvu.decode.RENDER_FOREGROUND

    #def on_display_background(self, event):
    #    self.page_widget.render_mode = djvu.decode.RENDER_BACKGROUND

    #def on_display_stencil(self, event):
    #    self.page_widget.render_mode = djvu.decode.RENDER_BLACK

    #def on_display_none(self, event):
    #    self.page_widget.render_mode = None

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
    def page_no():
        def get(self):
            return self._page_no
        def set(self, n):
            if self.index is None:
            #if self.document is None:
                self._page_no = 0
                self.status_bar.SetStatusText('', 1)
                return
            #if n < 0 or n >= len(self.document.pages):
            if n < 0 or n >= self.index.getFicheNo():
                return
            self._page_no = n
            self.status_bar.SetStatusText(_('Page %(pageno)d of %(npages)d') % {'pageno':(n + 1), 'npages':self.index.getFicheNo()}, 1)
            self.switch_document(self._page_no)
            #self.update_page_widget(new_page = True)
        return property(get, set)

    def on_first_page(self, event):
        self.page_no = 0

    def on_last_page(self, event):
        #self.page_no = len(self.document.pages) - 1
        self.page_no = self.index.getFicheNo() - 1

    def on_next_page(self, event):
        self.page_no += 1

    def on_previous_page(self, event):
        self.page_no -= 1
    
    def on_reg_select(self, elementId, notify=True):
        self.notify = notify
        self.page_no = self.index.getFicheNoById(elementId)
        self.notify = True

    def request_selection(self):
        return self.ficheId

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
    #        #    self._start_binary_search()
    #        #else:
        if self.active_register.binarySearchActive():
            self.active_register.nextBinary()

    def on_prev_binary(self, event):
    #    if self.mode == _('Browsing mode'):
    #        #if not self.taskreg_browser.binarySearchActive():
    #        #    self._start_binary_search()
    #        #else:
         if self.active_register.binarySearchActive():
             self.active_register.prevBinary()

    def on_stop_binary(self, event):
    #    if self.mode == _('Browsing mode'):
        if not self.active_register.binarySearchActive():
            self._start_binary_search()
        else:
            self.stop_binary_search()

    def on_goto_page(self, event):
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
        self.document = None
        self.index = None
        self.config = None
        self.taskRegister = None
        self.hintRegister = None
        self.top_panel.setHintRegister(None)
        self.ficheId = None

    def do_open(self, path):
        if isinstance(path, unicode):
            path = path.encode(system_encoding)
        if self.dirty:
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
        self.reset()
        self.taskreg_browser.reset()
        self.strucreg_browser.reset()
        self.page_no = 0
        self.dBController.setPerDocumentConnection(None, None, None)
        #def clear_models():
        #    self.metadata_model = self.text_model = self.outline_model = self.annotations_model = None
        #    self.models = ()
        #    self.enable_edit(False)
        if path is None:
            #clear_models()
            pass
        else:
            try:
                self.index = StructureIndex(path)
                self.config = Configuration(path)
                self.config.configureDatabase(self.dBController)
                self.hintRegister = HintRegister(path)
                self.hintRegister.readUserHints(path)
                self.top_panel.setHintRegister(self.hintRegister)
                self.taskRegister = self.config.getDefaultTaskRegister(self.index)
                self.document = self.context.new_document(djvu.decode.FileURI(self.index.getFiche(0).getDjVuPath()))
                try:
                    self.ficheId = self.taskRegister[0].getId()
                except IndexError:
                    self.ficheId = self.index.getFiche(0).getId()
                #self.metadata_model = MetadataModel(self.document)
                #self.text_model = TextModel(self.document)
                #self.outline_model = OutlineModel(self.document)
                #self.annotations_model = AnnotationsModel(path)
                #self.models = self.metadata_model, self.text_model, self.outline_model, self.annotations_model
                #self.enable_edit(True)
            except djvu.decode.JobFailed:
                #clear_models()
                self.reset()
                # TODO: A czyscic tez inne zmienne (j. w.)
                # Do *not* display error message here. It will be displayed by `handle_message()`.
        self.page_no = 0 # again, to set status bar text
        self.update_title()
        self.update_page_widget(new_document = True, new_page = True)
        self.initialize_registers()
        self.update_panels()
        self.dirty = False
        return True

    def switch_document(self, page_no):
        self.document = None
        try:
            self.document = self.context.new_document(djvu.decode.FileURI(self.index.getFiche(page_no).getDjVuPath()))
            self.ficheId = self.index.getFiche(page_no).getId()
        except djvu.decode.JobFailed:
            # TODO: A to powinno powodowac blad!
            self.reset()
            self.page_no = 0
        self.update_title()
        self.update_page_widget(new_document = True, new_page = True)
        self.update_registers()
        self.update_panels()
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
            self.taskreg_browser.setRegister(self.taskRegister)
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

    def update_registers(self):
        if self.notify:
            self.active_register.select(self.ficheId)

    def update_panels(self):
        if self.ficheId != None: # TODO: NOTE jest otwarty jakis dokument
            if self.dBController != None:
                hypothesis = self.dBController.getHypothesisForFiche(self.ficheId, self.active_register == self.strucreg_browser and self.index.isAlphabetic())
                if hypothesis == None:
                    hypothesis = self.index.getFicheById(self.ficheId).getHOCREntry(float(self.config.get("hocr_cut")))
                if hypothesis != None:
                    self.top_panel.setHypothesis(hypothesis)
                else:
                    self.top_panel.setHypothesis("")

    def update_title(self):
        if self.path is None:
            title = APPLICATION_NAME
        else:
            base_path = os.path.basename(self.path)
            if isinstance(base_path, str):
                base_path = base_path.decode(system_encoding, 'replace')
            title = u'%s — %s' % (APPLICATION_NAME, base_path)
        self.SetTitle(title)

    def on_about(self, event):
        message = '%(APPLICATION_NAME)s %(__version__)s\n' + _('Author') + ': %(__author__)s\n' + _('License') + ': %(LICENSE)s'
        message = message % globals()
        wx.MessageBox(message = message, caption = _(u'About…'))

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
        message += ''.join(format_exception(type_, value, traceback))
        caption = _('Unhandled exception: %s' % type_.__name__)
        wx.MessageBox(message=message, caption=caption, style = wx.OK | wx.ICON_ERROR)

    def OnInit(self):
        wx.lib.ogl.OGLInitialize()
        self.SetAppName(APPLICATION_NAME)
        if os.name == 'posix':
            legacy_path = os.path.expanduser('~/.DjVuSmooth')
        else:
            legacy_path = None
        self._config = config.Config('djvusmooth', legacy_path)
        sys.excepthook = self.except_hook
        return True

    def start(self, argv):
        window = MainWindow()
        window.Show(True)
        if argv:
            window.do_open(argv[0])
        return self.MainLoop()

# vim:ts=4 sw=4 et
