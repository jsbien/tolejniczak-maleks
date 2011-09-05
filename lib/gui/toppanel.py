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
import wx
from maleks.gui import __RESOURCES_PATH__

class TopPanelToolbar(wx.Panel, Notifier):

	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)
		Notifier.__init__(self)
		self.__sizer = wx.BoxSizer(wx.HORIZONTAL)
		self.__editPanelAcceptButton = wx.BitmapButton(self, wx.ID_ANY, wx.Bitmap(__RESOURCES_PATH__ + "/edins.png"))
		self.__editPanelPrefixAcceptButton = wx.BitmapButton(self, wx.ID_ANY, wx.Bitmap(__RESOURCES_PATH__ + "/edpre.png"))
		self.__hintPanelAcceptButton = wx.BitmapButton(self, wx.ID_ANY, wx.Bitmap(__RESOURCES_PATH__ + "/hins.png"))
		self.__sizer.Add(self.__editPanelAcceptButton, 0, wx.ALIGN_CENTER)
		self.__sizer.Add(self.__editPanelPrefixAcceptButton, 1, wx.ALIGN_CENTER)
		self.__sizer.Add(self.__hintPanelAcceptButton, 2, wx.ALIGN_CENTER)
		self.SetSizer(self.__sizer)
		self.Bind(wx.EVT_BUTTON, self.__onEditAccept, self.__editPanelAcceptButton)
		self.Bind(wx.EVT_BUTTON, self.__onEditPrefixAccept, self.__editPanelPrefixAcceptButton)
		self.Bind(wx.EVT_BUTTON, self.__onHintAccept, self.__hintPanelAcceptButton)

	def __onEditAccept(self, event):
		for l in self._listeners:
			l.on_edit_accept(event)

	def __onEditPrefixAccept(self, event):
		for l in self._listeners:
			l.on_edit_prefix_accept(event)

	def __onHintAccept(self, event):
		for l in self._listeners:
			l.on_hint_accept(event)

class TopPanel(wx.Panel):

	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)
		self.__hypothesisPanel = wx.TextCtrl(self, wx.ID_ANY)
		self.__editPanel = wx.TextCtrl(self, wx.ID_ANY)
		self.__hintPanel = wx.TextCtrl(self, wx.ID_ANY)
		self.toolbar = TopPanelToolbar(self, wx.ID_ANY)
		self.__sizer = wx.BoxSizer(wx.VERTICAL)
		self.__sizer.Add(self.__hypothesisPanel, 0, wx.ALIGN_CENTER | wx.EXPAND)
		self.__sizer.Add(self.__editPanel, 0, wx.ALIGN_CENTER | wx.EXPAND)
		self.__sizer.Add(self.__hintPanel, 0, wx.ALIGN_CENTER | wx.EXPAND)
		self.__sizer.Add(self.toolbar, 0, wx.ALIGN_LEFT)
		self.SetSizer(self.__sizer)
		self.__editPanel.Bind(wx.EVT_TEXT, self.__editPanelChanged)
		self.__hintRegister = None
		self.__hint = None

	def setHintRegister(self, register):
		self.__hintRegister = register

	def __editPanelChanged(self, event):
		hint = self.__hintRegister.findHint(self.__editPanel.GetValue())
		if hint != None:
			#print hint[0], hint[1]
			#print type(hint[0]), type(hint[1])
			self.__hintPanel.SetValue(unicode(hint[0], "utf-8") + u" " + unicode(hint[1], "utf-8"))
			self.__hint = hint[0]
		else:
			self.__hintPanel.SetValue("")
			self.__hint = None

	def getHint(self):	
		return self.__hint

	def getEditPanelContent(self):
		return self.__editPanel.GetValue()

	def setHypothesis(self, content):
		self.__hypothesisPanel.SetValue(content)
		self.__editPanel.SetValue(content)
		self.__editPanelChanged(None)

