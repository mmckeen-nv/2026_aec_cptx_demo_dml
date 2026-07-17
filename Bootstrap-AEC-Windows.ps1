#requires -Version 5.1
[CmdletBinding()]
param(
  [string]$Distro = 'Ubuntu',
  [switch]$OfflineOnly,
  [switch]$NoRestart,
  [switch]$Resume,
  [switch]$SkipVllm,
  [switch]$Yes
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoRoot = $PSScriptRoot
$RunOncePath = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce'
$RunOnceName = 'AEC-CPTX-Setup-Resume'
$LogRoot = Join-Path $env:ProgramData 'AEC-CPTX\logs'

function Write-Step([string]$Message) {
  Write-Host ''
  Write-Host "==> $Message" -ForegroundColor Cyan
}

function Test-Administrator {
  $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
  $principal = [Security.Principal.WindowsPrincipal]::new($identity)
  return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-BootstrapArguments([switch]$IncludeResume) {
  $arguments = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', ('"{0}"' -f $PSCommandPath), '-Distro', ('"{0}"' -f $Distro))
  if ($OfflineOnly) { $arguments += '-OfflineOnly' }
  if ($NoRestart) { $arguments += '-NoRestart' }
  if ($SkipVllm) { $arguments += '-SkipVllm' }
  if ($Yes) { $arguments += '-Yes' }
  if ($IncludeResume) { $arguments += '-Resume' }
  return $arguments
}

function Invoke-Checked([string]$FilePath, [string[]]$ArgumentList, [int[]]$AllowedExitCodes = @(0)) {
  & $FilePath @ArgumentList
  if ($LASTEXITCODE -notin $AllowedExitCodes) {
    throw "$FilePath exited with code $LASTEXITCODE"
  }
  return $LASTEXITCODE
}

function Register-ResumeAfterReboot {
  $command = 'powershell.exe ' + ((Get-BootstrapArguments -IncludeResume) -join ' ')
  New-Item -Path $RunOncePath -Force | Out-Null
  Set-ItemProperty -Path $RunOncePath -Name $RunOnceName -Value $command
  Write-Host 'Automatic post-reboot resume registered.' -ForegroundColor Yellow
}

function Remove-ResumeAfterReboot {
  Remove-ItemProperty -Path $RunOncePath -Name $RunOnceName -ErrorAction SilentlyContinue
}

function Request-Reboot([string]$Reason) {
  Register-ResumeAfterReboot
  Write-Warning $Reason
  if (-not $NoRestart) {
    Write-Host 'The computer will restart in 30 seconds. Run shutdown /a to cancel.' -ForegroundColor Yellow
    & shutdown.exe /r /t 30 /c 'AEC CPTX setup will resume automatically after sign-in.'
  } else {
    Write-Host 'Restart Windows when convenient; setup will resume automatically after sign-in.'
  }
  exit 3010
}

function Enable-WslFeatures {
  $restartNeeded = $false
  foreach ($featureName in @('Microsoft-Windows-Subsystem-Linux', 'VirtualMachinePlatform')) {
    $feature = Get-WindowsOptionalFeature -Online -FeatureName $featureName
    if ($feature.State -ne 'Enabled') {
      Write-Step "Enable Windows feature: $featureName"
      $result = Enable-WindowsOptionalFeature -Online -FeatureName $featureName -All -NoRestart
      if ($result.RestartNeeded) { $restartNeeded = $true }
    } else {
      Write-Host "Current: Windows feature $featureName"
    }
  }
  return $restartNeeded
}

function Get-WslDistros {
  if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) { return @() }
  $lines = @(& wsl.exe --list --quiet 2>$null)
  return @($lines | ForEach-Object { ($_ -replace [char]0, '').Trim() } | Where-Object { $_ })
}

function Test-WslCommand([string]$Command) {
  & wsl.exe -d $Distro -u root -e sh -lc $Command
  return ($LASTEXITCODE -eq 0)
}

if (-not (Test-Administrator)) {
  Write-Host 'Requesting administrator access for Windows/WSL setup...' -ForegroundColor Yellow
  $process = Start-Process powershell.exe -Verb RunAs -Wait -PassThru -ArgumentList (Get-BootstrapArguments)
  exit $process.ExitCode
}

New-Item -ItemType Directory -Path $LogRoot -Force | Out-Null
$logPath = Join-Path $LogRoot ("setup-{0}.log" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
Start-Transcript -Path $logPath -Force | Out-Null
try {
  Write-Host 'AEC CPTX one-click workstation setup' -ForegroundColor Green
  Write-Host "Source:  $RepoRoot"
  Write-Host "Log:     $logPath"
  Write-Host "Mode:    $(if ($OfflineOnly) { 'offline portable' } else { 'connected' })"

  $restartNeeded = Enable-WslFeatures
  if ($restartNeeded) {
    Request-Reboot 'Windows must restart before WSL2 can be completed.'
  }

  Write-Step 'Update WSL and select WSL2'
  if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
    throw 'wsl.exe is unavailable after enabling Windows features. Restart Windows and run Setup-AEC-Demo.cmd again.'
  }
  if (-not $OfflineOnly) {
    Invoke-Checked 'wsl.exe' @('--update') @(0, 3010) | Out-Null
  }
  Invoke-Checked 'wsl.exe' @('--set-default-version', '2') | Out-Null

  $distros = Get-WslDistros
  if ($Distro -notin $distros) {
    if ($OfflineOnly) {
      throw "Offline setup requires an existing '$Distro' WSL2 distro. Connect once and rerun Setup-AEC-Demo.cmd, or install/export Ubuntu in the managed machine image."
    }
    Write-Step "Install WSL2 distro: $Distro"
    Invoke-Checked 'wsl.exe' @('--install', '--distribution', $Distro, '--no-launch') @(0, 3010) | Out-Null
    $distros = Get-WslDistros
    if ($Distro -notin $distros) {
      Request-Reboot "Windows accepted the $Distro installation and must restart to finish it."
    }
  } else {
    Write-Host "Current: WSL distro $Distro"
  }

  Write-Step "Initialize $Distro and verify WSL2"
  Invoke-Checked 'wsl.exe' @('--set-version', $Distro, '2') | Out-Null
  Invoke-Checked 'wsl.exe' @('-d', $Distro, '-u', 'root', '-e', 'sh', '-lc', 'true') | Out-Null

  if (-not (Get-Command nvidia-smi.exe -ErrorAction SilentlyContinue)) {
    throw 'The Windows NVIDIA driver is missing or nvidia-smi.exe is unavailable. Install the current NVIDIA production driver, restart, then rerun Setup-AEC-Demo.cmd.'
  }
  $gpuLines = @(& wsl.exe -d $Distro -u root -e sh -lc "nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader")
  if ($LASTEXITCODE -ne 0 -or $gpuLines.Count -eq 0) {
    throw 'NVIDIA GPU passthrough is not working inside WSL2. Update the Windows NVIDIA driver and WSL kernel, restart, then rerun setup.'
  }
  if ($gpuLines.Count -lt 2) {
    throw "The tested local-model profile requires two visible NVIDIA GPUs (chat on GPU0, vision on GPU1); WSL2 reported $($gpuLines.Count)."
  }
  Write-Host "NVIDIA GPU passthrough: PASS ($($gpuLines.Count) GPUs)" -ForegroundColor Green

  if ($OfflineOnly -and -not $SkipVllm) {
    if (-not (Test-WslCommand 'command -v docker >/dev/null 2>&1 && command -v nvidia-ctk >/dev/null 2>&1')) {
      throw 'Offline setup cannot install missing Docker/NVIDIA Container Toolkit packages. Run connected Setup-AEC-Demo.cmd once, or use a managed WSL image that already contains them.'
    }
  }

  Write-Step 'Install and validate the AEC CPTX demo'
  $installer = Join-Path $RepoRoot 'Install-AEC-Demo.ps1'
  $installerArgs = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $installer, '-Tier', 'full', '-Yes', '-Distro', $Distro)
  if ($OfflineOnly) {
    $installerArgs += '-OfflineOnly'
  } else {
    $installerArgs += '-InstallDependencies'
    if (-not $SkipVllm) { $installerArgs += '-ProvisionVllm' }
  }
  if (-not $SkipVllm) { $installerArgs += '-StartVllm' }
  Invoke-Checked 'powershell.exe' $installerArgs | Out-Null

  Remove-ResumeAfterReboot
  Write-Host ''
  Write-Host 'AEC CPTX workstation setup completed successfully.' -ForegroundColor Green
  Write-Host 'Use the managed Desktop launchers for the rehearsed demos.'
  exit 0
} catch {
  Write-Host ''
  Write-Host ("ERROR: " + $_.Exception.Message) -ForegroundColor Red
  Write-Host "Setup log: $logPath" -ForegroundColor Yellow
  exit 1
} finally {
  try { Stop-Transcript | Out-Null } catch { }
}
