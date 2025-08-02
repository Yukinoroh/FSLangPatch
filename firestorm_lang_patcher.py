import shutil
import os
import plyer
#TODO import xml.etree.ElementTree as ET

osname=os.uname()[0]

def subitem(somepath,add):
	if osname == "Windows":
		somepath = somepath + "\\" + add
	else:
		somepath = somepath + "/" + add
	return somepath

def process(path):
	for (path,folders,files) in os.walk(path, topdown=True):
		# Processing of files
		for onefile in files:
			# XML patches
			if onefile.find(".xml.patch") >= 0:
				source=subitem(path,onefile)
				target=source[:-5:]
				target=subitem(fs_path,target[2:-1:])
				print("Patching or re-patching " + target + "...")
				if not os.path.exists(target):
					print("   Does not exist; skipping.")
				else:
					None # TODO
					# TODO xml parsing
#					xmlroot_src = ET.parse(source).getroot()
#					xmlroot_tgt = ET.parse(target).getroot()
#					if xmlroot_src.tag != xmlroot_tgt.tag:
#						print ("   Root element differs. Skipping.")
#					else:
#						xmlprocess(xmlroot_src,xmlroot_tgt)
#						print("   Done.")
			# XML files
			elif onefile.find(".xml") >= 0:
				source=subitem(path,onefile)
				target_dir=subitem(fs_path,path[2::])
				target=subitem(target_dir,onefile)
				if not os.path.exists(source+".patch"):	# TODO (remove if we don't use patches) Will not replace files if there is a patch
					if os.path.exists(target):
#						print("Replacing " + target + "...")
						os.remove(target)
					else:
						if not os.path.exists(target_dir):
							print("Adding " + target_dir + "...")
							os.mkdir(target_dir)
#						print("Adding " + target + "...")
					shutil.copy(source,target_dir)

# Gets language 
lang=os.getenv('LANG')
before_underscore_pos=lang.find('_')
lang=lang[0:before_underscore_pos:]

# Gets default Firestorm installation path
fs_path=""
fs_path2=""
if osname == "Windows":
	fs_path="C:\\Program Files\\Firestorm-Releasex64"
elif osname == "Linux":
	fs_path="/home/"+os.environ.get('USER', os.environ.get('USERNAME'))+"/"  # File chooser needs "/" to go into the folder.

# Prompts user for a folder
message="Choose Firestorm main folder"
if lang == "ca":
	message="Tria la carpeta principal de Firestorm"
elif lang == "fr":
	message="Choisissez le dossier principal de Firestorm"
elif lang == "uk":
	message="Виберіть головну папку Firestorm"
fs_path=plyer.filechooser.choose_dir(path=fs_path,title=message)[0]

# Walks the current python folder to process changes
process('.');

