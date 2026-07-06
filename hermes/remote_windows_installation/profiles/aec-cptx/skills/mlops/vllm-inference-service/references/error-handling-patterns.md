# vLLM Error Handling Patterns for AEC CPTX

This reference captures specific error scenarios encountered during vLLM deployment in the Hermes environment.

## Authentication Error Recovery

### Scenario
```
Error code: 401 - {'error': {'message': \"key not allowed to access model. This key can only access models=['default-models']. Tried to access vllm\", 'type': 'key_model_access_denied', 'param': 'model', 'code': '401'}}
```

### Root Cause
The `HERMES_VLLM_NEMOTRON_API_KEY` environment variable was set but not properly configured for vLLM model access.

### Solution Steps
1. Verify the API key format and permissions
2. Confirm the key targets the correct model group
3. Test connectivity with curl:
   ```bash
   curl -H "Authorization: Bearer *** $HERMES_HOME/.env | grep HERMES_VLLM_NEMOTRON_API_KEY | cut -d '=' -f2 | tr -d '\n')" \
        https://inference-api.nvidia.com/v1/models
   ```

### Permanent Fix
Add to `$HERMES_HOME/profiles/aec-cptx/config.yaml`:
```yaml
vllm:
  model_group: nvidia/zai-org
  api_key: ${HERMES_VLLM_NEMOTRON_API_KEY}
```

## SSL Certificate Issues

### Problem
```
SSLCertVerificationError: (1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain')
```

### Workarounds
1. Temporary (session):
   ```bash
   export PYTHONHTTPSVERIFY=0
   ```
2. Permanent (config.yaml):
   ```yaml
   security:
     ssl_verify: false  # WARNING: reduces security
   ```

3. Recommended: Import NVIDIA certificate into trusted store:
   ```bash
   sudo cp ./nvidia-root-ca.crt /usr/local/share/ca-certificates/
   sudo update-ca-certificates
   ```

## GPU Memory Optimization

### OOM Recovery Pattern
When encountering `CUDA out of memory`:
1. Reduce `--gpu-memory-utilization` incrementally (0.9 → 0.85 → 0.8)
2. Decrease `--max-model-len` proportionally to model size
3. Enable chunked prefill for better memory management:
   ```bash
   --enable-chunked-prefill
   ```

### Verification Script
`scripts/check-gpu-utilization.sh`:
```bash
#!/bin/bash
echo "GPU Utilization: $(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits)%"
echo "Memory Usage: $(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader -l 1 | tr '\n' '/')"
```

## Performance Tuning Checklist

- [ ] `--gpu-memory-utilization` set to 0.85-0.9
- [ ] `--max-model-len` appropriate for model size (8192 standard)
- [ ] `--port` mapped correctly (8000 for API)
- [ ] SSL certificate path verified
- [ ] API key has `model` scope for target models