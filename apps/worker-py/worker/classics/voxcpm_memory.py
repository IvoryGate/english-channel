from __future__ import annotations

import gc
import json
import os
import struct
import sys


def patch_voxcpm_low_memory_load() -> None:
    """Load VoxCPM2 tensors incrementally on memory-constrained Windows hosts."""
    import torch
    import voxcpm.model.voxcpm2 as voxcpm2
    from transformers import LlamaTokenizerFast
    from voxcpm.modules.audiovae import AudioVAEV2

    if getattr(voxcpm2.VoxCPM2Model.from_local, "_low_memory_patched", False):
        return

    load_file = voxcpm2.load_file

    @classmethod
    def from_local_low_memory(
        cls,
        path: str,
        optimize: bool = True,
        training: bool = False,
        device: str | None = None,
        lora_config=None,
    ):
        with open(os.path.join(path, "config.json"), encoding="utf-8") as config_file:
            config = voxcpm2.VoxCPMConfig.model_validate_json(config_file.read())
        default_max_length = "1024" if os.name == "nt" else "2048"
        max_length_cap = int(os.environ.get("ELR_VOXCPM_MAX_LENGTH", default_max_length))
        if max_length_cap < 256:
            raise ValueError("ELR_VOXCPM_MAX_LENGTH must be at least 256")
        config.max_length = min(config.max_length, max_length_cap)
        tokenizer = LlamaTokenizerFast.from_pretrained(path)

        audiovae_safetensors_path = os.path.join(path, "audiovae.safetensors")
        audiovae_pth_path = os.path.join(path, "audiovae.pth")
        audio_vae_config = getattr(config, "audio_vae_config", None)
        audio_vae = AudioVAEV2(config=audio_vae_config) if audio_vae_config else AudioVAEV2()
        if os.path.exists(audiovae_safetensors_path) and voxcpm2.SAFETENSORS_AVAILABLE:
            print(
                f"Loading AudioVAE from safetensors: {audiovae_safetensors_path}",
                file=sys.stderr,
            )
            vae_state_dict = load_file(audiovae_safetensors_path, device="cpu")
        elif os.path.exists(audiovae_pth_path):
            print(f"Loading AudioVAE from pytorch: {audiovae_pth_path}", file=sys.stderr)
            checkpoint = torch.load(audiovae_pth_path, map_location="cpu", weights_only=True)
            vae_state_dict = checkpoint.get("state_dict", checkpoint)
        else:
            raise FileNotFoundError(
                "AudioVAE checkpoint not found. Expected either "
                f"{audiovae_safetensors_path} or {audiovae_pth_path}"
            )

        # Meta initialization avoids a temporary full-size float32 parameter set.
        with torch.device("meta"):
            model = cls(config, tokenizer, audio_vae, lora_config, device=device)

        safetensors_path = os.path.join(path, "model.safetensors")
        pytorch_model_path = os.path.join(path, "pytorch_model.bin")
        streaming_load = False
        if os.path.exists(safetensors_path) and voxcpm2.SAFETENSORS_AVAILABLE:
            print(f"Loading model from safetensors: {safetensors_path}", file=sys.stderr)
            streaming_default = "1" if os.name == "nt" else "0"
            streaming_load = (
                os.environ.get("ELR_VOXCPM_STREAMING_LOAD", streaming_default) == "1"
            )
            if streaming_load:
                target_device = torch.device(device or model.device)
                expected_keys = set(model.state_dict().keys())
                unexpected_keys: list[str] = []

                def assign_tensor(key: str, value: torch.Tensor) -> None:
                    parent_name, _, leaf_name = key.rpartition(".")
                    parent = model.get_submodule(parent_name) if parent_name else model
                    value = value.to(target_device)
                    if leaf_name in parent._parameters:
                        current = parent._parameters[leaf_name]
                        requires_grad = bool(current.requires_grad) if current is not None else False
                        parent._parameters[leaf_name] = torch.nn.Parameter(
                            value, requires_grad=requires_grad
                        )
                    elif leaf_name in parent._buffers:
                        parent._buffers[leaf_name] = value
                    else:
                        raise KeyError(f"Checkpoint tensor has no module target: {key}")

                print(f"Streaming checkpoint tensors to: {target_device}", file=sys.stderr)
                dtype_map = {
                    "BF16": torch.bfloat16,
                    "F16": torch.float16,
                    "F32": torch.float32,
                    "F64": torch.float64,
                    "I8": torch.int8,
                    "I16": torch.int16,
                    "I32": torch.int32,
                    "I64": torch.int64,
                    "U8": torch.uint8,
                    "BOOL": torch.bool,
                }
                with open(safetensors_path, "rb") as checkpoint_file:
                    header_length = struct.unpack("<Q", checkpoint_file.read(8))[0]
                    header = json.loads(checkpoint_file.read(header_length))
                    data_start = 8 + header_length
                    tensor_items = [
                        (key, metadata)
                        for key, metadata in header.items()
                        if key != "__metadata__"
                    ]
                    for index, (key, metadata) in enumerate(tensor_items, start=1):
                        if key not in expected_keys:
                            unexpected_keys.append(key)
                            continue
                        start, end = (int(offset) for offset in metadata["data_offsets"])
                        checkpoint_file.seek(data_start + start)
                        buffer = bytearray(end - start)
                        bytes_read = checkpoint_file.readinto(buffer)
                        if bytes_read != len(buffer):
                            raise EOFError(
                                f"Short read for {key}: {bytes_read}/{len(buffer)} bytes"
                            )
                        dtype = dtype_map.get(str(metadata["dtype"]))
                        if dtype is None:
                            raise ValueError(
                                f"Unsupported safetensors dtype for {key}: {metadata['dtype']}"
                            )
                        tensor = torch.frombuffer(buffer, dtype=dtype).reshape(
                            tuple(metadata["shape"])
                        )
                        assign_tensor(key, tensor)
                        del tensor, buffer
                        if index % 100 == 0:
                            print(
                                f"Loaded {index}/{len(tensor_items)} checkpoint tensors",
                                file=sys.stderr,
                            )
                            gc.collect()
                for key, value in vae_state_dict.items():
                    target_key = f"audio_vae.{key}"
                    if target_key not in expected_keys:
                        unexpected_keys.append(target_key)
                        continue
                    assign_tensor(target_key, value)
                incompatible = type(
                    "StreamingLoadResult", (), {"unexpected_keys": unexpected_keys}
                )()
                del expected_keys
            else:
                checkpoint_device_override = os.environ.get(
                    "ELR_VOXCPM_CHECKPOINT_DEVICE", ""
                ).strip().lower()
                if checkpoint_device_override not in {"", "cpu", "cuda"}:
                    raise ValueError(
                        "ELR_VOXCPM_CHECKPOINT_DEVICE must be 'cpu' or 'cuda'"
                    )
                checkpoint_device = checkpoint_device_override or (
                    model.device if str(model.device).startswith("cuda") else "cpu"
                )
                print(f"Checkpoint load device: {checkpoint_device}", file=sys.stderr)
                model_state_dict = load_file(safetensors_path, device=checkpoint_device)
        elif os.path.exists(pytorch_model_path):
            print(f"Loading model from pytorch_model.bin: {pytorch_model_path}", file=sys.stderr)
            checkpoint = torch.load(
                pytorch_model_path, map_location="cpu", weights_only=True
            )
            model_state_dict = checkpoint.get("state_dict", checkpoint)
        else:
            raise FileNotFoundError(
                "Model file not found. Expected either "
                f"{safetensors_path} or {pytorch_model_path}"
            )

        if not streaming_load:
            for key, value in vae_state_dict.items():
                model_state_dict[f"audio_vae.{key}"] = value
            incompatible = model.load_state_dict(model_state_dict, strict=False, assign=True)
            del model_state_dict
        del vae_state_dict
        gc.collect()

        # Rotary caches are non-persistent and must be rebuilt after meta init.
        for language_model in model.modules():
            rope = getattr(language_model, "rope_emb", None)
            if rope is not None and any(buffer.is_meta for buffer in rope.buffers()):
                rope_type = type(rope)
                language_model.rope_emb = rope_type(language_model.config).to(model.device)
        unresolved = [
            name for name, parameter in model.named_parameters() if parameter.is_meta
        ]
        if unresolved:
            raise RuntimeError(
                "Checkpoint did not materialize model parameters: "
                + ", ".join(unresolved[:8])
            )
        if incompatible.unexpected_keys:
            raise RuntimeError(
                "Checkpoint contains unexpected model parameters: "
                + ", ".join(incompatible.unexpected_keys[:8])
            )
        unresolved_buffers = [
            name for name, buffer in model.named_buffers() if buffer.is_meta
        ]
        if unresolved_buffers:
            raise RuntimeError(
                "Checkpoint did not materialize model buffers: "
                + ", ".join(unresolved_buffers[:8])
            )
        if training:
            return model
        return model.to(model.device).eval().optimize(disable=not optimize)

    from_local_low_memory._low_memory_patched = True
    voxcpm2.VoxCPM2Model.from_local = from_local_low_memory
