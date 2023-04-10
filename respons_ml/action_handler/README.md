# Action Handler
The FONPR product provides a closed loop control system leveraging an Agent to make updates to infrastructure configuration.

The Action Handler's job is to take the value updates requested by the Agent, and to update the controlling configuration files accordingly.


## Preliminary Test Procedure
The functionality to be demonstrated is as follows:
1. Successfully access the target GitHub repo using a fine-grained token.
2. Pull the latest version of the target configuration document,
3. Update the values of that document locally according to the specified requested actions,
4. Push the updated document back to the originating branch on the repo.

To test the action handler manually, the following actions can be taken:

Log in to GitHub and create a new token:
Account page → Settings → Developer settings → Personal access tokens → Fine-grained tokens

Select "Generate new token": 
1. give it a name, 
2. choose expiration, 
3. select DISHDevEx as Resource owner, 
4. write reason for needing access,
5. select 'Only select repositories',
6. select 'DISHDevEx/openverso-charts' from the drop down,
7. in Repository permissions, select 'Read and write' for Contents permissions,
8. Select 'Generate token and request access'

Copy the token string and save it as an environment variable in your local environment under the name TOKEN

e.g.:
```bash
export TOKEN='<token_string>'
echo $TOKEN
```
Navigate to the respons_ml folder and enter the Python interactive shell by running the command 'python'.

Copy the following commands line-by-line, updating values between <> characters (remove the angle brackets prior to running) as needed.


```Python
import action_handler
import os

requested_actions = {
'target_pod' : 'amf',
'requests' : {'memory' : <3>, 'cpu' : <1>},
'limits' : {'memory' : <1>, 'cpu' : <3>}
}

token = os.environ['TOKEN']
filepath = <'DISHDevEx/openverso-charts/charts/respons/tomer_test_PR.txt'>
repo_branch = <'matt/gh_api_test'>

hndl = action_handler.ActionHandler(repo_branch, filepath, repo_branch, requested_actions)
hndl.establish_github_connection()
hndl.fetch_update_push()
```

You should see the following output:
```Python
Attempting fetch of contents from test/test.txt:
Fetch successful.
Updating YAML values:
Update complete.
Attempting push to test/test.txt:
Push complete.
```

Now, if you check your file in the remote repo, you should see a new commit and updated values.