#!/bin/bash

exit_with_msg() {
  echo
  echo $1
  echo Exiting...
  exit 1
}

if [ -z "$EXP_NET" ] ; then
  exit_with_msg "The variable EXP_NET must be set to the name of the docker network to be used in the experiment!"
fi

if [ -z "$CONTROLLER" ] ; then
  exit_with_msg "The variable CONTROLLER must be set to the DNS name of the controller docker container to be used in the experiment!"
fi

if [ -z "$EXP_DATA_PATH" ] ; then
	  exit_with_msg "The variable EXP_DATA_PATH must be set to the storage path to be used in the experiment!"
fi

ROOT_DIR=$(dirname "${BASH_SOURCE[0]}")

for NETWORK in $(cat "$ROOT_DIR"/ISP_list.txt) ; do
  echo Running experiment for: "$NETWORK"
  DATA_PATH=$EXP_DATA_PATH/SDNSandbox-$NETWORK
  echo Will save experiment output in "$DATA_PATH"
  mkdir -p $DATA_PATH
  sed s/Aarnet/$NETWORK/g "$ROOT_DIR"/../example.config.json > $DATA_PATH/config.json
  EXP_DATA_PATH=$DATA_PATH NETWORK=$NETWORK "$ROOT_DIR"/run_experiment.sh
  # stop if failure occurred
  [ $? != 0 ] && echo "Failure Occurred! Stopping..." && break
done
