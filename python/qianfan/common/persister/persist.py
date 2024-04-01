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
from typing import List, Type, TypeVar

from qianfan.common.persister.base import Persistent
from qianfan.consts import Consts
from qianfan.utils.logging import log_info

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


FileTmpPath = Consts.QianfanCacheDir / "file_tmp/"


class FilePersister(Persister):
    def __init__(self) -> None:
        if not path.exists(FileTmpPath):
            makedirs(FileTmpPath)

    @classmethod
    def save(cls, p: Persistent) -> None:
        b = p.persist()
        f_path_dir = path.join(FileTmpPath, p._space())
        if not path.exists(f_path_dir):
            makedirs(f_path_dir)
        f_path = path.join(f_path_dir, p._identity())
        log_info(f"save to {f_path}")
        with open(f_path, "wb") as f:
            f.write(b)

    @classmethod
    def load(cls, id: str, t: _T) -> Persistent:
        f_path_dir = path.join(FileTmpPath, t._space())
        if not path.exists(f_path_dir):
            makedirs(f_path_dir)
        with open(path.join(FileTmpPath, t._space(), id), "rb") as f:
            return t.load(f.read())

    @classmethod
    def list(cls, t: _T) -> List[Persistent]:
        space_path = path.join(FileTmpPath, t._space())
        res = []
        if not path.exists(space_path):
            makedirs(space_path)
        for file_path in glob.glob(path.join(space_path, "*")):
            with open(file_path, "rb") as f:
                res.append(t.load(f.read()))
        return res


g_persister = FilePersister()
# from qianfan.utils.cache import global_disk_cache, Cache
# class DiskCachePersister(Persister):

#     _instance: "Cache" = None

#     @classmethod
#     def save(cls, p: Persistent) -> None:
#        global_disk_cache.set(p._space, )
#        global_disk_cache.get()

#     @staticmethod
#     def get_instance() -> :
#         if DiskCachePersister._instance is None:
#             DiskCachePersister._instance = global_disk_cache
#         return DiskCachePersister._instance
