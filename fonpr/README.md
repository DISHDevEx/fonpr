# Action Handler
The FONPR product provides a closed loop control system leveraging an Agent to make updates to infrastructure configuration.

The agent conducts data ingestion via an advisor, executes logic to output a dictionary of requested actions based on the advisor outputs, and updates the controlling document in its remote repo using the action handler.

## Preliminary Test Procedure
The functionality to be demonstrated is as follows:
1. Successfully establish connection with AWS secrets manager, the Prometheus server, and GitHub.
2. Process incoming metrics and create appropriate limits and requests updates.
3. Push the updated value file back to GitHub.

**To test Agent functionality manually, the following actions can be taken**

Prerequisites:
* Docker locally installed


Pull the latest agent image from DockerHub

```bash
docker pull teamrespons/respons_agent:<most_recent_image_tag>
```

Create a container based on the image, and overide default actions for interactive mode

```bash
docker run -it --name agent_test teamrespons/respons_agent:<most_recent_image_tag> bash
```
You now should be in the container filesystem and see a command line prompt similar to

`root@692b562bed96:/app# `

Pass temporary credentials with access to the cluster from AWS

```console
export AWS_ACCESS_KEY_ID= <your_creds_here>
export AWS_SECRET_ACCESS_KEY= <your_creds_here>
export AWS_SESSION_TOKEN= <your_creds_here>
```

Navigate to the `fonpr` directory and start up a Python shell there

`cd fonpr && python`

In the Python shell, import the `agent` module and run `agent.execute_agent_cycle()` to pull, update, and push, the target value.yaml file (https://github.com/DISHDevEx/openverso-charts/blob/matt/gh_api_test/charts/respons/test.yaml)

```python
import agent
agent.execute_agent_cycle()
```