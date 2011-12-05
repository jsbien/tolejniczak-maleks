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
import icu
#from maleks.gui.reg_browser import RegisterBrowser
from maleks.gui.window_reg_browser import WindowRegisterBrowser
from maleks.maleks.registers import anyHint
from maleks.maleks.useful import ustr, Counter, getUser, stru
from maleks.maleks.worddict import SortedWordDictionary
from maleks.maleks import log
		
class HintRegisterBrowser(WindowRegisterBrowser):

	def __init__(self, *args, **kwargs):
		WindowRegisterBrowser.__init__(self, *args, **kwargs)

	def LIMIT(self):
		return 50
	
	def reset(self):
		log.log("HintRegisterBrowser.reset", [], 0)
		WindowRegisterBrowser.reset(self)
		self.Bind(wx.EVT_KEY_UP, self.__onKey, self)
		self.__hints = []
		log.log("HintRegisterBrowser.reset return", [], 1)

	def __onKey(self, event):
		log.op("HintRegisterBrowser.__onKey", [event.GetKeyCode()], 0)
		if event.GetKeyCode() == wx.WXK_RETURN:
			self.levelDown()
		else:
			event.Skip()
		log.opr("HintRegisterBrowser.__onKey return", [], 1)

	def levelDown(self):
		log.op("HintRegisterBrowser.levelDown", [self._selected if self._selected == None else self._elementOf(self._selected)], 0)
		if self._selected != None:
			for l in self._listeners:
				l.find_in_entry_register(self._elementOf(self._selected))
		log.opr("HintRegisterBrowser.levelDown return", [], 1)

	#def setRegister(self, reg, getEntry=None):
	#	self.reset()
	#	i = 0
	#	for element in reg:
	#		self.InsertStringItem(i, anyHint(element))
	#		self.SetStringItem(i, 1, "")
	#		self.SetStringItem(i, 2, "")
	#		self.SetStringItem(i, 3, element[3])
	#		self._items.append(i)
	#		self._item2element.setdefault(i, anyHint(element))
	#		self._element2item.setdefault(anyHint(element), i)
	#		self.__hints.append(element)
	#		i += 1
	#	self.SetColumnWidth(0, wx.LIST_AUTOSIZE)
	#	self.SetColumnWidth(3, wx.LIST_AUTOSIZE)
	#	self._initialized = True

	def onSelect(self, event):
	#mapsafe
		log.op("HintRegisterBrowser.onSelect", [event], 0)
		WindowRegisterBrowser.onSelect(self, event)
		log.opr("HintRegisterBrowser.onSelect return", [], 1)
	
	def setRegister(self, reg, getEntry=None):
		log.log("HintRegisterBrowser.setRegister", [reg, getEntry], 0)
		#self.__reverseIndex.disableSorting()
		WindowRegisterBrowser.setRegister(self, reg, getEntry=getEntry)
		#c = Counter()
		#self.__reverseIndex.sortAll()
		#print "s", c
		#self.__reverseIndex.enableSorting()
		log.log("HintRegisterBrowser.setRegister return", [], 1)

	def _element_selected(self, elementId):
		log.log("HintRegisterBrowser._element_selected", [elementId], 0)
		for l in self._listeners:
			#l.on_hint_selected(self.__hints[self._element2item[elementId]])
			l.on_hint_selected(self.__hints[self._itemOf(elementId)])
		log.log("HintRegisterBrowser._element_selected return", [], 1)

	def incrementalAdd(self, hint):
		log.log("HintRegisterBrowser.incrementalAdd", [hint], 0)
		#c = Counter()
		if not self._initialized:
			log.log("HintRegisterBrowser.incrementalAdd return", [], 2)
			return
		ind = self.__binaryFind(hint)
		if ind == len(self.__hints):
			#self._items.append(len(self._items))
			self._elements.append(stru(hint))
			self._elementLabels.append(ustr(hint))
		else:
			#self._items.insert(ind, ind)
			self._elements.insert(ind, stru(hint))
			self._elementLabels.insert(ind, ustr(hint))
		self._itemsNo += 1
		#print c
		self._reloadSelect(ind, veto=True)
		log.log("HintRegisterBrowser.incrementalAdd return", [], 1)

	def _label(self, element):
		return anyHint(element)

	def _id(self, element):
		return anyHint(element)

	def _secondColumn(self, element, getEntry):
		return element[3]

	def _customElementInitialization(self, element, i):
		self.__hints.append(element)

	# TODO: C warunki brzegowe?
	# TODO: A sprawdzanie czy rowne?
	# TODO: A zintegrowac z _findItem
	def __binaryFind(self, what):
		log.log("HintRegisterBrowser.__binaryFind", [what], 0)
		collator = icu.Collator.createInstance(icu.Locale('pl_PL.UTF-8'))
		def __pom(left, right):
			if left == right:
				if collator.compare(anyHint(self.__hints[left]), what) > 0:
					return left
				else:
					return left + 1
			elif left + 1 == right:
				if collator.compare(anyHint(self.__hints[left]), what) > 0:
					return left
				elif collator.compare(anyHint(self.__hints[right]), what) > 0:
					return right
				else:
					return right + 1			
			lenn = right - left
			center = left + lenn // 2
			if collator.compare(anyHint(self.__hints[center]), what) > 0:
				return __pom(left, center - 1)
			else:
				return __pom(center + 1, right)
		res = __pom(0, len(self.__hints) - 1)
		log.log("HintRegisterBrowser.__binaryFind return", [res], 1)
		return res
			
	def hintChanged(self, hint):
		log.log("HintRegisterBrowser.hintChanged", [hint], 0)
		itemId = self._findItem(hint)
		if itemId != -1:
			if self._selected != None:
				self._unselect(self._selected)
			self._select(itemId, veto=True)
		log.log("HintRegisterBrowser.hintChanged return", [], 1)

	def binaryAvailable(self):
		return False

	def allowsNextFiche(self):
		return False

