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
from typing import Any, Optional, Type

from qianfan.trainer.consts import ActionState


class Event:
    """Event is the event container for the various nodes in the
    execution process of Action, and for each different Action,
    it can be abstracted into five common ActionStates. For multi-Action
    tasks at the Pipeline level, numerous Events will be generated during
    the process. Through EventHandler, custom callback events can be
    registered and listened to, enabling the insertion of various
    types of callbacks or intermediate task functions in the Pipeline
    nodes.
    """

    action_class: Type
    action_id: str
    action_state: ActionState
    description: Optional[str] = None
    data: Any = None

    def __init__(
        self,
        action_class: Type,
        action_id: str,
        state: ActionState,
        description: Optional[str] = None,
        data: Any = None,
    ):
        """
        init method of event

        Parameters:
            action_class (type):
                The class type of the Action.
            action_id (str):
                The id of the Action, auto-generated when action is created.
            action_state (ActionState):
                The state of the Action.
            description (str):
                The description of the event.
            data (Any):
                for different event state, the data may be different.
        """
        self.action_class = action_class
        self.action_id = action_id
        self.action_state = state
        self.description = description
        self.data = data

    def __repr__(self) -> str:
        """
        str repr of event for log or display

        Returns:
            str: fields str of event
        """
        return str(self.__dict__)


class EventHandler:
    """
    EventHandler serves as a mechanism for registering and
    listening to custom callback events in the execution process of Actions.
    It facilitates the management of events occurring at different nodes during
    the execution of Actions within a Pipeline.
    """

    def dispatch(self, event: Event) -> None:
        """_summary_

        Parameters:
            event (Event):
                event to dispatch to user custom handler

        """
        return None


def dispatch_event(
    event_handler: Optional[EventHandler] = None, event: Optional[Event] = None
) -> None:
    """
    method to dispatch event from the event handler.

    Args:
        event_handler (Optional[EventHandler], optional):
            event handler. Defaults to None.
        event (Optional[Event], optional):
            runtime generated event instance. Defaults to None.
    """
    if event_handler is not None and event is not None:
        event_handler.dispatch(event)
