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

# TODO: C usuwanie cyklicznosci (python ma problemy z odzyskiwaniem pamieci
# jezeli w programie sa cykliczne referencje)

import wx
import os
from maleks.maleks.useful import nvl

# elementy: wx.ListItem, item, itemId
# fiszki: maleks.maleks.fiche.Fiche, element, elementId

# zaznaczenie jakiegos elementu w czasie wyszukiwania binarnego nie spowodowane
# przez ktoras z metod obslugujacych wyszukiwanie binarne powoduje przerwanie
# go:
#		if self._binary:
#			for l in self._listeners:
#				l.stop_binary_search()
# (ten fragment jest na poczatku wielu metod)

# widok wykazu zadaniowego - klasa ta stanowi jednoczesnie nadklase dla innych wykazow ktore
# wykorzystuja ja do wyszukiwania binarnego i przyrostowego na poziomie fiszek
class RegisterBrowser(wx.ListView):
	
	def __init__(self, *args, **kwargs):
		wx.ListView.__init__(self, *args, **kwargs)
		self.InsertColumn(0, '', width=300) # w tej kolumnie bedzie opis fiszki
		self.InsertColumn(1, '', width=15) # te dwie kolumny sa uzywane do wyswietlania
		self.InsertColumn(2, '', width=15) # informacji na temat przebiegu wyszukiwania binarnego
		self.InsertColumn(3, '', width=wx.LIST_AUTOSIZE) # w tej kolumnie bedzie haslo ktore jest
			# na fiszce (jezeli odpowiednia informacja jest w indeksie)
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onSelect, self)
		self._listeners = []
		self._itemsNo = 0
		self.reset()

	# calkowicie resetuje widok - po wywolaniu tej metody jest on w tym samym
	# stanie co zaraz po utworzeniu przez konstruktor
	def reset(self):
		self.DeleteAllItems()
		self._veto = False # patrz onSelect()
		self._selected = None # identyfikator aktualnie zaznaczonego elementu
		self._binary = False
		self.__left = 0
		self.__right = 0
		self.__center = 0
		self.__programmaticSelect = False # patrz onSelect()
		self._initialized = False # patrz isActive()

	def binaryAvailable(self):
		return True

	# w widoku jest zaznaczona jakas fiszka i pojecie 'nastepnej fiszki' ktora
	# zostanie wyswietlona w panelu glownym po zaakceptowaniu aktualnie zaznaczonej
	# fiszki
	# dla wykazu zadaniowego zawsze jest to prawda
	def allowsNextFiche(self):
		return True
	
	# dodaje listener - jest to w tej chwili tylko glowne okno programu
	def addListener(self, lsn):
		self._listeners.append(lsn)
	
	# usuwa wszystkie elementy widoku
	def DeleteAllItems(self):
		wx.ListCtrl.DeleteAllItems(self)
		self._items = []
		self._item2element = {} # mapowanie z identyfikatorow elementow na identyfikatory fiszek
		self._element2item = {} # vice versa

	# czy widok wykazu zostal wypelniony jakimis elementami (jest tak jezeli kartoteka
	# zostala poprawnie otwarta)
	def isActive(self):
		return self._initialized

	def _map(self, i):
		return i

	def _unmap(self, i):
		return i
	
	# wypelnia widok wykazu elementami odpowiadajacymi fiszkom z wykazu zadaniowego reg
	# getEntry to funkcja ktora dla identyfikatora danej fiszki zwraca haslo na tej fiszce (jezeli indeks hasel dla tej
	# fiszki jest wypelniony)
	def setRegister(self, reg, getEntry=None):
		if self._binary:
			for l in self._listeners:
				l.stop_binary_search()
		self.reset()
		i = 0
		self._itemsNo = 0
		for element in reg: # dla kazdej fiszki w wykazie utworz odpowiedni element i wypelnij slowniki
			#print element
			self.InsertStringItem(i, self._shownLabel(element))
			self.SetStringItem(i, 1, "")
			self.SetStringItem(i, 2, "")
			self.SetStringItem(i, 3, self._secondColumn(element, getEntry))
			self._items.append(i) # identyfikator elementu jest jednoczesnie jego indeksem w tablicy _items
			self._itemsNo += 1
			self._item2element.setdefault(i, self._id(element))
			self._element2item.setdefault(self._id(element), i)
			self._customElementInitialization(element, i)
			i += 1
		self.SetColumnWidth(0, wx.LIST_AUTOSIZE) # dopasuj szerokosc kolumn do
		self.SetColumnWidth(3, wx.LIST_AUTOSIZE) # ich zawartosci
		self._initialized = True

	def _itemsLen(self):
		return self._itemsNo

	def _itemOf(self, elementId):
		return self._element2item.get(elementId)

	def _elementOf(self, itemId):
		return self._item2element.get(itemId)

	def _customElementInitialization(self, element, i):
		pass
	
	def _label(self, element):
		return element.getLabel()

	def _shownLabel(self, element):
		return self._label(element)
	
	def _id(self, element):
		return element.getId()

	def _secondColumn(self, element, getEntry):
		if getEntry == None:
			return ""
		else:
			return nvl(getEntry(self._id(element)))

	# identyfikator fiszki ktorej odpowiada dany element widoku wykazu
	def __getElementId(self, item):
		return self._elementOf(item.GetId())
	
	# zaznaczono element - metoda ta jest wywolywana zarowno w przypadku klikniecia
	# na element widoku wykazu lub przejscia na element przy uzyciu strzalki jak
	# rowniez w przypadku zaznaczenia przez wx.ListView.Select() w ktorejs z metod
	# klasy RegisterBrowser
	def onSelect(self, event):
	#mapsafe
		if self._binary and (not self.__programmaticSelect): # wyszukiwanie binarne jest
				# aktywne - w takim przypadku nalezy je wylaczyc (zaznaczenie fiszki w czasie
				# wyszukiwania binarnego przerywa je)
				# jezeli flaga self.__programmaticSelect jest wlaczona, to znaczy, ze element
				# nie zostal zaznaczony przez akcje uzytkownika w GUI lecz przez jedna z
				# metod odpowiedzialna za przebieg wyszukiwania binarnego i nie nalezy go przerywac
			#self.stopBinarySearch()
			for l in self._listeners:
				l.stop_binary_search() # powiadom o przerwaniu wyszukiwania binarnego
		if not self._veto: # w niektorych metodach po zaznaczeniu elementu nie chcemy
			# powiadamiac o zaznaczeniu elementu bo jest on zaznaczany przez okno glowne
			# wiec nie ma potrzeby powiadamiania go o tym fakcie - wtedy ustawiamy flage _veto;
			# poniewaz w takiej sytuacji self._selected = itemId nie jest wykonywane w
			# metodzie onSelect trzeba je wykonac w metodzie wywolujacej wx.ListView.Select
			itemId = self._unmap(event.GetIndex()) # TODO: NOTE http://wxpython-users.1045709.n5.nabble.com/wx-ListCtrl-Item-Information-on-Double-Click-td3394264.html
			self._selected = itemId
			elementId = self._elementOf(itemId)
			self._element_selected(elementId) # TODO: NOTE to wywoluje zmiane strony a
				# w konsekwencji RegisterBrowser.select - zatem dany element jest zaznaczany
				# dwa razy (to nie powoduje jakichs duzych problemow)

	# zaznaczono fiszke o identyfikatorze elementId
	# wydzielone w osobna metode od onSelect glownie po to, zeby mozna nadpisywac w podklasach - jest
	# tez uzywana w _select
	# jezeli notify jest ustawione na False, to okno glowne po zmianie strony nie
	# wywoluje RegisterBrowser.select
	# TODO: NOTE roznica miedzy _veto w onSelect a notify = False polega na tym
	# ze w pierwszym przypadku wogle nie powiadamiamy okna glownego o zaznaczeniu
	# fiszki a w drugim powiadamiamy, ale ono nie wywoluje RegisterBrowser.select
	def _element_selected(self, elementId, notify=True):
	#mapsafe
		for l in self._listeners:
			l.on_reg_select(elementId, notify=notify) # powiadom o zaznaczeniu elementu
	
	# odznacz element o danym identyfikatorze
	def _unselect(self, itemId):
	#mapsafe
		self._selected = None
		self.Select(self._map(itemId), on=False)
	
	# zaznacz element o danym identyfikatorze
	# jezeli veto = True to nie powiadamiaj glownego okna o zaznaczaniu elementu
	def _select(self, itemId, veto=False):
	#mapsafe
		self.EnsureVisible(itemId)
		if veto:
			self._veto = True # ustaw flage dla onSelect
			self._selected = itemId # TODO: NOTE bo z powodu veto nie bedzie ustawione w onSelect
				# TODO: C jakos przeniesc do onSelect
		self.Select(self._map(itemId)) # powoduje wywolanie onSelect
		if self._binary: # TODO: NOTE onSelect (spowodowane przez akcje uzytkownika w GUI)
			# w trybie binarnym powoduje wyjscie z wyszukiwania binarnego; onSelect spowodowane
			# przez metode obslugujaca wyszukiwanie binarne nie robi nic (bo _veto i __programmaticSelect)
			# sa ustawione i trzeba recznie ustawic zmienna _selected oraz powiadomic glowne
			# okno:
			# (TODO: C przeniesc do onSelect pod warunkiem if __programmaticSelect)
			self._selected = itemId
			self._element_selected(self._elementOf(itemId), notify=False) # notify = False
				# zeby nie wywolac cyklu
		if veto:
			self._veto = False

	# zaznacz fiszke o danym identyfikatorze
	def select(self, elementId):
	#mapsafe
		if self._binary: # jesli binarne aktywne - przerwij
			#self.stopBinarySearch()
			for l in self._listeners:
				l.stop_binary_search()
		if self._selected != None:
			self._unselect(self._selected)
		itemId = self._itemOf(elementId)
		#print "select", itemId, elementId
		if itemId != None:
			self._select(itemId, veto=True) # veto=True bo ta metoda jest wywolywana
				# z okna glownego wiec nie ma potrzeby powiadamiac go o zaznaczeniu
				# elementu (bo to ono go zaznacza wiec wie o tym)

	# jakis element jest zaznaczony
	def hasSelection(self):
		return self._selected != None

	# zwroc nastepna fiszke po zaznaczonej
	def getNextFiche(self, entry=None):
		if self._binary: # jezeli binarne jest wlaczane to wylaczamy
			#self.stopBinarySearch()
			for l in self._listeners:
				l.stop_binary_search()
		if self._selected != None:
			itemId = self.GetNextItem(self._selected)
			if itemId != -1:
				self._unselect(self._selected)
				self._select(itemId, veto=True) # veto=True - nie chcemy wywolac onSelect
					# z _veto=False bo spowodowaloby to _element_selected z notify ustawionym
					# na True
				self._element_selected(self._elementOf(itemId), notify=False) # notify
					# = False bo nie ma potrzeby wywolywania RegisterBrowser.select (bo
					# odpowiedni element zostal przed chwila zaznaczony)
			else:
				self._nextFicheNotFound()

	# co robic jesli nie znaleziono fiszki w getNextFiche?
	# (metoda przeslaniana w niektorych podklasach, np. wykaz struktury moze
	# wybrac inny element struktyry i w nim poszukac nastepnej fiszki)
	def _nextFicheNotFound(self):
		pass

	#def selectPrevElement(self):
	#	#if self._binary:
	#	#	return
	#	if self._selected == None:
	#		return
	#	itemId = -1
	#	prev = -1
	#	while True:
	#		itemId = self.GetNextItem(itemId)
	#		if itemId == self._selected.GetId():
	#			if prev != -1:
	#				self._unselect(self._selected)
	#				self._select(prev)
	#				return
	#		prev = itemId
	#		if itemId == -1:
	#			break

	# znajdz element ktorego etykieta (napis w pierwszej kolumnie bedacy opisem
	# fiszki) ma prefix rowny text (text - napis w okienku wyszukiwania w panelu
	# wykazow)
	# zwraca identyfikator elementu lub -1 jezeli takiego elementu nie ma
	#def findItem(self, column, text):
	#	for i in self._items:
	#		item = self.GetItem(i, column)
	#		if os.path.commonprefix([item.GetText(), text]) == text:
	#			return i
	#	return -1

	# zaznacz element ktorego etykieta (napis w pierwszej kolumnie bedacy opisem
	# fiszki) ma prefix rowny text (text - napis w okienku wyszukiwania w panelu
	# wykazow)
	def find(self, text):
		if self._binary: # jezeli binarne to przerywamy je
			#self.stopBinarySearch()
			for l in self._listeners:
				l.stop_binary_search()
		itemId = self.FindItem(-1, text, partial=True)
		#itemId = self.findItem(2, text)
		if itemId != -1:
			if self._selected != None:
				self._unselect(self._selected)
			self._select(itemId)

	def binarySearchActive(self):
		return self._binary

	def stopBinarySearch(self, restart=None):
		self._binary = False
		self.__unmarkScope()
	
	# zaznacz srodkowy element w wyszukiwaniu binarnym
	def __selectCenter(self):
		# TODO: D co jak lenn == 0?
		lenn = self.__right - self.__left + 1
		if self.__left == self.__right == self.__center: # przedzial ograniczony do
			# jednego elementu - konczymy wyszukiwanie
			for l in self._listeners:
				l.stop_binary_search()
			return
		self.__center = self.__left
		self.__center += lenn // 2
		if self._selected != None:
			self._unselect(self._selected)
		self.__programmaticSelect = True # ustawiamy ta flage by onSelect nie przerwal
			# wyszukiwania binarnego w wyniku zaznaczenia elementu (bo zaznaczenie
			# przez metode obslugujaca wyszukiwanie binarne a nie uzytkownika)
		self._select(self._items[self.__center], veto=True) # patrz komentarz do
			# fragmentu metody _select pod warunkiem if self._binary
		self.__programmaticSelect = False
		if self.__left == self.__right == self.__center: # przedzial ograniczony do
			# jednego elementu - konczymy wyszukiwanie
			for l in self._listeners:
				l.stop_binary_search()

	# wyswietla aktualnie aktywny przedzial w wyszukiwaniu binarnym
	def __markScope(self):
		for i in self._items:
			if i >= self.__left and i <= self.__right:
				self.SetStringItem(i, 1, "*")
			else:
				self.SetStringItem(i, 1, "")
				
	# usun wszelkie informacje pomocnicze do wyszukiwania binarnego (przedzial
	# i historie)
	def __unmarkScope(self):
		for i in self._items:
			self.SetStringItem(i, 1, "")
			self.SetStringItem(i, 2, "")

	# zacznij wyszukiwanie binarne i inicjalizuj odpowiednie zmienne
	# target - wykorzystywany tylko przez NewEntryRegisterBrowser
	def startBinarySearch(self, target=None, restarting=False):
		self._binary = True
		self.__left = 0
		self.__right = len(self._items) - 1
		self.__markScope()
		self.__selectCenter()

	def nextBinary(self):
		self.__left = self.__center
		self.SetStringItem(self.__center, 2, ">") # zaznacz historie wyszukiwania
		self.__markScope()
		self.__selectCenter()

	def prevBinary(self):
		if self.__left == self.__right: # przedzial ograniczony do jednego elementu -
			# konczymy
			return # TODO: A cos tu jest nie tak! a gdzie wylaczenie wyszukiwania binarnego?
		self.__right = self.__center - 1
		self.SetStringItem(self.__center, 2, "<") # zaznacz historie wyszukiwania
		self.__markScope()
		self.__selectCenter()

	# czy wyszukiwanie binarne odbywa sie z celem - uzywane tylko w NewEntryRegisterBrowser
	def hasTarget(self):
		return False

	# zaznacz pierwszy element - tu nic nie robi (bo do pierwszego i ostatniego
	# elementu mozna nawigowac myszka lub Home/End), ale wykorzystywane w podklasie
	# EntryRegisterBrowser
	def showFirstElement(self):
		pass

	# zaznacz ostatni element - tu nic nie robi (bo do pierwszego i ostatniego
	# elementu mozna nawigowac myszka lub Home/End), ale wykorzystywane w podklasie
	# EntryRegisterBrowser
	def showLastElement(self):
		pass

