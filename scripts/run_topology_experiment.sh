#!/bin/bash

GRAPHML=$1
CONTROLLER=`getent ahostsv4 $CONTROLLER | head -n1 | cut -d" " -f1`


if [[ ! $CONTROLLER =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]
then
    echo "The CONTROLLER EnvVar is not set to the conroller hostname or IP (CONTROLLER==$CONTROLLER)... Exiting!"
    exit 1
fi

echo Pinging the SDN controller:

ping -c 3 $CONTROLLER
if [[ $? -eq 0 ]]
then
    echo Ping to controller at ip-addr=$CONTROLLER OK!
else
    echo Unable to ping controller at ip-addr=$CONTROLLER... Exiting!
    exit 1
fi

if [[ -f $GRAPHML ]]
then
    echo Running experiment with $GRAPHML
else
    echo Experiment file \"$GRAPHML\" is not a file or found... Exiting!
    exit 1
fi

EXP_PY=/tmp/`basename $GRAPHML`-topo.py
# generate experiment
./graphml-topo-mininet-generator.py -i $GRAPHML -o $EXP_PY -c $CONTROLLER

# run experiment
./run_experiment.sh $EXP_PY
