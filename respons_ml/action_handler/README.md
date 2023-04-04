# Preliminary Test Procedure

To test the action handler manually, the following actions can be taken:

Log in to GitHub and create a new token:
<<<<<<< HEAD
Account page -> Settings -> Developer settings -> Personal access tokens -> Fine-grained tokens

Select "Generate new token": 
* give it a name, 
* choose expiration, 
* select DISHDevEx as Resource owner, 
* write reason for needing access,
* select 'Only select repositories',
* select 'DISHDevEx/openverso-charts' from the drop down,
* in Repository permissions, select 'Read and write' for Contents permissions,
* Select 'Generate token and request access'
=======
Account page -> Settings -> Developer settings -> Personal access tokens -> Tokens (classic)

Select "Generate new token (classic)", give it a name, choose expiration, and select 'repo' for scope.
>>>>>>> 9a83522 (Added readme with manual test instructions for the action handler)

Copy the token string and save it as an environment variable in your local environment under the name TOKEN

e.g.:
```bash
export TOKEN='<token_string>'
echo $TOKEN
```
Navigate to the respons_ml folder and enter the Python interactive shell by running the command 'python'

<<<<<<< HEAD
<<<<<<< HEAD
Copy the file found at PaperArmada/hello-world/test/test.txt and paste it into your own GitHub directory for testing.

Run the following code within the python shell (you can update values for requests and limits as desired to see effect):
=======
=======
Copy the file found at PaperArmada/hello-world/test/test.txt and paste it into your own GitHub directory for testing.

>>>>>>> 1299c76 (Updated main readme.)
Run the following code within the python shell (replace the PaperArmada GitHub path / branch name with your own):
>>>>>>> 9a83522 (Added readme with manual test instructions for the action handler)

```Python
>>> import action_handler
>>> import os
>>> requested_actions = {
... 'target_pod' : 'amf',
... 'requests' : {'memory' : 3, 'cpu' : 1},
... 'limits' : {'memory' : 1, 'cpu' : 3}
... }
<<<<<<< HEAD
>>> hndl = action_handler.ActionHandler(os.environ['TOKEN'], <'DISHDevEx/openverso-charts/charts/respons/test.txt'>, 'matt/gh_api_test', requested_actions)
=======
>>> hndl = action_handler.ActionHandler(os.environ['TOKEN'], '<PaperArmada/hello-world/test/test.txt>', 'master', requested_actions)
>>>>>>> 9a83522 (Added readme with manual test instructions for the action handler)
>>> hndl.establish_github_connection()
>>> hndl.fetch_update_push()
Attempting fetch of contents from test/test.txt:
Fetch successful.
Updating YAML values:
Update complete.
Attempting push to test/test.txt:
Push complete.
```