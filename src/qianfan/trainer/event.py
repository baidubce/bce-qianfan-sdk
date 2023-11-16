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
