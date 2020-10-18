#!/bin/bash
set -x

# see how many hosts there are
export HOST_COUNT=`pgrep -c ITGRecv.sh`

if (( $HOST_COUNT == 0 )) ; then echo "Topology isn't online - no hosts found!" ; exit 1 ; fi

if (( $HOST_COUNT > 253 )) ; then echo "Topology is too big - current support is for up to 253 hosts only!" ; exit 1 ; fi

# declare & create sender scripts base path
export SENDERS_BASE=$EXP_DIR/senders
mkdir $SENDERS_BASE

# generate config files for senders
./generate_sender_scripts.py -d $SENDERS_BASE -n $HOST_COUNT

# create list of interfaces + indexes (ifIndex)
ip a | sed '/^ / d' - | cut -d: -f1,2 > $EXP_DIR/intfs-list

# turn on sflow
./set_ovs_sflow.sh

CSV_TITLES=`cat csv_titles`
# start collecting sflow datagrams
sflowtool -k -L $CSV_TITLES &> $EXP_DIR/sflow-datagrams &

# run the senders
HOST_IP_ADDRESSES=`h=1 ; while (( $h <= $HOST_COUNT )) ; do echo 10.0.0.$((h++)) ; done`

SSH_PROCS=""
for host_addr in $HOST_IP_ADDRESSES ; do
	HOST_SENDER=$SENDERS_BASE/sender-$host_addr.sh

	ssh $host_addr -o StrictHostKeyChecking=false -o ServerAliveInterval=10 "$HOST_SENDER &> $EXP_DIR/sender-$host_addr.log" &
	SSH_PROCS="$SSH_PROCS $!"
done

# zombie killer: sometimes timeout is stuck waiting for a zombie child process, this hack eliminates the problem
bash -c $'while true ; do ps -e -o stat,ppid | grep \'^Z \' | awk \'{print $2}\' | xargs --no-run-if-empty kill -9; sleep 1 ;done' &
ZOMBIE_KILLER_PID=$!
echo "Waiting for senders (proc_ids = $SSH_PROCS )"
wait $SSH_PROCS
kill $ZOMBIE_KILLER_PID
# stop datagram collection
pkill -15 sflowtool

