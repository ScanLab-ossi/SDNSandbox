#!/bin/bash
set -x

# see how many hosts there are
export HOST_COUNT=`pgrep -c ITGRecv.sh`

if (( $HOST_COUNT == 0 )) ; then echo "Topology isn't online - no hosts found!" ; exit 1 ; fi

if (( $HOST_COUNT > 253 )) ; then echo "Topology is too big - current support is for up to 253 hosts only!" ; exit 1 ; fi

# declare & create configuration base path
export CONF_BASE=$EXP_DIR/config
mkdir $CONF_BASE

# generate config files for senders
./generate_config.py -d $CONF_BASE -n $HOST_COUNT

# create list of interfaces + indexes (ifIndex)
ip a | sed '/^ / d' - | cut -d: -f1,2 > $EXP_DIR/intfs-list

# turn on sflow
./set_ovs_sflow.sh

# start collecting sflow datagrams
sflowtool -k &> $EXP_DIR/sflow-datagrams &

# run the senders
HOST_IP_ADDRESSES=`h=1 ; while (( $h <= $HOST_COUNT )) ; do echo 10.0.0.$((h++)) ; done`

for host_addr in $HOST_IP_ADDRESSES ; do
	HOST_CONF=$CONF_BASE/config-$host_addr

	ssh $host_addr -o StrictHostKeyChecking=false $HOST_CONF > /dev/null &
done

wait


# stop datagram collection
pkill -15 sflow

