##################################################################
# Use Python (pyCurl) and the SimpliVity REST API  to create
# multiple clones of a single VM
#
# Usage: SVTMultiCloneVM.py -s SOURCEVM -n NumberofClones
#
# http://www.vhersey.com/
# 
# http://www.simplivity.com/
#
##################################################################
import pycurl
import json
import base64
import urllib
from io import BytesIO
import requests
import sys, getopt

#IP or Hostname of OVC
ovc = '192.168.1.10'
#Username and Password
username = 'Domain\User'
password = 'Password'

#Clear sourcevm and clonevm
sourcevm = ''
numvms = 0
#Get sourcevm and clonevm from command line args
try:
   opts, args = getopt.getopt(sys.argv[1:],"hs:n:",["sourcevm=","numvms="])
except getopt.GetoptError:
   print 'SVTMultiCloneVM.py -s <sourcevm> -n <1-50>'
   sys.exit(2)
for opt, arg in opts:
   if opt == '-h':
      print 'SVTMultiCloneVM.py -s <sourcevm> -n <1-50>'
      sys.exit()
   elif opt in ("-s", "--sourcevm"):
      sourcevm = arg
   elif opt in ("-n", "--numvms"):
      numvms = int(arg)

if ( numvms > 50 ):
   print 'A maximum of 50 VMs can be created using this script'
   print 'SVTMultiCloneVM.py -s <sourcevm> -n <1-50>'
   sys.exit(2)
if ( sourcevm == '' ) or (numvms == 0):
   print 'Source VM Required\nNumber Clone VMs Required'
   print 'SVTMultiCloneVM.py -s <sourcevm> -n <1-50>'
   sys.exit(2)

print 'Source VM is: ', sourcevm
print 'Number of Clones to Create: ', numvms
   
#Fuction using pyCurl to post to SVT REST using url encoded data
def post_SVTREST(url, data, header):
   rdata = BytesIO()
   pdata = urllib.urlencode(data)
   c = pycurl.Curl()
   c.setopt(pycurl.SSL_VERIFYPEER, 0)
   c.setopt(pycurl.SSL_VERIFYHOST, 0)
   c.setopt(pycurl.URL, url)
   c.setopt(pycurl.HTTPHEADER, header)
   c.setopt(c.WRITEFUNCTION, rdata.write)
   c.setopt(pycurl.POST, 1)
   c.setopt(pycurl.POSTFIELDS, pdata)
   c.perform()
   c.close()
   jdata = json.loads(rdata.getvalue())
   return (jdata)

#Fuction using pyCurl to post to SVT REST using json data
def jpost_SVTREST(url, data, header):
   rdata = BytesIO()
   c = pycurl.Curl()
   c.setopt(pycurl.SSL_VERIFYPEER, 0)
   c.setopt(pycurl.SSL_VERIFYHOST, 0)
   c.setopt(pycurl.URL, url)
   c.setopt(pycurl.HTTPHEADER, header)
   c.setopt(c.WRITEFUNCTION, rdata.write)
   c.setopt(pycurl.POST, 1)
   c.setopt(pycurl.POSTFIELDS, data)
   c.perform()
   c.close()
   jdata = json.loads(rdata.getvalue())
   return (jdata)

#Funtion using pyCurl to get from SVT REST
def get_SVTREST(url, header):
   rdata = BytesIO()
   c = pycurl.Curl()
   c.setopt(pycurl.SSL_VERIFYPEER, 0)
   c.setopt(pycurl.SSL_VERIFYHOST, 0)
   c.setopt(pycurl.URL, url)
   c.setopt(pycurl.HTTPHEADER, header)
   c.setopt(c.WRITEFUNCTION, rdata.write)
   c.perform()
   c.close()
   jdata = json.loads(rdata.getvalue())
   return (jdata)

#Get Access Token
url = 'https://'+ ovc +'/api/oauth/token'
data = {'username': username,'password': password,'grant_type':'password'}
svtuser = 'simplivity:'
svtauth = 'Authorization:  Basic ' + base64.b64encode(svtuser)
htoken = ['Accept: application/json', svtauth ]
svttoken = post_SVTREST(url, data, htoken)
accesstoken = 'Authorization: Bearer ' + svttoken["access_token"]

#Get VM Id of Source VM
htoken = ['Accept: application/json', accesstoken]
url = 'https://'+ ovc +'/api/virtual_machines?show_optional_fields=false&name=' +  sourcevm
SVTvms = get_SVTREST(url, htoken)
vm_id = SVTvms['virtual_machines'][0]['id']

#Clone Source VM to Clone
url = 'https://'+ ovc +'/api/virtual_machines/'+ vm_id +'/clone'

count = 1
while (count <= numvms):
   clonevm = sourcevm +'-'+ str(count)
   data = {"app_consistent": "false", "virtual_machine_name": clonevm}
   sdata = json.dumps(data)
   htoken = ['Accept: application/json', 'Content-Type: application/vnd.simplivity.v1+json', accesstoken ]
   vmclone = jpost_SVTREST(url, sdata, htoken)
   #Report task details
   print 'SimpliVity Clone ', vmclone['task']['state']
   print 'SVT Task Id: ', vmclone['task']['id']
   count = count+1

