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

import icu
from maleks.maleks.useful import index, ustr, commonprefix

def commonprefix(a, b):
	pref = u""
	for i in range(0, min(len(a), len(b))):
		if a[i] != b[i]:
			break
		pref += a[i] 
	return pref

class SimpleDictionary:
	
	def __init__(self):
		self.__dict = {}
		self.__list = []
	
	def clean(self):
		self.__dict = {}
		self.__list = []
	
	def __insertFind(self, what):
		collator = icu.Collator.createInstance(icu.Locale('pl_PL.UTF-8'))
		def __pom(left, right):
			if left == right:
				if collator.compare(ustr(self.__list[left]), ustr(what)) > 0:
					return left
				elif collator.compare(ustr(self.__list[left]), ustr(what)) < 0:
					return left + 1
				else:
					return -1
			elif left + 1 == right:
				if collator.compare(ustr(self.__list[left]), ustr(what)) == 0:
					return -1
				elif collator.compare(ustr(self.__list[left]), ustr(what)) > 0:
					return left
				elif collator.compare(ustr(self.__list[right]), ustr(what)) > 0:
					return right
				elif collator.compare(ustr(self.__list[right]), ustr(what)) == 0:
					return -1
				else:
					return right + 1
			lenn = right - left
			center = left + lenn // 2
			if collator.compare(ustr(self.__list[center]), ustr(what)) > 0:
				return __pom(left, center - 1)
			elif collator.compare(ustr(self.__list[center]), ustr(what)) < 0:
				return __pom(center + 1, right)
			else:
				return -1
		if len(self.__list) == 0:
			return 0
		return __pom(0, len(self.__list) - 1)
		
	def addWord(self, key, value):
		where = self.__insertFind(key)
		if where != -1:
			self.__dict[key] = value
			if where == len(self.__list):
				self.__list.append(key)
			else:
				self.__list.insert(where, key)
				
	def findWord(self, what):
		collator = icu.Collator.createInstance(icu.Locale('pl_PL.UTF-8'))
		def __pom(left, right):
			if left == right:
				if collator.compare(ustr(self.__list[left]), ustr(what)) > 0:
					return left
				elif collator.compare(ustr(self.__list[left]), ustr(what)) < 0:
					return left + 1
				else:
					return left
			elif left + 1 == right:
				if collator.compare(ustr(self.__list[left]), ustr(what)) == 0:
					return left
				elif collator.compare(ustr(self.__list[left]), ustr(what)) > 0:
					return left
				elif collator.compare(ustr(self.__list[right]), ustr(what)) > 0:
					return right
				elif collator.compare(ustr(self.__list[right]), ustr(what)) == 0:
					return right
				else:
					return right + 1
			lenn = right - left
			center = left + lenn // 2
			if collator.compare(ustr(self.__list[center]), ustr(what)) > 0:
				return __pom(left, center - 1)
			elif collator.compare(ustr(self.__list[center]), ustr(what)) < 0:
				return __pom(center + 1, right)
			else:
				return center
		if len(self.__list) == 0:
			return ("", "")
		res = __pom(0, len(self.__list) - 1)
		if res == len(self.__list):
			res -= 1
		return self.__dict[self.__list[res]]
		
	def printYourself(self):
		for el in self.__list:
			print el
		
#Deprecated
class WordDictionary:

	def __init__(self, level=5, null=None):
		self._dict = {}
		self._level = level
		self._null = u"" if null == None else null
	
	def clean(self):
		self._dict = {}
	
	def _at(self, word, i):
		if i >= len(word):
			return ''
		else:
			return word[i]

	def addWord(self, key, value):	
		if self._level == 0:
			self._dict.setdefault(key, value)
		else:
			h = self._at(key, 0)
			if h != u'':
				t = key[1:]
			else:
				t = u''
			if self._dict.get(h) == None:
				self._dict.setdefault(h, WordDictionary(self._level - 1))
			self._dict.get(h).addWord(t, value)

	def findWord(self, key):
		if self._level == 0:
			lcp = u""
			hint = self._null
			for (k, v) in self._dict.iteritems():
				lcpnew = commonprefix(key, k)
				if len(lcpnew) >= len(lcp):
					hint = v
					lcp = lcpnew
			return hint
		else:
			h = self._at(key, 0)
			if h != u'':
				t = key[1:]
			else:
				t = u''
			if self._dict.get(h) == None:
				#print ":", h
				for (k, v) in self._dict.iteritems():
					#print v.printYourself()
					return v.findWord(t)
				return self._null
			return self._dict.get(h).findWord(t)	

	def printYourself(self, level=0):
		if self._level == 0:
			for (k, v) in self._dict.iteritems():
				print (u"  " * level + k + u" " + ustr(v)).encode("utf-8")
		else:
			for (k, v) in self._dict.iteritems():
				print (u"  " * level + k + u":").encode("utf-8")
				v.printYourself(level + 1)

class SortedWordDictionary(WordDictionary):

	def __init__(self, level=2, null=None):
		WordDictionary.__init__(self, level=level, null=null)
		self.__keys = []
		self.__exact = False
		self.__sorting = True

	def disableSorting(self):
		self.__sorting = False

	def enableSorting(self):
		self.__sorting = True

	def sortAll(self):
		if self._level == 0:
			self.__sort()
		else:
			for (k, v) in self._dict.iteritems():
				v.sortAll()

	def exact(self):
		return self.__exact

	def __sort(self):
		collator = icu.Collator.createInstance(icu.Locale('pl_PL.UTF-8'))
		self.__keys = sorted(self.__keys, cmp=lambda a, b: collator.compare(a, b))

	def addWord(self, key, value):	
		if self._level == 0:
			self._dict.setdefault(key, value)
			self.__keys.append(key)
			if self.__sorting:
				self.__sort()
		else:
			h = self._at(key, 0)
			if h != u'':
				t = key[1:]
			else:
				t = u''
			if self._dict.get(h) == None:
				self._dict.setdefault(h, SortedWordDictionary(self._level - 1))
				self.__keys.append(h)
				if self.__sorting:
					self.__sort()
			self._dict.get(h).addWord(t, value)

	def findWord(self, key):
		self.__exact = False
		collator = icu.Collator.createInstance(icu.Locale('pl_PL.UTF-8'))
		if self._level == 0:
			res = self._dict.get(key)
			if res != None:
				self.__exact = True
				return res
			for k in self.__keys:
				#print "  ", k, key
				if collator.compare(k, key) > 0:
					return self._dict.get(k)
			return None
		else:
			h = self._at(key, 0)
			if h != u'':
				t = key[1:]
			else:
				t = u''
			subdict = self._dict.get(h)
			if subdict != None:
				res = subdict.findWord(t)
				if res != None:
					self.__exact = subdict.exact()
					return res
			first = True
			for k in self.__keys:
				#print "L", k, key
				if collator.compare(k, h) > 0:
					res = self._dict.get(k).findWord(u'')
					if res != None:
						return res
			return None

	def printYourselfFlat(self, level=0):
		if self._level == 0:
			for k in self.__keys:
				print self._dict.get(k)
		else:
			for k in self.__keys:
				self._dict.get(k).printYourself()

