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
from maleks.gui.reg_browser import RegisterBrowser
from maleks.maleks.worddict import WordDictionary
from maleks.maleks.useful import nvl, ustr, stru
from maleks.maleks.registers import anyHint, commonprefix
from maleks.maleks import log

class WindowRegisterBrowser(RegisterBrowser):

	def __init__(self, *args, **kwargs):
		RegisterBrowser.__init__(self, *args, **kwargs)
		self._reg = None
		self.__entryGetter = None
		self._smart = True

	def LIMIT(self):
		return 100

	def _map(self, i):
		return i - self._window

	def _unmap(self, i):
		return i + self._window
	
	def reset(self):
		log.log("WindowRegisterBrowser.reset", [], 0)
		RegisterBrowser.reset(self)
		self._window = 0
		self._windowVeto = False
		# czy self._reg = None cos psuje?
		log.log("WindowRegisterBrowser.reset return", [], 1)
	
	def DeleteAllItems(self):
		log.log("WindowRegisterBrowser.DeleteAllItems", [], 0)
		RegisterBrowser.DeleteAllItems(self)
		self._elements = []
		self._elementLabels = []
		log.log("WindowRegisterBrowser.DeleteAllItems return", [], 1)

	def reinitialize(self):
		log.log("WindowRegisterBrowser.reinitialize", [], 0)
		self.reset()
		self.setRegister(self._reg, self.__entryGetter)
		log.log("WindowRegisterBrowser.reinitialize return", [], 1)

	def setRegister(self, reg, getEntry=None):
		#from maleks.maleks.useful import Counter
		#c = Counter()
		#g = Counter()
		log.log("WindowRegisterBrowser.setRegister", [reg, getEntry], 0)
		print len(reg), self.LIMIT()
		if len(reg) < 2 * self.LIMIT():
			#TODO: !A nie obsluguje hint_browsera?"
			self._smart = False
			RegisterBrowser.setRegister(self, reg, getEntry=getEntry)
		else:
			#print "els", c
			self._smart = True
			self.reset()
			i = 0
			self._reg = reg
			self.__entryGetter = getEntry
			#print "init", c
			self._itemsNo = 0
			for element in reg: # dla kazdej fiszki w wykazie utworz odpowiedni element i wypelnij slowniki
				if i < self.LIMIT():
					self.InsertStringItem(i, self._shownLabel(element))
					self.SetStringItem(i, 1, "")
					self.SetStringItem(i, 2, "")
					self.SetStringItem(i, 3, self._secondColumn(element, getEntry))
				self._elementLabels.append(ustr(self._label(element)))
				#self._items.append(i) # identyfikator elementu jest jednoczesnie jego indeksem w tablicy _items
				#self._item2element.setdefault(i, self._id(element))
				#self._element2item.setdefault(self._id(element), i)
				self._itemsNo += 1
				self._elements.append(self._id(element)) # TODO: A uporzadkowac (label powyzej nie potrzebny, tu wrzucic element a id czytac przez funkcje)
				self._customElementInitialization(element, i)
				i += 1
				#print i, c
			self._window = 0
			self.SetColumnWidth(0, wx.LIST_AUTOSIZE) # dopasuj szerokosc kolumn do
			self.SetColumnWidth(3, wx.LIST_AUTOSIZE) # ich zawartosci
			self._initialized = True
			#print "koniec", c
		#print "po", g
		log.log("WindowRegisterBrowser.setRegister return", [], 1)

	def _itemOf(self, elementId):
		return self._elements.index(elementId)

	def _elementOf(self, itemId):
		try:
			res = self._elements[itemId]
			return res
		except IndexError:
			return None

	def smartOn(self):
		self._smart = True

	def smartOff(self):
		self._smart = False
	
	#def __check(self):
	#	for i in range(0, len(self._reg)):
	#		print i, self._reg[i], stru(self._elementLabels[i]), stru(self._elements[i])
	#		assert (ustr(self._elements[i]) == ustr(anyHint(self._reg[i])))

	def _scrollBrowser(self, itemId):
	#mapsafe
		#print itemId, stru(self._elementLabels[itemId]), stru(self._elements[itemId])
		#self.__check()
		log.log("WindowRegisterBrowser._scrollBrowser", [itemId, self._window], 0)
		wx.ListCtrl.DeleteAllItems(self)
		halfBefore = self.LIMIT() / 2
		halfAfter = self.LIMIT() - halfBefore
		if itemId + halfAfter > self._itemsLen():#len(self._items):
			halfBefore += itemId + halfAfter - self._itemsLen()#len(self._items)
			halfAfter -= itemId + halfAfter - self._itemsLen()#len(self._items)
		elif itemId - halfBefore < 0:
			halfAfter += halfBefore - itemId
			halfBefore -= halfBefore - itemId
		#print itemId, self._window, self.__len
		#print halfBefore, halfAfter
		for i in range(0, self.LIMIT()):
			self.InsertStringItem(i, self._shownLabel(self._reg[itemId - halfBefore + i]))
			self.SetStringItem(i, 1, "")
			self.SetStringItem(i, 2, "")
			self.SetStringItem(i, 3, self._secondColumn(self._reg[itemId - halfBefore + i], self.__entryGetter))
		self.SetColumnWidth(0, wx.LIST_AUTOSIZE)
		self.SetColumnWidth(3, wx.LIST_AUTOSIZE)
		self._window = itemId - halfBefore
		log.log("WindowRegisterBrowser.setRegister return", [self._window], 1)

	def onSelect(self, event):
	#mapsafe
		log.op("WindowRegisterBrowser.onSelect", [self._elementOf(self._unmap(event.GetIndex())), self._smart], 0)
		if (not self._smart) or self._windowVeto:
			RegisterBrowser.onSelect(self, event)
		else:
			rawItemId = event.GetIndex()
			itemId = self._unmap(rawItemId)
			if rawItemId / float(self.LIMIT()) < 0.25 or rawItemId / float(self.LIMIT()) > 0.75:
				self._scrollBrowser(itemId)
				self._windowVeto = True
				self._select(itemId)
				self._windowVeto = False
			else:
				RegisterBrowser.onSelect(self, event)
		log.opr("WindowRegisterBrowser.onSelect return", [], 1)

	def _reloadSelect(self, itemId, veto=False):
		log.log("WindowRegisterBrowser._reloadSelect", [self._smart], 0)
		if not self._smart:
			pass
			# TODO: A co wtedy?
		self._scrollBrowser(itemId)
		RegisterBrowser._select(self, itemId, veto=veto)
		log.log("WindowRegisterBrowser._reloadSelect return", [], 1)

	def _select(self, itemId, veto=False):
	#mapsafe
		#print itemId, self._window, self.__len
		log.log("WindowRegisterBrowser._select", [itemId, veto, self._window, self._smart], 0)
		if self._smart and (itemId < self._window or itemId >= self.LIMIT() + self._window):
			#print "tu"
			self._scrollBrowser(itemId)
		#print "ok"
		RegisterBrowser._select(self, itemId, veto=veto)
		log.log("WindowRegisterBrowser._select return", [], 1)

	# TODO: A przeslonic w NewEntryRegisterBrowserze
	def _compare(self, a, b):
		collator = icu.Collator.createInstance(icu.Locale('pl_PL.UTF-8'))
		return collator.compare(a, b)

	# TODO: A to nie jest ogolne - specjalnie dla HintRegisterBrowsera
	# TODO: !!!A poprawic na prefiks
	# TODO: A polaczyc z self.find()
	def _findItem(self, text):
		log.log("WindowRegisterBrowser._findItem", [text], 0)
		if len(self._elementLabels) == 0:
			log.log("WindowRegisterBrowser._findItem return", [-1], 2)
			return -1
		def __pom(left, right):
			#print left, right, stru(text)
			#print stru(self._elementLabels[left]), stru(self._elementLabels[right])
			if left == right:
				if self._compare(self._elementLabels[left], text) <= 0:
					return left
				else:
					return left - 1
			elif left + 1 == right:
				if self._compare(self._elementLabels[right], text) <= 0:
					return right
				elif self._compare(self._elementLabels[left], text) <= 0:
					return left
				else:
					return left - 1			
			lenn = right - left
			center = left + lenn // 2
			#print center, stru(self._elementLabels[center])
			if self._compare(self._elementLabels[center], text) == 0:
				return center
			elif self._compare(self._elementLabels[center], text) > 0:
				return __pom(left, center - 1)
			else:
				return __pom(center + 1, right)
		res = __pom(0, len(self._elementLabels) - 1)
		if self._compare(self._elementLabels[res], text) < 0 and res < len(self._elementLabels) - 1 and len(commonprefix(self._elementLabels[res + 1], text)) > len(commonprefix(self._elementLabels[res], text)):
			res += 1
		res = 0 if res < 0 else res
		log.log("WindowRegisterBrowser._findItem return", [res], 1)
		return res

	def find(self, text):
		log.log("WindowRegisterBrowser.find", [text], 0)
		if not self._smart:
			RegisterBrowser.find(self, text)
		else:
			itemId = self._findItem(text)
			#assert(itemId != -1)
			if itemId != -1:
				if self._selected != None:
					self._unselect(self._selected)
				self._select(itemId)
		log.log("WindowRegisterBrowser.find return", [], 1)

	def binaryAvailable(self):
		return False

	def allowsNextFiche(self):
		return False

