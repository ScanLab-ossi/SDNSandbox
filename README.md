# SDNSandbox
An automated sandbox for provider SDN testing &amp; research

* All commands are linux based and expect that docker is installed

* Commands requiring environment variables repeat them for each description, although you can define them once

## Building The Container (Example)
We will tag our docker image with the "sdnsandbox" tag
`sudo docker build -t sdnsandbox .`

## Environment preparations
The following stages can be run using the following helper script:

`. ./demo/prepare_environment.sh`

The preparation stages need to happen before running the actual experiment.
We split them to a separate script as they can be run once for many experiment executions.
As the script exports environment variables to be used later it needs to be used with the source or "." operand.
### Creating a docker network
This is done so the experiment + controller communicate with each other.
`export EXP_NET=sdn-net`

`sudo docker network create $EXP_NET`

### Running the SDN controller
 You need a network loop enabled SDN controller - I use ONOS as it was designed for provider workloads
 
`export EXP_NET=sdn-net`

`./demo/run_onos_controller.sh`

* This will enable the reactive forwarding and openflow apps
* In order to delete a previously running controller add the ALWAYS_RM=TRUE env-var.

## Running The Experiment Container
### Single Experiment
This can be run using the demo command:

`./demo/run_experiment.sh`
        
* CONTROLLER is set to the relevant controller DNS name
* The script assumes NETWORK is set to the network name to be used from the ITZ (Internet Topology Zoo) -
requires internet connectivity to fetch the relevant GraphML file
    * The example works with the Abilene ISP network as it is the default of the script's "NETWORK" environment variable
    * You can currently change the way the GraphML file is loaded only by editing the relevant code
* The environment preparation script will define the following
    * EXP_NET=sdn-net
    * EXP_DATA_PATH=/data/
    * CONTROLLER=controller 
* At the end of the experiment the log will state the full path of the experiment files
(generated config files, logs, gathered samples etc.)

### Multiple Experiments
If you want to run experiments on multiple networks, we provide anouther helper script:

`./demo/run_list_of_experiments.sh`

The environment is expected to be the same as in the single experiment example except for the NETWORK variable.

In order to select the ITZ networks to be used for the experiments you can change the file "./demo/ISP_list.txt".
## Transforming samples to HD5
In order to analyze the samples, it is easier to use the HD5 file format.

To do that we have another helper script to use:
```
EXP_DIR=<the folder with the experiment files>
EXP_LINKS_CSV=<name of the topology csv created during the experiment>
./demo/prepare_experiment_output_for_analysis.sh
```

## Troubleshooting
* Make sure all hosts in the experiment were found
    - If "ssh: connect to host _IP_ port 22: No route to host" is seen in the
    sender log file ("sender-_IP_.log") the sender has failed to start because
    of a failed connection and you should rerun the experiment.