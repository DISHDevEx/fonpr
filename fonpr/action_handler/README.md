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

**To create your new token**

1. Select "Generate new token" (ensure that it is a fine-grained token, not classic). 
2. Give it a name (e.g. '<repo_name>_access_token'). 
3. Choose expiration. 
4. Select DISHDevEx as Resource owner. 
5. Write reason for needing access (e.g. 'automation development work'; this is for repo owner approval, fit appropriately to your needs).
6. Select 'Only select repositories'.
7. Select 'DISHDevEx/openverso-charts' from the drop down.
8. In 'Repository permissions', select 'Read and write' for 'Contents' permissions.
9. Select 'Generate token and request access'.

Copy the token string and save it as an environment variable in your local environment under the name TOKEN

e.g.:
```bash
export TOKEN='<token_string>'
echo $TOKEN
```
After receiving approval from the repo owner (Org admin), navigate to the respons_ml folder and enter the Python interactive shell by running the command `python`.

Copy the following commands line-by-line, updating values between `<>` characters (remove the angle brackets prior to running) as needed.


```Python
import action_handler
import os

requested_actions = {
    'target_pod' : 'amf',
    'requests' : {'memory' : <3>, 'cpu' : <1>},
    'limits' : {'memory' : <1>, 'cpu' : <3>}
}

token = os.environ['TOKEN']
gh_url = <'https://github.com/DISHDevEx/openverso-charts/blob/matt/gh_api_test/charts/respons/test.yaml'>
dir_name = <'charts'>

hndl = action_handler.ActionHandler(token, gh_url, dir_name, requested_actions)
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