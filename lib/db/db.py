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
from djvusmooth.i18n import _

class DBController(object):

	def __init__(self, config):
		self.__user = config.read('dbuser', '')
		self.__passwd = config.read('dbpass', '')
		self.__db = config.read('db', '')
		self.__conn = None

	def valid(self):
		return self.__user != '' and self.__passwd != '' and self.__db != ''

	def __openDBWithCursor(self):
		self.__conn = MySQLdb.connect(user=self.__user, passwd=self.__passwd, db=self.__db, use_unicode=False, init_command="SET NAMES 'utf8'",charset='utf8')
		return self.__conn.cursor()

	def __closeDBAndCursor(self, cursor):
		cursor.close()
		self.__conn.commit()
		self.__conn.close()

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

	def getHyphotesisForFiche(self, ficheId):
		cursor = self.__openDBWithCursor()
		cursor.execute("select entry_hypothesis from hypotheses where fiche = %s", (ficheId))
		row = cursor.fetchone()
		self.__closeDBAndCursor(cursor)
		if row == None:
			return None
		else:
			return row[0]

