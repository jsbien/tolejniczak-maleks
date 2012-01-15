# encoding=UTF-8
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

import datetime
import wx
from maleks.i18n import _
from maleks.maleks.useful import ustr
from maleks.maleks import log

class MessagePanel(wx.Panel):

	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)
		sizer = wx.BoxSizer(wx.VERTICAL)
		self.__list = MessageList(self, style=wx.LC_SINGLE_SEL | wx.LC_NO_HEADER | wx.LC_REPORT)
		sizer.Add(self.__list, 0, wx.EXPAND)
		self.SetSizer(sizer)

	def setParent(self, parent):
		self.__parent = parent

	def showMessage(self, msg):
		self.__list.showMessage(msg)
		self.Refresh()
		self.Update()
		self.__parent.Refresh()
		self.__parent.Update()
	
	def submit(self, ficheId, entry):
		msg = _('Fiche') + u' ' + ustr(ficheId) + u' ' + _('submitted for acceptation with entry') + u' ' + ustr(entry)
		self.showMessage(msg)
	
	def accept(self, ficheId, entry):
		msg = _('Fiche') + u' ' + ustr(ficheId) + u' ' + _('accepted with entry') + u' ' + ustr(entry)
		self.showMessage(msg)

	def error(self, ficheId, entry):
		msg = _('Fiche') + u' ' + ustr(ficheId) + u' ' + _('not accepted with entry') + u' ' + ustr(entry)
		self.showMessage(msg)

	def automaticBinaryStopped(self, target, steps):
		log.log("automaticBinaryStopped", [target, steps], 0)
		msg = _('Search for') + u" \"" + ustr(target) + u"\" " + _('finished') + u". " + _('Steps:') + u" " + unicode(steps)
		self.showMessage(msg)
		log.log("automaticBinaryStopped return", [], 1)

	def binaryStopped(self, steps):
		log.log("binaryStopped", [steps], 0)
		msg = _('Binary search') + u" " + _('finished') + u". " + _('Steps:') + u" " + unicode(steps)
		self.showMessage(msg)
		log.log("binaryStopped return", [], 1)

	def wrongFiche(self, entry):
		log.log("wrongFiche", [entry], 0)
		msg = ustr(entry) + u": " + _('fiche not in order')
		self.showMessage(msg)
		log.log("wrongFiche return", [], 1)

	def wrongOrder(self, entry):
		log.log("wrongOrder", [entry], 0)
		msg = ustr(entry) + u": " + _('corrupted alphabetic order')
		self.showMessage(msg)
		log.log("wrongOrder return", [], 1)

class MessageList(wx.ListView):

	LIMIT = 100

	def __init__(self, *args, **kwargs):
		wx.ListView.__init__(self, *args, **kwargs)
		self.InsertColumn(0, '', width=wx.LIST_AUTOSIZE)
		self.__messages = []
		self.SetColumnWidth(0, wx.LIST_AUTOSIZE)

	def showMessage(self, msg):
		log.op("showMessage", [msg], 0)
		if len(self.__messages) == MessageList.LIMIT:
			self.__messages = self.__messages[:len(self.__messages) - 1]
		self.__messages.insert(0, str(datetime.datetime.now()) + ": " + msg)
		self.DeleteAllItems()
		i = 0
		for m in self.__messages:
			self.InsertStringItem(i, m)
			i += 1
		self.SetColumnWidth(0, wx.LIST_AUTOSIZE)
		self.Refresh()
		self.Update()
		log.opr("showMessage return", [], 1)

