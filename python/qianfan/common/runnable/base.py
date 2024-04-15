# Copyright (c) 2023 Baidu, Inc. All Rights Reserved.
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
import datetime
import json
import os
import pickle
import sys
import threading
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar

import dill
import multiprocess as multiprocessing
import yaml

from qianfan.config import encoding
from qianfan.utils import utils
from qianfan.utils.logging import log_debug, log_info

Input = TypeVar("Input")
Output = TypeVar("Output")


class Executable(Generic[Input, Output], ABC):
    """
    generic abstraction class of executable

    """

    @abstractmethod
    def exec(self, input: Optional[Input] = None, **kwargs: Dict) -> Output:
        ...


class Serializable(ABC):
    """
    generic abstraction class of serializable.
    especially for the model, service, and trainer.
    """

    @abstractmethod
    def dumps(self) -> Optional[bytes]:
        """
        dumps

        Returns:
            serialized bytes data
        """
        ...

    @abstractmethod
    def loads(self, data: bytes) -> Any:
        """
        loads

        Parameters:
            data (bytes): load

        Returns:
            Any: _description_
        """
        ...


class SerializeHelper(ABC):
    """
    serialize helper class.
    """

    @abstractmethod
    def serialize(self, obj: Any) -> bytes:
        ...

    @abstractmethod
    def deserialize(self, data: bytes) -> Any:
        ...


class PickleSerializeHelper(SerializeHelper):
    """
    pickle serialize helper.
    """

    def serialize(self, obj: Any) -> bytes:
        return pickle.dumps(obj)

    def deserialize(self, data: bytes) -> Any:
        return pickle.loads(data)


StopMessage = "STOP"
QianfanTrainerLocalCacheDir = ".qianfan_exec_cache"


class YamlSerializeHelper(SerializeHelper):
    def serialize(self, obj: Any) -> bytes:
        return bytes(yaml.dump(obj, encoding=encoding()))

    def deserialize(self, data: bytes) -> Any:
        return yaml.safe_load(data)


class JsonSerializeHelper(SerializeHelper):
    """
    json serialize helper.
    """

    def serialize(self, obj: Any) -> bytes:
        res = json.dumps(obj, skipkeys=True)
        return res.encode(encoding=encoding())

    def deserialize(self, data: bytes) -> Any:
        return json.loads(data)


class DillSerializeHelper(SerializeHelper):
    """
    dill serialize helper.
    """

    def serialize(self, obj: Any) -> bytes:
        return dill.dumps(obj)

    def deserialize(self, data: bytes) -> Any:
        return dill.loads(data)


class CompatSerializeHelper(SerializeHelper):
    def __init__(self) -> None:
        self.helpers: List[SerializeHelper] = [
            JsonSerializeHelper(),
            YamlSerializeHelper(),
        ]

    def serialize(self, obj: Any) -> bytes:
        for helper in self.helpers:
            try:
                return helper.serialize(obj)
            except Exception:
                continue
        raise Exception("serialize failed")

    def deserialize(self, data: bytes) -> Any:
        for helper in self.helpers:
            try:
                return helper.deserialize(data)
            except Exception:
                continue
        raise Exception("deserialize failed")


class ExecuteSerializable(Executable[Input, Output], Serializable):
    """
    set of executable and serializable. subclass implement it to support
    exec and dumps/loads.
    """

    process_id: str = ""
    process: Optional[multiprocessing.Process] = None

    serialize_helper: SerializeHelper = CompatSerializeHelper()

    def _get_specific_cache_path(self) -> str:
        cache_path = os.path.join(
            QianfanTrainerLocalCacheDir,
            utils.generate_letter_num_random_id(8),
        )
        if not os.path.exists(cache_path):
            os.makedirs(cache_path)

        return cache_path

    def _get_log_path(self) -> str:
        current_date = datetime.datetime.now()
        date_str = current_date.strftime("%Y-%m-%d")

        return os.path.join(self._get_specific_cache_path(), f"{date_str}.log")

    def _start(self, **kwargs: Any) -> None:
        self.exec(**kwargs)

    def start(
        self, join_on_exited: bool = False, **kwargs: Any
    ) -> "ExecuteSerializable":
        def run_subprocess(pipe: multiprocessing.Pipe) -> None:
            # if platform.system() != "Windows":
            #     os.setsid()  # type: ignore[attr-defined]
            # redirect output
            log_path = self._get_log_path()
            with open(log_path, "a", encoding=encoding()) as f:
                log_info(f"check running log in {log_path}")
                sys.stdout = f
                from qianfan.utils.logging import redirect_log_to_file

                redirect_log_to_file(log_path)

            # start a thread for run
            main_t = threading.Thread(target=self._start, kwargs=kwargs)
            main_t.start()

            import time

            while True:
                time.sleep(1)
                msg = pipe.recv()  # 接收消息
                if msg == StopMessage:
                    log_debug("Child process received STOP signal, exiting...")
                    self.stop()
                    break
            log_info("trainer subprocess exited")

        parent_pipe, child_pipe = multiprocessing.Pipe()
        p = multiprocessing.Process(target=run_subprocess, args=(child_pipe,))
        p.start()
        log_info(f"trainer subprocess started, pid: {p.pid}")
        if not join_on_exited:
            self.join = p.join
            # multiprocess 在atexit注册自动join
            p.join = lambda: None
        self.parent_pipe = parent_pipe
        self.process = p
        self.process_id = p.pid
        return self

    def stop(self, **kwargs: Any) -> "ExecuteSerializable":
        if self.process:
            self.parent_pipe.send(StopMessage)
        return self

    def wait(self, **kwargs: Any) -> "ExecuteSerializable":
        if self.process:
            self.join()
        return self

    def dumps(self) -> Optional[bytes]:
        """
        dumps action input bytes

        Returns:
            serialized bytes action data
        """
        return self.serialize_helper.serialize(self)

    def loads(self, data: bytes) -> Any:
        """
        loads

        Parameters:
            data (bytes): load

        Returns:
            Any: action instance
        """
        return self.serialize_helper.deserialize(data)
