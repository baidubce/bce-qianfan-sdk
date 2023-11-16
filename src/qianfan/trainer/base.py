import copy
import pickle
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Sequence, TypeVar

from pydantic import BaseModel
from qianfan.trainer.consts import ActionState
from qianfan.trainer.event import Event, EventHandler

Input = TypeVar("Input")
Output = TypeVar("Output")


class Executable(Generic[Input, Output], ABC):
    @abstractmethod
    def exec(self, input: Optional[Input], **kwargs: Dict) -> Optional[Output]:
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
    id: Optional[str] = None
    name: Optional[str] = None
    state: ActionState = ActionState.Preceding
    event_dispatcher: EventHandler = None

    def __init__(
        self,
        id: Optional[str] = None,
        name: Optional[str] = None,
        event_handler: Optional[EventHandler] = None,
        **kwargs: Any
    ) -> None:
        self.id = id if id is not None else str(uuid.uuid4())
        self.name = name if name is not None else "actions_{}".format(self.id)
        self.state = ActionState.Preceding
        self.event_dispatcher = event_handler

    def _identifying(self) -> Optional[str]:
        return self._id

    def dumps(self) -> Optional[bytes]:
        return pickle.dumps(self)

    def loads(self, data: bytes) -> Any:
        return pickle.loads(data)

    def pre_process(self) -> None:
        ...
        # self._event_dispatcher.dispatch(Event(self.id, ActionState.Preceding))

    def post_process(self) -> None:
        ...
        # e = Event(self.id, ActionState.Done)
        # self._event_dispatcher.dispatch(e)

    def exec(self, input: Optional[Input] = None, **kwargs: Dict) -> Optional[Output]:
        # self.pre_process()
        self._event_dispatcher.dispatch(Event(self.id, ActionState.Done))
        # self.post_process()

    def resume(self, data: Optional[Input] = None, **kwargs: Dict) -> Optional[Output]:
        self.pre_process()
        self._event_dispatcher.dispatch(Event(self.id, ActionState.Done))
        self.post_process()

    def stop(self) -> None:
        self._event_dispatcher.dispatch(Event(self.id, ActionState.Stopped))


class Pipeline(BaseAction[Dict[str, Any], Dict[str, Any]]):
    _actions: Dict[str, BaseAction] = None
    _seq: Sequence[str] = None
    _next_actions: Sequence[BaseAction] = None
    _state: str = None
    _error: Exception = None

    def __init__(
        self,
        actions: Sequence[BaseAction],
        id: str = None,
        name: str = None,
        next_actions: Sequence[BaseAction] = None,
        event_handler: EventHandler = None,
        **kwargs: Any
    ) -> None:
        super().__init__(id, name, event_handler, **kwargs)
        self._actions = {}
        self._seq = []
        for action in actions:
            if action.id in self._actions:
                raise ValueError("action id {} is duplicated".format(action.id))
            self._actions[action.id] = action
            self._seq.append(action.id)
        self._next_actions = next_actions

    def exec(
        self, input: Optional[Dict[str, Any]] = None, **kwargs: Dict
    ) -> Dict[str, Any] | None:
        output: Dict[str, Any] = copy.deepcopy(input) if input is not None else {}
        for k in self._seq:
            # self._event_dispatcher.dispatch(
            #     Event(self.id, ActionState.Running, "actions exec...", {"action": k})
            # )
            output = self._actions[k].exec(output, **kwargs)
            self._state = k
        return output

    def resume(self, data: Dict[str, Any] = None, **kwargs: Dict) -> Dict[str, Any]:
        return super().resume(data, **kwargs)

    def stop(self) -> None:
        return super().stop()


class Trainer(ABC):
    ppls: List[Pipeline] = None
    status: Optional[str] = None
    error: Exception = None
    result: List[Any] = None

    @abstractmethod
    def start(self) -> None:
        ...

    def stop(self) -> None:
        ...

    def resume(self) -> None:
        ...

    def get_evaluate_result() -> Any:
        raise NotImplementedError("trainer get_evaluate_result")

    def get_log() -> Any:
        raise NotImplementedError("trainer get_log")
