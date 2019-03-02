#!/bin/bash

set -e

exit_with_msg() {
  echo
  echo $1
  echo Exiting...
  exit 1
}

activate_app() {
  echo Activating $APP...
  echo
  curl -X POST  $CONTROLLER_API/applications/$APP/active --user onos:rocks
  echo
  echo
  echo $APP activated
  echo
}

if [ -z "$EXP_NET" ] ; then
  exit_with_msg "The variable EXP_NET must be set to the name of the docker network to be used in the experiment!"
fi

CONTROLLER_NAME=controller
CONTROLLER_REMOVE_CMD="sudo docker rm -f $CONTROLLER_NAME"

FOUND=0
# Make sure there isn't another container with the same name
controller_found=$(sudo docker container inspect $CONTROLLER_NAME &> /dev/null ; echo $?)
if [ $controller_found -eq $FOUND ] ; then
  if [[ $ALWAYS_RM == TRUE ]] ; then
    $CONTROLLER_REMOVE_CMD
  else
    echo Another "$CONTROLLER_NAME" container exists. Set env ALWAYS_RM=TRUE or use the following command to remove it:
    exit_with_msg "$CONTROLLER_REMOVE_CMD"
  fi
fi


# Run controller docker container as "controller" with exposed ports
sudo docker run --net $EXP_NET --name $CONTROLLER_NAME --rm -d  -p 6653:6653 -p 8101:8101 -p 8181:8181 -p 9876:9876 onosproject/onos

CONTROLLER_API=localhost:8181/onos/v1

echo Waiting for controller to become ready...
TIMEOUT=30
TIMEOUT_COUNTER=0
until $( curl -o /dev/null --silent --head --fail $CONTROLLER_API/applications --user onos:rocks ) ; do
  if [[ $TIMEOUT_COUNTER == $TIMEOUT ]] ; then
    exit_with_msg "Controller did not become ready after timeout! (timeout==$TIMEOUT seconds)"
  fi
  printf '-'
  sleep 1
  ((++TIMEOUT_COUNTER))
done

echo
echo Controller is ready!
echo
sleep 3
echo Activating controller applications...
echo


# Activate the controlker's openflow suite
APP=org.onosproject.openflow
activate_app

# Activate the controller's reactive forwarding feature
APP=org.onosproject.fwd
activate_app
