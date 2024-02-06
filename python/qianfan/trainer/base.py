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
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    TypeVar,
    Union,
)

from qianfan.common.runnable.base import ExecuteSerializable
from qianfan.errors import InternalError, InvalidArgumentError
from qianfan.trainer.consts import ActionState
from qianfan.trainer.event import Event, EventHandler, dispatch_event
from qianfan.utils import log_debug, log_error, utils

Input = TypeVar("Input")
Output = TypeVar("Output")


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
        self.id = id if id is not None else utils.generate_letter_num_random_id()
        self.name = name if name is not None else f"action_{self.id}"
        self.state = ActionState.Preceding
        self.event_dispatcher = event_handler

    def dumps(self) -> Optional[bytes]:
        """
        dumps action input bytes

        Returns:
            serialized bytes action data
        """
        return pickle.dumps(self)

    def loads(self, data: bytes) -> Any:
        """
        loads

        Parameters:
            data (bytes): load

        Returns:
            Any: action instance
        """
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
    def resume(self, **kwargs: Dict) -> Output:
        """
        Action resume from last input, sub-class should implement this method
        with their own resuming logic. BaseAction don not support last input
        storage, because it's not different from actions in their each action
        state.
        """
        ...

    def stop(self, **kwargs: Dict) -> None:
        """
        Action stop method, sub-class should implement this method
        with their own stop logic.
        """
        self.action_event(ActionState.Stopped)

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
        post_actions: Sequence[BaseAction] = [],
        event_handler: Optional[EventHandler] = None,
        **kwargs: Any,
    ) -> None:
        """

        Parameters:
            actions Sequence[BaseAction]:
                The actions to be executed in the pipeline.
            post_actions: Sequence[BaseAction]:
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
        self.post_actions = post_actions
        self._state: str = ""
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
        return self.exec_from(input, 0, **kwargs)

    def exec_from(
        self,
        input: Optional[Dict[str, Any]] = None,
        start: Optional[Union[int, str]] = 0,
        **kwargs: Dict,
    ) -> Dict[str, Any]:
        if isinstance(start, str):
            start_idx = self.seq.index(start)
        elif isinstance(start, int):
            start_idx = start
        else:
            raise InvalidArgumentError(
                "pipeline start must be index of sequence or key of action"
            )
        output: Dict[str, Any] = copy.deepcopy(input) if input is not None else {}
        for i, k in enumerate(self.seq):
            if self._stop:
                break
            if i < start_idx:
                continue
            if self.event_dispatcher is not None:
                self.action_event(
                    ActionState.Running, "pipeline running", {"action": k}
                )
            self._state = k
            output = self.actions[k].exec(input=output, **kwargs)
            err = output.get("error")
            if err is not None:
                if isinstance(err, BaseException):
                    raise err
                else:
                    raise InternalError(f"[get internal error: {err}")

        for next in self.post_actions:
            next.exec(copy.deepcopy(output), **kwargs)
        return output

    def __getitem__(self, key: str) -> Optional[BaseAction]:
        """
        get action by key, which is the action id.

        Args:
            key (str):
                action id generate when action was created.

        Returns:
            Optional[BaseAction]:
                action with the given id if exists, otherwise None.
        """
        return self.actions.get(key)

    @with_event
    def resume(self, **kwargs: Dict) -> Dict[str, Any]:
        """
        resume pipeline running from last stopped or failed action.
        """
        self._stop = False
        last_output = self.actions[self._state].resume(**kwargs)
        if self.seq[-1] == self._state:
            # last node return directly
            return last_output
        idx = self.seq.index(self._state) + 1
        return self.exec_from(last_output, idx, **kwargs)

    def stop(self, **kwargs: Dict) -> None:
        """
        stop pipeline running, only stop the actions not running.
        """
        with self._sync_lock:
            self._stop = True

        action = self.actions.get(self._state)
        if action is None:
            raise InternalError("unknown action to stop")
        else:
            action.stop()
        return super().stop()

    def register_event_handler(
        self, event_handler: EventHandler, action_id: Optional[str] = None
    ) -> None:
        """
        Register the event handler to specific the action.
        Args:
            event_handler (EventHandler): The event handler instance.
        """
        self.event_dispatcher = event_handler
        for id, action in self.actions.items():
            if action_id is None and id == action_id:
                action.event_dispatcher == event_handler
                break
            else:
                action.event_dispatcher = event_handler


class Trainer(ABC):
    """
    Base Trainer class, which focus on one step call to run the
    whole training process. which define the basic 3 methods to
    operate training.
    - run() run the specific training process like fine-tuning
    - resume() resume from the stopped, failed
    - stop() stop the training process
    """

    ppls: List[Pipeline] = []
    """
    Pipelines for training, there may be multiple pipelines in
    the training process.
    """
    result: List[Any] = []
    """pipeline running results, which may be an error or an object"""

    @abstractmethod
    def run(self, **kwargs: Dict) -> "Trainer":
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
