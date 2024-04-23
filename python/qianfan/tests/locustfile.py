import logging
import random
from abc import ABC
from enum import Enum
from typing import Any
from typing import Dict
from typing import Literal

import locust
from locust import HttpUser
from locust import between, task, constant_throughput, constant_pacing
from pydantic import BaseModel

from pydantic import Field


class Url(Enum):
    chat: str = "/base/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions"
    completion: str = "/base/rpc/2.0/ai_custom/v1/wenxinworkshop/chat"
    service_list: str = "/console/wenxinworkshop/service/list"


token_total = "".join(["请"] * 3000)


class Req(ABC, BaseModel):
    url: str = Field(...)
    json: Dict[str, Any] = Field(default={})


class ChatReq(Req):
    url: str = Field(default=Url.chat.value)
    json: Dict[str, Any] = Field(default={"messages": ""})

    def generate(self, token_len: int = 10):
        global token_total
        dialog = token_total[:token_len]
        self.json["messages"] = [{"role": "user", "content": dialog}]
        logging.warning({"url": self.url, "json": self.json.copy()})
        return {
            "url": self.url,
            "json": self.json.copy(),
        }


class ServiceReq(Req):
    url: str = Field(default=Url.service_list.value)
    json: Dict[str, Any] = Field(
        default={"apiTypefilter": ["chat", "completions", "embeddings", "text2image"]}
    )

    def generate(self):
        svc_list = ["chat", "completions", "embeddings", "text2image"]
        self.json["apiTypefilter"] = random.choices(
            svc_list, k=random.randint(1, len(svc_list))
        )
        logging.warning({"url": self.url, "json": self.json.copy()})
        return {
            "url": self.url,
            "json": self.json.copy(),
        }


class ClientTest(HttpUser):
    wait_time = between(1, 5)

    @task(10)
    def chat_short(self):
        token_len = random.choice([3, 5, 10, 20])
        self.client.post(**(ChatReq().generate(token_len)))

    @task(5)
    def chat_mid(self):
        token_len = random.choice([30, 50, 100, 150])
        self.client.post(**(ChatReq().generate(token_len)))

    @task(1)
    def chat_long(self):
        token_len = random.choice([200, 500, 1000, 3000])
        self.client.post(**(ChatReq().generate(token_len)))

    @task(8)
    def svc_list(self):
        self.client.post(**(ServiceReq().generate()))


class QPS5Test(ClientTest):
    wait_time = constant_throughput(5)


class QPS50Test(ClientTest):
    wait_time = constant_throughput(50)


class RPM300Test(ClientTest):
    wait_time = constant_pacing(5)
