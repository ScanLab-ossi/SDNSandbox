#!/bin/bash
set -e

usage_and_exit() {
  echo "------------------------------------------------------------------------"
  echo "This SDNSandbox container is designed to run a SDN experiment"
  echo "It assumes the experiment script path is provided via the"
  echo "RUN_EXPERIMENT environment variable and it handles the GraphML input file"
  echo
  echo "Set either:"
  echo "  CONTROLLER=<controller_ip>"
  echo "  CONTROLLER=<controller_dns_name>"
  echo "to set the SDN controller address"
  echo
  echo "options:"
  echo "    -h                  display help information"
  echo "    /path/to/graphml    use graphml experiment topology file from path"
  echo "    URL                 use graphml experiment topology file from URL"
  echo "Otherwise - exit with 1"
  echo "NOTE: The container must run as root (privileged)"
  echo "to access network configurations in mininet"
  exit 1
}

check_controller() {
    CONTROLLER_IP=`getent ahostsv4 $CONTROLLER | head -n1 | cut -d" " -f1`

    # This isn't an exact IP regexp, but it's good enough
    if [[ ! $CONTROLLER_IP =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]
    then
        echo "The CONTROLLER EnvVar is invalid:"
        echo "Got CONTROLLER==$CONTROLLER --> CONTROLLER_IP==$CONTROLLER_IP"
        usage_and_exit
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

check_controller

if [[ $# -eq 1 ]]; then
  launch $1
else
  echo 'Only 1 argument is allowed. See help below...'
  usage_and_exit
fi
