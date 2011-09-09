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

import MySQLdb
import _mysql_exceptions
from maleks.i18n import _
from maleks.maleks.registers import TaskRegister
from maleks.maleks.fiche import Fiche

class DBController(object):

	def __nvl(self, obj):
		if obj == "":
			return None
		return obj

	def __init__(self, config):
		self.__user = config.read('dbuser', '')
		self.__globalUser = self.__user
		self.__passwd = config.read('dbpass', '')
		self.__globalPasswd = self.__passwd
		self.__db = config.read('db', '')
		self.__globalDb = self.__db
		self.__conn = None

	def setPerDocumentConnection(self, db, user, passwd):
		self.__user = user if user != None else self.__globalUser
		self.__passwd = passwd if passwd != None else self.__globalPasswd
		self.__db = db if db != None else self.__globalDb

	def valid(self):
		return self.__user != '' and self.__passwd != '' and self.__db != ''

	def __openDBWithCursor(self):
		self.__conn = MySQLdb.connect(user=self.__user, passwd=self.__passwd, db=self.__db, use_unicode=False, init_command="SET NAMES 'utf8'",charset='utf8')
		return self.__conn.cursor()

	def __closeDBAndCursor(self, cursor):
		cursor.close()
		self.__conn.commit()
		self.__conn.close()

	def addFicheToFichesIndex(self, ficheId):
		cursor = self.__openDBWithCursor()
		cursor.execute("insert into fiches values (null, %s, null, null, null)", (ficheId))
		self.__closeDBAndCursor(cursor)

	def bookmarkFiche(self, ficheId):
		cursor = self.__openDBWithCursor()
		cursor.execute("update fiches set bookmark = sysdate() where fiche = %s", (ficheId))
		self.__closeDBAndCursor(cursor)

	def addFicheToEntriesIndex(self, ficheId, entry):
		cursor = self.__openDBWithCursor()
		try:
			cursor.execute("insert into actual_entries values (%s, %s, null)", (ficheId, entry))
			cursor.execute("insert into original_entries values (%s, %s, null)", (ficheId, entry))
		except _mysql_exceptions.IntegrityError:
			self.__closeDBAndCursor(cursor)
			return _('Fiche already indexed')
		#print cursor.rowcount
		self.__closeDBAndCursor(cursor)
		return None

	def addFicheToPrefixesIndex(self, ficheId, entry):
		cursor = self.__openDBWithCursor()
		try:
			cursor.execute("insert into entry_prefixes values (%s, %s, null)", (ficheId, entry))
		except _mysql_exceptions.IntegrityError:
			self.__closeDBAndCursor(cursor)
			return _('Fiche already indexed in entry prefix index')
		self.__closeDBAndCursor(cursor)
		return None

	def getHypothesisForFiche(self, ficheId, alphabetic):
		cursor = self.__openDBWithCursor()
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
		self.__closeDBAndCursor(cursor)
		if row == None:
			return None
		else:
			return row[0]

	def getEntriesForFiche(self, ficheId):
		actual = ""
		actualComment = ""
		original = ""
		originalComment = ""
		cursor = self.__openDBWithCursor()
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
		self.__closeDBAndCursor(cursor)
		return (actual, actualComment, original, originalComment)

	def setEntriesForFiche(self, (actual, actualComment, original, originalComment), ficheId):
		cursor = self.__openDBWithCursor()
		cursor.execute("select entry from actual_entries where fiche = %s", (ficheId))
		row = cursor.fetchone()
		hasActual = row != None
		cursor.execute("select entry from original_entries where fiche = %s", (ficheId))
		row = cursor.fetchone()
		hasOriginal = row != None
		if hasActual:
			if actual != "":
				cursor.execute("update actual_entries set entry = %s, comment = %s where fiche = %s", (actual, self.__nvl(actualComment), ficheId))
			else:
				cursor.execute("delete from actual_entries where fiche = %s", (ficheId))
		elif actual != "":
			cursor.execute("insert into actual_entries values (%s, %s, %s)", (ficheId, actual, self.__nvl(actualComment)))
		if hasOriginal:
			if original != "":
				cursor.execute("update original_entries set entry = %s, comment = %s where fiche = %s", (original, self.__nvl(originalComment), ficheId))
			else:
				cursor.execute("delete from original_entries where fiche = %s", (ficheId))
		elif original != "":
			cursor.execute("insert into original_entries values (%s, %s, %s)", (ficheId, original, self.__nvl(originalComment)))
		self.__closeDBAndCursor(cursor)

	def getFiche(self, ficheId):
		cursor = self.__openDBWithCursor()
		cursor.execute("select work, firstWordPage, lastWordPage, matrixNumber, matrixSector, editor, comment from fiches where fiche = %s", (ficheId))
		row = cursor.fetchone()
		#print row
		self.__closeDBAndCursor(cursor)
		return row

	def setFiche(self, values, ficheId):
		cursor = self.__openDBWithCursor()
		cursor.execute("update fiches set work = %s, firstWordPage = %s, lastWordPage = %s, matrixNumber = %s, matrixSector = %s, editor = %s, comment = %s where fiche = %s", (self.__nvl(values[0]), self.__nvl(values[1]), self.__nvl(values[2]), self.__nvl(values[3]), self.__nvl(values[4]), self.__nvl(values[5]), self.__nvl(values[6]), ficheId))
		self.__closeDBAndCursor(cursor)

	def getBookmarksTaskRegister(self):
		reg = TaskRegister(None, None, empty=True)
		cursor = self.__openDBWithCursor()
		cursor.execute("select fiche from fiches where bookmark is not null order by position")
		row = cursor.fetchone()
		while row != None:
			reg.append(Fiche(row[0], row[0]))
			row = cursor.fetchone()
		self.__closeDBAndCursor(cursor)
		return reg

	#def getCommentTaskRegister(self):
	#	reg = TaskRegister(None, None, emtpy=True)
	#	cursor = self.__openDBWithCursor()
	#	cursor.execute("select fiche from fiches where comment is not null and comment <> '' order by position")
	#	row = cursor.fetchone()
	#	while row != None:
	#		reg.append(Fiche(row[0], row[0]))
	#		row = cursor.fetchone()
	#	self.__closeDBAndCursor(cursor)
	#	return reg

