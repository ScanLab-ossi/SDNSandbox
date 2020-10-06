#!/bin/sh
# Tiny script that re-launches ITGRecv in case it dies...
LOG_NAME=$EXP_DIR/receiver-$1.log
echo_this () {
  echo [`date`] $1  >> $LOG_NAME
}

while [ 1 ]
do
	echo_this "-------------------------------"
	echo_this "Starting ITGRecv"

	# Don't try to make ITGRecv log it's output, it handles this very poorly
	ITGRecv

	echo_this "ITGRecv has stopped!"
	sleep 1
done
