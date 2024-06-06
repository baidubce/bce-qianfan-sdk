#!/usr/bin/env python3
# coding=utf-8
"""
workers read shard data
"""

import logging
from typing import Any, Dict, Iterator

import gevent
import greenlet
from gevent.event import AsyncResult
from locust.env import Environment
from locust.runners import LocalRunner, MasterRunner, WorkerRunner

from qianfan.dataset.stress_test.yame.logger import logger

_results: Dict[int, AsyncResult] = {}


class Distributor(Iterator):
    """distributor"""

    def __init__(
        self,
        environment: Environment,
        iterator: Any,
        name: str = "distributor",
    ):
        """Register distributor method handlers and
        tie them to use the iterator that you pass.

        iterator is not used on workers, so you can leave it as None there.
        """
        self.iterator = iterator
        self.name = name
        self.environment = environment
        assert iterator or isinstance(
            self.environment.runner, WorkerRunner
        ), "iterator is a mandatory parameter when not on a worker runner"
        if self.environment.runner:
            # received on master
            def _distributor_request(
                environment: Environment, msg: Any, **kwargs: Any
            ) -> None:
                # do this in the background to avoid blocking
                # locust's client_listener loop
                gevent.spawn(
                    self._master_next_and_send, msg.data["gid"], msg.data["client_id"]
                )

            # received on worker
            def _distributor_response(
                environment: Environment, msg: Any, **kwargs: Any
            ) -> None:
                _results[msg.data["gid"]].set(msg.data)

            self.environment.runner.register_message(
                f"_{name}_request", _distributor_request
            )
            self.environment.runner.register_message(
                f"_{name}_response", _distributor_response
            )
        self.stop_iteration_num = 0

    def _master_next_and_send(self, gid: str, client_id: str) -> None:
        """master/local runner get next data and send to worker client"""
        # yame: quit/stop runner when iterator raises StopIteration.
        assert isinstance(self.environment.runner, (MasterRunner, LocalRunner))

        try:
            item = next(self.iterator)
        except StopIteration:
            self.stop_iteration_num += 1
            # if self.stop_iteration_num >= self.environment.runner.user_count:
            if self.stop_iteration_num >= self.environment.runner.target_user_count:
                logger.warning(
                    f"Distributor[{self.name}] StopIteration occurs"
                    f" {self.stop_iteration_num} times, and"
                    f" {self.environment.runner.target_user_count} users have been"
                    " spawned."
                )
                if self.environment.web_ui:
                    self.environment.runner.stop()
                else:
                    self.environment.runner.quit()
            return

        msg_kwargs = {}
        if isinstance(self.environment.runner, MasterRunner):
            msg_kwargs["client_id"] = client_id
        assert isinstance(self.environment.runner, (MasterRunner, LocalRunner))
        self.environment.runner.send_message(
            f"_{self.name}_response",
            {"item": item, "gid": gid},
            **msg_kwargs,
        )

    def __next__(self) -> Any:
        """Get the next data dict from iterator"""
        if (
            not self.environment.runner
        ):  # no need to do anything clever if there is no runner
            assert self.iterator
            return next(self.iterator)

        gid = greenlet.getcurrent().minimal_ident  # type: ignore

        if gid in _results:
            logging.warning("This user was already waiting for data. Strange.")

        _results[gid] = AsyncResult()
        assert isinstance(self.environment.runner, (WorkerRunner, LocalRunner))
        self.environment.runner.send_message(
            f"_{self.name}_request",
            {
                "gid": gid,
                "client_id": (
                    self.environment.runner.client_id
                    if isinstance(self.environment.runner, WorkerRunner)
                    else "0"
                ),
            },
        )
        item = _results[gid].get()["item"]  # this waits for the reply
        del _results[gid]
        return item
