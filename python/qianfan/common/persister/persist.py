# Copyright (c) 2024 Baidu, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import glob
from abc import ABC, abstractmethod
from os import makedirs, path
from pathlib import Path
from typing import List, Type, TypeVar

from qianfan.common.persister.base import Persistent
from qianfan.config import get_config
from qianfan.utils.logging import log_debug

_T = TypeVar("_T", bound=Type["Persistent"])


class Persister(ABC):
    @classmethod
    @abstractmethod
    def save(cls, p: Persistent) -> None:
        ...

    @classmethod
    @abstractmethod
    def list(self, t: _T) -> List[Persistent]:
        ...

    @classmethod
    @abstractmethod
    def load(self, id: str, t: _T) -> Persistent:
        ...


class FilePersister(Persister):
    @classmethod
    def _ensure_cache_existed(cls) -> Path:
        FileTmpPath = Path(get_config().CACHE_DIR) / "file_tmp/"
        if not path.exists(FileTmpPath):
            makedirs(FileTmpPath)
        return FileTmpPath

    @classmethod
    def save(cls, p: Persistent) -> None:
        if get_config().DISABLE_CACHE:
            log_debug("cache is disabled, skip save")
            return
        b = p.persist()
        cache_files_path = cls._ensure_cache_existed()
        f_path_dir = path.join(cache_files_path, p._space())
        if not path.exists(f_path_dir):
            makedirs(f_path_dir, exist_ok=True)
        f_path = path.join(f_path_dir, p._identity())
        log_debug(f"save to {f_path}")
        with open(f_path, "wb") as f:
            f.write(b)

    @classmethod
    def load(cls, id: str, t: _T) -> Persistent:
        if get_config().DISABLE_CACHE:
            raise ValueError(
                "cache is disabled, reset `QIANFAN_DISABLE_CACHE` if needed"
            )
        cache_files_path = cls._ensure_cache_existed()
        f_path_dir = path.join(cache_files_path, t._space())
        if not path.exists(f_path_dir):
            makedirs(f_path_dir)
        with open(path.join(cache_files_path, t._space(), id), "rb") as f:
            return t.load(f.read())

    @classmethod
    def list(cls, t: _T, skip_if_error: bool = True) -> List[Persistent]:
        space_path = path.join(cls._ensure_cache_existed(), t._space())
        res = []
        if not path.exists(space_path):
            makedirs(space_path)
        for file_path in glob.glob(path.join(space_path, "*")):
            try:
                with open(file_path, "rb") as f:
                    res.append(t.load(f.read()))
            except Exception:
                if skip_if_error:
                    continue
        return res
