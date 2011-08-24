# encoding=UTF-8
# Copyright © 2011 Tomasz Olejniczak <tomek.87@poczta.onet.pl>
#
# This package is free software; you can redistribute it and/or modify
# it under the terms of the GNU Library General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This package is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Library General Public License for more details.

def repeat(string, num):
	res = ""
	for _ in range(0, num):
		res += string
	return res

class Notifier(object):

	def __init__(self):
		self.__listeners = []

	def addListener(self, li):
		self.__listeners.append(li)

	def _notify(self, method):
		#for l in self.__listeners:
		pass

