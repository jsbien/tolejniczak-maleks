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

import wx
from maleks.i18n import _
from maleks.maleks.useful import ustr

class MessagePanel(wx.Panel):

	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)
		sizer = wx.BoxSizer(wx.VERTICAL)
		self.__list = MessageList(self, style=wx.LC_SINGLE_SEL | wx.LC_NO_HEADER | wx.LC_REPORT)
		sizer.Add(self.__list, 0, wx.EXPAND)
		self.SetSizer(sizer)

	def showMessage(self, msg):
		self.__list.showMessage(msg)

	def automaticBinaryStopped(self, target, steps):
		msg = _('Search for') + u" \"" + ustr(target) + u"\" " + _('finished') + u". " + _('Steps:') + u" " + unicode(steps)
		self.__list.showMessage(msg)

	def binaryStopped(self, steps):
		msg = _('Binary search') + u" " + _('finished') + u". " + _('Steps:') + u" " + unicode(steps)
		self.__list.showMessage(msg)

	def wrongFiche(self, entry):
		msg = ustr(entry) + u": " + _('fiche not in order')
		self.__list.showMessage(msg)

	def wrongOrder(self, entry):
		msg = ustr(entry) + u": " + _('corrupted alphabetic order')
		self.__list.showMessage(msg)

class MessageList(wx.ListView):

	LIMIT = 100

	def __init__(self, *args, **kwargs):
		wx.ListView.__init__(self, *args, **kwargs)
		self.InsertColumn(0, '', width=wx.LIST_AUTOSIZE)
		self.__messages = []
		self.SetColumnWidth(0, wx.LIST_AUTOSIZE)

	def showMessage(self, msg):
		if len(self.__messages) == MessageList.LIMIT:
			self.__messages = self.__messages[:len(self.__messages) - 1]
		self.__messages.insert(0, msg)
		self.DeleteAllItems()
		i = 0
		for m in self.__messages:
			self.InsertStringItem(i, m)
			i += 1
		self.SetColumnWidth(0, wx.LIST_AUTOSIZE)

