from openai import OpenAI
from config.keys import OPENROUTER_KEY

class AIService:
    _instance = None
    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            cls._client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=OPENROUTER_KEY,
            )
        return cls._client
