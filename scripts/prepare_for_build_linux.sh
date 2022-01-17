# Install devtoolset-9
yum update -y
yum install -y centos-release-scl
yum install -y devtoolset-9
echo "source /opt/rh/devtoolset-9/enable" >> /etc/bashrc
g++ --version

# Install Python, Java, wget, vim
yum install -y python2 python3 python3-devel wget java-1.8.0-openjdk \
    java-1.8.0-openjdk-devel vim

# Install Ant
cd /tmp
wget https://downloads.apache.org/ant/binaries/apache-ant-1.10.11-bin.zip
unzip apache-ant-1.10.11-bin.zip \
    && mv apache-ant-1.10.11/ /opt/ant \
    && ln -s /opt/ant/bin/ant /usr/bin/ant

# Download Buck
cd /opt
git clone https://github.com/facebook/buck.git

# Set JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk

# Build Buck
cd /opt/buck
ant
ln -s /opt/buck/bin/buck /usr/bin/buck

# Install Watchman
cd /opt/watchman
wget https://github.com/facebook/watchman/releases/download/v2020.09.21.00/watchman-v2020.09.21.00-linux.zip
unzip watchman-v2020.09.21.00-linux.zip
cd /opt/watchman/watchman-v2020.09.21.00-linux
mkdir -p /usr/local/{bin,lib} /usr/local/var/run/watchman
cp bin/* /usr/local/bin
cp lib/* /usr/local/lib
chmod 755 /usr/local/bin/watchman
chmod 2777 /usr/local/var/run/watchman

# Unpack the static python libraries from the manylinux image.
cd /opt/_internal/
XZ_OPT=-9e tar -xf static-libs-for-embedding-only.tar.xz cpython-*/lib/libpython*.a
