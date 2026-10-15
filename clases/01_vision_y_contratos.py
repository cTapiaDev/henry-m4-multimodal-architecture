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
