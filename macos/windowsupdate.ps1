# Adapted from
# https://blogs.technet.microsoft.com/jamesone/2009/01/27/managing-windows-update-with-powershell/

Function Add-WindowsUpdate {

  $resultcode = @{
    0="Not Started";
    1="In Progress";
    2="Succeeded";
    3="Succeeded With Errors";
    4="Failed";
    5="Aborted"
  }

  $updateSession = new-object -com "Microsoft.Update.Session"
  write-output "Checking available updates ..."
  $updates=$updateSession.CreateupdateSearcher().Search('').Updates

  if ($Updates.Count -eq 0) {
    write-output "There are no applicable updates."
    return
  }

  $downloader = $updateSession.CreateUpdateDownloader()
  $downloader.Updates = $Updates
  write-output "Downloading $($downloader.Updates.count) updates ..."
  $Result = $downloader.Download()  

  if (($Result.Hresult -eq 0) –and (($result.resultCode –eq 2) -or ($result.resultCode –eq 3)) ) {
    $updatesToInstall = New-object -com "Microsoft.Update.UpdateColl"
    $Updates | where {$_.isdownloaded} | foreach-Object {$updatesToInstall.Add($_) | out-null }
    $installer = $updateSession.CreateUpdateInstaller()
    $installer.Updates = $updatesToInstall

    write-output "Installing $($Installer.Updates.count) updates ..."
    $installationResult = $installer.Install()
    $Global:counter = -1
    $installer.updates | Format-Table -autosize -property Title,EulaAccepted,@{label='Result';
                         expression={$ResultCode[$installationResult.GetUpdateResult($Global:Counter++).resultCode ] }} 

    if ($installationResult.rebootRequired) {
      write-output "Reboot required. Rebooting now ..."
      shutdown.exe /t 0 /r
      sleep 999  # shutdown.exe does not block. Don't keep running.
    }
  }
}

Add-WindowsUpdate
