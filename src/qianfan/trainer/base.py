import copy
import pickle
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Sequence, TypeVar

from qianfan.trainer.consts import ActionState
from qianfan.trainer.event import Event, EventHandler, dispatch_event

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
        self.id = id if id is not None else str(uuid.uuid4())
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
        dispatch_event(self.event_dispatcher, Event(self.id, ActionState.Stopped))


class Pipeline(BaseAction[Dict[str, Any], Dict[str, Any]]):
    def __init__(
        self,
        actions: Sequence[BaseAction],
        id: Optional[str] = None,
        name: Optional[str] = None,
        next_actions: Sequence[BaseAction] = [],
        event_handler: Optional[EventHandler] = None,
        **kwargs: Any
    ) -> None:
        super().__init__(id, name, event_handler, **kwargs)
        self.actions: Dict[str, BaseAction] = {}
        self.seq: List[str] = []
        for action in actions:
            if action.id in self.actions:
                raise ValueError("action id {} is duplicated".format(action.id))
            self.actions[action.id] = action
            self.seq.append(action.id)
        self.next_actions = next_actions

    def exec(self, input: Dict[str, Any], **kwargs: Dict) -> Dict[str, Any]:
        output: Dict[str, Any] = copy.deepcopy(input) if input is not None else {}
        for k in self.seq:
            if self.event_dispatcher is not None:
                self.event_dispatcher.dispatch(
                    Event(
                        self.id, ActionState.Running, "actions exec...", {"action": k}
                    )
                )
            output = self.actions[k].exec(output, **kwargs)
            self._state = k
        for next in self.next_actions:
            pass

        return output

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
