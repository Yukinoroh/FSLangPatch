#!/bin/bash
home=$PWD
diffsrc_root=$1
difftgt_root=$2
difflog_root=$3
addpath=""

IFS=\"

process(){
	# Runs all folders
	local folders
	local addpath
	for folders in $(ls -Q)
	do
		if test -d $folders && [ "$folders" != "" ]
		then
			addpath=${PWD/$diffsrc_root/}
			cd $folders
			if ! test -d $difflog_root''$addpath'/'$folders
			then
				mkdir $difflog_root''$addpath'/'$folders
			fi
			process
			cd ..
			# If folder is empty, we can delete it.
			if [ -z "$( ls -A $difflog_root''$addpath'/'$folders )" ]
			then
#				echo 'Deleting '$difflog_root''$addpath'/'$folders for being empty
				rmdir $difflog_root''$addpath'/'$folders
			fi
		fi
	done

	# Runs all files
	local files
	addpath=${PWD/$diffsrc_root/}
	for files in $(ls -Q)
	do
		if [ "$files" != "" ] && ( [ ${files//.xml/} != $files ] )
		then
			diffsrc=$diffsrc_root''$addpath'/'$files
			difftgt=$difftgt_root''$addpath'/'$files
			difflog_dir=$difflog_root''$addpath
			difflog=$difflog_dir'/'$files'.diff'
			if test -f $difftgt
			then
#				echo 'Make diff '$diffsrc $difftgt' > '$difflog
				diff $diffsrc $difftgt > $difflog
			# If file does not exist, we copy it whole
			else
#				echo 'Copy '$diffsrc $difflog_dir
				cp $diffsrc $difflog_dir
			fi
		fi
	done
}


if [ "$diffsrc_root" == "" ] || [ "$difftgt_root" == "" ] || [ "$difflog_root" == "" ]
then
	echo "Wrong parameters. Please use <dif source path> <diff target path> <diff log path>"
	echo "(Only <diff write path> may be relative.)"
else
	# In case write_target was given as relative, translate to absolute
	cd $difflog_root
	difflog_root=$PWD

	cd $diffsrc_root
	process
fi
