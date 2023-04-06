# FONPR: agent creation and machine learning integration

> This readme is devoted to aid deployment of agents that respond in real time to eks cluster settings:
> 1. Agent <br/>
> 2. Advisor <br/>
> 3. Action Handler <br/>
> 4. Docker<br/>
> 5. Agent Deployment <br/>

## __Agent__
1. Agent lives in the agent.py file. 
2. The agent uses the advisor to set up a connection with the data source, and ingest data.
3. Then the agent performs policy logic and writes updated limits/requests to openverso charts in github via the action handler. 

## __Advisor__ 
1. There are 3 types of advisors at the agents desposal: prometheus, socket, spark. 
2. The current agent implementation uses the Prometheus based advisor to send queries to the Prometheus server.

    ip:port found at
    -  AWS → management console → EKS → clusters → resources tab → service and networking tab → endpoints → filter for Prometheus → Prometheus server endpoint

3. Agent implementation finds the limit and request for all pods and writes them to github. 

## __Action Handler__
1. The ActionHandler class takes in a GitHub token, target file path within the repository, branch name, and agent-requested parameter update values.
2. The current version of the file is fetched from github, updated with the new values, and then pushed back to the repository.

## __Docker__ 
1. To pull docker image from registry
```console
docker pull -t imagename:version . 

# e.g.
docker pull -t teamrespons/respons_agent:v0.0 .
```
2. To run docker image locally as a container
```console
docker run imageid
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

