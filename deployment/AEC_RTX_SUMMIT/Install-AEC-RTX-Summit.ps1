#requires -Version 5.1
[CmdletBinding(SupportsShouldProcess = $true)]
param(
  [switch]$Yes,
  [switch]$SkipDependencies,
  [switch]$SkipPreflight,
  [switch]$SmokeTest,
  [string]$HermesHome = (Join-Path $env:LOCALAPPDATA 'hermes')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$PackageRoot = $PSScriptRoot
$BundledRepoRoot = Join-Path $PackageRoot 'payload\aec-demo'
$InstallRoot = Join-Path $env:LOCALAPPDATA 'AEC_RTX_SUMMIT'
$RepoRoot = Join-Path $InstallRoot 'aec-demo'
$DmlPayload = Join-Path $PackageRoot 'payload\daystrom-dml-source'
$DmlRoot = Join-Path $HermesHome 'integrations\daystrom-dml'
$DmlSource = Join-Path $DmlRoot 'source'
$DmlVenv = Join-Path $DmlRoot '.venv-dml'
$ComfyPayload = Join-Path $PackageRoot 'payload\comfyui-source'
$ComfyModelPayload = Join-Path $PackageRoot 'payload\comfyui-models'
$ApplicationInstallerRoot = Join-Path $PackageRoot 'payload\application-installers'
$ComfyRoot = Join-Path $env:USERPROFILE 'ComfyUI'
$LogRoot = Join-Path $env:ProgramData 'AEC_RTX_SUMMIT\logs'
$RhinoHero = @{
  RelativePath = 'demos\cliff_house\hero\cliff_house_HERO_RHINO_MODEL.3dm'
  Bytes = 15985322L
  Sha256 = '029a9b8e338a12c3babef2a7a2c95f385475c0ffe09da8700fa8ade8ab2ea637'
}
$ApplicationInstallers = @(
  @{
    Name = 'Rhino 8 core'
    RelativePath = 'rhino\rhino.msi'
    SignerPattern = 'ROBERT MCNEEL'
  },
  @{
    Name = 'Rhino 8 English language pack'
    RelativePath = 'rhino\LanguagePack-en-us.msi'
    SignerPattern = 'ROBERT MCNEEL'
  },
  @{
    Name = 'Blender 5.2 ARM64'
    RelativePath = 'blender\blender-5.2.0-windows-arm64.msi'
    SignerPattern = 'BLENDER'
  },
  @{
    Name = 'Blender 5.2 x64'
    RelativePath = 'blender\blender-5.2.0-windows-x64.msi'
    SignerPattern = 'BLENDER'
  }
)
$ComfyModels = @(
  @{
    RelativePath = 'diffusion_models\flux-2-klein-base-4b-fp8.safetensors'
    Bytes = 4089498488L
    Sha256 = '44bab3a86fe98b85d21dd2a4729ebdc3ae51fb8a39f76e457e18c724219e6840'
  },
  @{
    RelativePath = 'text_encoders\qwen_3_4b.safetensors'
    Bytes = 8044982048L
    Sha256 = '6c671498573ac2f7a5501502ccce8d2b08ea6ca2f661c458e708f36b36edfc5a'
  },
  @{
    RelativePath = 'vae\flux2-vae.safetensors'
    Bytes = 336213556L
    Sha256 = 'd64f3a68e1cc4f9f4e29b6e0da38a0204fe9a49f2d4053f0ec1fa1ca02f9c4b5'
  }
)

function Write-Step([string]$Message) {
  Write-Host ''
  Write-Host "==> $Message" -ForegroundColor Cyan
}

function Confirm-Action([string]$Message) {
  if ($Yes) { return $true }
  return (Read-Host "$Message [y/N]").Trim().ToLowerInvariant() -in @('y', 'yes')
}

function Ensure-NvidiaApiCredential {
  $profilePath = Join-Path $HermesHome 'profiles\aec-cptx'
  $envFile = Join-Path $profilePath '.env'
  $existing = if (Test-Path -LiteralPath $envFile -PathType Leaf) {
    Get-Content -LiteralPath $envFile -Raw
  } else {
    ''
  }
  if ($existing -match '(?m)^NVIDIA_API_KEY=\S+\s*$') {
    Write-Host 'Current: NVIDIA API credential is already configured for aec-cptx.'
    return
  }

  $credential = $env:NVIDIA_API_KEY
  if ([string]::IsNullOrWhiteSpace($credential)) {
    Write-Step 'Configure NVIDIA hosted-model access'
    $secure = Read-Host `
      'Enter the NVIDIA inference API key for GPT-5.6 Sol and Nemotron Omni' `
      -AsSecureString
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
      $credential = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    } finally {
      [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
  }
  if ([string]::IsNullOrWhiteSpace($credential)) {
    throw 'An NVIDIA inference API key is required. Setup cannot continue without one.'
  }
  if ($credential -match '\s') {
    throw 'The NVIDIA inference API key contains whitespace. Rerun setup and paste the key again.'
  }

  New-Item -ItemType Directory -Path $profilePath -Force | Out-Null
  $normalized = $existing.TrimEnd()
  if ($normalized) { $normalized += "`r`n" }
  [IO.File]::WriteAllText(
    $envFile,
    ($normalized + "NVIDIA_API_KEY=$credential`r`n"),
    [Text.UTF8Encoding]::new($false)
  )
  $env:NVIDIA_API_KEY = $credential
  Write-Host 'Configured NVIDIA API credential for the aec-cptx profile.'
}

function Invoke-Checked {
  param([string]$FilePath, [string[]]$ArgumentList)
  & $FilePath @ArgumentList
  if ($LASTEXITCODE -ne 0) { throw "$FilePath exited with code $LASTEXITCODE" }
}

function Resolve-Command {
  param([string]$Name, [string[]]$Candidates = @())
  $command = Get-Command $Name -ErrorAction SilentlyContinue
  if ($command) { return $command.Source }
  foreach ($candidate in $Candidates) {
    if (Test-Path -LiteralPath $candidate -PathType Leaf) { return $candidate }
  }
  return $null
}

function Install-WingetPackage {
  param([string]$Id, [string]$Label)
  if ($SkipDependencies) { throw "$Label is missing. Rerun without -SkipDependencies or install it manually." }
  $winget = Resolve-Command 'winget.exe'
  if (-not $winget) { throw "$Label is missing and winget.exe is unavailable." }
  if (-not (Confirm-Action "Install $Label with winget?")) { throw "$Label is required." }
  Invoke-Checked $winget @(
    'install', '--id', $Id, '-e',
    '--accept-package-agreements', '--accept-source-agreements'
  )
}

function Test-Http([string]$Uri) {
  try {
    $response = Invoke-WebRequest -UseBasicParsing -Uri $Uri -TimeoutSec 3
    return $response.StatusCode -ge 200 -and $response.StatusCode -lt 300
  } catch {
    return $false
  }
}

function Test-SignedInstaller {
  param([string]$Path, [string]$SignerPattern)
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $false }
  $signature = Get-AuthenticodeSignature -LiteralPath $Path
  $signer = if ($signature.SignerCertificate) { $signature.SignerCertificate.Subject } else { '' }
  return $signature.Status -eq 'Valid' -and $signer -match $SignerPattern
}

function Invoke-MsiInstall {
  param([string]$Path, [string]$Label)
  if (-not (Test-SignedInstaller $Path (
    $ApplicationInstallers | Where-Object { $_.Name -eq $Label } |
      Select-Object -ExpandProperty SignerPattern
  ))) {
    throw "Refusing to run an unsigned or unexpected $Label installer: $Path"
  }
  Write-Step "Install $Label from the verified offline payload"
  $process = Start-Process -FilePath 'msiexec.exe' -Verb RunAs -Wait -PassThru `
    -ArgumentList @('/i', "`"$Path`"", '/qn', '/norestart')
  if ($process.ExitCode -notin @(0, 3010, 1641)) {
    throw "$Label installation failed with Windows Installer code $($process.ExitCode)."
  }
  if ($process.ExitCode -in @(3010, 1641)) {
    Write-Host "$Label installed; Windows requested a restart." -ForegroundColor Yellow
  }
}

function Find-RhinoExecutable {
  $candidates = @(
    (Join-Path $env:ProgramFiles 'Rhino 8\System\Rhino.exe'),
    (Join-Path ${env:ProgramFiles(x86)} 'Rhino 8\System\Rhino.exe')
  ) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
  return $candidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } |
    Select-Object -First 1
}

function Find-BlenderExecutable {
  $roots = @($env:ProgramFiles, ${env:ProgramFiles(x86)}) |
    Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
  $candidates = foreach ($root in $roots) {
    Get-ChildItem -LiteralPath (Join-Path $root 'Blender Foundation') `
      -Filter 'blender.exe' -File -Recurse -ErrorAction SilentlyContinue
  }
  return $candidates | Sort-Object {
    try { [version]$_.VersionInfo.ProductVersion } catch { [version]'0.0' }
  } -Descending | Select-Object -ExpandProperty FullName -First 1
}

function Ensure-Rhino {
  $rhino = Find-RhinoExecutable
  if ($rhino) {
    Write-Host "Preserving existing Rhino installation: $rhino"
    return $rhino
  }
  if ($SkipDependencies) { throw 'Rhino 8 is missing and dependency installation was skipped.' }
  if (-not (Confirm-Action 'Install Rhino 8 from the bundled, signed offline installers?')) {
    throw 'Rhino 8 is required for the complete AEC workflow.'
  }
  $core = Join-Path $ApplicationInstallerRoot 'rhino\rhino.msi'
  $language = Join-Path $ApplicationInstallerRoot 'rhino\LanguagePack-en-us.msi'
  Invoke-MsiInstall $core 'Rhino 8 core'
  Invoke-MsiInstall $language 'Rhino 8 English language pack'
  $rhino = Find-RhinoExecutable
  if (-not $rhino) {
    throw 'Rhino 8 installation finished but Rhino.exe was not found. A Windows restart may be required.'
  }
  Write-Host 'Rhino was installed. Rhino account sign-in and license activation remain interactive.'
  return $rhino
}

function Ensure-Blender {
  $blender = Find-BlenderExecutable
  if ($blender) {
    Write-Host "Preserving existing Blender installation: $blender"
    return $blender
  }
  if ($SkipDependencies) { throw 'Blender is missing and dependency installation was skipped.' }
  if (-not (Confirm-Action 'Install Blender 5.2 from the bundled, signed offline installer?')) {
    throw 'Blender is required for the complete AEC workflow.'
  }
  $architecture = [Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()
  $relativePath = if ($architecture -eq 'Arm64') {
    'blender\blender-5.2.0-windows-arm64.msi'
  } elseif ($architecture -eq 'X64') {
    'blender\blender-5.2.0-windows-x64.msi'
  } else {
    throw "No bundled Blender installer supports Windows architecture $architecture."
  }
  $label = if ($architecture -eq 'Arm64') { 'Blender 5.2 ARM64' } else { 'Blender 5.2 x64' }
  Invoke-MsiInstall (Join-Path $ApplicationInstallerRoot $relativePath) $label
  $blender = Find-BlenderExecutable
  if (-not $blender) {
    throw 'Blender installation finished but blender.exe was not found. A Windows restart may be required.'
  }
  return $blender
}

function Get-Uv {
  $uv = Resolve-Command 'uv.exe' @(
    (Join-Path $env:USERPROFILE '.local\bin\uv.exe'),
    (Join-Path $env:LOCALAPPDATA 'Programs\uv\uv.exe')
  )
  if (-not $uv) {
    Install-WingetPackage 'astral-sh.uv' 'uv'
    $uv = Resolve-Command 'uv.exe' @(
      (Join-Path $env:USERPROFILE '.local\bin\uv.exe'),
      (Join-Path $env:LOCALAPPDATA 'Programs\uv\uv.exe')
    )
  }
  if (-not $uv) { throw 'uv was not found after installation.' }
  return $uv
}

function Ensure-Hermes {
  $hermes = Join-Path $HermesHome 'hermes-agent\venv\Scripts\hermes.exe'
  if (Test-Path -LiteralPath $hermes -PathType Leaf) { return $hermes }
  if ($SkipDependencies) { throw "Hermes is missing at $hermes." }
  if (-not (Confirm-Action 'Install Hermes Agent using the official Nous Research Windows installer?')) {
    throw 'Hermes Agent is required.'
  }
  $installerUri = 'https://hermes-agent.nousresearch.com/install.ps1'
  $temporary = Join-Path ([IO.Path]::GetTempPath()) "hermes-install-$([guid]::NewGuid().ToString('N')).ps1"
  try {
    Write-Step 'Download the official Hermes Agent installer'
    Invoke-WebRequest -UseBasicParsing -Uri $installerUri -OutFile $temporary
    Write-Step 'Install Hermes Agent (the AEC installer configures the profile afterward)'
    Invoke-Checked 'powershell.exe' @(
      '-NoProfile', '-ExecutionPolicy', 'Bypass',
      '-File', $temporary,
      '-SkipSetup'
    )
    Write-Host 'Hermes Agent installation completed; continuing with Ollama and Daystrom DML.'
  } finally {
    Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue
  }
  if (-not (Test-Path -LiteralPath $hermes -PathType Leaf)) {
    throw 'The official Hermes installer completed without producing the expected executable.'
  }
  return $hermes
}

function Ensure-Ollama {
  $ollama = Resolve-Command 'ollama.exe' @(
    (Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'),
    (Join-Path $env:ProgramFiles 'Ollama\ollama.exe')
  )
  if (-not $ollama) {
    Install-WingetPackage 'Ollama.Ollama' 'Ollama'
    $ollama = Resolve-Command 'ollama.exe' @(
      (Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'),
      (Join-Path $env:ProgramFiles 'Ollama\ollama.exe')
    )
  }
  if (-not $ollama) { throw 'Ollama was not found after installation.' }
  if (-not (Test-Http 'http://127.0.0.1:11434/api/version')) {
    Start-Process -FilePath $ollama -ArgumentList @('serve') -WindowStyle Hidden | Out-Null
    $deadline = (Get-Date).AddSeconds(30)
    do {
      Start-Sleep -Milliseconds 500
      $ready = Test-Http 'http://127.0.0.1:11434/api/version'
    } until ($ready -or (Get-Date) -gt $deadline)
    if (-not $ready) { throw 'Ollama did not become ready on http://127.0.0.1:11434.' }
  }
  $models = (& $ollama list | Out-String).ToLowerInvariant()
  if ($models -notmatch 'qwen3-embedding:0\.6b') {
    Write-Step 'Pull the compact DML embedding model'
    Invoke-Checked $ollama @('pull', 'qwen3-embedding:0.6b')
  } else {
    Write-Host 'Current: qwen3-embedding:0.6b'
  }
}

function Install-DaystromRuntime {
  $uv = Get-Uv
  if (-not (Test-Path -LiteralPath (Join-Path $DmlPayload 'pyproject.toml') -PathType Leaf)) {
    throw "Bundled Daystrom source is incomplete: $DmlPayload"
  }
  if (-not (Test-Path -LiteralPath (Join-Path $DmlSource 'pyproject.toml') -PathType Leaf)) {
    if ($PSCmdlet.ShouldProcess($DmlSource, 'Install bundled Daystrom source')) {
      New-Item -ItemType Directory -Path $DmlRoot -Force | Out-Null
      Copy-Item -LiteralPath $DmlPayload -Destination $DmlSource -Recurse
    }
  } else {
    Write-Host "Preserving existing Daystrom source: $DmlSource"
  }
  $dmlPython = Join-Path $DmlVenv 'Scripts\python.exe'
  if (-not (Test-Path -LiteralPath $dmlPython -PathType Leaf)) {
    Write-Step 'Create the isolated Daystrom Python runtime'
    Invoke-Checked $uv @('venv', $DmlVenv, '--python', '3.11')
  }
  Write-Step 'Install Daystrom DML/CMA dependencies'
  # The Summit memory path uses Ollama embeddings and does not need Daystrom's
  # optional CUDA extension. A machine with nvcc but without Visual C++ causes
  # setuptools to auto-enable that extension and then fail looking for cl.exe.
  $previousCudaBuild = $env:DML_BUILD_CUDA
  try {
    $env:DML_BUILD_CUDA = '0'
    Invoke-Checked $uv @('pip', 'install', '--python', $dmlPython, '--editable', "${DmlSource}[mcp]")
  } finally {
    if ($null -eq $previousCudaBuild) {
      Remove-Item Env:DML_BUILD_CUDA -ErrorAction SilentlyContinue
    } else {
      $env:DML_BUILD_CUDA = $previousCudaBuild
    }
  }
  Invoke-Checked $dmlPython @('-c', 'import daystrom_dml, dml_mcp, cma, mcp; print("Daystrom runtime imports: PASS")')

  $configDir = Join-Path $DmlRoot 'config'
  $binDir = Join-Path $DmlRoot 'bin'
  New-Item -ItemType Directory -Path $configDir, $binDir -Force | Out-Null
  Copy-Item -LiteralPath (Join-Path $PackageRoot 'aec-cptx-portable.yaml') `
    -Destination (Join-Path $configDir 'aec-cptx-portable.yaml') -Force
  Copy-Item -LiteralPath (Join-Path $PackageRoot 'hermes-dml-memory.cmd') `
    -Destination (Join-Path $binDir 'hermes-dml-memory.cmd') -Force
}

function Install-AecDemoPayload {
  if (-not (Test-Path -LiteralPath (Join-Path $BundledRepoRoot 'Install-AEC-Demo.ps1') -PathType Leaf)) {
    throw "AEC Summit payload is incomplete: $BundledRepoRoot"
  }
  Write-Step "Install the AEC demo payload to $RepoRoot"
  New-Item -ItemType Directory -Path $RepoRoot -Force | Out-Null
  foreach ($item in Get-ChildItem -LiteralPath $BundledRepoRoot -Force) {
    Copy-Item -LiteralPath $item.FullName -Destination $RepoRoot -Recurse -Force
  }
  if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot 'Install-AEC-Demo.ps1') -PathType Leaf)) {
    throw "The installed AEC demo payload is incomplete: $RepoRoot"
  }
}

function Test-ModelFile {
  param([string]$Path, [hashtable]$Model)
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $false }
  $file = Get-Item -LiteralPath $Path
  if ($file.Length -ne $Model.Bytes) { return $false }
  return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() -eq $Model.Sha256
}

function Get-BundledModelParts {
  param([hashtable]$Model)
  $basePath = Join-Path $ComfyModelPayload $Model.RelativePath
  return @(Get-ChildItem -LiteralPath (Split-Path -Parent $basePath) `
    -Filter ((Split-Path -Leaf $basePath) + '.part*') -File |
    Sort-Object Name)
}

function Install-BundledModel {
  param([hashtable]$Model, [string]$Target)
  $parts = @(Get-BundledModelParts $Model)
  $partBytes = [long](($parts | ForEach-Object { $_.Length } | Measure-Object -Sum).Sum)
  if ($parts.Count -eq 0 -or $partBytes -ne $Model.Bytes) {
    throw "Bundled ComfyUI model chunks are incomplete: $($Model.RelativePath)"
  }

  New-Item -ItemType Directory -Path (Split-Path -Parent $Target) -Force | Out-Null
  $temporary = "$Target.installing"
  $output = [IO.File]::Create($temporary)
  try {
    foreach ($part in $parts) {
      $input = [IO.File]::OpenRead($part.FullName)
      try { $input.CopyTo($output) } finally { $input.Dispose() }
    }
  } finally {
    $output.Dispose()
  }
  if (-not (Test-ModelFile $temporary $Model)) {
    Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue
    throw "Reassembled ComfyUI model failed integrity validation: $($Model.RelativePath)"
  }
  Move-Item -LiteralPath $temporary -Destination $Target -Force
}

function Get-ChunkedModelHash {
  param([hashtable]$Model)
  $parts = @(Get-BundledModelParts $Model)
  $sha = [Security.Cryptography.SHA256]::Create()
  $buffer = New-Object byte[] (16MB)
  try {
    foreach ($part in $parts) {
      $input = [IO.File]::OpenRead($part.FullName)
      try {
        while (($read = $input.Read($buffer, 0, $buffer.Length)) -gt 0) {
          [void]$sha.TransformBlock($buffer, 0, $read, $null, 0)
        }
      } finally {
        $input.Dispose()
      }
    }
    [void]$sha.TransformFinalBlock([byte[]]::new(0), 0, 0)
    return ([BitConverter]::ToString($sha.Hash)).Replace('-', '').ToLowerInvariant()
  } finally {
    $sha.Dispose()
  }
}

function Test-PortablePayload {
  $failures = [Collections.Generic.List[string]]::new()
  $requiredFiles = @(
    (Join-Path $BundledRepoRoot 'Install-AEC-Demo.ps1'),
    (Join-Path $ComfyPayload 'main.py'),
    (Join-Path $ComfyPayload 'requirements.txt'),
    (Join-Path $DmlPayload 'pyproject.toml'),
    (Join-Path $PackageRoot 'Start-ComfyUI.ps1'),
    (Join-Path $PackageRoot 'aec-cptx-portable.yaml'),
    (Join-Path $PackageRoot 'hermes-dml-memory.cmd'),
    (Join-Path $BundledRepoRoot $RhinoHero.RelativePath)
  )
  $requiredFiles += @($ApplicationInstallers | ForEach-Object {
    Join-Path $ApplicationInstallerRoot $_.RelativePath
  })
  foreach ($path in $requiredFiles) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
      $failures.Add("Missing required payload file: $path")
    }
  }
  $rhinoHeroPath = Join-Path $BundledRepoRoot $RhinoHero.RelativePath
  if (Test-Path -LiteralPath $rhinoHeroPath -PathType Leaf) {
    $heroFile = Get-Item -LiteralPath $rhinoHeroPath
    $heroHash = (Get-FileHash -LiteralPath $rhinoHeroPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($heroFile.Length -ne $RhinoHero.Bytes -or $heroHash -ne $RhinoHero.Sha256) {
      $failures.Add("Rhino HERO integrity mismatch: $rhinoHeroPath")
    } else {
      Write-Host "SMOKE_RHINO_HERO_PASS objects=559 bytes=$($heroFile.Length)"
    }
  }
  foreach ($installer in $ApplicationInstallers) {
    $path = Join-Path $ApplicationInstallerRoot $installer.RelativePath
    if (Test-Path -LiteralPath $path -PathType Leaf) {
      if (Test-SignedInstaller $path $installer.SignerPattern) {
        $bytes = (Get-Item -LiteralPath $path).Length
        Write-Host "SMOKE_INSTALLER_PASS name=$($installer.Name) bytes=$bytes"
      } else {
        $failures.Add("Installer signature verification failed: $($installer.Name)")
      }
    }
  }
  if (Test-Path -LiteralPath (Join-Path $BundledRepoRoot 'Install-AEC-Demo.ps1') -PathType Leaf) {
    $demoInstaller = Get-Content -LiteralPath (Join-Path $BundledRepoRoot 'Install-AEC-Demo.ps1') -Raw
    foreach ($marker in @(
      'AEC_CLIFFHOUSE_CLI.bat',
      'AEC Cliff House - Hermes CLI',
      'CLI_LAUNCHER_SMOKE_PASS',
      '--cli',
      'AEC_CLIFFHOUSE_HERMES.bat',
      'AEC Cliff House - Hermes.lnk',
      'Start-Hermes-AEC-Desktop.ps1'
    )) {
      if (-not $demoInstaller.Contains($marker)) {
        $failures.Add("Hermes launcher marker is missing from the bundled demo installer: $marker")
      }
    }
  }

  $scripts = @(Get-ChildItem -LiteralPath $PackageRoot -Filter '*.ps1' -File -Recurse)
  foreach ($script in $scripts) {
    $tokens = $null
    $parseErrors = $null
    [void][Management.Automation.Language.Parser]::ParseFile(
      $script.FullName, [ref]$tokens, [ref]$parseErrors
    )
    foreach ($parseError in @($parseErrors)) {
      $failures.Add("PowerShell parse failure: $($script.FullName): $($parseError.Message)")
    }
  }

  foreach ($model in $ComfyModels) {
    $parts = @(Get-BundledModelParts $model)
    $partBytes = [long](($parts | ForEach-Object { $_.Length } | Measure-Object -Sum).Sum)
    if ($parts.Count -eq 0 -or $partBytes -ne $model.Bytes) {
      $failures.Add("Incomplete model chunks: $($model.RelativePath)")
      continue
    }
    $actualHash = Get-ChunkedModelHash $model
    if ($actualHash -ne $model.Sha256) {
      $failures.Add("Model hash mismatch: $($model.RelativePath)")
    } else {
      Write-Host "SMOKE_MODEL_PASS name=$($model.RelativePath) parts=$($parts.Count) bytes=$partBytes"
    }
  }

  $smokeRoot = Join-Path ([IO.Path]::GetTempPath()) "aec-summit-smoke-$([guid]::NewGuid().ToString('N'))"
  try {
    $smallestModel = $ComfyModels | Sort-Object { $_.Bytes } | Select-Object -First 1
    $reassembled = Join-Path $smokeRoot $smallestModel.RelativePath
    Install-BundledModel $smallestModel $reassembled
    if (-not (Test-ModelFile $reassembled $smallestModel)) {
      $failures.Add("Disposable model reassembly failed: $($smallestModel.RelativePath)")
    } else {
      Write-Host "SMOKE_REASSEMBLY_PASS name=$($smallestModel.RelativePath)"
    }
  } catch {
    $failures.Add("Disposable model reassembly error: $($_.Exception.Message)")
  } finally {
    if (Test-Path -LiteralPath $smokeRoot) {
      Remove-Item -LiteralPath $smokeRoot -Recurse -Force
    }
  }

  $forbidden = @(Get-ChildItem -LiteralPath $PackageRoot -File -Recurse -Force | Where-Object {
    $_.Extension -in @('.safetensors', '.gguf', '.tar')
  })
  foreach ($file in $forbidden) {
    $failures.Add("Unexpected unsplit model/runtime payload: $($file.FullName)")
  }

  $checksumPath = Join-Path $PackageRoot 'SHA256SUMS.txt'
  if (-not (Test-Path -LiteralPath $checksumPath -PathType Leaf)) {
    $failures.Add("Missing checksum manifest: $checksumPath")
  } else {
    $packagePrefix = [IO.Path]::GetFullPath($PackageRoot).TrimEnd('\') + '\'
    $checksumCount = 0
    foreach ($line in Get-Content -LiteralPath $checksumPath) {
      if ($line -notmatch '^([0-9a-f]{64}) \*(.+)$') {
        $failures.Add("Malformed checksum entry: $line")
        continue
      }
      $expectedHash = $Matches[1]
      $relativePath = $Matches[2]
      $payloadPath = [IO.Path]::GetFullPath(
        (Join-Path $PackageRoot $relativePath.Replace('/', '\'))
      )
      if (-not $payloadPath.StartsWith($packagePrefix, [StringComparison]::OrdinalIgnoreCase)) {
        $failures.Add("Checksum path escapes package root: $relativePath")
        continue
      }
      if (-not (Test-Path -LiteralPath $payloadPath -PathType Leaf)) {
        $failures.Add("Checksum target is missing: $relativePath")
        continue
      }
      $actualHash = (Get-FileHash -LiteralPath $payloadPath -Algorithm SHA256).Hash.ToLowerInvariant()
      if ($actualHash -ne $expectedHash) {
        $failures.Add("Checksum mismatch: $relativePath")
      }
      $checksumCount++
    }
    Write-Host "SMOKE_CHECKSUM_PASS entries=$checksumCount"
  }

  if ($failures.Count -gt 0) {
    $failures | ForEach-Object { Write-Host "SMOKE_FAIL $_" -ForegroundColor Red }
    throw "Portable payload smoke test failed with $($failures.Count) error(s)."
  }
  Write-Host "AEC_INSTALLER_SMOKE_PASS scripts=$($scripts.Count) models=$($ComfyModels.Count) application_installers=$($ApplicationInstallers.Count) cli_launcher=true" -ForegroundColor Green
}

function Install-ComfyUI {
  if (-not (Test-Path -LiteralPath (Join-Path $ComfyPayload 'main.py') -PathType Leaf)) {
    throw "Bundled ComfyUI source is incomplete: $ComfyPayload"
  }
  foreach ($model in $ComfyModels) {
    $parts = @(Get-BundledModelParts $model)
    $partBytes = [long](($parts | ForEach-Object { $_.Length } | Measure-Object -Sum).Sum)
    if ($parts.Count -eq 0 -or $partBytes -ne $model.Bytes) {
      throw "Bundled ComfyUI model chunks are incomplete: $($model.RelativePath)"
    }
  }

  $targetDrive = [IO.DriveInfo]::new([IO.Path]::GetPathRoot($ComfyRoot))
  $missingModels = @($ComfyModels | Where-Object {
    -not (Test-ModelFile (Join-Path (Join-Path $ComfyRoot 'models') $_.RelativePath) $_)
  })
  $missingModelBytes = [long](($missingModels | ForEach-Object { $_.Bytes } | Measure-Object -Sum).Sum)
  $runtimeHeadroom = if (Test-Path -LiteralPath (Join-Path $ComfyRoot '.venv\Scripts\python.exe')) { 2GB } else { 8GB }
  $requiredBytes = $missingModelBytes + $runtimeHeadroom
  if ($targetDrive.AvailableFreeSpace -lt $requiredBytes) {
    throw ("ComfyUI installation needs at least {0:N1} GiB free; only {1:N1} GiB is available." -f
      ($requiredBytes / 1GB), ($targetDrive.AvailableFreeSpace / 1GB))
  }

  if (-not (Test-Path -LiteralPath (Join-Path $ComfyRoot 'main.py') -PathType Leaf)) {
    Write-Step "Install bundled ComfyUI source to $ComfyRoot"
    New-Item -ItemType Directory -Path (Split-Path -Parent $ComfyRoot) -Force | Out-Null
    Copy-Item -LiteralPath $ComfyPayload -Destination $ComfyRoot -Recurse
  } else {
    Write-Host "Preserving existing ComfyUI source: $ComfyRoot"
  }

  $uv = Get-Uv
  $comfyPython = Join-Path $ComfyRoot '.venv\Scripts\python.exe'
  if (-not (Test-Path -LiteralPath $comfyPython -PathType Leaf)) {
    Write-Step 'Create the isolated ComfyUI Python 3.13 runtime'
    Invoke-Checked $uv @('venv', (Join-Path $ComfyRoot '.venv'), '--python', '3.13')
  }
  Write-Step 'Install the ComfyUI CUDA 13 runtime'
  Invoke-Checked $uv @(
    'pip', 'install', '--python', $comfyPython,
    'torch', 'torchvision', 'torchaudio',
    '--index-url', 'https://download.pytorch.org/whl/cu130'
  )
  Invoke-Checked $uv @(
    'pip', 'install', '--python', $comfyPython,
    '--requirement', (Join-Path $ComfyRoot 'requirements.txt')
  )

  Write-Step 'Install and verify the bundled FLUX.2 Klein model set'
  foreach ($model in $ComfyModels) {
    $target = Join-Path (Join-Path $ComfyRoot 'models') $model.RelativePath
    if (Test-ModelFile $target $model) {
      Write-Host "COMFY_MODEL_PRESENT path=$target"
      continue
    }
    Install-BundledModel $model $target
    Write-Host "COMFY_MODEL_INSTALLED path=$target"
  }

  Copy-Item -LiteralPath (Join-Path $PackageRoot 'Start-ComfyUI.ps1') `
    -Destination (Join-Path $ComfyRoot 'Start-ComfyUI.ps1') -Force
  Write-Step 'Start ComfyUI and wait for its health endpoint'
  Invoke-Checked 'powershell.exe' @(
    '-NoProfile', '-ExecutionPolicy', 'Bypass',
    '-File', (Join-Path $ComfyRoot 'Start-ComfyUI.ps1'),
    '-ComfyRoot', $ComfyRoot
  )
}

if (-not (Test-Path -LiteralPath (Join-Path $BundledRepoRoot 'Install-AEC-Demo.ps1') -PathType Leaf)) {
  throw "AEC Summit payload is incomplete: $BundledRepoRoot"
}
if ($SmokeTest) {
  Test-PortablePayload
  exit 0
}

New-Item -ItemType Directory -Path $LogRoot -Force | Out-Null
$logPath = Join-Path $LogRoot ("install-{0}.log" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
Start-Transcript -Path $logPath -Force | Out-Null
try {
  Write-Host 'AEC RTX Summit deployment' -ForegroundColor Green
  Write-Host 'Inference: NVIDIA-hosted GPT-5.6 Sol Responses API (1.05M context)'
  Write-Host 'Vision:    NVIDIA-hosted Nemotron 3 Nano Omni (262K context)'
  Write-Host 'Memory:    Daystrom DML + qwen3-embedding:0.6b'
  Write-Host 'Imaging:   ComfyUI + bundled FLUX.2 Klein 4B model set'
  Write-Host 'CAD/DCC:   Bundled Rhino 8 + Blender 5.2 offline installers'
  Write-Host 'Excluded:  vLLM, Qwen chat/vision containers, unrelated model archives'

  Ensure-NvidiaApiCredential
  Ensure-Rhino | Out-Null
  Ensure-Blender | Out-Null
  if (-not (Resolve-Command 'git.exe')) { Install-WingetPackage 'Git.Git' 'Git' }
  if (-not (Resolve-Command 'python.exe') -and -not (Resolve-Command 'py.exe')) {
    Install-WingetPackage 'Python.Python.3.12' 'Python 3.12'
  }
  Ensure-Hermes | Out-Null
  Ensure-Ollama
  Install-DaystromRuntime
  Install-ComfyUI
  Install-AecDemoPayload

  Write-Step 'Configure the AEC Summit Hermes profile and Mission Control'
  $arguments = @(
    '-NoProfile', '-ExecutionPolicy', 'Bypass',
    '-File', (Join-Path $RepoRoot 'Install-AEC-Demo.ps1'),
    '-Tier', 'summit',
    '-DmlSourceDirectory', $DmlSource
  )
  if ($Yes) { $arguments += '-Yes' }
  if ($SkipPreflight) { $arguments += '-SkipPreflight' }
  Invoke-Checked 'powershell.exe' $arguments

  Write-Step 'Build the Hermes Windows frontend for the AEC profile'
  Invoke-Checked 'powershell.exe' @(
    '-NoProfile', '-ExecutionPolicy', 'Bypass',
    '-File', (Join-Path $HermesHome 'bin\Start-Hermes-AEC-Desktop.ps1'),
    '-BuildOnly'
  )

  Write-Host ''
  Write-Host 'AEC RTX Summit deployment is ready.' -ForegroundColor Green
  Write-Host 'Rhino 8 and Blender 5.2 are installed; Rhino licensing may still require sign-in.'
  Write-Host 'ComfyUI and the verified FLUX.2 Klein model set are installed and ready.'
  Write-Host "Installer log: $logPath"
  exit 0
} catch {
  Write-Host ''
  Write-Host ("ERROR: " + $_.Exception.Message) -ForegroundColor Red
  Write-Host "Installer log: $logPath" -ForegroundColor Yellow
  exit 1
} finally {
  try { Stop-Transcript | Out-Null } catch { }
}
