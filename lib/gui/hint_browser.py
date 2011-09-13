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
from maleks.gui.reg_browser import RegisterBrowser
from maleks.maleks.registers import anyHint
		
class HintRegisterBrowser(RegisterBrowser):

	def __init__(self, *args, **kwargs):
		RegisterBrowser.__init__(self, *args, **kwargs)
	
	def reset(self):
		RegisterBrowser.reset(self)
		self.__hints = []

	def setRegister(self, reg, getEntry=None):
		self.reset()
		i = 0
		for element in reg:
			self.InsertStringItem(i, "")
			self.SetStringItem(i, 1, "")
			self.SetStringItem(i, 2, anyHint(element))
			self._items.append(i)
			self._item2element.setdefault(i, anyHint(element))
			self._element2item.setdefault(anyHint(element), i)
			self.__hints.append(element)
			i += 1
			
	def hintChanged(self, hint):
		itemId = self.FindItem(-1, hint, partial=True)
		if itemId != -1:
			if self._selected != None:
				self._unselect(self._selected)
			self._select(itemId, veto=True)

	def binaryAvailable(self):
		return False

	def allowsNextFiche(self):
		return False

	def _element_selected(self, elementId):
		for l in self._listeners:
			l.on_hint_selected(self.__hints[self._element2item[elementId]])

