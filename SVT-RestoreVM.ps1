##################################################################
# Use PowerShell and the SimpliVity REST API  to 
# Restore a SVT Protected VM 
#
# Usage: SVT-RestoreVM.ps1 -OVC OVCIP -Username USERNAME -Password PASSWORD -VM VMTORESTORE -DC RECOVERYDATACENTER -Name RESTOREVMNAME 
#
# http://www.vhersey.com/
# 
# http://www.simplivity.com/
#
##################################################################
#Get Parameters
param(
 [Parameter(Mandatory=$true, HelpMessage=”OVC IP Address”)][string]$OVC,
 [Parameter(Mandatory=$true, HelpMessage=”OVC Username”)][string]$Username,
 [Parameter(Mandatory=$true, HelpMessage=”OVC Password”)][string]$Password,
 [Parameter(Mandatory=$true, HelpMessage=”VM to Restore”)][string]$VM,
 [Parameter(Mandatory=$true, HelpMessage=”Recovery Datacenter”)][string]$DC,
 [Parameter(Mandatory=$true, HelpMessage=”Restored Name”)][string]$Name
)
############## Set Variables ############## 
$vmtorestore = $VM
$recoverydatacenter = $DC
$ovc = $OVC
$username = $Username
$pass_word = $Password
$restorename = $Name

#Ignore Self Signed Certificates and set TLS
Try {
Add-Type @"
       using System.Net;
       using System.Security.Cryptography.X509Certificates;
       public class TrustAllCertsPolicy : ICertificatePolicy {
           public bool CheckValidationResult(
               ServicePoint srvPoint, X509Certificate certificate,
               WebRequest request, int certificateProblem) {
               return true;
           }
       }
"@
   [System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicy
   [System.Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
} Catch {
}

# Authenticate - Get SVT Access Token
$uri = "https://" + $ovc + "/api/oauth/token"
$base64 = [Convert]::ToBase64String([System.Text.UTF8Encoding]::UTF8.GetBytes("simplivity:"))
$body = @{username="$username";password="$pass_word";grant_type="password"}
$headers = @{}
$headers.Add("Authorization", "Basic $base64")
$response = Invoke-RestMethod -Uri $uri -Headers $headers -Body $body -Method Post 
    
$atoken = $response.access_token

# Create SVT Auth Header
$headers = @{}
$headers.Add("Authorization", "Bearer $atoken")

# Restore Defined VM in Recovery Datacenter
# Get last backup for VM in Recovery Datacenter
$uri = "https://" + $ovc + "/api/backups?virtual_machine_name=" + $vmtorestore + "&omnistack_cluster_name=" + $recoverydatacenter + "&limit=1"
$response = Invoke-RestMethod -Uri $uri -Headers $headers -Method Get

$backuptorestore = $response.backups[0].id
$recoverydatastore = $response.backups[0].datastore_id

if ( $backuptorestore ) {
          
   $uri = "https://" + $ovc + "/api/backups/" + $backuptorestore + "/restore?restore_original=false"
   $body = @{}
   $dsid = $recoverydatastore
   $body.Add("datastore_id", "$dsid")
   $body.Add("virtual_machine_name", "$restorename") 
   $body = $body | ConvertTo-Json
      
   Write-Host "Restoring VM $vm from $backuptorestore to $dsid ... "
   $response = Invoke-RestMethod -Uri $uri -Headers $headers -Body $body -Method Post -ContentType 'application/vnd.simplivity.v1+json'
   
} else {
          
   Write-Host "Backup for $vm not found."
      
}
   
