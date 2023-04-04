# Preliminary Test Procedure

To test the action handler manually, the following actions can be taken:

Log in to GitHub and create a new token:
Account page -> Settings -> Developer settings -> Personal access tokens -> Tokens (classic)

Select "Generate new token (classic)", give it a name, choose expiration, and select 'repo' for scope.

Copy the token string and save it as an environment variable in your local environment under the name TOKEN

e.g.:
```bash
export TOKEN='<token_string>'
echo $TOKEN
```
Navigate to the respons_ml folder and enter the Python interactive shell by running the command 'python'

Run the following code within the python shell (replace the PaperArmada GitHub path / branch name with your own):

```Python
>>> import action_handler
>>> import os
>>> requested_actions = {
... 'target_pod' : 'amf',
... 'requests' : {'memory' : 3, 'cpu' : 1},
... 'limits' : {'memory' : 1, 'cpu' : 3}
... }
>>> hndl = action_handler.ActionHandler(os.environ['TOKEN'], '<PaperArmada/hello-world/test/test.txt>', 'master', requested_actions)
>>> hndl.establish_github_connection()
>>> hndl.fetch_update_push()
Attempting fetch of contents from test/test.txt:
Fetch successful.
Updating YAML values:
Update complete.
Attempting push to test/test.txt:
Push complete.
```