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

# TODO: C usuwanie cyklicznosci

import wx
from djvusmooth.i18n import _

class RegisterBrowser(wx.ListCtrl):
	
	def __init__(self, *args, **kwargs):
		wx.ListCtrl.__init__(self, *args, **kwargs)
		#col = wx.ListItem()
		#col.SetId(0)
		#col.SetText(_('Fiche identifiers'))
		#self.InsertColumnItem(0, col)
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onSelect, self)
		self.__listeners = []
		self.__veto = False
		self.__selected = None
		self.__items = []
		self.__binary = False
		self.__left = 0
		self.__right = 0
		self.__center = 0
		self.__item2element = {}
		self.__element2item = {}
	
	def addListener(self, lsn):
		self.__listeners.append(lsn)
	
	def DeleteAllItems(self):
		wx.ListCtrl.DeleteAllItems(self)
		self.__items = []
		self.__item2element = {}
		self.__element2item = {}
	
	def setRegister(self, reg):
		i = 0
		for element in reg:
			item = wx.ListItem()
			item.SetText(element.getLabel())
			item.SetId(i)
			i += 1
			idd = self.InsertItem(item)
			#self.SetStringItem(idd, 0, element.getLabel())
			self.__items.append(item)
			self.__item2element.setdefault(idd, element.getId())
			self.__element2item.setdefault(element.getId(), idd)

	def __getElementId(self, item):
		return self.__item2element[item]
	
	def onSelect(self, event):
		if self.__binary:
			return
		if not self.__veto:
    	# TODO: D uwaga! to wywoluje zmiane strony a w konsekwencji TaskRegisterBrowser.select
			itemId = event.GetIndex() # TODO: NOTE http://wxpython-users.1045709.n5.nabble.com/wx-ListCtrl-Item-Information-on-Double-Click-td3394264.html
			item = self.GetItem(itemId)
			self.__selected = item
			elementId = self.__item2element[itemId]
			for l in self.__listeners:
				l.on_reg_select(elementId)
	
	def __unselect(self, item):
		self.__selected = None
		#item = self.GetItem(itemId)
		mask = item.GetMask()
		state = item.GetState()
		#self.SetItemState(itemId, state & (~wx.LIST_STATE_SELECTED), mask | wx.LIST_MASK_STATE)
		self.SetItemState(item.GetId(), state & (~wx.LIST_STATE_SELECTED), mask | wx.LIST_MASK_STATE)
	
	def __select(self, itemId, veto=False):
		self.EnsureVisible(itemId)
		item = self.GetItem(itemId)
		mask = item.GetMask()
		state = item.GetState()
		if veto:
			self.__veto = True
			self.__selected = item # TODO: NOTE bo nie bedzie ustawione w onSelect
		self.SetItemState(itemId, state | wx.LIST_STATE_SELECTED, mask | wx.LIST_MASK_STATE)
		if self.__binary: # TODO: NOTE bo onSelect uzywamy w trybie binarnym tylko do blokowania
				# zaznaczen przez klikniecie myszki
			self.__selected = item.GetText()
			#print item.GetText(), self.GetItem(self.__selected).GetText()
			for l in self.__listeners:
				l.on_goto_fiche(item.GetText())
		if veto:
			self.__veto = False

	def select(self, elementId):
		if self.__binary:
			return
		if self.__selected != None:
			self.__unselect(self.__selected)
		itemId = self.__element2item.get(elementId)
		if itemId != None:
			self.__select(itemId, veto=True)

	def selectNextElement(self):
		if self.__binary:
			return
		if self.__selected != None:
			itemId = self.GetNextItem(self.__selected.GetId())
			if itemId != -1:
				self.__unselect(self.__selected)
				self.__select(itemId)

	def selectPrevElement(self):
		if self.__binary:
			return
		if self.__selected == None:
			return
		itemId = -1
		prev = -1
		while True:
			itemId = self.GetNextItem(itemId)
			if itemId == self.__selected.GetId():
				if prev != -1:
					self.__unselect(self.__selected)
					self.__select(prev)
					return
			prev = itemId
			if itemId == -1:
				break

	def find(self, text):
		if self.__binary:
			return
		itemId = self.FindItem(-1, text, partial=True)
		if itemId != -1:
			if self.__selected != None:
				self.__unselect(self.__selected)
			self.__select(itemId)

	def binarySearchActive(self):
		return self.__binary

	def stopBinarySearch(self):
		self.__binary = False
		self.Enable(True)
		self.find("")
		
	def __selectCenter(self):
		# TODO: D co jak lenn == 0?
		lenn = self.__right - self.__left + 1
		self.__center = self.__left
		if lenn > 2:
			self.__center += lenn // 2
		if self.__selected != None:
			self.__unselect(self.FindItem(-1, self.__selected))
		self.__select(self.__items[self.__center].GetId())

	def startBinarySearch(self):
		self.find("")
		self.__binary = True
		self.Enable(False)
		self.__left = 0
		self.__right = len(self.__items) - 1
		self.__selectCenter()

	def __limit(self):
		wx.ListCtrl.DeleteAllItems(self)
		for i in range(0, len(self.__items)):
			if i >= self.__left and i <= self.__right:
				self.InsertItem(self.__items[i])
			if self.__items[i].GetText() == self.__selected:
				self.__select(self.__items[i].GetId(), veto=True)
		#print self.__selected, self.GetItem(self.__selected).GetText()

	def nextBinary(self):
		self.__left = self.__center
		self.__selectCenter()
		self.__limit()

	def prevBinary(self):
		self.__right = self.__center
		self.__selectCenter()
		self.__limit()

