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
from maleks.maleks.useful import nvl
#from djvusmooth.i18n import _

class RegisterBrowser(wx.ListView):
	
	def __init__(self, *args, **kwargs):
		wx.ListView.__init__(self, *args, **kwargs)
		#col = wx.ListItem()
		#col.SetId(0)
		#col.SetText(_('Fiche identifiers'))
		#self.InsertColumnItem(0, col)
		self.InsertColumn(0, '', width=15)#wx.LIST_AUTOSIZE)
		self.InsertColumn(1, '', width=15)#wx.LIST_AUTOSIZE)
		self.InsertColumn(2, '', width=300)#wx.LIST_AUTOSIZE)
		self.InsertColumn(3, '', width=wx.LIST_AUTOSIZE)
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onSelect, self)
		self._listeners = []
		self.reset()

	def reset(self):
		self.DeleteAllItems()
		self._veto = False
		self._selected = None
		#self._items = []
		self._binary = False
		self.__left = 0
		self.__right = 0
		self.__center = 0
		#self._item2element = {}
		#self._element2item = {}
		self.__programmaticSelect = False
		self._initialized = False

	def binaryAvailable(self):
		return True

	def allowsNextFiche(self):
		return True
	
	def addListener(self, lsn):
		self._listeners.append(lsn)
	
	def DeleteAllItems(self):
		wx.ListCtrl.DeleteAllItems(self)
		self._items = []
		self._item2element = {}
		self._element2item = {}

	def isActive(self):
		return self._initialized
	
	def setRegister(self, reg, getEntry=None):
		if self._binary:
			for l in self._listeners:
				l.stop_binary_search()
		self.reset()
		i = 0
		for element in reg:
			self.InsertStringItem(i, "")
			self.SetStringItem(i, 1, "")
			self.SetStringItem(i, 2, element.getLabel())
			self.SetStringItem(i, 3, (lambda x: nvl(getEntry(x)) if getEntry != None else "")(element.getId()))
			self._items.append(i)
			self._item2element.setdefault(i, element.getId())
			self._element2item.setdefault(element.getId(), i)
			i += 1
		#self.SetColumnWidth(0, wx.LIST_AUTOSIZE)
		#self.SetColumnWidth(1, wx.LIST_AUTOSIZE)
		self.SetColumnWidth(2, wx.LIST_AUTOSIZE)
		self.SetColumnWidth(3, wx.LIST_AUTOSIZE)
		self._initialized = True

	def __getElementId(self, item):
		return self._item2element[item.GetId()]
	
	def onSelect(self, event):
		if self._binary and (not self.__programmaticSelect):
			self.stopBinarySearch()
			for l in self._listeners:
				l.stop_binary_search()
		if not self._veto:
    	# TODO: D uwaga! to wywoluje zmiane strony a w konsekwencji TaskRegisterBrowser.select
			itemId = event.GetIndex() # TODO: NOTE http://wxpython-users.1045709.n5.nabble.com/wx-ListCtrl-Item-Information-on-Double-Click-td3394264.html
			self._selected = itemId
			elementId = self._item2element[itemId]
			self._element_selected(elementId)

	def _element_selected(self, elementId, notify=True):
		for l in self._listeners:
			l.on_reg_select(elementId, notify=notify)
	
	def _unselect(self, itemId):
		self._selected = None
		self.Select(itemId, on=False)
	
	def _select(self, itemId, veto=False):
		self.EnsureVisible(itemId)
		if veto:
			self._veto = True
			self._selected = itemId # TODO: NOTE bo nie bedzie ustawione w onSelect
		self.Select(itemId)
		if self._binary: # TODO: NOTE bo onSelect uzywamy w trybie binarnym tylko do wychodzenia
				# z trybu binarnego
			self._selected = itemId
			self._element_selected(self._item2element[itemId], notify=False)
		if veto:
			self._veto = False

	def select(self, elementId):
		if self._binary:
			self.stopBinarySearch()
			for l in self._listeners:
				l.stop_binary_search()
		if self._selected != None:
			self._unselect(self._selected)
		itemId = self._element2item.get(elementId)
		if itemId != None:
			self._select(itemId, veto=True)

	def hasSelection(self):
		return self._selected != None

	def getNextFiche(self, entry=None):
		if self._binary:
			self.stopBinarySearch()
			for l in self._listeners:
				l.stop_binary_search()
		if self._selected != None:
			itemId = self.GetNextItem(self._selected)
			if itemId != -1:
				self._unselect(self._selected)
				self._select(itemId, veto=True)
				self._element_selected(self._item2element[itemId], notify=False)
			else:
				self._nextFicheNotFound()

	def _nextFicheNotFound(self):
		pass

	#def selectPrevElement(self):
	#	#if self._binary:
	#	#	return
	#	if self._selected == None:
	#		return
	#	itemId = -1
	#	prev = -1
	#	while True:
	#		itemId = self.GetNextItem(itemId)
	#		if itemId == self._selected.GetId():
	#			if prev != -1:
	#				self._unselect(self._selected)
	#				self._select(prev)
	#				return
	#		prev = itemId
	#		if itemId == -1:
	#			break

	def find(self, text):
		if self._binary:
			self.stopBinarySearch()
			for l in self._listeners:
				l.stop_binary_search()
		itemId = self.FindItem(-1, text, partial=True)
		if itemId != -1:
			if self._selected != None:
				self._unselect(self._selected)
			self._select(itemId)

	def binarySearchActive(self):
		return self._binary

	def stopBinarySearch(self):
		self._binary = False
		self.__unmarkScope()
		
	def __selectCenter(self):
		# TODO: D co jak lenn == 0?
		lenn = self.__right - self.__left + 1
		if self.__left == self.__right == self.__center:
			for l in self._listeners:
				l.stop_binary_search()
			return
		self.__center = self.__left
		self.__center += lenn // 2
		if self._selected != None:
			self._unselect(self._selected)
		self.__programmaticSelect = True
		self._select(self._items[self.__center], veto=True)
		self.__programmaticSelect = False
		if self.__left == self.__right == self.__center:
			for l in self._listeners:
				l.stop_binary_search()

	def __markScope(self):
		for i in self._items:
			if i >= self.__left and i <= self.__right:
				self.SetStringItem(i, 0, "*")
			else:
				self.SetStringItem(i, 0, "")
				
	def __unmarkScope(self):
		for i in self._items:
			self.SetStringItem(i, 0, "")
			self.SetStringItem(i, 1, "")

	def startBinarySearch(self):
		self._binary = True
		self.__left = 0
		self.__right = len(self._items) - 1
		self.__markScope()
		self.__selectCenter()

	def nextBinary(self):
		self.__left = self.__center
		self.SetStringItem(self.__center, 1, ">")
		self.__markScope()
		self.__selectCenter()

	def prevBinary(self):
		if self.__left == self.__right:
			return # TODO: A cos tu jest nie tak! a gdzie wylaczenie wyszukiwania binarnego?
		self.__right = self.__center - 1
		self.SetStringItem(self.__center, 1, "<")
		self.__markScope()
		self.__selectCenter()

	def showFirstElement(self):
		pass

	def showLastElement(self):
		pass

