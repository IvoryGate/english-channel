import json
import struct

import pytest
import torch

from worker.tts.chatterbox_memory import install_staged_offload, load_checkpoint


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


def test_staged_offload_evicts_inactive_weights_before_each_phase(monkeypatch):
    events = []
    class Component:
        def __init__(self, name):
            self.name, self.device = name, "cpu"
        def to(self, device):
            self.device = device
            events.append((self.name, device))
            assert not (model.t3.device == "cuda" and model.s3gen.device == "cuda")
            return self
        def inference(self, value):
            assert torch.is_inference_mode_enabled()
            assert self.device == "cuda"
            events.append(("call", self.name))
            return value + 1
    class Model:
        device = "cuda"
        conds = None
        def __init__(self):
            self.t3, self.s3gen, self.ve = (Component(name) for name in ("t3", "s3gen", "ve"))
        def prepare_conditionals(self, value):
            assert torch.is_inference_mode_enabled()
            assert self.s3gen.device == self.ve.device == "cuda"
            self.conds = value
        def generate(self, value):
            self.prepare_conditionals(value)
            return self.s3gen.inference(self.t3.inference(value))
    model = Model()
    monkeypatch.setattr(torch.cuda, "empty_cache", lambda: events.append(("cache", "clear")))
    install_staged_offload(model)
    assert model.generate(10) == 12
    assert model.generate(20) == 22  # second voice/turn repeats the same safe phases
    assert events.count(("call", "t3")) == events.count(("call", "s3gen")) == 2
    assert model.t3.device == model.ve.device == "cpu"
