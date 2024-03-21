import glob
from abc import ABC, abstractmethod
from os import path
from typing import List, TypeVar

from qianfan.common.persister.base import Persistent

_T = TypeVar("_T", bound=Persistent)


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


FileTmpPath = "./qianfan_tmp/tasks/"


class FilePersister(Persister):
    @classmethod
    def save(cls, p: Persistent) -> None:
        b = p.persist()
        with open(path.join(FileTmpPath, p._space(), str(p._identity())), "wb") as f:
            f.write(b)

    @classmethod
    def load(cls, id: str, t: _T) -> Persistent:
        with open(path.join(FileTmpPath, t._space(), id), "rb") as f:
            return t.load(f.read())

    @classmethod
    def list(cls, t: _T) -> List[Persistent]:
        space_path = path.join(FileTmpPath, t._space())
        res = []
        for file_path in glob.glob(path.join(space_path, "*")):
            with open(file_path, "rb") as f:
                res.append(t.load(f.read()))
        return res
