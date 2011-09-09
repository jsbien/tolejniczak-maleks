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

from xml.dom import Node

def repeat(string, num):
	res = ""
	for _ in range(0, num):
		res += string
	return res

class Notifier(object):

	def __init__(self):
		self._listeners = []

	def addListener(self, li):
		self._listeners.append(li)

def nvl(obj):
	if obj == None:
		return ""
	return str(obj)

# clazz powinna miec typ unicode
def getElementsByClassName(doc, clazz):
	els = doc.getElementsByTagName(u"*")
	res = []
	for el in els:
		try:
			classes = el.attributes[u"class"].value.split(u" ")
			for c in classes:
				if c == clazz:
					res.append(el)
		except KeyError:
			continue
	return res

def getBbox(hOCRDomElement):
	try:
		title = hOCRDomElement.attributes[u"title"].value
		els = title.split(u";")
		bbox = [0, 0, 0, 0]
		for el in els:
			if el.find(u"bbox") != -1:
				coords = el.lstrip().split(u" ")
				bbox = [int(coords[1]), int(coords[2]), int(coords[3]), int(coords[4])]
				break
	except KeyError:
		return [0, 0, 0, 0]
	return bbox

def getTextContent(domElement):
	if domElement.nodeType == Node.TEXT_NODE:
		return domElement.nodeValue
	else:
		res = u""
		for c in domElement.childNodes:
			res += getTextContent(c)
		return res

