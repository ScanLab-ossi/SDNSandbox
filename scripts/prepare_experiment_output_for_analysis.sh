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


EXP_LINKS_CSV=`echo $EXP_DIR/*.csv`
EXP_DATAGRAMS=$EXP_DIR/sflow-datagrams
EXP_INTFS=$EXP_DIR/intfs-list

set -x

python3 `dirname ${BASH_SOURCE[0]}`/util/csv2hd5.py \
--sflow-csv $EXP_DATAGRAMS \
--links-csv $EXP_LINKS_CSV \
--intfs-list $EXP_INTFS \
--titles `dirname ${BASH_SOURCE[0]}`/../scripts/csv_titles

python3 `dirname ${BASH_SOURCE[0]}`/util/calc_hd5_iqr.py \
--sflow-hd5 $EXP_DATAGRAMS.hd5

python3 `dirname ${BASH_SOURCE[0]}`/util/plot_hd5.py \
--sflow-hd5 $EXP_DATAGRAMS.hd5
