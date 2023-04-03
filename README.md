# response-ml: agent creation and machine learning integration

> This readme is devoted to aid building agents that respond in real time to eks cluster setttings:
> 1. Agent <br/>
> 2. Advisor <br/>
> 3. Docker<br/>
> 4. Agent Deployment <br/>

## __Agent__
1. Agent lives in the agent.py file. 
2. The agent uses the advisor to set up a connection with the data source, and ingest data.
2. Then the agent performs logic and writes updated limits/requests to openverso charts in github. 

## __Advisor__ 
1. There are 3 types of advisors at the agents desposal: prometheus, socket, spark. 
2. Current agent implementation uses the prometheus based client to send queries to the server
    a.the prometheus server ip and port information can be found in AWS EKS console, under endpoints
3. Current agent implementation finds the limit and request for all pods and writes them to github. 

## __Docker__ 
1. To build docker image
```console
docker build -t imagename:version . 
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
    a. update in the yaml file image: teamrespons/respons_agent:version
2. deploy 
```console
kubectl create -f https://raw.githubusercontent.com/DISHDevEx/response-ml/vinny/responseAgent/charts/respons_agent_manifest.yml
```

