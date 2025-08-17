#!/bin/bash
home=$PWD
diffsrc_root=$1
difftgt_root=$2
difflog_root=$3
addpath=""

IFS=\"

process(){
	mode=$1

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
			process $mode
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
		if [ "$files" != "" ] && ( [ ${files//.xml/} != $files ] || [ ${files//.html/} != $files ] )
		then
			diffsrc=$diffsrc_root''$addpath'/'$files
			difftgt=$difftgt_root''$addpath'/'$files
			difflog_dir=$difflog_root''$addpath
			difflog=$difflog_dir'/'$files'.diff'
			if test -f $difftgt
			then
				if [ "$mode" == "report deleted files and diff" ]	# Target exists and we are asked to diff
				then
	#				echo 'Make diff '$diffsrc $difftgt' > '$difflog
					diff $diffsrc $difftgt > $difflog
					if ! test -s $difflog	# Deletes empty diffs
					then
						rm $difflog
					fi
				fi
				# else: target exists but we don't diff, so do nothing.
			else	# Target exists
				if [ "$mode" == "report deleted files and diff" ]
				then
					touch $difflog_dir'/'MAYBE_REMOVE_''$files
				else
	#				echo 'Copy '$diffsrc $difflog_dir
					cp $diffsrc $difflog_dir
				fi
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

	# First we run source, which is the older version, and compare with target, the newer.
	# If files were deleted, we will touch a dummy file to notify.
	cd $diffsrc_root
	process "report deleted files and diff"

	# Switch source and target around to check for added files in target (No need to diff because it has been done already).
	# If files were added, we will copy them.
	difftemp_root=$diffsrc_root
	diffsrc_root=$difftgt_root
	difftgt_root=$difftemp_root
	cd $diffsrc_root
	process "prepare added files"
fi
