FROM debian:stretch 

ARG DEBIAN_FRONTEND=noninteractive 

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
    python-netaddr \
    sudo \
    libsctp-dev \
    mininet \
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

# Add the repo files in (with .git so we can later upgrade at runtime)
ADD .git ./.git

# Default command
ADD docker-entry-point.sh ./
ENTRYPOINT ["./docker-entry-point.sh"]
