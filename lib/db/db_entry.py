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
		
INF = 10000000000

class DBEntryController(DBCommon):

	def __init__(self, config):
		DBCommon.__init__(self, config)

	def __firstEntry(self, cursor, entry):
		cursor.execute("select max(position) from fiches f, actual_entries e where f.fiche = e.fiche and entry < %s", (entry))
		row = cursor.fetchone()
		if row == None or row[0] == None:
			maxPrev = -1
		else:
			maxPrev = int(row[0])
		cursor.execute("select min(position) from fiches f, actual_entries e where f.fiche = e.fiche and entry = %s and position > %s", (entry, maxPrev))
		row = cursor.fetchone()
		if row == None or row[0] == None:
			return INF # TODO: A lepiej; 100 mld fiszek starczy?
		else:
			return int(row[0])

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
		cursor = self._openDBWithCursor()
		##if ustr(entry) == _("First fiche"):
		##	first = self.__single(cursor, "select fiche from fiches order by position limit 1")
		##	return (first, first, 1)
		##elif ustr(entry) == _("Last fiche"):
		##	last = self.__single(cursor, "select fiche from fiches order by position desc limit 1")
		##	return (last, last, 1)
		(firstpos, lastpos) = self.__entryLimits(cursor, entry)
		#&res = int(self.__single(cursor, "select count(*) from fiches f where position >= %s and position <= %s and not exists (select * from actual_entries e where f.fiche = e.fiche and entry <> %s)", (firstpos, lastpos, entry)))
		res = int(self.__single(cursor, "select count(*) from fiches f where (position >= %s and position <= %s and not exists (select * from actual_entries e where f.fiche = e.fiche and entry <> %s)) or ((position < %s or position > %s) and exists (select * from actual_entries e where e.fiche = f.fiche and entry = %s))", (firstpos, lastpos, entry, firstpos, lastpos, entry)))
		first = self.__single(cursor, "select fiche from fiches where position = %s", (firstpos))
		last = self.__single(cursor, "select fiche from fiches where position = %s", (lastpos))
		self._closeDBAndCursor(cursor)
		return (first, last, res)

	def getFicheForEntryPosition(self, entry, pos):
		cursor = self._openDBWithCursor()
		##if ustr(entry) == _("First fiche"):
		##	res = self.__single(cursor, "select fiche from fiches order by position limit 1", ())
		##elif ustr(entry) == _("Last fiche"):
		##	res = self.__single(cursor, "select fiche from fiches order by position desc limit 1", ())
		##else:
		(first, last) = self.__entryLimits(cursor, entry)
		#&res = self.__single(cursor, "select fiche from fiches f where position >= %s and position <= %s and not exists (select * from actual_entries e where f.fiche = e.fiche and entry <> %s) order by position limit %s,1", (first, last, entry, pos))
		res = self.__single(cursor, "select fiche from fiches f where (position >= %s and position <= %s and not exists (select * from actual_entries e where f.fiche = e.fiche and entry <> %s)) or ((position < %s or position > %s) and exists (select * from actual_entries e where e.fiche = f.fiche and entry = %s)) order by position limit %s,1", (first, last, entry, first, last, entry, pos))
		self._closeDBAndCursor(cursor)
		return res
		
	def __getPositions(self, cursor, query, pars, left, right, center):
		cursor.execute("set @row = -1")
		leftFiche = self.__single(cursor, "select a.row from (" + query + ") a where a.fiche = %s", pars + tuple([left]))
		cursor.execute("set @row = -1")
		#print pars, left, right, center
		rightFiche = self.__single(cursor, "select a.row from (" + query + ") a where a.fiche = %s", pars + tuple([right]))
		cursor.execute("set @row = -1")
		centerFiche = self.__single(cursor, "select a.row from (" + query + ") a where a.fiche = %s", pars + tuple([center]))
		return (leftFiche, rightFiche, centerFiche)
		
	def getPositionsForFichesForEntry(self, entry, left, right, center):
		cursor = self._openDBWithCursor()
		##if ustr(entry) in [_("First fiche"), _("Last fiche")]: # TODO: D nie powinno sie wydarzyc, ale sprawdzic
		##	return (0, 0, 0)
		##else:
		(first, last) = self.__entryLimits(cursor, entry)
		#&(leftFiche, rightFiche, centerFiche) = self.__getPositions(cursor, "select @row := @row + 1 as row, fiche from fiches f where position >= %s and position <= %s and not exists (select * from actual_entries e where f.fiche = e.fiche and entry <> %s) order by position", (first, last, entry), left, right, center)
		(leftFiche, rightFiche, centerFiche) = self.__getPositions(cursor, "select @row := @row + 1 as row, fiche from fiches f where (position >= %s and position <= %s and not exists (select * from actual_entries e where f.fiche = e.fiche and entry <> %s)) or ((position < %s or position > %s) and exists (select * from actual_entries e where e.fiche = f.fiche and entry = %s)) order by position", (first, last, entry, first, last, entry), left, right, center)
		self._closeDBAndCursor(cursor)
		return (leftFiche, rightFiche, centerFiche)

	# TODO: C w dziurach ktore sa na poczatku i koncu jest pierwsza i ostatnia fiszka!
	def getGapCount(self, before, after):
		cursor = self._openDBWithCursor()
		if before == None and after == None:
			res = int(self.__single(cursor, "select count(*) from fiches", ()))
			first = self.__single(cursor, "select fiche from fiches order by position limit 1", ())
			last = self.__single(cursor, "select fiche from fiches order by position desc limit 1", ())
		elif before == None:
			num = self.__firstEntry(cursor, after)
			res = int(self.__single(cursor, "select count(*) from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position < %s", (num)))
			first = self.__single(cursor, "select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position < %s order by position limit 1", (num))
			last = self.__single(cursor, "select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position < %s order by position desc limit 1", (num))
		elif after == None:
			num = self.__lastEntry(cursor, before)
			res = int(self.__single(cursor, "select count(*) from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s", (num)))
			first = self.__single(cursor, "select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s order by position limit 1", (num))
			last = self.__single(cursor, "select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s order by position desc limit 1", (num))
		else:
			numa = self.__firstEntry(cursor, after)
			numb = self.__lastEntry(cursor, before)
			res = int(self.__single(cursor, "select count(*) from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s and position < %s", (numb, numa)))
			first = self.__single(cursor, "select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s and position < %s order by position limit 1", (numb, numa))
			last = self.__single(cursor, "select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s and position < %s order by position desc limit 1", (numb, numa))
		self._closeDBAndCursor(cursor)
		return (first, last, res)

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
		
	def getPositionsForFichesForGap(self, before, after, left, right, center):
		cursor = self._openDBWithCursor()
		if before == None and after == None:
			(leftFiche, rightFiche, centerFiche) = self.__getPositions(cursor, "select @row := @row + 1 as row, fiche from fiches order by position", (), left, right, center)
		elif before == None:
			num = self.__lastEntry(cursor, after)
			#print "tu"
			(leftFiche, rightFiche, centerFiche) = self.__getPositions(cursor, "select @row := @row + 1 as row, fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position < %s order by position", tuple([num]), left, right, center)
		elif after == None:
			num = self.__lastEntry(cursor, before)
			(leftFiche, rightFiche, centerFiche) = self.__getPositions(cursor, "select @row := @row + 1 as row, fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s order by position", tuple([num]), left, right, center)
		else:
			numa = self.__firstEntry(cursor, after)
			numb = self.__lastEntry(cursor, before)
			(leftFiche, rightFiche, centerFiche) = self.__getPositions(cursor, "select @row := @row + 1 as row, fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s and position < %s order by position", (numb, numa), left, right, center)
		self._closeDBAndCursor(cursor)
		return (leftFiche, rightFiche, centerFiche)

	def getEntriesRegisterWithGaps(self):
		cursor = self._openDBWithCursor()
		#cursor.execute("select distinct entry from fiches f, actual_entries e where f.fiche = e.fiche and position = 0")
		##cursor.execute("select min(position) from fiches")
		##minPos = int(cursor.fetchone()[0])
		##cursor.execute("select distinct entry from fiches f, actual_entries e where f.fiche = e.fiche and position = %s", (minPos))
		##if cursor.fetchone() == None:
		##	res = [_("First fiche")]
		##else:
		res = []
		#&cursor.execute("select distinct entry from fiches f, actual_entries e where f.fiche = e.fiche order by position")
		cursor.execute("select distinct entry from actual_entries order by entry")
		row = cursor.fetchone()
		while row != None:
			res.append(str(row[0]))
			row = cursor.fetchone()
		prev = ""
		##cursor.execute("select entry from actual_entries where fiche = (select fiche from fiches where position <> %s order by position desc limit 1)", (minPos))
		##if cursor.fetchone() == None:
		##	res.append(_("Last fiche"))
		prev = None
		newres = []
		if res == []:
			num = int(self.__single(cursor, "select count(*) from fiches f", ()))
			num -= 2
			if num > 0:
				newres.append((num, None, None))
		else:
			for el in res:
				firstEntry = self.__firstEntry(cursor, el)
				if firstEntry == INF:
					newres.append(el)
					continue
				if prev == None:
					pos = self.__firstEntry(cursor, el)
					num = int(self.__single(cursor, "select count(*) from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position < %s", (pos)))
					num -= 1
					if num > 0:
						newres.append((num, None, el))
					newres.append(el)
				else:
					posa = self.__firstEntry(cursor, el)
					posb = self.__lastEntry(cursor, prev)
					num = int(self.__single(cursor, "select count(*) from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s and position < %s", (posb, posa)))
					if num > 0:
						newres.append((num, prev, el))
					newres.append(el)
				prev = el
			pos = self.__lastEntry(cursor, prev)
			num = int(self.__single(cursor, "select count(*) from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s", (pos)))
			num -= 1
			if num > 0:
				newres.append((num, prev, None))
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
			num = self.__firstEntry(cursor, after)
			#cursor.execute("select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position < %s order by position", (num))
			(limitStart, next) = self.__smartLimit(cursor, "select # from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position < %s order by position", (num), limitStart, atleast, limit)
		elif after == None:
			num = self.__lastEntry(cursor, before)
			#print num
			#cursor.execute("select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s order by position", (num))
			(limitStart, next) = self.__smartLimit(cursor, "select # from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s order by position", (num), limitStart, atleast, limit)
		else:
			numa = self.__firstEntry(cursor, after)
			numb = self.__lastEntry(cursor, before)
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
		##if ustr(entry) == _("First fiche"):
		##	#cursor.execute("select fiche from fiches where position = 0") TODO: NOTE problem z autoincrement
		##	cursor.execute("select fiche from fiches order by position limit 1")
		##elif ustr(entry) == _("Last fiche"):
		##	cursor.execute("select fiche from fiches order by position desc limit 1")
		##else:
		(first, last) = self.__entryLimits(cursor, entry)
		#&(limitStart, next) = self.__smartLimit(cursor, "select # from fiches f where position >= %s and position <= %s and not exists (select * from actual_entries e where f.fiche = e.fiche and entry <> %s) order by position", (first, last, entry), limitStart, atleast, limit)
		(limitStart, next) = self.__smartLimit(cursor, "select # from fiches f where (position >= %s and position <= %s and not exists (select * from actual_entries e where f.fiche = e.fiche and entry <> %s)) or ((position < %s or position > %s) and exists (select * from actual_entries e where e.fiche = f.fiche and entry = %s)) order by position", (first, last, entry, first, last, entry), limitStart, atleast, limit)
		row = cursor.fetchone()
		while row != None:			
			res.append(str(row[0]))
			row = cursor.fetchone()
		self._closeDBAndCursor(cursor)
		return (res, limitStart, next)

	def getFichesForEntryForLastFiche(self, entry, limit):
		cursor = self._openDBWithCursor()
		(firstpos, lastpos) = self.__entryLimits(cursor, entry)
		ficheId = self.__single(cursor, "select fiche from fiches where position = %s", (lastpos))
		self._closeDBAndCursor(cursor)
		return self.getFichesForEntryForFiche(entry, ficheId, limit) + (ficheId,)

	def getFichesForEntryForFiche(self, entry, ficheId, limit):
		cursor = self._openDBWithCursor()
		res = []
		rownum = 0
		next = None
		##if ustr(entry) == _("First fiche"):
		##	cursor.execute("select fiche from fiches order by position limit 1")
		##elif ustr(entry) == _("Last fiche"):
		##	cursor.execute("select fiche from fiches order by position desc limit 1")
		##else:
		(first, last) = self.__entryLimits(cursor, entry)
		cursor.execute("set @row = -1")
		cursor.execute("select a.row from (select @row := @row + 1 as row, fiche from fiches f where (position >= %s and position <= %s and not exists (select * from actual_entries e where f.fiche = e.fiche and entry <> %s)) or ((position < %s or position > %s) and exists (select * from actual_entries e where e.fiche = f.fiche and entry = %s)) order by position) a where a.fiche = %s", (first, last, entry, first, last, entry, ficheId))
		rownum = cursor.fetchone()[0]
			#:cursor.execute("select fiche from fiches f where position >= %s and position <= %s and not exists (select * from actual_entries e where f.fiche = e.fiche and entry <> %s) order by position limit %s,%s", (first, last, entry, rownum + limit, 1))
			#:row = cursor.fetchone()
			#:if row != None:
			#:	next = str(row[0])
		rownum -= limit / 2
		if rownum < 0:
			rownum = 0
		cursor.execute("select fiche from fiches f where (position >= %s and position <= %s and not exists (select * from actual_entries e where f.fiche = e.fiche and entry <> %s)) or ((position < %s or position > %s) and exists (select * from actual_entries e where e.fiche = f.fiche and entry = %s)) order by position limit %s,%s", (first, last, entry, first, last, entry, rownum, limit))
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
		rownum -= limit / 2
		if rownum < 0:
			rownum = 0
		cursor.execute(query.replace("#", "") + " limit %s,%s", pars + (rownum, limit))
		return (rownum, next)

	def getFichesForGapForLastFiche(self, before, after, limit):
		cursor = self._openDBWithCursor()
		if before == None and after == None:
			ficheId = self.__single(cursor, "select fiche from fiches order by position desc limit 1", ())
		elif before == None:
			num = self.__firstEntry(cursor, after)
			ficheId = self.__single(cursor, "select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position < %s order by position desc limit 1", (num))
		elif after == None:
			num = self.__lastEntry(cursor, before)
			ficheId = self.__single(cursor, "select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s order by position desc limit 1", (num))
		else:
			numa = self.__firstEntry(cursor, after)
			numb = self.__lastEntry(cursor, before)
			ficheId = self.__single(cursor, "select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s and position < %s order by position desc limit 1", (numb, numa))
		self._closeDBAndCursor(cursor)
		return self.getFichesForGapForFiche(before, after, ficheId, limit) + (ficheId,)

	def getFichesForGapForFiche(self, before, after, ficheId, limit):
		cursor = self._openDBWithCursor()
		res = []
		if before == None and after == None:
			(rownum, next) = self.__smartQuery(cursor, "select # fiche from fiches order by position", (), ficheId, 0, limit)
		elif before == None:
			num = self.__firstEntry(cursor, after)
			(rownum, next) = self.__smartQuery(cursor, "select # fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position < %s order by position", tuple([num]), ficheId, 0, limit)
		elif after == None:
			num = self.__lastEntry(cursor, before)
			(rownum, next) = self.__smartQuery(cursor, "select # fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s order by position", tuple([num]), ficheId, 0, limit)
		else:
			numa = self.__firstEntry(cursor, after)
			numb = self.__lastEntry(cursor, before)
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
				#print "join", ficheId
				cursor.execute("select fiche from fiches where fiche = %s", (ficheId))
			elif before == None:
				num = self.__firstEntry(cursor, after)
				#print "\t", "a", num, ficheId
				cursor.execute("select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position < %s and fiche = %s", (num, ficheId))
			elif after == None:
				num = self.__lastEntry(cursor, before)
				#print "\t", "b", num, ficheId
				cursor.execute("select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s and fiche = %s", (num, ficheId))
			else:
				numa = self.__firstEntry(cursor, after)
				numb = self.__lastEntry(cursor, before)
				#print "\t", numa, numb, ficheId
				cursor.execute("select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s and position < %s and fiche = %s", (numb, numa, ficheId))
		else:
			##if ustr(element) == _("First fiche"):
			##	#print "\t", "first", ficheId
			##	cursor.execute("select a.fiche from (select f.fiche from fiches f order by f.position limit 1) a where a.fiche = %s", (ficheId))
			##elif ustr(element) == _("Last fiche"):
			##	#print "\t", "last", ficheId
			##	cursor.execute("select a.fiche from (select f.fiche from fiches f order by f.position desc limit 1) a where a.fiche = %s", (ficheId))
			##else:
			(first, last) = self.__entryLimits(cursor, element)
			#print "\t", first, last, element, ficheId
			#assert(cursor.fetchone() == None)
			cursor.execute("select fiche from fiches f where ((position >= %s and position <= %s and not exists (select * from actual_entries e where f.fiche = e.fiche and entry <> %s)) or ((position < %s or position > %s) and exists (select * from actual_entries e where e.fiche = f.fiche and entry = %s))) and fiche = %s", (first, last, element, first, last, element, ficheId))
		row = cursor.fetchone()
		#print "===", row
		#row2 = cursor.fetchone()
		#print "---", row2
		self._closeDBAndCursor(cursor)
		return row != None

