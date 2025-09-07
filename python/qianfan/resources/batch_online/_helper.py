import asyncio
import logging
import time

from typing import Any, Awaitable, Callable, Optional, TypeVar
from datetime import datetime, timedelta
from ...errors import ArgumentNotFoundError, RequestTimeoutError
from openai import OpenAI, APIConnectionError, APIStatusError
from openai.types.chat.chat_completion import ChatCompletion as OpenAIChatCompletion

R = TypeVar("R")

def request_with_retry(
    deadline: int,
    func: Callable[..., R],
    *args,
    **kwargs,
) -> R:
    retry_times = 0
    while True:

        if datetime.now() > deadline:
            raise RequestTimeoutError()

        try:
            return func(*args, **kwargs)
        except APIConnectionError:
            wait_time = _calculate_retry_wait_time(retry_times)
            log.debug(
                "Retry due to connection error, wait time: %is, retry times: %i",
                waitTime,
                retry_times,
            )

            if datetime.now() + timedelta(seconds=wait_time) > deadline:
                raise RequestTimeoutError(None, None)

            time.sleep(waitTime)
        except APIStatusError as err:
            if not _should_retry(err.response):
                raise err

        retry_times = retry_times + 1


async def async_request_with_retry(
    deadline: datetime,
    func: Callable[..., R],
    *args,
    **kwargs,
) -> R:
    retry_times = 0
    while True:

        if datetime.now() > deadline:
            raise RequestTimeoutError()

        try:
            return await func(*args, **kwargs)
        except APIConnectionError:
            wait_time = _calculate_retry_wait_time(retry_times)
            log.debug(
                "Retry due to connection error, wait time: %is, retry times: %i",
                waitTime,
                retry_times,
            )

            if datetime.now() + timedelta(seconds=wait_time) > deadline:
                raise RequestTimeoutError(None, None)

            await asyncio.sleep(waitTime)
        except APIStatusError as err:
            if not _should_retry(err.response):
                raise err

        retry_times = retry_times + 1


def calculate_request_last_time(timeout: int):
    """
    calculate the last time of request based on timeout
    """

    if timeout is None or timeout <= 0:
        timeout = 24 * 3600 # default timeout is 24 hours

    timeout_seconds = 0
    if isinstance(timeout, int):
        timeout_seconds = timeout
    else:
        raise TypeError(
            "timeout type {} is not supported".format(type(timeout))
        )

    # calculate the last time of request based on timeout
    return datetime.now() + timedelta(seconds=timeout_seconds)


def _calculate_retry_wait_time(retry_times) -> float:
    """
    retry backoff
    """

    max_retry_delay = consts.MAX_RETRY_DELAY
    initial_retry_delay = consts.INITIAL_RETRY_DELAY

    nb_retries = min(retry_times, max_retry_delay / initial_retry_delay)

    sleep_seconds = min(initial_retry_delay * pow(2, nb_retries), max_retry_delay)

    jitter = 1 - 0.25 * random()
    timeout = sleep_seconds * jitter
    return timeout if timeout >= 0 else 0


def _should_retry(response):
    """
    check if the request should be retried
    """

    # Retry on rate limits.
    if response.status_code == 429:
        return True

    # Retry internal errors.
    if response.status_code >= 500:
        return True

    return False