# encoding=UTF-8
# Copyright © 2011, 2012 Tomasz Olejniczak <tomek.87@poczta.onet.pl>
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
import shutil
import sys
import time
from maleks.maleks.registers import TaskRegister
from maleks.maleks.useful import repeat, getElementsByClassName, getBbox, getTextContent
from xml.dom import minidom

# TODO: C usuwanie cyklicznosci przy niszczeniu obiektow

# fiszka
class Fiche(object):

	# idd - identyfikator fiszki (jednoznaczny, obliczany dynamicznie przy tworzeniu indeksu struktury)
	# path - nazwa pliku djvu z fiszka bez rozszerzenia, jest jednoczesnie nazwa pliku hOCR (dualnego) z fiszka bez rozszerzenia
	def __init__(self, idd, path):
		self.__id = idd
		self.__path = path
		self.__djVuPath = path + ".djvu"
		self.__metaPath = None # tu bedzie kiedys sciezka do XMP
		self.__hOCRPath = path + ".xml"
		self.__parent = None
	
	# identyfikator fiszki
	def getId(self):
		return self.__id

	# opis fiszki wyswietlany w wykazach
	# TODO: ? czy wykazy korzystaja gdzies z tego ze id = getLabel()
	def getLabel(self):
		return self.__id
	
	# ustawia element struktury w ktorym znajduje sie fiszka
	def setParent(self, parent):
		self.__parent = parent

	# element struktury (np. pudelko lub szufladka) w ktorym znajduje sie fiszka
	def getParent(self):
		return self.__parent

	# sciezka absolutna do pliku djvu z fiszka
	def getDjVuPath(self):
		return self.__parent.getPath() + os.sep + self.__djVuPath
	
	# sciezka absolutna do pliku hOCR z fiszka
	def getHOCRPath(self):
		return self.__parent.getPath() + os.sep + self.__hOCRPath

	# "sciezka" opisowa (zlozona z nazw elementow struktury i identyfikatora fiszki)
	# widoczna w panelu wykazow
	def getDescriptivePath(self):
		return self.__parent.getDescriptivePath() + "/" + self.__id

	# reprezentacja tekstowa fiszki
	def __str__(self):
		return self.__id + ": " + self.__djVuPath

	def __isnum(self, string):
		try:
			int(string)
		except ValueError:
			return False
		return True

	def __computeClone(self, path):
		els = path.split("_")
		if len(els) < 3 or els[-2] != "clone":
			i = 1
			while True:
				if not os.path.exists(self.__parent.getPath() + os.sep + path + "_clone_" + str(i) + ".djvu"):
					return path + "_clone_" + str(i)
				i += 1
		elif els[-2] == "clone" and self.__isnum(els[-1]):
			res = ""
			for j in range(0, len(els) - 2):
				res += els[j] + "_"
			i = 1
			while True:
				if not os.path.exists(self.__parent.getPath() + os.sep + res + "clone_" + str(i) + ".djvu"):
					return res + "clone_" + str(i)
				i += 1
		else:
			print els
			assert(False)
	
	def clone(self):
		path = self.__computeClone(self.__path)
		print path
		cloned = Fiche(path, path)
		self.__parent.addAfter(self, cloned)
		shutil.copyfile(self.getDjVuPath(), cloned.getDjVuPath())
		if os.path.exists(self.getHOCRPath()):
			shutil.copyfile(self.getHOCRPath(), cloned.getHOCRPath())
		return cloned

	# zwraca zawartosc tekstowa pierwszego wiersza w hOCR jezeli stosunek jego
	# dolnego bounding boxu do wysokosci strony jest mniejszy niz parametr
	# hocr_cut w pliku config.cfg
	# w ten sposob wybieramy tylko te pierwsze wiersze ktore sa "podejrzana" o
	# bycie opisem hasla na fiszce (znajduja sie zaraz przy gornej krawedzi
	# strony) - jezeli program do OCRu nie rozpoznal recznego dopisku z opisem
	# hasla to pierwszy wiersz jest pierwszym wierszem tekstu maszynowego
	# znajdujacego sie nizej
	def getHOCREntry(self, pct):
		if os.path.exists(self.getHOCRPath()):
			doc = minidom.parse(self.getHOCRPath())
			line = getElementsByClassName(doc, u"ocrx_line")
			page = getElementsByClassName(doc, u"ocr_page")
			if line == [] or page == []:
				return None
			lineBbox = getBbox(line[0])
			pageBbox = getBbox(page[0])
			if float(lineBbox[3]) / float(pageBbox[3]) < pct:
				return getTextContent(line[0])
		return None

# element struktury (np. pudelko, szufladka, porcja)
class StructureNode(object):

	# name - nazwa elementu (zdefiniowana w pliku z indeksem struktury)
	# path - ścieżka do katalogu z elementem
	def __init__(self, name, path):
		self.__name = name
		self.__path = path
		self.__children = []
		self.__parent = None

	# identyfikator elementu
	def getId(self):
		return self.getPath()

	# opis elementu widoczny w panelu wykazow
	def getLabel(self):
		return self.__name

	# ojciec elementu (katalog nadrzedny)
	def getParent(self):
		return self.__parent
	
	# ustawia ojca elementu
	def setParent(self, parent):
		self.__parent = parent
	
	# dzieci elementu (podkatalogi albo fiszki)
	def getChildren(self):
		return self.__children

	# dodaje dziecko elementu i ustawia w nim referencje do elementu
	def add(self, child):
		self.__children.append(child)
		child.setParent(self)

	def addAfter(self, after, child):
		i = self.__children.index(after)
		if i == len(self.__children):
			self.__children.append(child)
		else:
			self.__children.insert(i + 1, child)
		child.setParent(self)

	# sciezka absolutna do elementu
	def getPath(self):
		if self.__parent == None:
			return self.__path
		else:
			return self.__parent.getPath() + os.sep + self.__path

	# sciezka "opisowa" widoczna w panelu wykazow (zlozona z nazw elementow struktury)
	def getDescriptivePath(self):
		if self.__parent == None:
			return "/" + self.__name
		else:
			return self.__parent.getDescriptivePath() + "/" + self.__name
	
	# tekstowa reprezentacja elementu
	def __str__(self):
		return self.__path + ": " + self.__name

	#def addClonedFiche(self, original, clone):
	#	index = self.__children.index(original)
	#	if index == len(self.__children) - 1:
	#		self.__children.append(clone)
	#	else:
	#		self.__children.insert(index, clone)

	# zwraca pierwsza fiszke w elemencie w porzadku naturalnym
	def firstFiche(self):
		if isinstance(self.__children[0], Fiche):
			return self.__children[0]
		else:
			return self.__children[0].firstFiche()

# konfiguracja (reprezentuje zawartosc pliku konfiguracyjnego kartoteki)
class Configuration(object):

	# otwiera plik o sciezce abspath i laduje z niego konfiguracje
	def __init__(self, abspath):
		# TODO: C obsluga bledow w pliku
		self.__dict = {}
		self.__abspath = abspath
		if os.path.exists(abspath + os.sep + "config.cfg"):
			f = open(abspath + os.sep + "config.cfg")
			for line in f:
				if line == "\n":
					continue
				line = line.strip()
				(k, v) = line.split("\t")
				self.__dict.setdefault(k, v)
			f.close()

	# odczytaj z konfiguracji wartosc k, jezeli nie ma to uzyj wartosci default
	def get(self, k, default=None):
		if self.__dict.get(k) == None:	
			return default
		else:
			return self.__dict.get(k)
	
	# zwraca domyslny wykaz zadaniowy (zdefiniowany w pliku konfiguracyjnym i
	# znajdujacy sie w karotece) lub wykaz pusty jesli takiego wykazu nie ma
	def getDefaultTaskRegister(self, index):
		# TODO: C komunikat o bledzie - nie ma takiego pliku
		path = self.__dict.get("default_task_register")
		if path != None:
			tr = TaskRegister(self.__abspath + os.sep + path, index)
			return tr
		else:
			return TaskRegister(None, None, empty=True)

	# konfiguruje kontroler bazy danych na podstawie konfiguracji karotetki
	# (pola z konfiguracji kartoteki przeslaniaja pola z globalnej konfiguracji)
	def configureDatabase(self, dBController):
		user = self.__dict.get("dbuser")
		db = self.__dict.get("db")
		passwd = self.__dict.get("dbpass")
		host = self.__dict.get("dbhost")
		port = self.__dict.get("dbport")
		if port != None:
			port = int(port)
		dBController.setPerDocumentConnection(db, user, passwd, host, port)

# indeks struktury
class StructureIndex(object):

	def diff(self):
		res = str(time.time() - self.__snapshot)
		self.__snapshot = time.time()
		return res

	# tworzy indeks struktury na podstawie pliku z indeksem struktury o sciezce
	# abspath
	def __init__(self, abspath, dBController=None):
		# TODO: C obsluga bledow w pliku
		self.__snapshot = time.time()
		sys.stderr.write('Tworzenie indeksu struktry ' + self.diff() + '\n')
		self.__ficheNo = 0
		self.__alphabetic = False
		self.__fiches = []
		self.__ficheDict = {}
		self.__nodeDict = {}
		self.__tree = StructureNode(abspath.split(os.sep)[-1], abspath)
		curNode = self.__tree
		self.__nodeDict.setdefault(curNode.getId(), curNode)
		f = open(abspath + os.sep + "index.ind")
		sys.stderr.write('Otwarto plik z indeksem ' + self.diff() + '\n')
		for line in f:
			sys.stderr.write(line + ' ' + self.diff() + '\n')
			if line == "\n":
				continue
			line = line.strip()
			sys.stderr.write('Stripped ' + self.diff() + '\n')
			if line == "$alphabetic":
				self.__alphabetic = True
			elif line[0:2] == "$ ":
				sys.stderr.write('Poczatek katalogu ' + self.diff() + '\n')
				els = line[2:].split("\t")
				sel = StructureNode(els[0], els[1])
				curNode.add(sel)
				curNode = sel
				self.__nodeDict.setdefault(sel.getId(), sel)
				sys.stderr.write('Poczatek katalogu - koniec ' + self.diff() + '\n')
			elif line == "$end":
				sys.stderr.write('Koniec katalogu ' + self.diff() + '\n')
				curNode = curNode.getParent()
				sys.stderr.write('Koniec katalogu - koniec ' + self.diff() + '\n')
			else:
				sys.stderr.write('Przetwarzanie plikow ' + self.diff() + '\n')
				# TODO: C inne opcje
				els = line.split("\t")
				if els[0] == "$from_names_djvu":
					sys.stderr.write('Przetwarzanie plikow from names ' + self.diff() + '\n')
					if els[1] == "$all":
						if dBController == None:
							key = lambda x: x
						else:
							key = lambda x: dBController.getPositionOfFiche(x[:-5]) if (len(x) > 5 and x[-5:] == ".djvu") else 0
						sys.stderr.write('Lambda ' + self.diff() + '\n')
						for filee in sorted(os.listdir(curNode.getPath()), key=key):
							#sys.stderr.write(filee + ' ' + self.diff() + '\n')
							if len(filee) > 5 and filee[-5:] == ".djvu":
								#sys.stderr.write('Len ok ' + self.diff() + '\n')
								fq = Fiche(filee[:-5], filee[:-5])
								curNode.add(fq)
								self.__fiches.append(fq)
								self.__ficheDict.setdefault(fq.getId(), (fq, self.__ficheNo)) # TODO: D wlaczyc numer do fiszki?
								self.__ficheNo += 1
				else:
					sys.stderr.write('Shouldn\'t happen ' + self.diff() + '\n')
					fq = Fiche(els[0], els[1])
					curNode.add(fq)
					self.__fiches.append(fq)
					self.__ficheDict.setdefault(fq.getId(), (fq, self.__ficheNo))
					self.__ficheNo += 1
		f.close()
		#print self.__ficheDict
	
	def clone(self, ficheId):
		(fiche, ficheNo) = self.__ficheDict[ficheId]
		clone = fiche.clone()
		if ficheNo == len(self.__fiches) - 1:
			self.__fiches.append(clone)
		else:
			self.__fiches.insert(ficheNo + 1, clone)
			self.__ficheDict[clone.getId()] = (clone, ficheNo + 1)
			for i in range(ficheNo + 2, len(self.__fiches)):
				fq = self.__fiches[i]
				self.__ficheDict[fq.getId()] = (fq, i)
		self.__ficheNo += 1
		return clone.getId()

	# zwraca fiszke o danym numerze kolejnym w porzadku naturalnym
	def getFiche(self, ficheNo):
		return self.__fiches[ficheNo]

	# zwraca liczbe wszystkich fiszek w kartotece
	def getFicheNo(self):
		return self.__ficheNo
	
	# zwraca numer kolejny fiszki o danym identyfikatorze (Fiche.getId()) w porzadku naturalnym
	def getFicheNoById(self, ficheId):
		try:
			return self.__ficheDict[ficheId][1]
		except KeyError:
			print ficheId
			raise
	
	# zwraca fiszke o danym identyfikatorze (Fiche.getId())
	def getFicheById(self, ficheId):
		try:
			return self.__ficheDict[ficheId][0]
		except KeyError:
			print ficheId
			raise

	# zwraca element struktury o danym identyfikatorze (StructureElement.getId())
	def getNodeById(self, nodeId):
		try:
			return self.__nodeDict[nodeId]
		except KeyError:
			print nodeId
			raise
	
	# zwraca element struktury reprezentujacy cala kartoteke
	def getRoot(self):
		return self.__tree

	# dla danego elementu struktury (ficheParent) znajduje pierwsza fiszke w
	# porzadku naturlanym po wszystkich fiszkach zawartym w danym elemencie;
	# jezeli takiej fiszki nie ma zwraca None
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

	# zwraca True jezeli fiszki w kartotece sa uporzadkowane w kolejnosci alfabetycznej
	# (jak w fiszkach z Ratuszowej)
	# wpp zwraca False
	def isAlphabetic(self):
		return self.__alphabetic

	# otwiera wykaz zadaniowy znajdujacy sie w pliku pod dana sciezka
	# TODO: C czy moga tu wystapic jakies bledy?
	def getTaskRegisterFromFile(self, path):
		res = TaskRegister(None, None, empty=True)
		f = open(path)
		for line in f:
			if line == "\n" or line[0] == "#":
				continue
			line = line.strip()
			res.append(self.getFicheById(line))
		f.close()
		return res

#si = StructureIndex("/home/to/fajny")
#def traverse(el, level=0):
#	if isinstance(el, fiche):
#		print el
#	else:
#		print el
#		for e in el.getChildren():
#			traverse(e, level=level+1)
#traverse(si.getRoot())

