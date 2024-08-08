# Copyright (c) 2024 Baidu, Inc. All Rights Reserved.
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
import os
import threading
import time
from typing import Any, Dict, Iterator, List, Optional, Sequence, Union

from qianfan.common.persister.persist import FilePersister
from qianfan.errors import InternalError, InvalidArgumentError
from qianfan.trainer.actions import (
    DeployAction,
    LoadDataSetAction,
    ModelPublishAction,
    TrainAction,
)
from qianfan.trainer.base import ActionState, BaseAction, EventHandler, with_event
from qianfan.utils.logging import log_error


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
        case_init_params: Optional[Dict] = None,
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
        self.current_action: str = ""
        self._sync_lock = threading.Lock()
        self._stop: bool = False
        self._last_output: Optional[Dict[str, Any]] = None
        self._case_init_params = case_init_params

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
        res: List[Any] = [{}]

        def _exec_helper(res: List[Any]) -> None:
            if len(res) == 0:
                return
            try:
                res[0] = self.exec_from(input, 0, **kwargs)
            except Exception as e:
                res[0] = e

        t = threading.Thread(target=_exec_helper, args=[res])
        t.start()

        while True:
            FilePersister.save(self)
            if isinstance(res[0], Exception):
                FilePersister.save(self)
                raise res[0]
            if self._stop:
                FilePersister.save(self)
                break
            time.sleep(10)

        return res[0]

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
        self._stop = False
        FilePersister.save(self)
        output: Dict[str, Any] = copy.deepcopy(input) if input is not None else {}
        for i, k in enumerate(self.seq):
            if self._stop:
                break
            if i < start_idx:
                continue
            if self.event_dispatcher is not None:
                self.action_event(
                    ActionState.Running,
                    "pipeline running",
                    {"action": k, "ppl_id": self.id},
                )
            self.current_action = k
            output = self.actions[k].exec(input=output, **kwargs)
            FilePersister.save(self)
            if output is not None:
                err = output.get("error")
                if err is not None:
                    if isinstance(err, BaseException):
                        raise err
                    else:
                        raise InternalError(f"[get internal error: {err}")

        for next in self.post_actions:
            next.exec(copy.deepcopy(output), **kwargs)
        self._stop = True
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
        last_output = self.actions[self.current_action].resume(**kwargs)
        if self.seq[-1] == self.current_action:
            # last node return directly
            return last_output
        idx = self.seq.index(self.current_action) + 1
        return self.exec_from(last_output, idx, **kwargs)

    def stop(self, **kwargs: Dict) -> "BaseAction":
        """
        stop pipeline running, only stop the actions not running.
        """
        with self._sync_lock:
            self._stop = True

        action = self.actions.get(self.current_action)
        if action is not None:
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

    @classmethod
    def _space(cls) -> str:
        return "pipeline"

    def persist(self) -> bytes:
        return self.serialize_helper.serialize(self._action_dict())

    def _action_dict(self) -> Dict:
        meta: Dict[str, Any] = {
            "id": self.id,
            "current_action": self.current_action,
            # "output": self._last_output,
        }
        meta["process_id"] = self.process_id if self.process_id else os.getpid()
        actions = []
        for action_id in self.seq:
            action_meta = self.actions[action_id]._action_dict()
            actions.append(action_meta)
        meta["actions"] = actions
        if self._case_init_params:
            meta["case_init_params"] = self._case_init_params
        return meta

    @classmethod
    def load(cls, b: bytes) -> "Pipeline":
        meta = cls.serialize_helper.deserialize(b)
        assert isinstance(meta, dict)
        try:
            return cls._load_from_dict(meta)
        except Exception as e:
            log_error(e)
            raise ValueError(
                "load pipeline error, please update qianfan or use `qianfan cache"
                " --clear` to clear all"
            )

    @classmethod
    def _load_from_dict(cls, meta: Dict[str, Any]) -> "Pipeline":
        actions: List = []
        for action_meta in meta.get("actions", []):
            action_type = action_meta.get("type")
            if action_type is None:
                raise ValueError("load pipeline error: action type is None")
            action_obj = Pipeline.load_action(action_type, action_meta)
            if action_obj is None:
                log_error(f"action {action_type} load error, raw: {action_meta}")
                continue
                # raise InternalError(f"action {action_type} load error")
            actions.append(action_obj)
        ppl = Pipeline(
            id=meta.get("id"),
            actions=actions,
            case_init_params=meta.get("case_init_params"),
        )
        assert isinstance(meta.get("current_action", ""), str)
        ppl.process_id = meta.get("process_id", "")
        ppl.current_action = meta.get("current_action", "")
        return ppl

    @staticmethod
    def load_action(action_type: str, meta: Dict[str, Any]) -> Optional[BaseAction]:
        if action_type == TrainAction.__name__:
            return TrainAction._load_from_dict(meta)
        if action_type == LoadDataSetAction.__name__:
            return LoadDataSetAction._load_from_dict(meta)
        if action_type == ModelPublishAction.__name__:
            return ModelPublishAction._load_from_dict(meta)
        if action_type == DeployAction.__name__:
            return DeployAction._load_from_dict(meta)
        # if action_type == EvaluateAction.__name__:
        # return EvaluateAction._load_from_dict(meta)
        return None

    def __len__(self) -> int:
        return len(self.actions)

    def __iter__(self) -> Iterator[BaseAction]:
        return iter([self.actions[i] for i in self.seq])
