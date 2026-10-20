import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    course_mode: str
    gemini_api_key: str
    groq_api_key: str
    gemini_model: str
    groq_model: str

    @property
    def is_live(self) -> bool:
        return self.course_mode.lower() == "live"

get_settings = lambda: Settings(
    course_mode=os.getenv("COURSE_MODE", "offline"),
    gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
    groq_api_key=os.getenv("GROQ_API_KEY", ""),
    gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
    groq_model=os.getenv("GROQ_MODEL", "llama-3.2-11b-vision-preview"),
)