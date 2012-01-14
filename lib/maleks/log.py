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
from maleks.maleks.useful import fstr, stru
from time import ctime

DEBUG = "DEBUG"
OP = "OP"
DB = "DB"
QUERY = "QUERY"
DBaQ = "DBaQ"
NONE = "NONE"

path = None
dirPath = None
level = OP

def setLevel(lev):
	global level
	level = lev

def startLog(absolutePath):
	global path, dirPath
	mod = 0
	dirPath = absolutePath
	absolutePath = os.path.abspath(absolutePath) # TODO: C potrzeba? (skad sie bierze path w do_open)?
	while os.path.exists(absolutePath + os.sep + "log_" + str(mod) + ".txt"):
		mod += 1
	f = open(absolutePath + os.sep + "log_" + str(mod) + ".txt", "w")
	path = absolutePath + os.sep + "log_" + str(mod) + ".txt"
	f.write("")
	f.close()

def dumpDatabase(dump):
	global path
	if level == NONE:
		return
	if path == None:
		return
	f = open(path, "a")
	f.write(dump)
	f.close()

def op(label, l, idd):
	global level
	if level == NONE:
		return
	__log("OP: " + label.upper(), l, idd, True)

def opr(label, l, idd):
	global level
	if level == NONE:
		return
	__log("OP: " + label, l, idd, True)

def db(label, l, idd):
	global level
	if level in [DB, DBaQ]:
		__log(label, l, idd)

def query(label, l, idd):
	global level
	if level in [QUERY, DBaQ]:
		__log(label, l, idd)

def log(label, l, idd):
	global level
	if level in [DEBUG, DB, QUERY, DBaQ]:
		__log(label, l, idd)

def __log(label, l, idd, op=False):
	global path
	if path == None:
		return
	f = open(path, "a")
	f.write(("" if op else "    ") + label + " (")
	f.write(str(idd) + ") " + str(ctime()) + ": ")
	for el in l:
		if isinstance(el, unicode):
			f.write(stru(el))
			f.write(": <type 'unicode'>")
		elif isinstance(el, list):
			f.write(str(el))
			f.write("(" + str(len(el)) + "): <type 'list'>")
		else:
			f.write(str(el) + ": ")
			f.write(str(type(el)))
		f.write("; ")
	f.write("\n")
	f.close()

