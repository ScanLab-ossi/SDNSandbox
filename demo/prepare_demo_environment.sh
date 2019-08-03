#!/bin/bash

export EXP_NET=sdn-net

export EXP_DATA_PATH=/data/

sudo docker network create $EXP_NET

export CONTROLLER=controller

./demo/run_onos_controller.sh

