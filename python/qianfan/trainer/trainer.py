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
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from qianfan.trainer.base import BaseAction, EventHandler
from qianfan.trainer.pipeline import Pipeline


class Trainer(ABC):
    """
    Base Trainer class, which focus on one step call to run the
    whole training process. which define the basic 3 methods to
    operate training.
    - run() run the specific training process like fine-tuning
    - resume() resume from the stopped, failed
    - stop() stop the training process
    """

    name: Optional[str] = ""
    """trainer name"""

    ppls: List[Pipeline] = []
    """
    Pipelines for training, there may be multiple pipelines in
    the training process.
    """
    result: List[Any] = []
    """pipeline running results, which may be an error or an object"""

    @abstractmethod
    def run(self, **kwargs: Any) -> "Trainer":
        """
        Trainer abstract method. For the diverse instance subclasses,
        Override this method to implement the specific training process.
        Returns:
            Trainer: Trainer instance
        """
        ...

    def start(self, join_on_exited: bool = False, **kwargs: Dict) -> "Trainer":
        """
        Trainer start method to start a training process in background.
        use `wait()` to block waiting for the training process to be
        finished.

        Returns:
            Trainer: Trainer instance
        """

        self.ppls[0].start(join_on_exited=join_on_exited, **kwargs)
        return self

    def wait(self, **kwargs: Dict) -> "Trainer":
        """
        Trainer wait method. Wait for the training process to finish.
        """
        self.ppls[0].wait(**kwargs)
        return self

    def stop(self, **kwargs: Dict) -> "Trainer":
        """
        Trainer  method. Subclasses implement it to support an
        more controllable usage in the concrete situations.
        Returns:
            Trainer: Trainer instance
        """
        self.ppls[0].stop(**kwargs)
        return self

    def resume(self, **kwargs: Dict) -> "Trainer":
        """
        Trainer resume method.

        Returns:
            PostPreTrain:
        """
        self.result[0] = self.ppls[0].resume(**kwargs)
        return self

    @property
    def status(self) -> str:
        """
        Trainer status。Implements different status for different process
        like fine-tuning, RLHF, PreTrain and so on.
        """
        return ""

    def get_evaluate_result(self) -> Any:
        """
        Receive the evaluate result from the pipeline. [coming soon].
        """
        raise NotImplementedError("trainer get_evaluate_result")

    def get_log(self) -> Any:
        """
        Receive the training log during the pipeline execution. [coming soon].
        """
        raise NotImplementedError("trainer get_log")

    def register_event_handler(
        self, event_handler: EventHandler, ppl_id: Optional[str] = None
    ) -> None:
        """
        Register the event handler to specific the ppls.
        Args:
            event_handler (EventHandler): The event handler instance.
        """
        for ppl in self.ppls:
            if ppl_id is None and ppl.id == ppl_id:
                ppl.register_event_handler(event_handler)
                break
            else:
                ppl.register_event_handler(event_handler)

    @property
    def actions(self) -> Dict[str, BaseAction]:
        """
        Get the available actions for trainer.
        Returns:
            List[str]: The list of action names.
        """
        return self.ppls[0].actions

    @property
    @abstractmethod
    def output(self) -> Any:
        ...

    @staticmethod
    @abstractmethod
    def list() -> List["Trainer"]:
        ...

    @staticmethod
    @abstractmethod
    def load(id: Optional[str] = None, file: Optional[str] = None) -> "Trainer":
        ...

    @abstractmethod
    def save(self, file: Optional[str] = None) -> None:
        ...

    def info(self) -> Dict:
        """
        Get the information of trainer.
        Returns:
            Dict: The dict of trainer info.
        """
        return {}

    @property
    @abstractmethod
    def id(self) -> str:
        ...
