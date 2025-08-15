import shutil
import os
import platform
import locale
import plyer
import plyer.platforms
from lxml import etree
from lxml import objectify

osname=platform.uname()[0]
sort_key = ""

# Gets path of subitem
def getpath(somepath,add):
	# Cleans additional path elements
	if ((osname == "Windows" and add.startswith(".")) or add.startswith(".")):
		add = add[1::]
	if ((osname == "Windows" and add.startswith("\\")) or add.startswith("/")):
		add = add[1::]
	if ((osname == "Windows" and add.endswith("\\")) or add.endswith("/")):
		add = add[:-2:]
	if add != "":
		if osname == "Windows":
			somepath = somepath + "\\" + add
		else:
			somepath = somepath + "/" + add
	return somepath

# Custom get attribute function to deal with "_text" key
def getattrib(element,attrib):
	element = uncomment(element)
	if attrib == "_text":
		return element.text
	else:
		try:
			return element.attrib[attrib]
		except: # No attributes or no attributes with this name
			return ""

# Returns element inside comment, or element itself if not a comment or comment has no element inside
def uncomment(element):
	if element.tag is etree.Comment:
		try:
			return etree.fromstring(element.text)
		except: # Not a single element inside
			try:
				# Could be a list of elements. Try to generate it.
				newtext = element.text.strip(" \n\t")
				newtext = "<FSLPelemlist>" + newtext + "</FSLPelemlist>"
				newelem = etree.fromstring(newtext)
				return newelem
			except:	# No hope
				return element
	else:	# Not a comment
		return element

# Custom sorting funcion
def sortfunc(element):
	return getattrib(element,sort_key)

# Symlinks one file to another and returns translated message
def makelink_func(source, target):
	message = ""
	if lang == "ca":
		message = "amb enllaç "
	elif lang == "fr":
		message = "avec lien "
	elif lang == "uk":
		message = "з посиланням "
	else:
		message = "with link "
	if os.path.islink(source):	# Avoids creating symlink to symlink.
		source = os.readlink(source)
	os.symlink(source,target)
	return message

# Tries to copy a file; returns true if source exists, false otherwise.
def trytocopy(source_dir, onefile, target_dir, overwrite, makelink, log):
	target = getpath(target_dir,onefile)
	source = getpath(source_dir,onefile)
	if not os.path.exists(source):
		return False
	else:
		if os.path.exists(target):
			if (overwrite):
				message = ""
				if lang == "ca":
					message = message + "Substituint "
				elif lang == "fr":
					message = message + "Remplace "
				elif lang == "uk":
					message = message + "Заміна "
				else:
					message = "Replacing "
				os.remove(target)
				if (makelink):
					message = message + makelink_func(source, target)
				else:
					shutil.copy(source,target_dir)
		#		print(message + target + " ...\n")
				log.write(message + target + " ...\n")
			# else: will do nothing (keep original file)
		else:
			message = ""
			if lang == "ca":
				message = message + "Afegint "
			elif lang == "fr":
				message = message + "Ajoute "
			elif lang == "uk":
				message = message + "Додавання Uaaaa "
			else:
				message = message + "Adding "
			if not os.path.exists(target_dir):
	#			print(message + target_dir + " ...\n")
				log.write(message + target_dir + " ...\n")
				os.mkdir(target_dir)
			if (makelink):
				message = message + makelink_func(source, target)
			else:
				shutil.copy(source,target_dir)
	#		print(message + target + " ...\n")
			log.write(message + target + " ...\n")
		return True

# Compares two XML elements
def elem_identical(one,two):
	identical = True
	if one.tag == two.tag and one.attrib == two.attrib:
		if len(one) == len(two):
			if len(one) > 0:	# Both have same non-zero number of children: need to inspect children
				for index in range(len(one)):
					indentical = elem_identical(one[index],two[index])
			# If both have no child, we need to compare text
			elif one.text != two.text:
				oneinside = uncomment(one)
				twoinside = uncomment(two)
				if one != oneinside and two != twoinside and len(oneinside) == len(twoinside): # Both contain same number of XML elements
					identical = elem_identical(oneinside,twoinside)					
				else:	# Either contains no valid XML, or contain a different number of XML elements
					identical = False
			# else: Both have no child and text matches; still identical.
		else:	# Different number of elements
			identical = False
	else: # Basic properties not the same
		identical = False

	return identical

# Recursive XML parsing
def xmlprocess(source,target):
	identical = True
	key_src = ""
	key_tgt = ""
	sort = False
	global sort_key
	sort_prepends=[]
	removed_positions = []
	for child_src in source:
		if child_src.tag == "remove":
			index1 = 0
			while index1 <= (len(target) - len(child_src)):
				# Builds a list of the same size as what is inside the remove tags
				templist = []
				for index2 in range(len(child_src)):
					templist.append(target[index1+index2])
				# Compares both lists to see if we have to remove.
				remove = True
				for index2 in range(len(templist)):
					remove &= elem_identical(templist[index2],child_src[index2])
					if not remove:
						break
				# Removes, if needed.
				if remove:
					for index2 in range(len(templist)):
						target.remove(templist[index2])
						identical = False
					removed_positions.append(index1)
					index1 = index1 - 1
				index1 = index1 + 1
		else: # Any other tag than "remove" will clear the removed positions (done at the end of this block)
			if child_src.tag == "append":
				for append_src in child_src:
					target.append(append_src)
					identical = False
			elif child_src.tag == "prepend":
				for prepend_src in child_src:
					target.insert(0,prepend_src)
					identical = False
			elif child_src.tag == "insert":
				for index1 in removed_positions:
					for index2 in range(len(child_src)):
						target.insert(index1+index2,child_src[index2])
						identical = False
			elif child_src.tag == "sort":
				sort=True
				sort_key=child_src.attrib['key']
				sort_prepends=child_src.attrib['prepends'].split(',')
			elif child_src.tag == "key":	# Found a key on source side
				key_src = child_src.text
			elif len(child_src) > 0: 	# Source element with any other tag has children: we need to find the same element on target side before diving in it.
				for child_tgt in target:
					if key_src != "":	# Map mode
						if child_tgt.tag == "key":	# Found a key on target side
							if child_tgt.text == key_src:	# Same as source key
								key_tgt = key_src
							# else, do nothing (keep looking)
						elif key_tgt == key_src:	 # On an element following equal keys
							key_tgt = ""
							identical = xmlprocess(child_src,child_tgt)
						# else: do nothing (on an element following unequal keys)
					# Other modes: Process elements if they seem identical
					elif child_src.tag == child_tgt.tag and child_src.attrib == child_tgt.attrib:
						identical = xmlprocess(child_src,child_tgt)
					# else: do nothing (on a different element)
				key_src = ""

			removed_positions = []
	if sort:
		# Separates into two lists prepends and items to be sorted. First makes a copies of both, we will remove elements.
		tosort = []
		toprepend = []
		for element in target:
			temp_element = uncomment(element)
			# Temporary element can be:
			# - A single element (extracted from a comment or not)
			# - An element list (in the form of an FSLPelemlist element)
			# - A hopeless comment, is to say a comment that we could not convert into either of the two cases above
			# Hopeless comments, element lists, elements with no attributes, elements with no key, and excludes will be prepended in the order they appear.
			if temp_element.tag is etree.Comment or temp_element.tag == "FSLPelemlist" or getattrib(temp_element,sort_key) == "":
				toprepend.append(element)
			else:	# Single element with a valid key«
				found = False
				for sort_prepend in sort_prepends:
					if getattrib(temp_element,sort_key) == sort_prepend:
						toprepend.append(element)
						found = True
				if not found:	# Not found in list to prepend, so we must sort it.
					tosort.append(element)
		# Sorts the items to be sorted
		tosort.sort(key=sortfunc)	# Note: sort_key should have been passed here but we can only pass one argument (the element); sort_key was made global as a hack
		# Empties the list while taking a copy of it to compare
		targetcopy = []
		for element in target:
			targetcopy.append(element)
			target.remove(element)
		# Repopulates the list
		for element in toprepend:
			target.append(element)
		for element in tosort:
			target.append(element)
		# Compares saved copy and repopulated list to check if they are identical
		for index, element in enumerate(targetcopy):
			if element != target[index]:
				identical = False
				break

	return identical

# Gets system language 
lang=locale.getdefaultlocale()[0]
before_underscore_pos=lang.find('_')
lang=lang[0:before_underscore_pos:]

# Gets possible desired Firestorm installation path (or near it)
fs_path=""
if osname == "Windows":
	fs_path="C:\\Program Files\\Firestorm-Releasex64\\"
elif osname == "Linux":
	fs_path="/home/"+os.environ.get('USER', os.environ.get('USERNAME'))+"/"  # File chooser needs "/" to go into the folder.
elif osname == "Darwin":	# Mac
	fs_path="/Applications/Firestorm-releasex64.app/Contents/Resources/"

# Prompts user for a folder
message = "Choose Firestorm main folder"
if lang == "ca":
	message = "Tria la carpeta principal de Firestorm"
elif lang == "fr":
	message = "Choisissez le dossier principal de Firestorm"
elif lang == "uk":
	message = "Виберіть головну папку Firestorm"
fs_path=plyer.filechooser.choose_dir(path=fs_path,title=message)
if fs_path != None:
	fs_path = fs_path[0]

# Prepares log file
log=open("./log.txt", "w")

# Make sure we have a target directory (user hasn't clicked cancel)
if fs_path == None:
	message = "Patching canceled by user.\n"
	if lang == "ca":
		message = "Correcció anul·lada per l'usuari.\n"
	elif lang == "fr":
		message = "Correction annulée par l'utilisateur..\n"
	elif lang == "uk":
		message = "Виправлення скасовано користувачем.\n"
#	print(message)
	log.write(message)
# Make sure target is a Firestorm installation
elif not os.path.exists(getpath(fs_path,"app_settings")) and not os.path.exists(getpath(fs_path,"skins")):
	message = "This does not seem to be a Firestorm folder.\n"
	if lang == "ca":
		message = "Aquest no sembla ser una carpeta de Firestorm.\n"
	elif lang == "fr":
		message = "Ceci n'a pas l'air d'un dossier de Firestorm.\n"
	elif lang == "uk":
		message = "Здається, це не папка Firestorm.\n"
#	print(message)
	log.write(message)
# Make sure there is something to do
elif not os.path.exists("./app_settings") and not os.path.exists("./skins"):
	message = "There seems to be no source patch.\n"
	if lang == "ca":
		message = "No sembla haver-hi cap font de correctiu.\n"
	elif lang == "fr":
		message = "Il semble n'y avoir aucune source de correctif.\n"
	elif lang == "uk":
		message = "Здається, патча з вихідним кодом немає.\n"
	log.write(message)
else:
	varietylang = ""
	varietylang_path = ""
	varietylang_parent = ""
	# Walks the current python folder to process changes
	for (path,folders,files) in os.walk('.', topdown=True):
		# Checks if we just walked out of a variety language path.
		# Note: we need to check walk outs before walks in to properly walk out of fr_CA when we have just walked in fr_CA_PIRATE, for example.
		if varietylang != "" and (not path.startswith(varietylang_path) or path.startswith(varietylang_path + "_")):
			varietylang = ""
			varietylang_path = ""
			varietylang_parent = ""
		# Checks if we just walked in a variety language path
		if varietylang == "":
			curfolder = ""
			if osname == "Windows":
				curfolder = path[path.rfind("\\")+1:]
			else:
				curfolder = path[path.rfind("/")+1:]
			if (curfolder != "app_settings" and curfolder.find("_") >= 1):	# Will skip "app_settings" but also "" because the result will be -1
				varietylang = curfolder
				varietylang_path = path
				if osname == "Windows":
					varietylang_parent = path[:path.rfind("\\")]
				else:
					varietylang_parent = path[:path.rfind("/")]

				# We have a language variety. Copies fallback for this variety.
				# Will copy recursively from closest to furthest parent, but will not overwrite, so closest parent (or original file) will have priority.
				fallbacklang = varietylang
				underscorepos = fallbacklang.rfind("_")
				while underscorepos >= 1:	# Note: fisrt position would not help much because there would be no fallback (ex: "_KS" -> "")
					fallbacklang = fallbacklang[:underscorepos]

					copysrc_dir = getpath(fs_path,varietylang_parent)
					copysrc_dir = getpath(copysrc_dir,fallbacklang)
					addpath = path.replace(varietylang_path,"")	# ex: "./skins/default/xui/fr_CA_PIRATE/widgets" -> "_CA_PIRATE/widgets";  		"./skins/default/xui/fr_CA_PIRATE" -> "_CA_PIRATE"
					if osname == "Windows":
						addpath = addpath[addpath.find("\\")::] # ex: "_CA_PIRATE/widgets" -> "/widgets"; 		"_CA_PIRATE" -> "/"
					else:
						addpath = addpath[addpath.find("/")::]
					copysrc_dir = getpath(copysrc_dir,addpath)

					for (path2,folders2,files2) in os.walk(copysrc_dir, topdown=True):
						copytgt_dir = getpath(fs_path,path)
						addpath = path2.replace(copysrc_dir,"")	# ex: "/home/something/firestorm/skins/default/xui/fr_CA/widgets" -> "/widgets";
						copytgt_dir = getpath(copytgt_dir,addpath)
						for onefile in files2:
							# In Linux, ask OS to make symbolic links instead of copying files - FS sees the target properly.
							# The same trick does not work in Windows. TODO - need to check in Mac.
							if osname == "Linux":
								trytocopy(path2, onefile, copytgt_dir, False, True, log)
							else:
								trytocopy(path2, onefile, copytgt_dir, False, False, log)

					underscorepos = fallbacklang.rfind("_")

		for onefile in files:
			if onefile.endswith(".xml") and not onefile.endswith(".xml.patch") and os.path.exists(getpath(path,onefile)+".patch"): 	# File is .xml and there is a .xml.patch
				message = "WARNING: Will not replace/add the following file because its patch is also present next to it: "
				if lang == "ca":
					message = "ALERTE: No es substituirà ni afegirà el fitxer següent perquè el seu correctiu també és present al seu costat: "
				elif lang == "fr":
					message = "ALERTE: Ne remplacera ni n'ajoutera pas le fichier suivant car son correctif est aussi présent à ses côtés: "
				elif lang == "uk":
					message = "ПОПЕРЕДЖЕННЯ: Наступний файл не буде замінено/додано, оскільки його патч також присутній поруч із ним: "
				log.write(message + "\n")
				log.write("   " + getpath(path,onefile) + "\n")
			elif onefile.endswith(".xml.patch") and os.path.exists(getpath(path,onefile)[:-6:]):								# File is .xml.patch and there is a .xml
				message = "WARNING: Will not apply the following patch because the complete file is also present next to it: "
				if lang == "ca":
					message = "ALERTA: No s'aplicarà el correctiu següent perquè el fitxer sencer també és present al seu costat: "
				elif lang == "fr":
					message = "ALERTE: N'appliquera pas le correctif suivant car le fichier complet est aussi présent à ses côtés: "
				elif lang == "uk":
					message = "ПОПЕРЕДЖЕННЯ: Наступний патч не застосовуватиметься, оскільки повний файл також присутній поруч із ним: "
				log.write(message + "\n")
				log.write("   " + getpath(path,onefile) + "\n")
			# XML patches
			elif onefile.endswith(".xml.patch"):
				source = getpath(path,onefile)
				target_dir = getpath(fs_path,path)
				target = getpath(fs_path,source[:-6:])
				message = "Patching "
				if lang == "ca":
					message = "Aplicant un correctiu a "
				elif lang == "fr":
					message = "Applique un correctif à "
				elif lang == "uk":
					message = "латання "
#				print(message + target + " ...\n")
				log.write(message + target + " ...\n")
				# If target does not exist...
				if not os.path.exists(target):
					message = "   Does not exist; skipping.\n"
					if lang == "ca":
						message = "   No existeix; el salto.\n"
					elif lang == "fr":
						message = "   N'existe pas; je le saute.\n"
					elif lang == "uk":
						message = "   Не існує; пропускається.\n"
#					print(message)
					log.write(message)
				else:	# Target exists
					xmlroot_src = etree.parse(source).getroot()
					xmltree_tgt = etree.parse(target)
					xmlroot_tgt = xmltree_tgt.getroot()
					if xmlroot_src.tag != xmlroot_tgt.tag:
						message = "   Root element differs; skipping.\n"
						if lang == "ca":
							message = "   L'element arrel difereix; el salto.\n"
						elif lang == "fr":
							message = "   L'élément racine diffère; je le saute.\n"
						elif lang == "uk":
							message = "   Кореневий елемент відрізняється; пропуск.\n"
#						print (message)
						log.write(message)
					elif (not xmlprocess(xmlroot_src,xmlroot_tgt)):	# Root element is the same, and we have changed something
						# If what we have is a symbolic link, we need to copy the original file before patching it, otherwise original file will be patched.
						if os.path.islink(target):
							linksrc = os.readlink(target)
							os.remove(target)
							shutil.copy(linksrc, target_dir)
						# Writing the file
						etree.indent(xmltree_tgt, space="\t")	# Because otherwise some indents do not work
						# Copies doctype
						doctype="";
						with open(target, "r") as f:
							doctype = f.readline()
						with open(target, "w") as f:
							f.write(doctype)
						# Parses the rest of the XML
						with open(target, "ab") as f:
							f.write(etree.tostring(xmltree_tgt, encoding="utf-8", xml_declaration=False))
			# XML files
			elif onefile.endswith(".xml"):
				trytocopy(path, onefile, getpath(fs_path,path), True, False, log)	# Will replace original files
log.close()
