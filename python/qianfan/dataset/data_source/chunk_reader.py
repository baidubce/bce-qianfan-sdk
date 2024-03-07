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
"""
A file which implements chunk reading from various file
"""
import io
import json
import multiprocessing
import os.path
import threading
from abc import ABC, abstractmethod
from queue import PriorityQueue, Queue
from typing import Any, Callable, Dict, List, Optional

import ijson
from clevercsv import stream_table
from typing_extensions import override

from qianfan.config import encoding
from qianfan.dataset.consts import QianfanDatasetPackColumnName
from qianfan.utils import log_error


class BaseReader(ABC):
    """A file reader which reads data streamly"""

    def __init__(self, chunk_size: int = 1, **kwargs: Any):
        self.chunk_size = chunk_size

    def get_chunk(self, chunk_size: int = 0) -> List[Any]:
        """get number of chunk from file"""
        if chunk_size == 0:
            chunk_size = self.chunk_size

        data_list: List[Any] = []
        for i in range(chunk_size):
            try:
                data_list.append(self._get_an_element(i))
            except StopIteration:
                break
            except Exception as e:
                err_msg = f"exception occurred during read csv file streamly: {e}"
                log_error(err_msg)
                raise e

        return data_list

    @abstractmethod
    def _get_an_element(self, index: int) -> Any:
        """get an element for reader"""

    def __iter__(self) -> "BaseReader":
        return self

    def __next__(self) -> List[Any]:
        """return the chunk of file data"""
        chunks = self.get_chunk()
        if not chunks:
            raise StopIteration
        return chunks


class CsvReader(BaseReader):
    def __init__(self, file_path: str, chunk_size: int = 10, **kwargs: Any):
        super().__init__(chunk_size, **kwargs)

        self.file_path = file_path

        if "dialect" in kwargs:
            self.data_stream = stream_table(file_path, dialect=kwargs["dialect"])
        else:
            self.data_stream = stream_table(file_path)

        self.column_list: List[str] = next(self.data_stream)

    def _get_an_element(self, index: int) -> Any:
        data = next(self.data_stream)
        elem: Dict[str, str] = {self.column_list[j]: data[j] for j in range(len(data))}
        return elem


class JsonReader(BaseReader):
    def __init__(
        self,
        file_path: str,
        chunk_size: int = 10,
        element_json_path: str = "item",
        **kwargs: Any,
    ):
        super().__init__(chunk_size, **kwargs)

        self.file_path = file_path
        self.fd = open(file_path, mode="r", encoding=encoding())

        self.ijson_object = ijson.items(self.fd, element_json_path)

    def _get_an_element(self, index: int) -> Any:
        return next(self.ijson_object)


class JsonLineReader(BaseReader):
    def __init__(self, file_path: str, chunk_size: int = 10, **kwargs: Any):
        super().__init__(chunk_size, **kwargs)

        self.file_path = file_path
        self.fd = open(file_path, mode="r", encoding=encoding())

    def _get_an_element(self, index: int) -> Any:
        data = self.fd.readline()
        if not data:
            raise StopIteration
        return json.loads(data)


class TextReader(BaseReader):
    def __init__(
        self,
        file_path: str,
        chunk_size: int = 10,
        using_file_as_element: bool = False,
        **kwargs: Any,
    ):
        super().__init__(chunk_size, **kwargs)

        self.file_path = file_path
        self.fd = open(file_path, mode="r", encoding=encoding())
        self.using_file_as_element = using_file_as_element

        self._is_folder = os.path.isdir(file_path)
        self._file_list: List[str] = []

        if self._is_folder:
            for root, dirs, files in os.walk(file_path):
                for file_name in files:
                    self._file_list.append(os.path.join(root, file_name))
        else:
            self._file_list = [file_path]

        self._current_fd: Optional[io.TextIOWrapper] = None
        self._current_file_index = 0

    def _close_and_switch(self) -> None:
        self._current_file_index += 1

        if not self._current_fd:
            return

        self._current_fd.close()
        self._current_fd = None

    def _get_an_element(self, index: int) -> Any:
        if self._current_file_index >= len(self._file_list):
            raise StopIteration

        if not self._current_fd:
            self._current_fd = open(
                self._file_list[self._current_file_index], mode="r", encoding=encoding()
            )

        if self.using_file_as_element:
            result = {QianfanDatasetPackColumnName: self._current_fd.read()}
            self._close_and_switch()
            return result

        content = self._current_fd.readline()
        if not content:
            self._close_and_switch()
            return self._get_an_element(index)

        return {QianfanDatasetPackColumnName: content}


class MapperReader(BaseReader):
    """
    专门用于封装 Table 的 Map 函数作为一个 Reader
    方便对外输出为一个 Arrow 文件并保存
    接受的 Callable 函数一定是需要返回一个用于排序的下标
    """

    def __init__(
        self,
        mapper_closure: Callable,
        chunk_size: int = 100,
        keep_original_order: bool = True,
        **kwargs: Any,
    ):
        super().__init__(chunk_size, **kwargs)
        # 设置生成器函数，以及判断是否需要保持顺序
        self.mapper_closure_func = mapper_closure
        self.keep_original_order = keep_original_order

        self.queue: Queue
        # 如果要保持顺序，则创建优先队列和其它附件
        if self.keep_original_order:
            self.data_id = 0
            self.queue = PriorityQueue()
        # 否则使用普通队列
        # 这两种队列都是原子的
        else:
            self.data_id = 0
            self.queue = Queue()

        # 一个可用 CPU 逻辑核一个迭代线程
        processing_thread_count = multiprocessing.cpu_count() + 1

        # 用于在顺序处理可行时唤醒的信号量
        self.processing_counter = threading.Semaphore()

        # 用于判断是否所有数据都已处理完毕的事件
        self.is_all_processing_done = threading.Event()

        # 用于同步所有处理线程的屏障和单词回调函数
        def _mark_process_done() -> None:
            self.is_all_processing_done.set()
            # 重新唤醒处理线程
            self.processing_counter.release()

        self.sync_done_barrier = threading.Barrier(
            processing_thread_count, _mark_process_done
        )

        def _process_closure() -> None:
            for elem in self.mapper_closure_func():
                assert isinstance(elem, tuple)
                data_id = elem[0]
                self.queue.put(elem)

                if not self.keep_original_order or (
                    self.keep_original_order and data_id <= self.data_id
                ):
                    self.processing_counter.release()

            self.sync_done_barrier.wait()

        for i in range(processing_thread_count):
            t = threading.Thread(target=_process_closure)
            t.start()

    def _get_an_element(self, index: int) -> List[Any]:
        # 循环检查输出队列是否为空
        while self.queue.empty():
            # 如果已经处理完毕，则跳出
            if self.is_all_processing_done.is_set():
                raise StopIteration()
            # 否则等待数据输入
            self.processing_counter.acquire()

        if self.keep_original_order:
            # 循环检查唤醒时拿到的数据是否是我们需要的数据
            while True:
                # 其实可以去掉超时，但是兜底
                data = self.queue.get(timeout=5)
                if data[0] != self.data_id:
                    self.queue.put(data)
                    self.processing_counter.acquire()
                    if self.is_all_processing_done.is_set():
                        raise StopIteration()
                else:
                    self.data_id += 1
                    break
        else:
            data = self.queue.get(timeout=5)

        return data[1]

    @override
    def get_chunk(self, chunk_size: int = 0) -> List[Any]:
        """get number of chunk from file"""
        try:
            data_list = self._get_an_element(0)
        except StopIteration:
            raise StopIteration()
        except Exception as e:
            err_msg = f"exception occurred during read csv file streamly: {e}"
            log_error(err_msg)
            raise e

        return data_list
