#!/bin/bash
set -e

usage_and_exit() {
  echo "docker run ML-net [options]"
  echo "Run ML-net experiment with latest version from the GitHub repo"
  echo "Assumes the experiment script, which handles the GraphML file is defined"
  echo "as $RUN_EXPERIMENT environment variable"
  echo "options:"
  echo "    -h            display help information"
  echo "    /path/file    run experiment with local file"
  echo "    URL           download graphml from URL and run experiment with it"
  echo "Otherwise - exit with 1"
  exit 1
}

check_is_graphml() {
  if [ ${GRAPHML: -8} != ".graphml" ]; then
    usage_and_exit
  fi
}

launch() {
  # If only a single option is given and it is "-h"
  # display help information
  if [ $1 == "-h" ]; then
    usage_and_exit
  else

    # If first argument is a URL then download the graphml and run the experiment
    # with it
    if [[ $1 =~ ^(file|http|https|ftp|ftps):// ]]; then
      url=$1
      GRAPHML="${url##*/}"
      check_is_graphml $GRAPHML
      curl -s -o $GRAPHML $1
      $RUN_EXPERIMENT $GRAPHML

    # If first argument is an absolute file path then run the experiment with it
    elif [[ $1 =~ ^/ ]]; then
      check_is_graphml $1
      $RUN_EXPERIMENT $1

    # Unknown argument
    else
      usage_and_exit
    fi
  fi
}

if [ -v $RUN_EXPERIMENT ]; then
  echo "Missing RUN_EXPERIMENT environment variable!"
  echo "Exiting!"
  exit 1
fi

# Start the Open Virtual Switch Service
service openvswitch-switch start

if [[ $GET_LATEST == true ]] ; then
  # Update
  git fetch
  git reset --hard HEAD
fi

# Move to scripts dir
cd ~/scripts

if [[ $# -eq 1 ]]; then
  launch $1
else
  usage_and_exit
fi
