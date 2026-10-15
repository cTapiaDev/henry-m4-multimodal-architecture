import sys
from henry_m4.config import get_settings


def ejecutar_diagnostico() -> int:
    settings = get_settings()
    print("🩺 HENRY AI ENGINEERING · MÓDULO 4 DOCTOR")
    print("-" * 50)
    print(f"🐍 Python Version : {sys.version.split()[0]}")
    print(f"⚙️  COURSE_MODE    : {settings.course_mode}")
    print(f"👁️  Vision Model   : {settings.model_vision}")
    print(f"🤖 Agent Model    : {settings.model_agent}")

    if settings.is_live and not settings.openai_api_key.startswith("sk-"):
        print("❌ ERROR: COURSE_MODE='live' requiere configurar OPENAI_API_KEY válida en .env")
        return 1

    print("✅ Entorno del Módulo 4 verificado correctamente. Listo para ejecutar clases y tests.")
    return 0


if __name__ == "__main__":
    raise SystemExit(ejecutar_diagnostico())