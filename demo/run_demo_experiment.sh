#!/bin/bash

sudo docker run --privileged -it --rm \
            --mount=type=bind,source=/tmp,destination=/opt \
            --env EXP_DIR=/opt \
            --env RUN_EXPERIMENT=./run_topology_experiment.sh \
            --env CONTROLLER=controller \
            --net $EXP_NET \
            --name experiment \
            sdnsandbox http://www.topology-zoo.org/files/Abilene.graphml