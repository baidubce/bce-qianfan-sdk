from typing import Any, Optional

from qianfan.trainer.consts import ActionState


class Event:
    action_id: Optional[str] = None
    action_state: ActionState
    description: Optional[str] = None
    data: Any = None

    def __init__(
        self,
        action_id: Optional[str],
        state: ActionState,
        description: Optional[str] = None,
        data: Any = None,
    ):
        self.action_id = action_id
        self.action_state = state
        self.description = description
        self.data = data


class EventHandler:
    def dispatch(self, event: Event) -> None:
        return None


def dispatch_event(
    event_handler: Optional[EventHandler] = None, event: Optional[Event] = None
) -> None:
    if event_handler is not None and event is not None:
        event_handler.dispatch(event)
