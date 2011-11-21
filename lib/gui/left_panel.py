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
from maleks.i18n import _
from maleks.maleks.useful import nvl, Notifier
from maleks.maleks import log

# TODO: C posprawdzac czy dirty dobrze dziala

class ValidatingTextCtrl(wx.TextCtrl):

	def __init__(self, id, value="", pos=wx.DefaultPosition, size=wx.DefaultSize, style=0, validator=wx.DefaultValidator, name=wx.TextCtrlNameStr, myvalidator=lambda x: True, idd=0):
		wx.TextCtrl.__init__(self, id, value=value, pos=pos, size=size, style=style, validator=validator, name=name)
		self.__value = None
		self.__validator = myvalidator
		self.__valid = True
		self.__frozen = None
		self.__id = idd

	def getId(self):
		return self.__id

	def CheckValidity(self, friend=None):
		if not self.__validator(self.GetValue()):
			self.SetBackgroundColour(wx.Colour(255, 0, 0))
			self.__valid = False
			#if friend != None:
			#	friend.SetBackgroundColour(wx.Colour(255, 0, 0))
			#	friend.__valid = False
		else:
			self.SetBackgroundColour(wx.NullColour)
			self.__valid = True
			#if friend != None:
			#	friend.SetBackgroundColour(wx.NullColour)
			#	friend.__valid = True

	def FreezeValue(self):
		self.__freeze = self.GetValue()

	def ThawValue(self):
		self.SetValue(self.__freeze)

	def MemorizeValue(self, value):
		self.__value = value
		self.SetValue(value)

	def GetMemorizedValue(self):
		return self.__value

	def GetValidatedValue(self):
		if self.__validator(self.GetValue()):
			return self.GetValue()
		else:
			return self.__value

	def DisableIfValid(self):
		if not self.__valid:
			self.SetBackgroundColour(wx.NullColour())
		else:
			self.Disable()

class IndexPanel(wx.Panel):
	
	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)
		self._dirty = False
		self._ficheId = None
		self._inputEventEnabled = False
		self._frozen = False

	def freezeValues(self):
		self._frozen = True

	def thawValues(self):
		self._frozen = False

	def _input(self, event):
		if self._inputEventEnabled and (not self._frozen):
			self._dirty = True

	def isDirty(self):
		return self._dirty

	def getFicheId(self):
		return self._ficheId

	def enableInputEvent(self):
		self._inputEventEnabled = True

	def disableInputEvent(self):
		self._inputEventEnabled = False

class SecondaryIndicesPanel(IndexPanel):

	def __init__(self, *args, **kwargs):
		IndexPanel.__init__(self, *args, **kwargs)
		sizer = wx.BoxSizer(wx.VERTICAL)
		self.__pageNumber = ValidatingTextCtrl(self, myvalidator=lambda x: x == "" or x.isdigit(), idd=0)
		self.__lineNumber = ValidatingTextCtrl(self, myvalidator=lambda x: x == "" or x.isdigit(), idd=1)
		self.__entryBegin = ValidatingTextCtrl(self, myvalidator=lambda x: len(x) <= 150, idd=2)
		self.__entryBeginLine = ValidatingTextCtrl(self, myvalidator=lambda x: x == "" or x.isdigit(), idd=3)
		self.__entryBeginWord = ValidatingTextCtrl(self, myvalidator=lambda x: x == "" or x.isdigit(), idd=4)
		self.__entryBeginChar = ValidatingTextCtrl(self, myvalidator=lambda x: x == "" or x.isdigit(), idd=5)
		self.__entryEnd = ValidatingTextCtrl(self, myvalidator=lambda x: len(x) <= 150, idd=6)
		self.__entryEndLine = ValidatingTextCtrl(self, myvalidator=lambda x: x == "" or x.isdigit(), idd=7)
		self.__entryEndWord = ValidatingTextCtrl(self, myvalidator=lambda x: x == "" or x.isdigit(), idd=8)
		self.__entryEndChar = ValidatingTextCtrl(self, myvalidator=lambda x: x == "" or x.isdigit(), idd=9)
		self.__ficheEntryComment = ValidatingTextCtrl(self, style=wx.TE_MULTILINE, myvalidator=lambda x: len(x) <= 50, idd=10)
		self.__entryLocation = ValidatingTextCtrl(self, myvalidator=lambda x: len(x) <= 150, idd=11)
		self.__textEntryComment = ValidatingTextCtrl(self, style=wx.TE_MULTILINE, myvalidator=lambda x: len(x) <= 50, idd=12)
		self.SetSizer(sizer)
		sizer.Add(wx.StaticText(self, label=_("Page number") + ":"))
		sizer.Add(self.__pageNumber, 0, wx.EXPAND)
		sizer.Add(wx.StaticText(self, label=_("Line number") + ":"))
		sizer.Add(self.__lineNumber, 0, wx.EXPAND)
		sizer.Add(wx.StaticText(self, label=_("Entry begin") + ":"))
		sizer.Add(self.__entryBegin, 0, wx.EXPAND)
		sizer.Add(wx.StaticText(self, label=_("Entry begin (line)") + ":"))
		sizer.Add(self.__entryBeginLine, 0, wx.EXPAND)
		sizer.Add(wx.StaticText(self, label=_("Entry begin (word)") + ":"))
		sizer.Add(self.__entryBeginWord, 0, wx.EXPAND)
		sizer.Add(wx.StaticText(self, label=_("Entry begin (char)") + ":"))
		sizer.Add(self.__entryBeginChar, 0, wx.EXPAND)
		sizer.Add(wx.StaticText(self, label=_("Entry end") + ":"))
		sizer.Add(self.__entryEnd, 0, wx.EXPAND)
		sizer.Add(wx.StaticText(self, label=_("Entry end (line)") + ":"))
		sizer.Add(self.__entryEndLine, 0, wx.EXPAND)
		sizer.Add(wx.StaticText(self, label=_("Entry end (word)") + ":"))
		sizer.Add(self.__entryEndWord, 0, wx.EXPAND)
		sizer.Add(wx.StaticText(self, label=_("Entry end (char)") + ":"))
		sizer.Add(self.__entryEndChar, 0, wx.EXPAND)
		sizer.Add(wx.StaticText(self, label=_("Comment") + ":"))
		sizer.Add(self.__ficheEntryComment, 2, wx.EXPAND)
		sizer.Add(wx.StaticText(self, label=_("Entry location") + ":"))
		sizer.Add(self.__entryLocation, 0, wx.EXPAND)
		sizer.Add(wx.StaticText(self, label=_("Comment") + ":"))
		sizer.Add(self.__textEntryComment, 2, wx.EXPAND)
		self.__pageNumber.Bind(wx.EVT_TEXT, self.__validateInput)
		self.__lineNumber.Bind(wx.EVT_TEXT, self.__validateInput)
		self.__entryBegin.Bind(wx.EVT_TEXT, self.__validateInput)
		self.__entryBeginLine.Bind(wx.EVT_TEXT, self.__validateInput)
		self.__entryBeginWord.Bind(wx.EVT_TEXT, self.__validateInput)
		self.__entryBeginChar.Bind(wx.EVT_TEXT, self.__validateInput)
		self.__entryEnd.Bind(wx.EVT_TEXT, self.__validateInput)
		self.__entryEndLine.Bind(wx.EVT_TEXT, self.__validateInput)
		self.__entryEndWord.Bind(wx.EVT_TEXT, self.__validateInput)
		self.__entryEndChar.Bind(wx.EVT_TEXT, self.__validateInput)
		self.__ficheEntryComment.Bind(wx.EVT_TEXT, self.__validateInput)
		self.__entryLocation.Bind(wx.EVT_TEXT, self.__entryLocationInput)
		self.__textEntryComment.Bind(wx.EVT_TEXT, self.__validateInput)

	def freezeValues(self):
		IndexPanel.freezeValues(self)
		self.__pageNumber.FreezeValue()
		self.__lineNumber.FreezeValue()
		self.__entryBegin.FreezeValue()
		self.__entryBeginLine.FreezeValue()
		self.__entryBeginWord.FreezeValue()
		self.__entryBeginChar.FreezeValue()
		self.__entryEnd.FreezeValue()
		self.__entryEndLine.FreezeValue()
		self.__entryEndWord.FreezeValue()
		self.__entryEndChar.FreezeValue()
		self.__ficheEntryComment.FreezeValue()
		self.__entryLocation.FreezeValue()
		self.__textEntryComment.FreezeValue()

	def thawValues(self):
		IndexPanel.thawValues(self)
		self.__pageNumber.ThawValue()
		self.__lineNumber.ThawValue()
		self.__entryBegin.ThawValue()
		self.__entryBeginLine.ThawValue()
		self.__entryBeginWord.ThawValue()
		self.__entryBeginChar.ThawValue()
		self.__entryEnd.ThawValue()
		self.__entryEndLine.ThawValue()
		self.__entryEndWord.ThawValue()
		self.__entryEndChar.ThawValue()
		self.__ficheEntryComment.ThawValue()
		self.__entryLocation.ThawValue()
		self.__textEntryComment.ThawValue()

	def __validateInput(self, event):
		log.op("__validateInput", [event.GetEventObject().getId(), event.GetEventObject().GetValue()], 0)
		self._input(event)
		event.GetEventObject().CheckValidity()
		log.opr("__validateInput return", [], 1)

	def __entryLocationInput(self, event):
		log.op("__entryLocationInput", [self.__entryLocation.GetValue()], 0)
		self._input(event)
		if self.__entryLocation.GetValue() == "":
			self.__textEntryComment.SetValue("")
			self.__textEntryComment.DisableIfValid()
		else:
			self.__textEntryComment.Enable()
		self.__entryLocation.CheckValidity(friend=self.__textEntryComment)
		log.opr("__entryLocationInput return", [], 1)

	def fill(self, values, ficheId):
		self._dirty = False
		self._ficheId = ficheId
		self.__pageNumber.MemorizeValue(nvl(values[0]))
		self.__lineNumber.MemorizeValue(nvl(values[1]))
		self.__entryBegin.MemorizeValue(nvl(values[2]))
		self.__entryBeginLine.MemorizeValue(nvl(values[3]))
		self.__entryBeginWord.MemorizeValue(nvl(values[4]))
		self.__entryBeginChar.MemorizeValue(nvl(values[5]))
		self.__entryEnd.MemorizeValue(nvl(values[6]))
		self.__entryEndLine.MemorizeValue(nvl(values[7]))
		self.__entryEndWord.MemorizeValue(nvl(values[8]))
		self.__entryEndChar.MemorizeValue(nvl(values[9]))
		self.__ficheEntryComment.MemorizeValue(nvl(values[10]))
		self.__entryLocation.MemorizeValue(nvl(values[11]))
		self.__textEntryComment.MemorizeValue(nvl(values[12]))
		if self.__entryLocation.GetValue() == "":
			self.__textEntryComment.DisableIfValid()

	def getValues(self):
		return ((self.__pageNumber.GetValidatedValue(), self.__lineNumber.GetValidatedValue(), self.__entryBegin.GetValidatedValue(), self.__entryBeginLine.GetValidatedValue(), self.__entryBeginWord.GetValidatedValue(), self.__entryBeginChar.GetValidatedValue(), self.__entryEnd.GetValidatedValue(), self.__entryEndLine.GetValidatedValue(), self.__entryEndWord.GetValidatedValue(), self.__entryEndChar.GetValidatedValue(), self.__ficheEntryComment.GetValidatedValue()), self.__entryLocation.GetValidatedValue(), self.__textEntryComment.GetValidatedValue())

class MainIndicesPanel(IndexPanel):

	def __init__(self, *args, **kwargs):
		IndexPanel.__init__(self, *args, **kwargs)		
		self._sizer = wx.BoxSizer(wx.VERTICAL)
		self._buildEntryIndicesGUI()
		self._buildFicheIndexGUI()
		self._buildPageAndLineIndicesGUI()
		self.SetSizer(self._sizer)
	
	def freezeValues(self):
		IndexPanel.freezeValues(self)
		self.__actualEntry.FreezeValue()
		self.__actualComment.FreezeValue()
		self.__originalEntry.FreezeValue()
		self.__originalComment.FreezeValue()
		self.__work.FreezeValue()
		self.__firstWordPage.FreezeValue()
		self.__lastWordPage.FreezeValue()
		self.__matrixNumber.FreezeValue()
		self.__matrixSector.FreezeValue()
		self.__editor.FreezeValue()
		self.__comment.FreezeValue()
		self.__page.FreezeValue()
		self.__pageComment.FreezeValue()
		self.__line.FreezeValue()
		self.__lineComment.FreezeValue()

	def thawValues(self):
		IndexPanel.thawValues(self)
		self.__actualEntry.ThawValue()
		self.__actualComment.ThawValue()
		self.__originalEntry.ThawValue()
		self.__originalComment.ThawValue()
		self.__work.ThawValue()
		self.__firstWordPage.ThawValue()
		self.__lastWordPage.ThawValue()
		self.__matrixNumber.ThawValue()
		self.__matrixSector.ThawValue()
		self.__editor.ThawValue()
		self.__comment.ThawValue()
		self.__page.ThawValue()
		self.__pageComment.ThawValue()
		self.__line.ThawValue()
		self.__lineComment.ThawValue()

	def _buildEntryIndicesGUI(self):
		self.__actualEntry = ValidatingTextCtrl(self, myvalidator=lambda x: len(x) <= 40, idd=13)
		self.__actualComment = ValidatingTextCtrl(self, style=wx.TE_MULTILINE, myvalidator=lambda x: len(x) <= 50, idd=14)
		self.__originalEntry = ValidatingTextCtrl(self, myvalidator=lambda x: len(x) <= 40, idd=15)
		self.__originalComment = ValidatingTextCtrl(self, style=wx.TE_MULTILINE, myvalidator=lambda x: len(x) <= 50, idd=16)
		self._sizer.Add(wx.StaticText(self, label=_("Actual entry") + ":"))
		self._sizer.Add(self.__actualEntry, 0, wx.EXPAND)
		self._sizer.Add(wx.StaticText(self, label=_("Comment") + ":"))
		self._sizer.Add(self.__actualComment, 2, wx.EXPAND)
		self._sizer.Add(wx.StaticText(self, label=_("Original entry") + ":"))
		self._sizer.Add(self.__originalEntry, 0, wx.EXPAND)
		self._sizer.Add(wx.StaticText(self, label=_("Comment") + ":"))
		self._sizer.Add(self.__originalComment, 2, wx.EXPAND)
		self.__actualEntry.Bind(wx.EVT_TEXT, self.__actualEntryInput)
		self.__actualComment.Bind(wx.EVT_TEXT, self.__validateInput)
		self.__originalEntry.Bind(wx.EVT_TEXT, self.__originalEntryInput)
		self.__originalComment.Bind(wx.EVT_TEXT, self.__validateInput)
	
	def __actualEntryInput(self, event):
		log.op("__actualEntryInput", [self.__actualEntry.GetValue()], 0)
		self._input(event)
		if self.__actualEntry.GetValue() == "":
			self.__actualComment.SetValue("")
			self.__actualComment.DisableIfValid()
		else:
			self.__actualComment.Enable()
		self.__actualEntry.CheckValidity(friend=self.__actualComment)
		log.opr("__actualEntryInput return", [], 1)

	def __originalEntryInput(self, event):
		log.op("__originalEntryInput", [self.__originalEntry.GetValue()], 0)
		self._input(event)
		if self.__originalEntry.GetValue() == "":
			self.__originalComment.SetValue("")
			self.__originalComment.DisableIfValid()
		else:
			self.__originalComment.Enable()
		self.__originalEntry.CheckValidity(friend=self.__originalComment)
		log.opr("__originalEntryInput return", [], 1)

	def fillEntryIndices(self, (actual, actualComment, original, originalComment), ficheId):
		self._dirty = False
		self._ficheId = ficheId
		self.__actualEntry.MemorizeValue(nvl(actual))
		self.__actualComment.MemorizeValue(nvl(actualComment))
		self.__originalEntry.MemorizeValue(nvl(original))
		self.__originalComment.MemorizeValue(nvl(originalComment))
		if self.__actualEntry.GetValue() == "":
			self.__actualComment.DisableIfValid()
		if self.__originalEntry.GetValue() == "":
			self.__originalComment.DisableIfValid()

	def getEntryIndicesValue(self):
		return (self.__actualEntry.GetValidatedValue(), self.__actualComment.GetValidatedValue(), self.__originalEntry.GetValidatedValue(), self.__originalComment.GetValidatedValue())

	def _buildFicheIndexGUI(self):
		self.__work = ValidatingTextCtrl(self, myvalidator=lambda x: len(x) <= 50, idd=17)
		self.__firstWordPage = ValidatingTextCtrl(self, myvalidator=lambda x: x == "" or x.isdigit(), idd=18)
		self.__lastWordPage = ValidatingTextCtrl(self, myvalidator=lambda x: x == "" or x.isdigit(), idd=19)
		self.__matrixNumber = ValidatingTextCtrl(self, myvalidator=lambda x: x == "" or x.isdigit(), idd=20)
		self.__matrixSector = ValidatingTextCtrl(self, myvalidator=lambda x: x in ["", "a", "b", "c"], idd=21)
		self.__editor = ValidatingTextCtrl(self, myvalidator=lambda x: len(x) <= 10, idd=22)
		self.__comment = ValidatingTextCtrl(self, style=wx.TE_MULTILINE, myvalidator=lambda x: len(x) <= 50, idd=23)
		self._sizer.Add(wx.StaticText(self, label=_("Work identificator") + ":"))
		self._sizer.Add(self.__work, 0, wx.EXPAND)
		self._sizer.Add(wx.StaticText(self, label=_("Page number of the first word") + ":"))
		self._sizer.Add(self.__firstWordPage, 0, wx.EXPAND)
		self._sizer.Add(wx.StaticText(self, label=_("Page number of the last word") + ":"))
		self._sizer.Add(self.__lastWordPage, 0, wx.EXPAND)
		self._sizer.Add(wx.StaticText(self, label=_("Matrix number") + ":"))
		self._sizer.Add(self.__matrixNumber, 0, wx.EXPAND)
		self._sizer.Add(wx.StaticText(self, label=_("Matrix sector symbol") + ":"))
		self._sizer.Add(self.__matrixSector, 0, wx.EXPAND)
		self._sizer.Add(wx.StaticText(self, label=_("Editor initials") + ":"))
		self._sizer.Add(self.__editor, 0, wx.EXPAND)
		self._sizer.Add(wx.StaticText(self, label=_("Comment") + ":"))
		self._sizer.Add(self.__comment, 2, wx.EXPAND)
		self.__work.Bind(wx.EVT_TEXT, self.__validateInput)
		self.__firstWordPage.Bind(wx.EVT_TEXT, self.__validateInput)
		self.__lastWordPage.Bind(wx.EVT_TEXT, self.__validateInput)
		self.__matrixNumber.Bind(wx.EVT_TEXT, self.__validateInput)
		self.__matrixSector.Bind(wx.EVT_TEXT, self.__validateInput)
		self.__editor.Bind(wx.EVT_TEXT, self.__validateInput)
		self.__comment.Bind(wx.EVT_TEXT, self.__validateInput)

	def fillFicheIndex(self, ficheIndexRecord, ficheId):
		self._dirty = False
		self._ficheId = ficheId
		self.__work.MemorizeValue(nvl(ficheIndexRecord[0]))
		self.__firstWordPage.MemorizeValue(nvl(ficheIndexRecord[1]))
		self.__lastWordPage.MemorizeValue(nvl(ficheIndexRecord[2]))
		self.__matrixNumber.MemorizeValue(nvl(ficheIndexRecord[3]))
		self.__matrixSector.MemorizeValue(nvl(ficheIndexRecord[4]))
		self.__editor.MemorizeValue(nvl(ficheIndexRecord[5]))
		self.__comment.MemorizeValue(nvl(ficheIndexRecord[6]))

	def __validateInput(self, event):
		log.op("__validateInput", [event.GetEventObject().getId(), event.GetEventObject().GetValue()], 2)
		self._input(event)
		event.GetEventObject().CheckValidity()
		#self.__firstWordPage.CheckValidity()
		#self.__lastWordPage.CheckValidity()
		#self.__matrixNumber.CheckValidity()
		log.opr("__validateInput return", [], 3)

	def getFicheIndexValue(self):
		return (self.__work.GetValidatedValue(), self.__firstWordPage.GetValidatedValue(), self.__lastWordPage.GetValidatedValue(), self.__matrixNumber.GetValidatedValue(), self.__matrixSector.GetValidatedValue(), self.__editor.GetValidatedValue(), self.__comment.GetValidatedValue())

	def _buildPageAndLineIndicesGUI(self):
		self.__page = ValidatingTextCtrl(self, myvalidator=lambda x: x == "" or x.isdigit(), idd=24)
		self.__pageComment = ValidatingTextCtrl(self, style=wx.TE_MULTILINE, myvalidator=lambda x: len(x) <= 50, idd=25)
		self.__line = ValidatingTextCtrl(self, myvalidator=lambda x: x == "" or x.isdigit(), idd=26)
		self.__lineComment = ValidatingTextCtrl(self, style=wx.TE_MULTILINE, myvalidator=lambda x: len(x) <= 50, idd=27)
		self._sizer.Add(wx.StaticText(self, label=_("Page number") + ":"), 0, wx.EXPAND)
		self._sizer.Add(self.__page, 0, wx.EXPAND)
		self._sizer.Add(wx.StaticText(self, label=_("Comment") + ":"), 0, wx.EXPAND)
		self._sizer.Add(self.__pageComment, 2, wx.EXPAND)
		self._sizer.Add(wx.StaticText(self, label=_("Line number") + ":"), 0, wx.EXPAND)
		self._sizer.Add(self.__line, 0, wx.EXPAND)
		self._sizer.Add(wx.StaticText(self, label=_("Comment") + ":"), 0, wx.EXPAND)
		self._sizer.Add(self.__lineComment, 2, wx.EXPAND)
		self.__page.Bind(wx.EVT_TEXT, self.__pageInput)
		self.__pageComment.Bind(wx.EVT_TEXT, self.__validateInput)
		self.__line.Bind(wx.EVT_TEXT, self.__lineInput)
		self.__lineComment.Bind(wx.EVT_TEXT, self.__validateInput)

	def __pageInput(self, event):
		log.op("__pageInput", [self.__page.GetValue()], 0)
		self._input(event)
		if self.__page.GetValue() == "":
			self.__pageComment.SetValue("")
			self.__pageComment.DisableIfValid()
		else:
			self.__pageComment.Enable()
		self.__page.CheckValidity(friend=self.__pageComment)
		log.opr("__pageInput return", [], 1)

	def __lineInput(self, event):
		log.op("__lineInput", [self.__line.GetValue()], 0)
		self._input(event)
		if self.__line.GetValue() == "":
			self.__lineComment.SetValue("")
			self.__lineComment.DisableIfValid()
		else:
			self.__lineComment.Enable()
		self.__line.CheckValidity(friend=self.__lineComment)
		log.opr("__lineInput return", [], 1)

	def fillPageAndLineIndices(self, (page, pageComment, line, lineComment), ficheId):
		self._dirty = False
		self._ficheId = ficheId
		self.__page.MemorizeValue(nvl(page))
		self.__pageComment.MemorizeValue(nvl(pageComment))
		self.__line.MemorizeValue(nvl(line))
		self.__lineComment.MemorizeValue(nvl(lineComment))
		if self.__page.GetValue() == "":
			self.__pageComment.DisableIfValid()
		if self.__line.GetValue() == "":
			self.__lineComment.DisableIfValid()

	def getPageAndLineIndicesValue(self):
		return (self.__page.GetValidatedValue(), self.__pageComment.GetValidatedValue(), self.__line.GetValidatedValue(), self.__lineComment.GetValidatedValue())

class ControlPanel(wx.Panel, Notifier):

	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)
		Notifier.__init__(self)
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		#:self.__button = wx.CheckBox(self, wx.ID_ANY)
		#self.__down = wx.ComboBox(self, wx.ID_ANY)
		#:sizer.Add(self.__button, 0, wx.EXPAND)
		#:sizer.Add(wx.StaticText(self, label=_("Search mode")), 0, wx.EXPAND)
		self.SetSizer(sizer)
		#:self.Bind(wx.EVT_CHECKBOX, self.__onClick)

	def __onClick(self, event):
		for l in self._listeners:
			l.on_search_mode(event)

	#def stopSearch(self):
	#	self.__button.SetValue(False)
	#	self.__onClick(None)

	#def isSearchMode(self):
	#	return self.__button.GetValue()

