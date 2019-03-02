#!/bin/bash

if [[ -f $GRAPHML ]]
then
    echo Running experiment with $GRAPHML
else
    echo Experiment file \"$GRAPHML\" is not a file or found... Exiting!
    exit 1
fi

if [[ -z "$EXP_DIR" ]] ; then
    echo "The value for the experiment directory (EXP_DIR) is not set"
    exit 1
fi

# trap ctrl-c and call end()
trap end INT

function end() {
    # cleanup mininet
    sudo mn -c

    echo The experiment files can be found in $EXP_DIR
}

# create experiment folder
export EXP_DIR=$EXP_DIR/OUTPUT_`date  +%Y%m%d-%H%M%S`
mkdir -p $EXP_DIR

# backup experiment graphml
cp $GRAPHML $EXP_DIR

TOPO_CSV=$EXP_DIR/`basename $GRAPHML`-topo.csv
# generate CSV
./graphml-topo-to-csv.py -i $GRAPHML -o $TOPO_CSV

EXP_PY=$EXP_DIR/`basename $GRAPHML`-topo.py

./mininet-experiment-generator.py -i $TOPO_CSV -o $EXP_PY -c $CONTROLLER_IP

# make sure needed services are running
sudo service ssh restart
sudo service openvswitch-switch restart

# run experiment
sudo EXP_DIR=$EXP_DIR $1 &> $EXP_DIR/experiment.log

end
