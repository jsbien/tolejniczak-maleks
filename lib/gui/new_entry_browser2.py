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

# TODO: C wyszukiwanie przyrostowe tu i w entry_browserze
# TODO: C locate w przypadku wyszukiwania przyrostowego

# TODO: !AAA przejscie do pojedynczej fiszki - przez accept+> nie przechodzi,
# przez ] przechodzi i nie konczy binarnego - poprawic

import wx
import icu
from maleks.gui.window_reg_browser import WindowRegisterBrowser
from maleks.gui.reg_browser import RegisterBrowser
from maleks.maleks.useful import nvl, ustr, stru, Counter, copy
from maleks.maleks import log
from maleks.i18n import _

class MockEvent:

	def __init__(self, itemId):
		self.__itemId = itemId
	
	def GetIndex(self):
		return self.__itemId

class NewEntryRegisterBrowser(WindowRegisterBrowser):

	def __init__(self, *args, **kwargs):
		WindowRegisterBrowser.__init__(self, *args, **kwargs)
		self.__dBController = None
		self.__limit = 100
		self.__localVeto = False
		self.__binarySelectVeto = False
		self.__binaryType = None
		self.__collator = icu.Collator.createInstance(icu.Locale('pl_PL.UTF-8'))
		self.__steps = 0
		self.__messagePanel = None
	
	def setMessagePanel(self, msgPanel):
		self.__messagePanel = msgPanel

	def setLimit(self, limit):
		self.__limit = limit

	def reset(self):
		#print "reset"
		log.log("NewEntryRegisterBrowser.reset", [], 0)
		WindowRegisterBrowser.reset(self)
		self.__level = "ENTRY"
		self.__selectedElement = None
		self.__index = 0
		self.__entry = None
		self.__next = None
		self.__noLocate = False
		self.__binaryTarget = None
		self.__leftTargetBinary = False
		#self.__binaryType = None
		log.log("NewEntryRegisterBrowser.reset return", [], 1)

	def getSelectedElement(self):
		return self.__selectedElement

	def setDBController(self, controller):
		self.__dBController = controller

	def initialize(self, entry=None):
		#if self.binarySearchActive():
		#	for l in self._listeners:
		#		l.stop_binary_search()
		log.log("NewEntryRegisterBrowser.initialize", [entry, self.__selectedElement], 0)
		if entry == None:
			self.reset()
			(elements, self.__entryLens) = self.__dBController.getEntriesRegisterWithGaps()
			self.__fillRegister(elements)
			self._initialized = True
		else:
			if not self._incrementalUpdate([self.__entryOf(self.__selectedElement), entry]):
				#self.reset()
				(elements, self.__entryLens) = self.__dBController.getEntriesRegisterWithGaps()
				self.__fillRegister(elements)
				self._initialized = True
			else:
				#print self.__selectedElement
				self._showUpdate()
		for l in self._listeners:
			l.on_structure_element_selected("")
		log.log("NewEntryRegisterBrowser.initialize return", [], 1)

	def refresh(self, ficheId):
		log.log("NewEntryRegisterBrowser.refresh", [ficheId, self.__level], 0)
		if self.__level in ["FICHE-GAP", "FICHE-ENTRY"]:
			self.initialize()
			self.locate(ficheId)
		else:
			self.initialize()
		log.log("NewEntryRegisterBrowser.refresh return", [], 1)

	def DeleteAllItems(self):
		log.log("NewEntryRegisterBrowser.DeleteAllItems", [], 0)
		WindowRegisterBrowser.DeleteAllItems(self)
		self.__elementObjects = []
		self.__entryLens = {}
		log.log("NewEntryRegisterBrowser.DeleteAllItems return", [], 1)

	def __fillRegister(self, elements, goingDown=True):
		log.log("NewEntryRegisterBrowser.__fillRegister", [elements, goingDown, self.__level], 0)
		self._itemsNo = 0
		#print len(elements)
		if len(elements) < 2 * self.LIMIT() or self.__level in ["FICHE-ENTRY", "FICHE-GAP"]:
			#print "smart"
			self._smart = False
			i = 0
			self._reg = copy(elements)
			#print len(elements)
			#print type(elements)
			for element in self._reg:
				#print element
				self.InsertStringItem(i, self._shownLabel(element))
				self.SetStringItem(i, 1, "")
				self.SetStringItem(i, 2, "")
				#self._items.append(i)
				#self._item2element.setdefault(i, element)
				#self._element2item.setdefault(element, i)
				self._itemsNo += 1
				self._elementLabels.append(ustr(self._label(element)))
				self._elements.append(self._id(element))
				self.__elementObjects.append(element)
				self._customElementInitialization(element, i)
				i += 1
			self.SetColumnWidth(0, wx.LIST_AUTOSIZE)
			self._window = 0
		else:
			#print "nonsmart"
			self._smart = True
			i = 0
			self._reg = copy(elements)
			#print len(elements)
			#print type(elements)
			for element in self._reg:
				#print element
				if i < self.LIMIT():
					self.InsertStringItem(i, self._shownLabel(element))
					self.SetStringItem(i, 1, "")
					self.SetStringItem(i, 2, "")
				#self._items.append(i)
				#self._item2element.setdefault(i, element)
				#self._element2item.setdefault(element, i)
				self._itemsNo += 1
				self._elementLabels.append(ustr(self._label(element)))
				self._elements.append(self._id(element))
				self.__elementObjects.append(element)
				self._customElementInitialization(element, i)
				i += 1
			self.SetColumnWidth(0, wx.LIST_AUTOSIZE)
			self._window = 0
		#print len(self._elements)
		log.log("NewEntryRegisterBrowser.__fillRegister return", [self._smart], 1)

	def _itemOf(self, elementId):
		return self._elements.index(elementId)

	def _elementOf(self, itemId):
		try:
			res = self._elements[itemId]
			return res
		except IndexError:
			return None

	def _incrementalUpdate(self, entries):
		#print "::::", entries
		#:(neighbourhoods, ok, hasFirstNone, hasLastNone, entryLens) = self.__dBController.getPartialEntriesRegisterWithGaps(entries)
		#:for (k, v) in entryLens.iteritems():
		#:	self.__entryLens[k] = v
		log.log("NewEntryRegisterBrowser._incrementalUpdate", [entries], 0)
		(neighbourhoods, ok, hasFirstNone, hasLastNone, self.__entryLens) = self.__dBController.getPartialEntriesRegisterWithGaps(entries)
		#print neighbourhoods
		if not ok:
			#print "blad"
			log.log("NewEntryRegisterBrowser._incrementalUpdate return", [False], 1)
			return False
		log.log("NewEntryRegisterBrowser._incrementalUpdate inspect", [neighbourhoods], 4)
		for (entry, elements) in neighbourhoods:
			#print elements
			#for e in elements:
			#	assert(isinstance(e, tuple) or isinstance(e, str))
			if ((not hasFirstNone) and isinstance(self.__elementObjects[0], tuple) and self.__elementObjects[0][1] == None) or (isinstance(elements[0], tuple) and elements[0][1] == None):
				indf = 0
			else:
				indf = self.__findForIncremental(elements[0])
			if ((not hasLastNone) and isinstance(self.__elementObjects[-1], tuple) and self.__elementObjects[-1][2] == None) or (isinstance(elements[-1], tuple) and elements[-1][2] == None):
				indt = len(self._elements) - 1
			else:
				indt = self.__findForIncremental(elements[-1])
			log.log("NewEntryRegisterBrowser._incrementalUpdate assert", [indf, indt, elements[0], elements[-1]], 3)
			assert(indf != -1)
			assert(indt != -1)
			if len(elements) < (indt - indf + 1):
				#print indt, indf, neighbourhoods
				for i in range(0, len(elements)):
					self._elements[indf + i] = self._id(elements[i])
					self._elementLabels[indf + i] = ustr(self._label(elements[i]))
					self.__elementObjects[indf + i] = elements[i]
				j = indf + len(elements)
				for i in range(indf + len(elements), indt + 1):
					self._elements.remove(self._elements[j])
					#print ":", self._elementLabels, self._elementLabels[j]
					self._elementLabels.remove(ustr(self._elementLabels[j]))
					self.__elementObjects.remove(self.__elementObjects[j])
					self._itemsNo -= 1
			else:
				for i in range(0, indt - indf + 1):
					self._elements[indf + i] = self._id(elements[i])
					self._elementLabels[indf + i] = ustr(self._label(elements[i]))
					self.__elementObjects[indf + i] = elements[i]
				for i in range(indt - indf + 1,  len(elements)):
					self._elements.insert(indf + i, self._id(elements[i]))
					self._elementLabels.insert(indf + i, ustr(self._label(elements[i])))
					self.__elementObjects.insert(indf + i, elements[i])
					self._itemsNo += 1
			self._reg = copy(self.__elementObjects)
		#print ":", len(self._elements), self._itemsNo
		if len(self._elements) < 2 * self.LIMIT():
			self._smart = False
		else:
			self._smart = True
		#:self.DeleteAllItems()
		#:elements = self.__dBController.getEntriesRegisterWithGaps()
		#:self.__fillRegister(elements)
		log.log("NewEntryRegisterBrowser._incrementalUpdate return", [True, self._smart], 2)
		return True

	def prepareForUpdateAfterAccept(self, ficheId):
		log.log("NewEntryRegisterBrowser.prepareForUpdateAfterAccept", [ficheId, self._elements], 0)
		self.__formerEntryElement = None
		if self.__level == "ENTRY":
			for el in self._elements:
				print el
				if self.__dBController.hasFiche(el, ficheId):
					self.__formerEntryElement = el
		log.log("NewEntryRegisterBrowser.prepareForUpdateAfterAccept return", [self.__formerEntryElement], 1)

	def updateAfterAccept(self, entry):
		log.log("NewEntryRegisterBrowser.updateAfterAccept", [entry, self.__formerEntryElement], 0)
		if self.__level == "ENTRY":
			if self.__formerEntryElement != None:
				inc = self._incrementalUpdate([entry, self.__entryOf(self.__formerEntryElement)])
				if inc:
					self.find(entry)
					log.log("NewEntryRegisterBrowser.updateAfterAccept return", [], 1)
					return
			self.DeleteAllItems()
			(elements, self.__entryLens) = self.__dBController.getEntriesRegisterWithGaps()
			self.__fillRegister(elements)
		log.log("NewEntryRegisterBrowser.updateAfterAccept return", [], 2)

	def _showUpdate(self):
		log.log("NewEntryRegisterBrowser._showUpdate", [self._smart], 0)
		if self._smart:
			wx.ListCtrl.DeleteAllItems(self)
			for i in range(0, self.LIMIT()):
				self.InsertStringItem(i, self._shownLabel(self._reg[i]))
				self.SetStringItem(i, 1, "")
				self.SetStringItem(i, 2, "")
			self.SetColumnWidth(0, wx.LIST_AUTOSIZE)
			self._window = 0
		else:
			self.DeleteAllItems()
			self.__fillRegister(self._reg)
		log.log("NewEntryRegisterBrowser._showUpdate return", [], 1)

	def _scrollBrowser(self, itemId):
	#mapsafe
		log.log("NewEntryRegisterBrowser._scrollBrowser", [itemId, self._smart], 0)
		#print itemId, stru(self._elementLabels[itemId]), stru(self._elements[itemId])
		#self.__check()
		#print self._smart
		if self._smart:
			wx.ListCtrl.DeleteAllItems(self)
			halfBefore = self.LIMIT() / 2
			halfAfter = self.LIMIT() - halfBefore
			if itemId + halfAfter > self._itemsLen():#len(self._items):
				halfBefore += itemId + halfAfter - self._itemsLen()#len(self._items)
				halfAfter -= itemId + halfAfter - self._itemsLen()#len(self._items)
			elif itemId - halfBefore < 0:
				halfAfter += halfBefore - itemId
				halfBefore -= halfBefore - itemId
			#print itemId, self.__window, self.__len
			#print halfBefore, halfAfter
			for i in range(0, self.LIMIT()):
				self.InsertStringItem(i, self._shownLabel(self._reg[itemId - halfBefore + i]))
				self.SetStringItem(i, 1, "")
				self.SetStringItem(i, 2, "")
			self.SetColumnWidth(0, wx.LIST_AUTOSIZE)
			self._window = itemId - halfBefore
		else:
			c = Counter()
			self.DeleteAllItems()
			#print "delete", c
			self.__fillRegister(self._reg)
		log.log("NewEntryRegisterBrowser._scrollBrowser return", [], 1)

	def _label(self, element):
		if isinstance(element, tuple):
			text = "(" + str(element[0]) + ")"
		else:
			#print element
			#assert isinstance(element, str)
			text = element
		return text

	def _id(self, element):
		return element

	def _shownLabel(self, element):
		return self._label(element)
		#if isinstance(element, tuple) or self.__level in ["FICHE-GAP", "FICHE-ENTRY"]:
		#	return self._label(element)
		#else:
		#return self._label(element) + " (" + str(self.__entryLens[element]) + ")"

	def selectAndShow(self, ficheId):
		log.log("NewEntryRegisterBrowser.selectAndShow", [ficheId, self.__level, self.__selectedElement], 0)
		if self.__level in ["FICHE-GAP", "FICHE-ENTRY"]:
			if self.__dBController.hasFiche(self.__selectedElement, ficheId):
				self.__selectAndShow(ficheId)
		log.log("NewEntryRegisterBrowser.selectAndShow return", [], 1)

	def __selectAndShow(self, ficheId):
		log.log("NewEntryRegisterBrowser.__selectAndShow", [ficheId, self.__selectedElement], 0)
		if isinstance(self.__selectedElement, tuple):
			(elements, self.__index, self.__next)  = self.__dBController.getFichesForGapForFiche(self.__selectedElement[1], self.__selectedElement[2], ficheId, self.__limit)
		else:
			(elements, self.__index, self.__next)  = self.__dBController.getFichesForEntryForFiche(self.__selectedElement, ficheId, self.__limit)
		self.DeleteAllItems()
		self.__fillRegister(elements)
		itemId = self._itemOf(ficheId)
		self.__localVeto = True
		self.__noLocate = True
		self._select(itemId)
		self.__noLocate = False
		self.__localVeto = False
		for l in self._listeners:
			l.on_structure_element_selected(self.__text(self.__selectedElement))
		log.log("NewEntryRegisterBrowser.__selectAndShow return", [], 1)

	def __text(self, element):
		if isinstance(element, tuple):
			text = nvl(element[1]) + "-" + nvl(element[2])
		else:
			text = element
		if self._binary and self.hasTarget():
			text = stru(self.__binaryTarget) + ": " + text
		return text

	def _item(self, i):
		if i == -1:
			return self._itemsLen()
		return i

	def onSelect(self, event):
	#mapsafe
		log.op("NewEntryRegisterBrowser.onSelect", [self._elementOf(self._unmap(event.GetIndex())), self._smart, self._windowVeto, self.__level], 0)
		if (not self._smart) or self._windowVeto or self.__level in ["FICHE-ENTRY", "FICHE-GAP"]:
			self.nonSmartSelect(event)
		else:
			rawItemId = event.GetIndex()
			itemId = self._unmap(rawItemId)
			if rawItemId / float(self.LIMIT()) < 0.25 or rawItemId / float(self.LIMIT()) > 0.75:
				self._scrollBrowser(itemId)
				self._windowVeto = True
				self._select(itemId)
				self._windowVeto = False
			else:
				self.nonSmartSelect(event)
		log.opr("NewEntryRegisterBrowser.onSelect return", [], 1)

	def _select(self, itemId, veto=False):
	#mapsafe
		log.log("NewEntryRegisterBrowser._select", [itemId, veto, self.__level, self._smart, self._window], 0)
		if self.__level == "ENTRY" and self._smart and (itemId < self._window or itemId >= self.LIMIT() + self._window):
			self._scrollBrowser(itemId)
		RegisterBrowser._select(self, itemId, veto=veto)
		log.log("NewEntryRegisterBrowser._select return", [], 1)

	def __binarySelect(self, itemId):
		log.log("NewEntryRegisterBrowser.__binarySelect", [itemId], 0)
		self.__binarySelectVeto = True
		self._select(itemId, veto=True)
		self.__binarySelectVeto = False
		log.log("NewEntryRegisterBrowser.__binarySelect return", [], 1)
	
	def handleClone(self, entries, ficheId):
		log.log("NewEntryRegisterBrowser.handleClone", [entries, ficheId], 0)
		if self.__level in ["FICHE-ENTRY", "FICHE-GAP"]:
			self.locate(ficheId)
		else:
			if not self._incrementalUpdate(entries):
				(elements, self.__entryLens) = self.__dBController.getEntriesRegisterWithGaps()
				self.__fillRegister(elements)
				self._initialized = True
			else:
				self._showUpdate()
		log.log("NewEntryRegisterBrowser.handleClone return", [], 1)

	def nonSmartSelect(self, event):
	#mapsafe
		log.log("NewEntryRegisterBrowser.nonSmartSelect", [event, self._binary, self.__localVeto, self.__level, self.__selectedElement], 0)
		if self.__binarySelectVeto:
			log.log("NewEntryRegisterBrowser.nonSmartSelect return", [], 1)
			return
		if self._binary:
			#self.stopBinarySearch()
			for l in self._listeners:
				l.stop_binary_search()
		if self._veto:
			log.log("NewEntryRegisterBrowser.nonSmartSelect return", [], 2)
			return
		if self.__localVeto:
			RegisterBrowser.onSelect(self, event)
		elif self.__level in ["FICHE-ENTRY", "FICHE-GAP"]:
			itemId = self._unmap(event.GetIndex())
			element = self._elementOf(itemId)
			entry = None
			for l in self._listeners:
				entry = l.request_entry_change()
			if entry != None and not (self.__noLocate):
				if not ((self.__entry == None and entry == u"") or (self.__entry != None and (self.__entry == entry or (entry == u"" and self._selected != self._item(0) and self._selected != self._item(-1))))):
					for l in self._listeners:
						l.locate_needed(element) # TODO: A zaznacza nie ta fiszke co potrzeba
							# zeby odtworzyc: w fiszce A modyfikujemy haslo w indeksie i przechodzimy
							# strzalka do fiszki B, pokaze sie fiszka A w swoim nowym hasle/dziurze
					RegisterBrowser.onSelect(self, event)
					log.log("NewEntryRegisterBrowser.nonSmartSelect return", [], 3)
					return
			#ind = self.__index + self._items.index(itemId) - self.__limit / 2
			ind = self.__index + self._item(itemId) - self.__limit / 2
			if ind < 0:
				ind = 0
			#if (self._items.index(itemId) / float(self._itemsLen()) < 0.25 or self._items.index(itemId) / float(self._itemsLen()) > 0.75) and self._itemsLen() > 1:
			#print self._item(itemId), self._itemsLen(), itemId
			if (self._item(itemId) / float(self._itemsLen()) < 0.25 or self._item(itemId) / float(self._itemsLen()) > 0.75) and self._itemsLen() > 1:
				if self.__level == "FICHE-GAP":
					(elements, self.__index, self.__next) = self.__dBController.getFichesForGap(self.__selectedElement[1], self.__selectedElement[2], self.__limit, ind, self._itemsLen())
				else:
					(elements, self.__index, self.__next) = self.__dBController.getFichesForEntry(self.__selectedElement, self.__limit, ind, self._itemsLen())
				self.DeleteAllItems()
				self.__fillRegister(elements)
				itemId = self._itemOf(element)
				self.__localVeto = True
				self.__noLocate = True
				self._select(itemId)
				self.__noLocate = False
				self.__localVeto = False
			else:
				RegisterBrowser.onSelect(self, event)
		else:
			itemId = self._unmap(event.GetIndex())
			element = self._elementOf(itemId)
			#print element
			for l in self._listeners:
				l.on_structure_element_selected(self.__text(element))
			RegisterBrowser.onSelect(self, event)
			log.log("NewEntryRegisterBrowser.nonSmartSelect return", [], 4)

	def _element_selected(self, element, notify=True):
		log.log("NewEntryRegisterBrowser._element_selected", [element, notify, self.__level], 0)
		if self.__level in ["FICHE-ENTRY", "FICHE-GAP"]:
			RegisterBrowser._element_selected(self, element, notify=notify)
		else:
			self.__selectedElement = element
		log.log("NewEntryRegisterBrowser._element_selected return", [], 1)

	def levelDown(self):
		log.op("NewEntryRegisterBrowser.levelDown", [self._binary, self.__selectedElement], 0)
		if self._binary:
			for l in self._listeners:
				l.stop_binary_search()
		if self.__selectedElement == None: # TODO: D kiedy? - tez co w takiej sytuacji w entry_browserze?
			log.opr("NewEntryRegisterBrowser.levelDown return", [])
			return
		if self.__level == "ENTRY":
			#print self._selected, ":"
			self.__index = 0
			if isinstance(self.__selectedElement, tuple):
				self.__level = "FICHE-GAP"
				self.__entry = None
				(num, before, after) = self.__selectedElement
				(elements, limitStart, self.__next) = self.__dBController.getFichesForGap(before, after, self.__limit)
			else:
				self.__level = "FICHE-ENTRY"
				self.__entry = self.__selectedElement
				(elements, limitStart, self.__next) = self.__dBController.getFichesForEntry(self.__selectedElement, self.__limit)
				(indexed, hypo) = self.__dBController.getEntryCount(self.__selectedElement)
				self.__messagePanel.showMessage(ustr(self.__selectedElement) + u': ' + _(u'Indexed fiches: ') + unicode(indexed) + u' ' + _(u'Hypothetical fiches: ') + unicode(hypo))
			self.DeleteAllItems()
			self.__fillRegister(elements)
			self.__localVeto = True
			self.__noLocate = True
			self._select(0)
			self.__noLocate = False
			self.__localVeto = False
			log.opr("NewEntryRegisterBrowser.levelDown return", [], 1)

	# ta metoda powoduje wyswietlenie w wykazie hasel odpowiedniej listy fiszek na
	# ktorej jest fiszka po zmianie czegos w panelu indeksow
	# TODO: A dodac efektywne odswiezanie wykazu hasel
	def locate(self, ficheId):
		log.log("NewEntryRegisterBrowser.locate", [ficheId], 0)
		(elements, self.__entryLens) = self.__dBController.getEntriesRegisterWithGaps()
		for el in elements:
			#print el
			if self.__dBController.hasFiche(el, ficheId):
				#print el
				self.__level = "ENTRY"
				self.__selectedElement = el
				self.levelDown()
				self.__selectAndShow(ficheId)
				log.log("NewEntryRegisterBrowser.locate return", [self.__selectedElement], 1)
				return
		log.log("NewEntryRegisterBrowser.locate assert", [elements], 2)
		assert(False)

	#:def _nextFicheNotFound(self):
	#:	if self.__next != None:
	#:		self.__selectAndShow(self.__next)

	def getLastFicheOfSelected(self):
		log.log("NewEntryRegisterBrowser.getLastFicheOfSelected", [self.__selectedElement], 0)
		log.log("NewEntryRegisterBrowser.getLastFicheOfSelected return", [self.__dBController.getLastFicheOfElement(self.__selectedElement)], 1)
		return self.__dBController.getLastFicheOfElement(self.__selectedElement)

	def getFirstFicheOfSelected(self):
		log.log("NewEntryRegisterBrowser.getFirstFicheOfSelected", [self.__selectedElement], 0)
		log.log("NewEntryRegisterBrowser.getFirstFicheOfSelected return", [self.__dBController.getFirstFicheOfElement(self.__selectedElement)], 1)
		return self.__dBController.getFirstFicheOfElement(self.__selectedElement)

	def getElementPath(self):
		if self.__selectedElement != None:
			return self.__text(self.__selectedElement)
		else:
			return ""

	def gotoPrevFiche(self):
		log.log("NewEntryRegisterBrowser.gotoPrevFiche", [], 0)
		if self._binary:
			for l in self._listeners:
				l.stop_binary_search()
		if self._selected != None:
			itemId = self.GetPrevItem(self._selected)
			if itemId != -1:
				self._select(itemId)
		log.log("NewEntryRegisterBrowser.gotoNextFiche return", [], 1)

	def gotoNextFiche(self):
		log.log("NewEntryRegisterBrowser.gotoNextFiche", [], 0)
		if self._binary:
			for l in self._listeners:
				l.stop_binary_search()
		if self._selected != None:
			itemId = self.GetNextItem(self._selected)
			if itemId != -1:
				self._select(itemId)
		log.log("NewEntryRegisterBrowser.gotoNextFiche return", [], 1)

	def getNextFiche(self, entry=None):
		log.log("NewEntryRegisterBrowser.getNextFiche", [entry, self.__entry, self._selected, self._item(0), self._item(-1)], 0)
		if self._selected == None: # TODO: C kiedy?
			log.log("NewEntryRegisterBrowser.getNextFiche return", [], 1)
			return
		if (self.__entry == None and entry == "") or (self.__entry != None and (self.__entry == entry or (entry == "" and self._selected != self._item(0) and self._selected != self._item(-1)))):
			#print "nie trzeba"
			RegisterBrowser.getNextFiche(self)
		else:
			itemId = self.GetNextItem(self._selected)
			if itemId != -1:
				ficheId = self._elementOf(itemId)
				self.locate(ficheId)
				#print "znaleziono fiszke"
				log.log("NewEntryRegisterBrowser.getNextFiche return", [], 2)
				return
			else:
				#:if self.__next != None:
				#:	self.locate(ficheId)
				#:else:
				#print "nie bylo nastepnej fiszki"
				self.initialize()
				for l in self._listeners:
					l.on_structure_element_selected("")
		log.log("NewEntryRegisterBrowser.getNextFiche return", [], 3)

	def onUp(self, event):
		log.op("NewEntryRegisterBrowser.onUp", [event, self.__level], 0)
		if self.__level in ["FICHE-ENTRY", "FICHE-GAP"]:
			self.initialize()
		for l in self._listeners:
			l.on_structure_element_selected("")
		log.opr("NewEntryRegisterBrowser.onUp return", [], 1)

	def select(self, elementId):
		log.log("NewEntryRegisterBrowser.select", [elementId, self.__level], 0)
		if self.__level in ["FICHE-ENTRY", "FICHE-GAP"]:
			self.__noLocate = True
			RegisterBrowser.select(self, elementId)
			self.__noLocate = False
		log.log("NewEntryRegisterBrowser.select return", [], 1)

	def _compare(self, a, b): # dla wyszukiwania przyrostowego
		collator = icu.Collator.createInstance(icu.Locale('pl_PL.UTF-8'))
		if isinstance(a, tuple):
			(num, fromm, too) = a
			if fromm != None and collator.compare(ustr(fromm), ustr(b)) >= 0:
				return 1
			elif too != None and collator.compare(ustr(too), ustr(b)) <= 0:
				return -1
			else:
				return 0
		else:
			return collator.compare(ustr(a), ustr(b))
			
	def __compareForIncremental(self, a, b):
		collator = icu.Collator.createInstance(icu.Locale('pl_PL.UTF-8'))
		if isinstance(a, tuple) and isinstance(b, tuple):
			(numa, froma, toa) = a
			(numb, fromb, tob) = b
			if toa != None and fromb != None and collator.compare(ustr(toa), ustr(fromb)) <= 0:
				return -1
			elif tob != None and froma != None and collator.compare(ustr(tob), ustr(froma)) <= 0:
				return 1
			else:
				if not (toa == tob and froma == fromb):
					log.log("NewEntryRegisterBrowser.__compareForIncremental assert", [a, b, self.__elementObjects], 0)
					assert(False)
				return 0
		elif isinstance(a, tuple):
			(num, fromm, too) = a
			if fromm != None and collator.compare(ustr(fromm), ustr(b)) >= 0:
				return 1
			elif too != None and collator.compare(ustr(too), ustr(b)) <= 0:
				return -1
			else:
				log.log("NewEntryRegisterBrowser.__compareForIncremental assert", [a, b, self.__elementObjects], 1)
				assert(False)
		elif isinstance(b, tuple):
			(num, fromm, too) = b
			if fromm != None and collator.compare(ustr(fromm), ustr(a)) >= 0:
				return -1
			elif too != None and collator.compare(ustr(too), ustr(a)) <= 0:
				return 1
			else:
				log.log("NewEntryRegisterBrowser.__compareForIncremental assert", [a, b, self.__elementObjects], 2)
				assert(False)
		else:
			return collator.compare(ustr(a), ustr(b))

	def __findForIncremental(self, element):
		log.log("NewEntryRegisterBrowser.__findForIncremental", [element], 0)
		def __pom(left, right):
			#print left, right, stru(text)
			#print self.__elementObjects[left], self.__elementObjects[right]
			if left == right:
				return left
			elif left + 1 == right:
				if self.__compareForIncremental(self.__elementObjects[right], element) == 0:
					return right
				elif self.__compareForIncremental(self.__elementObjects[left], element) == 0:
					return left
				else:
					log.log("NewEntryRegisterBrowser.__findForIncremental assert", [self.__elementObjects[right], self.__elementObjects[left], left, right, self.__elementObjects], 2)
					assert(False)
			lenn = right - left
			center = left + lenn // 2
			#print center, self.__elementObjects[center]
			if self.__compareForIncremental(self.__elementObjects[center], element) == 0:
				return center
			elif self.__compareForIncremental(self.__elementObjects[center], element) > 0:
				return __pom(left, center - 1)
			else:
				return __pom(center + 1, right)
		res = __pom(0, len(self.__elementObjects) - 1)
		log.log("NewEntryRegisterBrowser.__findForIncremental return", [res], 1)
		return res

	def _findItem(self, text):
		log.log("NewEntryRegisterBrowser._findItem", [text], 0)
		if len(self.__elementObjects) == 0:
			log.log("NewEntryRegisterBrowser._findItem return", [-1], 1)
			return -1
		def __pom(left, right):
			#print left, right, stru(text)
			#print self.__elementObjects[left], self.__elementObjects[right]
			if left == right:
				return left
			elif left + 1 == right:
				if self._compare(self.__elementObjects[right], text) <= 0:
					return right
				else:
					return left
			lenn = right - left
			center = left + lenn // 2
			#print center, self.__elementObjects[center]
			if self._compare(self.__elementObjects[center], text) == 0:
				return center
			elif self._compare(self.__elementObjects[center], text) > 0:
				return __pom(left, center - 1)
			else:
				return __pom(center + 1, right)
		res = __pom(0, len(self.__elementObjects) - 1)
		log.log("NewEntryRegisterBrowser._findItem return", [res], 2)
		return res

	def find(self, text):
		log.log("NewEntryRegisterBrowser.find", [text], 0)
		if self.__level in ["FICHE-ENTRY", "FICHE-GAP"]:
			RegisterBrowser.find(self, text)
		else:
			#print "szukamy"
			itemId = self._findItem(text)
			#print "mamy", itemId
			#assert(itemId != -1)
			if itemId != -1:
				#print "czyli", self._elementOf(itemId)
				#print self._elements
				if self._selected != None:
					self._unselect(self._selected)
				print "select:", itemId
				self._select(itemId)
		log.log("NewEntryRegisterBrowser.find return", [], 1)

	def gapSelected(self):
		log.log("NewEntryRegisterBrowser.gapSelected", [], 0)
		log.log("NewEntryRegisterBrowser.gapSelected return", [isinstance(self.__selectedElement, tuple)], 1)
		return isinstance(self.__selectedElement, tuple)

	def wrongOrder(self, entry):
		log.log("NewEntryRegisterBrowser.wrongOrder", [entry], 0)
		if self.__selectedElement != None and isinstance(self.__selectedElement, tuple):
			if self.__selectedElement[2] != None and self.__collator.compare(ustr(self.__selectedElement[2]), ustr(entry)) < 0:
				log.log("NewEntryRegisterBrowser.wrongOrder return", [(True, False)], 1)
				return (True, False)
			elif self.__selectedElement[1] != None and self.__collator.compare(ustr(self.__selectedElement[1]), ustr(entry)) > 0:
				log.log("NewEntryRegisterBrowser.wrongOrder return", [(False, True)], 2)
				return (False, True)
			else:
				log.log("NewEntryRegisterBrowser.wrongOrder return", [(False, False)], 3)
				return (False, False)
		else:
			log.log("NewEntryRegisterBrowser.wrongOrder return", [(False, False)], 4)
			return (False, False)

	def selectElementContaining(self, ficheId):
		log.log("NewEntryRegisterBrowser.selectElementContaining", [ficheId], 0)
		for i in range(0, self._itemsLen()):
			el = self._elementOf(i)
			has = self.__dBController.hasFiche(el, self.__centerFiche)
			if has:
				self.__selectedElement = el
				for l in self._listeners:
					l.on_structure_element_selected(self.__text(el))
				break
		self._scrollBrowser(self._itemOf(self.__selectedElement))
		self.__binarySelect(self._itemOf(self.__selectedElement))
		log.log("NewEntryRegisterBrowser.selectElementContaining return", [self.__selectedElement], 1)


	# --- WYSZUKIWANIE BINARNE --- #

	def binaryAvailable(self):
		return self.__level == "ENTRY"
	
	def __determineAutomaticSearchScope(self):#, right):
		log.log("NewEntryRegisterBrowser.__determineAutomaticSearchScope", [], 0)
		for i in range(0, self._itemsLen()):
			elem = self._elementOf(i)
			#print elem
			if elem != None and isinstance(elem, tuple):
				#print elem, self.__binaryTarget
				#print unicode(nvl(elem[1]), "utf-8"), elem[2], "None" if elem[2] == None else unicode(elem[2], "utf-8")
				#print self.__collator.compare(unicode(nvl(elem[1]), "utf-8"), self.__binaryTarget)
				#if elem[2] != None:
				#	print self.__collator.compare(unicode(elem[2], "utf-8"), self.__binaryTarget)
				#else:
				#	print "none"
				#print self.__binaryTarget
				#print "---"
				#:if right:
				#:	if self.__collator.compare(unicode(nvl(elem[1]), "utf-8"), self.__binaryTarget) == 0:
				#:		return elem
				#:else:
				#:	if (self.__collator.compare(unicode(nvl(elem[1]), "utf-8"), self.__binaryTarget) < 0 and (elem[2] == None or self.__collator.compare(unicode(elem[2], "utf-8"), self.__binaryTarget) > 0)) or unicode(nvl(elem[2]), "utf-8") == self.__binaryTarget:
				if (elem[1] == None or self.__collator.compare(unicode(elem[1], "utf-8"), self.__binaryTarget) < 0) and (elem[2] == None or self.__collator.compare(unicode(elem[2], "utf-8"), self.__binaryTarget) >= 0):
					#print elem, self.__binaryTarget, ":::"
					log.log("NewEntryRegisterBrowser.__determineAutomaticSearchScope return", [(elem, False)], 1)
					return (elem, False)
				if (elem[1] != None and self.__collator.compare(unicode(elem[1], "utf-8"), self.__binaryTarget) == 0) and (elem[2] == None or self.__collator.compare(unicode(elem[2], "utf-8"), self.__binaryTarget) > 0):
					#print elem, self.__binaryTarget
					log.log("NewEntryRegisterBrowser.__determineAutomaticSearchScope return", [(elem, True)], 2)
					return (elem, True)
		log.log("NewEntryRegisterBrowser.__determineAutomaticSearchScope return", [(None, None)], 3)
		return (None, None)

	def startBinarySearch(self, target=None, restarting=False):
		log.log("NewEntryRegisterBrowser.startBinarySearch", [target, restarting, self.__selectedElement, self.__binaryType], 0)
		self.__binaryScopeValid = True
		self.__binaryTarget = target
		self._binary = True
		#assert(self.__binaryTarget != None)
		#print "tu"
		#print self.__binaryTarget, restarting
		if self.__binaryTarget != None:
			if restarting:
				#print "restarting"
				self.__steps += 1
				for l in self._listeners:
					l.on_structure_element_selected(self.__text(self.__selectedElement))
					l.next_step(self.__steps)
					self._scrollBrowser(self._itemOf(self.__selectedElement))
					self.__binarySelect(self._itemOf(self.__selectedElement))
			else:
				self.__steps = 0
				(elem, right) = self.__determineAutomaticSearchScope()
				if elem == None or (not isinstance(elem, tuple)):
					#print "ojej!"
					self._binary = False
					self.__binaryTarget = None
					log.log("NewEntryRegisterBrowser.startBinarySearch return", [], 1)
					return
				else:
					self.__selectedElement = elem
					self.__leftTargetBinary = not right
					#self.__firstIndexedFicheEntry = None
					for l in self._listeners:
						l.on_structure_element_selected(self.__text(self.__selectedElement))
						#self._scrollBrowser(self._itemOf(self.__selectedElement))
						self.__binarySelect(self._itemOf(self.__selectedElement))
		else:
			self.__steps = 0
		#print right, self.__leftTargetBinary			
		#print self.__selectedElement, self.__binaryTarget
		assert(self.__selectedElement != None)
		if isinstance(self.__selectedElement, tuple):
			(self.__leftFiche, self.__rightFiche, length) = self.__dBController.getGapCount(self.__selectedElement[1], self.__selectedElement[2])
			self.__binaryType = "GAP"
		else:
			(self.__leftFiche, self.__rightFiche, length) = self.__dBController.getEntriesCount(self.__selectedElement)
			self.__binaryType = "ENTRY"
		self.__left = 0
		self.__right = length - 1
		self.__selectCenter()
		log.log("NewEntryRegisterBrowser.startBinarySearch return", [], 2)

	def getSteps(self):
		return self.__steps

	def restartable(self, binaryTarget):
		log.log("NewEntryRegisterBrowser.startBinarySearch", [binaryTarget], 0)
		#print binaryTarget
		self.__binaryTarget = binaryTarget
		(elem, right) = self.__determineAutomaticSearchScope()
		#print elem, right
		if elem != None:
			#print elem, self.__binaryTarget
			#assert(false)
			self.__leftTargetBinary = not right
			self.__selectedElement = elem
			log.log("NewEntryRegisterBrowser.restartable return", [True], 1)
			return True
		self.__binaryTarget = None
		self.__leftTargetBinary = False
		log.log("NewEntryRegisterBrowser.restartable return", [False], 2)
		return False

	def getTarget(self):
		return self.__binaryTarget

	def stopBinarySearch(self):
		log.log("NewEntryRegisterBrowser.stopBinarySearch", [self.__selectedElement, self.__binaryType], 0)
		self._binary = False
		#print "@", restart
		#print "restartujemy?"
		#print restart, self.__binaryTarget, self.__leftTargetBinary
		#if restart and self.__binaryTarget != None and self.__firstIndexedFicheEntry == self.__binaryTarget and self.__leftTargetBinary:
		#:if restart and self.__binaryTarget != None and self.__leftTargetBinary:
			#print "in"
			#print "restartujemy!"
			#:itemId = self.FindItem(-1, self.__binaryTarget, partial=True)
			#:assert(itemId) != -1 # TODO: NOTE niekoniecznie (bo binaryTarget mogl byc rozny od pierwszego zaindeksowanego hasla)
			#:elem = self._item2element.get(itemId + 1)
			#:if elem != None and isinstance(elem, tuple) and unicode(nvl(elem[1]), "utf-8") == self.__binaryTarget:
			#:	#print "o!", elem
			#:	self.__selectedElement = elem
			#:	return self.__binaryTarget
			#:else:
			#:	#print "els"
			#:	for i in self._items:
			#:		elem = self._item2element.get(i)
			#:		#print elem, unicode(nvl(elem[1]), "utf-8"), self.__binaryTarget
			#:		if elem != None and isinstance(elem, tuple) and unicode(nvl(elem[1]), "utf-8") == self.__binaryTarget:
			#:			self.__selectedElement = elem
			#:			return self.__binaryTarget
		#print "ojej, stalo sie cos dziwnego"
		self.__binaryTarget = None
		self.__leftBinaryTarget = False
		log.log("NewEntryRegisterBrowser.stopBinarySearch return", [None], 1)
		return None

	def nextBinaryAcceptPrepare(self, automatic=False):
		log.log("NewEntryRegisterBrowser.nextBinaryAcceptPrepare", [automatic, self.__selectedElement, self.__binaryType], 0)
		#print "!", self.__left, self.__center, self.__right
		#
		#print "::", self.__left, self.__right
		if self.__center == self.__right and self.__left == self.__center - 1:
			log.log("NewEntryRegisterBrowser.nextBinaryAcceptPrepare return", [False], 1)
			return False
		if self.__left == self.__right:
			if not automatic:
				for l in self._listeners:
					l.stop_binary_search()
			log.log("NewEntryRegisterBrowser.nextBinaryAcceptPrepare return", [False], 2)
			return False
		#
		self.__left = self.__center + 1
		if self.__left > self.__right:
			self.__left = self.__right
		if not self.__binaryScopeValid: # TODO: A po co?
			self.__binaryScopeValid = True
			self.__leftFiche = self.__potentialNextLeftFiche
			if self.__left == self.__right:
				log.log("NewEntryRegisterBrowser.nextBinaryAcceptPrepare return", [False], 3)
				return False
			self.__center = self.__potentialNextCenter
			self.__centerFiche = self.__potentialNextCenterFiche
			log.log("NewEntryRegisterBrowser.nextBinaryAcceptPrepare return", [True], 4)
			return True
		if self.__binaryType == "GAP":
			self.__leftFiche = self.__dBController.getFicheForGapPosition(self.__selectedElement[1], self.__selectedElement[2], self.__left)
		else:
			self.__leftFiche = self.__dBController.getFicheForEntryPosition(self.__selectedElement, self.__left)
		res = self.__selectCenterPrepare()
		log.log("NewEntryRegisterBrowser.nextBinaryAcceptPrepare return", [res], 5)
		return res

	def prevBinaryAcceptPrepare(self, automatic=False):
		log.log("NewEntryRegisterBrowser.prevBinaryAcceptPrepare", [automatic, self.__selectedElement, self.__binaryType], 0)
		#print "!", self.__left, self.__center, self.__right
		#
		#print ":", self.__left, self.__right
		if self.__left == self.__right:
			if not automatic:
				for l in self._listeners:
					l.stop_binary_search()
			log.log("NewEntryRegisterBrowser.prevBinaryAcceptPrepare return", [False], 1)
			return False
		#
		self.__right = self.__center - 1
		if self.__right < self.__left:
			self.__right = self.__left
		if not self.__binaryScopeValid: # TODO: A po co?
			self.__binaryScopeValid = True
			self.__rightFiche = self.__potentialPrevRightFiche
			if self.__right == self.__left:
				log.log("NewEntryRegisterBrowser.prevBinaryAcceptPrepare return", [False], 2)
				return False
			self.__center = self.__potentialPrevCenter
			self.__centerFiche = self.__potentialPrevCenterFiche
			log.log("NewEntryRegisterBrowser.prevBinaryAcceptPrepare return", [True], 3)
			return True
		if self.__binaryType == "GAP":
			self.__rightFiche = self.__dBController.getFicheForGapPosition(self.__selectedElement[1], self.__selectedElement[2], self.__right)
		else:
			self.__rightFiche = self.__dBController.getFicheForEntryPosition(self.__selectedElement, self.__right)
		res = self.__selectCenterPrepare()
		log.log("NewEntryRegisterBrowser.prevBinaryAcceptPrepare return", [res], 4)
		return res

	def initializeForActiveBinary(self, entry):
		log.log("NewEntryRegisterBrowser.initializeForActiveBinary", [entry, self.__selectedElement, self.__binaryType], 0)
		self._selected = None
		if not self._incrementalUpdate([self.__entryOf(self.__selectedElement), entry]):
			self.DeleteAllItems()
			(elements, self.__entryLens) = self.__dBController.getEntriesRegisterWithGaps()
			self.__fillRegister(elements)
		else:
			self._showUpdate()
		log.log("NewEntryRegisterBrowser.initializeForActiveBinary return", [], 1)

	def prepareForActiveBinary(self):
		log.log("NewEntryRegisterBrowser.prepareForActiveBinary", [self.__selectedElement, self.__binaryType, self.__left, self.__center, self.__right], 0)
		#print self.__left, self.__center, self.__right
		potentialPrevLeft = self.__left
		potentialPrevRight = self.__center - 1
		if potentialPrevRight < potentialPrevLeft:
			potentialPrevRight = potentialPrevLeft
		lenn = potentialPrevRight - potentialPrevLeft + 1
		#if potentialPrevRight == potentialPrevLeft:
		#	return
		#print self.__left, self.__center, self.__right
		self.__potentialPrevCenter = potentialPrevLeft + lenn / 2
		log.log("NewEntryRegisterBrowser.prepareForActiveBinary assert", [self.__potentialPrevCenter], 3)
		assert(self.__potentialPrevCenter >= 0)
		#print potentialPrevLeft, self.__potentialPrevCenter, potentialPrevRight
		potentialNextLeft = self.__center + 1
		potentialNextRight = self.__right
		if potentialNextLeft > potentialNextRight:
			potentialNextLeft = potentialNextRight
		lenn = potentialNextRight - potentialNextLeft + 1
		#if potentialNextRight == potentialNextLeft:
		#	return
		self.__potentialNextCenter = potentialNextLeft + lenn / 2
		self.__potentialPrevLeftFiche = self.__leftFiche
		#print self.__selectedElement, potentialPrevRight, self.__potentialPrevCenter, potentialPrevLeft
		#print potentialNextRight, self.__potentialNextCenter, potentialNextLeft
		self.__left, self.__center, self.__right
		if self.__binaryType == "GAP":
			self.__potentialPrevCenterFiche = self.__dBController.getFicheForGapPosition(self.__selectedElement[1], self.__selectedElement[2], self.__potentialPrevCenter)
			self.__potentialPrevRightFiche = self.__dBController.getFicheForGapPosition(self.__selectedElement[1], self.__selectedElement[2], potentialPrevRight)
			self.__potentialNextLeftFiche = self.__dBController.getFicheForGapPosition(self.__selectedElement[1], self.__selectedElement[2], potentialNextLeft)
			self.__potentialNextCenterFiche = self.__dBController.getFicheForGapPosition(self.__selectedElement[1], self.__selectedElement[2], self.__potentialNextCenter)
			#print self.__potentialPrevLeftFiche, self.__potentialPrevCenterFiche, self.__potentialPrevRightFiche
		else:
			self.__potentialPrevCenterFiche = self.__dBController.getFicheForEntryPosition(self.__selectedElement, self.__potentialPrevCenter)
			self.__potentialPrevRightFiche = self.__dBController.getFicheForEntryPosition(self.__selectedElement, potentialPrevRight)
			self.__potentialNextLeftFiche = self.__dBController.getFicheForEntryPosition(self.__selectedElement, potentialNextLeft)
			self.__potentialNextCenterFiche = self.__dBController.getFicheForEntryPosition(self.__selectedElement, self.__potentialNextCenter)
		self.__potentialNextRightFiche = self.__rightFiche
		#log.log(["element początkowy:", self.__selectedElement])
		#log.log(["zakres początkowy:", self.__left, self.__center, self.__right])
		#log.log(["fiszki początkowe:", self.__leftFiche, self.__centerFiche, self.__rightFiche])
		#log.log(["obliczony zakres potencjalny w lewo:", potentialPrevLeft, self.__potentialPrevCenter, potentialPrevRight])
		#log.log(["obliczone fiszki potencjalne w lewo:", self.__potentialPrevLeftFiche, self.__potentialPrevCenterFiche, self.__potentialPrevRightFiche])
		#log.log(["obliczony zakres potencjalny w prawo:", potentialNextLeft, self.__potentialNextCenter, potentialNextRight])
		#log.log(["obliczone fiszki potencjalne w prawo:", self.__potentialNextLeftFiche, self.__potentialNextCenterFiche, self.__potentialNextRightFiche])
		log.log("NewEntryRegisterBrowser.prepareForActiveBinary assert", [self.__potentialNextCenterFiche, self.__potentialPrevCenterFiche], 2)
		assert(self.__potentialNextCenterFiche != None and self.__potentialPrevCenterFiche != None)
		self.__binaryScopeValid = False
		log.log("NewEntryRegisterBrowser.prepareForActiveBinary return", [], 1)

	def __entryOf(self, el):
		if isinstance(el, tuple):
			if el[1] != None:
				return el[1]
			else:
				return el[2]
		else:
			return el

	def binaryAcceptFinalize(self, entry, safe=False):
		#gc = Counter()
		log.log("NewEntryRegisterBrowser.binaryAcceptFinalize", [entry, safe, self.__selectedElement, self.__binaryType], 0)
		self._selected = None
		#c = Counter()
		if not self._incrementalUpdate([self.__entryOf(self.__selectedElement), entry]):
			self.DeleteAllItems()
			#print "DeleteAllItems", c
			(elements, self.__entryLens) = self.__dBController.getEntriesRegisterWithGaps()
			#print "getEntriesRegisterWithGaps", c
			self.__fillRegister(elements) # wpp zajmuje sie tym showupdate
		#print "init", c#, self._smart
		#print "!!!", self.__left, self.__center, self.__right
		#print "@@@", self.__leftFiche, self.__centerFiche, self.__rightFiche
		#print "fillRegister", c
		self.__left = None		
		#lc = Counter()
		#::for (i, el) in self._item2element.iteritems():
		#print self._itemsLen(), len(self._elements)
		for i in range(0, self._itemsLen()):
			el = self._elementOf(i)
			#print "$$$", el, self.__centerFiche, self.__dBController.hasFiche(el, self.__centerFiche)
			#print el
			#c.reset()
			has = self.__dBController.hasFiche(el, self.__centerFiche)
			#print "hasFiche", c
			#print has
			if has:#self.__dBController.hasFiche(el, self.__centerFiche):
				#print "has"
				self.__selectedElement = el
				for l in self._listeners:
					l.on_structure_element_selected(self.__text(el))
				if isinstance(el, tuple):
					#print "tuple"
					self.__binaryType = "GAP"
					#c.reset()
					(self.__left, self.__right, self.__center) = self.__dBController.getPositionsForFichesForGap(el[1], el[2], self.__leftFiche, self.__rightFiche, self.__centerFiche)
					#print "getPositionsForFichesForGap", c
				else:
					#print "entry"
					self.__binaryType = "ENTRY"
					#c.reset
					(self.__left, self.__right, self.__center) = self.__dBController.getPositionsForFichesForEntry(el, self.__leftFiche, self.__rightFiche, self.__centerFiche)
					#print "getPositionsForFichesForEntry", c
				#print self.__left, self.__center, self.__right
				break
			else:
				pass
				#print "not has"
		#print self.__selectedElement, self._elements
		#print "loop", c
		self._scrollBrowser(self._itemOf(self.__selectedElement))
		#print "scrollBrowser", c
		self.__binarySelect(self._itemOf(self.__selectedElement))
		#print "binarySelect", c
		# TODO: C konczenie wyszukiwania z celem gdy wyladowalismy nie w GAP tylko w ENTRY
		#print ":::::", self.__centerFiche
		#print self.__leftFiche, self.__rightFiche, self.__left, self.__right, self.__center
		log.log("NewEntryRegisterBrowser.binaryAcceptFinalize assert", [self.__leftFiche, self.__rightFiche, self.__centerFiche, self._elements], 1)
		assert(self.__left != None)
		#c.reset()
		self.__steps += 1
		for l in self._listeners:
			l.invisible_binary_search(self.__centerFiche)
			#print "invisible_binary_search", c
			l.next_step(self.__steps)
		if safe and self.__left == self.__right:
			for l in self._listeners:
				l.stop_binary_search()
		#print "stop_binary_search2", c
		#print "global", gc
		log.log("NewEntryRegisterBrowser.binaryAcceptFinalize return", [], 2)
		
	def nextBinary(self):
		log.log("NewEntryRegisterBrowser.nextBinary", [self.__selectedElement, self.__binaryType], 0)
		# TODO: NOTE niepotrzebne? (bo w selectCenter)
		#if self.__left == self.__right:
		#	for l in self._listeners:
		#		l.stop_binary_search()
		#
		self.__left = self.__center + 1
		if self.__left > self.__right:
			self.__left = self.__right
		self.__steps += 1
		for l in self._listeners:
			l.next_step(self.__steps)
		if not self.__binaryScopeValid:
			self.__binaryScopeValid = True
			self.__leftFiche = self.__potentialNextLeftFiche
			#if self.__left == self.__right:
			#	for l in self._listeners:
			#		l.stop_binary_search()
			#	return
			self.__center = self.__potentialNextCenter
			self.__centerFiche = self.__potentialNextCenterFiche
			self.__selectedElement = None
			log.log("NewEntryRegisterBrowser.nextBinary inspect", [self.__centerFiche, self._elements], 1)
			#::for (i, el) in self._item2element.iteritems():
			for i in range(0, self._itemsLen()):
				el = self._elementOf(i)
				#log.log(["w", el, ":", self.__dBController.hasFiche(el, self.__centerFiche)])
				if self.__dBController.hasFiche(el, self.__centerFiche):
					self.__selectedElement = el
					if isinstance(self.__selectedElement, tuple):
						self.__binaryType = "GAP"
						(self.__left, self.__right, self.__center) = self.__dBController.getPositionsForFichesForGap(el[1], el[2], self.__leftFiche, self.__rightFiche, self.__centerFiche)
					else:
						self.__binaryType = "ENTRY"
						(self.__left, self.__right, self.__center) = self.__dBController.getPositionsForFichesForEntry(el, self.__leftFiche, self.__rightFiche, self.__centerFiche)
					break
			#print self.__left, self.__center, self.__right
			#print self.__leftFiche, self.__centerFiche, self.__rightFiche
			assert(self.__selectedElement != None)
			self._scrollBrowser(self._itemOf(self.__selectedElement))
			self.__binarySelect(self._itemOf(self.__selectedElement))
			for l in self._listeners:
				l.on_structure_element_selected(self.__text(self.__selectedElement))
				l.invisible_binary_search(self.__centerFiche)
			if self.__left == self.__right:
				for l in self._listeners:
					l.stop_binary_search()
					log.log("NewEntryRegisterBrowser.nextBinary return", [], 2)
			return
		if self.__binaryType == "GAP":
			self.__leftFiche = self.__dBController.getFicheForGapPosition(self.__selectedElement[1], self.__selectedElement[2], self.__left)
		else:
			self.__leftFiche = self.__dBController.getFicheForEntryPosition(self.__selectedElement, self.__left)
		self.__selectCenter()
		log.log("NewEntryRegisterBrowser.nextBinary return", [], 3)

	def prevBinary(self):
		log.log("NewEntryRegisterBrowser.prevBinary", [self.__selectedElement, self.__binaryType], 0)
		#print self.__right, self.__center, self.__left
		#print self.__rightFiche, self.__centerFiche, self.__leftFiche
		# TODO: NOTE niepotrzebne? (bo w selectCenter)
		#if self.__left == self.__right:
		#	for l in self._listeners:
		#		l.stop_binary_search()
		#
		self.__right = self.__center - 1
		if self.__right < self.__left:
			self.__right = self.__left
		self.__steps += 1
		for l in self._listeners:
			l.next_step(self.__steps)	
		if not self.__binaryScopeValid:
			self.__binaryScopeValid = True
			self.__rightFiche = self.__potentialPrevRightFiche
			#if self.__left == self.__right:
			#	for l in self._listeners:
			#		l.stop_binary_search()
			#	return
			self.__center = self.__potentialPrevCenter
			self.__centerFiche = self.__potentialPrevCenterFiche
			self.__selectedElement = None
			#print "szukamy " + self.__centerFiche
			log.log("NewEntryRegisterBrowser.prevBinary inspect", [self.__centerFiche, self._elements], 1)
			#::for (i, el) in self._item2element.iteritems():
			for i in range(0, self._itemsLen()):
				el = self._elementOf(i)
				#print self.__centerFiche, el, self.__dBController.hasFiche(el, self.__centerFiche)
				#log.log(["w", el, ":", self.__dBController.hasFiche(el, self.__centerFiche)])
				if self.__dBController.hasFiche(el, self.__centerFiche):
					self.__selectedElement = el
					if isinstance(self.__selectedElement, tuple):
						self.__binaryType = "GAP"
						(self.__left, self.__right, self.__center) = self.__dBController.getPositionsForFichesForGap(el[1], el[2], self.__leftFiche, self.__rightFiche, self.__centerFiche)
					else:
						self.__binaryType = "ENTRY"
						(self.__left, self.__right, self.__center) = self.__dBController.getPositionsForFichesForEntry(el, self.__leftFiche, self.__rightFiche, self.__centerFiche)
					break
			#print self.__left, self.__center, self.__right
			#print self.__leftFiche, self.__centerFiche, self.__rightFiche
			assert(self.__selectedElement != None)
			self._scrollBrowser(self._itemOf(self.__selectedElement))
			self.__binarySelect(self._itemOf(self.__selectedElement))
			for l in self._listeners:
				l.on_structure_element_selected(self.__text(self.__selectedElement))
				l.invisible_binary_search(self.__centerFiche)
			if self.__left == self.__right:
				for l in self._listeners:
					l.stop_binary_search()
			log.log("NewEntryRegisterBrowser.prevBinary return", [], 2)
			return
		if self.__binaryType == "GAP":
			#print self.__selectedElement
			self.__rightFiche = self.__dBController.getFicheForGapPosition(self.__selectedElement[1], self.__selectedElement[2], self.__right)
		else:
			self.__rightFiche = self.__dBController.getFicheForEntryPosition(self.__selectedElement, self.__right)
		#print self.__rightFiche, self.__right
		log.log("NewEntryRegisterBrowser.prevBinary return", [], 3)
		self.__selectCenter()
		
	def __selectCenterPrepare(self):
		#print "select center fired"
		log.log("NewEntryRegisterBrowser.__selectCenterPrepare", [self.__left, self.__right], 0)
		lenn = self.__right - self.__left + 1
		self.__center = self.__left
		self.__center += lenn // 2
		if self.__binaryType == "GAP":
			self.__centerFiche = self.__dBController.getFicheForGapPosition(self.__selectedElement[1], self.__selectedElement[2], self.__center)
		else:
			self.__centerFiche = self.__dBController.getFicheForEntryPosition(self.__selectedElement, self.__center)
		#if self.__left == self.__right:
		#	#print "ojej!"
		#	return False
		#if self.__left == self.__right == self.__center:
		#	return False
		log.log("NewEntryRegisterBrowser.__selectCenterPrepare return", [True], 1)
		return True
			
	def __selectCenter(self):
		log.log("NewEntryRegisterBrowser.__selectCenter", [self.__left, self.__right], 0)
		lenn = self.__right - self.__left + 1
		#:if self.__left == self.__right:# == self.__center:
		#:	#for l in self._listeners:
		#:	#	l.on_structure_element_selected("")
		#:	for l in self._listeners:
		#:		l.stop_binary_search()
		#:	return
		self.__center = self.__left
		self.__center += lenn // 2
		#print self.__binaryType, self.__center
		#print ":::", self.__selectedElement, self.__center
		if self.__binaryType == "GAP":
			self.__centerFiche = self.__dBController.getFicheForGapPosition(self.__selectedElement[1], self.__selectedElement[2], self.__center)
		else:
			self.__centerFiche = self.__dBController.getFicheForEntryPosition(self.__selectedElement, self.__center)
		#if self.__centerFiche == None:
		#	print self.__selectedElement
		#	print self.__left, self.__center, self.__right
		#	print self.__leftFiche, self.__centerFiche, self.__rightFiche
		#	print self._elements
		log.log("NewEntryRegisterBrowser.__selectCenter assert", [self.__centerFiche, self.__center, self.__selectedElement], 2)
		assert(self.__centerFiche != None)
		for l in self._listeners:
			l.invisible_binary_search(self.__centerFiche)
		#print self.__left, self.__center, self.__right
		#print self.__leftFiche, self.__centerFiche, self.__rightFiche
		if self.__left == self.__right and self.__binaryTarget == None:# == self.__center:
		#	#for l in self._listeners:
		#	#	l.on_structure_element_selected("")
			for l in self._listeners:
				l.stop_binary_search()
		log.log("NewEntryRegisterBrowser.__selectCenter return", [], 1)

	def topLevel(self):
		return self.__level == "ENTRY"

	def allowsNextFiche(self):
		return self.__level in ["FICHE-ENTRY", "FICHE-GAP"]

	def showFirstElement(self):
		log.log("NewEntryRegisterBrowser.showFirstElement", [self.__level], 0)
		if self.__level == "ENTRY":
			log.log("NewEntryRegisterBrowser.showFirstElement return", [], 1)
			return
		if self.__level == "FICHE-GAP":
			(elements, self.__index, self.__next) = self.__dBController.getFichesForGap(self.__selectedElement[1], self.__selectedElement[2], self.__limit, 0, self._itemsLen())
		else:
			(elements, self.__index, self.__next) = self.__dBController.getFichesForEntry(self.__selectedElement, self.__limit, 0, self._itemsLen())
		self.DeleteAllItems()
		self.__fillRegister(elements)
		self.__localVeto = True
		self.__noLocate = True
		self._select(0)
		self.__noLocate = False
		self.__localVeto = False
		log.log("NewEntryRegisterBrowser.showFirstElement return", [], 2)

	def showLastElement(self):
		log.log("NewEntryRegisterBrowser.showLastElement", [self.__level], 0)
		if self.__level == "ENTRY":
			log.log("NewEntryRegisterBrowser.showLastElement return", [], 1)
			return
		if self.__level == "FICHE-GAP":
			(elements, self.__index, self.__next, element) = self.__dBController.getFichesForGapForLastFiche(self.__selectedElement[1], self.__selectedElement[2], self.__limit)
		else:
			(elements, self.__index, self.__next, element) = self.__dBController.getFichesForEntryForLastFiche(self.__selectedElement, self.__limit)
		self.DeleteAllItems()
		#print elements
		self.__fillRegister(elements)
		itemId = self._itemOf(element)
		self.__localVeto = True
		self.__noLocate = True
		self._select(itemId)
		self.__noLocate = False
		self.__localVeto = False
		log.log("NewEntryRegisterBrowser.showLastElement return", [], 2)

	def hasTarget(self):
		log.log("NewEntryRegisterBrowser.hasTarget", [], 0)
		log.log("NewEntryRegisterBrowser.hasTarget return", [self.__binaryTarget != None], 1)
		return self.__binaryTarget != None

	def determineNextTarget(self, entry):
		# TODO: C co jak jestesmy w niewlasciwym elemencie (nie jestesmy w dziurze z tym celem)?		
		#print entry, self.__binaryTarget, self.__leftTargetBinary
		log.log("NewEntryRegisterBrowser.determineNextTarget", [entry], 0)
		if self.__leftTargetBinary:
			if self.__collator.compare(entry, self.__binaryTarget) >= 0:
				#print "left"
				log.log("NewEntryRegisterBrowser.determineNextTarget return", ["LEFT"], 1)
				return "LEFT"
			else: # TODO: C obsluga fiszek nie po kolei
				#print "right"
				log.log("NewEntryRegisterBrowser.determineNextTarget return", ["RIGHT"], 2)
				return "RIGHT"
		else:
			if self.__collator.compare(entry, self.__binaryTarget) <= 0:
				#print "right2"
				log.log("NewEntryRegisterBrowser.determineNextTarget return", ["RIGHT"], 3)
				return "RIGHT"
			else: # TODO: C j.w.
				#print "left2"
				log.log("NewEntryRegisterBrowser.determineNextTarget return", ["LEFT"], 4)
				return "LEFT"

