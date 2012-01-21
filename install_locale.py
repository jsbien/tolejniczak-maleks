#!/usr/bin/python

import os

process = os.popen("whereis maleks")
path = process.readline()
process.close()
els = path.split("/")
res = ""
for i in range(1, len(els) - 1):
	res += "/" + els[i]
os.system("cp -r locale " + res)

