#!/bin/bash

set -e

if [[ -x $1 ]]
then
    echo Running experiment with $@
else
    echo Experiment file \"$1\" is not executable or found
    exit 1
fi

if [ -z "$EXP_DIR" ] ; then
    echo "The value for the experiment directory (EXP_DIR) is not set"
    exit 1
fi


# make sure needed services are running
sudo service ssh restart
sudo service openvswitch-switch restart

# create experiment folder
export EXP_DIR=$EXP_DIR/OUTPUT_`date  +%Y%m%d-%H%M%S`
mkdir -p $EXP_DIR

# backup experiment executable
cp $1 $EXP_DIR

# run experiment
sudo EXP_DIR=$EXP_DIR $1 &> $EXP_DIR/experiment.log

# cleanup mininet
sudo mn -c

echo The experiment files can be found in $EXP_DIR
