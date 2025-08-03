import shutil
import os
import platform
import plyer
import plyer.platforms
import locale
from lxml import etree

osname=platform.uname()[0]
#osname=os.uname()[0]

def subitem(somepath,add):
	if osname == "Windows":
		somepath = somepath + "\\" + add
	else:
		somepath = somepath + "/" + add
	return somepath

def xmlprocess(source,target):
	key_src = ""
	key_tgt = ""
	for child_src in source:
		if child_src.tag == "key":	# Found a key on source side
			key_src=child_src.text
		else:	# Anything else than key on source side
			intarget=0;
			for child_tgt in target:
				if key_src != "":	# Map mode
					if child_tgt.tag == "key":	# Found a key on target side
						if child_tgt.text == key_src:
							key_tgt = key_src
						# else, do nothing (keep looking)
					elif key_tgt == key_src:	 # On an element following equal keys
						key_src = ""
						key_tgt = ""
						intarget=1
						xmlprocess(child_src,child_tgt)
						break
					# else: do nothing (on an element following unequal keys)
				else:	# Other modes
					# Needs to inspect elements if they are identical but have different number of elements (ex: top map) or if they contain the same text (ex: string)
					if child_src.tag == child_tgt.tag and child_src.attrib == child_tgt.attrib and (len(child_src) != len(child_tgt) or child_src.text == child_tgt.text):
						intarget=1;
						xmlprocess(child_src,child_tgt)
						break
					# else: do nothing (on different element)
			if not intarget:
				target.append(child_src)

def process(path):
	for (path,folders,files) in os.walk(path, topdown=True):
		# Processing of files
		for onefile in files:
			# XML patches
			if onefile.find(".xml.patch") >= 0:
				source=subitem(path,onefile)
				target=source[:-5:]
				target=subitem(fs_path,target[2:-1:])
#				print("Patching or re-patching " + target + "...")
				log.write("Patching or re-patching " + target + "...\n")
				if not os.path.exists(target):
#					print("   Does not exist; skipping.")
					log.write("   Does not exist; skipping.\n")
				else:
					xmlroot_src = etree.parse(source).getroot()
					xmltree_tgt = etree.parse(target)
					xmlroot_tgt = xmltree_tgt.getroot()
					if xmlroot_src.tag != xmlroot_tgt.tag:
						print ("   Root element differs. Skipping.")
					else:
						xmlprocess(xmlroot_src,xmlroot_tgt)
						# Writing the file
						etree.indent(xmltree_tgt, space="\t")	# Because otherwise some indents do not work
						# Copies doctype
						doctype="";
						with open(target, "r") as f:
							doctype = f.readline()
							f.close()
						with open(target, "w") as f:
							f.write(doctype)
						# Parses the rest of the XML
						with open(target, "ab") as f:
							f.write(etree.tostring(xmltree_tgt, encoding="utf-8", xml_declaration=False))
			# XML files
			elif onefile.find(".xml") >= 0:
				source=subitem(path,onefile)
				target_dir=subitem(fs_path,path[2::])
				target=subitem(target_dir,onefile)
				if not os.path.exists(source+".patch"):
					if os.path.exists(target):
#						print("Replacing " + target + "...")
						log.write("Replacing " + target + "...\n")
						os.remove(target)
					else:
						if not os.path.exists(target_dir):
#							print("Adding " + target_dir + "...")
							log.write("Adding " + target_dir + "...\n")
							os.mkdir(target_dir)
#						print("Adding " + target + "...")
						log.write("Adding " + target + "...\n")
					shutil.copy(source,target_dir)

# Gets language 
#lang=os.getenv('LANG')
#lang=os.environ['LANG']
lang=locale.getdefaultlocale()[0]
print(lang)
before_underscore_pos=lang.find('_')
lang=lang[0:before_underscore_pos:]

# Gets default Firestorm installation path
fs_path=""
if osname == "Windows":
	fs_path="C:\\Program Files\\Firestorm-Releasex64\\"
elif osname == "Linux":
	fs_path="/home/"+os.environ.get('USER', os.environ.get('USERNAME'))+"/"  # File chooser needs "/" to go into the folder.
elif osname == "Darwin":	# Mac
	fs_path="/Applications/Firestorm-releasex64.app/Contents/Resources/"

# Prompts user for a folder
message="Choose Firestorm main folder"
if lang == "ca":
	message="Tria la carpeta principal de Firestorm"
elif lang == "fr":
	message="Choisissez le dossier principal de Firestorm"
elif lang == "uk":
	message="Виберіть головну папку Firestorm"
fs_path=plyer.filechooser.choose_dir(path=fs_path,title=message)[0]

# Prepares log file
log=open("./log.txt", "w")

# Make sure this is a Firestorm installation
if not os.path.exists(subitem(fs_path,"app_settings")) and not os.path.exists(subitem(fs_path,"skins")):
	message="This does not seem to be a Firestorm folder.\n"
	if lang == "ca":
		message="Aquest no sembla ser una carpeta de Firestorm.\n"
	elif lang == "fr":
		message="Ceci n'a pas l'air d'un dossier de Firestorm.\n"
	elif lang == "uk":
		message="Здається, це не папка Firestorm.\n"
#	print(message)
	log.write(message)
elif not os.path.exists("./app_settings") and not os.path.exists("./skins"):
	message="There seems to be no source patch.\n"
	if lang == "ca":
		message="No sembla haver-hi cap font de correctiu.\n"
	elif lang == "fr":
		message="Il semble n'y avoir aucune source de correctif.\n"
	elif lang == "uk":
		message="Здається, патча з вихідним кодом немає.\n"
	log.write(message)
else:
	# Walks the current python folder to process changes
	process('.');
