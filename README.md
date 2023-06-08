# FONPR: Automated 5G Network Control and Continuous Improvement

## Quick Deployment 
DQN agent deployment:
```console
kubectl create -f https://raw.githubusercontent.com/DISHDevEx/fonpr/main/deployment/manifest_dqn_agent.yml
```
BBO agent deployment:
```console
kubectl create -f https://raw.githubusercontent.com/DISHDevEx/fonpr/main/deployment/manifest_bbo_agent.yml
```
V0 agent deployment:
```console
kubectl create -f https://raw.githubusercontent.com/DISHDevEx/fonpr/main/deployment/manifest_v0_agent.yml
```


## First Open Network Pattern Reactors guide: 
> This readme is intended to provide background on First Open Network Pattern Reactors and their deployment.

> Contents:
> 1. Agent <br/>
> 2. Advisor <br/>
> 3. Action Handler <br/>
> 4. Docker<br/>
> 5. Agent Deployment <br/>
> 6. Test Runbook <br/>

## __1. Agent__
An Agent is responsible for implementing a policy, i.e. mapping observed system state to desired control actions. The policy can be informed by subject matter experts, or learned independently by a reinforcement learning (RL) algorithm.

**All agents currently ingest data via prometheus server, and take actions against a yml file that controls the target application.**

**General usage:** 
* Agent lives as a script in the agent.py file.  
* The Agent script is run automatically on deployment in the network cluster as a containerized application, and executes its logic at regular intervals.
* The Agent utilizes an Advisor function to set up a connection with the data source, and ingest data.
* The Agent executes policy logic and updates cluster (Helm) configuration files in github via the Action Handler. 

**V0 agent:**

    Modify hyperparameters in agent_v0.py for custom deployment

 * The primary functionality for the V0 agent is to use hueristics in order to update limits and requests for AMF. 
 * V0 agent allows for improved Kube-Scheduling. 
 * Inputs: Max CPU for AMF, Avg. CPU for AMF, Max Memory for AMF, Avg. Memory for AMF. 
 * Outputs: Update yml file limits and requests for AMF pods. 

**BBO agent:**

    Modify hyperparameters in agent_bbo.py for custom deployment
    
 * Google Vizier Library
 * BBO agent treats the system as a black box. It allows for efficient search of paremeters to optimize a function. It does not understand the function.
 * BBO is aware of X and Y of a function mapping via system: X->system->Y. 
 * The X are the paremters the BBO Agent can modify. 
 * The Y is the reward the BBO agent recieves after making its actions and allowing the actions to manifest in the system. 
 * The current algorithm underneath the BBO agent is Gaussian Process Optimization. 
 * Inputs BBO: Profit = SLO Price - Infra Cost
 * Ouputs BBO: UPF Node Sizing

**DQN agent:** 

    Modify hyperparameters in agent_dqn.py for custom deployment


 * Tensorflow Library 
 * 7 x 20 x 20 x 20 Fully Connected Nueral Network.
 * Uses replay buffer for training.
 * DQN
    * Inputs: Action, Observation, Reward, Discount, Next Step Type, Policy Info, Current Step Type. 
    * Outputs: Q-Value (maximum expected reward) for taking a small sizing action or large sizing action. 
* The agent itself outputs a modification of UPF Node Sizing 



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

* To pull docker image from registry:
    
    ```console
    docker pull -t <imagename>:<version> . 
    
    # e.g.
    docker pull -t teamrespons/respons_agent:v0.0 .
    ```

* To run docker image locally as a container:
    ```console
    docker run <imageid>
    ```

To create new images and contribute them:

*  To Build docker image from an updated Dockerfile
    
    ```console
    docker build -t teamrespons/respons_agent:<tagname> -f <dockerfile name> .  
    
    # e.g. 
    docker build -t teamrespons/respons_agent:v0-agent -f Dockerfile_V0 .
    ```
* To run docker image locally as a container
    ```console
    docker run <imageid>
    ```

* To push docker image to dockerhub under the response-ml
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

    Update in the yaml file to specify which image you want deployed into the cluster.
        
         "file image: teamrespons/respons_agent:version"
        
2. Agent deployments

    DQN agent deployment:
    ```console
    kubectl create -f https://raw.githubusercontent.com/DISHDevEx/fonpr/main/deployment/manifest_dqn_agent.yml
    ```
    BBO agent deployment:
    ```console
    kubectl create -f https://raw.githubusercontent.com/DISHDevEx/fonpr/main/deployment/manifest_bbo_agent.yml
    ```
    V0 agent deployment:
    ```console
    kubectl create -f https://raw.githubusercontent.com/DISHDevEx/fonpr/main/deployment/manifest_v0_agent.yml
    ```
