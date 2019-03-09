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


sudo docker run --privileged -it --rm \
            --mount=type=bind,source=/tmp,destination=/opt \
            --env EXP_DIR=/opt \
            --env RUN_EXPERIMENT=./run_topology_experiment.sh \
            --env CONTROLLER=$CONTROLLER \
            --net $EXP_NET \
            --name experiment \
            sdnsandbox http://www.topology-zoo.org/files/Abilene.graphml