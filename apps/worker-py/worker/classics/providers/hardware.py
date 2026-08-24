from __future__ import annotations

import sys
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any


def heavy_resource_lease(repo_root: Path, label: str) -> AbstractContextManager[Any]:
    """Bridge the production adapter to the shared legacy GPU mutex.

    The channel lease scheduler will replace this provider. Until then every
    public heavy Classic Listening command uses the same repository-level lock
    as ELR and Shorts.
    """

    scripts_root = repo_root / "scripts"
    if str(scripts_root) not in sys.path:
        sys.path.insert(0, str(scripts_root))
    try:
        import gpu_production_lock
    except ImportError as exc:
        raise RuntimeError("The shared GPU production lock is unavailable") from exc
    gpu_production_lock.LOCK_PATH = repo_root / "logs" / "gpu_production.lock"
    return gpu_production_lock.GpuProductionLock(label)
