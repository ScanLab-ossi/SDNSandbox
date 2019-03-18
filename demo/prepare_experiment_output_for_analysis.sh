#!/bin/bash


exit_with_msg() {
  echo
  echo $1
  echo Exiting...
  exit 1
}

if [ -z "$EXP_DIR" ] ; then
  exit_with_msg "The variable EXP_DIR must be set to the name of the directory of the experiment output!"
fi


if [ -z "$EXP_LINKS_CSV" ] ; then
  exit_with_msg "The variable $EXP_LINKS_CSV must be set to the CSV of the experiment topology links!"
fi


python `dirname ${BASH_SOURCE[0]}`/util/csv2hd5.py \
--sflow-csv $EXP_DIR/sflow-datagrams \
--links-csv $EXP_DIR/$EXP_LINKS_CSV \
--intfs-list $EXP_DIR/intfs-list \
--titles ../scripts/csv_titles
