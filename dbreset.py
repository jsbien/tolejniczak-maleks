#encoding=utf-8

from maleks.maleks.fiche import Configuration
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
	cfg = Configuration(path)
	cfg.configureDatabase(dbController)
	dbController.reset()
	print "baza zresetowana"
else:
	print sys.argv[1], "nie jest katalogiem"

