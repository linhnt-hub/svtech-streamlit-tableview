import streamlit as st
import pandas as pd # Data Frame
import numpy as np
import json # Json format
import os, sys, logging
from streamlit_utilities import * #Lib for stdout,stderr, gitcommit, gitpr
from pathlib import Path 
import time
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
# def display_xml_tree(xml_string):
#     try:
#         # Parse the XML string using etree.fromstring()
#         root = etree.fromstring(xml_string)
#         # Display the XML tree using etree.tostring() with pretty_print
#         tree_str = etree.tostring(root, pretty_print=True, encoding="unicode")
#         print(tree_str)
#     except etree.XMLSyntaxError as e:
#         print(f"XMLSyntaxError: {e}")

def get_xml_data(device_host, username, password, command):
    try:
        # Connect to the Junos device
        dev = Device(host=device_host, user=username, password=password)
        dev.open()

        # Execute the command and get the XML response
        response_xml = dev.cli(command, format='xml')

        # Parse the XML response
        root = etree.fromstring(response_xml)

        return root
    except Exception as e:
        return f"Error: {e}"

    finally:
        # Close the connection
        dev.close()
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
############## Import /opt/SVTECH-Junos-Automation/module_utils/PYEZ_BASE_FUNC.py ######################
# Load config path from file
#config = yaml.load(open('app_config.yml',"r"), Loader=yaml.FullLoader)
#st.write(config.get('path_module_utils'))

sys.path.insert(0, config.get('path_junos_tableview', {}).get('path_module_utils'))
from PYEZ_BASE_FUNC import PYEZ_TABLEVIEW_TO_DATAFRAME
from PYEZ_BASE_FUNC import GET_PYEZ_TABLEVIEW_RAW
from BASE_FUNC import LOGGER_INIT
## EXPLAIN: setting shell_output = False will create a default log Streamhandler, which by default send all   all Python log to stderr
## then we send all console stdout to TerminalOutput tab
## all stderr data (which include formatted log) to the LogData tab
#LOGGER_INIT(log_level=logging.NOTSET, print_log_init = False, shell_output= False) 

########################### Read file ########3#################
#file_path = '/opt/SVTECH-Junos-Automation/Junos_tableview/'
#file_type = 'yml'
#list_file_result = get_list_file(file_path, file_type) # List file in directory
list_file_result = ['conf_get_table.yml', 'op_get_protocols.yml', 'op_get_hardware.yml', 'op_get_system.yml', 'op_get_services.yml']
list_table_result=[] # Save list tables
list_view_result=[] # Save list views
dict_table_result={} # Save dict tables
dict_view_result={}  # Save dict views
dict_path={}  # Save dict path
# val= [] # Variable insert db

########################### Browser file #######################
try:
  for j in range(len(list_file_result)):
    path = config.get('path_junos_tableview', {}).get('path_table_view') + "/" + list_file_result[j]
    file_yml = yaml.load(open(path,"r"), Loader=yaml.FullLoader)
    res_table = {key: val for key, val in file_yml.items() if key.endswith("Table")}  # Get dict Table
    res_view = {key: val for key, val in file_yml.items() if key.endswith("iew")}     # Get dict View
    if res_table:
      for i in range(len(list(res_table.keys()))):
        list_table_result.append(list(res_table.keys())[i]) # Save name table to list
        dict_table_result.update(res_table)                 # Save dict_table to dict
        dict_path [list(res_table.keys())[i]]=path
        ### Record to prepare write to Database
        # temp = (str(list(res_table.keys())[i]), str(res_table.get(list(res_table.keys())[i]).get("view")), str(path))
        # val.append(list(temp)) 
            
    if res_view:
      for i in range(len(list(res_view.keys()))):
        list_view_result.append(list(res_view.keys())[i])
        dict_view_result.update(res_view)
except Exception as e:
  print("An exception occurred, check file yaml %s" %e)
######################## PAGE ################################
if 'test_table' not in st.session_state:
  st.session_state.test_table = True
  st.session_state.commit = True
  st.session_state.test_table_edit = True
  st.session_state.commit_edit = True
  st.session_state.commit_del_edit = True

tab5, tab6, tab7 = st.tabs(["🔢 TABLES / VIEWS", "📩 TERMINAL LOG", "📞LOG DATA"])
with st_stdout("code",tab6), st_stderr("code",tab7):
  with tab5:
    tab1, tab2, tab3, tab4 = st.tabs(["1️⃣ VIEW","2️⃣CREATE", "3️⃣ EDIT / TEST", "4️⃣RPC CHECK / XPATH TESTER"])
    ################# TAB1 #############
    with tab1:
        #st.header(':green[What table are your lookup ?]')
        st.subheader('Look Table/View Content ')
        options = st.multiselect(':orange[Type or select for searching]',list_table_result, placeholder = 'Select for view')
        #st.write('You selected:', options)
        dict_export_file={}
        if options:
          for option in options:
              dict_export_file[option]= dict_table_result.get(option)
              dict_export_file[dict_table_result.get(option).get("view")] = dict_view_result.get(dict_table_result.get(option).get("view"))
              with st.container(border = True) as container:
                col1, col2 = st.columns(2)
                with col1:
                    dict_temp1_tab1={}
                    container = st.container(border = True)
                    dict_temp1_tab1[option] = dict_table_result.get(option)
                    #container.code("%s" % option, language= 'yaml')
                    container.code(yaml.dump(dict_temp1_tab1, indent = 4), language = 'yaml', line_numbers= True) # Display dict by yaml format
                with col2:
                    dict_temp2_tab1={}
                    container = st.container(border = True)
                    dict_temp2_tab1[dict_table_result.get(option).get("view")] = dict_view_result.get(dict_table_result.get(option).get("view"))
                    #container.code("%s" % dict_table_result.get(option).get("view"), language= 'yaml')
                    container.code(yaml.dump(dict_temp2_tab1, indent = 4), language = 'yaml', line_numbers= True)
        with st.container(border = True) as container:
          col3, col4 = st.columns([9,1])
          with col3:
            st.write("*Use beside button for exporting your selection ...*")
          with col4:
            st.download_button('Export', "---"+"\n"+ yaml.dump(dict_export_file, indent = 4, encoding= None))
    ###################### TAB2 ################################
    with tab2:
      st.subheader('1. Create new Table/View ')
      with st.container(border = True):
        op = st.radio(
          ":orange[Choose your aim when you create tables/views : ]",
          ["*Option 1*", "*Option 2*", "*Option 3*", "*Option 4*", "*Option 5*"],
          captions = ["Extract :green[Protocols] ( Firewall, ARP, APS, BFD, BGP, OSPF, ISIS, MPLS, RSVP, LDP ...) informations from Junos devices.", 
          "Extract :green[Hardware] ( Alarms, Enviroment, Craft-interface, Fabric, Fan, FPC, Hardware, Power, ...) informations from Junos devices.", 
          "Extract :green[System Operational] ( Interfaces, Alarms, Software, Connections, Storage, User, Snapshot, NTP ... ) informations from Junos devices.",
          "Extract :green[Services State] ( BNG, l2circuit, l2vpn, mac-vrf, loop-detect, multicast, mvpn, network-access, nonstop-routing, policer, route, services, snmp ...) informations from Junos devices.", 
          "Retrieve :green[Configuration Data]."],
          index= None,
        )
      ############## TAB2 Table ####################################################
      with st.container(border = True):
        col1, col2 = st.columns([2,30])
        with col1:
          st.text_area(
            "N1",
            label_visibility = 'hidden',
            height=370,
            disabled = True,
            placeholder= "  1 \n  2\n  3  \n  4  \n  5  \n  6  \n  7  \n  8  \n  9  \n 10\n 11\n 12\n 13\n 14\n 15",
          )
        with col2:
          add_table = st.text_area(
            ":orange[Add Table]  *YAML with Identation = 4*",
            height=370,
            placeholder= "* Compose your table structure*",
          )
      ############## TAB2 View ####################################################
      with st.container(border = True):
        col3, col4 = st.columns([2,30])
        with col3:
          st.text_area(
            "N2",
            label_visibility = 'hidden',
            height=370,
            disabled = True,
            placeholder= "  1 \n  2\n  3  \n  4  \n  5  \n  6  \n  7  \n  8  \n  9  \n 10\n 11\n 12\n 13\n 14\n 15",
          )
        with col4:
          add_view = st.text_area(
            ":orange[Add View]  *YAML with Identation = 4*",
            height=370,
            placeholder= "* Compose your view structure*",
          )
        if op:  # Check state of selecting
          if (add_table.find(':') != -1) and add_table.split(':')[0].endswith("Table") and (add_table.find("view") != -1):
            if list_table_result.count(add_table.split(':')[0]) == 0: # Check duplicate table Name
              if (add_view.find(':') != -1) and add_view.split(':')[0].endswith("iew"):
                if list_view_result.count(add_view.split(':')[0]) == 0: # Check duplicate view Name
                  if add_view.split(':')[0] == add_table.split(':')[-1].strip():  # Need strip for remove space
                    conf_ymllint = YamlLintConfig('extends: default') ### Modify file /home/juniper/.local/lib/python3.10/site-packages/yamllint/conf/relaxed.yaml
                    error_table = linter.run(add_table , conf_ymllint)
                    error_view = linter.run(add_view , conf_ymllint)
                    list_err_table = list(error_table)
                    list_err_view = list(error_view)
                    if (len(list_err_table) + len(list_err_view)) != 0:
                      #st.write(list_err_table)
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
                      st.info("""
                      :green[Check table/view syntax successfully]\n
                      :green[Use below for testing new table/view]
                      """)     # No Table/View syntax error
                      st.session_state.test_table = False
                      st.session_state.commit = True
                  else:
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
                  st.warning("""
                    :red[- Duplicate ]
                    :orange[View]
                    :red[ Name. Choose other name, plz ]
                    """
                    )
                  st.session_state.test_table = True
                  st.session_state.commit = True
              else:
                st.error("""
                  :red[- Add/Check ] 
                  :orange[View] 
                  :red[ content.]\n
                  :grey[*Note: view must have suffix \"view\" or \"View\"*]
                  """)
                st.session_state.test_table = True
                st.session_state.commit = True
            else:
              st.warning("""
                :red[- Duplicate ]
                :orange[Table]
                :red[ Name. Choose other name, plz ]
                """
                )
              st.session_state.test_table = True
              st.session_state.commit = True
          else:
              st.error("""
                :red[- Add/Check ] 
                :orange[Table] 
                :red[ content.]
                \n
                :grey[*Note: table must have suffix Table*]\n
                :grey[*Note: table must have \"view:\"*]
                """)
              st.session_state.test_table = True
              st.session_state.commit = True
        else:
          st.error(
            '''
            :red[Check one of below before create, please :]\n
            :red[- Choose one of five options.]\n
            :red[- Add table content.]\n
            :red[- Add view content.]
          ''')
          st.session_state.test_table = True
          st.session_state.commit = True
      #with st.expander(":blue[See when you want to dicovery RPC with your router]"):
      st.subheader('2. Try your new table/view with your router')
      
      #############################TAB2 Form test table/view #####################################
      with st.form("form1"):
        user= st.text_input(':orange[Your username:] ', placeholder = 'Typing user')
        passwd= st.text_input(':orange[Your password:] ', type= 'password', placeholder = 'Typing password')
        router= st.text_input(':orange[Your router IP:] ', placeholder = 'Typing IP\'s device')
        submitted = st.form_submit_button(label= "Run", disabled= st.session_state.test_table)
        if submitted:
          with st.spinner('Wait for it...'):
            time.sleep(1)
            try:
              with Device(host=router, user= user, password= passwd) as dev:
                #print('Are we connected?', dev.connected)
                try:
                    myYAML="".join([add_table,"\n",add_view])
                    #print(myYAML) 
                    globals().update(FactoryLoader().load(yaml.load(myYAML, Loader=yaml.FullLoader)))
                    #print("*" * 70, "\n")
                    exec('table_object = %s(dev)'%add_table.split(':')[0]) 
                    table_object.get()
                    dataframe= PYEZ_TABLEVIEW_TO_DATAFRAME(dev= dev, tableview_obj= table_object)
                    st.write(dataframe)
                    #print(dataframe)
                    #print(pd.DataFrame(dataframe))
                    st.success('''
                    Get successfully\n
                    Use button below for creating and commit
                    ''')
                    dev.close()
                    st.session_state.commit = False
                except:
                    st.error(
                    """
                    - Can't get data by table/view. Review table/view
                    """)
                    st.session_state.commit = True
            except:
              st.error(
                """
                - Check Your Username/Password\n
                - Check connection to Router
                """
                )
              st.session_state.commit = True
      
      ##################################### TAB2 Create and commit #####################################
      st.subheader('3. Create and commit')
      with st.form('form2'):
        comment_commit_tab2= st.text_input(':orange[Typing your comment for commit]', placeholder= 'Your comment')
        submitted = st.form_submit_button(label= "Create and commit",type = 'primary', disabled= st.session_state.commit)
        if submitted:
          match op:
            case "*Option 1*":
              path_out = config.get('path_table_view') + "/op_get_protocols.yml"
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
                #st.code(add_table, language='yaml')
                #st.code(add_view, language='yaml')
            case "*Option 2*":
              path_out = config.get('path_table_view') + "/op_get_hardware.yml"
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
                #st.code(add_table, language='yaml')
                #st.code(add_view, language='yaml')
            case "*Option 3*":
              path_out = config.get('path_table_view') + "/op_get_system.yml"
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
                #st.code(add_table, language='yaml')
                #st.code(add_view, language='yaml')
            case "*Option 4*":
              path_out = config.get('path_table_view') + "/op_get_services.yml"
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
                #st.code(add_table, language='yaml')
                #st.code(add_view, language='yaml')
            case "*Option 5*":
                path_out = config.get('path_table_view') + "/conf_get_table.yml"
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
                  #st.code(add_table, language='yaml')
                  #st.code(add_view, language='yaml')
          st.success('Create and commit successfully')
    ############################################# TAB3 ###########################################
    with tab3:
      dict_table_tab3={}
      dict_view_tab3={}
      edit_table=""
      edit_view=""
      st.subheader('1. Select Table/View')
      option = st.selectbox(':orange[Type or select from list]',tuple(list_table_result), placeholder = 'Select table/view', index = None)
      #st.write('You selected:', options)
      if option:
        st.session_state.test_table_edit = True
        st.session_state.commit_edit = True
        dict_temp1_tab3={}
        dict_temp2_tab3={}
        with st.container(border = True) as container:
          col1, col2 = st.columns(2)
          with col1:
            container = st.container(border = True)
            dict_temp1_tab3[option] = dict_table_result.get(option)
            edit_table= container.text_area(':green[Table]', yaml.dump(dict_temp1_tab3, indent = 4), height= 250)
            ####### Display for edit args in table
            if list(dict_temp1_tab3.get(option).keys()).count('args') == 0:
              edit_table_args= container.text_area(':green[Args]', height= 150)
            else:
              edit_table_args= container.text_area(':green[Args]', yaml.dump(dict_temp1_tab3.get(option).get('args'), indent = 4), height= 150)
          with col2:
            dict_temp2_tab3={}
            container = st.container(border = True)
            dict_temp2_tab3[dict_table_result.get(option).get("view")] = dict_view_result.get(dict_table_result.get(option).get("view"))
            edit_view= container.text_area(':green[View]', yaml.dump(dict_temp2_tab3, indent = 4), height= 445)
        try:
          edit_path_out = dict_path.get(option)
          edit_file_yml = yaml.load(open(edit_path_out,"r"), Loader=yaml.FullLoader)
          edit_res_table = {key: val for key, val in edit_file_yml.items() if key.endswith("Table")}  # Get dict Table
          edit_res_view = {key: val for key, val in edit_file_yml.items() if key.endswith("iew")}     # Get dict View
          if edit_res_table:
            for i in range(len(list(edit_res_table.keys()))):
              dict_table_tab3.update(edit_res_table) # Save dict_table to dict
          if edit_res_view:
            for i in range(len(list(edit_res_view.keys()))):
              dict_view_tab3.update(edit_res_view)  # Save view to dict
        except:
          st.write("An exception occurred")
        
        with st.container(border = True) as container:
          output=[]
          col3, col4, col5 = st.columns([10,1.5,1])
          with col3:
            st.write("*Use beside button for check syntax/delete your table/view ...*")
          with col4:
            if st.button('Check syntax', type= 'primary'):
              conf_ymllint_tab3 = YamlLintConfig('extends: default')
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
        user= st.text_input(':orange[Your username:] ', placeholder = 'Typing user')
        passwd= st.text_input(':orange[Your password:] ', type= 'password', placeholder = 'Typing password')
        router= st.text_input(':orange[Your router IP:] ', placeholder = 'Typing IP\'s device')
        submitted = st.form_submit_button(label= "Run", disabled= st.session_state.test_table_edit)
        if submitted:
          with st.spinner('Wait for it...'):
            time.sleep(1)
            args_dict = yaml.safe_load(edit_table_args)
            print(args_dict)
            try:
              with Device(host=router, user= user, password= passwd) as dev:
                #print('Are we connected?', dev.connected)
                try:
                  #myYAML= "".join([edit_table,"\n",edit_view])
                  # myYAML= myYAML[:(myYAML.find('args')-4)] + '\n' + myYAML[(myYAML.find('args')-4):]
                  # print(myYAML)
                  #globals().update(FactoryLoader().load(yaml.load(myYAML, Loader=yaml.FullLoader)))
                  #st.write(yaml.args)
                  #print("*" * 70, "\n")
                  #exec('table_object = %s(dev)'%edit_table.split(':')[0]) 
                  #table_object.get()
                  #dataframe= PYEZ_TABLEVIEW_TO_DATAFRAME(dev= dev, tableview_obj= table_object)
                  #st.write(dataframe)
                  with open('file_test_temp.yml','w') as file:
                    file.write(edit_table)
                    file.write('\n')
                    file.write(edit_view)
                    file.close()
                  raw= GET_PYEZ_TABLEVIEW_RAW(dev= dev, data_type = edit_table.split(':')[0][:-5] ,tableview_file= 'file_test_temp.yml', kwargs= args_dict)
                  raw.get()
                  print("This is TABLEVIEW_RAW [%s]"%raw)
                  dataframe= PYEZ_TABLEVIEW_TO_DATAFRAME(dev= dev, tableview_obj= raw)
                  st.write(dataframe)
                  #st.write(raw.items())
                  os.remove('file_test_temp.yml')
                  st.toast(':blue[Get successfully]')
                  st.success('''
                  Use button below for saving and commit
                  ''')
                  dev.close()
                  st.session_state.commit_edit = False
                except Exception as e:
                    st.error(
                    """
                    - Can't get data by table/view. Review table/view
                    """)
                    logging.error ( "[620] Can't get data by table/view. Review table/view [ {} ]".format(e))
                    st.session_state.commit_edit = True
            except Exception as e:
              st.error(
                """
                - Check Your Username/Password\n
                - Check connection to Router
                """
                )
              logging.error ( "[629] Check Your Username/Password/Connection [ {} ]".format(e))
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
          st.success('Save change and commit successfully')
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
          st.success('Delete and commit successfully')
        st.session_state.commit_del_edit = True
    ###################### TAB4 ##########################################################################
    with tab4:
      with st.expander(":blue[See when you want to dicovery RPC with your router and evaluate xpath]"):
        st.subheader('Discovery RPC with your router and evaluate xpath')
        with st.form("form6"):
          user= st.text_input(':orange[Your username:] ', placeholder = 'Typing user')
          passwd= st.text_input(':orange[Your password:] ', type= 'password', placeholder = 'Typing password')
          router= st.text_input(':orange[Your router IP:] ', placeholder = 'Typing IP\'s device')
          command= st.text_input(':orange[Command need check:] ', placeholder = 'Typing command here')
          xpath= st.text_input(':orange[XPath for expression:] ','*', placeholder = 'Typing xpath here')
          submitted = st.form_submit_button("Check", type= 'primary')
          if submitted:
            with st.spinner('Wait for it...'):
              time.sleep(1)
              try:
                with Device(host=router, user= user, password= passwd, normalize=True) as dev:
                  #print('Are we connected?', dev.connected)
                  try:
                    # print("*" * 70, "\n")
                    # response_xml = dev.cli(command, format='xml')
                    # root = etree.fromstring(response_xml)
                    # st.write(root)
                    rpc_cmd = dev.display_xml_rpc(command, format= 'xml').tag.replace("-", "_")
                    exec('a1=dev.rpc.%s(normalize=True)'%rpc_cmd)
                    #st.write(etree.tostring(a1, encoding= 'unicode'))
                    st.code(dev.display_xml_rpc(command, format= 'text'), language='yaml')
                    #print(command, f"= {sys_cmd}", "\n" + "-" * 70)
                    #print("\n\n" + "*" * 70)
                    col1, col2 = st.columns([1,9])
                    with col1:
                      st.code('RPC >>>')
                    with col2:
                      st.code(rpc_cmd)
                    is_valid, error_message = check_xpath_syntax(xpath)
                    if is_valid:
                      st.info("Result:")
                      #st.write(a1.xpath(xpath))
                      #list_xml= []
                      for e in a1.xpath(xpath):
                        xml_minidom = xml.dom.minidom.parseString(etree.tostring(e)) # Func display xml like pretty
                        xml_pretty = xml_minidom.toprettyxml()
                        st.code(xml_pretty, language= 'xml')
                        #list_xml.append(etree.tostring(e, encoding='UTF-8'))
                      #st.write(list_xml)
                      st.toast(':blue[Done]')
                    else:
                      st.error(f"Syntax XPath is invalid. Error message: [{error_message}]")
                    #st.code(dev.cli(command), language='yaml', line_numbers= True)
                    dev.close()
                  except:
                      st.error(
                      """
                      No command entered or xml rpc equivalent of this command is not available.
                      """)
              except:
                st.error(
                  """
                  - Check Your Username/Password\n
                  - Check connection to Router
                  """
                  )
      with st.expander(":blue[XPath Tester - Evaluator]"):
          st.subheader('Allows you to test your XPath expressions/queries against a XML.')
          example_xml= st.text_area(':orange[Step 1: Copy-paste your XML here] ', height=300)
          example_xpath= st.text_input(':orange[Step 2: XPath expression] ')
          #st.code(example_xml, language = 'xml')
          if example_xml:
            if example_xpath:
              is_valid, error_message = check_xpath_syntax(example_xpath)
              # Display the result
              #st.write(f"XPath Expression: {example_xpath}")
              if is_valid:
                  st.write(":blue[Result is :]")
                  try:
                    result = evaluate_xpath(example_xml, example_xpath)
                    st.write(result)
                  except:
                    st.error("XML syntax error")
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
    st.subheader(":blue[Python PRINTING OPERATION (STDOUT) will be displayed on this tab]")
  with tab7:
    ##EXPLAIN: you dont have to do anything here becase we already specify this as output for stderr above
    st.subheader(":blue[Python LOGGING DATA from logger object will be displayed on this tab]")
