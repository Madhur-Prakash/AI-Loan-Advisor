set -e

echo "####################################### Starting the Installer #######################################"
echo "####################################### Updating the System #######################################"
sudo apt-get update -y

echo "####################################### Installing Required Packages #######################################"
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common \
    gnupg-agent

echo "####################################### Adding Docker Repository #######################################"
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository -y \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"

echo "####################################### Installing Docker #######################################"
sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

echo "####################################### Enabling Docker #######################################"
sudo systemctl start docker
sudo systemctl enable docker