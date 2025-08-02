import shutil
import os
import plyer

osname=os.uname()[0]

# Gets language 
lang=os.getenv('LANG')
before_underscore_pos=lang.find('_')
lang=lang[0:before_underscore_pos:]

# Gets default Firestorm installation
installedpath=""
if osname == "Windows":
	installedpath="C:\Program Files\Firestorm-Releasex64"
elif osname == "Linux":
	installedpath="/home/"+os.environ.get('USER', os.environ.get('USERNAME'))+"/"

# Prompts user for a Folder
message="Choose Firestorm main folder"
if lang == "ca":
	message="Tria la carpeta principal de Firestorm"
elif lang == "fr":
	message="Choisissez le dossier principal de Firestorm"
elif lang == "uk":
	message="Виберіть головну папку Firestorm"
folder=plyer.filechooser.choose_dir(path=installedpath,title=message)

# Make sure this is a Firestorm folder
#TODO
