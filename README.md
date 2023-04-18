# FONPR: Automated 5G Network Control and Continuous Improvement

> This readme is intended to provide background on RESPONS 5G network control agents and their deployment.

> Contents:
> 1. Agent <br/>
> 2. Advisor <br/>
> 3. Action Handler <br/>
> 4. Docker<br/>
> 5. Agent Deployment <br/>
> 6. Test Runbook <br/>

## __1. Agent__
An Agent is responsible for implementing a policy, i.e. mapping observed system state to desired control actions. The policy can be informed by subject matter experts, or learned independently by a reinforcement learning (RL) algorithm.

General usage:
* Agent lives as a script in the agent.py file.
* The Agent script is run automatically on deployment in the network cluster as a containerized application, and executes its logic at regular intervals.
* The Agent utilizes an Advisor function to set up a connection with the data source, and ingest data.
* The Agent executes policy logic and updates cluster (Helm) configuration files in github via the Action Handler. 

## __2. Advisor__
An Advisor is responsible for connecting with a data source, ingesting data, and preprocessing / filtering that data prior to handing it off to the Agent.

The Prometheus based advisor to send queries to a Prometheus server.

To target the server, the ip address and port number can be found as follows:

    ip:port found at
    -  AWS → management console → EKS → clusters → resources tab → service and networking tab → endpoints → filter for Prometheus → Prometheus server endpoint


## __3. Action Handler__
An Action Handler is responsible for taking the requested cluster configuration updates (actions) and update the controlling configuration file accordingly.

The current architecture leverages GitHub for revision control and housing of the cluster configuration files. When a config file is updated, it triggers redeployment of the network cluster via Flux.

General usage:
* The ActionHandler class takes in a GitHub token, the target file path within the repository, branch name, and a dictionary of agent-requested value updates.
* The current version of the value file is fetched from GitHub, updated with the new values, and then pushed back to the repository, triggering a new cluster deployment.

## __4. Docker__
The Agent and its helper functions are containerized using Docker.

To view existing docker images locally:
To pull docker image from registry
```console
docker pull -t <imagename>:<version> . 

# e.g.
docker pull -t teamrespons/respons_agent:v0.0 .
```
To run docker image locally as a container
```console
docker run <imageid>
```

To create new images and contribute them:
To build docker image from an updated Dockerfile
```console
docker build -t teamrespons/respons_agent:<tagname> . 
```
To run docker image locally as a container
```console
docker run <imageid>
```
To push docker image to dockerhub under the response-ml
```console
docker push teamrespons/respons_agent:<tagname>
```

## __5. Agent Deployment__ 
Pre-Requisites:
1. Set up your machine with the following CLI tools:

    AWS CLI

    Kubectl

    Helm
    
2. Set up your local AWS CLI Environment Variables for an account that has access to the EKS cluster:
```console
export AWS_ACCESS_KEY_ID=""
export AWS_SECRET_ACCESS_KEY=""
export AWS_SESSION_TOKEN=""
```

3. Update local kubectl config file:

```console
aws eks --region <region> update-kubeconfig --name <clustername>
```
Deployment:
1. Update deployment/respons_agent_manifest.yml

    a. Update in the yaml file to specify which image you want deployed into the cluster.
     - "file image: teamrespons/respons_agent:version"
2. deploy 
```console
kubectl create -f https://raw.githubusercontent.com/DISHDevEx/respons-ml/main/deployment/respons_agent_manifest.yml
```

## __6. Test Runbook__ 

When testing functionality, for a PR or otherwise, the following steps can be taken to ensure integrity of the build:

Prerequisites:
* Repo has been cloned locally and the branch in question is checked out.
* Logged in to dockerhub
* Kubectl configured for your target cluster and context set for your desired namespace

1. Within the root directory of the repo build the docker image from source.

```bash
docker build -t teamrespons/respons_agent:<your_test_image> .
```

2. Push the freshly built test image back up to DockerHub.

```bash
docker push teamrespons/respons_agent:<your_test_image>
```

3. Create a K8s pod config file and point to it for deployment into the cluster.

test-deployment.yaml
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: <your_pod_name>
spec:
  volumes:
  - name: shared-data
    emptyDir: {}
  containers:
  - name: <your_container_name>
    image: teamrespons/respons_agent:<your_test_image>
    command: ["python3"]
    args: ["fonpr/agent.py", "--interval", "2"]
    volumeMounts:
    - name: shared-data
      mountPath: /usr/share/spark
  hostNetwork: true
  dnsPolicy: Default
```
deploy into cluster
```bash
kubectl apply -f /path/to/test-deployment.yaml
```

4. Confirm that the pod has been successfully deployed.

```bash
kubectl get pods
```

5. Confirm that the pod is functioning as expected.

```bash
kubectl logs <your_pod_name>
```

6. Confirm that the target file is updating in GitHub.