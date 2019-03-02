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
    python-netaddr \
    python3 \
    sudo \
    libsctp-dev \
    mininet \
    openvswitch-switch \
    d-itg \
# Clean up packages.
    && apt-get clean \

WORKDIR /tmp

# install sflowtool
RUN git clone http://github.com/sflow/sflowtool \
    && cd sflowtool \
    && ./boot.sh \
    && ./configure \
    && make \
    && make install

WORKDIR /root

# Create SSH keys
RUN cat /dev/zero | ssh-keygen -q -N ""
RUN cat /root/.ssh/id_rsa.pub >> /root/.ssh/authorized_keys
RUN chmod 400 /root/.ssh/*

# HACK around https://github.com/dotcloud/docker/issues/5490
RUN apt-get install -y tcpdump
RUN mv /usr/sbin/tcpdump /usr/bin/tcpdump

ADD scripts ./scripts

# Default command
ADD docker-entry-point.sh ./
ENTRYPOINT ["./docker-entry-point.sh"]
