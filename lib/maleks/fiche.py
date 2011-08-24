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
from useful import repeat

# TODO: C usuwanie cyklicznosci przy niszczeniu obiektow

class Fiche(object):

	def __init__(self, idd, djVuPath):
		self.__id = idd
		self.__djVuPath = djVuPath
		self.__metaPath = None
		self.__hOCRPath = None
		self.__parent = None
	
	def getId(self):
		return self.__id
	
	def getLabel(self):
		return self.__id
	
	def setParent(self, parent):
		self.__parent = parent
	
	def getDjVuPath(self):
		return self.__parent.getPath() + "/" + self.__djVuPath

	def __str__(self):
		return self.__id + ": " + self.__djVuPath

class StructureNode(object):

	def __init__(self, name, path):
		self.__name = name
		self.__path = path
		self.__children = []
		self.__parent = None

	def getParent(self):
		return self.__parent
	
	def setParent(self, parent):
		self.__parent = parent
	
	def getChildren(self):
		return self.__children

	def add(self, child):
		self.__children.append(child)
		child.setParent(self)

	def getPath(self):
		if self.__parent == None:
			return self.__path
		else:
			return self.__parent.getPath() + "/" + self.__path
	
	def __str__(self):
		return self.__path + ": " + self.__name

class Configuration(object):

	def __init__(self, abspath):
		# TODO: C obsluga bledow w pliku
		self.__dict = {}
		self.__abspath = abspath
		f = open(abspath + "/config.cfg")
		for line in f:
			if line == "\n":
				continue
			line = line.strip()
			(k, v) = line.split("\t")
			self.__dict.setdefault(k, v)
		f.close()
	
	def getDefaultTaskRegister(self, index):
		# TODO: C komunikat o bledzie - nie ma takiego pliku
		path = self.__dict.get("default_task_register")
		if path != None:
			tr = TaskRegister(self.__abspath + "/" + path, index)
			return tr
		else:
			return path

class TaskRegister(object):

	def __init__(self, abspath, index):
		self.__ids = []
		f = open(abspath)
		for line in f:
			if line == "\n":
				continue
			line = line.strip()
			self.__ids.append(index.getFicheById(line))
		f.close()
	
	def __getitem__(self, ind):
		return self.__ids[ind]

class StructureIndex(object):

	def __init__(self, abspath):
		# TODO: C obsluga bledow w pliku
		self.__ficheNo = 0
		self.__fiches = []
		self.__ficheDict = {}
		self.__tree = StructureNode("Main index root", abspath)
		curNode = self.__tree
		f = open(abspath + "/index.ind")
		for line in f:
			if line == "\n":
				continue
			line = line.strip()
			if line[0:2] == "$ ":
				els = line[2:].split("\t")
				sel = StructureNode(els[0], els[1])
				curNode.add(sel)
				curNode = sel
			elif line == "$end":
				curNode = curNode.getParent()
			else:
				# TODO: C inne opcje
				els = line.split("\t")
				if els[0] == "$from_names_djvu":
					if els[1] == "$all":
						for filee in sorted(os.listdir(curNode.getPath())):
							if len(filee) > 5 and filee[-5:] == ".djvu":
								fq = Fiche(filee[:-5], filee)
								curNode.add(fq)
								self.__fiches.append(fq)
								self.__ficheDict.setdefault(fq.getId(), (fq, self.__ficheNo)) # TODO: D wlaczyc numer do fiszki?
								self.__ficheNo += 1
				else:
					fq = Fiche(els[0], els[1])
					curNode.add(fq)
					self.__fiches.append(fq)
					self.__ficheDict.setdefault(fq.getId(), (fq, self.__ficheNo))
					self.__ficheNo += 1
		f.close()

	def getFiche(self, ficheNo):
		return self.__fiches[ficheNo]

	def getFicheNo(self):
		return self.__ficheNo
	
	def getFicheNoById(self, ficheId):
		return self.__ficheDict[ficheId][1]
	
	def getFicheById(self, ficheId):
		return self.__ficheDict[ficheId][0]
	
	def getRoot(self):
		return self.__tree

#si = StructureIndex("/home/to/fajny")
#def traverse(el, level=0):
#	if isinstance(el, fiche):
#		print el
#	else:
#		print el
#		for e in el.getChildren():
#			traverse(e, level=level+1)
#traverse(si.getRoot())

