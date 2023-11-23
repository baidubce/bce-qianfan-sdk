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
import copy
import pickle
from abc import ABC, abstractmethod
from threading import Lock
from typing import Any, Callable, Dict, Generic, List, Optional, Sequence, TypeVar, cast

from qianfan.errors import InternalError
from qianfan.trainer.consts import ActionState
from qianfan.trainer.event import Event, EventHandler, dispatch_event
from qianfan.utils import utils

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

        Args:
            data (bytes): load

        Returns:
            Any: _description_
        """
        ...


class ExecuteSerializable(Executable[Input, Output], Serializable):
    ...


class BaseAction(ExecuteSerializable[Input, Output], ABC):
    """
    BaseAction is a reusable, atomic operation components that can be
    freely orchestrated for use in Pipelines.
    """

    def __init__(
        self,
        id: Optional[str] = None,
        name: Optional[str] = None,
        event_handler: Optional[EventHandler] = None,
        **kwargs: Dict[str, Any],
    ) -> None:
        """
        init method

        Parameters:
            id (Optional[str], optional):
                action id for identify action. Defaults to None.
            name (Optional[str], optional):
                action name. Defaults to None.
            event_handler (Optional[EventHandler], optional):
                event_handler implements for action state track. Defaults to None.
        """
        self.id = id if id is not None else utils.uuid()
        self.name = name if name is not None else f"actions_{self.id}"
        self.state = ActionState.Preceding
        self.event_dispatcher = event_handler

    def dumps(self) -> Optional[bytes]:
        return pickle.dumps(self)

    def loads(self, data: bytes) -> Any:
        return pickle.loads(data)

    @abstractmethod
    def exec(self, input: Optional[Input] = None, **kwargs: Dict) -> Output:
        """
        exec is a abstract method for execute action.

        Parameters:
            input (Optional[Input], optional): input. Defaults to None.

        Returns:
            Output: output
        """
        ...

    @abstractmethod
    def resume(self, input: Input, **kwargs: Dict) -> None:
        ...

    def stop(self) -> None:
        self.action_event(ActionState.Stopped)

    def action_error_event(self, e: Exception) -> None:
        """
        dispatch action error event

        Parameters:
            e (Exception): _description_
        """
        dispatch_event(
            self.event_dispatcher,
            Event(
                self.__class__.__name__ + self.id,
                ActionState.Error,
                f"action_error: action[{self.id}], msg:{str(e)}",
                {"error": str(e)},
            ),
        )

    def action_event(self, state: ActionState, msg: str = "", data: Any = None) -> None:
        """
        dispatch action event

        Parameters:
            state (ActionState): action state
            msg (str, optional): action custom description. Defaults to "".
            data (Any, optional): action custom data. Defaults to None.
        """
        dispatch_event(
            self.event_dispatcher,
            Event(
                f"{self.__class__.__name__}_{self.id}",
                state,
                f"action_event: action[{self.id}], msg:{msg}",
                data,
            ),
        )


def with_event(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    decorator for action state tracking with event.

    """

    def wrapper(self: BaseAction, input: Any, **kwargs: Any) -> Any:
        try:
            self.action_event(ActionState.Preceding, "", {})
            resp = func(self, input=input, **kwargs)
            self.action_event(ActionState.Done, "", resp)
            return resp
        except Exception as e:
            self.action_error_event(e)
            return {"error": e}

    return wrapper


class Pipeline(BaseAction[Dict[str, Any], Dict[str, Any]]):
    """
    Pipeline is a sequentially executed chain composed of multiple actions,
    and users can customize the action chain according to their needs. At
    any given moment, the Pipeline retains the id of the currently executing
    action, allowing users to retrieve information about the action currently
    in progress. By registering an EventHandler, user can listen to events
    generated during the Pipeline running process.
    """

    def __init__(
        self,
        actions: Sequence[BaseAction],
        next_actions: Sequence[BaseAction] = [],
        event_handler: Optional[EventHandler] = None,
        **kwargs: Any,
    ) -> None:
        """

        Parameters:
            actions Sequence[BaseAction]:
                The actions to be executed in the pipeline.
            next_actions: Sequence[BaseAction]:
                The actions to be executed after the pipeline is completed.
            event_handler: Optional[EventHandler]
                event_handler to receive events.
            kwargs (Any):
                Additional keyword arguments.

        ```
        ppl = Pipeline(
            actions=actions,
        )
        ```

        """
        super().__init__(event_handler=event_handler, **kwargs)
        self.actions: Dict[str, BaseAction] = {}
        self.seq: List[str] = []
        for action in actions:
            if action.id in self.actions:
                raise ValueError(f"action id {action.id} is duplicated")
            self.actions[action.id] = action
            self.seq.append(action.id)
        self.next_actions = next_actions
        self._state: Optional[Any] = None
        self._sync_lock = Lock()
        self._stop: bool = False
        self._last_output: Optional[Dict[str, Any]] = None

    @with_event
    def exec(
        self, input: Optional[Dict[str, Any]] = None, **kwargs: Dict
    ) -> Dict[str, Any]:
        """
        Parameters:
            input: Optional[Dict[str, Any]] input of the pipeline.
            kwargs: additional keyword arguments.
        Return:
            Dict[str, Any]: The output of the pipeline.
        """
        output: Dict[str, Any] = copy.deepcopy(input) if input is not None else {}
        for k in self.seq:
            if self._stop:
                break
            if self.event_dispatcher is not None:
                self.action_event(
                    ActionState.Running, "pipeline running", {"action": k}
                )
            self._state = k
            output = self.actions[k].exec(output, **kwargs)

            if output.get("error") is not None:
                raise InternalError(cast(str, output.get("error")))

        for next in self.next_actions:
            next.exec(copy.deepcopy(output), **kwargs)

        return output

    def __getitem__(self, key: str) -> Optional[BaseAction]:
        return self.actions.get(key)

    def resume(self, input: Dict[str, Any], **kwargs: Dict) -> None:
        """
        resume pipeline running from last stopped or failed action.
        """
        for k in self.seq:
            if k != self._state:
                continue
            self.actions[k].exec(input, **kwargs)
        return None

    def stop(self) -> None:
        """
        stop pipeline running, only stop the actions not running.
        """
        with self._sync_lock:
            self._stop = True

        return super().stop()


class Trainer(ABC):
    """
    Base Trainer class, which focus on one step call to run the
    whole training process. which define the basic 3 methods to
    operate training.
    - start() start the specific training process like fine-tuning
    - resume() resume from the stopped, failed
    - stop() stop the training process
    """

    ppls: List[Pipeline] = []
    error: Optional[Exception] = None
    result: List[Any] = []

    @abstractmethod
    def start(self, **kwargs: Dict) -> "Trainer":
        """
        Trainer abstract method. For the diverse instance subclasses,
        Override this method to implement the specific training process.
        Returns:
            Trainer: Trainer instance
        """
        ...

    @abstractmethod
    def stop(self, **kwargs: Dict) -> "Trainer":
        """
        Trainer abstract method. Subclasses implement it to support an
        more controllable usage in the concrete situations.
        Returns:
            Trainer: Trainer instance
        """
        return self

    @abstractmethod
    def resume(self, **kwargs: Dict) -> "Trainer":
        """
        Counter to stop method. User can resume the training process by
        calling resume() method.
        Returns:
            Trainer: Trainer instance
        """
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
