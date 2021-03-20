VERSION=v0.37.5 # use the latest release version from https://github.com/google/cadvisor/releases
sudo docker run \
	  --rm \
	  --volume=/:/rootfs:ro \
	  --volume=/var/run:/var/run:ro \
	  --volume=/sys:/sys:ro \
	  --volume=/var/lib/docker/:/var/lib/docker:ro \
	  --volume=/dev/disk/:/dev/disk:ro \
	  --publish=8088:8080 \
	  --detach=true \
          --name=cadvisor \
	  --privileged \
	  --device=/dev/kmsg \
	  gcr.io/cadvisor/cadvisor:$VERSION
