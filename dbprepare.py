#encoding=utf-8

from maleks.maleks.fiche import StructureIndex, Configuration, Fiche
from maleks.db.db import DBController
from maleks import config
import sys
import os

if len(sys.argv) != 2:
	print "Zła liczba argumentów"
	exit()

if os.path.isdir(sys.argv[1]):
	path = sys.argv[1]
	if os.name == 'posix':
		legacy_path = os.path.expanduser('~/.Maleks')
	else:
		legacy_path = None
	config = config.Config('maleks', legacy_path)
	print 'Zaladowana konfiguracja'
	dbController = DBController(config)
	print 'Zainicjalizowane DAO'
	index = StructureIndex(path)
	print 'Zaladowany indeks struktury' 
	cfg = Configuration(path)
	print 'Zaladowana konfiguracja karotetki'
	cfg.configureDatabase(dbController)
	print 'Baza skonfigurowana'
	def __traverse(node):
		if isinstance(node, Fiche):
			dbController.addFicheToFichesIndex(node.getId())
		else:
			for c in node.getChildren():
				__traverse(c)
	__traverse(index.getRoot())
	print 'Utworzono indeks fiszek'
else:
	print sys.argv[1], "nie jest katalogiem"

