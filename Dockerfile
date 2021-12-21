FROM ubuntu:18.04

# Update and install minimal.
RUN \
    apt-get update \
        --quiet \
    && apt-get install \
        --yes \
        --no-install-recommends \
        --no-install-suggests \
# sflowtool build dependencies
    git \
    ca-certificates \
    g++ \
    make \
    automake \
    autoconf \
# python dependencies
    python3 \
    python3-pip \
    python3-setuptools \
# OvS
    openvswitch-switch \
# D-ITG
    d-itg \
# Nping
    nmap \
# Mininet & deps
    mininet \
    iproute2 \
# Clean up packages.
    && apt-get clean

# install sflowtool
WORKDIR /tmp
RUN git clone https://github.com/sflow/sflowtool \
    && cd sflowtool \
    && ./boot.sh \
    && ./configure \
    && make \
    && make install

# Install python requirements
ADD requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

WORKDIR /tmp
ADD sdnsandbox ./sdnsandbox
ADD example.config.json ./example.config.json
ADD docker-entry-point.sh ./docker-entry-point.sh

# Default command
ENTRYPOINT ["./docker-entry-point.sh"]
