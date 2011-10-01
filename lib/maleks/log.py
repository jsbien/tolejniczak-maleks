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

PATH = None

from maleks.maleks.useful import ustr

def startLog(absolutePath):
	global PATH
	f = open(absolutePath + "/log.txt", "w")
	PATH = absolutePath + "/log.txt"
	f.write("")
	f.close()

def log(l):
	global PATH
	if PATH == None:
		return
	f = open(PATH, "a")
	for el in l:
		if isinstance(el, unicode):
			f.write(el)
		else:
			f.write(str(el))
		f.write(" ")
	f.write("\n")
	f.close()

