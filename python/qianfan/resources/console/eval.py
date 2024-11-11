from typing import Any, Dict, Optional

from qianfan.consts import Consts
from qianfan.resources.console.utils import _get_console_v2_query, console_api_request
from qianfan.resources.typing import QfRequest


class Eval:
    class V2:
        @classmethod
        def base_api_route(cls) -> str:
            """
            base api url route for service V2.

            Returns:
                str: base api url route
            """
            return Consts.ModelEvalV2API

        @classmethod
        @console_api_request
        def create_eval_task(
            cls,
            task_name: str,
            eval_object_type: str,
            eval_object_config: Dict[str, Any],
            eval_config: Dict[str, Any],
            description: str = "",
            **kwargs: Any,
        ) -> QfRequest:
            """
            create an evaluation task.

            Parameters:
            task_name: str,
                evaluation task name
            eval_object_type: str,
                the type of evaluation object
            eval_object_config: Dict[str, Any],
                info for evaluated object
            eval_config: Dict[str, Any],
                evaluation config
            description: str,
                evaluation task description

            kwargs:
                Additional keyword arguments that can be passed to customize
                the request.

            Note:
            The `@console_api_request` decorator is applied to this method, enabling
            it to send the generated QfRequest and return a QfResponse to the user.
            """
            req = QfRequest(
                method="POST",
                url=cls.base_api_route(),
                query=_get_console_v2_query(Consts.ModelEvalV2Create),
            )

            req.json_body = {
                k: v
                for k, v in {
                    **kwargs,
                    "taskName": task_name,
                    "evalObjectType": eval_object_type,
                    "evalObjectConfig": eval_object_config,
                    "evalConfig": eval_config,
                    "description": description,
                }.items()
                if v is not None
            }

            return req

        @classmethod
        @console_api_request
        def describe_eval_tasks(
            cls,
            eval_type: str,
            key_filter: Optional[str] = None,
            marker: Optional[str] = None,
            max_keys: Optional[int] = None,
            page_reverse: Optional[bool] = None,
            **kwargs: Any,
        ) -> QfRequest:
            """
            create an evaluation task.

            Parameters:
            eval_type: str,
                evaluation task type
            key_filter: Optional[str] = None,
                a filter field for filtering by task name, id and model version id
            marker: Optional[str] = None,
                job_id, the marker of the first page.
            max_keys: Optional[int] = None,
                max keys of the page.
            page_reverse: Optional[bool] = None,
                page reverse or not.

            kwargs:
                Additional keyword arguments that can be passed to customize
                the request.

            Note:
            The `@console_api_request` decorator is applied to this method, enabling
            it to send the generated QfRequest and return a QfResponse to the user.
            """
            req = QfRequest(
                method="POST",
                url=cls.base_api_route(),
                query=_get_console_v2_query(Consts.ModelEvalV2DescribeTasks),
            )

            req.json_body = {
                k: v
                for k, v in {
                    **kwargs,
                    "evalType": eval_type,
                    "keyFilter": key_filter,
                    "marker": marker,
                    "maxKeys": max_keys,
                    "pageReverse": page_reverse,
                }.items()
                if v is not None
            }

            return req

        @classmethod
        @console_api_request
        def describe_eval_task(
            cls,
            task_id: str,
            **kwargs: Any,
        ) -> QfRequest:
            """
            create an evaluation task.

            Parameters:
            task_id: str,
                evaluation task id

            kwargs:
                Additional keyword arguments that can be passed to customize
                the request.

            Note:
            The `@console_api_request` decorator is applied to this method, enabling
            it to send the generated QfRequest and return a QfResponse to the user.
            """
            req = QfRequest(
                method="POST",
                url=cls.base_api_route(),
                query=_get_console_v2_query(Consts.ModelEvalV2DescribeTask),
                json_body={
                    "taskId": task_id,
                },
            )

            return req

        @classmethod
        @console_api_request
        def describe_eval_task_report(
            cls,
            task_id: str,
            **kwargs: Any,
        ) -> QfRequest:
            """
            create an evaluation task.

            Parameters:
            task_id: str,
                evaluation task id

            kwargs:
                Additional keyword arguments that can be passed to customize
                the request.

            Note:
            The `@console_api_request` decorator is applied to this method, enabling
            it to send the generated QfRequest and return a QfResponse to the user.
            """
            req = QfRequest(
                method="POST",
                url=cls.base_api_route(),
                query=_get_console_v2_query(Consts.ModelEvalV2DescribeTaskReport),
                json_body={
                    "taskId": task_id,
                },
            )

            return req

        @classmethod
        @console_api_request
        def delete_eval_task(
            cls,
            task_id: str,
            **kwargs: Any,
        ) -> QfRequest:
            """
            create an evaluation task.

            Parameters:
            task_id: str,
                evaluation task id

            kwargs:
                Additional keyword arguments that can be passed to customize
                the request.

            Note:
            The `@console_api_request` decorator is applied to this method, enabling
            it to send the generated QfRequest and return a QfResponse to the user.
            """
            req = QfRequest(
                method="POST",
                url=cls.base_api_route(),
                query=_get_console_v2_query(Consts.ModelEvalV2DeleteTask),
                json_body={
                    "taskId": task_id,
                },
            )

            return req
