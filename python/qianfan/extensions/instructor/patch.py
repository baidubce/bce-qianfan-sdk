from typing import Any, ParamSpec, Type, TypeVar

from instructor.function_calls import Mode
from instructor.patch import handle_response_model, retry_sync
from pydantic import BaseModel

from qianfan import ChatCompletion

T_Model = TypeVar("T_Model", bound=BaseModel)
T_Retval = TypeVar("T_Retval")
T_ParamSpec = ParamSpec("T_ParamSpec")
T = TypeVar("T")


class OpenAIResponse:
    data: dict = {}

    def __init__(self) -> None:
        self.data = {}

    def __getattr__(self, name: str) -> Any:
        return self.data.get(name)


def from_dict_obj(dict) -> Any:
    res = OpenAIResponse()
    res.data = dict
    return res


def patch(d: ChatCompletion, mode=Mode.FUNCTIONS):
    func = d.do

    def _request(**kwargs) -> OpenAIResponse:
        resp = func(**kwargs)
        result = from_dict_obj(resp.body)
        if resp.get("result") is not None:
            if resp.get("function_call"):
                msg = from_dict_obj(
                    {
                        "role": "assistant",
                        "content": resp.get("result"),
                        "function_call": from_dict_obj(resp.get("function_call")),
                    }
                )
                choice = from_dict_obj(
                    {"message": msg, "finish_reason": "stop", "index": 0}
                )
            else:
                msg = from_dict_obj(
                    {"role": "assistant", "content": resp.get("result")}
                )
                choice = from_dict_obj(
                    {"message": msg, "finish_reason": "function_call", "index": 0}
                )

            result.data["choices"] = [choice]
        return result

    def new_create_sync(
        response_model: Type[T_Model] = None,
        validation_context: dict = None,
        max_retries: int = 1,
        *args: Any,
        **kwargs: Any
    ) -> T_Model:
        response_model, new_kwargs = handle_response_model(
            response_model=response_model, mode=mode, **kwargs
        )
        response = retry_sync(
            func=_request,
            response_model=response_model,
            validation_context=validation_context,
            max_retries=max_retries,
            mode=mode,
            args=args,
            kwargs=new_kwargs,
        )

        return response

    d.do = new_create_sync
    return d.do
