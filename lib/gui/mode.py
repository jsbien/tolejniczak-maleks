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

class Mode(object):

	def __init__(self, name, accel=wx.AcceleratorTable([])):
		self.__name = name
		self.__acceleratorTable = accel
		self.__menuShortcut = {}
	
	def getName(self):
		return self.__name
	
	def setName(self, name):
		self.__name = name
	
	def getAcceleratorTable(self):
		return self.__acceleratorTable

	def addMenuShortcut(self, method, shortcut):
		self.__menuShortcut.setdefault(method, shortcut)

	def getMenuShortcut(self, method):
		return self.__menuShortcut.get(method)

