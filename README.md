# SDNSandbox
An automated sandbox for provider SDN testing &amp; research

** All commands are linux based and expect that docker is installed
** Commands requiring environment variables repeat them for each description, although you can define them once

## Building The Container (Example)
sudo docker build -t sdnsandbox .

## Creating a docker volume to get the experiment results from the container
EXP_VOL=sdn-vol
sudo docker volume create $EXP_VOL

## Creating a docker network so the experiment + controller communicate with eachother
EXP_NET=sdn-net
sudo docker network create $EXP_NET

## Running the ONOS controller (you need a network loop enabled SDN controller)
EXP_NET=sdn-net
./scripts/run_onos_controller.sh
** In order to delete a previously running controller add the ALWAYS_RM=TRUE env-var.

## Running The Container (Example with the Getnet ISP network)
EXP_VOL=sdn-vol
EXP_NET=sdn-net
CONTROLLER=controller
sudo docker run --privileged -t --rm \
            --mount=type=volume,source=$EXP_VOL,destination=/opt \
            --env EXP_DIR=/opt \
            --env RUN_EXPERIMENT=./run_topology_experiment.sh \
            --env CONTROLLER=controller \
            --net $EXP_NET \
            --name experiment \
            sdnsandbox http://www.topology-zoo.org/files/Getnet.graphml
** CONTROLLER is set to the relevant DNS name

