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
from typing import Any, Callable, Dict, Generic, List, Optional, Sequence, TypeVar, cast

from qianfan.errors import InternalError
from qianfan.trainer.consts import ActionState
from qianfan.trainer.event import Event, EventHandler, dispatch_event
from qianfan.utils import utils

Input = TypeVar("Input")
Output = TypeVar("Output")


class Executable(Generic[Input, Output], ABC):
    @abstractmethod
    def exec(self, input: Input, **kwargs: Dict) -> Output:
        ...


class Serializable(ABC):
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
        ...


class ExecuteSerializable(Executable[Input, Output], Serializable):
    ...


class BaseAction(ExecuteSerializable[Input, Output], ABC):
    def __init__(
        self,
        id: Optional[str] = None,
        name: Optional[str] = None,
        event_handler: Optional[EventHandler] = None,
        **kwargs: Dict[str, Any]
    ) -> None:
        self.id = id if id is not None else utils.uuid()
        self.name = name if name is not None else "actions_{}".format(self.id)
        self.state = ActionState.Preceding
        self.event_dispatcher = event_handler

    def _identifying(self) -> Optional[str]:
        return self.id

    def dumps(self) -> Optional[bytes]:
        return pickle.dumps(self)

    def loads(self, data: bytes) -> Any:
        return pickle.loads(data)

    def pre_process(self) -> None:
        ...

    def post_process(self) -> None:
        ...

    @abstractmethod
    def exec(self, input: Input, **kwargs: Dict) -> Output:
        ...

    @abstractmethod
    def resume(self, input: Input, **kwargs: Dict) -> None:
        ...

    def stop(self) -> None:
        self.action_event(ActionState.Stopped)

    def action_error_event(self, e: Exception) -> None:
        dispatch_event(
            self.event_dispatcher,
            Event(
                self.__class__.__name__ + self.id,
                ActionState.Error,
                "action_error: action[{}], msg:{}".format(self.id, str(e)),
                {"error": str(e)},
            ),
        )

    def action_event(self, state: ActionState, msg: str = "", data: Any = None) -> None:
        dispatch_event(
            self.event_dispatcher,
            Event(
                "{}_{}".format(self.__class__.__name__, self.id),
                state,
                "action_event: action[{}], msg:{}".format(self.id, msg),
                data,
            ),
        )


def with_state(func: Callable[..., Any]) -> Callable[..., Any]:
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
        **kwargs: Any
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
                raise ValueError("action id {} is duplicated".format(action.id))
            self.actions[action.id] = action
            self.seq.append(action.id)
        self.next_actions = next_actions

    @with_state
    def exec(self, input: Dict[str, Any] = {}, **kwargs: Dict) -> Dict[str, Any]:
        output: Dict[str, Any] = copy.deepcopy(input) if input is not None else {}
        for k in self.seq:
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

    def __getitem__(self, key: str) -> BaseAction:
        return self.actions[key]

    def resume(self, input: Dict[str, Any], **kwargs: Dict) -> None:
        return None


class Trainer(ABC):
    ppls: List[Pipeline] = []
    status: Optional[str] = None
    error: Optional[Exception] = None
    result: List[Any] = []

    @abstractmethod
    def start(self) -> "Trainer":
        ...

    def stop(self) -> "Trainer":
        return self

    def resume(self) -> "Trainer":
        return self

    def get_evaluate_result(self) -> Any:
        raise NotImplementedError("trainer get_evaluate_result")

    def get_log(self) -> Any:
        raise NotImplementedError("trainer get_log")
