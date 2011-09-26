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

# TODO: C wyszukiwanie przyrostowe tu i w entry_browserze
# TODO: C locate w przypadku wyszukiwania przyrostowego

import wx
from maleks.gui.reg_browser import RegisterBrowser
from maleks.maleks.useful import nvl

class NewEntryRegisterBrowser(RegisterBrowser):

	def __init__(self, *args, **kwargs):
		RegisterBrowser.__init__(self, *args, **kwargs)
		self.__dBController = None
		self.__limit = 8
		self.__localVeto = False

	def setLimit(self, limit):
		self.__limit = limit

	def reset(self):
		RegisterBrowser.reset(self)
		self.__level = "ENTRY"
		self.__selectedElement = None
		self.__index = 0
		self.__entry = None
		self.__next = None
		self.__noLocate = False
		#self.__binaryType = None

	def setDBController(self, controller):
		self.__dBController = controller

	def initialize(self):
		#if self.binarySearchActive():
		#	for l in self._listeners:
		#		l.stop_binary_search()
		self.reset()
		elements = self.__dBController.getEntriesRegisterWithGaps()
		self.__fillRegister(elements)
		self._initialized = True

	def refresh(self, ficheId):
		self.initialize()
		if self.__level in ["FICHE-GAP", "FICHE-ENTRY"]:
			self.locate(ficheId)

	def __fillRegister(self, elements):
		i = 0
		for element in elements:
			if isinstance(element, tuple):
				text = "(" + str(element[0]) + ")"
			else:
				text = element
			self.InsertStringItem(i, "")
			self.SetStringItem(i, 1, "")
			self.SetStringItem(i, 2, text)
			self._items.append(i)
			self._item2element.setdefault(i, element)
			self._element2item.setdefault(element, i)
			i += 1
		self.SetColumnWidth(2, wx.LIST_AUTOSIZE)

	def selectAndShow(self, ficheId):
		if self.__level in ["FICHE-GAP", "FICHE-ENTRY"]:
			if self.__dBController.hasFiche(self.__selectedElement, ficheId):
				self.__selectAndShow(ficheId)

	def __selectAndShow(self, ficheId):
		if isinstance(self.__selectedElement, tuple):
			(elements, self.__index, self.__next)  = self.__dBController.getFichesForGapForFiche(self.__selectedElement[1], self.__selectedElement[2], ficheId, self.__limit)
		else:
			(elements, self.__index, self.__next)  = self.__dBController.getFichesForEntryForFiche(self.__selectedElement, ficheId, self.__limit)
		self.DeleteAllItems()
		self.__fillRegister(elements)
		itemId = self._element2item[ficheId]
		self.__localVeto = True
		self.__noLocate = True
		self._select(itemId)
		self.__noLocate = False
		self.__localVeto = False
		for l in self._listeners:
			l.on_structure_element_selected(self.__text(self.__selectedElement))

	def __text(self, element):
		if isinstance(element, tuple):
			text = nvl(element[1]) + "-" + nvl(element[2])
		else:
			text = element
		return text

	def onSelect(self, event):
		#print "reg select"
		if self._binary:
			#self.stopBinarySearch()
			for l in self._listeners:
				l.stop_binary_search()
		if self._veto:
			return
		if self.__localVeto:
			RegisterBrowser.onSelect(self, event)
		elif self.__level in ["FICHE-ENTRY", "FICHE-GAP"]:
			itemId = event.GetIndex()
			element = self._item2element[itemId]
			entry = None
			for l in self._listeners:
				entry = l.request_entry_change()
			if entry != None and not (self.__noLocate):
				if not ((self.__entry == None and entry == u"") or (self.__entry != None and (self.__entry == entry or (entry == u"" and self._selected != self._items[0] and self._selected != self._items[-1])))):
					for l in self._listeners:
						l.locate_needed(element)
					RegisterBrowser.onSelect(self, event)
					return
			ind = self.__index + self._items.index(itemId) - self.__limit / 2
			if ind < 0:
				ind = 0
			if (self._items.index(itemId) / float(len(self._items)) < 0.25 or self._items.index(itemId) / float(len(self._items)) > 0.75) and len(self._items) > 1:
				if self.__level == "FICHE-GAP":
					(elements, self.__index, self.__next) = self.__dBController.getFichesForGap(self.__selectedElement[1], self.__selectedElement[2], self.__limit, ind, len(self._items))
				else:
					(elements, self.__index, self.__next) = self.__dBController.getFichesForEntry(self.__selectedElement, self.__limit, ind, len(self._items))					
				self.DeleteAllItems()
				self.__fillRegister(elements)
				itemId = self._element2item[element]
				self.__localVeto = True
				self.__noLocate = True
				self._select(itemId)
				self.__noLocate = False
				self.__localVeto = False
			else:
				RegisterBrowser.onSelect(self, event)
		else:
			itemId = event.GetIndex()
			element = self._item2element[itemId]
			for l in self._listeners:
				l.on_structure_element_selected(self.__text(element))
			RegisterBrowser.onSelect(self, event)

	def _element_selected(self, element, notify=True):
		if self.__level in ["FICHE-ENTRY", "FICHE-GAP"]:
			RegisterBrowser._element_selected(self, element, notify=notify)
		else:
			self.__selectedElement = element

	def levelDown(self):
		if self._binary:
			for l in self._listeners:
				l.stop_binary_search()
		if self.__selectedElement == None: # TODO: D kiedy? - tez co w takiej sytuacji w entry_browserze?
			return
		if self.__level == "ENTRY":
			#print self._selected, ":"
			self.__index = 0
			if isinstance(self.__selectedElement, tuple):
				self.__level = "FICHE-GAP"
				self.__entry = None
				(num, before, after) = self.__selectedElement
				(elements, limitStart, self.__next) = self.__dBController.getFichesForGap(before, after, self.__limit)
				self._select(0)
			else:
				self.__level = "FICHE-ENTRY"
				self.__entry = self.__selectedElement
				(elements, limitStart, self.__next) = self.__dBController.getFichesForEntry(self.__selectedElement, self.__limit)
			self.DeleteAllItems()
			self.__fillRegister(elements)
			self.__localVeto = True
			self.__noLocate = True
			self._select(0)
			self.__noLocate = False
			self.__localVeto = False

	def locate(self, ficheId):
		elements = self.__dBController.getEntriesRegisterWithGaps()
		for el in elements:
			#print el
			if self.__dBController.hasFiche(el, ficheId):
				#print el
				self.__level = "ENTRY"
				self.__selectedElement = el
				self.levelDown()
				self.__selectAndShow(ficheId)
				return
		assert(False)

	#:def _nextFicheNotFound(self):
	#:	if self.__next != None:
	#:		self.__selectAndShow(self.__next)

	def getNextFiche(self, entry=None):
		if self._selected == None: # TODO: C kiedy?
			return
		#print self.__entry, entry
		if (self.__entry == None and entry == "") or (self.__entry != None and (self.__entry == entry or (entry == "" and self._selected != self._items[0] and self._selected != self._items[-1]))):
			#print "nie trzeba"
			RegisterBrowser.getNextFiche(self)
		else:
			itemId = self.GetNextItem(self._selected)
			if itemId != -1:
				ficheId = self._item2element[itemId]
				self.locate(ficheId)
				#print "znaleziono fiszke"
				return
			else:
				#:if self.__next != None:
				#:	self.locate(ficheId)
				#:else:
				#print "nie bylo nastepnej fiszki"
				self.initialize()
				for l in self._listners:
					l.on_structure_element_selected("")

	def onUp(self, event):
		if self.__level in ["FICHE-ENTRY", "FICHE-GAP"]:
			self.initialize()
		for l in self._listeners:
			l.on_structure_element_selected("")

	def select(self, elementId):
		if self.__level in ["FICHE-ENTRY", "FICHE-GAP"]:
			self.__noLocate = True
			RegisterBrowser.select(self, elementId)
			self.__noLocate = False

	def binaryAvailable(self):
		return self.__level == "ENTRY"

	def startBinarySearch(self):
		if isinstance(self.__selectedElement, tuple):
			(self.__leftFiche, self.__rightFiche, length) = self.__dBController.getGapCount(self.__selectedElement[1], self.__selectedElement[2])
			self.__binaryType = "GAP"
		else:
			(self.__leftFiche, self.__rightFiche, length) = self.__dBController.getEntriesCount(self.__selectedElement)
			self.__binaryType = "ENTRY"
		self._binary = True
		self.__left = 0
		self.__right = length - 1
		self.__selectCenter()

	def stopBinarySearch(self):
		self._binary = False

	def nextBinaryAcceptPrepare(self):
		self.__left = self.__center + 1
		if self.__left > self.__right:
			self.__left = self.__right
		if self.__binaryType == "GAP":
			self.__leftFiche = self.__dBController.getFicheForGapPosition(self.__selectedElement[1], self.__selectedElement[2], self.__left)
		else:
			self.__leftFiche = self.__dBController.getFicheForEntryPosition(self.__selectedElement, self.__left)
		return self.__selectCenterPrepare()

	def prevBinaryAcceptPrepare(self):
		#print "!", self.__left, self.__center, self.__right
		self.__right = self.__center - 1
		if self.__right < self.__left:
			self.__right = self.__left
		if self.__binaryType == "GAP":
			self.__rightFiche = self.__dBController.getFicheForGapPosition(self.__selectedElement[1], self.__selectedElement[2], self.__right)
		else:
			self.__rightFiche = self.__dBController.getFicheForEntryPosition(self.__selectedElement, self.__right)
		return self.__selectCenterPrepare()

	def binaryAcceptFinalize(self):
		self._selected = None
		self.DeleteAllItems()
		elements = self.__dBController.getEntriesRegisterWithGaps()
		self.__fillRegister(elements)
		#print "!!!", self.__left, self.__center, self.__right
		#print "@@@", self.__leftFiche, self.__centerFiche, self.__rightFiche
		self.__left = None
		for (i, el) in self._item2element.iteritems():
			#print "$$$", el, self.__centerFiche, #self.__dBController.hasFiche(el, self.__centerFiche)
			#print el
			if self.__dBController.hasFiche(el, self.__centerFiche):
				#print "has"
				self.__selectedElement = el
				for l in self._listeners:
					l.on_structure_element_selected(self.__text(el))
				if isinstance(el, tuple):
					self.__binaryType = "GAP"
					(self.__left, self.__right, self.__center) = self.__dBController.getPositionsForFichesForGap(el[1], el[2], self.__leftFiche, self.__rightFiche, self.__centerFiche)
				else:
					self.__binaryType = "ENTRY"
					(self.__left, self.__right, self.__center) = self.__dBController.getPositionsForFichesForEntry(el, self.__leftFiche, self.__rightFiche, self.__centerFiche)
				print self.__left, self.__center, self.__right
				break
			else:
				pass
				#print "not has"
		#print ":::::", self.__centerFiche
		#print self.__leftFiche, self.__rightFiche, self.__left, self.__right, self.__center
		assert(self.__left != None)
		for l in self._listeners:
			l.invisible_binary_search(self.__centerFiche)
		
	def nextBinary(self):
		self.__left = self.__center + 1
		if self.__left > self.__right:
			self.__left = self.__right
		if self.__binaryType == "GAP":
			self.__leftFiche = self.__dBController.getFicheForGapPosition(self.__selectedElement[1], self.__selectedElement[2], self.__left)
		else:
			self.__leftFiche = self.__dBController.getFicheForEntryPosition(self.__selectedElement, self.__left)
		self.__selectCenter()

	def prevBinary(self):
		self.__right = self.__center - 1
		if self.__right < self.__left:
			self.__right = self.__left
		if self.__binaryType == "GAP":
			self.__rightFiche = self.__dBController.getFicheForGapPosition(self.__selectedElement[1], self.__selectedElement[2], self.__right)
		else:
			self.__rightFiche = self.__dBController.getFicheForEntryPosition(self.__selectedElement, self.__right)
		self.__selectCenter()
		
	def __selectCenterPrepare(self):
		lenn = self.__right - self.__left + 1
		if self.__left == self.__right:
			return False
		self.__center = self.__left
		self.__center += lenn // 2
		if self.__binaryType == "GAP":
			self.__centerFiche = self.__dBController.getFicheForGapPosition(self.__selectedElement[1], self.__selectedElement[2], self.__center)
		else:
			self.__centerFiche = self.__dBController.getFicheForEntryPosition(self.__selectedElement, self.__center)
		#if self.__left == self.__right == self.__center:
		#	return False
		return True			
			
	def __selectCenter(self):
		lenn = self.__right - self.__left + 1
		if self.__left == self.__right:# == self.__center:
			#for l in self._listeners:
			#	l.on_structure_element_selected("")
			for l in self._listeners:
				l.stop_binary_search()
			return
		self.__center = self.__left
		self.__center += lenn // 2
		if self.__binaryType == "GAP":
			self.__centerFiche = self.__dBController.getFicheForGapPosition(self.__selectedElement[1], self.__selectedElement[2], self.__center)
		else:
			self.__centerFiche = self.__dBController.getFicheForEntryPosition(self.__selectedElement, self.__center)
		for l in self._listeners:
			l.invisible_binary_search(self.__centerFiche)
		#if self.__left == self.__right == self.__center:
		#	#for l in self._listeners:
		#	#	l.on_structure_element_selected("")
		#	for l in self._listeners:
		#		l.stop_binary_search()

	def allowsNextFiche(self):
		return self.__level in ["FICHE-ENTRY", "FICHE-GAP"]

	def showFirstElement(self):
		if self.__level == "ENTRY":
			return
		if self.__level == "FICHE-GAP":
			(elements, self.__index, self.__next) = self.__dBController.getFichesForGap(self.__selectedElement[1], self.__selectedElement[2], self.__limit, 0, len(self._items))
		else:
			(elements, self.__index, self.__next) = self.__dBController.getFichesForEntry(self.__selectedElement, self.__limit, 0, len(self._items))
		self.DeleteAllItems()
		self.__fillRegister(elements)
		self.__localVeto = True
		self.__noLocate = True
		self._select(0)
		self.__noLocate = False
		self.__localVeto = False

	def showLastElement(self):
		if self.__level == "ENTRY":
			return
		if self.__level == "FICHE-GAP":
			(elements, self.__index, self.__next, element) = self.__dBController.getFichesForGapForLastFiche(self.__selectedElement[1], self.__selectedElement[2], self.__limit)
		else:
			(elements, self.__index, self.__next, element) = self.__dBController.getFichesForEntryForLastFiche(self.__selectedElement, self.__limit)
		self.DeleteAllItems()
		print elements
		self.__fillRegister(elements)
		itemId = self._element2item[element]
		self.__localVeto = True
		self.__noLocate = True
		self._select(itemId)
		self.__noLocate = False
		self.__localVeto = False
