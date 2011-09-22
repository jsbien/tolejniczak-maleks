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
from maleks.i18n import _
from maleks.maleks.useful import ustr

class DBCommon(object):

	def _nvl(self, obj):
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

	def _openDBWithCursor(self):
		self.__conn = MySQLdb.connect(user=self.__user, passwd=self.__passwd, db=self.__db, use_unicode=False, init_command="SET NAMES 'utf8'",charset='utf8')
		return self.__conn.cursor()

	def _closeDBAndCursor(self, cursor):
		cursor.close()
		self.__conn.commit()
		self.__conn.close()

class DBEntryController(DBCommon):

	def __init__(self, config):
		DBCommon.__init__(self, config)

	def __firstEntry(self, cursor, entry):
		return int(self.__single(cursor, "select min(position) from fiches f, actual_entries e where f.fiche = e.fiche and entry = %s", (entry)))

	def __lastEntry(self, cursor, entry):
		return int(self.__single(cursor, "select max(position) from fiches f, actual_entries e where f.fiche = e.fiche and entry = %s", (entry)))

	def __entryLimits(self, cursor, entry):
		return (self.__firstEntry(cursor, entry), self.__lastEntry(cursor, entry))

	def __single(self, cursor, query, pars):
		cursor.execute(query, pars)
		row = cursor.fetchone()
		if row == None:
			return None
		else:
			return row[0]

	def getEntriesCount(self, entry):
		if ustr(entry) in [_("First fiche"), _("Last fiche")]:
			return 1
		cursor = self._openDBWithCursor()
		(first, last) = self.__entryLimits(cursor, entry)
		res = int(self.__single(cursor, "select count(*) from fiches f where position >= %s and position <= %s and not exists (select * from actual_entries e where f.fiche = e.fiche and entry <> %s)", (first, last, entry)))
		self._closeDBAndCursor(cursor)
		return res

	def getFicheForEntryPosition(self, entry, pos):
		cursor = self._openDBWithCursor()
		if ustr(entry) == _("First fiche"):
			res = self.__single(cursor, "select fiche from fiches order by position limit 1", ())
		elif ustr(entry) == _("Last fiche"):
			res = self.__single(cursor, "select fiche from fiches order by position desc limit 1", ())
		else:
			(first, last) = self.__entryLimits(cursor, entry)
			res = self.__single(cursor, "select fiche from fiches f where position >= %s and position <= %s and not exists (select * from actual_entries e where f.fiche = e.fiche and entry <> %s) order by position limit %s,1", (first, last, entry, pos))
		self._closeDBAndCursor(cursor)
		return res

	# TODO: C w dziurach ktore sa na poczatku i koncu jest pierwsza i ostatnia fiszka!
	def getGapCount(self, before, after):
		cursor = self._openDBWithCursor()
		if before == None and after == None:
			res = int(self.__single(cursor, "select count(*) from fiches", ()))
		elif before == None:
			num = self.__firstEntry(cursor, after)
			res = int(self.__single(cursor, "select count(*) from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position < %s", (num)))
		elif after == None:
			num = self.__lastEntry(cursor, before)
			res = int(self.__single(cursor, "select count(*) from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s", (num)))
		else:
			numa = self.__firstEntry(cursor, after)
			numb = self.__lastEntry(cursor, before)
			res = int(self.__single(cursor, "select count(*) from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s and position < %s", (numb, numa)))
		self._closeDBAndCursor(cursor)
		return res

	def getFicheForGapPosition(self, before, after, pos):
		cursor = self._openDBWithCursor()
		if before == None and after == None:
			res = self.__single(cursor, "select fiche from fiches order by position limit %s,1", (pos))
		elif before == None:
			num = self.__firstEntry(cursor, after)
			res = self.__single(cursor, "select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position < %s order by position limit %s,1", (num, pos))
		elif after == None:
			num = self.__lastEntry(cursor, before)
			res = self.__single(cursor, "select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s order by position limit %s,1", (num, pos))
		else:
			numa = self.__firstEntry(cursor, after)
			numb = self.__lastEntry(cursor, before)
			res = self.__single(cursor, "select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s and position < %s order by position limit %s,1", (numb, numa, pos))
		self._closeDBAndCursor(cursor)
		return res

	def getEntriesRegisterWithGaps(self):
		cursor = self._openDBWithCursor()
		#cursor.execute("select distinct entry from fiches f, actual_entries e where f.fiche = e.fiche and position = 0")
		cursor.execute("select min(position) from fiches")
		minPos = int(cursor.fetchone()[0])
		cursor.execute("select distinct entry from fiches f, actual_entries e where f.fiche = e.fiche and position = %s", (minPos))
		if cursor.fetchone() == None:
			res = [_("First fiche")]
		else:
			res = []
		cursor.execute("select distinct entry from fiches f, actual_entries e where f.fiche = e.fiche order by position")
		row = cursor.fetchone()
		while row != None:
			res.append(str(row[0]))
			row = cursor.fetchone()
		prev = ""
		cursor.execute("select entry from actual_entries where fiche = (select fiche from fiches where position <> %s order by position desc limit 1)", (minPos))
		if cursor.fetchone() == None:
			res.append(_("Last fiche"))
		prev = None
		newres = []
		for el in res:
			if prev == None:
				prev = el
				newres.append(el)
				continue
			if ustr(prev) == _("First fiche") and ustr(el) == _("Last fiche"):
				cursor.execute("select count(*) from fiches f")
				num = int(cursor.fetchone()[0])
				num -= 2
				if num > 0:
					newres.append((num, None, None))
				newres.append(el)
			elif ustr(prev) == _("First fiche"):
				cursor.execute("select count(*) from fiches where position < (select min(position) from fiches f, actual_entries e where f.fiche = e.fiche and entry = %s)", (el))
				num = int(cursor.fetchone()[0])
				num -= 1
				if num > 0:
					newres.append((num, None, el))
				newres.append(el)
			elif ustr(el) == _("Last fiche"):
				cursor.execute("select count(*) from fiches where position > (select max(position) from fiches f, actual_entries e where f.fiche = e.fiche and entry = %s)", (prev))
				num = int(cursor.fetchone()[0])
				num -= 1
				if num > 0:
					newres.append((num, prev, None))
				newres.append(el)
			else:
				cursor.execute("select count(*) from fiches where position > (select max(position) from fiches f, actual_entries e where f.fiche = e.fiche and entry = %s) and position < (select min(position) from fiches f, actual_entries e where f.fiche = e.fiche and entry = %s)", (prev, el))
				num = int(cursor.fetchone()[0])
				if num > 0:
					newres.append((num, prev, el))
				newres.append(el)
			prev = el
		self._closeDBAndCursor(cursor)
		return newres

	def __smartLimit(self, cursor, query, pars, limitStart, atleast, limit):
		if atleast != None:
			cursor.execute(query.replace("#", "count(*)"), pars)
			num = int(cursor.fetchone()[0])
			if limitStart + atleast > num:
				limitStart = num - atleast
		#print query.replace("#", "fiche") + " limit " + str(limitStart) + "," + str(limit), pars
		#:cursor.execute(query.replace("#", "fiche") + " limit " + str(limitStart + limit) + ",1", pars)
		#:row = cursor.fetchone()
		#:if row != None:
		#:	next = str(row[0])
		#:else:
		next = None
		cursor.execute(query.replace("#", "fiche") + " limit " + str(limitStart) + "," + str(limit), pars)
		return (limitStart, next)

	def getFichesForGap(self, before, after, limit, limitStart=0, atleast=None):
		cursor = self._openDBWithCursor()
		res = []
		#print ":", before, after
		if before == None and after == None:
			#cursor.execute("select fiche from fiches order by position")
			(limitStart, next) = self.__smartLimit(cursor, "select # from fiches order by position", (), limitStart, atleast, limit) 
		elif before == None:
			cursor.execute("select min(position) from fiches f, actual_entries e where f.fiche = e.fiche and entry = %s", (after))
			row = cursor.fetchone()
			num = int(row[0])
			#cursor.execute("select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position < %s order by position", (num))
			(limitStart, next) = self.__smartLimit(cursor, "select # from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position < %s order by position", (num), limitStart, atleast, limit)
		elif after == None:
			cursor.execute("select max(position) from fiches f, actual_entries e where f.fiche = e.fiche and entry = %s", (before))
			row = cursor.fetchone()
			num = int(row[0])
			#print num
			#cursor.execute("select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s order by position", (num))
			(limitStart, next) = self.__smartLimit(cursor, "select # from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s order by position", (num), limitStart, atleast, limit)
		else:
			cursor.execute("select min(position) from fiches f, actual_entries e where f.fiche = e.fiche and entry = %s", (after))
			row = cursor.fetchone()
			numa = int(row[0])
			cursor.execute("select max(position) from fiches f, actual_entries e where f.fiche = e.fiche and entry = %s", (before))
			row = cursor.fetchone()
			numb = int(row[0])
			#cursor.execute("select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s and position < %s order by position", (numb, numa))
			(limitStart, next) = self.__smartLimit(cursor, "select # from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s and position < %s order by position", (numb, numa), limitStart, atleast, limit)
		row = cursor.fetchone()
		while row != None:
			#print row
			res.append(str(row[0]))
			row = cursor.fetchone()
		self._closeDBAndCursor(cursor)
		return (res, limitStart, next)

	def getFichesForEntry(self, entry, limit, limitStart=0, atleast=None):
		res = []
		next = None
		cursor = self._openDBWithCursor()
		if ustr(entry) == _("First fiche"):
			#cursor.execute("select fiche from fiches where position = 0") TODO: NOTE problem z autoincrement
			cursor.execute("select fiche from fiches order by position limit 1")
		elif ustr(entry) == _("Last fiche"):
			cursor.execute("select fiche from fiches order by position desc limit 1")
		else:
			cursor.execute("select min(position) from fiches f, actual_entries e where f.fiche = e.fiche and entry = %s", (entry))
			first = int(cursor.fetchone()[0])
			cursor.execute("select max(position) from fiches f, actual_entries e where f.fiche = e.fiche and entry = %s", (entry))
			last = int(cursor.fetchone()[0])
			(limitStart, next) = self.__smartLimit(cursor, "select # from fiches f where position >= %s and position <= %s and not exists (select * from actual_entries e where f.fiche = e.fiche and entry <> %s) order by position", (first, last, entry), limitStart, atleast, limit)
		row = cursor.fetchone()
		while row != None:			
			res.append(str(row[0]))
			row = cursor.fetchone()
		self._closeDBAndCursor(cursor)
		return (res, limitStart, next)

	def getFichesForEntryForFiche(self, entry, ficheId, limit):
		cursor = self._openDBWithCursor()
		res = []
		rownum = 0
		next = None
		if ustr(entry) == _("First fiche"):
			cursor.execute("select fiche from fiches order by position limit 1")
		elif ustr(entry) == _("Last fiche"):
			cursor.execute("select fiche from fiches order by position desc limit 1")
		else:
			cursor.execute("select min(position) from fiches f, actual_entries e where f.fiche = e.fiche and entry = %s", (entry))
			first = int(cursor.fetchone()[0])
			cursor.execute("select max(position) from fiches f, actual_entries e where f.fiche = e.fiche and entry = %s", (entry))
			last = int(cursor.fetchone()[0])
			cursor.execute("set @row = -1")
			cursor.execute("select a.row from (select @row := @row + 1 as row, fiche from fiches f where position >= %s and position <= %s and not exists (select * from actual_entries e where f.fiche = e.fiche and entry <> %s) order by position) a where a.fiche = %s", (first, last, entry, ficheId))
			rownum = cursor.fetchone()[0]
			#:cursor.execute("select fiche from fiches f where position >= %s and position <= %s and not exists (select * from actual_entries e where f.fiche = e.fiche and entry <> %s) order by position limit %s,%s", (first, last, entry, rownum + limit, 1))
			#:row = cursor.fetchone()
			#:if row != None:
			#:	next = str(row[0])
			cursor.execute("select fiche from fiches f where position >= %s and position <= %s and not exists (select * from actual_entries e where f.fiche = e.fiche and entry <> %s) order by position limit %s,%s", (first, last, entry, rownum, limit))
		row = cursor.fetchone()
		while row != None:			
			res.append(str(row[0]))
			row = cursor.fetchone()
		self._closeDBAndCursor(cursor)
		return (res, rownum, next)
		
	def __smartQuery(self, cursor, query, pars, ficheId, ind, limit):
		cursor.execute("set @row = -1")
		cursor.execute("select a.row from (" + query.replace("#", "@row := @row + 1 as row,") + ") a where a.fiche = %s", pars + tuple([ficheId]))
		rownum = cursor.fetchone()[0]
		#:cursor.execute(query.replace("#", "") + " limit %s,%s", pars + (limit + ind, 1))
		#:row = cursor.fetchone()
		#:if row != None:
		#:	next = str(row[0])
		#:else:
		next = None
		cursor.execute(query.replace("#", "") + " limit %s,%s", pars + (ind, limit))
		return (rownum, next)

	def getFichesForGapForFiche(self, before, after, ficheId, limit):
		cursor = self._openDBWithCursor()
		res = []
		if before == None and after == None:
			(rownum, next) = self.__smartQuery(cursor, "select # fiche from fiches order by position", (), ficheId, 0, limit)
		elif before == None:
			cursor.execute("select min(position) from fiches f, actual_entries e where f.fiche = e.fiche and entry = %s", (after))
			row = cursor.fetchone()
			num = int(row[0])
			(rownum, next) = self.__smartQuery(cursor, "select # fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position < %s order by position", tuple([num]), ficheId, 0, limit)
		elif after == None:
			cursor.execute("select max(position) from fiches f, actual_entries e where f.fiche = e.fiche and entry = %s", (before))
			row = cursor.fetchone()
			num = int(row[0])
			(rownum, next) = self.__smartQuery(cursor, "select # fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s order by position", tuple([num]), ficheId, 0, limit)
		else:
			cursor.execute("select min(position) from fiches f, actual_entries e where f.fiche = e.fiche and entry = %s", (after))
			row = cursor.fetchone()
			numa = int(row[0])
			cursor.execute("select max(position) from fiches f, actual_entries e where f.fiche = e.fiche and entry = %s", (before))
			row = cursor.fetchone()
			numb = int(row[0])
			(rownum, next) = self.__smartQuery(cursor, "select # fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s and position < %s order by position", (numb, numa), ficheId, 0, limit)
		row = cursor.fetchone()
		while row != None:
			res.append(str(row[0]))
			row = cursor.fetchone()
		self._closeDBAndCursor(cursor)
		return (res, rownum, next)

	def hasFiche(self, element, ficheId):
		cursor = self._openDBWithCursor()
		if isinstance(element, tuple):
			(num, before, after) = element
			if before == None and after == None:
				cursor.execute("select fiche from fiches where fiche = %s", (ficheId))
			elif before == None:
				cursor.execute("select position from fiches f, actual_entries e where f.fiche = e.fiche and entry = %s", (after))
				row = cursor.fetchone()
				num = int(row[0])
				#print "\t", "a", num, ficheId
				cursor.execute("select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position < %s and fiche = %s", (num, ficheId))
			elif after == None:
				cursor.execute("select position from fiches f, actual_entries e where f.fiche = e.fiche and entry = %s", (before))
				row = cursor.fetchone()
				num = int(row[0])
				#print "\t", "b", num, ficheId
				cursor.execute("select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s and fiche = %s", (num, ficheId))
			else:
				cursor.execute("select position from fiches f, actual_entries e where f.fiche = e.fiche and entry = %s", (after))
				row = cursor.fetchone()
				numa = int(row[0])
				cursor.execute("select position from fiches f, actual_entries e where f.fiche = e.fiche and entry = %s", (before))
				row = cursor.fetchone()
				numb = int(row[0])
				#print "\t", numa, numb, ficheId
				cursor.execute("select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s and position < %s and fiche = %s", (numb, numa, ficheId))
		else:
			if ustr(element) == _("First fiche"):
				#print "\t", "first"
				cursor.execute("select a.fiche from (select f.fiche from fiches f order by f.position limit 1) a where a.fiche = %s", (ficheId))
			elif ustr(element) == _("Last fiche"):
				#print "\t", "last"
				cursor.execute("select a.fiche from (select f.fiche from fiches f order by f.position desc limit 1) a where a.fiche = %s", (ficheId))
			else:
				cursor.execute("select min(position) from fiches f, actual_entries e where f.fiche = e.fiche and entry = %s", (element))
				first = int(cursor.fetchone()[0])
				cursor.execute("select max(position) from fiches f, actual_entries e where f.fiche = e.fiche and entry = %s", (element))
				last = int(cursor.fetchone()[0])
				#print "\t", first, last, element, ficheId
				cursor.execute("select fiche from fiches f where position >= %s and position <= %s and not exists (select * from actual_entries e where f.fiche = e.fiche and entry <> %s) and fiche = %s", (first, last, element, ficheId))
		row = cursor.fetchone()
		#print row
		self._closeDBAndCursor(cursor)
		return row != None

