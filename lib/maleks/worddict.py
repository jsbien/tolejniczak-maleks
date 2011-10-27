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

def commonprefix(a, b):
	pref = u""
	for i in range(0, min(len(a), len(b))):
		if a[i] != b[i]:
			break
		pref += a[i] 
	return pref

class WordDictionary:

	def __init__(self, level):
		self.__dict = {}
		self.__level = level
	
	def __at(self, word, i):
		if i >= len(word):
			return ''
		else:
			return word[i]

	def addWord(self, key, value):	
		if self.__level == 0:
			self.__dict.setdefault(key, value)
		else:
			h = self.__at(key, 0)
			if h != u'':
				t = key[1:]
			else:
				t = u''
			if self.__dict.get(h) == None:
				self.__dict.setdefault(h, WordDictionary(self.__level - 1))
			self.__dict.get(h).addWord(t, value)

	def findWord(self, key):
		if self.__level == 0:
			lcp = u""
			hint = u""
			for (k, v) in self.__dict.iteritems():
				lcpnew = commonprefix(key, k)
				if len(lcpnew) >= len(lcp):
					hint = v
					lcp = lcpnew
			return hint
		else:
			h = self.__at(key, 0)
			if h != u'':
				t = key[1:]
			else:
				t = u''
			if self.__dict.get(h) == None:
				#print ":", h
				for (k, v) in self.__dict.iteritems():
					#print v.printYourself()
					return v.findWord(t)
				return (u"", u"")
			return self.__dict.get(h).findWord(t)

	def printYourself(self, level=0):
		if self.__level == 0:
			for (k, v) in self.__dict.iteritems():
				print (u"  " * level + k + u" " + v).encode("utf-8")
		else:
			for (k, v) in self.__dict.iteritems():
				print (u"  " * level + k + u":").encode("utf-8")
				v.printYourself(level + 1)

