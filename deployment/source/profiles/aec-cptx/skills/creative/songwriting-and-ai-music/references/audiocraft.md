# AudioCraft: Audio Generation

Comprehensive guide to using Meta's AudioCraft for text-to-music and text-to-audio generation with MusicGen, AudioGen, and EnCodec.

## When to use AudioCraft

**Use AudioCraft when:**
- Need to generate music from text descriptions
- Creating sound effects and environmental audio
- Building music generation applications
- Need melody-conditioned music generation
- Want stereo audio output
- Require controllable music generation with style transfer

**Key features:**
- **MusicGen**: Text-to-music generation with melody conditioning
- **AudioGen**: Text-to-sound effects generation
- **EnCodec**: High-fidelity neural audio codec
- **Multiple model sizes**: Small (300M) to Large (3.3B)
- **Stereo support**: Full stereo audio generation
- **Style conditioning**: MusicGen-Style for reference-based generation

**Use alternatives instead:**
- **Stable Audio**: For longer commercial music generation
- **Bark**: For text-to-speech with music/sound effects
- **Riffusion**: For spectogram-based music generation
- **OpenAI Jukebox**: For raw audio generation with lyrics

## Quick start

### Installation

```bash
# From PyPI
pip install audiocraft

# From GitHub (latest)
pip install git+https://github.com/facebookresearch/audiocraft.git

# Or use HuggingFace Transformers
pip install transformers torch torchaudio
```

### Basic text-to-music (AudioCraft)

```python
import torchaudio
from audiocraft.models import MusicGen

# Load model
model = MusicGen.get_pretrained('facebook/musicgen-small')

# Set generation parameters
model.set_generation_params(
    duration=8,  # seconds
    top_k=250,
    temperature=1.0
)

# Generate from text
descriptions = ["happy upbeat electronic dance music with synths"]
wav = model.generate(descriptions)

# Save audio
torchaudio.save("output.wav", wav[0].cpu(), sample_rate=32000)
```

### Using HuggingFace Transformers

```python
from transformers import AutoProcessor, MusicgenForConditionalGeneration
import scipy

# Load model and processor
processor = AutoProcessor.from_pretrained("facebook/musicgen-small")
model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-small")
model.to("cuda")

# Generate music
inputs = processor(
    text=["80s pop track with bassy drums and synth"],
    padding=True,
    return_tensors="pt"
).to("cuda")

audio_values = model.generate(
    **inputs,
    do_sample=True,
    guidance_scale=3,
    max_new_tokens=256
)

# Save
sampling_rate = model.config.audio_encoder.sampling_rate
scipy.io.wavfile.write("output.wav", rate=sampling_rate, data=audio_values[0, 0].cpu().numpy())
```

### Text-to-sound with AudioGen

```python
from audiocraft.models import AudioGen

# Load AudioGen
model = AudioGen.get_pretrained('facebook/audiogen-medium')

model.set_generation_params(duration=5)

# Generate sound effects
descriptions = ["dog barking in a park with birds chirping"]
wav = model.generate(descriptions)

torchaudio.save("sound.wav", wav[0].cpu(), sample_rate=16000)
```

## Core concepts

### Architecture overview

```
AudioCraft Architecture:
┌──────────────────────────────────────────────────────────────┐
│                    Text Encoder (T5)                          │
│                         │                                     │
│                    Text Embeddings                            │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│              Transformer Decoder (LM)                         │
│     Auto-regressively generates audio tokens                  │
│     Using efficient token interleaving patterns               │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                EnCodec Audio Decoder                          │
│        Converts tokens back to audio waveform                 │
└──────────────────────────────────────────────────────────────┘
```

### Model variants

| Model | Size | Description | Use Case |
|-------|------|-------------|----------|
| `musicgen-small` | 300M | Text-to-music | Quick generation |
| `musicgen-medium` | 1.5B | Text-to-music | Balanced |
| `musicgen-large` | 3.3B | Text-to-music | Best quality |
| `musicgen-melody` | 1.5B | Text + melody | Melody conditioning |
| `musicgen-melody-large` | 3.3B | Text + melody | Best melody |
| `musicgen-stereo-*` | Varies | Stereo output | Stereo generation |
| `musicgen-style` | 1.5B | Style transfer | Reference-based |
| `audiogen-medium` | 1.5B | Text-to-sound | Sound effects |

### Generation parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `duration` | 8.0 | Length in seconds (1-120) |
| `top_k` | 250 | Top-k sampling |
| `top_p` | 0.0 | Nucleus sampling (0 = disabled) |
| `temperature` | 1.0 | Sampling temperature |
| `cfg_coef` | 3.0 | Classifier-free guidance |

## MusicGen usage

### Text-to-music generation

```python
from audiocraft.models import MusicGen
import torchaudio

model = MusicGen.get_pretrained('facebook/musicgen-medium')

# Configure generation
model.set_generation_params(
    duration=30,          # Up to 30 seconds
    top_k=250,            # Sampling diversity
    top_p=0.0,            # 0 = use top_k only
    temperature=1.0,      # Creativity (higher = more varied)
    cfg_coef=3.0          # Text adherence (higher = stricter)
)

# Generate multiple samples
descriptions = [
    "epic orchestral soundtrack with strings and brass",
    "chill lo-fi hip hop beat with jazzy piano",
    "energetic rock song with electric guitar"
]

# Generate (returns [batch, channels, samples])
wav = model.generate(descriptions)

# Save each
for i, audio in enumerate(wav):
    torchaudio.save(f"music_{i}.wav", audio.cpu(), sample_rate=32000)
```

### Melody-conditioned generation

```python
from audiocraft.models import MusicGen
import torchaudio

# Load melody model
model = MusicGen.get_pretrained('facebook/musicgen-melody')
model.set_generation_params(duration=30)

# Load melody audio
melody, sr = torchaudio.load("melody.wav")

# Generate with melody conditioning
descriptions = ["acoustic guitar folk song"]
wav = model.generate_with_chroma(descriptions, melody, sr)

torchaudio.save("melody_conditioned.wav", wav[0].cpu(), sample_rate=32000)
```

### Stereo generation

```python
from audiocraft.models import MusicGen

# Load stereo model
model = MusicGen.get_pretrained('facebook/musicgen-stereo-medium')
model.set_generation_params(duration=15)

descriptions = ["ambient electronic music with wide stereo panning"]
wav = model.generate(descriptions)

# wav shape: [batch, 2, samples] for stereo
print(f"Stereo shape: {wav.shape}")  # [1, 2, 480000]
torchaudio.save("stereo.wav", wav[0].cpu(), sample_rate=32000)
```

### Audio continuation

```python
from transformers import AutoProcessor, MusicgenForConditionalGeneration

processor = AutoProcessor.from_pretrained("facebook/musicgen-medium")
model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-medium")

# Load audio to continue
import torchaudio
audio, sr = torchaudio.load("intro.wav")

# Process with text and audio
inputs = processor(
    audio=audio.squeeze().numpy(),
    sampling_rate=sr,
    text=["continue with a epic chorus"],
    padding=True,
    return_tensors="pt"
)

# Generate continuation
audio_values = model.generate(**inputs, do_sample=True, guidance_scale=3, max_new_tokens=512)
```

## MusicGen-Style usage

### Style-conditioned generation

```python
from audiocraft.models import MusicGen

# Load style model
model = MusicGen.get_pretrained('facebook/musicgen-style')

# Configure generation with style
model.set_generation_params(
    duration=30,
    cfg_coef=3.0,
    cfg_coef_beta=5.0  # Style influence
)

# Configure style conditioner
model.set_style_conditioner_params(
    eval_q=3,          # RVQ quantizers (1-6)
    excerpt_length=3.0  # Style excerpt length
)

# Load style reference
style_audio, sr = torchaudio.load("reference_style.wav")

# Generate with text + style
descriptions = ["upbeat dance track"]
wav = model.generate_with_style(descriptions, style_audio, sr)
```

### Style-only generation (no text)

```python
# Generate matching style without text prompt
model.set_generation_params(
    duration=30,
    cfg_coef=3.0,
    cfg_coef_beta=None  # Disable double CFG for style-only
)

wav = model.generate_with_style([None], style_audio, sr)
```

## AudioGen usage

### Sound effect generation

```python
from audiocraft.models import AudioGen
import torchaudio

model = AudioGen.get_pretrained('facebook/audiogen-medium')
model.set_generation_params(duration=10)

# Generate various sounds
descriptions = [
    "thunderstorm with heavy rain and lightning",
    "busy city traffic with car horns",
    "ocean waves crashing on rocks",
    "crackling campfire in forest"
]

wav = model.generate(descriptions)

for i, audio in enumerate(wav):
    torchaudio.save(f"sound_{i}.wav", audio.cpu(), sample_rate=16000)
```

## EnCodec usage

### Audio compression

```python
from audiocraft.models import CompressionModel
import torch
import torchaudio

# Load EnCodec
model = CompressionModel.get_pretrained('facebook/encodec_32khz')

# Load audio
wav, sr = torchaudio.load("audio.wav")

# Ensure correct sample rate
if sr != 32000:
    resampler = torchaudio.transforms.Resample(sr, 32000)
    wav = resampler(wav)

# Encode to tokens
with torch.no_grad():
    encoded = model.encode(wav.unsqueeze(0))
    codes = encoded[0]  # Audio codes

# Decode back to audio
with torch.no_grad():
    decoded = model.decode(codes)

torchaudio.save("reconstructed.wav", decoded[0].cpu(), sample_rate=32000)
```

## Common workflows

### Workflow 1: Music generation pipeline

```python
import torch
import torchaudio
from audiocraft.models import MusicGen

class MusicGenerator:
    def __init__(self, model_name="facebook/musicgen-medium"):
        self.model = MusicGen.get_pretrained(model_name)
        self.sample_rate = 32000

    def generate(self, prompt, duration=30, temperature=1.0, cfg=3.0):
        self.model.set_generation_params(
            duration=duration,
            top_k=250,
            temperature=temperature,
            cfg_coef=cfg
        )

        with torch.no_grad():
            wav = self.model.generate([prompt])

        return wav[0].cpu()

    def generate_batch(self, prompts, duration=30):
        self.model.set_generation_params(duration=duration)

        with torch.no_grad():
            wav = self.model.generate(prompts)

        return wav.cpu()

    def save(self, audio, path):
        torchaudio.save(path, audio, sample_rate=self.sample_rate)

# Usage
generator = MusicGenerator()
audio = generator.generate(
    "epic cinematic orchestral music",
    duration=30,
    temperature=1.0
)
generator.save(audio, "epic_music.wav")
```

### Workflow 2: Sound design batch processing

```python
import json
from pathlib import Path
from audiocraft.models import AudioGen
import torchaudio

def batch_generate_sounds(sound_specs, output_dir):
    """
    Generate multiple sounds from specifications.

    Args:
        sound_specs: list of {"name": str, "description": str, "duration": float}
        output_dir: output directory path
    """
    model = AudioGen.get_pretrained('facebook/audiogen-medium')
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    results = []

    for spec in sound_specs:
        model.set_generation_params(duration=spec.get("duration", 5))

        wav = model.generate([spec["description"]])

        output_path = output_dir / f"{spec['name']}.wav"
        torchaudio.save(str(output_path), wav[0].cpu(), sample_rate=16000)

        results.append({
            "name": spec["name"],
            "path": str(output_path),
            "description": spec["description"]
        })

    return results

# Usage
sounds = [
    {"name": "explosion", "description": "massive explosion with debris", "duration": 3},
    {"name": "footsteps", "description": "footsteps on wooden floor", "duration": 5},
    {"name": "door", "description": "wooden door creaking and closing", "duration": 2}
]

results = batch_generate_sounds(sounds, "sound_effects/")
```

### Workflow 3: Gradio demo

```python
import gradio as gr
import torch
import torchaudio
from audiocraft.models import MusicGen

model = MusicGen.get_pretrained('facebook/musicgen-small')

def generate_music(prompt, duration, temperature, cfg_coef):
    model.set_generation_params(
        duration=duration,
        temperature=temperature,
        cfg_coef=cfg_coef
    )

    with torch.no_grad():
        wav = model.generate([prompt])

    # Save to temp file
    path = "temp_output.wav"
    torchaudio.save(path, wav[0].cpu(), sample_rate=32000)
    return path

demo = gr.Interface(
    fn=generate_music,
    inputs=[
        gr.Textbox(label="Music Description", placeholder="upbeat electronic dance music"),
        gr.Slider(1, 30, value=8, label="Duration (seconds)"),
        gr.Slider(0.5, 2.0, value=1.0, label="Temperature"),
        gr.Slider(1.0, 10.0, value=3.0, label="CFG Coefficient")
    ],
    outputs=gr.Audio(label="Generated Music"),
    title="MusicGen Demo"
)

demo.launch()
```

## Performance optimization

### Memory optimization

```python
# Use smaller model
model = MusicGen.get_pretrained('facebook/musicgen-small')

# Clear cache between generations
torch.cuda.empty_cache()

# Generate shorter durations
model.set_generation_params(duration=10)  # Instead of 30

# Use half precision
model = model.half()
```

### Batch processing efficiency

```python
# Process multiple prompts at once (more efficient)
descriptions = ["prompt1", "prompt2", "prompt3", "prompt4"]
wav = model.generate(descriptions)  # Single batch

# Instead of
for desc in descriptions:
    wav = model.generate([desc])  # Multiple batches (slower)
```

### GPU memory requirements

| Model | FP32 VRAM | FP16 VRAM |
|-------|-----------|-----------|
| musicgen-small | ~4GB | ~2GB |
| musicgen-medium | ~8GB | ~4GB |
| musicgen-large | ~16GB | ~8GB |

## Common issues

| Issue | Solution |
|-------|----------|
| CUDA OOM | Use smaller model, reduce duration |
| Poor quality | Increase cfg_coef, better prompts |
| Generation too short | Check max duration setting |
| Audio artifacts | Try different temperature |
| Stereo not working | Use stereo model variant |

## Resources

- **GitHub**: https://github.com/facebookresearch/audiocraft
- **Paper (MusicGen)**: https://arxiv.org/abs/2306.05284
- **Paper (AudioGen)**: https://arxiv.org/abs/2209.15352
- **HuggingFace**: https://huggingface.co/facebook/musicgen-small
- **Demo**: https://huggingface.co/spaces/facebook/MusicGen

---

# AudioCraft Advanced Usage Guide

## Fine-tuning MusicGen

### Custom dataset preparation

```python
import os
import json
from pathlib import Path
import torchaudio

def prepare_dataset(audio_dir, output_dir, metadata_file):
    """
    Prepare dataset for MusicGen fine-tuning.

    Directory structure:
    output_dir/
    ├── audio/
    │   ├── 0001.wav
    │   ├── 0002.wav
    │   └── ...
    └── metadata.json
    """
    output_dir = Path(output_dir)
    audio_output = output_dir / "audio"
    audio_output.mkdir(parents=True, exist_ok=True)

    # Load metadata (format: {"path": "...", "description": "..."})
    with open(metadata_file) as f:
        metadata = json.load(f)

    processed = []

    for idx, item in enumerate(metadata):
        audio_path = Path(audio_dir) / item["path"]

        # Load and resample to 32kHz
        wav, sr = torchaudio.load(str(audio_path))
        if sr != 32000:
            resampler = torchaudio.transforms.Resample(sr, 32000)
            wav = resampler(wav)

        # Convert to mono if stereo
        if wav.shape[0] > 1:
            wav = wav.mean(dim=0, keepdim=True)

        # Save processed audio
        output_path = audio_output / f"{idx:04d}.wav"
        torchaudio.save(str(output_path), wav, sample_rate=32000)

        processed.append({
            "path": str(output_path.relative_to(output_dir)),
            "description": item["description"],
            "duration": wav.shape[1] / 32000
        })

    # Save processed metadata
    with open(output_dir / "metadata.json", "w") as f:
        json.dump(processed, f, indent=2)

    print(f"Processed {len(processed)} samples")
    return processed
```

### Fine-tuning with dora

```bash
# AudioCraft uses dora for experiment management
# Install dora
pip install dora-search

# Clone AudioCraft
git clone https://github.com/facebookresearch/audiocraft.git
cd audiocraft

# Create config for fine-tuning
cat > config/solver/musicgen/finetune.yaml << 'EOF'
defaults:
  - musicgen/musicgen_base
  - /model: lm/musicgen_lm
  - /conditioner: cond_base

solver: musicgen
autocast: true
autocast_dtype: float16

optim:
  epochs: 100
  batch_size: 4
  lr: 1e-4
  ema: 0.999
  optimizer: adamw

dataset:
  batch_size: 4
  num_workers: 4
  train:
    - dset: your_dataset
      root: /path/to/dataset
  valid:
    - dset: your_dataset
      root: /path/to/dataset

checkpoint:
  save_every: 10
  keep_every_states: null
EOF

# Run fine-tuning
dora run solver=musicgen/finetune
```

### LoRA fine-tuning

```python
from peft import LoraConfig, get_peft_model
from audiocraft.models import MusicGen
import torch

# Load base model
model = MusicGen.get_pretrained('facebook/musicgen-small')

# Get the language model component
lm = model.lm

# Configure LoRA
lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=["q_proj", "v_proj", "k_proj", "out_proj"],
    lora_dropout=0.05,
    bias="none"
)

# Apply LoRA
lm = get_peft_model(lm, lora_config)
lm.print_trainable_parameters()
```

## Multi-GPU Training

### DataParallel

```python
import torch
import torch.nn as nn
from audiocraft.models import MusicGen

model = MusicGen.get_pretrained('facebook/musicgen-small')

# Wrap LM with DataParallel
if torch.cuda.device_count() > 1:
    model.lm = nn.DataParallel(model.lm)

model.to("cuda")
```

### DistributedDataParallel

```python
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP

def setup(rank, world_size):
    dist.init_process_group("nccl", rank=rank, world_size=world_size)
    torch.cuda.set_device(rank)

def train(rank, world_size):
    setup(rank, world_size)

    model = MusicGen.get_pretrained('facebook/musicgen-small')
    model.lm = model.lm.to(rank)
    model.lm = DDP(model.lm, device_ids=[rank])

    # Training loop
    # ...

    dist.destroy_process_group()
```

## Custom Conditioning

### Adding new conditioners

```python
from audiocraft.modules.conditioners import BaseConditioner
import torch

class CustomConditioner(BaseConditioner):
    """Custom conditioner for additional control signals."""

    def __init__(self, dim, output_dim):
        super().__init__(dim, output_dim)
        self.embed = torch.nn.Linear(dim, output_dim)

    def forward(self, x):
        return self.embed(x)

    def tokenize(self, x):
        # Tokenize input for conditioning
        return x

# Use with MusicGen
from audiocraft.models.builders import get_lm_model

# Modify model config to include custom conditioner
# This requires editing the model configuration
```

### Melody conditioning internals

```python
from audiocraft.models import MusicGen
from audiocraft.modules.codebooks_patterns import DelayedPatternProvider
import torch

model = MusicGen.get_pretrained('facebook/musicgen-melody')

# Access chroma extractor
chroma_extractor = model.lm.condition_provider.conditioners.get('chroma')

# Manual chroma extraction
def extract_chroma(audio, sr):
    """Extract chroma features from audio."""
    import librosa

    # Compute chroma
    chroma = librosa.feature.chroma_cqt(y=audio.numpy(), sr=sr)

    return torch.from_numpy(chroma).float()

# Use extracted chroma for conditioning
chroma = extract_chroma(melody_audio, sample_rate)
```

## EnCodec Deep Dive

### Custom compression settings

```python
from audiocraft.models import CompressionModel
import torch

# Load EnCodec
encodec = CompressionModel.get_pretrained('facebook/encodec_32khz')

# Access codec parameters
print(f"Sample rate: {encodec.sample_rate}")
print(f"Channels: {encodec.channels}")
print(f"Cardinality: {encodec.cardinality}")  # Codebook size
print(f"Num codebooks: {encodec.num_codebooks}")
print(f"Frame rate: {encodec.frame_rate}")

# Encode with specific bandwidth
# Lower bandwidth = more compression, lower quality
encodec.set_target_bandwidth(6.0)  # 6 kbps

audio = torch.randn(1, 1, 32000)  # 1 second
encoded = encodec.encode(audio)
decoded = encodec.decode(encoded[0])
```

### Streaming encoding

```python
import torch
from audiocraft.models import CompressionModel

encodec = CompressionModel.get_pretrained('facebook/encodec_32khz')

def encode_streaming(audio_stream, chunk_size=32000):
    """Encode audio in streaming fashion."""
    all_codes = []

    for chunk in audio_stream:
        # Ensure chunk is right shape
        if chunk.dim() == 1:
            chunk = chunk.unsqueeze(0).unsqueeze(0)

        with torch.no_grad():
            codes = encodec.encode(chunk)[0]
            all_codes.append(codes)

    return torch.cat(all_codes, dim=-1)

def decode_streaming(codes_stream, output_stream):
    """Decode codes in streaming fashion."""
    for codes in codes_stream:
        with torch.no_grad():
            audio = encodec.decode(codes)
            output_stream.write(audio.cpu().numpy())
```

## MultiBand Diffusion

### Using MBD for enhanced quality

```python
from audiocraft.models import MusicGen, MultiBandDiffusion

# Load MusicGen
model = MusicGen.get_pretrained('facebook/musicgen-medium')

# Load MultiBand Diffusion
mbd = MultiBandDiffusion.get_mbd_musicgen()

model.set_generation_params(duration=10)

# Generate with standard decoder
descriptions = ["epic orchestral music"]
wav_standard = model.generate(descriptions)

# Generate tokens and use MBD decoder
with torch.no_grad():
    # Get tokens
    gen_tokens = model.generate_tokens(descriptions)

    # Decode with MBD
    wav_mbd = mbd.tokens_to_wav(gen_tokens)

# Compare quality
print(f"Standard shape: {wav_standard.shape}")
print(f"MBD shape: {wav_mbd.shape}")
```

## API Server Deployment

### FastAPI server

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import torch
import torchaudio
from audiocraft.models import MusicGen
import io
import base64

app = FastAPI()

# Load model at startup
model = None

@app.on_event("startup")
async def load_model():
    global model
    model = MusicGen.get_pretrained('facebook/musicgen-small')
    model.set_generation_params(duration=10)

class GenerateRequest(BaseModel):
    prompt: str
    duration: float = 10.0
    temperature: float = 1.0
    cfg_coef: float = 3.0

class GenerateResponse(BaseModel):
    audio_base64: str
    sample_rate: int
    duration: float

@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")

    try:
        model.set_generation_params(
            duration=min(request.duration, 30),
            temperature=request.temperature,
            cfg_coef=request.cfg_coef
        )

        with torch.no_grad():
            wav = model.generate([request.prompt])

        # Convert to bytes
        buffer = io.BytesIO()
        torchaudio.save(buffer, wav[0].cpu(), sample_rate=32000, format="wav")
        buffer.seek(0)

        audio_base64 = base64.b64encode(buffer.read()).decode()

        return GenerateResponse(
            audio_base64=audio_base64,
            sample_rate=32000,
            duration=wav.shape[-1] / 32000
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": model is not None}

# Run: uvicorn server:app --host 0.0.0.0 --port 8000
```

### Batch processing service

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
import torch
from audiocraft.models import MusicGen

class MusicGenService:
    def __init__(self, model_name='facebook/musicgen-small', max_workers=2):
        self.model = MusicGen.get_pretrained(model_name)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.lock = asyncio.Lock()

    async def generate_async(self, prompt, duration=10):
        """Async generation with thread pool."""
        loop = asyncio.get_event_loop()

        def _generate():
            with torch.no_grad():
                self.model.set_generation_params(duration=duration)
                return self.model.generate([prompt])

        # Run in thread pool
        wav = await loop.run_in_executor(self.executor, _generate)
        return wav[0].cpu()

    async def generate_batch_async(self, prompts, duration=10):
        """Process multiple prompts concurrently."""
        tasks = [self.generate_async(p, duration) for p in prompts]
        return await asyncio.gather(*tasks)

# Usage
service = MusicGenService()

async def main():
    prompts = ["jazz piano", "rock guitar", "electronic beats"]
    results = await service.generate_batch_async(prompts)
    return results
```

## Integration Patterns

### LangChain tool

```python
from langchain.tools import BaseTool
import torch
import torchaudio
from audiocraft.models import MusicGen
import tempfile

class MusicGeneratorTool(BaseTool):
    name = "music_generator"
    description = "Generate music from a text description. Input should be a detailed description of the music style, mood, and instruments."

    def __init__(self):
        super().__init__()
        self.model = MusicGen.get_pretrained('facebook/musicgen-small')
        self.model.set_generation_params(duration=15)

    def _run(self, description: str) -> str:
        with torch.no_grad():
            wav = self.model.generate([description])

        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            torchaudio.save(f.name, wav[0].cpu(), sample_rate=32000)
            return f"Generated music saved to: {f.name}"

    async def _arun(self, description: str) -> str:
        return self._run(description)
```

### Gradio with advanced controls

```python
import gradio as gr
import torch
import torchaudio
from audiocraft.models import MusicGen

models = {}

def load_model(model_size):
    if model_size not in models:
        model_name = f"facebook/musicgen-{model_size}"
        models[model_size] = MusicGen.get_pretrained(model_name)
    return models[model_size]

def generate(prompt, duration, temperature, cfg_coef, top_k, model_size):
    model = load_model(model_size)

    model.set_generation_params(
        duration=duration,
        temperature=temperature,
        cfg_coef=cfg_coef,
        top_k=top_k
    )

    with torch.no_grad():
        wav = model.generate([prompt])

    # Save
    path = "output.wav"
    torchaudio.save(path, wav[0].cpu(), sample_rate=32000)
    return path

demo = gr.Interface(
    fn=generate,
    inputs=[
        gr.Textbox(label="Prompt", lines=3),
        gr.Slider(1, 30, value=10, label="Duration (s)"),
        gr.Slider(0.1, 2.0, value=1.0, label="Temperature"),
        gr.Slider(0.5, 10.0, value=3.0, label="CFG Coefficient"),
        gr.Slider(50, 500, value=250, step=50, label="Top-K"),
        gr.Dropdown(["small", "medium", "large"], value="small", label="Model Size")
    ],
    outputs=gr.Audio(label="Generated Music"),
    title="MusicGen Advanced",
    allow_flagging="never"
)

demo.launch(share=True)
```

## Audio Processing Pipeline

### Post-processing chain

```python
import torch
import torchaudio
import torchaudio.transforms as T
import numpy as np

class AudioPostProcessor:
    def __init__(self, sample_rate=32000):
        self.sample_rate = sample_rate

    def normalize(self, audio, target_db=-14.0):
        """Normalize audio to target loudness."""
        rms = torch.sqrt(torch.mean(audio ** 2))
        target_rms = 10 ** (target_db / 20)
        gain = target_rms / (rms + 1e-8)
        return audio * gain

    def fade_in_out(self, audio, fade_duration=0.1):
        """Apply fade in/out."""
        fade_samples = int(fade_duration * self.sample_rate)

        # Create fade curves
        fade_in = torch.linspace(0, 1, fade_samples)
        fade_out = torch.linspace(1, 0, fade_samples)

        # Apply fades
        audio[..., :fade_samples] *= fade_in
        audio[..., -fade_samples:] *= fade_out

        return audio

    def apply_reverb(self, audio, decay=0.5):
        """Apply simple reverb effect."""
        impulse = torch.zeros(int(self.sample_rate * 0.5))
        impulse[0] = 1.0
        impulse[int(self.sample_rate * 0.1)] = decay * 0.5
        impulse[int(self.sample_rate * 0.2)] = decay * 0.25

        # Convolve
        audio = torch.nn.functional.conv1d(
            audio.unsqueeze(0),
            impulse.unsqueeze(0).unsqueeze(0),
            padding=len(impulse) // 2
        ).squeeze(0)

        return audio

    def process(self, audio):
        """Full processing pipeline."""
        audio = self.normalize(audio)
        audio = self.fade_in_out(audio)
        return audio

# Usage with MusicGen
from audiocraft.models import MusicGen

model = MusicGen.get_pretrained('facebook/musicgen-small')
model.set_generation_params(duration=10)

wav = model.generate(["chill ambient music"])
processor = AudioPostProcessor()
wav_processed = processor.process(wav[0].cpu())

torchaudio.save("processed.wav", wav_processed, sample_rate=32000)
```

## Evaluation

### Audio quality metrics

```python
import torch
from audiocraft.metrics import CLAPTextConsistencyMetric
from audiocraft.data.audio import audio_read

def evaluate_generation(audio_path, text_prompt):
    """Evaluate generated audio quality."""
    # Load audio
    wav, sr = audio_read(audio_path)

    # CLAP consistency (text-audio alignment)
    clap_metric = CLAPTextConsistencyMetric()
    clap_score = clap_metric.compute(wav, [text_prompt])

    return {
        "clap_score": clap_score,
        "duration": wav.shape[-1] / sr
    }

# Batch evaluation
def evaluate_batch(generations):
    """Evaluate multiple generations."""
    results = []
    for gen in generations:
        result = evaluate_generation(gen["path"], gen["prompt"])
        result["prompt"] = gen["prompt"]
        results.append(result)

    # Aggregate
    avg_clap = sum(r["clap_score"] for r in results) / len(results)
    return {
        "individual": results,
        "average_clap": avg_clap
    }
```

## Model Comparison

### MusicGen variants benchmark

| Model | CLAP Score | Generation Time (10s) | VRAM |
|-------|------------|----------------------|------|
| musicgen-small | 0.35 | ~5s | 2GB |
| musicgen-medium | 0.42 | ~15s | 4GB |
| musicgen-large | 0.48 | ~30s | 8GB |
| musicgen-melody | 0.45 | ~15s | 4GB |
| musicgen-stereo-medium | 0.41 | ~18s | 5GB |

### Prompt engineering tips

```python
# Good prompts - specific and descriptive
good_prompts = [
    "upbeat electronic dance music with synthesizer leads and punchy drums at 128 bpm",
    "melancholic piano ballad with strings, slow tempo, emotional and cinematic",
    "funky disco groove with slap bass, brass section, and rhythmic guitar"
]

# Bad prompts - too vague
bad_prompts = [
    "nice music",
    "song",
    "good beat"
]

# Structure: [mood] [genre] with [instruments] at [tempo/style]
```


---

# AudioCraft Troubleshooting Guide

## Installation Issues

### Import errors

**Error**: `ModuleNotFoundError: No module named 'audiocraft'`

**Solutions**:
```bash
# Install from PyPI
pip install audiocraft

# Or from GitHub
pip install git+https://github.com/facebookresearch/audiocraft.git

# Verify installation
python -c "from audiocraft.models import MusicGen; print('OK')"
```

### FFmpeg not found

**Error**: `RuntimeError: ffmpeg not found`

**Solutions**:
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows (using conda)
conda install -c conda-forge ffmpeg

# Verify
ffmpeg -version
```

### PyTorch CUDA mismatch

**Error**: `RuntimeError: CUDA error: no kernel image is available`

**Solutions**:
```bash
# Check CUDA version
nvcc --version
python -c "import torch; print(torch.version.cuda)"

# Install matching PyTorch
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# For CUDA 11.8
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### xformers issues

**Error**: `ImportError: xformers` related errors

**Solutions**:
```bash
# Install xformers for memory efficiency
pip install xformers

# Or disable xformers
export AUDIOCRAFT_USE_XFORMERS=0

# In Python
import os
os.environ["AUDIOCRAFT_USE_XFORMERS"] = "0"
from audiocraft.models import MusicGen
```

## Model Loading Issues

### Out of memory during load

**Error**: `torch.cuda.OutOfMemoryError` during model loading

**Solutions**:
```python
# Use smaller model
model = MusicGen.get_pretrained('facebook/musicgen-small')

# Force CPU loading first
import torch
device = "cpu"
model = MusicGen.get_pretrained('facebook/musicgen-small', device=device)
model = model.to("cuda")

# Use HuggingFace with device_map
from transformers import MusicgenForConditionalGeneration
model = MusicgenForConditionalGeneration.from_pretrained(
    "facebook/musicgen-small",
    device_map="auto"
)
```

### Download failures

**Error**: Connection errors or incomplete downloads

**Solutions**:
```python
# Set cache directory
import os
os.environ["AUDIOCRAFT_CACHE_DIR"] = "/path/to/cache"

# Or for HuggingFace
os.environ["HF_HOME"] = "/path/to/hf_cache"

# Resume download
from huggingface_hub import snapshot_download
snapshot_download("facebook/musicgen-small", resume_download=True)

# Use local files
model = MusicGen.get_pretrained('/local/path/to/model')
```

### Wrong model type

**Error**: Loading wrong model for task

**Solutions**:
```python
# For text-to-music: use MusicGen
from audiocraft.models import MusicGen
model = MusicGen.get_pretrained('facebook/musicgen-medium')

# For text-to-sound: use AudioGen
from audiocraft.models import AudioGen
model = AudioGen.get_pretrained('facebook/audiogen-medium')

# For melody conditioning: use melody variant
model = MusicGen.get_pretrained('facebook/musicgen-melody')

# For stereo: use stereo variant
model = MusicGen.get_pretrained('facebook/musicgen-stereo-medium')
```

## Generation Issues

### Empty or silent output

**Problem**: Generated audio is silent or very quiet

**Solutions**:
```python
import torch

# Check output
wav = model.generate(["upbeat music"])
print(f"Shape: {wav.shape}")
print(f"Max amplitude: {wav.abs().max().item()}")
print(f"Mean amplitude: {wav.abs().mean().item()}")

# If too quiet, normalize
def normalize_audio(audio, target_db=-14.0):
    rms = torch.sqrt(torch.mean(audio ** 2))
    target_rms = 10 ** (target_db / 20)
    gain = target_rms / (rms + 1e-8)
    return audio * gain

wav_normalized = normalize_audio(wav)
```

### Poor quality output

**Problem**: Generated music sounds bad or noisy

**Solutions**:
```python
# Use larger model
model = MusicGen.get_pretrained('facebook/musicgen-large')

# Adjust generation parameters
model.set_generation_params(
    duration=15,
    top_k=250,          # Increase for more diversity
    temperature=0.8,    # Lower for more focused output
    cfg_coef=4.0        # Increase for better text adherence
)

# Use better prompts
# Bad: "music"
# Good: "upbeat electronic dance music with synthesizers and punchy drums"

# Try MultiBand Diffusion
from audiocraft.models import MultiBandDiffusion
mbd = MultiBandDiffusion.get_mbd_musicgen()
tokens = model.generate_tokens(["prompt"])
wav = mbd.tokens_to_wav(tokens)
```

### Generation too short

**Problem**: Audio shorter than expected

**Solutions**:
```python
# Check duration setting
model.set_generation_params(duration=30)  # Set before generate

# Verify in generation
print(f"Duration setting: {model.generation_params}")

# Check output shape
wav = model.generate(["prompt"])
actual_duration = wav.shape[-1] / 32000
print(f"Actual duration: {actual_duration}s")

# Note: max duration is typically 30s
```

### Melody conditioning fails

**Error**: Issues with melody-conditioned generation

**Solutions**:
```python
import torchaudio
from audiocraft.models import MusicGen

# Load melody model (not base model)
model = MusicGen.get_pretrained('facebook/musicgen-melody')

# Load and prepare melody
melody, sr = torchaudio.load("melody.wav")

# Resample to model sample rate if needed
if sr != 32000:
    resampler = torchaudio.transforms.Resample(sr, 32000)
    melody = resampler(melody)

# Ensure correct shape [batch, channels, samples]
if melody.dim() == 1:
    melody = melody.unsqueeze(0).unsqueeze(0)
elif melody.dim() == 2:
    melody = melody.unsqueeze(0)

# Convert stereo to mono
if melody.shape[1] > 1:
    melody = melody.mean(dim=1, keepdim=True)

# Generate with melody
model.set_generation_params(duration=min(melody.shape[-1] / 32000, 30))
wav = model.generate_with_chroma(["piano cover"], melody, 32000)
```

## Memory Issues

### CUDA out of memory

**Error**: `torch.cuda.OutOfMemoryError: CUDA out of memory`

**Solutions**:
```python
import torch

# Clear cache before generation
torch.cuda.empty_cache()

# Use smaller model
model = MusicGen.get_pretrained('facebook/musicgen-small')

# Reduce duration
model.set_generation_params(duration=10)  # Instead of 30

# Generate one at a time
for prompt in prompts:
    wav = model.generate([prompt])
    save_audio(wav)
    torch.cuda.empty_cache()

# Use CPU for very large generations
model = MusicGen.get_pretrained('facebook/musicgen-small', device="cpu")
```

### Memory leak during batch processing

**Problem**: Memory grows over time

**Solutions**:
```python
import gc
import torch

def generate_with_cleanup(model, prompts):
    results = []

    for prompt in prompts:
        with torch.no_grad():
            wav = model.generate([prompt])
            results.append(wav.cpu())

        # Cleanup
        del wav
        gc.collect()
        torch.cuda.empty_cache()

    return results

# Use context manager
with torch.inference_mode():
    wav = model.generate(["prompt"])
```

## Audio Format Issues

### Wrong sample rate

**Problem**: Audio plays at wrong speed

**Solutions**:
```python
import torchaudio

# MusicGen outputs at 32kHz
sample_rate = 32000

# AudioGen outputs at 16kHz
sample_rate = 16000

# Always use correct rate when saving
torchaudio.save("output.wav", wav[0].cpu(), sample_rate=sample_rate)

# Resample if needed
resampler = torchaudio.transforms.Resample(32000, 44100)
wav_resampled = resampler(wav)
```

### Stereo/mono mismatch

**Problem**: Wrong number of channels

**Solutions**:
```python
# Check model type
print(f"Audio channels: {wav.shape}")
# Mono: [batch, 1, samples]
# Stereo: [batch, 2, samples]

# Convert mono to stereo
if wav.shape[1] == 1:
    wav_stereo = wav.repeat(1, 2, 1)

# Convert stereo to mono
if wav.shape[1] == 2:
    wav_mono = wav.mean(dim=1, keepdim=True)

# Use stereo model for stereo output
model = MusicGen.get_pretrained('facebook/musicgen-stereo-medium')
```

### Clipping and distortion

**Problem**: Audio has clipping or distortion

**Solutions**:
```python
import torch

# Check for clipping
max_val = wav.abs().max().item()
print(f"Max amplitude: {max_val}")

# Normalize to prevent clipping
if max_val > 1.0:
    wav = wav / max_val

# Apply soft clipping
def soft_clip(x, threshold=0.9):
    return torch.tanh(x / threshold) * threshold

wav_clipped = soft_clip(wav)

# Lower temperature during generation
model.set_generation_params(temperature=0.7)  # More controlled
```

## HuggingFace Transformers Issues

### Processor errors

**Error**: Issues with MusicgenProcessor

**Solutions**:
```python
from transformers import AutoProcessor, MusicgenForConditionalGeneration

# Load matching processor and model
processor = AutoProcessor.from_pretrained("facebook/musicgen-small")
model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-small")

# Ensure inputs are on same device
inputs = processor(
    text=["prompt"],
    padding=True,
    return_tensors="pt"
).to("cuda")

# Check processor configuration
print(processor.tokenizer)
print(processor.feature_extractor)
```

### Generation parameter errors

**Error**: Invalid generation parameters

**Solutions**:
```python
# HuggingFace uses different parameter names
audio_values = model.generate(
    **inputs,
    do_sample=True,           # Enable sampling
    guidance_scale=3.0,       # CFG (not cfg_coef)
    max_new_tokens=256,       # Token limit (not duration)
    temperature=1.0
)

# Calculate tokens from duration
# ~50 tokens per second
duration_seconds = 10
max_tokens = duration_seconds * 50
audio_values = model.generate(**inputs, max_new_tokens=max_tokens)
```

## Performance Issues

### Slow generation

**Problem**: Generation takes too long

**Solutions**:
```python
# Use smaller model
model = MusicGen.get_pretrained('facebook/musicgen-small')

# Reduce duration
model.set_generation_params(duration=10)

# Use GPU
model.to("cuda")

# Enable flash attention if available
# (requires compatible hardware)

# Batch multiple prompts
prompts = ["prompt1", "prompt2", "prompt3"]
wav = model.generate(prompts)  # Single batch is faster than loop

# Use compile (PyTorch 2.0+)
model.lm = torch.compile(model.lm)
```

### CPU fallback

**Problem**: Generation running on CPU instead of GPU

**Solutions**:
```python
import torch

# Check CUDA availability
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA device: {torch.cuda.get_device_name(0)}")

# Explicitly move to GPU
model = MusicGen.get_pretrained('facebook/musicgen-small')
model.to("cuda")

# Verify model device
print(f"Model device: {next(model.lm.parameters()).device}")
```

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `CUDA out of memory` | Model too large | Use smaller model, reduce duration |
| `ffmpeg not found` | FFmpeg not installed | Install FFmpeg |
| `No module named 'audiocraft'` | Not installed | `pip install audiocraft` |
| `RuntimeError: Expected 3D tensor` | Wrong input shape | Check tensor dimensions |
| `KeyError: 'melody'` | Wrong model for melody | Use musicgen-melody |
| `Sample rate mismatch` | Wrong audio format | Resample to model rate |

## Getting Help

1. **GitHub Issues**: https://github.com/facebookresearch/audiocraft/issues
2. **HuggingFace Forums**: https://discuss.huggingface.co
3. **Paper**: https://arxiv.org/abs/2306.05284

### Reporting Issues

Include:
- Python version
- PyTorch version
- CUDA version
- AudioCraft version: `pip show audiocraft`
- Full error traceback
- Minimal reproducible code
- Hardware (GPU model, VRAM)
