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

from djvusmooth.maleks.useful import Notifier
import wx
from djvusmooth.gui import __RESOURCES_PATH__

class TopPanelToolbar(wx.Panel, Notifier):

	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)
		Notifier.__init__(self)
		self.__sizer = wx.BoxSizer(wx.HORIZONTAL)
		self.__editPanelAcceptButton = wx.BitmapButton(self, wx.ID_ANY, wx.Bitmap(__RESOURCES_PATH__ + "/edins.png"))
		self.__sizer.Add(self.__editPanelAcceptButton, 0, wx.ALIGN_CENTER | wx.EXPAND)
		self.SetSizer(self.__sizer)
		self.Bind(wx.EVT_BUTTON, self.__onEditAccept, self.__editPanelAcceptButton)

	def __onEditAccept(self, event):
		for l in self._listeners:
			l.on_edit_accept(event)

class TopPanel(wx.Panel):

	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)
		self.__hypothesisPanel = wx.TextCtrl(self, wx.ID_ANY)
		self.__editPanel = wx.TextCtrl(self, wx.ID_ANY)
		self.__hintPanel = wx.TextCtrl(self, wx.ID_ANY)
		self.toolbar = TopPanelToolbar(self, wx.ID_ANY)
		self.__sizer = wx.BoxSizer(wx.VERTICAL)
		self.__sizer.Add(self.__hypothesisPanel, 0, wx.ALIGN_CENTER | wx.EXPAND)
		self.__sizer.Add(self.__editPanel, 1, wx.ALIGN_CENTER | wx.EXPAND)
		self.__sizer.Add(self.__hintPanel, 2, wx.ALIGN_CENTER | wx.EXPAND)
		self.__sizer.Add(self.toolbar, 3, wx.ALIGN_CENTER | wx.EXPAND)
		self.SetSizer(self.__sizer)

	def getEditPanelContent(self):
		return self.__editPanel.GetValue()

	def setHypothesis(self, content):
		self.__hypothesisPanel.SetValue(content)
		self.__editPanel.SetValue(content)

