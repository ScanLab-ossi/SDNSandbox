# SDNSandbox
An automated sandbox for provider SDN testing &amp; research

* All commands are linux based and expect that docker is installed

* Commands requiring environment variables repeat them for each description, although you can define them once

## Building The Container (Example)
`sudo docker build -t sdnsandbox .`

## Creating a docker network so the experiment + controller communicate with eachother
`EXP_NET=sdn-net`

`sudo docker network create $EXP_NET`

## Running the ONOS controller (you need a network loop enabled SDN controller)
`EXP_NET=sdn-net`

`./demo/run_onos_controller.sh`

* This will enable the fwd (reactive forwarding and openflow apps)
* In order to delete a previously running controller add the ALWAYS_RM=TRUE env-var.

## Running The Experiment Container (Example with the Abilene ISP network)

### Defining Environment
`EXP_NET=sdn-net`

`CONTROLLER=controller`

### Running the experiment

```
sudo docker run --privileged -it --rm \
            --mount=type=volume,source=$EXP_VOL,destination=/opt \
            --env EXP_DIR=/opt \
            --env RUN_EXPERIMENT=./run_topology_experiment.sh \
            --env CONTROLLER=controller \
            --net $EXP_NET \
            --name experiment \
            sdnsandbox http://www.topology-zoo.org/files/Abilene.graphml
```
This can also be run using the demo command:

`EXP_NET=sdn-net CONTROLLER=controller ./demo/run_demo_experiment.sh`
        
* CONTROLLER is set to the relevant DNS name