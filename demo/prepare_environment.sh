#!/bin/bash

export EXP_NET=sdn-net

export EXP_DATA_PATH=/data/

sudo docker network create $EXP_NET

export CONTROLLER=controller

`dirname ${BASH_SOURCE[0]}`/run_onos_controller.sh

