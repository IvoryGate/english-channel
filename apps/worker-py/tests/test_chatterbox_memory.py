import json
import struct

import pytest
import torch

from worker.tts.chatterbox_memory import load_checkpoint


def checkpoint(path, tensors):
    data = bytearray()
    header = {}
    for key, tensor in tensors.items():
        raw = tensor.numpy().tobytes()
        header[key] = {"dtype": "F32", "shape": list(tensor.shape),
                       "data_offsets": [len(data), len(data) + len(raw)]}
        data.extend(raw)
    encoded = json.dumps(header).encode()
    path.write_bytes(struct.pack("<Q", len(encoded)) + encoded + data)


def test_exact_values_and_nonpersistent_buffers(tmp_path):
    source = torch.nn.Linear(3, 2)
    target = torch.nn.Linear(3, 2)
    target.register_buffer("cache", torch.ones(2), persistent=False)
    path = tmp_path / "weights.safetensors"
    checkpoint(path, source.state_dict())
    load_checkpoint(target, path)
    for key, value in source.state_dict().items():
        assert torch.equal(target.state_dict()[key], value)
    assert torch.equal(target.cache, torch.ones(2))
    assert torch.equal(target(torch.ones(3)), source(torch.ones(3)))


def test_bad_shape_rejected_before_changes(tmp_path):
    target = torch.nn.Linear(3, 2)
    original = target.weight.detach().clone()
    path = tmp_path / "bad.safetensors"
    checkpoint(path, {"weight": torch.ones(2, 4), "bias": torch.ones(2)})
    with pytest.raises(ValueError, match="Invalid checkpoint tensor"):
        load_checkpoint(target, path)
    assert torch.equal(target.weight, original)


def test_strict_keys_and_optional_keys(tmp_path):
    target = torch.nn.Linear(3, 2)
    path = tmp_path / "partial.safetensors"
    checkpoint(path, {"bias": torch.ones(2), "unused": torch.ones(1)})
    with pytest.raises(ValueError, match="keys"):
        load_checkpoint(target, path)
    load_checkpoint(target, path, strict=False)
    assert torch.equal(target.bias, torch.ones(2))


def test_truncated_checkpoint_rejected(tmp_path):
    target = torch.nn.Linear(3, 2)
    path = tmp_path / "truncated.safetensors"
    checkpoint(path, target.state_dict())
    path.write_bytes(path.read_bytes()[:-1])
    with pytest.raises(ValueError, match="Invalid checkpoint tensor"):
        load_checkpoint(target, path)
