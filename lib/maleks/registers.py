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

import os
import icu
#from maleks.i18n import _
from maleks.maleks.worddict import WordDictionary, SimpleDictionary
from maleks.maleks.useful import ustr, getUser, Counter, commonprefix

def _(s):
	return s

def compare(a, b, hint):
	collator = icu.Collator.createInstance(icu.Locale('pl_PL.UTF-8'))
	if len(commonprefix(a, hint)) > len(commonprefix(b, hint)):
		return 1
	elif len(commonprefix(b, hint)) > len(commonprefix(a, hint)):
		return -1
	else:
		return collator.compare(b, a)

def anyHint((a, b, c, d)):
	return a if a != "" else (b if b != "" else c)

class HintRegister(object):

	def __init__(self, abspath):
		self.__entries = []
		self.__dict17 = SimpleDictionary() #WordDictionary(5, (u"", u""))
		self.__dictLin = SimpleDictionary() #WordDictionary(5, (u"", u""))
		self.__dictDor = SimpleDictionary() #WordDictionary(5, (u"", u""))
		self.__new = []
		self.__path = abspath
		if os.path.exists(abspath + "/hint.reg"):
			f = open(abspath + "/hint.reg")
			for line in f:
				if line == "\n" or line[0] == "#":
					continue
				line = line[:-1]
				els = line.split(",")
				for i in range(0, len(els)):
					els[i] = els[i].replace('\\;', ',').replace('\\\\', '\\')
				siglum = self.__computeSiglum(els)
				self.__entries.append((els[0], els[1], els[2], siglum))
				#c = Counter()
				if els[0] != '':
					self.__dict17.addWord(ustr(els[0]), (els[0], siglum))
				if els[1] != '':
					self.__dictLin.addWord(ustr(els[1]), (els[1], siglum))
				if els[2] != '':
					self.__dictDor.addWord(ustr(els[2]), (els[2], siglum))
				#print c
			f.close()

	def __computeSiglum(self, els):
		res = ""
		if els[0] != "":
			res += "SJPXVII, "
		if els[1] != "":
			res += "L, "
		if els[2] != "":
			res += "SJPDor"
		if res[-2:] == ", ":
			res = res[:-2]
		return "(" + res + ")"

	def readUserHints(self, abspath):
		if os.path.exists(abspath + "/user_hint.reg"):
			f = open(abspath + "/user_hint.reg")
			for line in f:
				if line == "\n" or line[0] == "#":
					continue
				els = line[:-1].split("\t")
				for i in range(0, len(els)):
					els[i] = els[i].replace('\\;', ',').replace('\\\\', '\\')
				self.__entries.append((els[0], "", "", "(" + els[1] + ")"))
				self.__dict17.addWord(ustr(els[0]), (els[0], "(" + els[1] + ")"))
			f.close()
			self.sort()

	# TODO: A dokladnie omowic kasztowosc (tutaj i w innych przypadkach)
	def findHint(self, entry):
		if ustr(entry) == u"":
			return ("", "")
		(lcp17, sig17) = self.__dict17.findWord(ustr(entry))
		(lcpLin, sigLin) = self.__dictLin.findWord(ustr(entry))
		(lcpDor, sigDor) = self.__dictDor.findWord(ustr(entry))
		if compare(ustr(lcp17), ustr(lcpLin), ustr(entry)) >= 0:
			if compare(ustr(lcp17), ustr(lcpDor), ustr(entry)) >= 0:
				return (lcp17, sig17)
			elif compare(ustr(lcpLin), ustr(lcpDor), ustr(entry)) >= 0:
				return (lcpLin, sigLin)
			else:
				return (lcpDor, sigDor)
		elif compare(ustr(lcpLin), ustr(lcpDor), ustr(entry)) >= 0:
			return (lcpLin, sigLin)
		else:
			return (lcpDor, sigDor)
	#def findHint(self, entry):
	#	lcp = ""
	#	hint = None
	#	# TODO: C lepiej (lista zamiast krotki i obliczanie siglum dopiero gdy potrzebne)
	#	for (sp17Entry, lindeEntry, doroszewskiEntry, siglum) in self.__entries:
	#		#print type(sp17Entry), type(lindeEntry), type(doroszewskiEntry), type(entry)
	#		lcp17 = commonprefix(entry, unicode(sp17Entry, "utf-8"))
	#		lcpLin = commonprefix(entry, unicode(lindeEntry, "utf-8"))
	#		lcpDor = commonprefix(entry, unicode(doroszewskiEntry, "utf-8"))
	#		for lcpX in [lcp17, lcpLin, lcpDor]:
	#			if lcpX != "":
	#				if len(lcpX) > len(lcp):
	#					lcp = lcpX
	#					hint = (sp17Entry if sp17Entry != "" else (lindeEntry if lindeEntry != "" else doroszewskiEntry), siglum)
	#			break
	#		if lcp == entry:
	#			break
	#	return hint
		
	# TODO: C efektywniej (kubelki na litery?, posortowac?)

	def addHint(self, hint):
		(lcp17, sig17) = self.__dict17.findWord(ustr(hint))
		(lcpLin, sigLin) = self.__dictLin.findWord(ustr(hint))
		(lcpDor, sigDor) = self.__dictDor.findWord(ustr(hint))
		if ustr(lcp17) == ustr(hint) or ustr(lcpLin) == ustr(hint) or ustr(lcpDor) == ustr(hint):
			return False
			self.__new.append(str(hint.encode("utf-8")) + "\t" + getUser())
		self.__dict17.addWord(ustr(hint), (str(hint.encode("utf-8")), "(" + getUser() + ")"))
		self.__entries.append((str(hint.encode("utf-8")), "", "", "(" + getUser() + ")"))
		self.sort()
		self.__new.append(str(hint.encode("utf-8")) + "\t" + getUser())
		return True
	#def addHint(self, hint):
	#	found = False
	#	for (sp17Entry, lindeEntry, doroszewskiEntry, siglum) in self.__entries:
	#		if hint == unicode(sp17Entry, "utf-8") or hint == unicode(lindeEntry, "utf-8") or hint == unicode(doroszewskiEntry, "utf-8"):
	#			found = True
	#			return False
	#	if not found:
	#		self.__entries.append((str(hint.encode("utf-8")), "", "", "(" + getUser() + ")"))
	#		self.__new.append(str(hint.encode("utf-8")) + "\t" + getUser())
	#		self.sort()
	#		return True
	#return False

	def saveUserHints(self):
		f = open(self.__path + "/user_hint.reg", "a")
		for hint in self.__new:
			hint = hint.replace('\\', '\\\\').replace(',', '\\;')
			f.write(hint + "\n")
		f.close()

	def sort(self):
		collator = icu.Collator.createInstance(icu.Locale('pl_PL.UTF-8'))
		self.__entries = sorted(self.__entries, cmp=lambda a, b: collator.compare(anyHint(a), anyHint(b)))

	def __getitem__(self, ind):
		return self.__entries[ind]

	def __len__(self):
		return len(self.__entries)

class TaskRegister(object):

	def __init__(self, abspath, index, empty=False):
		self.__ids = []
		if not empty:
			f = open(abspath)
			for line in f:
				if line == "\n":
					continue
				line = line.strip()
				self.__ids.append(index.getFicheById(line))
			f.close()

	def append(self, fiche):
		self.__ids.append(fiche)
	
	def __getitem__(self, ind):
		return self.__ids[ind]
	
	def __len__(self):
		return len(self.__ids)

	def saveToFile(self, path):
		f = open(path, "w")
		for fiche in self.__ids:
			f.write(fiche.getId() + "\n")			
		f.close()

