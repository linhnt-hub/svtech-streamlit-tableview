# from tkinter import N
import streamlit as st
# import pandas as pd
# import numpy as np
import yaml
import os, sys
from git import Repo
import git
# import json
from github import Github # pip install PyGithub
import requests # pip install requests
import logging
sys.path.insert(0, '/opt/SVTECH-Junos-Automation/module_utils')

from BASE_FUNC import *
from PYEZ_BASE_FUNC import *
from NETWORK_FUNC import *

from streamlit.runtime.scriptrunner.script_run_context  import SCRIPT_RUN_CONTEXT_ATTR_NAME
from threading import current_thread
from contextlib import contextmanager
from io import StringIO


@contextmanager
def st_redirect(src, dst, dst_container):
    '''
    src: the data to be displayed on streamlit container, we will sepcify either sys.stdout or sys.stderr obj here
    dst: the streamlit container type to store the src data (text box, code, header whatever)
    dst_container: the streamlit larger container to help navigate to the container that store the src data (tab,sidebar..etc..)
    '''
    placeholder = dst_container.empty()
    output_func = getattr(placeholder, dst)

    with StringIO() as buffer:
        old_write = src.write

        def new_write(b):
            if getattr(current_thread(), SCRIPT_RUN_CONTEXT_ATTR_NAME, None):
                buffer.write('{} \r\n'.format(b))
                output_func(buffer.getvalue() + '')
            else:
                old_write(b)

        try:
            src.write = new_write
            yield
        finally:
            src.write = old_write

@contextmanager
def st_stdout(dst,dst_container):
    with st_redirect(sys.stdout, dst,dst_container):
        yield

@contextmanager
def st_stderr(dst,dst_container):
    with st_redirect(sys.stderr, dst,dst_container):
        yield
## read file yaml config
def read_config_yaml(file_path):
    with open(file_path, 'r') as yaml_file:
        config_data = yaml.safe_load(yaml_file)
        return config_data

file_path='/home/juniper/svtech-streamlit-tableview/web-app/default_variable.yml'    
config= read_config_yaml(file_path)

 ## create git(add/commit/push) 
def gitCommit(file_commit, commit_message, repo_path = config.get('config_git', {}).get('repo_path'), remote = config.get('config_git', {}).get('remote'), branch_name = config.get('config_git', {}).get('branch_name')):
    repo = Repo(repo_path)
    print(f"repo is {repo}")
    ## git switch 
    try:
      repo.git.switch(branch_name)
      print(f"Switched to branch {branch_name}.")
    except Exception as e:
      logging.exception('Switched to branch failed due to {}'.format(e))
      sys.exit()
    ## git stash
    try:
      repo.git.stash('save', '-u')
      print("Stashed changes successfully")
    except Exception as e:
      logging.exception('Create stash failed due to {}'.format(e))
      sys.exit()
    ## git pull
    try:  
      repo.remotes[remote].pull(branch_name)
      print(f"Pulled changes from {remote}/{branch_name}.")
    except Exception as e:
      logging.exception('Pull changes from github failed due to {}'.format(e))
      sys.exit()   
    ## git stash apply
    try:
      repo.git.stash('apply')
      print("Applied the latest stash successfully.")
    except Exception as e:
      logging.exception('Applied the latest stash failed due to {}'.format(e))
      sys.exit()
    ## git add  
    try:
      repo.index.add(file_commit)
      print("Git add successful.")
    except Exception as e:
      logging.exception('Git add failed due to {}'.format(e))
      sys.exit()
    ## git commit 
    try:
      repo.index.commit(commit_message)
      print("Git commit successful.")
    except Exception as e:
      logging.exception('Git commit failed due to {}'.format(e))
      sys.exit()        
    ## git push 
    try:
      repo.git.push(remote, branch_name)
      print(f"Pushed to {remote}/{branch_name} successfully.")
    except Exception as e:
      logging.exception('Git push failed due to {}'.format(e))
      sys.exit()     

  ## check pull request and create git pull request to master branch
def gitpr(title, body, repo_path = config.get('config_git', {}).get('repo_path'), base_branch = config.get('config_git', {}).get('base_branch'), branch_name = config.get('config_git', {}).get('branch_name'), repo = config.get('config_git', {}).get('repo'), owner = config.get('config_git', {}).get('owner'), token_git = config.get('config_git', {}).get('token_git')):
    base_url = f'https://api.github.com/repos/{owner}/{repo}/pulls'
    params = {'head': f'{owner}:{branch_name}'}

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        pull_requests = response.json()
        if pull_requests:
            print(f"Pull request already exists for {owner}:{branch_name}.")
            return True
        else:
            print(f"No existing pull request for {owner}:{branch_name}.")
            repo = git.Repo(repo_path)
            repo.git.push("--set-upstream", "origin", branch_name)

            github_token = token_git  
            g = Github(github_token)  
            user = g.get_user()
            repo_name = repo.remotes.origin.url.split('/')[-1][:-4]
            repository = user.get_repo(repo_name)
            pull_request = repository.create_pull(
                title=title,
                body=body,
                base=base_branch,
                head=branch_name
            )
            print(f"Pull Request: {pull_request.html_url}")
    else:
        print(f"Failed to fetch pull requests. Status code: {response.status_code}")
        return False
