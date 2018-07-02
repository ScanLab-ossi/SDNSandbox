# SDNSandbox
An automated sandbox for provider SDN testing &amp; research
## Building The Container (Example)
  sudo docker build -t SDNSandbox .

## Running The Container (Example)
sudo docker run --privileged --env EXP_DIR=/opt --env RUN_EXPERIMENT=./run_topology_experiment.sh SDNSand http://www.topology-zoo.org/files/Getnet.graphml
