FROM ubuntu:18.04

# Update and install minimal.
RUN \
    apt-get update \
        --quiet \
    && apt-get install \
        --yes \
        --no-install-recommends \
        --no-install-suggests \
    git \
    ca-certificates \
    g++ \
    make \
    automake \
    autoconf \
    openssh-server \
    openssh-client \
    bc \
    unzip \
    wget \
    iputils-ping \
    iproute2 \
    net-tools \
    python3 \
    python3-pip \
    python3-setuptools \
    sudo \
    libsctp-dev \
    openvswitch-switch \
    d-itg \
    netcat \
    tcpdump \
# Clean up packages.
    && apt-get clean

# HACK around https://github.com/dotcloud/docker/issues/5490
RUN cp /usr/sbin/tcpdump /usr/bin/tcpdump

# install sflowtool
WORKDIR /tmp
RUN git clone http://github.com/sflow/sflowtool \
    && cd sflowtool \
    && ./boot.sh \
    && ./configure \
    && make \
    && make install

# install mininet @ a python3-compatible tag
WORKDIR /tmp
RUN git clone git://github.com/mininet/mininet \
    && cd mininet \
    && git checkout -b 2.3.0d5 \
    && ./util/install.sh -s . -nfv

# Install python requirements
ADD requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

ADD sdnsandbox ./sdnsandbox
ADD example.config.json ./example.config.json

# Default command
ENTRYPOINT ["python3  -m sdnsandbox -c example.config.json -o "]
