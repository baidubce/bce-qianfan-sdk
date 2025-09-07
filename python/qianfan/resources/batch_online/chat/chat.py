from .completions import AsyncCompletions, Completions

class Chat():
    def completions(self, api_key: str) -> Completions:
        return Completions(api_key)


class AsyncChat():
    def completions(self,api_key: str) -> AsyncCompletions:
        return AsyncCompletions(api_key)