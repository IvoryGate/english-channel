from __future__ import annotations

import argparse
import gc
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf
import torch

from audiobook_workspace import (
    DEFAULT_CFG_VALUE,
    DEFAULT_INFERENCE_TIMESTEPS,
    DEFAULT_MODEL_ID,
    clean_reference_path,
    compose_control,
    ensure_segment_defaults,
    load_json,
    manifest_path,
    normalize_segment_peak,
    parse_segment_ids,
    write_json,
)
from compose_chapter import compose


def patch_voxcpm_low_memory_load() -> None:
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
        with open(os.path.join(path, "config.json"), "r", encoding="utf-8") as cfg_file:
            config = voxcpm2.VoxCPMConfig.model_validate_json(cfg_file.read())
        # The upstream checkpoint reserves an 8,192-token KV cache before the
        # weights are loaded. That is useful for long-form synthesis, but it can
        # terminate the Windows process outright on an 8 GB GPU (and on a host
        # with a small page file) before Python can report an OOM. Short-form
        # renders never need that capacity, so allow the runtime to cap it.
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
            print(f"Loading AudioVAE from safetensors: {audiovae_safetensors_path}", file=sys.stderr)
            vae_state_dict = load_file(audiovae_safetensors_path, device="cpu")
        elif os.path.exists(audiovae_pth_path):
            print(f"Loading AudioVAE from pytorch: {audiovae_pth_path}", file=sys.stderr)
            checkpoint = torch.load(
                audiovae_pth_path,
                map_location="cpu",
                weights_only=True,
            )
            vae_state_dict = checkpoint.get("state_dict", checkpoint)
        else:
            raise FileNotFoundError(
                f"AudioVAE checkpoint not found. Expected either {audiovae_safetensors_path} or {audiovae_pth_path}"
            )

        # Build checkpoint-backed modules on PyTorch's meta device. This avoids
        # allocating an unused 8+ GB float32 parameter set before opening the
        # 4.27 GB checkpoint. Explicit CUDA KV-cache allocations in the model
        # constructor remain real; only replaceable parameters/buffers are meta.
        with torch.device("meta"):
            model = cls(config, tokenizer, audio_vae, lora_config, device=device)

        safetensors_path = os.path.join(path, "model.safetensors")
        pytorch_model_path = os.path.join(path, "pytorch_model.bin")
        if os.path.exists(safetensors_path) and voxcpm2.SAFETENSORS_AVAILABLE:
            print(f"Loading model from safetensors: {safetensors_path}", file=sys.stderr)
            streaming_default = "1" if os.name == "nt" else "0"
            streaming_load = os.environ.get("ELR_VOXCPM_STREAMING_LOAD", streaming_default) == "1"
            if streaming_load:
                # Windows counts a full 4.27 GB checkpoint copy plus CUDA
                # allocations against the system commit limit. Load and assign
                # one tensor at a time so peak committed memory stays bounded.
                import json
                import struct

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
                        parent._parameters[leaf_name] = torch.nn.Parameter(value, requires_grad=requires_grad)
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
                with open(safetensors_path, "rb") as checkpoint:
                    header_length = struct.unpack("<Q", checkpoint.read(8))[0]
                    header = json.loads(checkpoint.read(header_length))
                    data_start = 8 + header_length
                    tensor_items = [(key, meta) for key, meta in header.items() if key != "__metadata__"]
                    for index, (key, meta) in enumerate(tensor_items, start=1):
                        if key not in expected_keys:
                            unexpected_keys.append(key)
                            continue
                        start, end = (int(offset) for offset in meta["data_offsets"])
                        checkpoint.seek(data_start + start)
                        buffer = bytearray(end - start)
                        bytes_read = checkpoint.readinto(buffer)
                        if bytes_read != len(buffer):
                            raise EOFError(f"Short read for {key}: {bytes_read}/{len(buffer)} bytes")
                        dtype = dtype_map.get(str(meta["dtype"]))
                        if dtype is None:
                            raise ValueError(f"Unsupported safetensors dtype for {key}: {meta['dtype']}")
                        tensor = torch.frombuffer(buffer, dtype=dtype).reshape(tuple(meta["shape"]))
                        assign_tensor(key, tensor)
                        del tensor, buffer
                        if index % 100 == 0:
                            print(f"Loaded {index}/{len(tensor_items)} checkpoint tensors", file=sys.stderr)
                            gc.collect()
                for key, value in vae_state_dict.items():
                    target_key = f"audio_vae.{key}"
                    if target_key not in expected_keys:
                        unexpected_keys.append(target_key)
                        continue
                    assign_tensor(target_key, value)
                incompatible = type("StreamingLoadResult", (), {"unexpected_keys": unexpected_keys})()
                del expected_keys
            else:
                # Fast path for hosts with enough commit capacity.
                checkpoint_device_override = os.environ.get("ELR_VOXCPM_CHECKPOINT_DEVICE", "").strip().lower()
                if checkpoint_device_override not in {"", "cpu", "cuda"}:
                    raise ValueError("ELR_VOXCPM_CHECKPOINT_DEVICE must be 'cpu' or 'cuda'")
                checkpoint_device = (
                    checkpoint_device_override
                    or (model.device if str(model.device).startswith("cuda") else "cpu")
                )
                print(f"Checkpoint load device: {checkpoint_device}", file=sys.stderr)
                model_state_dict = load_file(safetensors_path, device=checkpoint_device)
        elif os.path.exists(pytorch_model_path):
            print(f"Loading model from pytorch_model.bin: {pytorch_model_path}", file=sys.stderr)
            checkpoint = torch.load(
                pytorch_model_path,
                map_location="cpu",
                weights_only=True,
            )
            model_state_dict = checkpoint.get("state_dict", checkpoint)
        else:
            raise FileNotFoundError(
                f"Model file not found. Expected either {safetensors_path} or {pytorch_model_path}"
            )

        if not (os.path.exists(safetensors_path) and voxcpm2.SAFETENSORS_AVAILABLE and streaming_load):
            for key, value in vae_state_dict.items():
                model_state_dict[f"audio_vae.{key}"] = value
            incompatible = model.load_state_dict(model_state_dict, strict=False, assign=True)
            del model_state_dict
        del vae_state_dict
        gc.collect()
        # Rotary caches are intentionally non-persistent and therefore are not
        # present in the checkpoint. Rebuild them after meta initialization.
        for language_model in model.modules():
            rope = getattr(language_model, "rope_emb", None)
            if rope is not None and any(buffer.is_meta for buffer in rope.buffers()):
                rope_type = type(rope)
                language_model.rope_emb = rope_type(language_model.config).to(model.device)
        unresolved = [name for name, parameter in model.named_parameters() if parameter.is_meta]
        if unresolved:
            raise RuntimeError(
                "Checkpoint did not materialize model parameters: " + ", ".join(unresolved[:8])
            )
        if incompatible.unexpected_keys:
            raise RuntimeError(
                "Checkpoint contains unexpected model parameters: "
                + ", ".join(incompatible.unexpected_keys[:8])
            )
        unresolved_buffers = [name for name, buffer in model.named_buffers() if buffer.is_meta]
        if unresolved_buffers:
            raise RuntimeError(
                "Checkpoint did not materialize model buffers: " + ", ".join(unresolved_buffers[:8])
            )
        if training:
            return model
        return model.to(model.device).eval().optimize(disable=not optimize)

    from_local_low_memory._low_memory_patched = True
    voxcpm2.VoxCPM2Model.from_local = from_local_low_memory


def load_voxcpm(model_id: str, device: str):
    # Windows CUDA often rejects expandable_segments; leave allocator at defaults (same as audiobook).
    if "expandable_segments" in os.environ.get("PYTORCH_CUDA_ALLOC_CONF", ""):
        os.environ.pop("PYTORCH_CUDA_ALLOC_CONF", None)
    patch_voxcpm_low_memory_load()
    from voxcpm import VoxCPM

    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    gc.collect()
    return VoxCPM.from_pretrained(
        model_id,
        load_denoiser=False,
        optimize=False,
        device=device,
        local_files_only=True,
    )


def active_reference(manifest: dict[str, Any], workspace: Path, no_clean_reference: bool) -> str:
    original = manifest.get("referenceAudioOriginal")
    clean = manifest.get("referenceAudioClean") or str(clean_reference_path(workspace)).replace("\\", "/")
    if no_clean_reference:
        if not original:
            raise ValueError("--no-clean-reference was set but referenceAudioOriginal is empty")
        return str(original)
    if Path(clean).is_file():
        return str(clean)
    if original:
        return str(original)
    raise ValueError("No usable reference audio. Run clean_reference_audio.py or set referenceAudioOriginal.")


def render_segments(
    workspace: Path,
    selected_ids: set[str],
    no_clean_reference: bool,
    compose_after: bool,
    self_check: bool = True,
) -> dict[str, object]:
    manifest_file = manifest_path(workspace)
    manifest = ensure_segment_defaults(load_json(manifest_file))
    segments = manifest["segments"]
    global_control = str(manifest["globalControl"])
    pace_cue = str(manifest["paceCue"]) if "paceCue" in manifest else None
    character_profiles = dict(manifest.get("characterProfiles") or {})
    reference_audio = active_reference(manifest, workspace, no_clean_reference)
    manifest["activeReferenceAudio"] = reference_audio
    write_json(manifest_file, manifest)

    if not selected_ids:
        selected_ids = {str(segment["id"]) for segment in segments}
    known_ids = {str(segment["id"]) for segment in segments}
    unknown = selected_ids - known_ids
    if unknown:
        raise ValueError(f"Unknown segment ids: {sorted(unknown)}")

    print("Loading VoxCPM2...")
    model = load_voxcpm(
        str(manifest.get("modelId", DEFAULT_MODEL_ID)),
        str(manifest.get("device", "cuda")),
    )
    sample_rate = model.tts_model.sample_rate
    rendered = []

    for segment in segments:
        if str(segment["id"]) not in selected_ids:
            continue
        request = compose_control(
            segment,
            global_control,
            pace_cue=pace_cue,
            character_profiles=character_profiles,
        )
        print(
            f"Rendering {segment['id']} -> {segment['filename']}: {segment['speaker']} | "
            f"{request['policy']} max_len={request['maxLen']}"
        )
        kwargs = {
            "text": request["ttsText"],
            "reference_wav_path": reference_audio,
            "cfg_value": float(manifest.get("cfgValue", DEFAULT_CFG_VALUE)),
            "inference_timesteps": int(manifest.get("inferenceTimesteps", DEFAULT_INFERENCE_TIMESTEPS)),
            "normalize": False,
            "denoise": False,
        }
        if request["maxLen"] is not None:
            kwargs["max_len"] = request["maxLen"]
        wav = model.generate(**kwargs).astype(np.float32, copy=False)
        wav = normalize_segment_peak(wav)
        output = workspace / str(segment["filename"])
        sf.write(output, wav, sample_rate)
        rendered.append(
            {
                "id": segment["id"],
                "filename": segment["filename"],
                "durationSec": round(float(len(wav) / sample_rate), 3),
                "policy": request["policy"],
                "maxLen": request["maxLen"],
            }
        )

    run: dict[str, object] | None = None
    qc_report: dict[str, object] | None = None
    if compose_after:
        run = compose(workspace)
        if self_check:
            from check_chapter import format_qc_conversation_summary, run_chapter_check

            print("\n=== QC SELF-CHECK ===", flush=True)
            qc_report = run_chapter_check(workspace, write_report=False, verbose=True)
            print(format_qc_conversation_summary(qc_report), flush=True)
    return {"rendered": rendered, "composed": run, "qc": qc_report}


def main() -> None:
    parser = argparse.ArgumentParser(description="Render all or selected audiobook chapter segments.")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--segments", help="Comma-separated ids, e.g. 003,009,010")
    parser.add_argument("--no-compose", action="store_true")
    parser.add_argument("--no-self-check", action="store_true", help="Skip post-compose QC self-check.")
    parser.add_argument("--no-clean-reference", action="store_true")
    args = parser.parse_args()
    result = render_segments(
        Path(args.workspace),
        parse_segment_ids(args.segments),
        no_clean_reference=args.no_clean_reference,
        compose_after=not args.no_compose,
        self_check=not args.no_self_check,
    )
    print(f"rendered={len(result['rendered'])}")
    if result["composed"]:
        print(f"output={result['composed']['output']}")


if __name__ == "__main__":
    main()
