# encoding=UTF-8
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

from maleks.maleks.useful import Notifier
from maleks.maleks.registers import anyHint
from maleks.i18n import _
import wx
from maleks.gui import __RESOURCES_PATH__
from maleks.maleks import log

class TopPanel(wx.Panel, Notifier):

	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)
		Notifier.__init__(self)
		sizer = wx.FlexGridSizer(3, 3)
		sizer.AddGrowableCol(1, 1)
		self.__hypothesisPanel = wx.TextCtrl(self, wx.ID_ANY)
		self.__editPanel = wx.TextCtrl(self, wx.ID_ANY)
		self.__hintPanel = wx.TextCtrl(self, wx.ID_ANY)
		self.__editPanelAcceptButton = wx.BitmapButton(self, wx.ID_ANY, wx.Bitmap(__RESOURCES_PATH__ + "/edins.png"))
		self.__editPanelAcceptButton.SetToolTip(wx.ToolTip(_('Accept edit panel content')))
		self.__editPanelPrefixAcceptButton = wx.BitmapButton(self, wx.ID_ANY, wx.Bitmap(__RESOURCES_PATH__ + "/edpre.png"))
		self.__editPanelPrefixAcceptButton.SetToolTip(wx.ToolTip(_('Accept edit panel content as prefix')))
		self.__hintPanelAcceptButton = wx.BitmapButton(self, wx.ID_ANY, wx.Bitmap(__RESOURCES_PATH__ + "/hins.png"))
		self.__hintPanelAcceptButton.SetToolTip(wx.ToolTip(_('Accept hint panel content')))
		sizer.Add(wx.Panel(self), 0)
		sizer.Add(self.__hypothesisPanel, 1, wx.EXPAND)
		sizer.Add(wx.Panel(self), 0)
		sizer.Add(self.__editPanelAcceptButton, 0)
		sizer.Add(self.__editPanel, 1, wx.EXPAND)
		sizer.Add(self.__editPanelPrefixAcceptButton, 0)
		sizer.Add(self.__hintPanelAcceptButton, 0)
		sizer.Add(self.__hintPanel, 1, wx.EXPAND)
		sizer.Add(wx.Panel(self), 0)
		self.SetSizerAndFit(sizer)
		self.__editPanel.Bind(wx.EVT_TEXT, self.editPanelChanged)
		self.__editPanel.Bind(wx.EVT_KEY_DOWN, self.__onEditAcceptEnter, self.__editPanel)
		self.__hintPanel.Bind(wx.EVT_TEXT, self.__hintPanelChanged)
		self.Bind(wx.EVT_BUTTON, self.__onEditAccept, self.__editPanelAcceptButton)
		self.Bind(wx.EVT_BUTTON, self.__onEditPrefixAccept, self.__editPanelPrefixAcceptButton)
		self.Bind(wx.EVT_BUTTON, self.__onHintAccept, self.__hintPanelAcceptButton)
		self.__hintRegister = None
		self.__hint = None
		self.__browsingHistory = False

	def focus(self):
		log.log("focus", [], 0)
		self.__editPanel.SetFocus()
		log.log("focus return", [], 1)

	def editPanelHasFocus(self):
		return wx.Window.FindFocus() == self.__editPanel

	def setHintRegister(self, register):
		self.__hintRegister = register

	def __onEditAcceptEnter(self, event):
		log.op("__onEditAcceptEnter", [event.GetKeyCode(), wx.WXK_RETURN], 0)
		if event.GetKeyCode() == wx.WXK_RETURN and not event.ControlDown():
			#print "Enter"
			self.__onEditAccept(event)
		else:
			#print "Not"
			event.Skip()
		log.opr("__onEditAcceptEnter return", [], 1)

	def __onEditAccept(self, event):
		log.op("__onEditAccept", [event, self.__editPanel.GetValue()], 0)
		for l in self._listeners:
			l.on_edit_accept(event)
		log.opr("__onEditAcceptEnter return", [], 1)

	def __onEditPrefixAccept(self, event):
		log.op("__onEditPrefixAccept", [event, self.__editPanel.GetValue()], 0)
		for l in self._listeners:
			l.on_edit_prefix_accept(event)
		log.opr("__onEditPrefixAccept return", [], 1)

	def __onHintAccept(self, event):
		# TODO: C strip siglum?
		log.op("__onHintAccept", [event, self.__hintPanel.GetValue()], 0)
		for l in self._listeners:
			l.on_hint_accept(event)
		log.opr("__onHintAccept return", [], 1)

	def editPanelChanged(self, event):
		log.op("editPanelChanged", [event, self.__editPanel.GetValue()], 0)
		if not self.__browsingHistory:
			for l in self._listeners:
				l.stop_browsing_entry_history(event)
		if self.__hintRegister == None:
			hint = None
		else:
			hint = self.__hintRegister.findHint(self.__editPanel.GetValue())
		if hint != None:
			for l in self._listeners:
				l.on_hint_changed(hint[0])
			#print hint[0], hint[1]
			#print type(hint[0]), type(hint[1])
			self.__hintPanel.SetValue(unicode(hint[0], "utf-8") + (u" " if hint[0] != '' and hint[1] != '' else u"") + unicode(hint[1], "utf-8"))
			self.__hint = hint[0]
		else:
			self.__hintPanel.SetValue("")
			self.__hint = None
		log.opr("editPanelChanged return", [], 1)

	def __hintPanelChanged(self, event):
		log.op("__hintPanelChanged", [event, self.__hintPanel.GetValue()], 0)
		self.__hint = self.__hintPanel.GetValue() # niepoprawne (bo siglum)
		log.opr("__hintPanelChanged return", [], 1)
		
	def __stripSiglum(self, text):
		ind = text.rfind("(")
		return text[:ind - 1]

	def copyHintToEditPanel(self):
		log.op("copyHintToEditPanel", [self.__hintPanel.GetValue()], 0)
		self.setEntry(self.__stripSiglum(self.__hintPanel.GetValue()))
		log.opr("copyHintToEditPanel return", [], 1)

	def getHint(self):
		return self.__hint

	def setHint(self, hint):
		log.log("setHint", [hint], 0)
		self.__hintPanel.SetValue(unicode(anyHint(hint), "utf-8") + u" " + unicode(hint[3], "utf-8"))
		self.__hint = anyHint(hint)
		log.log("setHint return", [self.__hintPanel.GetValue()], 1)

	def getEditPanelContent(self):
		return self.__editPanel.GetValue()

	def setHypothesis(self, content):
		log.log("setHypothesis", [content], 0)
		self.__hypothesisPanel.SetValue(content)
		self.__editPanel.SetValue(content)
		self.editPanelChanged(None)
		#self.__hintPanel.SetFocus() # potrzebne ...
		#self.focus() # ... zeby tu zaznaczylo
		log.log("setHypothesis return", [self.__hypothesisPanel.GetValue()], 1)

	def setEntry(self, entry, browsingHistory=False):
		log.log("setEntry", [entry, browsingHistory], 0)
		if browsingHistory:
			self.__browsingHistory = True
		self.__editPanel.SetValue(entry)
		self.editPanelChanged(None)
		if browsingHistory:
			self.__browsingHistory = False
		log.log("setEntry return", [self.__editPanel.GetValue()], 1)

	def refreshForAutomaticBinary(self, target):
		log.log("refreshForAutomaticBinary", [target], 0)
		self.setEntry(target)
		self.__hintPanel.SetFocus()
		self.focus()
		log.log("refreshForAutomaticBinary return", [], 1)

