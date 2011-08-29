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
from djvusmooth.gui.reg_browser import RegisterBrowser
from djvusmooth.maleks.fiche import Fiche

class StructureRegisterBrowser(RegisterBrowser):

	def __init__(self, *args, **kwargs):
		RegisterBrowser.__init__(self, *args, **kwargs)

	def reset(self):
		RegisterBrowser.reset(self)
		self.__binaryAvailable = False
		self.__register = None
		self.__ficheLevel = False
		self.__element = None

	def setRegister(self, reg):
		self.__register = reg
		self.__fillRegister(reg.getRoot().getChildren())
		self.__element = reg.getRoot()

	def __fillRegister(self, elements):
		i = 0
		for element in elements:
			if isinstance(element, Fiche):
				self.__ficheLevel = True
			self.InsertStringItem(i, element.getLabel())
			self._items.append(i)
			self._item2element.setdefault(i, element.getId())
			self._element2item.setdefault(element.getId(), i)
			i += 1	

	def select(self, elementId):
		if self.__ficheLevel:
			RegisterBrowser.select(self, elementId)

	def _element_selected(self, elementId, notify=True):
		if self.__ficheLevel:
			RegisterBrowser._element_selected(self, elementId, notify=notify)
		else:
			self.__element = self.__register.getNodeById(elementId)
			self.DeleteAllItems()
			self.__fillRegister(self.__element.getChildren())
			if self.__ficheLevel:
				for l in self._listeners: # TODO: D jeden listener
					elementId = l.request_selection()
					if elementId != None:
						self.select(elementId)
						#time.sleep(0.5) # TODO: NOTE bez tego nie zaznacza w wykazie aktualnie ogladanej fiszki
	
	def binaryAvailable(self):
		return self.__binaryAvailable

