import os
import sys

def parent(path):
	els = path.split("/")
	res = ""
	for el in els[:-1]:
		if els == "":
			continue
		res += "/" + el
	return res

__RESOURCES_PATH__ = parent(os.path.abspath(os.path.dirname(sys.argv[0]))) + "/share/maleks/res"

