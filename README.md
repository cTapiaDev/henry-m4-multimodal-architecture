# Henry · AI Engineering - Módulo 4: Sistemas Multimodales, MCP y Arquitectura

Bienvenido al repositorio oficial del **Módulo 4**. Este repositorio mantiene las mismas convenciones de ingeniería, flujo con `uv` y modalidad dual (`offline` / `live`) del Módulo 3, enfocado en los desafíos de producción del Módulo 4:

- **L1 · IA que Ve y Crea:** Pipelines de Visión, Contratos Multimodales con Pydantic v2, Abstención Visual y _Self-Healing Loops_.
- **L2 · IA que Escucha y Habla:** Pipelines de Audio, cálculo de _Word Error Rate (WER)_ y evaluaciones acústicas.
- **L3 · Model Context Protocol (MCP):** Estandarización de servidores de contexto, herramientas y recursos desacoplados.
- **L4 & L5 · Arquitecturas Avanzadas y Proyecto Final:** Sistema multiagente de auditoría de contratos con parser multimodal y observabilidad completa en **Langfuse**.

---

## 🚀 Inicio Rápido (Quickstart)

1. Abre esta carpeta en **VS Code** (o tu editor preferido).
2. En una terminal integrada ejecuta:

```bash
uv sync
uv run python scripts/doctor.py
```

3. Verifica que todos los contratos y pipelines del módulo pasen las pruebas en modo `offline`:

```bash
uv run pytest -q
uv run python scripts/verify.py
```

---

## 🧭 Modos de Ejecución (`offline` vs `live`)

- **Modo `offline`(default):** Utiliza `ModeloGuionadoVision`, un motor determinista con fallas ópticas programadas a propósito para depurar validadores de Pydantic, bucles de autorreparación y reglas de _routing_ gratis y sin conexión.
- **Modo `live`:** Copia `.env.example` a `.env`, cambia `COURSE_MODE=live` y agrega tu `OPENAI_API_KEY` para conectar el pipeline directamente a modelos multimodales reales.

---

## 📂 Estructura del Repositorio

- **`src/henry_m4/`:** Paquete central del Módulo 4(`config.py`, `schemas.py`, `vision_engine.py`).
- **`clases/01_vision_y_contratos.py`:** Script interactivo en formato **Jupytext**(`# %%`) para ejecutar celda por celda durante la clase sincrónica.
- **`docs/TALLER_M4L1_CONSIGNA.md`:** Escenario, rúbrica y guía del taller grupal del banco.
- **`soluciones/m4l1_golden_case_banco.py`:** Solución oficial y generador del _Golden Case JSON_.
- **`scripts/doctor.py` y `scripts/verify.py`:** Herramientas de diagnóstico y validación continua.
- **`tests/test_m4l1_vision.py`:** Suite de pruebas automatizadas con `pytest`.
