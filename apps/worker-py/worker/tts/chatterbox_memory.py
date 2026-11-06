"""Bounded checkpoint reads without Windows whole-file copy-on-write mapping."""
from __future__ import annotations

import json
import math
import struct
from pathlib import Path


def load_checkpoint(module, path: Path, *, strict: bool = True) -> None:
    """Copy one tensor at a time into normally initialized parameters/buffers.

    Keep ordinary constructors (including nonpersistent buffers), checkpoint
    dtype conversion, and strict key/shape checks. Never initialize on meta.
    """
    import torch

    dtypes = {"F64": torch.float64, "F32": torch.float32,
              "F16": torch.float16, "BF16": torch.bfloat16,
              "I64": torch.int64, "I32": torch.int32,
              "I16": torch.int16, "I8": torch.int8,
              "U8": torch.uint8, "BOOL": torch.bool}
    targets = module.state_dict()
    with path.open("rb") as handle:
        prefix = handle.read(8)
        if len(prefix) != 8:
            raise ValueError("Truncated safetensors header")
        size = struct.unpack("<Q", prefix)[0]
        file_size = path.stat().st_size
        if size > min(100_000_000, file_size - 8):
            raise ValueError("Invalid safetensors header length")
        header = json.loads(handle.read(size))
        rows = {key: value for key, value in header.items() if key != "__metadata__"}
        if strict and rows.keys() != targets.keys():
            raise ValueError("Checkpoint keys do not match model")
        # Validate all selected shapes/offsets before changing any model tensor.
        for key, row in rows.items():
            if key not in targets:
                continue
            dtype = dtypes[row["dtype"]]
            start, end = row["data_offsets"]
            shape = tuple(row["shape"])
            expected = math.prod(shape) * torch.empty((), dtype=dtype).element_size()
            if (shape != tuple(targets[key].shape) or start < 0 or end < start
                    or end - start != expected or 8 + size + end > file_size):
                raise ValueError(f"Invalid checkpoint tensor: {key}")
        with torch.no_grad():
            for key, row in rows.items():
                if key not in targets:
                    continue
                start, end = row["data_offsets"]
                if end == start:
                    continue
                handle.seek(8 + size + start)
                buffer = bytearray(end - start)
                if handle.readinto(buffer) != len(buffer):
                    raise EOFError(f"Truncated checkpoint tensor: {key}")
                value = torch.frombuffer(buffer, dtype=dtypes[row["dtype"]]).reshape(row["shape"])
                targets[key].copy_(value)
                del value, buffer


def install_staged_offload(model):
    """Retain FP32 inference, but never keep T3 and S3Gen on CUDA together.

    Wrap the installed provider's phase methods instead of copying its sampling,
    conditioning or watermark implementations. Both comparison arms use this mode.
    """
    import torch

    components = {"t3": model.t3, "s3gen": model.s3gen, "ve": model.ve}
    prepare = model.prepare_conditionals
    tokens = model.t3.inference
    waveform = model.s3gen.inference
    generate = model.generate

    def activate(*names):
        for name, component in components.items():
            if name not in names:
                component.to("cpu")
        torch.cuda.empty_cache()
        for name in names:
            components[name].to(model.device)

    def prepare_conditionals(*args, **kwargs):
        model.conds = None
        activate("s3gen", "ve")
        return prepare(*args, **kwargs)

    def infer_tokens(*args, **kwargs):
        activate("t3")
        return tokens(*args, **kwargs)

    def infer_waveform(*args, **kwargs):
        activate("s3gen")
        return waveform(*args, **kwargs)

    def infer(*args, **kwargs):
        # Reference feature extraction is outside the upstream inference context.
        # Disable autograd there too, so offloading cannot retain its CUDA graph.
        with torch.inference_mode():
            return generate(*args, **kwargs)

    model.prepare_conditionals = prepare_conditionals
    model.t3.inference = infer_tokens
    model.s3gen.inference = infer_waveform
    model.generate = infer
    return model


def load_chatterbox(model_path: Path, device: str, *, runtime_mode: str = "default"):
    """Preserve the installed original Chatterbox model and voice behavior."""
    import torch
    from chatterbox.tts import (
        ChatterboxTTS, Conditionals, EnTokenizer, S3Gen, T3, VoiceEncoder,
    )

    if runtime_mode not in {"default", "staged_cpu_offload"}:
        raise ValueError("Unsupported Chatterbox runtime mode")
    staged = runtime_mode == "staged_cpu_offload"
    if staged and not device.startswith("cuda"):
        raise ValueError("Staged offload requires CUDA")
    load_device = "cpu" if staged else device

    def component(factory, filename, *, strict=True):
        model = factory()
        model.to(load_device).eval()
        load_checkpoint(model, model_path / filename, strict=strict)
        return model

    ve = component(VoiceEncoder, "ve.safetensors")
    t3 = component(T3, "t3_cfg.safetensors")
    s3gen = component(S3Gen, "s3gen.safetensors", strict=False)
    tokenizer = EnTokenizer(str(model_path / "tokenizer.json"))
    conds = None
    if (model_path / "conds.pt").exists():
        location = torch.device("cpu") if load_device in {"cpu", "mps"} else None
        conds = Conditionals.load(model_path / "conds.pt", map_location=location).to(device)
    model = ChatterboxTTS(t3, s3gen, ve, tokenizer, device, conds=conds)
    return install_staged_offload(model) if staged else model
