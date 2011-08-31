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
from djvusmooth.maleks.registers import TaskRegister
from djvusmooth.maleks.useful import repeat

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

	def getParent(self):
		return self.__parent

	def getDjVuPath(self):
		return self.__parent.getPath() + "/" + self.__djVuPath

	def getDescriptivePath(self):
		return self.__parent.getDescriptivePath() + "/" + self.__id

	def __str__(self):
		return self.__id + ": " + self.__djVuPath

class StructureNode(object):

	def __init__(self, name, path):
		self.__name = name
		self.__path = path
		self.__children = []
		self.__parent = None

	def getId(self):
		return self.getPath()

	def getLabel(self):
		return self.__name

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

	def getDescriptivePath(self):
		if self.__parent == None:
			return "/" + self.__name
		else:
			return self.__parent.getDescriptivePath() + "/" + self.__name
	
	def __str__(self):
		return self.__path + ": " + self.__name

	def firstFiche(self):
		if isinstance(self.__children[0], Fiche):
			return self.__children[0]
		else:
			return self.__children[0].firstFiche()

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
	
	# TODO: A co jak wogole nie ma zadnego wykazu zadaniowego?
	def getDefaultTaskRegister(self, index):
		# TODO: C komunikat o bledzie - nie ma takiego pliku
		path = self.__dict.get("default_task_register")
		if path != None:
			tr = TaskRegister(self.__abspath + "/" + path, index)
			return tr
		else:
			return path

class StructureIndex(object):

	def __init__(self, abspath):
		# TODO: C obsluga bledow w pliku
		self.__ficheNo = 0
		self.__fiches = []
		self.__ficheDict = {}
		self.__nodeDict = {}
		self.__tree = StructureNode(abspath.split("/")[-1], abspath)
		curNode = self.__tree
		self.__nodeDict.setdefault(curNode.getId(), curNode)
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
				self.__nodeDict.setdefault(sel.getId(), sel)
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

	def getNodeById(self, nodeId):
		return self.__nodeDict[nodeId]
	
	def getRoot(self):
		return self.__tree

	def findNextFiche(self, ficheParent):
		parent = self.__nodeDict[ficheParent.getId()]
		while True:
			if parent.getParent() == None:
				return None
			gparent = parent.getParent()
			i = gparent.getChildren().index(parent)
			if len(gparent.getChildren()) - 1 > i:
				return gparent.getChildren()[i + 1].firstFiche()
			parent = gparent
		return None

#si = StructureIndex("/home/to/fajny")
#def traverse(el, level=0):
#	if isinstance(el, fiche):
#		print el
#	else:
#		print el
#		for e in el.getChildren():
#			traverse(e, level=level+1)
#traverse(si.getRoot())

