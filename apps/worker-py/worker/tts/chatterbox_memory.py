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


def load_chatterbox(model_path: Path, device: str):
    """Preserve the installed original Chatterbox model and voice behavior."""
    import torch
    from chatterbox.tts import (
        ChatterboxTTS, Conditionals, EnTokenizer, S3Gen, T3, VoiceEncoder,
    )

    def component(factory, filename, *, strict=True):
        model = factory()
        model.to(device).eval()
        load_checkpoint(model, model_path / filename, strict=strict)
        return model

    ve = component(VoiceEncoder, "ve.safetensors")
    t3 = component(T3, "t3_cfg.safetensors")
    s3gen = component(S3Gen, "s3gen.safetensors", strict=False)
    tokenizer = EnTokenizer(str(model_path / "tokenizer.json"))
    conds = None
    if (model_path / "conds.pt").exists():
        location = torch.device("cpu") if device in {"cpu", "mps"} else None
        conds = Conditionals.load(model_path / "conds.pt", map_location=location).to(device)
    return ChatterboxTTS(t3, s3gen, ve, tokenizer, device, conds=conds)
