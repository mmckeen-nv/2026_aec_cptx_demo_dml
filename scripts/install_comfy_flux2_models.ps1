[CmdletBinding()]
param(
    [string]$ComfyRoot = (Join-Path $HOME 'ComfyUI'),
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

$models = @(
    @{
        Name = 'flux-2-klein-base-4b-fp8.safetensors'
        RelativePath = 'models\diffusion_models\flux-2-klein-base-4b-fp8.safetensors'
        Url = 'https://huggingface.co/black-forest-labs/FLUX.2-klein-base-4b-fp8/resolve/main/flux-2-klein-base-4b-fp8.safetensors'
        Bytes = 4089498488L
        Sha256 = '44bab3a86fe98b85d21dd2a4729ebdc3ae51fb8a39f76e457e18c724219e6840'
    },
    @{
        Name = 'qwen_3_4b.safetensors'
        RelativePath = 'models\text_encoders\qwen_3_4b.safetensors'
        Url = 'https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/text_encoders/qwen_3_4b.safetensors'
        Bytes = 8044982048L
        Sha256 = '6c671498573ac2f7a5501502ccce8d2b08ea6ca2f661c458e708f36b36edfc5a'
    },
    @{
        Name = 'flux2-vae.safetensors'
        RelativePath = 'models\vae\flux2-vae.safetensors'
        Url = 'https://huggingface.co/Comfy-Org/flux2-dev/resolve/main/split_files/vae/flux2-vae.safetensors'
        Bytes = 336213556L
        Sha256 = 'd64f3a68e1cc4f9f4e29b6e0da38a0204fe9a49f2d4053f0ec1fa1ca02f9c4b5'
    }
)

if (-not (Test-Path -LiteralPath $ComfyRoot -PathType Container)) {
    throw "ComfyUI root does not exist: $ComfyRoot"
}

foreach ($model in $models) {
    $target = Join-Path $ComfyRoot $model.RelativePath
    $part = "$target.part"
    $directory = Split-Path -Parent $target
    New-Item -ItemType Directory -Path $directory -Force | Out-Null

    $valid = $false
    if (-not $Force -and (Test-Path -LiteralPath $target -PathType Leaf)) {
        $file = Get-Item -LiteralPath $target
        if ($file.Length -eq $model.Bytes) {
            $hash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
            $valid = $hash -eq $model.Sha256
        }
    }
    if ($valid) {
        Write-Host "COMFY_MODEL_PRESENT name=$($model.Name) path=$target"
        continue
    }

    if ($Force -and (Test-Path -LiteralPath $part)) {
        Remove-Item -LiteralPath $part -Force
    }
    Write-Host "COMFY_MODEL_DOWNLOAD name=$($model.Name) bytes=$($model.Bytes)"
    $curlArgs = @('-L', '--fail', '--retry', '5', '--retry-delay', '2')
    if (Test-Path -LiteralPath $part) {
        $curlArgs += @('-C', '-')
    }
    $curlArgs += @('-o', $part, $model.Url)
    & curl.exe @curlArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Download failed for $($model.Name) with curl exit code $LASTEXITCODE"
    }

    $download = Get-Item -LiteralPath $part
    if ($download.Length -ne $model.Bytes) {
        throw "Size mismatch for $($model.Name): actual=$($download.Length) expected=$($model.Bytes)"
    }
    $downloadHash = (Get-FileHash -LiteralPath $part -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($downloadHash -ne $model.Sha256) {
        throw "SHA-256 mismatch for $($model.Name): actual=$downloadHash expected=$($model.Sha256)"
    }
    Move-Item -LiteralPath $part -Destination $target -Force
    Write-Host "COMFY_MODEL_INSTALLED name=$($model.Name) path=$target"
}

Write-Host 'COMFY_FLUX2_MODELS_PASS count=3'
