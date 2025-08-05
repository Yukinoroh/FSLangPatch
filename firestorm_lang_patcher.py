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
	if osname == "Windows":
		somepath = somepath + "\\" + add
	else:
		somepath = somepath + "/" + add
	return somepath

# Custom get attribute function to deal with "_text" key
def getattrib(element,attrib):
	element = uncomment(element)	# Note: we're nost supposed to get a comment without an element inside here.
	if attrib == "_text":
		return element.text
	else:
		return element.attrib[attrib]

# Returns element inside comment, or element itself if not a comment or comment has no element inside
def uncomment(element):
	if element.tag is etree.Comment:
		try:
			return etree.fromstring(element.text)
		except:	# No element inside: We just use the comment as is.
			return element
	else:
		return element

# Custom sorting funcion
def sortfunc(element):
	return getattrib(element,sort_key)

# Recursive XML parsing
def xmlprocess(source,target):
	identical = True
	key_src = ""
	key_tgt = ""
	sort = False
	global sort_key
	sort_prepends=[]
	for child_src in source:
		if child_src.tag == "sort":		# We will sort all child_tgt
			sort=True
			sort_key=child_src.attrib['key']
			sort_prepends=child_src.attrib['prepends'].split(',')
		elif child_src.tag == "key":	# Found a key on source side
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
						identical = xmlprocess(child_src,child_tgt)
						#break	# Commented so that it replaces all occurences
					# else: do nothing (on an element following unequal keys)
				else:	# Other modes
					temp_child_src = uncomment(child_src)
					temp_child_tgt = uncomment(child_tgt)
					# Needs to inspect elements if they are identical but have different number of elements (ex: top map) or if they contain the same text (ex: string)
					if temp_child_src.tag == temp_child_tgt.tag and temp_child_src.attrib == temp_child_tgt.attrib and (len(temp_child_src) != len(temp_child_tgt) or temp_child_src.text == temp_child_tgt.text):
						intarget=1;
						identical = xmlprocess(temp_child_src,temp_child_tgt)
						# If elements are identical inside and only one side is commented, we have to update (either comment or uncomment)
						if identical and ((temp_child_src != child_src and temp_child_tgt == child_tgt) or (temp_child_src == child_src and temp_child_tgt != child_tgt)):
							target.replace(child_tgt,child_src)
							identical = False
						#break	# Commented so that it replaces all occurences
					# else: do nothing (on different element)
			if not intarget:
				target.append(child_src)
				identical = False
	if sort:
		# Separates into two lists prepends and items to be sorted. First makes a copies of both, we will remove elements.
		tosort = []
		toprepend = []
		for element in target:
			temp_element = uncomment(element)
			# Temporary element may be a comment, an element extracted from a comment, or an element.
			# Since it can be extracted from a comment, we have to add/remove the original element to the list whatever.
			# Will prepend comments, elements with no key, and excludes.
			if temp_element.tag is etree.Comment:
				toprepend.append(element)
			else:	# Not a comment
				found = False
				for sort_prepend in sort_prepends:
					if getattrib(temp_element,sort_key) == sort_prepend:
						toprepend.append(element)
						found = True
				if not found:	# Not found in list to prepend, so we must sort it.
					tosort.append(element)
		# Sorts the items to be sorted
		tosort.sort(key=sortfunc)	# Note: sort_key should have been passed here but we can only pass one argument (the element); sort_key was made global as a hack
		# Takes a copy of the list to compare after sorting
		targetcopy = []
		for element in target:
			targetcopy.append(element)
		# Repopulates the list
		target.clear()
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

# Gets language 
lang=locale.getdefaultlocale()[0]
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

# Make sure target is a Firestorm installation
if not os.path.exists(getpath(fs_path,"app_settings")) and not os.path.exists(getpath(fs_path,"skins")):
	message="This does not seem to be a Firestorm folder.\n"
	if lang == "ca":
		message="Aquest no sembla ser una carpeta de Firestorm.\n"
	elif lang == "fr":
		message="Ceci n'a pas l'air d'un dossier de Firestorm.\n"
	elif lang == "uk":
		message="Здається, це не папка Firestorm.\n"
#	print(message)
	log.write(message)
# Make sure there is something to do
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
	for (path,folders,files) in os.walk('.', topdown=True):
		# Processing of files
		for onefile in files:
			if onefile.endswith(".xml") and not onefile.endswith(".xml.patch") and os.path.exists(getpath(path,onefile)+".patch"): 	# File is .xml and there is a .xml.patch
				message="WARNING: Will not replace/add the following file because its patch is also present next to it: "
				if lang == "ca":
					message="ALERTE: No es substituirà ni afegirà el fitxer següent perquè el seu correctiu també és present al seu costat: "
				elif lang == "fr":
					message="ALERTE: Ne remplacera ni n'ajoutera pas le fichier suivant car son correctif est aussi présent à ses côtés: "
				elif lang == "uk":
					message="ПОПЕРЕДЖЕННЯ: Наступний файл не буде замінено/додано, оскільки його патч також присутній поруч із ним: "
				log.write(message + "\n")
				log.write("   " + getpath(path,onefile) + "\n")
			elif onefile.endswith(".xml.patch") and os.path.exists(getpath(path,onefile)[:-6:]):								# File is .xml.patch and there is a .xml
				message="WARNING: Will not apply the following patch because the complete file is also present next to it: "
				if lang == "ca":
					message="ALERTA: No s'aplicarà el correctiu següent perquè el fitxer sencer també és present al seu costat: "
				elif lang == "fr":
					message="ALERTE: N'appliquera pas le correctif suivant car le fichier complet est aussi présent à ses côtés: "
				elif lang == "uk":
					message="ПОПЕРЕДЖЕННЯ: Наступний патч не застосовуватиметься, оскільки повний файл також присутній поруч із ним: "
				log.write(message + "\n")
				log.write("   " + getpath(path,onefile) + "\n")
			# XML patches
			elif onefile.endswith(".xml.patch"):
				source=getpath(path,onefile)
				target=source[:-5:]
				target=getpath(fs_path,target[2:-1:])
				message="Patching "
				if lang == "ca":
					message="Aplicant un correctiu a "
				elif lang == "fr":
					message="Applique un correctif à "
				elif lang == "uk":
					message="латання "
#				print(message + target + "...\n")
				log.write(message + target + "...\n")
				if not os.path.exists(target):
					message="   Does not exist; skipping.\n"
					if lang == "ca":
						message="   No existeix; el salto.\n"
					elif lang == "fr":
						message="   N'existe pas; je le saute.\n"
					elif lang == "uk":
						message="   Не існує; пропускається.\n"
#					print(message)
					log.write(message)
				else:
					xmlroot_src = etree.parse(source).getroot()
					xmltree_tgt = etree.parse(target)
					xmlroot_tgt = xmltree_tgt.getroot()
					if xmlroot_src.tag != xmlroot_tgt.tag:
						message="   Root element differs; skipping.\n"
						if lang == "ca":
							message="   L'element arrel difereix; el salto.\n"
						elif lang == "fr":
							message="   L'élément racine diffère; je le saute.\n"
						elif lang == "uk":
							message="   Кореневий елемент відрізняється; пропуск.\n"
#						print (message)
						log.write(message)
					else:
						xmlprocess(xmlroot_src,xmlroot_tgt)
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
				source=getpath(path,onefile)
				target_dir=getpath(fs_path,path[2::])
				target=getpath(target_dir,onefile)
				if os.path.exists(target):
					message="Replacing "
					if lang == "ca":
						message="Substituint "
					elif lang == "fr":
						message="Remplace "
					elif lang == "uk":
						message="Заміна "
#						print(message + target + "...\n")
					log.write(message + target + "...\n")
					os.remove(target)
				else:
					message="Adding "
					if lang == "ca":
						message="Afegint "
					elif lang == "fr":
						message="Ajoute "
					elif lang == "uk":
						message="Додавання Uaaaa "
					if not os.path.exists(target_dir):
#							print(message + target_dir + "...\n")
						log.write(message + target_dir + "...\n")
						os.mkdir(target_dir)
#						print(message + target + "...\n")
					log.write(message + target + "...\n")
				shutil.copy(source,target_dir)
