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
import json
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

    def __repr__(self) -> str:
        return json.dumps(self.__dict__)


class EventHandler:
    def dispatch(self, event: Event) -> None:
        return None


def dispatch_event(
    event_handler: Optional[EventHandler] = None, event: Optional[Event] = None
) -> None:
    if event_handler is not None and event is not None:
        event_handler.dispatch(event)
