import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    course_mode: str
    openai_api_key: str
    model_vision: str
    model_agent: str
    reasoning_effort: str

    @property
    def is_live(self) -> bool:
        return self.course_mode.lower() == "live"

get_settings = lambda: Settings(
    course_mode=os.getenv("COURSE_MODE", "offline"),
    openai_api_key=os.getenv("OPENAI_API_KEY", ""),
    model_vision=os.getenv("OPENAI_MODEL_VISION", "gpt-6-luna"),
    model_agent=os.getenv("OPENAI_MODEL_AGENT", "gpt-6.1-sol"),
    reasoning_effort=os.getenv("OPENAI_REASONING_EFFORT", "low"),
)