#!/bin/bash

exit_with_msg() {
  echo
  echo $1
  echo Exiting...
  exit 1
}

if [ -z "$NUM_HOSTS" ] ; then
  exit_with_msg "The variable NUM_HOSTS must be set to the number of switches/hosts used in the experiment!"
fi

if [ -z "$EXP_DIR" ] ; then
  exit_with_msg "The variable EXP_DIR must be set to the name of the experiment directory name!"
fi

for i in $( seq $NUM_HOSTS )
do
	echo Drops for 10.0.0.$i = `grep "10.0.0.$i failed, skipping" $EXP_DIR/*.log | wc -l`
done
