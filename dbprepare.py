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
	dbController = DBController(config)
	index = StructureIndex(path)
	cfg = Configuration(path)
	cfg.configureDatabase(dbController)
	def __traverse(node):
		if isinstance(node, Fiche):
			dbController.addFicheToFichesIndex(node.getId())
		else:
			for c in node.getChildren():
				__traverse(c)
	__traverse(index.getRoot())
else:
	print sys.argv[1], "nie jest katalogiem"

