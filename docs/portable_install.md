# Portable and offline installation

The Windows bootstrapper can run directly from an NTFS or exFAT USB drive.
It records the drive's current repository path in `AEC_DEMO_ROOT`, installs
managed launchers, creates only missing Hermes profiles, and runs preflight.
If the drive letter changes, rerun `Install-AEC-Demo.cmd` from the drive.

## Connected installation

From the repository root on the target Windows machine:

```powershell
.\Install-AEC-Demo.cmd -InstallDependencies -Configure -ProvisionVllm -StartVllm
```

This path may use Winget, Ubuntu package repositories, Docker registries,
Hugging Face, and Ollama. Model downloads happen only when the corresponding
cache is absent.

## Build a portable drive

Run this on a configured online/reference machine:

```powershell
.\New-AEC-PortableBundle.ps1 -Destination E:\AEC-CPTX
```

That copies only Git-tracked repository files. It excludes live credentials,
sessions, logs, caches, `.git`, and other untracked machine state.

To prepare vLLM for disconnected use, first confirm both models run on the
reference machine, then include the Docker image and Hugging Face cache:

```powershell
.\New-AEC-PortableBundle.ps1 `
  -Destination E:\AEC-CPTX `
  -IncludeVllmRuntime `
  -IncludeOllamaModels
```

On the current reference machine the vLLM image is about 9 GB and the two
Hugging Face model caches total about 43 GB. Use a drive with at least 64 GiB
free; 128 GB or larger is recommended when repository and Ollama assets are
included. FAT32 is not supported because individual archives exceed 4 GB.

To refresh tracked installer files and the manifest after a source-only
update without exporting the large payload again, reuse the existing assets:

```powershell
.\New-AEC-PortableBundle.ps1 `
  -Destination E:\AEC-CPTX `
  -IncludeVllmRuntime `
  -IncludeOllamaModels `
  -ReuseExistingAssets
```

The builder requires the existing archives and Ollama store to be present and
rehashes the runtime archives before writing the refreshed manifest.

## Disconnected installation

The target must already have:

- Windows with `wsl.exe` and an Ubuntu WSL2 distro;
- a compatible Windows NVIDIA driver with WSL GPU passthrough;
- Docker Engine and NVIDIA Container Toolkit inside that distro;
- Windows Python for preflight and Windows Hermes for agent profiles.

Those operating-system and driver prerequisites are not safely portable as a
generic bundle. Prepare them while connected, or use a managed machine image.

With prerequisites present, run from the prepared drive:

```powershell
E:\AEC-CPTX\Install-AEC-Demo.cmd -OfflineOnly -StartVllm
```

The installer verifies each manifest size and SHA-256 checksum, loads the
bundled Docker image when absent, restores both model
snapshots into WSL's Hugging Face cache, optionally merges bundled Ollama model
files, creates missing profiles, installs launchers, and verifies the selected
tier. `-OfflineOnly` rejects switches that inherently require the network.

If Daystrom DML is already installed under the standard Hermes integration
directory, the installer and managed launchers validate its `pyproject.toml`
and set `DML_SOURCE_DIR` to that source checkout automatically. The DML store
remains the separate path declared by the Daystrom integration configuration.
For managed demo profiles, an older `retrieval_policy: conditional` value is
backed up and migrated to the required `always` policy; no other live profile
configuration is replaced.

## Security and repeatability

- Live `config.yaml`, `.env`, API keys, DML stores, and sessions are never
  copied into the bundle.
- Existing managed launcher files are backed up before replacement.
- Existing Hermes profiles are never overwritten.
- The bundle manifest records the source commit, archive sizes, and optional
  SHA-256 checksums.
- Rerunning the installer is supported; cached images and model snapshots are
  not restored again when already present.

Before relying on a drive for a demo, perform the end-to-end smoke test on a
separate target: launcher installation, WSL asset restore, both `/v1/models`
endpoints, one real inference request per model, Hermes profile startup, and
DML memory status.
