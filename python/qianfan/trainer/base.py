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
from abc import ABC, abstractmethod
from typing import (
    Any,
    Callable,
    Dict,
    Optional,
    TypeVar,
)

from qianfan.common.persister.base import Persistent
from qianfan.common.runnable.base import ExecuteSerializable
from qianfan.trainer.consts import ActionState
from qianfan.trainer.event import Event, EventHandler, dispatch_event
from qianfan.utils import log_debug, log_error, utils

Input = TypeVar("Input")
Output = TypeVar("Output")


class BaseAction(ExecuteSerializable[Input, Output], Persistent, ABC):
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
        self.id = id if id is not None else utils.generate_letter_num_random_id()
        self.name = name if name is not None else f"action_{self.id}"
        self.state = ActionState.Preceding
        self.event_dispatcher = event_handler

    def persist(self) -> bytes:
        return b""

    @classmethod
    def load(cls, b: bytes) -> "BaseAction":
        meta = cls.serialize_helper.deserialize(b)
        assert isinstance(meta, dict)
        return cls._load_from_dict(meta)

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
    def resume(self, **kwargs: Dict) -> Output:
        """
        Action resume from last input, sub-class should implement this method
        with their own resuming logic. BaseAction don not support last input
        storage, because it's not different from actions in their each action
        state.
        """
        ...

    def stop(self, **kwargs: Dict) -> "BaseAction":
        """
        Action stop method, sub-class should implement this method
        with their own stop logic.
        """
        super().stop()
        self.action_event(ActionState.Stopped)
        return self

    def action_error_event(self, e: Exception) -> None:
        """
        dispatch action error event

        Parameters:
            e (Exception): action runtime error
        """
        dispatch_event(
            self.event_dispatcher,
            Event(
                self.__class__,
                self.id,
                ActionState.Error,
                (
                    f"action_error: action_type[{self.__class__.__name__}]"
                    f" action_id[{self.id}], msg:{str(e)}"
                ),
                {"error": str(e)},
            ),
        )

    def action_event(self, state: ActionState, msg: str = "", data: Any = None) -> None:
        """
        dispatch action event

        Parameters:
            state (ActionState): action state
            msg (str, optional): action custom dfscription. Defaults to "".
            data (Any, optional): action custom data. Defaults to None.
        """
        dispatch_event(
            self.event_dispatcher,
            Event(
                self.__class__,
                self.id,
                state,
                (
                    f"action_event: action_type[{self.__class__.__name__}]"
                    f" action_id[{self.id}], msg:{msg}"
                ),
                data,
            ),
        )

    @classmethod
    def action_type(cls) -> str:
        return "base"

    @classmethod
    def _space(cls) -> str:
        return "action"

    def _identity(self) -> str:
        return self.id

    def _init_params(self) -> Dict:
        return {}

    def _input_dict(self) -> Dict:
        return {}

    def _output_dict(self) -> Dict:
        return {}

    @abstractmethod
    def _action_dict(self) -> Dict:
        ...

    @classmethod
    @abstractmethod
    def _load_from_dict(cls, meta: Dict[str, Any]) -> "BaseAction":
        ...


def with_event(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    decorator for action state tracking with event.

    """

    def wrapper(self: BaseAction, **kwargs: Any) -> Any:
        """
        method wrapper
        """
        try:
            log_debug(f"action[{self.__class__.__name__}][{self.id}] Preceding")
            self.action_event(ActionState.Preceding, "", {})
            resp = func(self, **kwargs)
            self.action_event(ActionState.Done, "", resp)
            log_debug(f"action[{self.__class__.__name__}][{self.id}] Done")
            return resp
        except Exception as e:
            log_error(f"action[{self.__class__.__name__}][{self.id}] error {e}")
            self.action_error_event(e)
            # return {"error": e}
            raise e

    return wrapper
