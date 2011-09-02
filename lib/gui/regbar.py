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

class RegisterToolbar(wx.Panel, Notifier):

	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)
		Notifier.__init__(self)
		self.__sizer = wx.BoxSizer(wx.VERTICAL)
		self.__label = wx.StaticText(self, wx.ID_ANY)
		self.__bar = wx.Panel(self, wx.ID_ANY)
		self.__barSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.__upButton = wx.BitmapButton(self.__bar, wx.ID_ANY, wx.Bitmap(__RESOURCES_PATH__ + "/up.png"))
		self.__leftButton = wx.BitmapButton(self.__bar, wx.ID_ANY, wx.Bitmap(__RESOURCES_PATH__ + "/prev.png"))
		self.__rightButton = wx.BitmapButton(self.__bar, wx.ID_ANY, wx.Bitmap(__RESOURCES_PATH__ + "/next.png"))
		self.__binaryButton = wx.BitmapButton(self.__bar, wx.ID_ANY, wx.Bitmap(__RESOURCES_PATH__ + "/binary.png"))
		self.__chooseRegisterButton = wx.BitmapButton(self.__bar, wx.ID_ANY, wx.Bitmap(__RESOURCES_PATH__ + "/chreg.png"))
		self.__barSizer.Add(self.__upButton, 0, wx.ALIGN_LEFT)
		self.__barSizer.Add(self.__leftButton, 0, wx.ALIGN_LEFT)
		self.__barSizer.Add(self.__rightButton, 0, wx.ALIGN_LEFT)
		self.__barSizer.Add(self.__binaryButton, 0, wx.ALIGN_LEFT)
		self.__barSizer.Add(self.__chooseRegisterButton, 0, wx.ALIGN_LEFT)
		self.__bar.SetSizer(self.__barSizer)
		self.__sizer.Add(self.__label, 0, wx.ALIGN_LEFT | wx.ALIGN_TOP)
		self.__sizer.Add(self.__bar, 1, wx.ALIGN_LEFT | wx.ALIGN_TOP)
		self.SetSizer(self.__sizer)
		self.Bind(wx.EVT_BUTTON, self.__onUp, self.__upButton)
		self.Bind(wx.EVT_BUTTON, self.__onLeft, self.__leftButton)
		self.Bind(wx.EVT_BUTTON, self.__onRight, self.__rightButton)
		self.Bind(wx.EVT_BUTTON, self.__onBinary, self.__binaryButton)
		self.Bind(wx.EVT_BUTTON, self.__onChooseRegister, self.__chooseRegisterButton)

	def __onChooseRegister(self, event):
		for l in self._listeners:
			l.on_choose_register(event)

	def __onUp(self, event):
		for l in self._listeners:
			l.on_up(event)

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

