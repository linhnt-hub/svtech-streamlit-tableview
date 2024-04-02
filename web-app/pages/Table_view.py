import streamlit as st
from streamlit_ace import st_ace
import pandas as pd # Data Frame
import numpy as np
import json # Json format
import os, sys, logging
sys.path.append('../')
from streamlit_pyez_utilities import * #Lib for stdout,stderr, gitcommit, gitpr
sys.path.append('../device_config_processing/classes')
from textprocessing import *
from pathlib import Path 
import time # Time
from datetime import datetime, timezone, timedelta # Datetime

import re
from PIL import Image
from yamllint import linter # Lib for check yaml grammar
from yamllint.config import YamlLintConfig # Lib for check yaml grammar

from jnpr.junos import Device # Lib for connect to Router
from jnpr.junos.factory.factory_loader import FactoryLoader
import yaml # Yaml format
from lxml import etree
import xml.etree.ElementTree as et
import xml.dom.minidom

import tarfile
import zipfile
import rarfile
from io import BytesIO
import base64
import io
import uuid

#sudo apt install unrar
def download_file_button(object_to_download, download_filename, button_text, pickle_it=False):
    """
    Generates a link to download the given object_to_download.
    Params:
    ------
    object_to_download:  The object to be downloaded.
    download_filename (str): filename and extension of file. e.g. mydata.csv,
    some_txt_output.txt download_link_text (str): Text to display for download
    link.
    button_text (str): Text to display on download button (e.g. 'click here to download file')
    pickle_it (bool): If True, pickle file.
    Returns:
    -------
    (str): the anchor tag to download object_to_download
    Examples:
    --------
    download_link(your_df, 'YOUR_DF.csv', 'Click to download data!')
    download_link(your_str, 'YOUR_STRING.txt', 'Click to download text!')
    """
    if pickle_it:
        try:
            object_to_download = pickle.dumps(object_to_download)
        except pickle.PicklingError as e:
            st.write(e)
            return None
    else:
        if isinstance(object_to_download, bytes):
            pass

        elif isinstance(object_to_download, pd.DataFrame):
            object_to_download = object_to_download.to_csv(index=False)
        else:
            object_to_download = json.dumps(object_to_download)
    try:
        b64 = base64.b64encode(object_to_download.encode()).decode()
    except AttributeError as e:
        b64 = base64.b64encode(object_to_download).decode()

    button_uuid = str(uuid.uuid4()).replace('-', '')
    button_id = re.sub('\d+', '', button_uuid)

    custom_css = f""" 
        <style>
            #{button_id} {{
                background-color: rgb(255, 255, 255);
                color: rgb(38, 39, 48);
                padding: 0.25em 0.38em;
                position: relative;
                text-decoration: none;
                border-radius: 4px;
                border-width: 1px;
                border-style: solid;
                border-color: rgb(230, 234, 241);
                border-image: initial;
            }} 
            #{button_id}:hover {{
                border-color: rgb(246, 51, 102);
                color: rgb(246, 51, 102);
            }}
            #{button_id}:active {{
                box-shadow: none;
                background-color: rgb(246, 51, 102);
                color: white;
                }}
        </style> """

    dl_link = custom_css + f'<a download="{download_filename}" id="{button_id}" href="data:file/txt;base64,{b64}">{button_text}</a><br></br>'

    return dl_link
def extract_tar(data, output_dir):
    with tarfile.open(fileobj=BytesIO(data), mode='r') as tar:
        tar.extractall(output_dir)

def extract_tar_gz(data, output_dir):
    with tarfile.open(fileobj=BytesIO(data), mode='r:gz') as tar_gz:
        tar_gz.extractall(output_dir)

def extract_zip(data, output_dir):
    with zipfile.ZipFile(BytesIO(data), 'r') as zip_file:
        zip_file.extractall(output_dir)

def extract_rar(data, output_dir):
    with rarfile.RarFile(BytesIO(data), 'r') as rar:
        rar.extractall(output_dir)
        
############### Page style ##################
st.set_page_config(layout="wide", page_icon="✨")
font_css = """
<style>
button[data-baseweb="tab"] > div[data-testid="stMarkdownContainer"] > p {
  font-size: 18px;
}
</style>
"""
st.write(font_css, unsafe_allow_html=True)
################################################################

sys.path.insert(0, config.get('path_junos_tableview', {}).get('path_module_utils'))
from PYEZ_BASE_FUNC import PYEZ_TABLEVIEW_TO_DATAFRAME
from PYEZ_BASE_FUNC import GET_PYEZ_TABLEVIEW_RAW
from PYEZ_BASE_FUNC import GET_PYEZ_TABLEVIEW
from PYEZ_BASE_FUNC import GET_TABLEVIEW_CATALOGUE
from PYEZ_BASE_FUNC import IMPORT_JUNOS_TABLE_VIEW
from BASE_FUNC import LOGGER_INIT
from NETWORK_FUNC import *
## EXPLAIN: setting shell_output = False will create a default log Streamhandler, which by default send all   all Python log to stderr
## then we send all console stdout to TerminalOutput tab
## all stderr data (which include formatted log) to the LogData tab
#LOGGER_INIT(log_level=logging.DEBUG, print_log_init = False, shell_output= False) 

########################### Varriable #########################                                                        
list_table_result=[] # Save list tables
list_view_result=[] # Save list views
dict_table_result={} # Save dict tables
dict_view_result={}  # Save dict views
yamllint_conf= config.get('yamllint', {}).get('config')

try:
  tableview_cat= GET_TABLEVIEW_CATALOGUE(config.get('path_junos_tableview', {}).get('path_table_view'))
  dict_table_result = {key: val for key, val in tableview_cat.items() if key.endswith("Table")}  # Get dict Table
  dict_view_result = {key: val for key, val in tableview_cat.items() if key.endswith("iew")}  # Get dict View
  list_table_result= list(dict_table_result.keys())
  list_view_result= list(dict_view_result.keys())
except Exception as e:
  print("[Call GET_TABLEVIEW_CATALOGUE] An exception occurred, check error %s" %e)

######################## Create session_state ################################
if 'test_table' not in st.session_state:
  st.session_state.test_table = True
  st.session_state.commit = True
  st.session_state.test_table_edit = True
  st.session_state.commit_edit = True
  st.session_state.commit_del_edit = True

######################## Parent TAB ##########################################
tab5, tab6, tab7 = st.tabs(["🔢 TABLES / VIEWS", "📩 TERMINAL LOG", "📞LOG DATA"])
with st_stdout("code",tab6), st_stderr("code",tab7):
  with tab5:
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["1️⃣ VIEW","2️⃣CREATE", "3️⃣ EDIT / TEST", "4️⃣OFFLINE DATA", "5️⃣RPC CHECK / XPATH TESTER"])
    ################# TAB1 ##########################################
    with tab1:
      st.subheader('1. Get Table/View By Selection')
      options = st.multiselect(':orange[Type or select for searching]',dict_table_result.keys(), placeholder = 'Select for view')
      for opt in options:
        print('[TAB1] You selected:[%s] with path [%s]' %(opt, dict_table_result.get(opt).get('dir')))
      dict_export_file={}  # Variable for export button
      if options:
        for option in options:
            dict_export_file[option]= dict_table_result.get(option).get('content')
            dict_export_file[dict_table_result.get(option).get('view')] = dict_view_result.get(dict_table_result.get(option).get('view')).get('content')
            with st.container(border = True) as container:
              col1, col2 = st.columns(2)
              with col1:
                  dict_temp1_tab1={}
                  container = st.container(border = True)
                  dict_temp1_tab1[option] = dict_table_result.get(option).get('content')
                  container.code(yaml.dump(dict_temp1_tab1, indent = 4), language = 'yaml', line_numbers= True) # Display dict by yaml format
              with col2:
                  dict_temp2_tab1={}
                  container = st.container(border = True)
                  dict_temp2_tab1[dict_table_result.get(option).get('content').get('view')] = dict_view_result.get(dict_table_result.get(option).get('content').get('view')).get('content')
                  container.code(yaml.dump(dict_temp2_tab1, indent = 4), language = 'yaml', line_numbers= True)
      with st.container(border = True) as container:
        col3, col4 = st.columns([9,1])
        with col3:
          st.write("*Use beside button for exporting your selection ...*")
        with col4:
          # Export button
          st.download_button('Export', "---"+"\n"+ yaml.dump(dict_export_file, indent = 4, encoding= None), key= '1')
      if options:
        with st.expander(":green[Expand for getting Data from Router]"):
          with st.form("form10"):
            user, passwd, router = component_login()
            tab1_list_host= GET_ALIVE_HOST(router)
            print("[TAB1] List host %s"%tab1_list_host)
            submitted = st.form_submit_button(label= "Run")
            if submitted:
              with st.spinner('Wait for it...'):
                try:
                  for ip in tab1_list_host:
                    with Device(host=ip, user= user, password= passwd) as dev:
                      print('[TAB1] Get multiple table/view data')
                      try:
                        for option in options:
                          table_object = GET_PYEZ_TABLEVIEW(dev= dev, data_type = option[:-5])
                          table_object.get()
                          dataframe= PYEZ_TABLEVIEW_TO_DATAFRAME(dev= dev, tableview_obj= table_object)
                          with st.container(border= True):                 
                            st.success('''
                            Get table **%s** successfully from **%s** \n
                            '''%(option,ip))
                            st.dataframe(dataframe)
                        dev.close()
                      except Exception as e:
                          st.error(
                          """
                          - Can't get data by table/view. Review table/view
                          """)
                          print("[TAB1] Check exception %s"%e)
                except Exception as e:
                  st.error(
                    """
                    - Check Your Username/Password\n
                    - Check connection to Router (Or no router available)
                    """
                    )
                  print('[TAB1] Check exception %s'%e)
      #############Search table by key###########################
      st.subheader('2. Get List Table/View By Keywork')
      option_fil=[]
      kw= st.text_input(':orange[Type your keyword:]', placeholder = 'Your keyword with case-insensitive')
      #option_fil = {val for val in list_table_result if val.endswith("%s"%kw)}
      if kw:
        print('[TAB1] Search by key: %s'%kw)
        for i in range(len(list_table_result)):
            x= re.search(kw,list_table_result[i],re.IGNORECASE)
            if x != None:
                option_fil.append(list_table_result[i])
      else:
        print('[TAB1] Key empty')
      for opt in option_fil:
        print('[TAB1] You selected:[%s] with path [%s]' %(opt, dict_table_result.get(opt).get('dir')))
      dict_export_file={}  # Variable for export button
      if option_fil:
        for option in option_fil:
            dict_export_file[option]= dict_table_result.get(option).get('content')
            dict_export_file[dict_table_result.get(option).get('view')] = dict_view_result.get(dict_table_result.get(option).get('view')).get('content')
            with st.expander(":green[%s]"%option):
              col1, col2 = st.columns(2)
              with col1:
                  dict_temp1_tab1={}
                  container = st.container(border = True)
                  dict_temp1_tab1[option] = dict_table_result.get(option).get('content')
                  container.code(yaml.dump(dict_temp1_tab1, indent = 4), language = 'yaml', line_numbers= True) # Display dict by yaml format
              with col2:
                  dict_temp2_tab1={}
                  container = st.container(border = True)
                  dict_temp2_tab1[dict_table_result.get(option).get('content').get('view')] = dict_view_result.get(dict_table_result.get(option).get('content').get('view')).get('content')
                  container.code(yaml.dump(dict_temp2_tab1, indent = 4), language = 'yaml', line_numbers= True)
      with st.container(border = True) as container:
        col3, col4 = st.columns([9,1])
        with col3:
          st.write("*Use beside button for exporting your selection ...*")
        with col4:
          # Export button
          st.download_button('Export', "---"+"\n"+ yaml.dump(dict_export_file, indent = 4, encoding= None), key= '2')
    ###################### TAB2 ################################
    with tab2:
      st.subheader('1. Create new Table/View ')
      with st.container(border = True):
        op = st.radio(
          ":orange[Choose your aim when you create tables/views : ]",
          ["*Option 1*", "*Option 2*", "*Option 3*", "*Option 4*", "*Option 5*", "*Option 6*"],
          captions = ["Extract :green[Protocols] (ARP, APS, BFD, BGP, OSPF, ISIS, RSVP, LDP, MPLS LSP, LLDP, PIM, Route ...) informations from Junos devices.", 
          "Extract :green[Hardware] ( Alarms, Enviroment, Craft-interface, Fabric, Fan, FPC, Hardware, Power, ...) informations from Junos devices.", 
          "Extract :green[System Operational] ( Alarms, Software, Connections, Storage, User, Snapshot, NTP, nonstop-routing... ) informations from Junos devices.",
          "Extract :green[Services State] ( BNG, l2circuit, l2vpn, l3vpn, mac-vrf, loop-detect, mvpn, network-access, , firewall, policer, snmp ...) informations from Junos devices.", 
          "Extract :green[Links State] (Interfaces, physical/logical, LACP, mpls interfaces, snmp ifl-index) informations from Junos devices.",
          "Retrieve :green[Configuration Data]."],
          index= None,
        )
        print('[TAB2] Option selected [%s]'%op)
      col1, col2 = st.columns(2)
      with col1:
        ############## TAB2 Table ####################################################
        with st.container(border = True):
          st.write(":orange[Add Table]  *YAML with Identation = 4*")
          add_table= st_ace(
            language= config.get('config_streamlit_ace', {}).get('language'), 
            theme= config.get('config_streamlit_ace', {}).get('theme'), 
            show_gutter= config.get('config_streamlit_ace', {}).get('show_gutter'), 
            keybinding=config.get('config_streamlit_ace', {}).get('keybinding') , 
            auto_update= config.get('config_streamlit_ace', {}).get('auto_update'), 
            placeholder= '* Compose your table structure*', 
            height= 300)
      with col2:
        ############## TAB2 View ####################################################
        with st.container(border = True):
          st.write(":orange[Add View]  *YAML with Identation = 4*")
          add_view= st_ace(
            language= config.get('config_streamlit_ace', {}).get('language'), 
            theme= config.get('config_streamlit_ace', {}).get('theme'), 
            show_gutter= config.get('config_streamlit_ace', {}).get('show_gutter'), 
            keybinding=config.get('config_streamlit_ace', {}).get('keybinding') , 
            auto_update= config.get('config_streamlit_ace', {}).get('auto_update'), 
            placeholder= '* Compose your view structure*', 
            height= 300)
      with st.container(border = True):
        if op:  # Check state of selecting
          if (add_table.find(':') != -1) and add_table.split(':')[0].endswith("Table") and (add_table.find("view") != -1) and (len(add_table.split(':')[0]) <= 31):
            print("[TAB2] Table must end with Table, must have view:, must have :, [PASS]")
            if list_table_result.count(add_table.split(':')[0]) == 0: # Check duplicate table Name
              print("[TAB2] Don't duplicate table name [PASS]")
              if (add_view.find(':') != -1) and add_view.split(':')[0].endswith("iew"):
                print("[TAB2] View must end with View/view, must have :[PASS]")
                if list_view_result.count(add_view.split(':')[0]) == 0: # Check duplicate view Name
                  print("[TAB2] Don't duplicate view name [PASS]")
                  if add_view.split(':')[0] == add_table.split(':')[-1].strip():  # Check table-view match with view, Need strip for remove space
                    print("[TAB2] Match Table/view and View [PASS]")
                    conf_ymllint = YamlLintConfig('extends: %s'%yamllint_conf) ### Modify file /home/juniper/.local/lib/python3.10/site-packages/yamllint/conf/relaxed.yaml
                    # Or /usr/local/lib/python3.10/dist-packages/yamllint/conf
                    error_table = linter.run(add_table , conf_ymllint)
                    error_view = linter.run(add_view , conf_ymllint)
                    list_err_table = list(error_table)
                    list_err_view = list(error_view)
                    if (len(list_err_table) + len(list_err_view)) != 0:
                      for i in range(len(list_err_table)):
                        str1= str(list_err_table[i]).split(':')
                        st.error(":red[Check [ Table ] line %s from character %s with *%s*]" %(str1[0], str1[1], str1[2]))
                        st.session_state.test_table = True
                        st.session_state.commit = True
                      for j in range(len(list_err_view)):
                        str2= str(list_err_view[j]).split(':')
                        st.error(":red[Check [ View ] line %s from character %s with *%s*]" %(str2[0],str2[1],str2[2]))
                        st.session_state.test_table = True
                        st.session_state.commit = True
                    else:
                      print('[TAB2] Check table/view syntax successfully')
                      st.info("""
                      :green[Check table/view syntax successfully]\n
                      :green[Use below for testing new table/view]
                      """)     # No Table/View syntax error
                      st.session_state.test_table = False
                      st.session_state.commit = True
                  else:
                    print('[TAB2] Dont match Table.view with View')
                    st.warning("""
                      :red[- Don't match ]
                      :orange[Table.view ]
                      :red[ with ]
                      :orange[ View ]
                      :red[ check it, plz ]
                      """
                      )
                    st.session_state.test_table = True
                    st.session_state.commit = True
                else:
                  print('[TAB2] Duplicate View Name')
                  st.warning("""
                    :red[- Duplicate ]
                    :orange[View]
                    :red[ Name. Choose other name, plz ]
                    """
                    )
                  st.session_state.test_table = True
                  st.session_state.commit = True
              else:
                print('[TAB2] Add/Check view content ')
                st.error("""
                  :red[- Add/Check ] 
                  :orange[View] 
                  :red[ content.]\n
                  :grey[*Note: view must have suffix \"view\" or \"View\"*]
                  """)
                st.session_state.test_table = True
                st.session_state.commit = True
            else:
              print('[TAB2] Duplicate Table Name')
              st.warning("""
                :red[- Duplicate ]
                :orange[Table]
                :red[ Name. Choose other name, plz ]
                """
                )
              st.session_state.test_table = True
              st.session_state.commit = True
          else:
              print('[TAB2] Add/Check table content ')
              st.error("""
                :red[- Add/Check ] 
                :orange[Table] 
                :red[ content.]
                \n
                :grey[*Length name table < 31 characters*]\n
                :grey[*Note: table must have suffix Table*]\n
                :grey[*Note: table must have \"view:\"*]
                """)
              st.session_state.test_table = True
              st.session_state.commit = True
        else:
          print('[TAB2] Select Option/Add table/Add view ')
          st.error(
            '''
            :red[Check one of below before create, please :]\n
            :red[- Choose one of five options.]\n
            :red[- Add table content.]\n
            :red[- Add view content.]
          ''')
          st.session_state.test_table = True
          st.session_state.commit = True
      st.subheader('2. Try your new table/view with your router')
      print('[TAB2] Test table/view with router')
      #############################TAB2 Form test table/view #####################################
      with st.form("form1"):
        user, passwd, router = component_login()
        tab2_list_host= GET_ALIVE_HOST(router)
        submitted = st.form_submit_button(label= "Run", disabled= st.session_state.test_table)
        if submitted:
          with st.spinner('Wait for it...'):
            # time.sleep(1)
            try:
              for ip in tab2_list_host:
                with Device(host=ip, user= user, password= passwd) as dev:
                  print('[TAB2] Are we connected?', dev.connected)
                  try:
                      myYAML="".join([add_table,"\n",add_view])
                      globals().update(FactoryLoader().load(yaml.load(myYAML, Loader=yaml.FullLoader)))
                      exec('table_object = %s(dev)'%add_table.split(':')[0]) 
                      table_object.get()
                      dataframe= PYEZ_TABLEVIEW_TO_DATAFRAME(dev= dev, tableview_obj= table_object)
                      with st.expander(":blue[Data from router %s :]"%ip):
                        st.dataframe(dataframe)                 
                        st.success('''
                        Get successfully\n
                        Use button below for creating and commit
                        ''')
                      print('[TAB2] Get data successfully. Use button below for creating and commit')
                      dev.close()
                      st.session_state.commit = False
                  except Exception as e:
                      st.error(
                      """
                      - Can't get data by table/view. Review table/view
                      """)
                      print("[TAB2] Check exception %s"%e)
                      st.session_state.commit = True
            except Exception as e:
              st.error(
                """
                - Check Your Username/Password\n
                - Check connection to Router (Or no router available)
                """
                )
              print('[TAB2] Check exception %s'%e)
              st.session_state.commit = True
      
      ##################################### TAB2 Create and commit #####################################
      st.subheader('3. Create and commit')
      with st.form('form2'):
        comment_commit_tab2= st.text_input(':orange[Typing your comment for commit]', placeholder= 'Your comment')
        submitted = st.form_submit_button(label= "Create and commit",type = 'primary', disabled= st.session_state.commit)
        if submitted:
          match op:
            case "*Option 1*":
              path_out = config.get('path_junos_tableview', {}).get('path_table_view') + "/op_get_protocols.yml"
              print('[TAB2] Save table/view to %s'%path_out)
              with open(path_out, 'a') as file_out :
                file_out.write("\n")
                file_out.write("#")
                file_out.write(datetime.now(timezone(timedelta(hours=+7), 'ICT')).strftime("%d/%m/%Y %H:%M:%S"))
                file_out.write("\n")
                file_out.write(add_table)
                file_out.write("\n")
                file_out.write(add_view)
                file_out.write("\n")
                file_out.close()
            case "*Option 2*":
              path_out = config.get('path_junos_tableview', {}).get('path_table_view') + "/op_get_hardware.yml"
              print('[TAB2] Save table/view to %s'%path_out)
              with open(path_out, 'a') as file_out :
                file_out.write("\n")
                file_out.write("#")
                file_out.write(datetime.now(timezone(timedelta(hours=+7), 'ICT')).strftime("%d/%m/%Y %H:%M:%S"))
                file_out.write("\n")
                file_out.write(add_table)
                file_out.write("\n")
                file_out.write(add_view)
                file_out.write("\n")
                file_out.close()
            case "*Option 3*":
              path_out = config.get('path_junos_tableview', {}).get('path_table_view') + "/op_get_system.yml"
              print('[TAB2] Save table/view to %s'%path_out)
              with open(path_out, 'a') as file_out :
                file_out.write("\n")
                file_out.write("#")
                file_out.write(datetime.now(timezone(timedelta(hours=+7), 'ICT')).strftime("%d/%m/%Y %H:%M:%S"))
                file_out.write("\n")
                file_out.write(add_table)
                file_out.write("\n")
                file_out.write(add_view)
                file_out.write("\n")
                file_out.close()
            case "*Option 4*":
              path_out = config.get('path_junos_tableview', {}).get('path_table_view') + "/op_get_services.yml"
              print('[TAB2] Save table/view to %s'%path_out)
              with open(path_out, 'a') as file_out :
                file_out.write("\n")
                file_out.write("#")
                file_out.write(datetime.now(timezone(timedelta(hours=+7), 'ICT')).strftime("%d/%m/%Y %H:%M:%S"))
                file_out.write("\n")
                file_out.write(add_table)
                file_out.write("\n")
                file_out.write(add_view)
                file_out.write("\n")
                file_out.close()
            case "*Option 5*":
                path_out = config.get('path_junos_tableview', {}).get('path_table_view') + "/op_get_links.yml"
                print('[TAB2] Save table/view to %s'%path_out)
                with open(path_out, 'a') as file_out :
                  file_out.write("\n")
                  file_out.write("#")
                  file_out.write(datetime.now(timezone(timedelta(hours=+7), 'ICT')).strftime("%d/%m/%Y %H:%M:%S"))
                  file_out.write("\n")
                  file_out.write(add_table)
                  file_out.write("\n")
                  file_out.write(add_view)
                  file_out.write("\n")
                  file_out.close()     
            case "*Option 6*":
                path_out = config.get('path_junos_tableview', {}).get('path_table_view') + "/conf_get_table.yml"
                print('[TAB2] Save table/view to %s'%path_out)
                with open(path_out, 'a') as file_out :
                  file_out.write("\n")
                  file_out.write("#")
                  file_out.write(datetime.now(timezone(timedelta(hours=+7), 'ICT')).strftime("%d/%m/%Y %H:%M:%S"))
                  file_out.write("\n")
                  file_out.write(add_table)
                  file_out.write("\n")
                  file_out.write(add_view)
                  file_out.write("\n")
                  file_out.close()  
          print(f"[TAB2] save+commit, path is {path_out}")                             
          gitCommit(
            # repo_path=repo_path,
            file_commit = path_out,
            commit_message = comment_commit_tab2,
            # remote=remote,
            # branch_name= branch_name
          )
          # print(34, file_commit)
          gitpr(
            title='fix: Create new file Junos_tableview',
            body='This PR to add new file Junos_tableview'
          )
          st.success('Create and commit successfully')
          print('[TAB2] Create and commit successfully')
    ############################################# TAB3 ###########################################
    with tab3:
      dict_table_tab3={}
      dict_view_tab3={}
      edit_table=""
      edit_view=""
      st.subheader('1. Select Table/View')
      option = st.selectbox(':orange[Type or select from list]',list_table_result , placeholder = 'Select table/view', index = None)
      if option:
        print('[TAB3] You selected: [%s] with path [%s]'%(option, dict_table_result.get(option).get('dir')))
        st.session_state.test_table_edit = True
        st.session_state.commit_edit = True
        dict_temp1_tab3={}
        dict_temp2_tab3={}
        with st.container(border = True) as container:
          col1, col2 = st.columns(2)
          with col1:
            with st.container(border = True) as container:
              dict_temp1_tab3[option] = dict_table_result.get(option).get('content')
              st.write(':green[**Table**]')
              edit_table= st_ace(value= yaml.dump(dict_temp1_tab3, indent = 4), 
              language= config.get('config_streamlit_ace', {}).get('language'), 
              theme= config.get('config_streamlit_ace', {}).get('theme'), 
              show_gutter= config.get('config_streamlit_ace', {}).get('show_gutter'), 
              keybinding=config.get('config_streamlit_ace', {}).get('keybinding') , 
              auto_update= config.get('config_streamlit_ace', {}).get('auto_update'), 
              height= 200)
              #edit_table= container.text_area(':green[Table]', yaml.dump(dict_temp1_tab3, indent = 4), height= 250)
              ####### Display for edit args in table
              if list(dict_temp1_tab3.get(option).keys()).count('args') == 0:
                st.write(':green[**Args**]')
                edit_table_args= st_ace(value= '', 
              language= config.get('config_streamlit_ace', {}).get('language'), 
              theme= config.get('config_streamlit_ace', {}).get('theme'), 
              show_gutter= config.get('config_streamlit_ace', {}).get('show_gutter'), 
              keybinding=config.get('config_streamlit_ace', {}).get('keybinding') , 
              auto_update= config.get('config_streamlit_ace', {}).get('auto_update'),  
                height= 100)
              #edit_table_args= container.text_area(':green[Args]', height= 150)
              else:
                st.write(':green[**Args**]')
                edit_table_args= st_ace(value= yaml.dump(dict_temp1_tab3.get(option).get('args'), indent = 4), 
              language= config.get('config_streamlit_ace', {}).get('language'), 
              theme= config.get('config_streamlit_ace', {}).get('theme'), 
              show_gutter= config.get('config_streamlit_ace', {}).get('show_gutter'), 
              keybinding=config.get('config_streamlit_ace', {}).get('keybinding') , 
              auto_update= config.get('config_streamlit_ace', {}).get('auto_update'), 
                height= 100)
              #edit_table_args= container.text_area(':green[Args]', yaml.dump(dict_temp1_tab3.get(option).get('args'), indent = 4), height= 150)
          with col2:
            dict_temp2_tab3={}
            with st.container(border = True) as container:
              dict_temp2_tab3[dict_table_result.get(option).get("view")] = dict_view_result.get(dict_table_result.get(option).get("view")).get('content')
              st.write(':green[**View**]')
              edit_view= st_ace(value= yaml.dump(dict_temp2_tab3, indent = 4), 
              language= config.get('config_streamlit_ace', {}).get('language'), 
              theme= config.get('config_streamlit_ace', {}).get('theme'), 
              show_gutter= config.get('config_streamlit_ace', {}).get('show_gutter'), 
              keybinding=config.get('config_streamlit_ace', {}).get('keybinding') , 
              auto_update= config.get('config_streamlit_ace', {}).get('auto_update'), 
              height= 380)
              #edit_view= container.text_area(':green[View]', yaml.dump(dict_temp2_tab3, indent = 4), height= 445)
        try:
          edit_path_out = dict_table_result.get(option).get('dir')
          edit_file_yml = yaml.load(open(edit_path_out,"r"), Loader=yaml.FullLoader)
          dict_table_tab3 = {key: val for key, val in edit_file_yml.items() if key.endswith("Table")}  # Get dict Table
          dict_view_tab3 = {key: val for key, val in edit_file_yml.items() if key.endswith("iew")}     # Get dict View
        except Exception as e:
          st.error("[TAB3] Read file yaml fail with log error [%s]"%e)
          print("[TAB3] Read file yaml fail with log error [%s]"%e)
        with st.container(border = True) as container:
          output=[]
          col3, col4, col5 = st.columns([10,1.5,1])
          with col3:
            st.write("*Use beside button for check syntax/delete your table/view ...*")
          with col4:
            if st.button('Check syntax', type= 'primary'):
              conf_ymllint_tab3 = YamlLintConfig('extends: %s'%yamllint_conf)
              error_table_tab3 = linter.run(edit_table , conf_ymllint_tab3)
              error_view_tab3 = linter.run(edit_view , conf_ymllint_tab3)
              error_args_tab3 = linter.run(edit_table_args , conf_ymllint_tab3)
              list_err_table_tab3 = list(error_table_tab3)
              list_err_view_tab3 = list(error_view_tab3)
              list_err_args_tab3 = list(error_args_tab3)
              if edit_table.split(':')[0] == option:
                if edit_view.split(':')[0] == dict_table_tab3.get(option).get("view"):
                  if edit_view.split(':')[0] == edit_table.split(':')[-1].strip():
                    if (edit_table_args.find(':') != -1) or (edit_table_args.strip() == ""):
                      if (len(list_err_table_tab3) + len(list_err_view_tab3)+len(list_err_args_tab3)) != 0:
                        for i in range(len(list_err_table_tab3)):
                          str1= str(list_err_table_tab3[i]).split(':')
                          output.append(":red[Check [ Table ] line %s from character %s with *%s*]" %(str1[0], str1[1], str1[2]))
                        for j in range(len(list_err_view_tab3)):
                          str2= str(list_err_view_tab3[j]).split(':')
                          output.append(":red[Check [ View ] line %s from character %s with *%s*]" %(str2[0],str2[1],str2[2]))
                        for k in range(len(list_err_args_tab3)):
                          str3= str(list_err_args_tab3[k]).split(':')
                          output.append(":red[Check [ Args ] line %s from character %s with *%s*]" %(str3[0],str3[1],str3[2]))
                      else:
                        st.toast(':blue[Check table/view syntax successfully]')
                        output.append("""
                        :blue[Use form below for trying]
                        """)
                        st.session_state.test_table_edit = False
                        st.session_state.commit_edit = True
                    else:
                      output.append(":red[Wrong Args Syntax]")
                      st.session_state.test_table_edit = True
                      st.session_state.commit_edit = True               
                  else:
                    output.append(":red[Don't match Table.view with View]")
                    st.session_state.test_table_edit = True
                    st.session_state.commit_edit = True
                else:
                  output.append(":red[Don't change your View Name]")
                  st.session_state.test_table_edit = True
                  st.session_state.commit_edit = True
              else:
                output.append(":red[Don't change your Table Name]")
                st.session_state.test_table_edit = True
                st.session_state.commit_edit = True
          with col5:
            if st.button('Delete'):
              if edit_table.split(':')[0] == option:
                if edit_view.split(':')[0] == dict_table_tab3.get(option).get("view"):
                  output.append(":blue[Did you select delete your table/view? Use button below for commit]")
                  st.session_state.commit_del_edit = False
                else:
                  output.append(":red[Don't change your View Name]")
                  st.session_state.commit_del_edit = True
              else:
                output.append(":red[Don't change your Table Name]")
                st.session_state.commit_del_edit = True
          for o in output:    
            st.write(str(o))
            if o == output[-1]:
              output.clear()
      ########################## TAB3 Test table/view ####################################################
      st.subheader('2. Try your edited table/view with your router')
      with st.form("form3"):
        user, passwd, router = component_login()
        tab3_list_host= GET_ALIVE_HOST(router)
        print(tab3_list_host)
        submitted = st.form_submit_button(label= "Run", disabled= st.session_state.test_table_edit)
        if submitted:
          with st.spinner('Wait for it...'):
            #time.sleep(1)
            args_dict = yaml.safe_load(edit_table_args)
            #print(args_dict)
            try:
              for ip in tab3_list_host:
                with Device(host=ip, user= user, password= passwd) as dev:
                  try:
                    print("[TAB3] Call GET_PYEZ_TABLEVIEW")
                    tv_obj = GET_PYEZ_TABLEVIEW(dev= dev, data_type = edit_table.split(':')[0][:-5], kwargs= args_dict)
                    tv_obj.get()
                    print("[TAB3] Call PYEZ_TABLEVIEW_TO_DATAFRAME [%s]"%tv_obj)
                    dataframe= PYEZ_TABLEVIEW_TO_DATAFRAME(dev= dev, tableview_obj= tv_obj)
                    with st.expander(":green[Data from host %s:]"%ip):
                      st.dataframe(dataframe)
                      dev.close()
                  except Exception as e:
                      st.error(
                      """
                      - Can't get data by table/view. Review table/view
                      """)
                      logging.error ( "Can't get data by table/view. Review table/view [ {} ]".format(e))
                      st.session_state.commit_edit = True
              st.toast(':blue[Get successfully]')
              st.success('''
              Use button below for saving and commit
              ''')
              st.session_state.commit_edit = False
            except Exception as e:
              st.error(
                """
                - Check Your Username/Password\n
                """
                )
              logging.error ( "Check Your Username/Password/Connection [ {} ]".format(e))
              st.session_state.commit_edit = True
      ############################## TAB3 Save and commit #################################################
      st.subheader('3. Save change and commit')
      with st.form("form4"):
        comment_commit_tab3= st.text_input(':orange[Typing your comment for commit]', placeholder= 'Your comment')
        submitted = st.form_submit_button(label= "Save change and commit",type= 'primary', disabled= st.session_state.commit_edit)
        if submitted:
          with st.container(border = True) as container:
            dict_view_tab3.pop(dict_table_tab3.get(option).get("view"))
            dict_table_tab3.pop(option)
            with open(edit_path_out, 'w') as file_out :
              file_out.write("---")
              file_out.write("\n")
              file_out.write(yaml.dump(dict_table_tab3, indent = 4))
              file_out.write("\n")
              file_out.write(yaml.dump(dict_view_tab3, indent = 4))
              file_out.write("\n")
              file_out.write('#')
              file_out.write(datetime.now(timezone(timedelta(hours=+7), 'ICT')).strftime("%d/%m/%Y %H:%M:%S"))
              file_out.write("\n")
              file_out.write(edit_table)
              file_out.write("\n")
              file_out.write(edit_view)
              file_out.write("\n")
              file_out.close()
          print(f"[TAB3] Path is {edit_path_out}")                                
          gitCommit(
            # repo_path=repo_path,
            file_commit = edit_path_out,
            commit_message = comment_commit_tab3,
            # remote=remote,
            # branch_name= branch_name
            )
          gitpr(
            title='fix: Modify file Junos_tableview',
            body='This PR to modify file Junos_tableview'
            )
          st.success('Save change and commit successfully')
          print('[TAB3] Save change and commit successfully')
        st.session_state.commit_edit = True
      ############################## TAB3 Delete and commit #################################################
      st.subheader('4. Delete and commit')
      with st.form("form5"):
        comment_commit_tab3= st.text_input(':orange[Typing your comment for commit]', placeholder= 'Your comment')
        submitted = st.form_submit_button(label= "Confirm delete and commit",type= 'primary', disabled= st.session_state.commit_del_edit)
        if submitted:
          with st.container(border = True) as container:
            dict_view_tab3.pop(dict_table_tab3.get(option).get("view"))
            dict_table_tab3.pop(option)
            with open(edit_path_out, 'w') as file_out :
              file_out.write("---")
              file_out.write("\n")
              file_out.write(yaml.dump(dict_table_tab3, indent = 4))
              file_out.write("\n")
              file_out.write(yaml.dump(dict_view_tab3, indent = 4))
              file_out.close()
          print(f"[702][TAB3] Path is {edit_path_out}")
                                             
          gitCommit(
            # repo_path=repo_path,
            file_commit = edit_path_out,
            commit_message = comment_commit_tab3,
            # remote=remote,
            # branch_name= branch_name
            )
          # print(34, file_commit)
          gitpr(
            title='fix: Delete file Junos_tableview',
            body='This PR to delete file Junos_tableview'
            )
          st.success('Delete and commit successfully')
          print('[TAB3] Delete and commit successfully')
        st.session_state.commit_del_edit = True
    ###################### TAB4 ##########################################################################
    with tab4:
      st.subheader('1. Select Table/View ')
      option = st.multiselect(':orange[Type or select for searching]',dict_table_result.keys(), placeholder = 'Select table/view')
      list_data_type = option
      if option:
        for option in option:
          print('[TAB4] You selected: [%s] with path [%s]'%(option, dict_table_result.get(option).get('dir')))
          # list_data_type.append(option)
          dict_export_file[option]= dict_table_result.get(option).get('content')
          dict_export_file[dict_table_result.get(option).get('view')] = dict_view_result.get(dict_table_result.get(option).get('view')).get('content')
          with st.expander(":green[%s]"%option):
            col1, col2 = st.columns(2)
            with col1:
                dict_temp1_tab4={}
                container = st.container(border = True)
                dict_temp1_tab4[option] = dict_table_result.get(option).get('content')
                container.code(yaml.dump(dict_temp1_tab4, indent = 4), language = 'yaml', line_numbers= True) # Display dict by yaml format
            with col2:
                dict_temp2_tab4={}
                container = st.container(border = True)
                dict_temp2_tab4[dict_table_result.get(option).get('content').get('view')] = dict_view_result.get(dict_table_result.get(option).get('content').get('view')).get('content')
                container.code(yaml.dump(dict_temp2_tab4, indent = 4), language = 'yaml', line_numbers= True)
      ########################## TAB4 Test table/view witch offline data ####################################################
      st.subheader('2. Try your edited table/view with your XML file')
      uploaded_file = st.file_uploader("Choose a file", type=["tar", "gz", "zip", "rar"])
      submitted = st.button(label= "Run")
      if uploaded_file is not None and submitted:
        with st.spinner('Wait for it...'):
          # time.sleep(1)
          file_contents = uploaded_file.read()
          file_name = os.path.splitext(uploaded_file.name)[0]
          file_format = uploaded_file.name.split('.')[-1]
          # Specify the output directory where you want to extract the contents
          timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
          output_directory= os.path.join(config.get('path_junos_tableview', {}).get('dir_output'), f"{file_name}_{timestamp}")
          ## extract file input and save to output directory
          if file_format == "tar":
              extract_tar(file_contents, output_directory)
          elif file_format == "gz":
              extract_tar_gz(file_contents, output_directory)
          elif file_format == "zip":
              extract_zip(file_contents, output_directory)
          elif file_format == "rar":
              extract_rar(file_contents, output_directory)
          list_result = []
          list_result_all = []
          try:
            if os.path.isdir(output_directory):
              for item in os.listdir(output_directory):
                  item_path = os.path.join(output_directory, item)
                  if os.path.isdir(item_path):
                      dir_xml= os.path.join(output_directory, file_name)
                  else:
                      dir_xml= output_directory
            else:
                print(f"{output_directory} not directory")
            #print("[TAB4] Call GET_PYEZ_TABLEVIEW")
            for filename in os.listdir(dir_xml):
                if os.path.isfile(os.path.join(dir_xml, filename)):
                    cmd_process = TextProcessing(os.path.join(dir_xml, filename),"juniper_command")
                    cmd_process.file_to_content()
                    hostname = cmd_process.extract_hostname_from_content().pop()
                    cmd_list = cmd_process.extract_cmd_list_from_content()
                    block_xml = cmd_process.extract_text_command_pair()
                    rpc_reply_content = block_xml[0]['output_text']
                    if rpc_reply_content:
                      with open(os.path.join(dir_xml, f"{hostname}.xml"), 'a') as outfile:
                          for rpc_reply_content  in rpc_reply_content:
                              outfile.write("<rpc-reply ")
                              outfile.write(rpc_reply_content.strip())
                              outfile.write('\n</rpc-reply>\n')
                      with open(os.path.join(dir_xml, f"{hostname}.xml"), 'r+') as file:
                          content = file.read()
                          file.seek(0)
                          file.write(f"<div>\n{content}</div>\n")   
            excel_file_path= os.path.join(dir_xml, "output_excel.xlsx")  
            with pd.ExcelWriter(excel_file_path) as writer:
              for data_type in list_data_type:
                try:
                  final_result=pd.DataFrame()
                  tableview_file= dict_table_result.get(data_type).get('dir')
                  defined_tablelist = IMPORT_JUNOS_TABLE_VIEW(tableview_file)
                  for file in os.listdir(dir_xml):
                      if file.endswith('.xml'):
                        hostname= os.path.splitext(file)[0]
                        xml_path= os.path.join(dir_xml,file)
                        data = defined_tablelist[data_type](path=xml_path)
                        data.get()
                        if len(data.get()) != 0:
                            data_frame = PYEZ_TABLEVIEW_TO_DATAFRAME(tableview_obj=data, include_hostname=False)
                            data_frame.insert(0, 'hostname', hostname)
                            final_result=pd.concat([final_result, data_frame], ignore_index=True)
                except Exception as e:
                  logging.error(e)
                final_result.to_excel(writer, sheet_name=data_type, index=False)
                st.write(f"<p style='color:green;'>Output for <strong>{data_type}</strong>:</p>", unsafe_allow_html=True)
                st.dataframe(final_result)
              st.toast(':blue[Get successfully]')
            with open(excel_file_path, 'rb') as f:
                s = f.read()
            download_button_str = download_file_button(s, "output.xlsx", 'Download all xlsx')
            st.markdown(download_button_str, unsafe_allow_html=True)
          except Exception as e:
              st.error(
              """
              - Can't get data by table/view. Review table/view
              """)
              logging.error ( "Can't get data by table/view. Review table/view [ {} ]".format(e))      

    ###################### TAB5 ##########################################################################
    with tab5:
      with st.container(border=True):
      # with st.expander(":blue[See when you want to dicovery RPC with your router and evaluate xpath]"):
        st.subheader('Discovery RPC with your router and evaluate xpath')
        with st.form("form6"):
          user, passwd, router = component_login()
          tab5_list_host=GET_ALIVE_HOST(router)
          command= st.text_input(':orange[Command need check:] ', placeholder = 'Typing command here')
          xpath= st.text_input(':orange[XPath for expression:] ','*', placeholder = 'Typing xpath here')
          submitted = st.form_submit_button("Check", type= 'primary')
          if submitted:
            with st.spinner('Wait for it...'):
              # time.sleep(1)
              try:
                #rpc_cmd = dev.display_xml_rpc(command, format= 'xml').tag.replace("-", "_")
                #exec('xml_obj=dev.rpc.%s(normalize=True)'%rpc_cmd)
                for ip in tab5_list_host:
                  rpc_name , xml_obj = get_xml_obj(host = ip, username= user, password=passwd, command= command)
                  col1, col2 = st.columns([1,9])
                  with col1:
                    st.code('RPC >>>')
                  with col2:
                    st.code(rpc_name)
                  is_valid, error_message = check_xpath_syntax(xpath)
                  if is_valid:
                    with st.expander(":green[Data of router %s:]"%ip):
                      print('[TAB5] Element of RPC XPath %s'%xml_obj.xpath(xpath))
                      for e in xml_obj.xpath(xpath):
                        xml_pretty = convert_xml_pretty(e)
                        st.code(xml_pretty, language= 'xml')
                  else:
                    st.error(f"Syntax XPath is invalid. Error message: [{error_message}]")
                st.toast(':blue[Done]')
              except Exception as e:
                  print('[TAB5] Error exception is [%s]'%e)
                  st.error(
                  """
                  Check connection/username/password\n
                  Check command entered\n
                  Or xml rpc equivalent of this command is not available.
                  """)
      with st.expander(":blue[XPath Tester - Evaluator]"):
          st.subheader('Allows you to test your XPath expressions/queries against a XML.')
          st.write(':orange[*Step 1: Copy-paste your XML here*] ')
          input_xml= st_ace(
            language= 'xml', 
            theme= config.get('config_streamlit_ace', {}).get('theme'), 
            show_gutter= config.get('config_streamlit_ace', {}).get('show_gutter'), 
            keybinding=config.get('config_streamlit_ace', {}).get('keybinding') , 
            auto_update= config.get('config_streamlit_ace', {}).get('auto_update'), 
            placeholder= '* Your XML*', 
            height= 300)
          st.write(':orange[*Step 2: XPath expression*] ')
          example_xpath= st.text_input(':orange[Step 2: XPath expression] ', label_visibility="hidden")
          if input_xml:
            example_xml = remove_xml_namespaces(input_xml)
            if example_xpath:
              is_valid, error_message = check_xpath_syntax(example_xpath)
              if is_valid:
                  st.write(":blue[Elements is :]")
                  try:
                    result_xml = evaluate_xpath(example_xml, example_xpath)
                    print('[TAB5] Element of XPath Tester %s'%result_xml)
                    for e in result_xml:
                      xml_pretty = convert_xml_pretty(e)
                      st.code(xml_pretty, language= 'xml')
                  except Exception as e:
                    st.error("XML syntax error %s"%e)
              else:
                  st.error(f"Syntax is invalid. Error message: {error_message}")
            else:
              st.error(
                """
                - XPath Empty
                """
                )
          else:
              st.error(
                """
                - XML Empty
                """
                )             
  with tab6:
    ##EXPLAIN: you dont have to do anything here becase we already specify this as output for stdout above
    st.write(":blue[Python Printing Operation (stdout) will be displayed on this tab. ]")
  with tab7:
    ##EXPLAIN: you dont have to do anything here becase we already specify this as output for stderr above
    st.write(":blue[Python Logging Data from logger object will be displayed on this tab. ]")
