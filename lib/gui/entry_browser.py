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

from maleks.gui.reg_browser import RegisterBrowser
from maleks.maleks import log
import time
import wx

class EntryRegisterBrowser(RegisterBrowser):

	def __init__(self, *args, **kwargs):
		RegisterBrowser.__init__(self, *args, **kwargs)
		self.__dBController = None

	def reset(self):
		log.log("EntryRegisterBrowser.reset", [], 0)
		RegisterBrowser.reset(self)
		self.__level = "ENTRY"
		self.__stack = []
		self.__selectedElement = None
		log.log("EntryRegisterBrowser.reset return", [], 1)

	def setDBController(self, controller):
		self.__dBController = controller
		
	def onSelect(self, event):
		log.op("EntryRegisterBrowser.onSelect", [self._elementOf(self._unmap(event.GetIndex()))], 0)
		RegisterBrowser.onSelect(self, event)
		log.opr("EntryRegisterBrowser.onSelect return", [], 1)

	def initialize(self):
		log.log("EntryRegisterBrowser.initialize", [], 0)
		if self.binarySearchActive():
			for l in self._listeners:
				l.stop_binary_search()
		self.reset()
		elements = self.__dBController.getEntriesRegister()
		#print elements
		#elements = ["a", "b", "c", "d"]
		self.__fillRegister(elements)
		self._initialized = True
		log.log("EntryRegisterBrowser.initialize return", [], 1)

	def __fillRegister(self, elements):
		log.log("EntryRegisterBrowser.initialize", [elements], 0)
		i = 0
		for element in elements:
			self.InsertStringItem(i, element)
			self.SetStringItem(i, 1, "")
			self.SetStringItem(i, 2, "")
			self._items.append(i)
			self._item2element.setdefault(i, element)
			self._element2item.setdefault(element, i)
			i += 1
		self.SetColumnWidth(0, wx.LIST_AUTOSIZE)
		log.log("EntryRegisterBrowser.initialize return", [], 1)

	def select(self, elementId):
		log.log("EntryRegisterBrowser.select", [elementId, self.__level], 0)
		if self.__level == "FICHE":
			RegisterBrowser.select(self, elementId)
		log.log("EntryRegisterBrowser.select return", [], 1)	

	def _element_selected(self, elementId, notify=True):
		log.log("EntryRegisterBrowser._element_selected", [elementId, notify, self.__level], 0)
		if self.__level == "FICHE":
			RegisterBrowser._element_selected(self, elementId, notify=notify)
		else:
			self.__selectedElement = elementId
		log.log("EntryRegisterBrowser._element_selected return", [], 1)

	def levelDown(self):
		log.op("EntryRegisterBrowser.levelDown", [self.__selectedElement, self.__level], 0)
		elementId = self.__selectedElement
		#elif self.__level == "ENTRY":
		if self.__level == "ENTRY":	
			elements = self.__dBController.getWorksForEntry(elementId)	
			self.__stack.append(elementId)
			self.__level = "WORK"
			self.DeleteAllItems()
			self.__fillRegister(elements)
		elif self.__level == "WORK":	
			#print elementId
			elements = self.__dBController.getPagesForWork(self.__stack[-1], elementId)
			#elements = ["0", "1", "2", "3", "4"]
			self.__stack.append(elementId)
			self.__level = "PAGE"
			self.DeleteAllItems()
			self.__fillRegister(elements)
		elif self.__level == "PAGE":
			elements = self.__dBController.getLinesForPage(self.__stack[-2], self.__stack[-1], elementId)
			#elements = ["4", "5", "6", "7"]
			self.__stack.append(elementId)
			self.__level = "LINE"
			self.DeleteAllItems()
			self.__fillRegister(elements)
		else:
			elements = self.__dBController.getFichesForLine(self.__stack[-3], self.__stack[-2], self.__stack[-1], elementId)
			self.__level = "FICHE"
			self.DeleteAllItems()
			self.__fillRegister(elements)
			for l in self._listeners: # TODO: D jeden listener
				elementId = l.request_selection()
				if elementId != None:
					self.select(elementId)
			time.sleep(0.1) # TODO: NOTE bez tego nie zaznacza w wykazie aktualnie ogladanej fiszki
		log.opr("EntryRegisterBrowser.levelDown return", [], 1)

	def onUp(self, event):
		#pass
		#print "up", self.__stack, self.__level
		log.op("EntryRegisterBrowser.levelDown", [self.__selectedElement, self.__level], 0)
		if self.__stack == []:
			return
		if self.__level == "FICHE":
			elements = self.__dBController.getLinesForPage(self.__stack[-3], self.__stack[-2], self.__stack[-1])
			#elements = ["4", "5", "6", "7"]
			self.__level = "LINE"
			self.DeleteAllItems()
			self.__fillRegister(elements)
		elif self.__level == "LINE":
			self.__stack.pop()
			elements = self.__dBController.getPagesForWork(self.__stack[-2], self.__stack[-1])
			#elements = ["0", "1", "2", "3", "4"]
			self.__level = "PAGE"
			self.DeleteAllItems()
			self.__fillRegister(elements)
		elif self.__level == "PAGE":
			self.__stack.pop()
			elements = self.__dBController.getWorksForEntry(self.__stack[-1])
			self.__level = "WORK"
			self.DeleteAllItems()
			self.__fillRegister(elements)
		elif self.__level == "WORK":
			self.__stack.pop()
			elements = self.__dBController.getEntriesRegister()
			self.__level = "ENTRY"
			self.DeleteAllItems()
			self.__fillRegister(elements)
		log.opr("EntryRegisterBrowser.onUp return", [], 1)

	def topLevel(self):
		return self.__level == "ENTRY"
			
	def binaryAvailable(self):
		return self.__level == "ENTRY" and self._itemsLen() > 0

	def allowsNextFiche(self):
		return False

