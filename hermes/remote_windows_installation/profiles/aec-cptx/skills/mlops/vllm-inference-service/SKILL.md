---
name: vllm-inference-service
description: "Production-grade vLLM LLM serving configuration and deployment patterns for the AEC CPTX ecosystem. Captures successful deployments, failure modes, and user-specific configuration requirements."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, windows]
tags: ["vllm", "inference", "serving", "mlops", "aec-cptx"]
---

# vLLM Inference Service Configuration

This skill consolidates proven deployment patterns for vLLM inference servers within the AEC CPTX environment, incorporating user-specific constraints and correction signals.

## Key Learnings from User Interaction

- User prefers **local inference endpoints** over external APIs when possible
- User requires **NVIDIA-specific configuration** due to ecosystem integration
- User needs **transparent error handling** for authentication failures
- User values **clear launch parameter documentation** for reproducibility

## Deployment Patterns

### Standard OpenAI-Compatible Deployment
```bash
# Basic deployment (7B-13B models)
vllm serve meta-llama/Llama-3-8B-Instruct \
  --gpu-memory-utilization 0.9 \
  --max-model-len 8192 \
  --port 8000 \
  --host 0.0.0.0

# Production deployment with metrics
vllm serve meta-llama/Llama-3-8B-Instruct \
  --gpu-memory-utilization 0.9 \
  --enable-prefix-caching \
  --enable-metrics \
  --metrics-port 9090 \
  --port 8000 \
  --host 0.0.0.0
```

### NVIDIA-Optimized Configuration
```bash
# NIM container deployment pattern
docker run --gpus all -p 8000:8000 \
  vllm/vllm-openai:latest \
  --model nvidia/zai-org/glm-5.2 \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.85 \
  --enable-chunked-prefill \
  --trust-remote-code
```

### Deployment Signatures
- **User Preference**: Local endpoint-first approach
- **GPU Memory Utilization**: Typically 0.85-0.9 for stable performance
- **Model Length**: 8192 tokens standard, configurable per task
- **Port Configuration**: 8000 for API, 9090 for metrics
- **Host Binding**: 0.0.0.0 for container accessibility

## Error Handling & Recovery

Common failure modes and fixes:

### Authentication Errors
```
Error: key not allowed to access model. This key can only access models=['default-models']
```
**Fix**: Configure dedicated API key with vLLM model access permissions via environment variable `HERMES_VLLM_NEMOTRON_API_KEY`

### SSL Certificate Verification Failures
```
SSLCertVerificationError: (1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed')
```
**Fix**: Disable certificate verification temporarily for self-signed certs:
```bash
export PYTHONHTTPSVERIFY=0
```

### GPU Memory Pressure
```
RuntimeError: CUDA out of memory
```
**Fix**: Adjust `--gpu-memory-utilization` between 0.7-0.9 and ensure `--max-model-len` is appropriate for model size

## Integration with AEC CPTX

### Environment Variables
```yaml
# ~/.hermes/profiles/aec-cptx/.env
HERMES_VLLM_NEMOTRON_API_KEY=your_api_key_here
```

### Skill Dependencies
- `mlops-inference` (parent category)
- `torch`, `transformers` (Python dependencies)
- `vllm` (core serving engine)

### Usage Examples
```python
# Simple inference call via OpenAI SDK pattern
from openai import OpenAI
client = OpenAI(
    base_url='http://localhost:8000/v1',
    api_key='EMPTY'  # vLLM accepts empty API keys
)
response = client.chat.completions.create(
    model='nvidia/zai-org/glm-5.2',
    messages=[{'role': 'user', 'content': 'Explain quantum computing'}]
)
```

---

## Version History
- **1.0.0** (2026-07-07): Initial release capturing user preference for local vLLM deployment and documented error recovery patterns