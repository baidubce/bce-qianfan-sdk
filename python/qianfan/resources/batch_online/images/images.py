from .generations import AsyncGenerations, Generations

class Images():
    def generations(self, api_key: str) -> Generations:
        return Generations(api_key)


class AsyncImages():
    def generations(self,api_key: str) -> AsyncGenerations:
        return AsyncGenerations(api_key)