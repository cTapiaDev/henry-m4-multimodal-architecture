# %% [markdown]
# # M4L1 · IA que Ve y Crea: Visión, Contratos Multimodales y Self-Healing
#
# En el Módulo 3 construyeron agentes confiables con `buscar_archivo`, validación de citas y abstención sobre texto.
# En el **Módulo 4** llevamos esa misma disciplina de ingeniería al mundo **Multimodal (Visión y Audio)**.
#
# ### Pregunta central de esta clase:
# **¿Qué NO puede hacer un prompt por sí solo cuando procesamos documentos reales (manuscritos, borrosos o escaneados)?**

# %% [1] Inspección del Contrato Visual y Abstención
import json
from henry_m4.schemas import SolicitudCreditoBancario
from henry_m4.vision_engine import PipelineVisionAutoreparable

print("✅ Esquema JSON generado automáticamente por Pydantic v2 para enviar al VLM:")
print(json.dumps(SolicitudCreditoBancario.model_json_schema(), indent=2, ensure_ascii=False)[:900] + "\n... [truncado]")

# %% [2] Falla de lectura en manuscrito y Bucle de Autorreparación
pipeline = PipelineVisionAutoreparable(max_intentos=3)

resultado_manuscrito = pipeline.procesar_formulario("form_02_manuscrito.png")

print(f"📄 Archivo procesado: {resultado_manuscrito.archivo_origen}")
print(f"🔄 Intentos requeridos: {resultado_manuscrito.intentos_utilizados}")
print("⚠️ Bitácora de intercepción de Pydantic (@model_validator):")
for err in resultado_manuscrito.bitacora_errores_pydantic:
    print(f"   ❌ {err}")

print(f"\n✅ Monto corregido tras Self-Healing: USD {resultado_manuscrito.datos_validados.monto_credito_solicitado:,.2f}")
print(f"🧭 Decisión de Ruteo: {resultado_manuscrito.decision_ruteo.value}")
print(f"📝 Motivo: {resultado_manuscrito.motivo_ruteo}")


# %% [3] Escenarios del Banco y el Golden Case JSON
archivos_lote = [
    "form_01_limpio.png",
    "form_02_manuscrito.png",
    "form_03_borroso.png",
]

for archivo in archivos_lote:
    res = pipeline.procesar_formulario(archivo)
    print("=" * 80)
    print(f"📌 CASO: {res.archivo_origen} | Intentos: {res.intentos_utilizados} | Ruteo: {res.decision_ruteo.value}")
    print(f"   Motivo: {res.motivo_ruteo}")
    if archivo == "form_03_borroso.png":
        print("\n🏆 GOLDEN CASE JSON (Escenario Crítico con Abstención Visual y Ruteo HITL):")
        print(res.model_dump_json(indent=2))
# %%


# %% [markdown]
# ---
# ### 🔴 MODO LIVE: Procesando Imágenes Reales con Google Gemini API
# A continuación conectamos nuestro pipeline a la API real de visión para procesar fotos físicas 1 a 1.
# ---

# %% [4] Caso 1: Procesar formulario Limpio en MODO LIVE
import os
from pathlib import Path
from dotenv import load_dotenv

if Path.cwd().name == "clases":
    os.chdir(Path.cwd().parent)

load_dotenv(override=True)

from henry_m4.config import get_settings
from henry_m4.vision_engine import PipelineVisionAutoreparable

settings = get_settings()
print("=" * 80)
print(f"🚀 INICIANDO MODO LIVE | Proveedor: Google API | Modelo: {settings.gemini_model}")
print("👁️ Analizando píxeles reales de 'form_01_limpio.jpg'...")

pipeline_live = PipelineVisionAutoreparable(max_intentos=3, forzar_live=True)
res_limpio = pipeline_live.procesar_formulario("assets/formularios/form_01_limpio.jpg")

if res_limpio.datos_validados:
    datos = res_limpio.datos_validados
    print("\n✅ DATOS EXTRAÍDOS POR GEMINI:")
    print(f"👤 Titular: {datos.nombre_solicitante}")
    print(f"💰 Ingreso Mensual: {datos.ingreso_mensual_declarado}")
    print(f"💵 Monto Solicitado: {datos.monto_credito_solicitado}")
    print(f"✍️ Firma Detectada: {datos.posee_firma_autografa}")
    print(f"📊 Confianza Global: {datos.confianza_global_extraccion}")
    
print(f"\n🧭 Ruteo Final: {res_limpio.decision_ruteo.value}")
print(f"📝 Motivo: {res_limpio.motivo_ruteo}")


# %% [5] Caso 2: Procesar formulario Manuscrito en MODO LIVE
from henry_m4.config import get_settings
from henry_m4.vision_engine import PipelineVisionAutoreparable

settings = get_settings()
print("=" * 80)
print(f"🚀 INICIANDO MODO LIVE | Proveedor: Google API | Modelo: {settings.gemini_model}")
print("👁️ Analizando píxeles reales de 'form_02_manuscrito.jpg'...")

pipeline_live = PipelineVisionAutoreparable(max_intentos=3, forzar_live=True)
res_manuscrito = pipeline_live.procesar_formulario("assets/formularios/form_02_manuscrito.jpg")

if res_manuscrito.datos_validados:
    datos = res_manuscrito.datos_validados
    print("\n✅ DATOS EXTRAÍDOS POR GEMINI:")
    print(f"👤 Titular: {datos.nombre_solicitante}")
    print(f"💰 Ingreso Mensual: {datos.ingreso_mensual_declarado}")
    print(f"💵 Monto Solicitado: {datos.monto_credito_solicitado}")
    print(f"🔄 Intentos del bucle: {res_manuscrito.intentos_utilizados}")
    
print(f"\n🧭 Ruteo Final: {res_manuscrito.decision_ruteo.value}")
print(f"📝 Motivo: {res_manuscrito.motivo_ruteo}")


# %% [6] Caso 3: Procesar formulario Borroso (Abstención) en MODO LIVE
from henry_m4.config import get_settings
from henry_m4.vision_engine import PipelineVisionAutoreparable

settings = get_settings()
print("=" * 80)
print(f"🚀 INICIANDO MODO LIVE | Proveedor: Google API | Modelo: {settings.gemini_model}")
print("👁️ Analizando píxeles reales de 'form_03_borroso.jpg'...")

pipeline_live = PipelineVisionAutoreparable(max_intentos=3, forzar_live=True)
res_borroso = pipeline_live.procesar_formulario("assets/formularios/form_03_borroso.jpg")

if res_borroso.datos_validados:
    datos = res_borroso.datos_validados
    print("\n✅ DATOS EXTRAÍDOS POR GEMINI (Nota la Abstención Visual):")
    print(f"👤 Titular: {datos.nombre_solicitante}")
    print(f"💰 Ingreso Mensual: {datos.ingreso_mensual_declarado}  <-- ¡Se abstuvo (None)!")
    print(f"✍️ Firma Detectada: {datos.posee_firma_autografa}")
    print(f"📊 Confianza Global: {datos.confianza_global_extraccion}")
    
    evidencia_ingreso = next((e for e in datos.evidencias_visuales if e.campo == "ingreso_mensual_declarado"), None)
    if evidencia_ingreso:
        print("\n🔍 QUÉ VIO GEMINI EN ESE CAMPO (Chain-of-Thought Visual):")
        print(f"   - Transcripción literal: {evidencia_ingreso.transcripcion_literal}")
        print(f"   - Anomalía detectada : {evidencia_ingreso.observacion_anomalia}")

print(f"\n🧭 Ruteo Final: {res_borroso.decision_ruteo.value}")
print(f"📝 Motivo: {res_borroso.motivo_ruteo}")
# %%
