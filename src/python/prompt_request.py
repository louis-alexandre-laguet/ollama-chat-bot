from typing import Optional
from pydantic import BaseModel

class PromptRequest(BaseModel):
    """
    Pydantic model to validate the structure of the request body for prompt generation.
    """
    prompt: str
    top_n: Optional[int] = None
    num_ctx: int = 2048
    temperature: float = 0.8
    repeat_last_n: int = 64
    repeat_penalty: float = 1.1