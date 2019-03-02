#!/bin/bash
set -e

usage_and_exit() {
  echo "------------------------------------------------------------------------"
  echo "Run SDN RUN_EXPERIMENT"
  echo "Assumes the experiment script, which handles the GraphML file is defined"
  echo "as RUN_EXPERIMENT environment variable"
  echo "Set CONTROLLER=<controller_dns_name> to set a different controller for the experiment"
  echo "options:"
  echo "    -h            display help information"
  echo "    /path/file    run experiment with local topology graphml file"
  echo "    URL           download graphml from URL and run experiment with it"
  echo "Otherwise - exit with 1"
  echo "NOTE: The container must run as root (privileged) to access network configurations in mininet"
  exit 1
}

convert_controller_name_to_ip() {
    CONTROLLER_IP=`getent ahostsv4 $CONTROLLER | head -n1 | cut -d" " -f1`

    if [[ ! $CONTROLLER_IP =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]
    then
        echo "The CONTROLLER EnvVar is invalid:"
        echo "(CONTROLLER==$CONTROLLER -> CONTROLLER_IP==$CONTROLLER_IP)... Exiting!"
        exit 1
    fi

    echo Pinging the SDN controller:

    ping -c 3 $CONTROLLER_IP
    if [[ $? -eq 0 ]]
    then
        echo Ping to controller at ip-addr=$CONTROLLER_IP OK!
    else
        echo Unable to ping controller at ip-addr=$CONTROLLER_IP... Exiting!
        exit 1
    fi
}

check_is_graphml() {
  if [[ ${GRAPHML: -8} != ".graphml" ]]; then
    echo "File is not GraphML - doesn't have the .graphml extension!"
    usage_and_exit
  fi
}

launch() {
  # If only a single option is given and it is "-h"
  # display help information
  if [[ $1 == "-h" ]]; then
    usage_and_exit
  else

    # Move to scripts dir
    cd ~/scripts

    # If first argument is a URL then download the graphml and run the experiment
    # with it
    if [[ $1 =~ ^(file|http|https|ftp|ftps):// ]]; then
      url=$1
      GRAPHML="${url##*/}"
      check_is_graphml $GRAPHML
      wget -O $GRAPHML $url
      CONTROLLER_IP=$CONTROLLER_IP GRAPHML=$GRAPHML $RUN_EXPERIMENT

    # If first argument is an absolute file path then run the experiment with it
    elif [[ $1 =~ ^/ ]]; then
      check_is_graphml $1
      CONTROLLER_IP=$CONTROLLER_IP GRAPHML=$GRAPHML $RUN_EXPERIMENT

    # Unknown argument
    else
      echo 'Unknown argument (arg=$1), see help below...'
      usage_and_exit
    fi
  fi
}

if [[ -v $RUN_EXPERIMENT ]]; then
  echo "Missing RUN_EXPERIMENT environment variable! See help below..."
  usage_and_exit
fi

convert_controller_name_to_ip

if [[ $# -eq 1 ]]; then
  launch $1
else
  echo 'Only 1 argument is allowed. See help below...'
  usage_and_exit
fi
