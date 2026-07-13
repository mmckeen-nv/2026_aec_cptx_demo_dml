# WSL2 vLLM deployment — agent instructions

This directory is the source of truth for standing up the two vLLM model
containers that the `aec-cptx` and `bac_teapot` Hermes profiles depend on
(chat model on port 8000, vision model on port 8001, both inside a WSL2
Ubuntu distro on the Windows host). Read this whole file before touching
WSL2 or Docker on a new machine — it exists so an agent (or a human) can
rebuild this setup from zero without re-discovering the DNS-crash pitfall
the hard way.

## Architecture recap

```
Windows host (native)
├── Hermes profiles (aec-cptx, bac_teapot, default) — run natively,
│   NOT inside WSL2. They just point their model config at
│   http://localhost:8000/v1 and http://localhost:8001/v1.
└── WSL2 Ubuntu distro
    └── Docker Engine + NVIDIA Container Toolkit
        ├── vllm-qwen36           chat model    :8000  GPU0
        └── vllm-nemotron-vision  vision model  :8001  GPU1
```

Windows automatically forwards `localhost:8000`/`localhost:8001` into the
WSL2 distro's Docker port bindings — no extra port-proxy config needed on a
standard WSL2 install.

Files in this directory:

| File | Purpose | Run from |
|---|---|---|
| `provision-wsl2.sh` | One-time (idempotent) WSL2 setup: Docker Engine + NVIDIA Container Toolkit + GPU passthrough verification + image pull | inside WSL2 |
| `run-vllm-qwen36.sh` | Create/start the chat model container | inside WSL2 |
| `run-vllm-nemotron-vision.sh` | Create/start the vision model container | inside WSL2 |
| `status-vllm.sh` | Print container status + hit both `/v1/models` endpoints | inside WSL2 |
| `stop-vllm.sh` | Stop both containers, free GPU memory | inside WSL2 |
| `start_vllm.bat` | Windows Desktop launcher: `docker start` both containers + poll until ready | Windows (double-click or `cmd.exe /c`) |
| `stop_vllm.bat` | Windows Desktop launcher: stop both containers | Windows |
| `check_vllm.bat` | Windows Desktop launcher: status check, no side effects | Windows |

## Building out WSL2 from scratch (new machine, or after a WSL2 reset)

1. Confirm a WSL2 Ubuntu distro exists and has NVIDIA GPU passthrough:
   ```
   wsl -l -v                     # from Windows — confirm "Ubuntu" is VERSION 2
   wsl -e nvidia-smi              # from Windows — confirms GPU passthrough works
   ```
   If `nvidia-smi` fails inside WSL2, that's a Windows-side NVIDIA driver /
   WSL2 kernel issue — fix that first (update the Windows NVIDIA driver;
   WSL2 GPU passthrough does NOT need a separate Linux NVIDIA driver
   inside the distro, only the Windows host driver + a recent WSL2 kernel).
   This is out of scope for the scripts here.

2. Copy this whole `wsl-vllm/` directory somewhere reachable from inside
   WSL2. The easiest path is to just read it directly off the Windows
   mount, no copying needed:
   ```
   wsl -d Ubuntu
   cd /mnt/c/Users/<windows-user>/<repo>/deployment/wsl-vllm
   ```

3. Run the provisioning script:
   ```
   bash provision-wsl2.sh
   ```
   This installs Docker Engine + NVIDIA Container Toolkit if missing,
   configures Docker's nvidia runtime, verifies GPU access from inside a
   container, and pulls `vllm/vllm-openai:latest`. It is safe to re-run —
   every step checks for existing state first.

4. Start each model container for the first time (this triggers the HF
   weight download — can take a while depending on network speed and
   model size):
   ```
   bash run-vllm-qwen36.sh
   bash run-vllm-nemotron-vision.sh
   ```
   Watch progress with `docker logs -f vllm-qwen36` (or `-nemotron-vision`)
   in another terminal. Wait for `Application startup complete.` in the
   logs, or poll `curl http://localhost:8000/v1/models` until it returns
   HTTP 200 with a JSON model list.

5. Verify both:
   ```
   bash status-vllm.sh
   ```

6. From here on, day-to-day start/stop should go through the Windows
   .bat launchers (copy them to the Desktop, or run them directly from
   this repo path) — see below. They call `docker start`/`docker stop` on
   the already-configured containers, which is much faster than
   recreating them from scratch every time.

## Day-to-day usage (containers already provisioned)

From Windows:
```
deployment\wsl-vllm\start_vllm.bat   # starts both, polls until ready (~1-2min typical, up to 4min on cold cache)
deployment\wsl-vllm\check_vllm.bat   # status only, no side effects
deployment\wsl-vllm\stop_vllm.bat    # stops both, frees GPU memory
```

Or equivalently, from inside WSL2:
```
bash run-vllm-qwen36.sh              # idempotent: docker start if it exists
bash run-vllm-nemotron-vision.sh
bash status-vllm.sh
bash stop-vllm.sh
```

## Known pitfall: DNS-flake crash-loop on vllm-qwen36 startup

**Symptom:** `vllm-qwen36` exits shortly after `docker start`, with a
traceback ending in either:
```
httpx.ConnectError: [Errno -3] Temporary failure in name resolution
```
or
```
RuntimeError: Cannot send a request, as the client has been closed.
```
(the second is a downstream symptom of the first — vLLM's HF metadata
fetch times out/fails mid-flight and leaves the httpx client in a bad
state, which then blows up model_config construction).

**Root cause:** vLLM calls `get_hf_image_processor_config` (via
`transformers.utils.hub.cached_file`) on every single startup to refresh
image-processor metadata from huggingface.co — even when the model weights
are already fully cached locally and no download is actually needed. On
this machine's WSL2 networking, that specific outbound DNS/HTTPS call is
intermittently flaky, and when it fails, the whole container startup
crashes instead of falling back to the local cache.

**Fix (already baked into the run scripts):** when the required model snapshot
exists, set both `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1` as container
env vars. This forces vLLM/transformers/huggingface_hub to load everything
from the persistent local HF cache and skip the network metadata call. On a
fresh online installation the scripts leave offline mode disabled so the
initial model download can succeed. A portable bundle restores the snapshots
before container creation, so disconnected starts select offline mode.

**If you ever recreate the container by hand and forget these env vars,**
you will hit this crash loop again. Diagnose it the same way we did
originally:
```
docker logs vllm-qwen36 2>&1 | tail -40           # look for the httpx/DNS traceback
wsl -e bash -lc 'getent hosts huggingface.co'      # sanity-check DNS from WSL2 host side
docker exec vllm-qwen36 ls /root/.cache/huggingface/hub   # confirm weights ARE cached
```
If weights are cached and DNS is the culprit, `docker rm -f vllm-qwen36`
and re-run `bash run-vllm-qwen36.sh` (which has the fix built in), or add
the two env vars to whatever `docker run` invocation you're using.

The vision container (`vllm-nemotron-vision`) has not been observed to hit
this in practice, but the same fix applies if it ever does — see the
comment block at the top of `run-vllm-nemotron-vision.sh`.

## Other pitfalls / gotchas

- **Stray native (non-Docker) vLLM process squatting on a port.** If
  `docker start vllm-qwen36` fails with `address already in use` on
  port 8000/8001, something else already has that port bound — check with
  `wsl -e bash -lc "ss -tlnp | grep -E ':(8000|8001)'"` and
  `ps aux | grep vllm` inside WSL2. On this machine we found (and killed,
  with user confirmation) a leftover native `python -m
  vllm.entrypoints.openai.api_server` process serving an unrelated model
  on port 8000. Always confirm with the user before killing an unfamiliar
  process — it might be intentional.

- **GPU pinning.** `vllm-nemotron-vision` is pinned to GPU 1 via
  `CUDA_VISIBLE_DEVICES=1` / `NVIDIA_VISIBLE_DEVICES=1` so it never
  contends with the chat model on GPU 0. `vllm-qwen36` sees all GPUs
  (`--gpus all`, no pinning env var) but only uses one due to
  `--tensor-parallel-size 1` — it happens to land on GPU 0 in practice.
  If you ever see both models competing for the same GPU, check these env
  vars first.

- **Cold start time.** Both models load weights, run `torch.compile`, and
  capture CUDA graphs on every fresh container start (this state is NOT
  persisted across container stop/start in the current setup, only the HF
  weight cache is). Expect 1-2 minutes typical, up to ~3 minutes if the
  torch compile cache is cold. The polling loop in `start_vllm.bat` /
  `run-vllm-*.sh` accounts for this — don't shorten the timeout without
  testing several cold starts first.

- **`docker start` vs recreate.** Always prefer `docker start` (what the
  idempotent run scripts and .bat launchers do) over `docker rm` +
  `docker run` for routine start/stop. Recreating loses nothing
  functionally (weights are on a persistent volume) but is unnecessary
  churn and slightly slower. Only recreate when you're intentionally
  changing a `docker run` flag (model, port, GPU pinning, env vars) — use
  `--recreate` on the run scripts for that.

- **Configured port present but container detached from Docker bridge.** A
  container can remain `Up` while `.NetworkSettings.Networks` is empty. In
  that state the model listens inside the container, but Windows receives a
  connection error because the configured published port is not effective.
  `start_vllm.bat` reconnects the container to `bridge` and restarts it so
  Docker reapplies the port. It also accepts `--no-pause` for profile
  launchers and uses an stdin-independent delay for noninteractive polling.

## Verification checklist after any change here

1. `bash status-vllm.sh` (or `check_vllm.bat` from Windows) — both
   containers `Up`, both `/v1/models` return HTTP 200 with the expected
   model id.
2. A real inference call against each, not just `/v1/models`:
   ```
   curl http://localhost:8000/v1/chat/completions -H "Content-Type: application/json" \
     -d '{"model":"nvidia/Qwen3.6-35B-A3B-NVFP4","messages":[{"role":"user","content":"say pong"}],"max_tokens":5}'
   curl http://localhost:8001/v1/chat/completions -H "Content-Type: application/json" \
     -d '{"model":"nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-NVFP4","messages":[{"role":"user","content":"say pong"}],"max_tokens":5}'
   ```
3. If you touched `run-vllm-qwen36.sh`, do at least 2 full cold starts
   (`docker rm -f vllm-qwen36 && bash run-vllm-qwen36.sh`, twice) to make
   sure the DNS-flake crash from the "Known pitfall" section above doesn't
   resurface — it was intermittent, so one clean start does not prove the
   fix still holds.
