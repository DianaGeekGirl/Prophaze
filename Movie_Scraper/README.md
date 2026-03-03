# Webkyte Movie Anti-Piracy Search API

A Flask-based REST API application for automated movie search and verification using Playwright, containerized with Docker, and deployed on a self-hosted Kubernetes cluster.

**Live Deployment**: http://3.106.188.31:30007  
**Docker Hub Image**: https://hub.docker.com/r/moviechecker/webkyte-antipiracy

## Table of Contents

1. [Prerequisites](#prerequisites)  
   1.1 [Local Development](#local-development)  
   1.2 [Self-Hosted Kubernetes Cluster](#self-hosted-kubernetes-cluster)  
2. [Architecture](#architecture)  
   2.1 [Complete Deployment Pipeline](#complete-deployment-pipeline)  
   2.2 [Kubernetes Cluster Architecture](#kubernetes-cluster-architecture)  
3. [File Structure](#file-structure)  
4. [Installation & Setup](#installation--setup)  
   4.1 [1. Cluster Setup Steps](#1-cluster-setup-steps)  
      4.1.1 [Step 1.1: Launch EC2 Instance](#step-11-launch-ec2-instance)  
      4.1.2 [Step 1.2: Connect to the Instance](#step-12-connect-to-the-instance)  
      4.1.3 [Step 1.3: Install Kubernetes Dependencies](#step-13-install-kubernetes-dependencies)  
      4.1.4 [Step 1.4: Initialize Kubernetes Cluster](#step-14-initialize-kubernetes-cluster)  
      4.1.5 [Step 1.5: Install Network Plugin (Flannel)](#step-15-install-network-plugin-flannel)  
      4.1.6 [Step 1.6: Disable Password Authentication (Security)](#step-16-disable-password-authentication-security)  
      4.1.7 [Step 1.7: Verify Cluster Setup](#step-17-verify-cluster-setup)  
   4.2 [2. Docker Image Build, Push & Deploy](#2-docker-image-build-push--deploy)  
      4.2.1 [Docker Hub Repository](#docker-hub-repository)  
      4.2.2 [Step 2.1: Build Docker Image Locally](#step-21-build-docker-image-locally)  
      4.2.3 [Step 2.2: Test Docker Image Locally](#step-22-test-docker-image-locally)  
      4.2.4 [Step 2.3: Push Image to Docker Hub](#step-23-push-image-to-docker-hub)  
      4.2.5 [Step 2.4: Pull Image from Docker Hub (For Distribution)](#step-24-pull-image-from-docker-hub-for-distribution)  
      4.2.6 [Dockerfile Layers (What gets built)](#dockerfile-layers-what-gets-built)  
   4.3 [3. Kubernetes Deployment Steps](#3-kubernetes-deployment-steps)  
      4.3.1 [Step 3.1: Kubernetes Pulls Image from Docker Hub](#step-31-kubernetes-pulls-image-from-docker-hub)  
      4.3.2 [Step 3.1: Copy Kubernetes Manifests to Cluster](#step-31-copy-kubernetes-manifests-to-cluster)  
      4.3.3 [Step 3.2: Apply Kubernetes Resources](#step-32-apply-kubernetes-resources)  
      4.3.4 [Step 3.3: Verify Deployment](#step-33-verify-deployment)  
      4.3.5 [Step 3.4: View Application Logs](#step-34-view-application-logs)  
5. [How to Access the Application](#how-to-access-the-application)  
   5.1 [AWS Instance Details](#aws-instance-details)  
   5.2 [Security Group Configuration](#security-group-configuration)  
   5.3 [Access via Web Browser](#1-access-via-web-browser)  
6. [API Endpoints](#api-endpoints)  
7. [Docker Image Reference](#docker-image-reference)  
8. [Security Features](#security-features)  
9. [Application Access](#application-access)


## Prerequisites

### Local Development
- Python 3.8+
- pip (Python package manager)
- Docker 20.10+
- kubectl CLI
- Git

### Self-Hosted Kubernetes Cluster
- Ubuntu 20.04 LTS or later (on EC2 or VM)
- Minimum 2 vCPU and 4GB RAM
- SSH key-based access configured
- Docker installed and running on the host
- kubeadm, kubelet, and kubectl installed

## Architecture

### Complete Deployment Pipeline

```
LOCAL MACHINE                    DOCKER HUB                    KUBERNETES CLUSTER
═════════════════════════════════════════════════════════════════════════════════════

App Source Code
    ├── app.py
    ├── webkyte_automation.py
    ├── requirements.txt
    ├── templates/
    └── Dockerfile
        │
        ├─→ docker build          
        │       ↓
        │   Docker Image
        │   (850MB)  ─────────────→  moviechecker/webkyte-antipiracy:v1  
        │                               (Stored on Docker Hub Registry)
        │                                       │
        │                                       ↓
        │                    (ImagePullPolicy: Always)
        │                                       │
        │                                   Pulled by
        │                                       ↓
        │                        Kubernetes Deployment
        │                                       ↓
        │                    ┌──────────────────┴──────────────────┐
        │                    ↓                                      ↓
        │         Pod 1 (Flask App)                    Pod 2 (Flask App)
        │         Port: 5000                           Port: 5000
        │                    │                                      │
        │                    └──────────────────┬──────────────────┘
        │                                       ↓
        │                        NodePort Service (30007)
        │                                       ↓
        └──────────────────────────────→  Public: 3.106.188.31:30007

```

### Kubernetes Cluster Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       │ HTTP (Port 30007)
       │
┌──────▼─────────────────────────────┐
│         Kubernetes Cluster         │
│                                    │
│  ┌────────────────────────────┐   │
│  │  NodePort Service (30007)  │   │
│  └────────────┬───────────────┘   │
│               │                   │
│  ┌────────────▼──────────────┐   │
│  │  Deployment (2 Replicas)   │   │
│  └─────────────────────────────┘  │
│  ┌─────────────┐ ┌─────────────┐ │
│  │   Pod 1     │ │   Pod 2     │ │
│  │ Port: 5000  │ │ Port: 5000  │ │
│  └─────────────┘ └─────────────┘ │
└────────────────────────────────────┘
```

## File Structure

```
Movie_Scraper/
├── app.py                    # Flask REST API server
├── webkyte_automation.py     # Playwright movie search automation
├── Dockerfile               # Docker image build configuration
│                              └─→ Builds: moviechecker/webkyte-antipiracy:v1
├── requirements.txt         # Python dependencies (pip packages)
├── templates/
│   └── index.html          # Web interface
├── k8s/                    # Kubernetes manifests
│   ├── namespace.yaml      # Kubernetes namespace
│   ├── deployment.yaml     # Uses image from Docker Hub
│   └── service.yaml        # Exposes NodePort 30007
└── README.md               # This file
```

## Installation & Setup

### 1. Cluster Setup Steps

#### Step 1.1: Launch EC2 Instance 
```bash
# Recommended configuration (our actual setup):
# - AMI: Ubuntu Server 20.04 LTS
# - Instance Type: t3.micro (free tier)
# - Security Group: Allow SSH (22), HTTP (80), HTTPS (443), and NodePort (30007)
# - Storage: 20GB minimum
# - Region: ap-southeast-2 (Asia Pacific - Sydney)
# - Key Pair: k8s-key
```

#### Step 1.2: Connect to the Instance
```bash
# Set correct permissions on SSH key
chmod 400 ~/Desktop/prophaze/AWS_keypair/k8s-key.pem

# SSH into the instance
ssh -i ~/Desktop/prophaze/AWS_keypair/k8s-key.pem ubuntu@3.106.188.31
```

#### Step 1.3: Install Kubernetes Dependencies
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker
sudo apt install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Disable swap (required for kubeadm)
sudo swapoff -a
sudo sed -i '/ swap / s/^/#/' /etc/fstab

# Install kubeadm, kubelet, kubectl
curl -fsSLo /usr/share/keyrings/kubernetes-archive-keyring.gpg https://packages.cloud.google.com/apt/doc/apt-key.gpg
echo "deb [signed-by=/usr/share/keyrings/kubernetes-archive-keyring.gpg] https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo apt update
sudo apt install -y kubeadm kubelet kubectl
sudo apt-mark hold kubeadm kubelet kubectl
```

#### Step 1.4: Initialize Kubernetes Cluster
```bash
# Get the private IP of the instance
PRIVATE_IP=$(hostname -I | awk '{print $1}')

# Initialize kubeadm with pod network CIDR
sudo kubeadm init \
  --pod-network-cidr=10.244.0.0/16 \
  --apiserver-advertise-address=$PRIVATE_IP

# Configure kubectl for current user
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

# Verify cluster initialization
kubectl get nodes
```

#### Step 1.5: Install Network Plugin (Flannel)
```bash
# Apply Flannel CNI (Container Network Interface)
kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml

# Wait for nodes to be ready (may take 1-2 minutes)
kubectl get nodes -w
```

#### Step 1.6: Disable Password Authentication (Security)
```bash
# Edit SSH configuration
sudo nano /etc/ssh/sshd_config

# Change the following lines:
# PasswordAuthentication no
# PubkeyAuthentication yes
# PermitRootLogin no

# Restart SSH daemon
sudo systemctl restart sshd
```

#### Step 1.7: Verify Cluster Setup
```bash
# Check cluster nodes
kubectl get nodes

# Expected output:
# NAME          STATUS   ROLES           AGE   VERSION
# k8s-master    Ready    control-plane   XXm   vX.XX.X

# Check cluster info
kubectl cluster-info
```

### 2. Docker Image Build, Push & Deploy

#### Docker Hub Repository
- **Repository**: https://hub.docker.com/r/moviechecker/webkyte-antipiracy
- **Image Name**: `moviechecker/webkyte-antipiracy`
- **Current Version**: `v1`
- **Full Image ID**: `moviechecker/webkyte-antipiracy:v1`

#### Step 2.1: Build Docker Image Locally

```bash
# Set Docker environment variable for socket access
export DOCKER_HOST=unix:///var/run/docker.sock

# Ensure Docker daemon is running
sudo systemctl start docker

# Navigate to project directory
cd /home/diana/Desktop/prophaze/Movie_Scraper

# Build the Docker image
docker build -t moviechecker/webkyte-antipiracy:v1 .

# Verify image was built successfully
docker images | grep webkyte-antipiracy
```

Expected output:
```
REPOSITORY                              TAG   IMAGE ID     CREATED          SIZE
moviechecker/webkyte-antipiracy         v1    abc123def    2 minutes ago    850MB
```

#### Step 2.2: Test Docker Image Locally

```bash
# Run the container locally to test
docker run -p 5000:5000 moviechecker/webkyte-antipiracy:v1

# In another terminal, test the API
curl http://localhost:5000

# Stop the container (Ctrl+C in the first terminal)
```

#### Step 2.3: Push Image to Docker Hub

```bash
# Login to Docker Hub
docker login
# Enter your Docker Hub username and password

# Push the image to Docker Hub
docker push moviechecker/webkyte-antipiracy:v1

# Verify push was successful
# Check Docker Hub: https://hub.docker.com/r/moviechecker/webkyte-antipiracy
```

#### Step 2.4: Pull Image from Docker Hub (For Distribution)

**Anyone can now pull and use this image:**

```bash
# Pull the image from Docker Hub
docker pull moviechecker/webkyte-antipiracy:v1

# Run it locally
docker run -p 5000:5000 moviechecker/webkyte-antipiracy:v1

```

#### Dockerfile Layers (What gets built)

The Dockerfile creates an image with:
1. **Base Image**: `mcr.microsoft.com/playwright/python:v1.40.0-jammy`
   - Includes Python + Playwright + Chromium browser
2. **Dependencies**: `requirements.txt` installed via pip
3. **Application Code**: Flask app + Playwright automation
4. **Security**: Runs as non-root user `appuser`
5. **Port**: Exposes port 5000

### 3. Kubernetes Deployment Steps

#### Step 3.1: Kubernetes Pulls Image from Docker Hub

When you deploy to Kubernetes, the cluster automatically:
- Pulls `moviechecker/webkyte-antipiracy:v1` from Docker Hub
- Creates 2 pod replicas with this image
- Exposes the service on port 30007 (NodePort)

#### Step 3.1: Copy Kubernetes Manifests to Cluster
```bash
# From your local machine, copy the k8s directory to the cluster
scp -i ~/Desktop/prophaze/AWS_keypair/k8s-key.pem \
    -r /home/diana/Desktop/prophaze/Movie_Scraper/k8s \
    ubuntu@<INSTANCE_IP>:/home/ubuntu/

# SSH into the cluster
ssh -i ~/Desktop/prophaze/AWS_keypair/k8s-key.pem ubuntu@<INSTANCE_IP>
```

#### Step 3.2: Apply Kubernetes Resources

The `k8s/deployment.yaml` file contains this key line:

```yaml
spec:
  containers:
  - name: webkyte-app
    image: moviechecker/webkyte-antipiracy:v1  # ← References Docker Hub image
    imagePullPolicy: Always
    ports:
    - containerPort: 5000
```

This tells Kubernetes to:
1. Pull `moviechecker/webkyte-antipiracy:v1` from Docker Hub
2. Create 2 replicas of this container
3. Expose each container on internal port 5000
4. The NodePort Service routes external traffic (port 30007) → internal pods (port 5000)

```bash
# Create namespace 
kubectl apply -f k8s/namespace.yaml

# Deploy the application (pulls image from Docker Hub)
kubectl apply -f k8s/deployment.yaml

# Create the service (exposes on port 30007)
kubectl apply -f k8s/service.yaml

# Watch deployment rollout
kubectl rollout status deployment/webkyte-antipiracy

# Expected output:
# deployment "webkyte-antipiracy" successfully rolled out
```

#### Step 3.3: Verify Deployment
```bash
# Check pods are running
kubectl get pods -o wide

# Expected output shows 2 running pods:
# NAME                                  READY   STATUS    RESTARTS   AGE
# webkyte-antipiracy-xxxxxxxxxx-xxxxx   1/1     Running   0          XXs
# webkyte-antipiracy-xxxxxxxxxx-xxxxx   1/1     Running   0          XXs

# Check services
kubectl get services

# Expected output:
# NAME                          TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)
# webkyte-antipiracy-service    NodePort   10.XX.XX.XX     <none>        80:30007/TCP

# Check deployment details
kubectl get deployment webkyte-antipiracy
```

#### Step 3.4: View Application Logs
```bash
# View logs from all pods
kubectl logs -l app=webkyte-antipiracy --tail=50

# View logs from specific pod
kubectl logs <POD_NAME> -f

# Example:
kubectl logs webkyte-antipiracy-xxxxxxxxxx-xxxxx -f
```

## How to Access the Application

### AWS Instance Details
- **Instance ID**: i-0c7690bc536ed9870
- **Instance Type**: t3.micro
- **Instance Name**: kubernetes-node
- **Region**: ap-southeast-2 (Asia Pacific - Sydney)
- **Private IP**: 172.31.3.180
- **Public IP**: 3.106.188.31
- **Key Pair**: k8s-key
- **SSH Access**: `ssh -i ~/Desktop/prophaze/AWS_keypair/k8s-key.pem ubuntu@3.106.188.31`

### Security Group Configuration
- Port 22 (SSH) - For SSH access
- Port 80 (HTTP) - For web traffic
- Port 6443 (TCP) - Kubernetes API Server
- Port 10250 (TCP) - kubelet API
- Port 30007 (TCP) - **NodePort Service (Application)**

### 1. Access via Web Browser

**Live Application URL**: 
```
http://3.106.188.31:30007
```

The application is currently running and accessible at: **http://3.106.188.31:30007**


## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface (index.html) |
| `/api/search` | POST | Start new movie search |
| `/api/search/<id>` | GET | Get search status or results |
| `/api/export/<id>` | GET | Export results as CSV |
| `/health` | GET | Health check endpoint |

## Docker Image Reference

| Property | Value |
|----------|-------|
| **Repository** | moviechecker/webkyte-antipiracy |
| **Docker Hub URL** | https://hub.docker.com/r/moviechecker/webkyte-antipiracy |
| **Current Tag** | v1 |
| **Full Image Name** | moviechecker/webkyte-antipiracy:v1 |
| **Base Image** | mcr.microsoft.com/playwright/python:v1.40.0-jammy |
| **Size** | ~850MB |
| **Architecture** | Linux/amd64 |
| **Includes** | Python, Playwright, Chromium Browser |
| **Entry Point** | Flask app on port 5000 |
| **User** | appuser (non-root) |

**Pull Command**:
```bash
docker pull moviechecker/webkyte-antipiracy:v1
```

**Run Locally**:
```bash
docker run -p 5000:5000 moviechecker/webkyte-antipiracy:v1
```

**View on Docker Hub**:
```
https://hub.docker.com/r/moviechecker/webkyte-antipiracy
```

## Security Features

### 1. SSH Key-Based Authentication
- ✅ Password authentication disabled on cluster
- ✅ Only SSH keys can connect to the instance
- ✅ Private key stored locally with restricted permissions (chmod 400)

### 2. Container Security
- ✅ Non-root user (`appuser`) runs the application
- ✅ Container runs with read-only root filesystem where possible
- ✅ Resource limits set to prevent resource exhaustion
- ✅ Liveness and readiness probes for automatic pod restart

### 3. Network Security
- ✅ Service uses NodePort (can be restricted via security groups)
- ✅ Network policies can be implemented with Calico or similar
- ✅ Internal pod-to-pod communication isolated by default


### Application Access

Open your web browser and navigate to:
```
http://3.106.188.31:30007
```

You should see the Movie Anti-Piracy Search API web interface with the form to submit searches.

