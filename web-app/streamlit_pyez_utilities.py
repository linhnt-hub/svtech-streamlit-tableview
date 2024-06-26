import os
import sys 
import yaml
import logging
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.append('../../')
sys.path.append('../../module_utils/')
from module_utils import BASE_FUNC
from module_utils import PYEZ_BASE_FUNC
from module_utils import NETWORK_FUNC

from streamlit.runtime.scriptrunner.script_run_context  import SCRIPT_RUN_CONTEXT_ATTR_NAME
from threading import current_thread
from contextlib import contextmanager
from io import StringIO
import nt
from git import Repo
import git
import subprocess
from github import Github # pip install PyGithub
import requests # pip install requests

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
    
# if "VAR_PATH" in os.environ:
file_path= os.environ['VAR_PATH']
print(f"VAR_PATH IS {file_path}")
# else:
#    print("ENV does not exist, using path default /root/svtech-streamlit-tableview/web-app/default_variable.yml")
#    file_path='/opt/SVTECH-Junos-Automation/Python-Development/streamlit_apps/default_variable.yml'    

config=read_config_yaml(file_path)

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
      repo.git.stash('save')
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
      # repo.index.add(file_commit)
      subprocess.run(['git', 'add', file_commit], cwd=repo_path)
      print("Git add successful.")
    except Exception as e:
      print("An exception occurred: %s" %e)
      sys.exit()
    ## git commit 
    try:
      # repo.index.commit(commit_message)
      subprocess.run(['git', 'commit' , '-m', commit_message], cwd=repo_path)
      print("Git commit successful.")
    except Exception as e:
      logging.exception('Git commit failed due to {}'.format(e))
      sys.exit()        
    ## git push 
    try:
      # repo.git.push(remote, branch_name)
      subprocess.run(["git", "push"], cwd=repo_path)
      print(f"Pushed to {remote}/{branch_name} successfully.")
    except Exception as e:
      logging.exception('Git push failed due to {}'.format(e))
      sys.exit()     

  ## check pull request and create git pull request to master branch
def gitpr(title, body, repo_path = config.get('config_git', {}).get('repo_path'), base_branch = config.get('config_git', {}).get('base_branch'), branch_name = config.get('config_git', {}).get('branch_name'), repo = config.get('config_git', {}).get('repo'), owner = config.get('config_git', {}).get('owner'), token_git = config.get('config_git', {}).get('token_git')):
    base_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    headers = {
        "Authorization": f"token {token_git}",
        "Accept": "application/vnd.github.v3+json",  # Use GitHub API v3
    } 
    response = requests.get(base_url, headers=headers)
    if response.status_code == 200:
        pull_requests = response.json()      
        total_pr=len(pull_requests)
        if pull_requests:
          for pr in pull_requests:
              source_branch = pr['head']['ref']  
              print(f"Pull Request #{pr['number']}: Source Branch: {source_branch}")
              if source_branch == branch_name:
                 print(f"Pull request already exists for {owner}:{branch_name}.")
                 return True
              else:
                # if total_pr == 2:
                #   print("Two PRs already exist on the repo")
                #   return True
                # else:
                print(f"No existing pull request for {owner}:{branch_name}.")
                data = {
                  'title': title,
                  'body': body,
                  'head': branch_name,
                  'base': base_branch,
                }
                response = requests.post(base_url,headers=headers,json=data)
                if response.status_code == 201:
                    print("Pull request created successfully.")
                    pull_request_info = response.json()
                    print(f"Pull Request URL: {pull_request_info['html_url']}")
                else:
                    print(f"Failed to create pull request. Status code: {response.status_code}")
                    print(f"Error message: {response.text}")
    else:
        print(f"Failed to fetch pull requests. Status code: {response.status_code}")
        return False
############### XML Function######################
# [linhnt] add March 2024

from lxml import etree
def evaluate_xpath(xml_content, xpath_expression):
    try:
        # Parse the XML content
        root = etree.fromstring(xml_content)
        # Use XPath to evaluate the expression
        result = root.xpath(xpath_expression)

        return result
    except etree.XPathError as e:
        return f"XPathError: {e}"
def check_xpath_syntax(xpath_expression):
    try:
        # Attempt to create an XPath object with the given expression
        etree.XPath(xpath_expression)
        return True, None
    except etree.XPathSyntaxError as e:
        return False, str(e)
def remove_xml_namespaces(input_xml):
    root = etree.fromstring(input_xml)
    # Iterate through all XML elements
    for elem in root.getiterator():
        # Skip comments and processing instructions,
        # because they do not have names
        if not (
            isinstance(elem, etree._Comment)
            or isinstance(elem, etree._ProcessingInstruction)
        ):
            # Remove a namespace URI in the element's name
            elem.tag = etree.QName(elem).localname
    # Remove unused namespace declarations
    etree.cleanup_namespaces(root)
    return etree.tostring(root).decode()
def convert_xml_pretty(element):
    from lxml import etree
    import xml.etree.ElementTree as et
    import xml.dom.minidom
    try: 
      xml_minidom = xml.dom.minidom.parseString(etree.tostring(element))
      xml_pretty = xml_minidom.toprettyxml()
    except Exception as e:
      print(f"Element Parse Fail. Error: {e}")
    return xml_pretty

############### Get XML from host/list_host Function######################
# [linhnt] add March 2024

def get_xml_obj(host, username, password, command):
  """ 
  host: string (ip /32)
  username: string
  password: string
  command: string
  """
  from jnpr.junos import Device
  try:
    # Connect to the Junos device
    dev = Device(host=host, user=username, password=password, normalize=True)
    dev.open()
    # Execute the command and get the XML response
    try:
      rpc_cmd = dev.display_xml_rpc(command, format= 'xml').tag.replace("-", "_")
      xml_obj= eval("dev.rpc.{}(normalize=True)".format(rpc_cmd))
      return rpc_cmd, xml_obj #return rpc_name, xml object
    except Exception as e:
      print(f"Can't get rpc, xml value. Check command Error: {e}")
  except Exception as e:
    print(f"Check ip/username/password. Error: {e}")
  finally:
    # Close the connection
    dev.close()

def get_dict_xml_obj(host, username, password, command):
  """ 
  host: list (ip subnet)
  username: string
  password: string
  command: string
  """
  from jnpr.junos import Device
  rpc_cmd=""
  dict_xml_obj={}
  if isinstance(host, list):
    for ip in host:
      try:
        # Connect to the Junos device
        dev = Device(host=ip, user=username, password=password, normalize=True)
        dev.open()
        # Execute the command and get the XML response
        try:
          rpc_cmd = dev.display_xml_rpc(command, format= 'xml').tag.replace("-", "_")
          xml_obj= eval("dev.rpc.{}(normalize=True)".format(rpc_cmd))
          dict_xml_obj.update({ip : xml_obj})
          # Close the connection
          dev.close()
        except Exception as e:
          print(f"Can't get rpc, xml value. Check command Error: {e}")
      except Exception as e:
        print(f"Check ip/username/password. Error: {e}")
    return rpc_cmd, dict_xml_obj #return rpc_cmd and dict of xml_obj ({ip : xml_obj})
  else: 
    print(f"Host isn't list")

############### Streamlit front-end component login######################
# [linhnt] add March 2024

def component_login():
    import streamlit as st
    user= st.text_input(':orange[Your username:] ', placeholder = 'Typing user')
    passwd= st.text_input(':orange[Your password:] ', type= 'password', placeholder = 'Typing password')
    ip = st.text_input(':orange[Your router IP:] ', placeholder = 'Typing IP\'s device')
    return user, passwd, ip
############### Streamlit juniper_component_login######################
# [linhnt] add April 2024
sys.path.insert(0, config.get('path_junos_tableview', {}).get('path_module_utils'))
from NETWORK_FUNC import *
def juniper_component_login():
    import streamlit as st
    from jnpr.junos import Device
    list_device_dict=[] # save list of device dict
    list_ip=[] # save list IP
    input_dict={} # Save host, user, password
    usable_input_option = ['host', 'user','passwd'] # Input from dir(Device)
    # ip_input = st.text_input(':orange[Your IP subnet:] ', placeholder = 'Typing IP\'s device')
    #for item in dir(Device):
    for item in ["host", "user", "passwd", "port", "gather_facts", "mode", "auto_probe", "normalize", "conn_open_timeout"]:
        if item in usable_input_option:
            if item == 'passwd':
                input_dict[item] = st.text_input(':orange[Your %s:]'%item, placeholder = 'Please input {}'.format(item), type= 'password')
            else:
                input_dict[item] = st.text_input(':orange[Your %s:]'%item, placeholder = 'Please input {}'.format(item))
    # {host = x, user = y, pass  = z }
    try:
      list_ip = GET_ALIVE_HOST(input_dict['host'])
    except Exception as e:
      print(f"Check GET_ALIVE_HOST . Check command Error: {e}")
    if isinstance(list_ip, list):
      for ip in list_ip:
        try:
          device_dict = {}
          # Connect to the Junos device
          dev = Device(host=ip, user= input_dict.get('user'), password=input_dict.get('passwd'))
          dev.open()
          device_dict.update({'ip':ip})
          device_dict.update({'user':input_dict.get('user')})
          device_dict.update({'obj':dev})
          dev.close()
          list_device_dict.append(device_dict)
        except Exception as e:
          print(f"Check username/password. Error: {e}")
    else:
        print(f"Don't have alive host")
    return list_device_dict