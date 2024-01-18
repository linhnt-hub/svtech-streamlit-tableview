
import os
import re

def get_list_file(file_path, file_type):
  file_list=[]
  list_file_result=[]

  for files in os.walk(file_path):
      file_list = files[2] #Get file_list
  
  for i in range(len(file_list)):
    str = "^.*" + file_type + "$"
    x= re.search(str,file_list[i])
    if x:
        list_file_result.append(file_list[i])
  #list_file_result_str = [str(x) for x in list_file_result]     # Change string format
  return list_file_result