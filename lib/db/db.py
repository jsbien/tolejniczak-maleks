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

import _mysql_exceptions
from maleks.db.db_work import DBWorkController
from maleks.i18n import _
from maleks.maleks.registers import TaskRegister
from maleks.maleks.fiche import Fiche

class DBController(DBWorkController):

	def __init__(self, config):
		DBWorkController.__init__(self, config)

	def addFicheToFichesIndex(self, ficheId):
		cursor = self._openDBWithCursor()
		cursor.execute("insert into fiches values (null, %s, null, null, null, null, null, null, null, null)", (ficheId))
		self._closeDBAndCursor(cursor)

	def bookmarkFiche(self, ficheId):
		cursor = self._openDBWithCursor()
		cursor.execute("update fiches set bookmark = sysdate() where fiche = %s", (ficheId))
		self._closeDBAndCursor(cursor)

	def addFicheToEntriesIndex(self, ficheId, entry):
		cursor = self._openDBWithCursor()
		#try:
		#	cursor.execute("insert into actual_entries values (%s, %s, null)", (ficheId, entry))
		#	cursor.execute("insert into original_entries values (%s, %s, null)", (ficheId, entry))
		#except _mysql_exceptions.IntegrityError:
		#	self._closeDBAndCursor(cursor)
		#	return _('Fiche already indexed')
		try:
			cursor.execute("insert into actual_entries values (%s, %s, null)", (ficheId, entry))
		except _mysql_exceptions.IntegrityError:
			cursor.execute("update actual_entries set entry = %s where fiche = %s", (entry, ficheId))
		try:
			cursor.execute("insert into original_entries values (%s, %s, null)", (ficheId, entry))
		except _mysql_exceptions.IntegrityError:
			cursor.execute("update original_entries set entry = %s where fiche = %s", (entry, ficheId))
		#print cursor.rowcount
		self._closeDBAndCursor(cursor)
		return None

	def addFicheToPrefixesIndex(self, ficheId, entry):
		cursor = self._openDBWithCursor()
		try:
			cursor.execute("insert into entry_prefixes values (%s, %s, null)", (ficheId, entry))
		except _mysql_exceptions.IntegrityError:
			self._closeDBAndCursor(cursor)
			return _('Fiche already indexed in entry prefix index')
		self._closeDBAndCursor(cursor)
		return None

	def getHypothesisForFiche(self, ficheId, alphabetic):
		cursor = self._openDBWithCursor()
		cursor.execute("select entry_hypothesis from hypotheses where fiche = %s", (ficheId))
		row = cursor.fetchone()
		if row == None and alphabetic:
			cursor.execute("select position from fiches where fiche = %s", (ficheId))
			pos = cursor.fetchone()
			cursor.execute("select b.entry, c.entry from fiches a, actual_entries b, original_entries c where a.fiche = b.fiche and b.fiche = c.fiche and position < %s order by position desc", (pos[0]))
			prevEntry = cursor.fetchone()
			cursor.execute("select b.entry, c.entry from fiches a, actual_entries b, original_entries c where a.fiche = b.fiche and b.fiche = c.fiche and position > %s order by position", (pos))
			nextEntry = cursor.fetchone()
			if nextEntry != None and prevEntry != None and nextEntry[0] == prevEntry[0] == nextEntry[1] == prevEntry[1]:
				row = nextEntry
		self._closeDBAndCursor(cursor)
		if row == None:
			return None
		else:
			return row[0]

	def getActualEntryForFiche(self, ficheId):
		res = None
		cursor = self._openDBWithCursor()
		cursor.execute("select entry from actual_entries where fiche = %s", (ficheId))
		row = cursor.fetchone()
		if row != None:
			res = row[0]
		self._closeDBAndCursor(cursor)
		return res

	def getOriginalEntryForFiche(self, ficheId):
		res = None
		cursor = self._openDBWithCursor()
		cursor.execute("select entry from original_entries where fiche = %s", (ficheId))
		row = cursor.fetchone()
		if row != None:
			res = row[0]
		self._closeDBAndCursor(cursor)
		return res

	def getEntriesForFiche(self, ficheId):
		actual = ""
		actualComment = ""
		original = ""
		originalComment = ""
		cursor = self._openDBWithCursor()
		cursor.execute("select entry, comment from actual_entries where fiche = %s", (ficheId))
		row = cursor.fetchone()
		if row != None:
			actual = row[0]
			actualComment = row[1]
		cursor.execute("select entry, comment from original_entries where fiche = %s", (ficheId))
		row = cursor.fetchone()
		if row != None:
			original = row[0]
			originalComment = row[1]
		self._closeDBAndCursor(cursor)
		return (actual, actualComment, original, originalComment)

	def setEntriesForFiche(self, (actual, actualComment, original, originalComment), ficheId):
		cursor = self._openDBWithCursor()
		cursor.execute("select entry from actual_entries where fiche = %s", (ficheId))
		row = cursor.fetchone()
		hasActual = row != None
		cursor.execute("select entry from original_entries where fiche = %s", (ficheId))
		row = cursor.fetchone()
		hasOriginal = row != None
		if hasActual:
			if actual != "":
				cursor.execute("update actual_entries set entry = %s, comment = %s where fiche = %s", (actual, self._nvl(actualComment), ficheId))
			else:
				cursor.execute("delete from actual_entries where fiche = %s", (ficheId))
		elif actual != "":
			cursor.execute("insert into actual_entries values (%s, %s, %s)", (ficheId, actual, self._nvl(actualComment)))
		if hasOriginal:
			if original != "":
				cursor.execute("update original_entries set entry = %s, comment = %s where fiche = %s", (original, self._nvl(originalComment), ficheId))
			else:
				cursor.execute("delete from original_entries where fiche = %s", (ficheId))
		elif original != "":
			cursor.execute("insert into original_entries values (%s, %s, %s)", (ficheId, original, self._nvl(originalComment)))
		self._closeDBAndCursor(cursor)

	def getFiche(self, ficheId):
		cursor = self._openDBWithCursor()
		cursor.execute("select work, firstWordPage, lastWordPage, matrixNumber, matrixSector, editor, comment from fiches where fiche = %s", (ficheId))
		row = cursor.fetchone()
		#print row
		self._closeDBAndCursor(cursor)
		return row

	def setFiche(self, values, ficheId):
		cursor = self._openDBWithCursor()
		cursor.execute("update fiches set work = %s, firstWordPage = %s, lastWordPage = %s, matrixNumber = %s, matrixSector = %s, editor = %s, comment = %s where fiche = %s", (self._nvl(values[0]), self._nvl(values[1]), self._nvl(values[2]), self._nvl(values[3]), self._nvl(values[4]), self._nvl(values[5]), self._nvl(values[6]), ficheId))
		self._closeDBAndCursor(cursor)

	def getPageAndLineForFiche(self, ficheId):
		page = ""
		pageComment = ""
		line = ""
		lineComment = ""
		cursor = self._openDBWithCursor()
		cursor.execute("select page, comment from pages where fiche = %s", (ficheId))
		row = cursor.fetchone()
		if row != None:
			page = row[0]
			pageComment = row[1]
		cursor.execute("select line, comment from linesIndex where fiche = %s", (ficheId))
		row = cursor.fetchone()
		if row != None:
			line = row[0]
			lineComment = row[1]
		self._closeDBAndCursor(cursor)
		return (page, pageComment, line, lineComment)

	def setPageAndLineForFiche(self, (page, pageComment, line, lineComment), ficheId):
		cursor = self._openDBWithCursor()
		cursor.execute("select page from pages where fiche = %s", (ficheId))
		row = cursor.fetchone()
		hasPage = row != None
		cursor.execute("select line from linesIndex where fiche = %s", (ficheId))
		row = cursor.fetchone()
		hasLine = row != None
		if hasPage:
			if page != "":
				cursor.execute("update pages set page = %s, comment = %s where fiche = %s", (page, self._nvl(pageComment), ficheId))
			else:
				cursor.execute("delete from pages where fiche = %s", (ficheId))
		elif page != "":
			cursor.execute("insert into pages values (%s, %s, %s)", (ficheId, page, self._nvl(pageComment)))
		if hasLine:
			if line != "":
				cursor.execute("update linesIndex set line = %s, comment = %s where fiche = %s", (line, self._nvl(lineComment), ficheId))
			else:
				cursor.execute("delete from linesIndex where fiche = %s", (ficheId))
		elif line != "":
			cursor.execute("insert into linesIndex values (%s, %s, %s)", (ficheId, line, self._nvl(lineComment)))
		self._closeDBAndCursor(cursor)

	def getSecondaryIndicesForFiche(self, ficheId):
		res0 = [""]*11
		res1 = [""]*2
		cursor = self._openDBWithCursor()
		cursor.execute("select * from fiche_entries where fiche = %s", (ficheId))
		row = cursor.fetchone()
		if row != None:
			res0 = list(row)[1:]
		cursor.execute("select entry, comment from text_entries where fiche = %s", (ficheId))
		row = cursor.fetchone()
		if row != None:
			res1 = list(row)
		self._closeDBAndCursor(cursor)
		return res0 + res1

	def setSecondaryIndicesForFiche(self, (ficheEntry, textEntry, textEntryComment), ficheId):
		cursor = self._openDBWithCursor()
		cursor.execute("select count(*) from fiche_entries where fiche = %s", (ficheId))
		if cursor.fetchone()[0] > 0:
			cursor.execute("update fiche_entries set pageNo = %s, lineNo = %s, entryBegin = %s, entryBeginLine = %s, entryBeginWord = %s, entryBeginChar = %s, entryEnd = %s, entryEndLine = %s, entryEndWord = %s, entryEndChar = %s, comment = %s where fiche = %s", tuple([self._nvl(el) for el in ficheEntry] + [ficheId]))
		elif ficheEntry != tuple([""]*11):
			cursor.execute("insert into fiche_entries values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", tuple([ficheId] + [self._nvl(a) for a in ficheEntry]))
		cursor.execute("select count(*) from text_entries where fiche = %s", (ficheId))
		if cursor.fetchone()[0] > 0:
			if textEntry == "":
				cursor.execute("delete from text_entries where fiche = %s", (ficheId))
			else:
				cursor.execute("update text_entries set entry = %s, comment = %s where fiche = %s", (textEntry, self._nvl(textEntryComment), ficheId))
		elif textEntry != "":
			cursor.execute("insert into text_entries values (%s, %s, %s)", (ficheId, textEntry, self._nvl(textEntryComment)))
		self._closeDBAndCursor(cursor)

	def getEntriesRegister(self):
		cursor = self._openDBWithCursor()
		cursor.execute("select distinct entry from actual_entries order by entry")
		res = [_("Entry unknown")]
		row = cursor.fetchone()
		while row != None:
			res.append(str(row[0]))
			row = cursor.fetchone()
		self._closeDBAndCursor(cursor)
		return res

	def getWorksForEntry(self, entry):
		cursor = self._openDBWithCursor()
		print entry, type(entry)
		if isinstance(entry, unicode) and entry == _("Entry unknown"): # TODO: NOTE tu i w ponizszych metodach, bo _ zamienia na unicode
			cursor.execute("select distinct work from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) order by work")
		else:
			cursor.execute("select distinct work from fiches f, actual_entries e where f.fiche = e.fiche and entry = %s order by work", (entry))
		res = [_('Work unknown')]
		row = cursor.fetchone()
		while row != None:
			if row[0] != None:
				res.append(str(row[0]))
			row = cursor.fetchone()
		self._closeDBAndCursor(cursor)
		return res

	def getPagesForWork(self, entry, work):
		cursor = self._openDBWithCursor()
		if isinstance(work, unicode) and work == _("Work unknown"):
			if isinstance(entry, unicode) and entry == _("Entry unknown"):
				cursor.execute("select distinct page from fiches f, pages p where f.fiche = p.fiche and work is null and not exists (select * from actual_entries e where f.fiche = e.fiche) order by page")
			else:
				cursor.execute("select distinct page from fiches f, pages p, actual_entries e where f.fiche = p.fiche and p.fiche = e.fiche and entry = %s and work is null order by page", (entry))
		else:
			if isinstance(entry, unicode) and entry == _("Entry unknown"):
				cursor.execute("select distinct page from fiches f, pages p where f.fiche = p.fiche and work = %s and not exists (select * from actual_entries e where f.fiche = e.fiche) order by page", (work))
			else:
				cursor.execute("select distinct page from fiches f, pages p, actual_entries e where f.fiche = p.fiche and p.fiche = e.fiche and entry = %s and work = %s order by page", (entry, work))
		res = [_("Page unknown")]
		row = cursor.fetchone()
		while row != None:
			res.append(str(row[0]))
			row = cursor.fetchone()
		self._closeDBAndCursor(cursor)
		return res

	def getLinesForPage(self, entry, work, page):
		cursor = self._openDBWithCursor()
		if isinstance(page, unicode) and page == _("Page unknown"):
			if isinstance(work, unicode) and work == _("Work unknown"):
				if isinstance(entry, unicode) and entry == _("Entry unknown"):
					cursor.execute("select distinct line from fiches f, linesIndex l where f.fiche = l.fiche and work is null and not exists (select * from actual_entries e where f.fiche = e.fiche) and not exists (select * from pages p where l.fiche = p.fiche) order by line")
				else:
					cursor.execute("select distinct line from fiches f, linesIndex l, actual_entries e where f.fiche = l.fiche and f.fiche = e.fiche and entry = %s and work is null and not exists (select * from pages p where l.fiche = p.fiche) order by line", (entry))
			else:
				if isinstance(entry, unicode) and entry == _("Entry unknown"):
					cursor.execute("select distinct line from fiches f, linesIndex l where f.fiche = l.fiche and work = %s and not exists (select * from actual_entries e where f.fiche = e.fiche) and not exists (select * from pages p where l.fiche = p.fiche) order by line", (work))
				else:
					cursor.execute("select distinct line from fiches f, linesIndex l, actual_entries e where f.fiche = l.fiche and f.fiche = e.fiche and entry = %s and work = %s and not exists (select * from pages p where l.fiche = p.fiche) order by line", (entry, work))
		else:
			if isinstance(work, unicode) and work == _("Work unknown"):
				if isinstance(entry, unicode) and entry == _("Entry unknown"):
					cursor.execute("select distinct line from fiches f, linesIndex l, pages p where f.fiche = p.fiche and p.fiche = l.fiche and page = %s and work is null and not exists (select * from actual_entries e where f.fiche = e.fiche) order by line", (page))
				else:
					cursor.execute("select distinct line from fiches f, linesIndex l, pages p, actual_entries e where f.fiche = p.fiche and p.fiche = l.fiche and p.fiche = e.fiche and page = %s and entry = %s and work is null order by line", (page, entry))
			else:
				if isinstance(entry, unicode) and entry == _("Entry unknown"):
					cursor.execute("select distinct line from fiches f, linesIndex l, pages p where f.fiche = p.fiche and p.fiche = l.fiche and page = %s and work = %s and not exists (select * from actual_entries e where f.fiche = e.fiche) order by line", (page, work))
				else:
					cursor.execute("select distinct line from fiches f, linesIndex l, pages p, actual_entries e where f.fiche = p.fiche and p.fiche = l.fiche and p.fiche = e.fiche and page = %s and entry = %s and work = %s order by line", (page, entry, work))
		res = [_("Line unknown")]
		row = cursor.fetchone()
		while row != None:
			res.append(str(row[0]))
			row = cursor.fetchone()
		self._closeDBAndCursor(cursor)
		return res

	def getFichesForLine(self, entry, work, page, line):
		cursor = self._openDBWithCursor()
		if isinstance(line, unicode) and line == _("Line unknown"):
			if isinstance(page, unicode) and page == _("Page unknown"):
				if isinstance(work, unicode) and work == _("Work unknown"):
					if isinstance(entry, unicode) and entry == _("Entry unknown"):
						cursor.execute("select * from fiches where 1 = 2")
					else:
						cursor.execute("select f.fiche from fiches f, actual_entries e where f.fiche = e.fiche and entry = %s and work is null and not exists (select * from pages p where f.fiche = p.fiche) and not exists (select * from linesIndex l where l.fiche = f.fiche)", (entry))
				else:
					if isinstance(entry, unicode) and entry == _("Entry unknown"):
						cursor.execute("select f.fiche from fiches f where work = %s and not exists (select * from actual_entries e where f.fiche = e.fiche) and not exists (select * from pages p where f.fiche = p.fiche) and not exists (select * from linesIndex l where l.fiche = f.fiche)", (work))
					else:
						cursor.execute("select f.fiche from fiches f, actual_entries e where f.fiche = e.fiche and entry = %s and work = %s and not exists (select * from pages p where f.fiche = p.fiche) and not exists (select * from linesIndex l where l.fiche = f.fiche)", (entry, work))
			else:
				if isinstance(work, unicode) and work == _("Work unknown"):
					if isinstance(entry, unicode) and entry == _("Entry unknown"):
						cursor.execute("select f.fiche from fiches f, pages p where f.fiche = p.fiche and page = %s and work is null and not exists (select * from actual_entries e where f.fiche = e.fiche) and not exists (select * from linesIndex l where l.fiche = f.fiche)", (page))
					else:
						cursor.execute("select f.fiche from fiches f, pages p, actual_entries e where f.fiche = p.fiche and p.fiche = e.fiche and page = %s and entry = %s and work is null and not exists (select * from linesIndex l where l.fiche = f.fiche)", (page, entry))
				else:
					if isinstance(entry, unicode) and entry == _("Entry unknown"):
						cursor.execute("select f.fiche from fiches f, pages p where f.fiche = p.fiche and page = %s and work = %s and not exists (select * from actual_entries e where f.fiche = e.fiche) and not exists (select * from linesIndex l where l.fiche = f.fiche)", (page, work))
					else:
						cursor.execute("select f.fiche from fiches f, pages p, actual_entries e where f.fiche = p.fiche and p.fiche = e.fiche and page = %s and entry = %s and work = %s and not exists (select * from linesIndex l where l.fiche = f.fiche)", (page, entry, work))
		else:
			if isinstance(page, unicode) and page == _("Page unknown"):
				if isinstance(work, unicode) and work == _("Work unknown"):
					if isinstance(entry, unicode) and entry == _("Entry unknown"):
						cursor.execute("select l.fiche from fiches f, linesIndex l where f.fiche = l.fiche and work is null and not exists (select * from actual_entries e where f.fiche = e.fiche) and not exists (select * from pages p where l.fiche = p.fiche) and line = %s", (line))
					else:
						cursor.execute("select l.fiche from fiches f, linesIndex l, actual_entries e where f.fiche = l.fiche and f.fiche = e.fiche and entry = %s and work is null and not exists (select * from pages p where l.fiche = p.fiche) and line = %s", (entry, line))
				else:
					if isinstance(entry, unicode) and entry == _("Entry unknown"):
						cursor.execute("select l.fiche from fiches f, linesIndex l where f.fiche = l.fiche and work = %s and not exists (select * from actual_entries e where f.fiche = e.fiche) and not exists (select * from pages p where l.fiche = p.fiche) and line = %s", (work, line))
					else:
						cursor.execute("select l.fiche from fiches f, linesIndex l, actual_entries e where f.fiche = l.fiche and f.fiche = e.fiche and entry = %s and work = %s and not exists (select * from pages p where l.fiche = p.fiche) and line = %s", (entry, work, line))
			else:
				if isinstance(work, unicode) and work == _("Work unknown"):
					if isinstance(entry, unicode) and entry == _("Entry unknown"):
						cursor.execute("select l.fiche from fiches f, linesIndex l, pages p where f.fiche = p.fiche and p.fiche = l.fiche and page = %s and work is null and not exists (select * from actual_entries e where f.fiche = e.fiche) and line = %s", (page, line))
					else:
						cursor.execute("select l.fiche from fiches f, linesIndex l, pages p, actual_entries e where f.fiche = p.fiche and p.fiche = l.fiche and p.fiche = e.fiche and page = %s and entry = %s and work is null and line = %s", (page, entry, line))
				else:
					if isinstance(entry, unicode) and entry == _("Entry unknown"):
						cursor.execute("select l.fiche from fiches f, linesIndex l, pages p where f.fiche = p.fiche and p.fiche = l.fiche and page = %s and work = %s and not exists (select * from actual_entries e where f.fiche = e.fiche) and line = %s", (page, work, line))
					else:
						cursor.execute("select l.fiche from fiches f, linesIndex l, pages p, actual_entries e where f.fiche = p.fiche and p.fiche = l.fiche and p.fiche = e.fiche and page = %s and entry = %s and work = %s and line = %s", (page, entry, work, line))
		res = []
		row = cursor.fetchone()
		while row != None:
			res.append(row[0])
			row = cursor.fetchone()
		self._closeDBAndCursor(cursor)
		return res

	def getBookmarksTaskRegister(self):
		reg = TaskRegister(None, None, empty=True)
		cursor = self._openDBWithCursor()
		cursor.execute("select fiche from fiches where bookmark is not null order by position")
		row = cursor.fetchone()
		while row != None:
			reg.append(Fiche(row[0], row[0]))
			row = cursor.fetchone()
		self._closeDBAndCursor(cursor)
		return reg

	#def getCommentTaskRegister(self):
	#	reg = TaskRegister(None, None, emtpy=True)
	#	cursor = self._openDBWithCursor()
	#	cursor.execute("select fiche from fiches where comment is not null and comment <> '' order by position")
	#	row = cursor.fetchone()
	#	while row != None:
	#		reg.append(Fiche(row[0], row[0]))
	#		row = cursor.fetchone()
	#	self._closeDBAndCursor(cursor)
	#	return reg

