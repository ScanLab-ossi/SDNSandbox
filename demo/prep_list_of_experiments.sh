#!/bin/bash

if [ -z "$EXP_BASE_DIR" ] ; then
	EXP_BASE_DIR=/data/multi-experiment
	echo Using $EXP_BASE_DIR as EXP_BASE_DIR - the folder holding experiment folders
fi


for folder in `find $EXP_BASE_DIR -mindepth 1 -maxdepth 1 -type d ` ; do
	echo Preparing $folder
	EXP_DIR=$folder `dirname ${BASH_SOURCE[0]}`/prepare_experiment_output_for_analysis.sh &
	sleep 1
done
wait
