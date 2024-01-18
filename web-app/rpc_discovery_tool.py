from jnpr.junos import Device
from getpass import getpass
import jnpr.junos.exception
import sys

def rpc_discovery(ipadd, user, password, arg):
    try:
        with Device(host=ipadd, user= user, password= password) as dev:
            print('Are we connected?', dev.connected)
            try:
                print("*" * 70, "\n")
                sys_cmd = dev.display_xml_rpc(arg).tag.replace("-", "_")
                print(arg, f"= {sys_cmd}", "\n" + "-" * 70)
                print("\n\n" + "*" * 70)
            except IndexError:
                print(
                """
                No command entered, i.e.,
                python3.py rpc.discovery_tool.py 'show version'
                """)
    except jnpr.junos.exception.ConnectAuthError as autherr:
        print('Check key password', autherr)
    return sys_cmd