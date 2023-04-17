"""
Module to contain action-handler helpers for updating GitHub repositories programatically.
"""

import github
from github import Github
import os
import yaml
import copy
import boto3
import json
import logging
from botocore.exceptions import ClientError


class ActionHandler:
    """
    Helper for fetching a current value.yaml file, updating that file with
    actions requested by an agent, and pushing those updates back to the repo.

    Attributes
    ----------
        repo_token : str
            session token that contains the appropriate GitHub credentials
        repo_name : str
            target GitHub repository (e.g. 'DISHDevEx/response-ml')
        branch_name : str
            target branch to pull from and push to (e.g. 'matt/gh_api_test')
        value_file_dir : str
            directory holding target value.yaml file (e.g. 'charts/respons')
        value_file_name : str
            name of target value.yaml file (e.g. '5gSA_no_ues_values.yaml')
        requested_actions : dict
            dictionary containing value updates for the YAML file
            e.g.:
                requested_actions = {
                    'target_pod' : 'amf',
                    'requests' : {'memory' : 1, 'cpu' : 1},
                    'limits' : {'memory' : 1,'cpu' : 1},
                }
    Methods
    -------
        set_token(token:str):

        get_repo_name():

        set_repo_name(repo_name:str):

        get_branch_name():

        set_branch_name(branch_name:str):

        get_value_file_dir():

        set_value_file_dir(value_file_dir:str):

        get_value_file_name():

        set_value_file_name(value_file_name:str):

        get_requested_actions():

        set_requested_actions(requested_actions:dict):

        establish_github_connection():
            Instantiate access to Github API v3 wih token.

        list_repos():
            List repos from current session;
            establish_github_connection must be called prior to use.

        get_value_file_contents():
            Connect to target repository, set repo object as attribute,
            and fetch the specified file as a dictionary. Retain file hash as
            attribute for future push operations.

            establish_github_connection must be called prior to use.

        get_updated_value_file(current_values:dict):
            Update dictionary values with requested actions,
            and return in YAML file format.

        push_to_repository(updated_file:yaml.YAMLObject, message='auto-update'):
            Using connection to target repository, push the supplied updated file
            back out to GitHub,

            get_value_file_contents must be called prior to use.

        fetch_update_push():
            Execute complete file update process with a single command.
    """
    
    def __init__(self, 
        repo_token='', 
        value_file_url='', 
        dir_name='',
        requested_actions={}
        ):
        """
        Contstructor for the action-handler helper.

        Parameters
        ----------
            repo_token : str
                session token that contains the appropriate GitHub credentials
                prod handling of credentials is yet to be implemented
            value_file_url : str
                url to target value.yaml file
                (e.g. 'https://github.com/DISHDevEx/openverso-charts/blob/matt/gh_api_test/charts/respons/5gSA_no_ues_values.yaml')
            dir_name : str
                root directory within the repo (e.g. 'charts')
            requested_actions : dict
                dictionary containing value updates for the YAML file
                (e.g.:
                    requested_actions = {
                        'target_pod' : 'amf',
                        'requests' : {'memory' : 1, 'cpu' : 1},
                        'limits' : {'memory' : 1,'cpu' : 1},
                    })
        """

        self.repo_token = repo_token
        
        if value_file_url != '':
            try:
                # parse url to structure repo path for GitHub API
                split_path = value_file_url.split('/')
                blob_index = split_path.index('blob')
                dir_index = split_path.index(dir_name)
                
                self.repo_name = '/'.join(split_path[3:blob_index])
                self.value_file_dir = '/'.join(split_path[dir_index:-1])
                self.value_file_name = split_path[-1]
                self.branch_name = '/'.join(split_path[blob_index+1:dir_index])
            except Exception as excp:
                logging.error(f'Failed to build object instance with the following exception: {excp}')
        else:
            self.repo_name = ''
            self.value_file_dir = ''
            self.value_file_name = ''
            
        self.requested_actions = requested_actions

        self.session = self.establish_github_connection()

    def set_token(self, token: str) -> None:
        # TODO: This method needs to be updated with prod credential handling
        self.repo_token = token

    def get_repo_name(self) -> str:
        return self.repo_name

    def set_repo_name(self, repo_name: str) -> None:
        self.repo_name = repo_name

    def get_branch_name(self) -> str:
        return self.branch_name

    def set_branch_name(self, branch_name: str) -> None:
        self.branch_name = branch_name

    def get_value_file_dir(self) -> str:
        return self.value_file_dir

    def set_value_file_dir(self, value_file_dir: str) -> None:
        self.value_file_dir = value_file_dir

    def get_value_file_name(self) -> str:
        return self.value_file_name

    def set_value_file_name(self, value_file_name: str) -> None:
        self.value_file_name = value_file_name

    def get_requested_actions(self) -> dict:
        return self.requested_actions

    def set_requested_actions(self, requested_actions: dict) -> None:
        self.requested_actions = requested_actions

    def establish_github_connection(self) -> github.MainClass.Github:
        """
        Instantiate access to Github API v3 wih token.

        Parameters
        ---------
            None

        Returns
        -------
            None
        """
        return Github(self.repo_token)

    def list_repos(self) -> [str]:
        """
        List repos from current session;
        establish_github_connection must be called prior to use.

        Parameters
        ---------
            None

        Returns
        -------
            repos : list of strings
                List of all repo names associated with the token account.
        """
        try:
            repos = [repo.name for repo in self.session.get_user().get_repos()]
            return repos
        except NameError as excp:
            logging.error(f"{excp}: GitHub connection not yet established.")
        except Exception as excp:
            logging.error(f"The following exception occurred while trying to fetch repo names: {excp}")
            
    def get_value_file_contents(self) -> dict:
        """
        Connect to target repository, set repo object as attribute,
        and fetch the specified file as a dictionary. Retain file hash as
        attribute for future push operations.

        establish_github_connection must be called prior to use.

        Parameters
        ---------
            None

        Returns
        -------
            contents : dict
                Dictionary representation of existing target YAML file contents.
        """
        try:
            logging.info(f'Attempting fetch of contents from {self.value_file_dir}/{self.value_file_name}:')
            # Fetch contents
            self.repo = self.session.get_repo(self.repo_name)
            response = self.repo.get_contents(
                f"{self.value_file_dir}/{self.value_file_name}", ref=self.branch_name
            )

            # Collect and retain file hash for push operation
            self.response_sha = response.sha
            logging.info('Fetch successful.')
            contents = yaml.safe_load(response.decoded_content)
            return contents

        except Exception as excp:
            logging.error(f'Failed to fetch file with the following exception: {excp}')
            
    def get_updated_value_file(self, current_values:dict) -> yaml.YAMLObject:
        """
        Update dictionary values with requested actions, and return in YAML file format.

        Parameters
        ---------
            current_values : dict
                The dictionary representation of the target file fetched from GitHub

        Returns
        -------
            updated_yaml : YAML Object
                Target file containing updated values, output in YAML format.
        """
        try:
            # TODO: Automate key-value population based on requested_actions dict
            logging.info('Updating YAML values:')
            new_values = copy.deepcopy(current_values)
            new_values[self.requested_actions["target_pod"]]["resources"] = {
                "requests": self.requested_actions["requests"],
                "limits": self.requested_actions["limits"],
            }
            logging.info('Update complete.')
            updated_yaml = yaml.dump(new_values)
            return updated_yaml

        except Exception as excp:
            logging.error(f'Failed to update target values with the following exception: {excp}')
            
    def push_to_repository(self, updated_file:yaml.YAMLObject, message='auto-update') -> None:
        """
        Using connection to target repository, push the supplied updated file
        back out to GitHub,

        get_value_file_contents must be called prior to use.

        Parameters
        ---------
            updated_yaml : YAML Object
                Target file containing updated values, output in YAML format.

            message : str
                Commit message to be included with the push event.

        Returns
        -------
            None
        """
        try:
            logging.info(f'Attempting push to {self.value_file_dir}/{self.value_file_name}:')
            self.repo.update_file(
                path=f"{self.value_file_dir}/{self.value_file_name}",
                message=message,
                content=updated_file,
                sha=self.response_sha,
                branch=self.branch_name,
            )
            logging.info('Push complete.')
        except Exception as excp:
            logging.error(f'Failed to push to repo with the following exception: {excp}')
            
    def fetch_update_push(self) -> None:
        """
        Execute complete file update process with a single command.

        Parameters
        ---------
            None

        Returns
        -------
            None
        """
        current_values = self.get_value_file_contents()
        updated_file = self.get_updated_value_file(current_values)
        self.push_to_repository(updated_file)


def get_token(token_key="token") -> str:
    """
    Fetch and return token string for GitHub API access from AWS Secrets Manager.

    Parameters
    ---------
        token_key : str
            Key name for target secret

    Returns
    -------
        token : str
            Secret token string
    """

    secret_name = "RESPONS/DISHDevEx/openverso-charts/rw"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    # Decrypts secret using the associated KMS key.
    secret = get_secret_value_response["SecretString"]

    token = json.loads(secret)[token_key]
    return token
