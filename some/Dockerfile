FROM jenkins/jenkins:lts

USER root

# Install required packages
RUN apt-get update && apt-get install -y \
    ca-certificates \
    curl \
    apt-transport-https \
    gnupg \
    lsb-release

# Install Docker CLI
RUN curl -fsSL https://get.docker.com | sh

# Install kubectl
RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl \
    && chmod +x kubectl \
    && mv kubectl /usr/local/bin/

# Give Jenkins access to docker socket
RUN groupadd docker || true && usermod -aG docker jenkins

USER jenkins

