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
import time
from maleks.gui.reg_browser import RegisterBrowser
from maleks.maleks.fiche import Fiche
from maleks.maleks import log

class StructureRegisterBrowser(RegisterBrowser):

	def __init__(self, *args, **kwargs):
		RegisterBrowser.__init__(self, *args, **kwargs)

	def reset(self):
		log.log("StructreRegisterBrowser.reset", [], 0)
		RegisterBrowser.reset(self)
		self.__binaryAvailable = False
		self.__register = None
		self.__ficheLevel = False
		self.__element = None
		self.__path = ""
		log.log("StructureRegisterBrowser.reset return", [], 1)

	def setRegister(self, reg, getEntry=None):
		log.log("StructureRegisterBrowser.setRegister", [reg, getEntry], 0)
		if self.binarySearchActive():
			for l in self._listeners:
				l.stop_binary_search()
		self.reset()
		self.__register = reg
		self.__fillRegister(reg.getRoot().getChildren())
		self.__element = reg.getRoot()
		self.__path = self.__element.getDescriptivePath()
		self._initialized = True
		log.log("StructureRegisterBrowser.setRegister return", [], 1)

	def handleClone(self, ficheId):
		log.log("StructureRegisterBrowser.handleClone", [], 0)
		if self.__ficheLevel:
			self.__selectStructureNode(self.__element)
			self.select(ficheId)
		log.log("StructureRegisterBrowser.handleClone return", [], 1)

	def __fillRegister(self, elements):
		log.log("StructureRegisterBrowser.__fillRegister", [elements], 0)
		i = 0
		self._itemsNo = 0
		for element in elements:
			if isinstance(element, Fiche):
				self.__ficheLevel = True
			self.InsertStringItem(i, element.getLabel())
			self.SetStringItem(i, 1, "")
			self.SetStringItem(i, 2, "")
			self._items.append(i)
			self._item2element.setdefault(i, element.getId())
			self._element2item.setdefault(element.getId(), i)
			self._itemsNo += 1
			i += 1
		self.SetColumnWidth(0, wx.LIST_AUTOSIZE)
		log.log("StructureRegisterBrowser.__fillRegister return", [], 1)

	def onSelect(self, event):
		log.op("StructureRegisterBrowser.onSelect", [self._elementOf(self._unmap(event.GetIndex()))], 0)
		RegisterBrowser.onSelect(self, event)
		log.opr("StructureRegisterBrowser.onSelect return", [], 1)

	def select(self, elementId):
		log.log("StructureRegisterBrowser.select", [elementId], 0)
		if self.__ficheLevel:
			RegisterBrowser.select(self, elementId)
		log.log("StructureRegisterBrowser.select return", [], 1)
	
	def __selectStructureNode(self, node):
		log.log("StructureRegisterBrowser.__selectStructureNode", [node.getDescriptivePath()], 0)
		self.__path = node.getDescriptivePath()
		for l in self._listeners:
			l.on_structure_element_selected(node.getDescriptivePath())
		self.DeleteAllItems()
		self.__fillRegister(node.getChildren())
		log.log("StructureRegisterBrowser.__selectStructureNode return", [], 1)

	def _element_selected(self, elementId, notify=True):
		log.log("StructureRegisterBrowser._element_selected", [elementId, notify], 0)
		if self.__ficheLevel:
			RegisterBrowser._element_selected(self, elementId, notify=notify)
		else:
			self.__element = self.__register.getNodeById(elementId)
		log.log("StructureRegisterBrowser._element_selected return", [self.__element], 1)

	def levelDown(self):
		log.op("StructureRegisterBrowser.levelDown", [self.__ficheLevel], 0)
		if not self.__ficheLevel:
			self.__selectStructureNode(self.__element)
			if self.__ficheLevel:
				for l in self._listeners:
					l.start_binary_search()
				self.__binaryAvailable = True
				#for l in self._listeners: # TODO: D jeden listener
				#	elementId = l.request_selection()
				#	if elementId != None:
				#		self.select(elementId)
				#		time.sleep(0.1) # TODO: NOTE bez tego nie zaznacza w wykazie aktualnie ogladanej fiszki
				time.sleep(0.1)
		log.opr("StructureRegisterBrowser.levelDown return", [], 1)

	def onUp(self, event):
		log.op("StructureRegisterBrowser.onUp", [event], 0)
		if self.__element.getParent() != None:
			self.__ficheLevel = False
			self.__binaryAvailable = False
			self.__element = self.__element.getParent()
			self.__selectStructureNode(self.__element)
		log.op("StructureRegisterBrowser.onUp return", [], 1)

	def topLevel(self):
		return self.__element.getParent() == None

	def _nextFicheNotFound(self):
		log.op("StructureRegisterBrowser._nextFicheNotFound", [], 0)
		fiche = self.__register.findNextFiche(self.__element)
		if fiche != None:
			self.__element = fiche.getParent()
			self.__selectStructureNode(self.__element)
			itemId = self._element2item[fiche.getId()]
			self._unselect(self._selected)
			self._select(itemId, veto=True)
			RegisterBrowser._element_selected(self, fiche.getId(), notify=False)
		log.op("StructureRegisterBrowser._nextFicheNotFound return", [], 1)

	def getPath(self):
		return self.__path
	
	def binaryAvailable(self):
		return self.__binaryAvailable and self._itemsLen() > 0

	def allowsNextFiche(self):
		return self.__ficheLevel

