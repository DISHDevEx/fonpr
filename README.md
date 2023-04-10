<<<<<<< HEAD
# FONPR: agent creation and machine learning integration
=======
# respons-ml: Automated 5G Network Control and Continuous Improvement
>>>>>>> 94bca0e (Updated readme for clarity)

> This readme is intended to provide background on RESPONS 5G network control agents and their deployment.

> Contents:
> 1. Agent <br/>
> 2. Advisor <br/>
> 3. Action Handler <br/>
> 4. Docker<br/>
> 5. Agent Deployment <br/>

## __1. Agent__
An Agent is responsible for implementing a policy, i.e. mapping observed system state to desired control actions. The policy can be informed by subject matter experts, or learned independently by a reinforcement learning (RL) algorithm.

General usage:
* Agent lives as a script in the agent.py file.
* The Agent script is run automatically on deployment in the network cluster as a containerized application, and executes its logic at regular intervals.
* The Agent utilizes an Advisor function to set up a connection with the data source, and ingest data.
* The Agent executes policy logic and updates cluster (Helm) configuration files in github via the Action Handler. 

## __2. Advisor__
An Advisor is responsible for connecting with a data source, ingesting data, and preprocessing / filtering that data prior to handing it off to the Agent.

The current agent implementation uses the Prometheus based advisor to send queries to a Prometheus server.

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
docker pull -t imagename:version . 

# e.g.
docker pull -t teamrespons/respons_agent:v0.0 .
```
To run docker image locally as a container
```console
docker run imageid
```

To create new images and contribute them:
To build docker image from an updated Dockerfile
```console
docker build -t teamrespons/respons_agent:tagname . 
```
To run docker image locally as a container
```console
docker run imageid
```
To push docker image to dockerhub under the response-ml
```console
docker push teamrespons/respons_agent:tagname
```

## __Agent Deployment__ 
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
aws eks --region {region} update-kubeconfig --name {clustername}
```
Deployment:
1. Update deployment/respons_agent_manifest.yml

    a. Update in the yaml file to specify which image you want deployed into the cluster.
     - "file image: teamrespons/respons_agent:version"
2. deploy 
```console
kubectl create -f https://raw.githubusercontent.com/DISHDevEx/respons-ml/main/deployment/respons_agent_manifest.yml
```

