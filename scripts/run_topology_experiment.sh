#!/bin/bash

GRAPHML=$1

if [[ -f $GRAPHML ]]
then
    echo Running experiment with $GRAPHML
else
    echo Experiment file \"$GRAPHML\" is not a file or found
    exit 1
fi

EXP_PY=/tmp/`basename $GRAPHML`-topo.py
# generate experiment
./graphml-topo-mininet-generator.py -i $GRAPHML -o $EXP_PY -c 127.0.0.1

# run experiment
./run_experiment.sh $EXP_PY
