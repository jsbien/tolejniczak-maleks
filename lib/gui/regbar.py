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
from maleks.i18n import _
import wx
from maleks.gui import __RESOURCES_PATH__

class RegisterToolbar(wx.Panel, Notifier):

	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)
		Notifier.__init__(self)
		self.__sizer = wx.BoxSizer(wx.VERTICAL)
		self.__label = wx.StaticText(self, wx.ID_ANY)
		self.__bar = wx.Panel(self, wx.ID_ANY)
		self.__barSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.__upButton = wx.BitmapButton(self.__bar, wx.ID_ANY, wx.Bitmap(__RESOURCES_PATH__ + "/up.png"))
		self.__upButton.SetToolTip(wx.ToolTip(_('Go to element parent in structure register')))
		self.__backButton = wx.BitmapButton(self.__bar, wx.ID_ANY, wx.Bitmap(__RESOURCES_PATH__ + "/back.png"))
		self.__backButton.SetToolTip(wx.ToolTip(_('Go back to previous fiche')))
		self.__leftButton = wx.BitmapButton(self.__bar, wx.ID_ANY, wx.Bitmap(__RESOURCES_PATH__ + "/prev.png"))
		self.__leftButton.SetToolTip(wx.ToolTip(_('Go to left in binary search')))
		self.__rightButton = wx.BitmapButton(self.__bar, wx.ID_ANY, wx.Bitmap(__RESOURCES_PATH__ + "/next.png"))
		self.__rightButton.SetToolTip(wx.ToolTip(_('Go to right in binary search')))
		self.__binaryButton = wx.BitmapButton(self.__bar, wx.ID_ANY, wx.Bitmap(__RESOURCES_PATH__ + "/binary.png"))
		self.__binaryButton.SetToolTip(wx.ToolTip(_('Start/stop binary search')))
		self.__chooseRegisterButton = wx.BitmapButton(self.__bar, wx.ID_ANY, wx.Bitmap(__RESOURCES_PATH__ + "/chreg.png"))
		self.__chooseRegisterButton.SetToolTip(wx.ToolTip(_('Load task register from file')))
		self.__defaultRegisterButton = wx.BitmapButton(self.__bar, wx.ID_ANY, wx.Bitmap(__RESOURCES_PATH__ + "/defreg.png"))
		self.__defaultRegisterButton.SetToolTip(wx.ToolTip(_('Show default task register')))
		self.__barSizer.Add(self.__upButton, 0, wx.ALIGN_LEFT)
		self.__barSizer.Add(self.__backButton, 0, wx.ALIGN_LEFT)
		self.__barSizer.Add(self.__leftButton, 0, wx.ALIGN_LEFT)
		self.__barSizer.Add(self.__rightButton, 0, wx.ALIGN_LEFT)
		self.__barSizer.Add(self.__binaryButton, 0, wx.ALIGN_LEFT)
		self.__barSizer.Add(self.__chooseRegisterButton, 0, wx.ALIGN_LEFT)
		self.__barSizer.Add(self.__defaultRegisterButton, 0, wx.ALIGN_LEFT)
		self.__bar.SetSizer(self.__barSizer)
		self.__sizer.Add(self.__label, 0, wx.ALIGN_LEFT | wx.ALIGN_TOP)
		self.__sizer.Add(self.__bar, 1, wx.ALIGN_LEFT | wx.ALIGN_TOP)
		self.SetSizer(self.__sizer)
		self.Bind(wx.EVT_BUTTON, self.__onUp, self.__upButton)
		self.Bind(wx.EVT_BUTTON, self.__onBack, self.__backButton)
		self.Bind(wx.EVT_BUTTON, self.__onLeft, self.__leftButton)
		self.Bind(wx.EVT_BUTTON, self.__onRight, self.__rightButton)
		self.Bind(wx.EVT_BUTTON, self.__onBinary, self.__binaryButton)
		self.Bind(wx.EVT_BUTTON, self.__onChooseRegister, self.__chooseRegisterButton)
		self.Bind(wx.EVT_BUTTON, self.__onDefaultRegister, self.__defaultRegisterButton)

	def __onChooseRegister(self, event):
		for l in self._listeners:
			l.on_choose_register(event)

	def __onDefaultRegister(self, event):
		for l in self._listeners:
			l.on_default_register(event)

	def __onUp(self, event):
		for l in self._listeners:
			l.on_up(event)
			
	def __onBack(self, event):
		for l in self._listeners:
			l.on_back(event)

	def __onLeft(self, event):
		for l in self._listeners:
			l.on_prev_binary(event)

	def __onRight(self, event):
		for l in self._listeners:
			l.on_next_binary(event)

	def __onBinary(self, event):
		for l in self._listeners:
			l.on_stop_binary(event)

	def setPath(self, path):
		self.__label.SetLabel(path)

