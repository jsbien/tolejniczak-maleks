import os
import shutil
import sys
from optparse import OptionParser

def spaces(level):
	res = ""
	for i in range(0, level):
		res += "\t"
	return res

def superdir(node):
	hasDirs = False
	hasFiles = False
	for filee in os.listdir(node):
		if os.path.isdir(node + os.sep + filee):
			hasDirs = True
		else:
			hasFiles = True
	if hasDirs and not hasFiles:
		return True
	elif hasFiles and not hasDirs:
		return False
	elif not hasFiles and not hasDirs:
		print "pusty katalog: " + node
		return True
	else:
		print "pliki w podkatalogu nie bedacym lisciem: " + node
		return True

def printStructureNode(fout, level, node, name, root=False):
	if not root:
		fout.write(spaces(level) + "$ " + name + "\t" + name + "\n")
	if root or superdir(node):
		for filee in sorted(os.listdir(node)):
			if (not root) or os.path.isdir(node + os.sep + filee):
				printStructureNode(fout, level + 1, node + os.sep + filee, filee)
	else:
		fout.write(spaces(level + 1) + "$from_names_djvu\t$all\n")
	if not root:
		fout.write(spaces(level) + "$end\n")
	
parser = OptionParser()
parser.add_option("-u", "--save-user", help="zapisz parametry polaczenia do bazy w konfiguracji kartoteki", action="store_true", dest="user", default=False)
parser.add_option("-c", "--hocr-cut", help="jaka czesc fiszki jest podejrzewana o posiadanie hasla", dest="hocr", default=None)
parser.add_option("-a", "--alphabetic", help="fiszki sa uporzadkowane alfabetycznie", dest="alpha", action="store_true", default=False)
parser.add_option("-r", "--default-reg", help="sciezka do domyslnego wykazu zadaniowego", dest="defr", default=None)
parser.add_option("-m", "--maleks", help="sciezka do skryptu maleks.sql", dest="maleks", default="maleks.sql")
parser.add_option("-i", "--hint-reg", help="sciezka do wykazu podpowiedzi", dest="hint", default=None)
parser.add_option("-p", "--port", help="port bazy danych", dest="port", default=None)
parser.add_option("-o", "--host", help="host bazy danych", dest="host", default=None)
(options, args) = parser.parse_args(sys.argv)

if len(args) != 7:
	print "Zla liczba argumentow"
	exit()

if os.path.isdir(args[1]):
	path = args[1]
	f = open(path + os.sep + "index.ind", "w")
	if options.alpha:
		f.write("$alphabetic\n")
	printStructureNode(f, -1, path, None, root=True)
	f.close()
	f = open(path + os.sep + "config.cfg", "w")
	f.write("db\t" + args[2] + "\n")
	if options.user:
		f.write("dbpass\t" + args[4] + "\n")
		f.write("dbuser\t" + args[3] + "\n")
		if options.host != None:
			f.write("dbhost\t" + options.host + "\n")
		if options.port != None:
			f.write("dbport\t" + options.port + "\n")
	if options.hocr != None:
		f.write("hocr_cut\tn" + options.hocr + "\n")
	if options.defr != None:
		if os.path.exists(options.defr):
			shutil.copy(options.defr, args[1] + os.sep + "domyslny_wykaz.reg")
			f.write("default_task_register\tdomyslny_wykaz.reg\n")
		else:
			print options.defr, "nie ma takiego pliku"
	f.close()
	if options.hint != None:
		if os.path.exists(options.hint):
			shutil.copy(options.hint, args[1] + os.sep + "hint.reg")
		else:
			print options.hint, "nie ma takiego pliku"
	urlstr = ""
	if options.host != None:
		urlstr += " -h " + options.host + " "
	if options.port != None:
		urlstr += " -P " + options.port + " "
	os.system("mysql " + urlstr + " -u " + args[5] + " -p" + args[6] + " \"-e create database " + args[2] + " character set = utf8 collate = utf8_polish_ci\"")
	os.system("mysql " + urlstr + " -u " + args[5] + " -p" + args[6] + " \"-e grant all on " + args[2] + ".* to " + args[3] + "\"")
	os.system("mysql " + urlstr + " -u " + args[3] + " -p" + args[4] + " " + args[2] + " < " + options.maleks)
else:
	print args[1], "nie jest katalogiem"

