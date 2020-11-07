#!/bin/bash
set -e

service openvswitch-switch start
python3  -m sdnsandbox -c example.config.json -o /opt