FROM debian 
# Based on ozzyjohnson/mininet
MAINTAINER Yossi Solomon <yosisolomon@gmail.com>

ENV DEBIAN_FRONTEND noninteractive 

ENV MININET_REPO https://github.com/mininet/mininet.git 
ENV MININET_INSTALLER mininet/util/install.sh 

ENV MLNET_REPO http://github.com/yossisolomon/ML-net

# Update and install minimal.
RUN \
    apt-get update \
        --quiet \
    && apt-get install \
        --yes \
        --no-install-recommends \
        --no-install-suggests \
    git \
    autoconf \
    automake \
    ca-certificates \
    libtool \
    net-tools \
    patch \
    vim \
    g++ \
    openssh-server \
    openssh-client \
    bc \
    unzip \
    wget \
    python-numpy \
    python-sklearn \
    python-netaddr \
    sudo \
    libsctp-dev \


# Clean up packages.
    && apt-get clean \

WORKDIR /tmp

# install mininet
RUN git clone $MININET_REPO \ 
# A few changes to make the install script behave. 
    && sed -e 's/sudo //g' \ 
    -e 's/~\//\//g' \ 
    -e 's/DEBIAN_FRONTEND=noninteractive//g' \
    -e 's/git:/http:/g' \
    -e 's/\(apt-get -y -q install\)/\1 --no-install-recommends --no-install-suggests/g' \ 
    -i $MININET_INSTALLER \ 

# Install script expects to find this. Easier than patching that part of the script. 
    && touch /.bashrc \ 

# Proceed with the install. 
    && chmod +x $MININET_INSTALLER \ 
    && ./$MININET_INSTALLER -nfv \ 
# Clean up source. 
    && rm -rf /tmp/mininet \ 
    /tmp/openflow

# install sflowtool
RUN git clone http://github.com/sflow/sflowtool \
    && cd sflowtool \
    && ./boot.sh \
    && ./configure \
    && make \
    && make install

# install D-ITG
RUN wget http://traffic.comics.unina.it/software/ITG/codice/D-ITG-2.8.1-r1023-src.zip \
    && unzip D-ITG-2.8.1-r1023-src.zip \
    && cd D-ITG-2.8.1-r1023/src \
    && make sctp=on dccp=on \
    && make install PREFIX=/usr/local

# Clone and install ML-net
WORKDIR /root
RUN git clone $MLNET_REPO

# Create SSH keys
RUN cat /dev/zero | ssh-keygen -q -N ""
RUN cat /root/.ssh/id_rsa.pub >> /root/.ssh/authorized_keys
RUN chmod 400 /root/.ssh/*


# Default command.
ENTRYPOINT ["bash"]
