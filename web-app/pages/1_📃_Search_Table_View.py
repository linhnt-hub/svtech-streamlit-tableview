import streamlit as st
import pandas as pd
import numpy as np
import yaml
import json
import os, sys
from pathlib import Path
import time
from datetime import datetime, timezone, timedelta

import re
from PIL import Image
from yamllint import linter
from yamllint.config import YamlLintConfig

from jnpr.junos import Device
from jnpr.junos.factory.factory_loader import FactoryLoader
import yaml
from lxml import etree # For XML XPath

import mysql.connector

# Import /opt/SVTECH-Junos-Automation/module_utils/PYEZ_BASE_FUNC.py
sys.path.insert(0, '/opt/SVTECH-Junos-Automation/module_utils')
from PYEZ_BASE_FUNC import PYEZ_TABLEVIEW_TO_DATAFRAME

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

###### Connect MySQL ###################
# mydb = mysql.connector.connect(
#   host="localhost",
#   user="linhnt",
#   password="Linhnt@123",
#   database="tableviews",
#   auth_plugin='mysql_native_password',
# )
# mycursor = mydb.cursor()

########### Read file #################
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

####### Browser file #################
try:
  for j in range(len(list_file_result)):
    path = "/opt/SVTECH-Junos-Automation/Junos_tableview/" + list_file_result[j]
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
except:
  st.write("An exception occurred")
########## Check duplicate table/view #############
#dup_table= {x for x in list_table_result if list_table_result.count(x) > 1} # Check duplicate table
#dup_view= {x for x in list_view_result if list_view_result.count(x) > 1} # Check duplicate view
###################################################
### SQL Command to insert DB ###
# mycursor.execute("DELETE from tables") # Delete tables on Database before INSERT
# sql= "INSERT INTO tables (name, view, file) VALUES (%s, %s, %s)"
# mycursor.executemany(sql,val)
# mydb.commit()
################# Page include 3 tabs #############
if 'test_table' not in st.session_state:
  st.session_state.test_table = True
  st.session_state.commit = True
  st.session_state.test_table_edit = True
  st.session_state.commit_edit = True

tab1, tab2, tab3, tab4 = st.tabs(["🔎VIEW","📑CREATE", "📝 EDIT", "✔️RPC CHECKING"])
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
                container.code(yaml.dump(dict_temp1_tab1, indent = 4), language = 'yaml') # Display dict by yaml format
            with col2:
                dict_temp2_tab1={}
                container = st.container(border = True)
                dict_temp2_tab1[dict_table_result.get(option).get("view")] = dict_view_result.get(dict_table_result.get(option).get("view"))
                #container.code("%s" % dict_table_result.get(option).get("view"), language= 'yaml')
                container.code(yaml.dump(dict_temp2_tab1, indent = 4), language = 'yaml')
    with st.container(border = True) as container:
      col3, col4 = st.columns([9,1])
      with col3:
        st.write("*Use beside button for exporting your selection ...*")
      with col4:
        st.download_button('Export', "---"+"\n"+ yaml.dump(dict_export_file, indent = 4, encoding= None))
###################### TAB2 ################################
with tab2:
  # Save state of test_table button
  st.subheader('1. Create new Table/View ')
  #with st.form("form1"):
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
    # Every form must have a submit button.
    # submitted = st.form_submit_button("Create", type= 'primary')
    # if submitted:
    if op:
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
                  st.info(":green[Check table/view syntax successfully]")     # No Table/View syntax error
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
  
  test_table= 0 # Save state test
  ############################# Form test table/view #####################################
  with st.form("form2"):
    user= st.text_input('Your username: ', placeholder = 'Typing user')
    passwd= st.text_input('Your password: ', type= 'password', placeholder = 'Typing password')
    router= st.text_input('Your router IP: ', placeholder = 'Typing IP\'s device')
    #command= st.text_input('Command need check: ', placeholder = 'Typing command here')
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
                st.success('Get successfully')
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
  with st.form('form3'):
    submitted = st.form_submit_button(label= "Create and commit",type = 'primary', disabled= st.session_state.commit)
    if submitted:
      match op:
        case "*Option 1*":
          path_out = "/opt/SVTECH-Junos-Automation/Junos_tableview/op_get_protocols.yml"
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
          path_out = "/opt/SVTECH-Junos-Automation/Junos_tableview/op_get_hardware.yml"
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
          path_out = "/opt/SVTECH-Junos-Automation/Junos_tableview/op_get_system.yml"
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
          path_out = "/opt/SVTECH-Junos-Automation/Junos_tableview/op_get_services.yml"
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
            path_out = "/opt/SVTECH-Junos-Automation/Junos_tableview/conf_get_table.yml"
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
  st.subheader('1. Edit Table/View')
  option = st.selectbox(':orange[Type or select for edit]',tuple(list_table_result), placeholder = 'Select table/view for editting', index = None)
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
        edit_table= container.text_area(':green[Table]', yaml.dump(dict_temp1_tab3, indent = 4), height= 300)
      with col2:
        dict_temp2_tab3={}
        container = st.container(border = True)
        dict_temp2_tab3[dict_table_result.get(option).get("view")] = dict_view_result.get(dict_table_result.get(option).get("view"))
        edit_view= container.text_area(':green[View]', yaml.dump(dict_temp2_tab3, indent = 4), height= 300)
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
        st.write("*Use beside button for check/delete your change ...*")
      with col4:
        if st.button('Check syntax', type= 'primary'):
          conf_ymllint_tab3 = YamlLintConfig('extends: default')
          error_table_tab3 = linter.run(edit_table , conf_ymllint_tab3)
          error_view_tab3 = linter.run(edit_view , conf_ymllint_tab3)
          list_err_table_tab3 = list(error_table_tab3)
          list_err_view_tab3 = list(error_view_tab3)
          if edit_table.split(':')[0] == option:
            if edit_view.split(':')[0] == dict_table_tab3.get(option).get("view"):
              if edit_view.split(':')[0] == edit_table.split(':')[-1].strip():
                if (len(list_err_table_tab3) + len(list_err_view_tab3)) != 0:
                  for i in range(len(list_err_table_tab3)):
                    str1= str(list_err_table_tab3[i]).split(':')
                    output.append(":red[Check [ Table ] line %s from character %s with *%s*]" %(str1[0], str1[1], str1[2]))
                  for j in range(len(list_err_view_tab3)):
                    str2= str(list_err_view_tab3[j]).split(':')
                    output.append(":red[Check [ View ] line %s from character %s with *%s*]" %(str2[0],str2[1],str2[2]))
                else:
                  output.append(":blue[Check table/view syntax successfully]")
                  st.session_state.test_table_edit = False
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
              dict_view_tab3.pop(dict_table_tab3.get(option).get("view"))
              dict_table_tab3.pop(option)
              with open(edit_path_out, 'w') as file_out :
                file_out.write("---")
                file_out.write("\n")
                file_out.write(yaml.dump(dict_table_tab3, indent = 4))
                file_out.write("\n")
                file_out.write(yaml.dump(dict_view_tab3, indent = 4))
                file_out.close()
              output.append(":blue[Delete your table/view successfully]")
            else:
              output.append(":red[Don't change your View Name]")
          else:
            output.append(":red[Don't change your Table Name]")
      for o in output:    
        st.write(str(o))
        if o == output[-1]:
          output.clear()
  ########################## TAB3 Test table/view ####################################################
  st.subheader('2. Try your edited table/view with your router')
  with st.form("form5"):
    user= st.text_input('Your username: ', placeholder = 'Typing user')
    passwd= st.text_input('Your password: ', type= 'password', placeholder = 'Typing password')
    router= st.text_input('Your router IP: ', placeholder = 'Typing IP\'s device')
    submitted = st.form_submit_button(label= "Run", disabled= st.session_state.test_table_edit)
    if submitted:
      with st.spinner('Wait for it...'):
        time.sleep(1)
        try:
          with Device(host=router, user= user, password= passwd) as dev:
            #print('Are we connected?', dev.connected)
            try:
                myYAML= "".join([edit_table,"\n",edit_view])
                print(myYAML) 
                globals().update(FactoryLoader().load(yaml.load(myYAML, Loader=yaml.FullLoader)))
                #print("*" * 70, "\n")
                exec('table_object = %s(dev)'%edit_table.split(':')[0]) 
                table_object.get()
                dataframe= PYEZ_TABLEVIEW_TO_DATAFRAME(dev= dev, tableview_obj= table_object)
                st.write(dataframe)
                #print(dataframe)
                #print(pd.DataFrame(dataframe))
                st.success('Get successfully')
                dev.close()
                st.session_state.commit_edit = False
            except:
                st.error(
                """
                - Can't get data by table/view. Review table/view
                """)
                st.session_state.commit_edit = True
        except:
          st.error(
            """
            - Check Your Username/Password\n
            - Check connection to Router
            """
            )
          st.session_state.commit_edit = True
  ############################## TAB3 Save and commit #################################################
  st.subheader('3. Save change and commit')
  with st.form("form6"):
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
###################### TAB4 ##########################################################################
with tab4:
  with st.expander(":blue[See when you want to dicovery RPC with your router]"):
    st.subheader('Discovery RPC with your router')
    with st.form("form4"):
      user= st.text_input('Your username: ', placeholder = 'Typing user')
      passwd= st.text_input('Your password: ', type= 'password', placeholder = 'Typing password')
      router= st.text_input('Your router IP: ', placeholder = 'Typing IP\'s device')
      command= st.text_input('Command need check: ', placeholder = 'Typing command here')
      submitted = st.form_submit_button("Check", type= 'primary')
      if submitted:
        with st.spinner('Wait for it...'):
          time.sleep(1)
          try:
            with Device(host=router, user= user, password= passwd, normalize=True) as dev:
              #print('Are we connected?', dev.connected)
              try:
                # print("*" * 70, "\n")
                rpc_cmd = dev.display_xml_rpc(command, format= 'xml').tag.replace("-", "_")
                exec('a1=dev.rpc.%s(normalize=True)'%rpc_cmd)
                #st.write(etree.tostring(a1, encoding= 'unicode'))
                st.code(dev.cli(command), language='yaml')
                st.code(dev.display_xml_rpc(command, format= 'text'), language='yaml')
                #print(command, f"= {sys_cmd}", "\n" + "-" * 70)
                #print("\n\n" + "*" * 70)
                col1, col2 = st.columns([1,9])
                with col1:
                  st.code('RPC >>>')
                with col2:
                  st.code(rpc_cmd)
                #st.code(rpc_xml)
                st.success('Done')
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

