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
import time
import icu
from maleks.maleks import log
from maleks.i18n import _
from maleks.maleks.useful import ustr, fstr

#def _(x):
#	return x

class DBCommon(object):

	def _nvl(self, obj):
		if obj == "":
			return None
		return obj

	def __init__(self, config=None):
		if config != None:
			self.__user = config.read('dbuser', '')
			self.__globalUser = self.__user
			self.__passwd = config.read('dbpass', '')
			self.__globalPasswd = self.__passwd
			self.__db = config.read('db', '')
			self.__globalDb = self.__db
		self.__conn = None

	def configure(self, user, passwd, db):
		self.__user = user
		self.__globalUser = self.__user
		self.__passwd = passwd
		self.__globalPasswd = passwd
		self.__db = db
		self.__globalDB = db

	def setPerDocumentConnection(self, db, user, passwd):
		self.__user = user if user != None else self.__globalUser
		self.__passwd = passwd if passwd != None else self.__globalPasswd
		self.__db = db if db != None else self.__globalDb

	def valid(self):
		return self.__user != '' and self.__passwd != '' and self.__db != ''

	def _openDBWithCursor(self):
		self.__conn = MySQLdb.connect(user=self.__user, passwd=self.__passwd, db=self.__db, use_unicode=False, init_command="SET NAMES 'utf8'",charset='utf8')
		#self._time = 0
		return self.__conn.cursor()

	def _closeDBAndCursor(self, cursor):
		#print "uplynelo:", self._time
		cursor.close()
		self.__conn.commit()
		self.__conn.close()

	def _execute(self, cursor, query, pars=()):
		if not isinstance(pars, tuple) and pars != None:
			pars = (pars,)
		#if pars == None:
		#	pars = ()
		#print pars
		querystr = query
		i = querystr.find("%s")
		j = 0
		ok = True
		while i != -1:
			querya = querystr[:i]
			queryb = querystr[i + 2:]
			try:
				querystr = querya + str(pars[j]) + queryb
			except IndexError:
				ok = False
				break
			j += 1
			i = querystr.find("%s")
		if ok:
			log.query(querystr, [], 0)
			#print querystr
		else:
			log.query(query, [pars], 1)
			#print query, pars
		#start = time.time()
		cursor.execute(query, pars)
		#stop = time.time()
		#self._time += stop - start
		#if stop - start >= 1.0:
		#	print querystr
		#	print stop - start
		
INF = 10000000000

class DBEntryController(DBCommon):

	def __init__(self, config=None):
		DBCommon.__init__(self, config=config)

	def __firstEntry(self, cursor, entry):
		self._execute(cursor, "select max(position) from fiches f, actual_entries e where f.fiche = e.fiche and entry < %s", (entry))
		row = cursor.fetchone()
		if row == None or row[0] == None:
			maxPrev = -1
		else:
			maxPrev = int(row[0])
		self._execute(cursor, "select min(position) from fiches f, actual_entries e where f.fiche = e.fiche and entry = %s and position > %s", (entry, maxPrev))
		row = cursor.fetchone()
		if row == None or row[0] == None:
			return INF # TODO: A lepiej; 100 mld fiszek starczy?
		else:
			return int(row[0])

	def __lastEntry(self, cursor, entry):
		#print entry
		return int(self.__single(cursor, "select max(position) from fiches f, actual_entries e where f.fiche = e.fiche and entry = %s", (entry)))

	def __entryLimits(self, cursor, entry):
		return (self.__firstEntry(cursor, entry), self.__lastEntry(cursor, entry))
		
	def __single(self, cursor, query, pars):
		return self._single(cursor, query, pars)

	def _single(self, cursor, query, pars):
		self._execute(cursor, query, pars)
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
		(first, last, res) = self.__getEntriesCount(cursor, entry)
		self._closeDBAndCursor(cursor)
		return (first, last, res)

	def __getEntriesCount(self, cursor, entry):
		assert(entry != None)
		(firstpos, lastpos) = self.__entryLimits(cursor, entry)
		#&res = int(self.__single(cursor, "select count(*) from fiches f where position >= %s and position <= %s and not exists (select * from actual_entries e where f.fiche = e.fiche and entry <> %s)", (firstpos, lastpos, entry)))
		res = int(self.__single(cursor, "select count(*) from fiches f where (position >= %s and position <= %s and not exists (select * from actual_entries e where f.fiche = e.fiche and entry <> %s)) or ((position < %s or position > %s) and exists (select * from actual_entries e where e.fiche = f.fiche and entry = %s))", (firstpos, lastpos, entry, firstpos, lastpos, entry)))
		first = self.__single(cursor, "select fiche from fiches where position = %s", (firstpos))
		last = self.__single(cursor, "select fiche from fiches where position = %s", (lastpos))
		return (first, last, res)

	def getFicheForEntryPosition(self, entry, pos):
		log.db("getFicheForEntryPosition", [entry, pos], 0)
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
		log.db("getFicheForEntryPosition return", [res], 1)
		return res
		
	def getFirstFicheOfElement(self, el):
		if isinstance(el, tuple):
			return self.__getFirstFicheOfGap(el)
		else:
			return self.__getFirstFicheOfEntry(el)

	def getLastFicheOfElement(self, el):
		if isinstance(el, tuple):
			return self.__getLastFicheOfGap(el)
		else:
			return self.__getLastFicheOfEntry(el)
	
	def __getFirstFicheOfEntry(self, entry):
		log.db("__getFirstFicheOfEntry", [entry], 0)
		cursor = self._openDBWithCursor()
		res = self.__single(cursor, "select fiche from entries where entry = %s order by position asc limit 1", (entry))
		self._closeDBAndCursor(cursor)
		log.db("__getFirstFicheOfEntry return", [res], 1)
		return res

	def __getFirstFicheOfGap(self, (num, before, after)):
		log.db("__getFirstFicheOfGap", [(num, before, after)], 0)
		cursor = self._openDBWithCursor()
		if before == None and after == None:
			res = self.__single(cursor, "select fiche from fiches order by position asc limit 1", ())
		elif before == None:
			num = self.__firstEntry(cursor, after)
			res = self.__single(cursor, "select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position < %s order by position asc limit 1", (num))
		elif after == None:
			num = self.__lastEntry(cursor, before)
			res = self.__single(cursor, "select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s order by position asc limit 1", (num))
		else:
			numa = self.__firstEntry(cursor, after)
			numb = self.__lastEntry(cursor, before)
			res = self.__single(cursor, "select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s and position < %s order by position asc limit 1", (numb, numa))
		self._closeDBAndCursor(cursor)
		log.db("__getFirstFicheOfGap return", [res], 1)
		return res

	def __getLastFicheOfEntry(self, entry):
		log.db("__getLastFicheOfEntry", [entry], 0)
		cursor = self._openDBWithCursor()
		res = self.__single(cursor, "select fiche from entries where entry = %s order by position desc limit 1", (entry))
		self._closeDBAndCursor(cursor)
		#if res == None:
		#	print "select fiche from entries where entry = %s order by position desc limit 1", entry
		log.db("__getLastFicheOfEntry return", [res], 1)
		return res

	def __getLastFicheOfGap(self, (num, before, after)):
		log.db("__getLastFicheOfGap", [(num, before, after)], 0)
		cursor = self._openDBWithCursor()
		if before == None and after == None:
			res = self.__single(cursor, "select fiche from fiches order by position desc limit 1", ())
		elif before == None:
			num = self.__firstEntry(cursor, after)
			res = self.__single(cursor, "select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position < %s order by position desc limit 1", (num))
		elif after == None:
			num = self.__lastEntry(cursor, before)
			res = self.__single(cursor, "select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s order by position desc limit 1", (num))
		else:
			numa = self.__firstEntry(cursor, after)
			numb = self.__lastEntry(cursor, before)
			res = self.__single(cursor, "select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s and position < %s order by position desc limit 1", (numb, numa))
		self._closeDBAndCursor(cursor)
		#if res == None:
		#	print before, after
		#	print "select fiche from fiches order by position desc limit 1"
		#	print "select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position < %s order by position desc limit 1", num
		#	print "select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s order by position desc limit 1", num
		#	print "select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s and position < %s order by position desc limit 1", numb, numa
		log.db("__getLastFicheOfGap return", [res], 1)
		return res
		
	def __getPositions(self, cursor, query, pars, left, right, center):
		log.db("__getPositions", [cursor, query, pars, left, right, center], 0)
		self._execute(cursor, "set @row = -1")
		leftFiche = self.__single(cursor, "select a.row from (" + query + ") a where a.fiche = %s", pars + tuple([left]))
		self._execute(cursor, "set @row = -1")
		#print pars, left, right, center
		rightFiche = self.__single(cursor, "select a.row from (" + query + ") a where a.fiche = %s", pars + tuple([right]))
		self._execute(cursor, "set @row = -1")
		centerFiche = self.__single(cursor, "select a.row from (" + query + ") a where a.fiche = %s", pars + tuple([center]))
		log.db("__getPositions return", [(leftFiche, rightFiche, centerFiche)], 1)
		return (leftFiche, rightFiche, centerFiche)
		
	def getPositionsForFichesForEntry(self, entry, left, right, center):
		log.db("getPositionsForFichesForEntry", [entry, left, right, center], 0)
		cursor = self._openDBWithCursor()
		##if ustr(entry) in [_("First fiche"), _("Last fiche")]: # TODO: D nie powinno sie wydarzyc, ale sprawdzic
		##	return (0, 0, 0)
		##else:
		(first, last) = self.__entryLimits(cursor, entry)
		#&(leftFiche, rightFiche, centerFiche) = self.__getPositions(cursor, "select @row := @row + 1 as row, fiche from fiches f where position >= %s and position <= %s and not exists (select * from actual_entries e where f.fiche = e.fiche and entry <> %s) order by position", (first, last, entry), left, right, center)
		(leftFiche, rightFiche, centerFiche) = self.__getPositions(cursor, "select @row := @row + 1 as row, fiche from fiches f where (position >= %s and position <= %s and not exists (select * from actual_entries e where f.fiche = e.fiche and entry <> %s)) or ((position < %s or position > %s) and exists (select * from actual_entries e where e.fiche = f.fiche and entry = %s)) order by position", (first, last, entry, first, last, entry), left, right, center)
		self._closeDBAndCursor(cursor)
		log.db("getPositionsForFichesForEntry return", [(leftFiche, rightFiche, centerFiche)], 1)
		return (leftFiche, rightFiche, centerFiche)

	# TODO: C w dziurach ktore sa na poczatku i koncu jest pierwsza i ostatnia fiszka!
	def getGapCount(self, before, after):
		log.db("getGapCount", [before, after], 0)
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
		log.db("getGapCount return", [(first, last, res)], 1)
		return (first, last, res)

	def getFicheForGapPosition(self, before, after, pos):
		#print pos
		log.db("getFicheForGapPosition", [before, after, pos], 0)
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
			#print after, before
			numa = self.__firstEntry(cursor, after)
			numb = self.__lastEntry(cursor, before)
			res = self.__single(cursor, "select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s and position < %s order by position limit %s,1", (numb, numa, pos))
		self._closeDBAndCursor(cursor)
		log.db("getFicheForGapPosition return", [res], 1)
		return res
		
	def getPositionsForFichesForGap(self, before, after, left, right, center):
		log.db("getPositionsForFichesForGap", [before, after, left, right, center], 0)
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
		log.db("getPositionsForFichesForGap return", [(leftFiche, rightFiche, centerFiche)], 1)
		return (leftFiche, rightFiche, centerFiche)

	def getEntriesRegisterWithGaps(self, preloadedEntries=None):
		log.db("getEntriesRegisterWithGaps", [preloadedEntries], 0)
		cursor = self._openDBWithCursor()
		#self._execute(cursor, "select distinct entry from fiches f, actual_entries e where f.fiche = e.fiche and position = 0")
		##self._execute(cursor, "select min(position) from fiches")
		##minPos = int(cursor.fetchone()[0])
		##self._execute(cursor, "select distinct entry from fiches f, actual_entries e where f.fiche = e.fiche and position = %s", (minPos))
		##if cursor.fetchone() == None:
		##	res = [_("First fiche")]
		##else:
		entryLens = {}
		if preloadedEntries == None:
			res = []
			#&self._execute(cursor, "select distinct entry from fiches f, actual_entries e where f.fiche = e.fiche order by position")
			self._execute(cursor, "select distinct entry from actual_entries order by entry")
			#:self._execute(cursor, "select count(position), entry from entries group by entry order by entry")
			row = cursor.fetchone()
			while row != None:
				res.append(str(row[0]))
				row = cursor.fetchone()
			prev = ""
			#:for entry in res:
			#:	(first, last, num) = self.__getEntriesCount(cursor, entry)
			#:	entryLens.setdefault(entry, num)
		else:
			res = preloadedEntries
		##self._execute(cursor, "select entry from actual_entries where fiche = (select fiche from fiches where position <> %s order by position desc limit 1)", (minPos))
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
					#num -= 1
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
			#num -= 1
			if num > 0:
				newres.append((num, prev, None))
		self._closeDBAndCursor(cursor)
		log.db("getEntriesRegisterWithGaps return", [(newres, entryLens)], 1)
		return (newres, entryLens)

	NEIGHBOURHOOD = 3
	
	def __zero(self, i):
		if i < 0:
			return 0
		else:
			return i

	def __max(self, i, m):
		if i > m:
			return m
		else:
			return i
			
	SMART_LIMIT = 2
	
	def __binaryFind(self, text, li): # jesli nie ma zwraca nastepne haslo, poprzednie w razie gdy osiagnieto koniec listy
		log.db("__binaryFind", [text, li], 0)
		collator = icu.Collator.createInstance(icu.Locale('pl_PL.UTF-8'))
		def __pom(left, right):
			#print left, right, stru(text)
			#print stru(self._elementLabels[left]), stru(self._elementLabels[right])
			if left == right:
				if collator.compare(li[left], text) >= 0:
					return left
				else:
					return left + 1
			elif left + 1 == right:
				if collator.compare(li[left], text) >= 0:
					return left
				elif collator.compare(li[right], text) >= 0:
					return right
				else:
					return right + 1
			lenn = right - left
			center = left + lenn // 2
			#print center, stru(self._elementLabels[center])
			if collator.compare(li[center], text) == 0:
				return center
			elif collator.compare(li[center], text) > 0:
				return __pom(left, center - 1)
			else:
				return __pom(center + 1, right)
		res = __pom(0, len(li) - 1)
		if res == len(li):
			res -= 1
		log.db("__binaryFind return", [res], 1)
		return res

	def __fillGap(self, cursor, prev, el, newres, myEntries):
		if prev == None and el == myEntries[0]:
			pos = self.__firstEntry(cursor, el)
			num = int(self.__single(cursor, "select count(*) from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position < %s", (pos)))
			if num > 0:
				newres.append((num, None, el))
			newres.append(el)
		elif prev == None:
			newres.append(el)
		elif prev != None:
			posa = self.__firstEntry(cursor, el)
			posb = self.__lastEntry(cursor, prev)
			num = int(self.__single(cursor, "select count(*) from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s and position < %s", (posb, posa)))
			if num > 0:
				newres.append((num, prev, el))
			newres.append(el)
		return newres

	def getPartialEntriesRegisterWithGaps(self, entries):
		log.db("getPartialEntriesRegisterWithGaps", [entries], 0)
		cursor = self._openDBWithCursor()
		res = []
		neighbourhoods = []
		myEntries = []
		entryLens = {}
		self._execute(cursor, "select distinct entry from actual_entries order by entry")
		#:self._execute(cursor, "select count(position), entry from entries group by entry order by entry")
		row = cursor.fetchone()
		while row != None:
			myEntries.append(str(row[0]))
			row = cursor.fetchone()
		#:for entry in myEntries:
		#:	(first, last, num) = self.__getEntriesCount(cursor, entry)
		#:	entryLens.setdefault(entry, num)
		if len(myEntries) < DBEntryController.SMART_LIMIT:
			return (None, False, None, None, None)
		hasFirstNone = int(self.__single(cursor, "select count(*) from entries where position = (select min(position) from fiches)", ())) == 0
		hasLastNone = int(self.__single(cursor, "select count(*) from entries where position = (select max(position) from fiches)", ())) == 0
		inds = []
		for e in entries:
			#ind = myEntries.index(e)
			ind = self.__binaryFind(e, myEntries) # bo dziury
			inds.append(self.__zero(ind - DBEntryController.NEIGHBOURHOOD))
			inds.append(self.__max(ind + DBEntryController.NEIGHBOURHOOD, len(myEntries)))
		fromm  = min(inds)
		too = max(inds)
		if True:
		#for e in entries:
			neighbours = []
		#	for i in range(self.__zero(ind - DBEntryController.NEIGHBOURHOOD), self.__max(ind + DBEntryController.NEIGHBOURHOOD, len(myEntries))):
			#:for i in range(fromm, too):
			#:	neighbours.append(myEntries[i])
		#	#fromm = self._execute(cursor, "select min(position) from entries where entry = %s", (neighbours[0]))
		#	#too = self._execute(cursor, "select max(position) from entries where entry = %s", (neighbours[-1]))
			prev = None
			newres = []
			#:for el in neighbours:
			if fromm < 0:
				fromm = 0
			if too > len(myEntries):
				too = len(myEntries)
			i = fromm
			firstEntryNotInOrder = False
			firstEntryInOrder = None
			while True:
				neighbours.append(myEntries[i])
				el = myEntries[i]
				firstEntry = self.__firstEntry(cursor, el)
				if firstEntry == INF:
					newres.append(el)
					if i == fromm:
						firstEntryNotInOrder = True
					i += 1
					continue
				newres = self.__fillGap(cursor, prev, el, newres, myEntries)
				prev = el
				if firstEntryInOrder == None:
					firstEntryInOrder = el
				i += 1
				if i >= too:
					break
			if neighbours[-1] == myEntries[-1]:
				pos = self.__lastEntry(cursor, prev)
				num = int(self.__single(cursor, "select count(*) from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s", (pos)))
				if num > 0:
					newres.append((num, prev, None))
			if firstEntryNotInOrder:
				if firstEntryInOrder == None:
					log.log("db_entry assert", [myEntries, entries, fromm, too], 0)
					assert(False)
				i = fromm
				while True:
					prev = myEntries[i]
					firstEntry = self.__firstEntry(cursor, prev)
					if firstEntry == INF:
						if i != fromm:
							newres.insert(0, prev)
						i -= 1
						if i < 0:
							log.log("db_entry assert", [myEntries, entries, fromm, too], 1)
							assert(False)
						continue
					posa = self.__firstEntry(cursor, firstEntryInOrder)
					posb = self.__lastEntry(cursor, prev)
					num = int(self.__single(cursor, "select count(*) from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s and position < %s", (posb, posa)))
					if num > 0:
						newres.insert(0, (num, prev, firstEntryInOrder))
					newres.insert(0, prev)
					break
			neighbourhoods.append((ustr(e), newres))
		#neighbourhoods = self.__combine(neighbourhoods)
		self._closeDBAndCursor(cursor)
		log.db("getPartialEntriesRegisterWithGaps return", [(neighbourhoods, True, hasFirstNone, hasLastNone, entryLens)], 1)
		return (neighbourhoods, True, hasFirstNone, hasLastNone, entryLens)

	#def __eq(self, a, b):
	#	if isinstance(a, tuple) and isinstance(b, tuple):
	#		return a[1] == b[1] and a[2] == b[2]
	#	elif isinstance(a, str) and isinstance(b, str):
	#		return a == b
	#	else:
	#		return False

	#def __join(self, n1, n2):
	#	for i in range(0, len(n1)):
	#		for j in range(0, len(n2)):
	#			if len(n1[i + 1:]) < len(n2[j + 1:]) and self.__eq(n1[i], n2[j]):
	#				res = n1[0:i + 1]
	#			for k in range(j + 1, len(n2)):
	#					res.append(n2[k])
	#				return res
	#	return None

	#def __combine(self, neighbourhoods):
	#	was = True
	#	while was:
	#		was = False
	#		newNeys = neighbourhoods
	#		for n1 in neighbourhoods:
	#			#print type(n1[0])
	#			ok = True
	#			for n2 in neighbourhoods:
	#				#print type(n2[0])
	#				#print n1, n2
	#				if n2 != n1:
	#					new = self.__join(n1[1], n2[1])
	#					if new != None:
	#						newNeys.remove(n1)
	#						newNeys.remove(n2)
	#						newNeys.append((n1[0], new))
	#						was = True
	#						ok = False
	#						break
	#			if not ok:
	#				break
	#		neighbourhoods = newNeys
	#	return neighbourhoods			

	def __smartLimit(self, cursor, query, pars, limitStart, atleast, limit):
		log.db("__smartLimit", [cursor, query, pars, limitStart, atleast, limit], 0)
		if atleast != None:
			self._execute(cursor, query.replace("#", "count(*)"), pars)
			num = int(cursor.fetchone()[0])
			if limitStart + atleast > num:
				limitStart = num - atleast
		#print query.replace("#", "fiche") + " limit " + str(limitStart) + "," + str(limit), pars
		#:self._execute(cursor, query.replace("#", "fiche") + " limit " + str(limitStart + limit) + ",1", pars)
		#:row = cursor.fetchone()
		#:if row != None:
		#:	next = str(row[0])
		#:else:
		next = None
		self._execute(cursor, query.replace("#", "fiche") + " limit " + str(limitStart) + "," + str(limit), pars)
		log.db("__smartLimit return", [(limitStart, next)], 1)
		return (limitStart, next)

	def getFichesForGap(self, before, after, limit, limitStart=0, atleast=None):
		log.db("getFichesForGap", [before, after, limit, limitStart, atleast], 0)
		cursor = self._openDBWithCursor()
		res = []
		#print ":", before, after
		if before == None and after == None:
			#self._execute(cursor, "select fiche from fiches order by position")
			(limitStart, next) = self.__smartLimit(cursor, "select # from fiches order by position", (), limitStart, atleast, limit) 
		elif before == None:
			num = self.__firstEntry(cursor, after)
			#self._execute(cursor, "select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position < %s order by position", (num))
			(limitStart, next) = self.__smartLimit(cursor, "select # from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position < %s order by position", (num), limitStart, atleast, limit)
		elif after == None:
			num = self.__lastEntry(cursor, before)
			#print num
			#self._execute(cursor, "select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s order by position", (num))
			(limitStart, next) = self.__smartLimit(cursor, "select # from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s order by position", (num), limitStart, atleast, limit)
		else:
			numa = self.__firstEntry(cursor, after)
			numb = self.__lastEntry(cursor, before)
			#self._execute(cursor, "select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s and position < %s order by position", (numb, numa))
			(limitStart, next) = self.__smartLimit(cursor, "select # from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s and position < %s order by position", (numb, numa), limitStart, atleast, limit)
		row = cursor.fetchone()
		while row != None:
			#print row
			res.append(str(row[0]))
			row = cursor.fetchone()
		self._closeDBAndCursor(cursor)
		log.db("getFichesForGap return", [(res, limitStart, next)], 1)
		return (res, limitStart, next)
	
	def getEntryCount(self, entry):
		log.db("getEntryCount", [entry], 0)
		cursor = self._openDBWithCursor()
		(first, last) = self.__entryLimits(cursor, entry)
		indexed = int(self._single(cursor, "select count(*) from entries where entry = %s", (entry)))
		#hypothetical = int(self._single(cursor, "select count(*) from fiches f where position > %s and position < %s and not exists (select * from entries g where g.fiche = f.fiche and g.position = f.position)", (first, last, entry)))
		hypothetical = int(self._single(cursor, "select count(*) from fiches f where (position > %s and position < %s and not exists (select * from actual_entries e where f.fiche = e.fiche)) or ((position < %s or position > %s) and exists (select * from actual_entries e where e.fiche = f.fiche and entry = %s))", (first, last, first, last, entry)))
		self._closeDBAndCursor(cursor)
		log.db("getEntryCount return", [], 1)
		return (indexed, hypothetical)

	def getFichesForEntry(self, entry, limit, limitStart=0, atleast=None):
		log.db("getFichesForEntry", [entry, limit, limitStart, atleast], 0)
		res = []
		next = None
		cursor = self._openDBWithCursor()
		##if ustr(entry) == _("First fiche"):
		##	#self._execute(cursor, "select fiche from fiches where position = 0") TODO: NOTE problem z autoincrement
		##	self._execute(cursor, "select fiche from fiches order by position limit 1")
		##elif ustr(entry) == _("Last fiche"):
		##	self._execute(cursor, "select fiche from fiches order by position desc limit 1")
		##else:
		(first, last) = self.__entryLimits(cursor, entry)
		#&(limitStart, next) = self.__smartLimit(cursor, "select # from fiches f where position >= %s and position <= %s and not exists (select * from actual_entries e where f.fiche = e.fiche and entry <> %s) order by position", (first, last, entry), limitStart, atleast, limit)
		(limitStart, next) = self.__smartLimit(cursor, "select # from fiches f where (position >= %s and position <= %s and not exists (select * from actual_entries e where f.fiche = e.fiche and entry <> %s)) or ((position < %s or position > %s) and exists (select * from actual_entries e where e.fiche = f.fiche and entry = %s)) order by position", (first, last, entry, first, last, entry), limitStart, atleast, limit)
		row = cursor.fetchone()
		while row != None:			
			res.append(str(row[0]))
			row = cursor.fetchone()
		self._closeDBAndCursor(cursor)
		log.db("getFichesForEntry return", [(res, limitStart, next)], 1)
		return (res, limitStart, next)

	def getFichesForEntryForLastFiche(self, entry, limit):
		log.db("getFichesForEntryForLastFiche", [entry, limit], 0)
		cursor = self._openDBWithCursor()
		(firstpos, lastpos) = self.__entryLimits(cursor, entry)
		ficheId = self.__single(cursor, "select fiche from fiches where position = %s", (lastpos))
		self._closeDBAndCursor(cursor)
		res = self.getFichesForEntryForFiche(entry, ficheId, limit) + (ficheId,)
		log.db("getFichesForEntryForLastFiche return", [res], 1)
		return res

	def getFichesForEntryForFiche(self, entry, ficheId, limit):
		log.db("getFichesForEntryForFiche", [entry, ficheId, limit], 0)
		cursor = self._openDBWithCursor()
		res = []
		rownum = 0
		next = None
		##if ustr(entry) == _("First fiche"):
		##	self._execute(cursor, "select fiche from fiches order by position limit 1")
		##elif ustr(entry) == _("Last fiche"):
		##	self._execute(cursor, "select fiche from fiches order by position desc limit 1")
		##else:
		(first, last) = self.__entryLimits(cursor, entry)
		self._execute(cursor, "set @row = -1")
		self._execute(cursor, "select a.row from (select @row := @row + 1 as row, fiche from fiches f where (position >= %s and position <= %s and not exists (select * from actual_entries e where f.fiche = e.fiche and entry <> %s)) or ((position < %s or position > %s) and exists (select * from actual_entries e where e.fiche = f.fiche and entry = %s)) order by position) a where a.fiche = %s", (first, last, entry, first, last, entry, ficheId))
		rownum = cursor.fetchone()[0]
			#:self._execute(cursor, "select fiche from fiches f where position >= %s and position <= %s and not exists (select * from actual_entries e where f.fiche = e.fiche and entry <> %s) order by position limit %s,%s", (first, last, entry, rownum + limit, 1))
			#:row = cursor.fetchone()
			#:if row != None:
			#:	next = str(row[0])
		rownum -= limit / 2
		if rownum < 0:
			rownum = 0
		self._execute(cursor, "select fiche from fiches f where (position >= %s and position <= %s and not exists (select * from actual_entries e where f.fiche = e.fiche and entry <> %s)) or ((position < %s or position > %s) and exists (select * from actual_entries e where e.fiche = f.fiche and entry = %s)) order by position limit %s,%s", (first, last, entry, first, last, entry, rownum, limit))
		row = cursor.fetchone()
		while row != None:			
			res.append(str(row[0]))
			row = cursor.fetchone()
		self._closeDBAndCursor(cursor)
		log.db("getFichesForEntryForFiche return", [(res, rownum, next)], 1)
		return (res, rownum, next)
		
	def __smartQuery(self, cursor, query, pars, ficheId, ind, limit):
		log.db("__smartQuery", [cursor, query, pars, ficheId, ind, limit], 0)
		self._execute(cursor, "set @row = -1")
		self._execute(cursor, "select a.row from (" + query.replace("#", "@row := @row + 1 as row,") + ") a where a.fiche = %s", pars + tuple([ficheId]))
		rownum = cursor.fetchone()[0]
		#:self._execute(cursor, query.replace("#", "") + " limit %s,%s", pars + (limit + ind, 1))
		#:row = cursor.fetchone()
		#:if row != None:
		#:	next = str(row[0])
		#:else:
		next = None
		rownum -= limit / 2
		if rownum < 0:
			rownum = 0
		self._execute(cursor, query.replace("#", "") + " limit %s,%s", pars + (rownum, limit))
		log.db("__smartQuery return", [(rownum, next)], 1)
		return (rownum, next)

	def getFichesForGapForLastFiche(self, before, after, limit):
		log.db("getFichesForGapForLastFiche", [], 0)
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
		res = self.getFichesForGapForFiche(before, after, ficheId, limit) + (ficheId,)
		log.db("getFichesForGapForLastFiche return", [res], 1)
		return res

	def getFichesForGapForFiche(self, before, after, ficheId, limit):
		log.db("getFichesForGapForFiche", [], 0)
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
		log.db("getFichesForGapForFiche return", [(res, rownum, next)], 1)
		return (res, rownum, next)

	def hasFiche(self, element, ficheId):
		log.db("hasFiche", [element, ficheId], 0)
		cursor = self._openDBWithCursor()
		if isinstance(element, tuple):
			(num, before, after) = element
			if before == None and after == None:
				#print "join", ficheId
				self._execute(cursor, "select fiche from fiches where fiche = %s", (ficheId))
			elif before == None:
				num = self.__firstEntry(cursor, after)
				#print "\t", "a", num, ficheId
				self._execute(cursor, "select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position < %s and fiche = %s", (num, ficheId))
			elif after == None:
				num = self.__lastEntry(cursor, before)
				#print "\t", "b", num, ficheId
				self._execute(cursor, "select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s and fiche = %s", (num, ficheId))
			else:
				numa = self.__firstEntry(cursor, after)
				numb = self.__lastEntry(cursor, before)
				#print "\t", numa, numb, ficheId
				self._execute(cursor, "select fiche from fiches f where not exists (select * from actual_entries e where f.fiche = e.fiche) and position > %s and position < %s and fiche = %s", (numb, numa, ficheId))
		else:
			##if ustr(element) == _("First fiche"):
			##	#print "\t", "first", ficheId
			##	self._execute(cursor, "select a.fiche from (select f.fiche from fiches f order by f.position limit 1) a where a.fiche = %s", (ficheId))
			##elif ustr(element) == _("Last fiche"):
			##	#print "\t", "last", ficheId
			##	self._execute(cursor, "select a.fiche from (select f.fiche from fiches f order by f.position desc limit 1) a where a.fiche = %s", (ficheId))
			##else:
			(first, last) = self.__entryLimits(cursor, element)
			#print "\t", first, last, element, ficheId
			#assert(cursor.fetchone() == None)
			self._execute(cursor, "select fiche from fiches f where ((position >= %s and position <= %s and not exists (select * from actual_entries e where f.fiche = e.fiche and entry <> %s)) or ((position < %s or position > %s) and exists (select * from actual_entries e where e.fiche = f.fiche and entry = %s))) and fiche = %s", (first, last, element, first, last, element, ficheId))
		row = cursor.fetchone()
		#print "===", row
		#row2 = cursor.fetchone()
		#print "---", row2
		self._closeDBAndCursor(cursor)
		log.db("hasFiche return", [row != None], 1)
		return row != None

	def dumpDatabase(self):
		cursor = self._openDBWithCursor()
		res = ""
		cursor.execute("select * from entries")
		row = cursor.fetchone()
		while row != None:
			res += fstr(row[0]) + ", " + fstr(row[1]) + ", " + fstr(row[2]) + "\n"
			row = cursor.fetchone()
		self._closeDBAndCursor(cursor)
		return res

