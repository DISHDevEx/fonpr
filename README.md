# FONPR: agent creation and machine learning integration

> This readme is devoted to aid deployment of agents that respond in real time to eks cluster settings:
> 1. Agent <br/>
> 2. Advisor <br/>
> 3. Docker<br/>
> 4. Agent Deployment <br/>

## __Agent__
1. Agent lives in the agent.py file. 
2. The agent uses the advisor to set up a connection with the data source, and ingest data.
3. Then the agent performs logic and writes updated limits/requests to openverso charts in github. 

## __Advisor__ 
1. There are 3 types of advisors at the agents desposal: prometheus, socket, spark. 
2. The current agent implementation uses the Prometheus based advisor to send queries to the Prometheus server.

    ip:port found at
    -  AWS → management console → EKS → clusters → resources tab → service and networking tab → endpoints → filter for Prometheus → Prometheus server endpoint

3. Agent implementation finds the limit and request for all pods and writes them to github. 

## __Docker__ 
1. To build docker image
```console
docker build -t teamrespons/respons_agent:tagname . 
```
2. To run docker image locally as a container
```console
docker run imageid
```
3. To push docker image to dockerhub under the response-ml
```console
docker push teamrespons/respons_agent:tagname
```

## __Agent Deployment__ 
Pre-Requisites:
1. Set up your machine with the following CLI tools:

    AWS CLI

    Kubectl

    Helm
    
2. Set up your local AWS CLI Environment Variables

3. Update local kubectl config file:

```console
aws eks --region {region} update-kubeconfig --name {clustername}
```
Deployment:
1. Update charts/respons_agent_manifest.yml

    a. Update in the yaml file to specify which image you want deployed into the cluster.
     - "file image: teamrespons/respons_agent:version"
2. deploy 
```console
kubectl create -f https://raw.githubusercontent.com/DISHDevEx/respons-ml/main/deployment/respons_agent_manifest.yml
```

