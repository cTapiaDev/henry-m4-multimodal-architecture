# %% [markdown]
# # M4L2 · IA que Escucha y Habla: Audio, WER y Pipelines End-to-End
# 
# En esta clase analizamos los desafíos de transcribir audio a texto (STT) y 
# generar respuestas (TTS).
# 
# ### Ejercicio del Taller: Diagnosticar el Pipeline
# Transcripción STT rota: *"El cliente dijo que tenía probrema para a ceder a los detayes de su cuenta..."*

# %% [1] DIAGNÓSTICO 1: Tipos de Error y WER (Word Error Rate)
from henry_m4.audio_engine import STTOfflineSimulator

audio_stt = STTOfflineSimulator.transcribir_audio("audio_soporte_01")

print("🎙️ Frase Original (Lo que el cliente realmente dijo):")
print(f"   {audio_stt['texto_limpio_ideal']}\n")

print("🎧 Transcripción Cruda (Lo que entendió Whisper sin contexto):")
print(f"   {audio_stt['transcripcion_cruda']}\n")

print("📉 Auditoría de Errores (Cálculo para WER):")
errores_wer = STTOfflineSimulator.auditar_wer(audio_stt['transcripcion_cruda'])
for error in errores_wer:
    print(f"   ❌ {error}")


# %% [2] DIAGNÓSTICO 2: ¿Por qué la transcripción mala rompe al LLM? (Tokenización)
from henry_m4.audio_engine import diagnosticar_tokenizacion

texto_ideal = "acceder a los detalles"
texto_roto = "a ceder a los detayes"

tokens_ideales = diagnosticar_tokenizacion(texto_ideal)
tokens_rotos = diagnosticar_tokenizacion(texto_roto)

print("🧠 Cómo lee un LLM la frase correcta (Vocabulario fuerte y conectado):")
print(f"   {texto_ideal}  ->  {tokens_ideales} (Total: {len(tokens_ideales)} tokens)\n")

print("💥 Cómo lee un LLM la frase rota por el STT (Fragmentación y pérdida semántica):")
print(f"   {texto_roto}  ->  {tokens_rotos} (Total: {len(tokens_rotos)} tokens)\n")
print("⚠️ Conclusión: Al romperse 'acceder' en 'a' + 'ceder', el LLM pierde el contexto de que se trata de un login informático.")


# %% [3] LA SOLUCIÓN: Pipeline Autorreparable con Pydantic
from henry_m4.audio_engine import PipelineAudioSoporte

pipeline = PipelineAudioSoporte(max_intentos=3)
resultado = pipeline.procesar_llamada(audio_stt['transcripcion_cruda'])

print("🛡️ BUCLE DE AUTORREPARACIÓN (STT -> LLM):")
print(f"Intentos necesarios: {resultado['intentos']}\n")

print("🚨 Intercepciones de Pydantic (@model_validator):")
for err in resultado['errores_atrapados']:
    print(f"   {err}\n")

print("✅ RESUMEN FINAL CORREGIDO (Listo para enviar al Text-to-Speech):")
print(resultado['datos'].model_dump_json(indent=2))
# %%

# %% [markdown]
# ---
# ### 🔴 MODO LIVE: Pipeline Híbrido (Whisper STT + Gemini LLM)
# Escuchamos un archivo .mp3 real usando la API de Groq Whisper y lo validamos con Gemini.
# ---

# %% [4] Flujo End-to-End con Audio Real
import os
from pathlib import Path
from dotenv import load_dotenv
from henry_m4.config import get_settings
from henry_m4.audio_engine import PipelineAudioSoporte

# Truco para VS Code
if Path.cwd().name == "clases":
    os.chdir(Path.cwd().parent)
load_dotenv(override=True)

settings = get_settings()
ruta_mp3 = "assets/audios/llamada_01.mp3"

print("=" * 80)
print("🚀 INICIANDO MODO LIVE HÍBRIDO")
print("👂 Oído (STT): Groq API (whisper-large-v3)")
print(f"🧠 Cerebro (LLM): Google API ({settings.gemini_model})")
print("=" * 80)

if not Path(ruta_mp3).exists():
    print(f"⚠️ Archivo no encontrado. Ejecuta primero: uv run python scripts/generar_audio_prueba.py")
else:
    pipeline_live = PipelineAudioSoporte(max_intentos=3, forzar_live=True)
    
    print(f"🎙️ Escuchando y transcribiendo '{ruta_mp3}' en tiempo real...")
    resultado = pipeline_live.procesar_llamada(ruta_mp3)
    
    print("\n📝 Transcripción cruda devuelta por Whisper:")
    print(f"   > {resultado['transcripcion_obtenida']}")
    
    print(f"\n🔄 Intentos de validación Pydantic: {resultado['intentos']}")
    if resultado['errores_atrapados']:
        print("🚨 Errores interceptados y autorreparados:")
        for err in resultado['errores_atrapados']:
            print(f"   ❌ {err}")
            
    if resultado['datos']:
        datos = resultado['datos']
        print("\n✅ DATOS ESTRUCTURADOS (Listos para base de datos y TTS):")
        print(f"   🏷️ Motivo Central: {datos.motivo_principal_llamada}")
        print(f"   📦 Entidades: {datos.entidades_afectadas}")
        print(f"   ⚠️ Escalar a humano: {datos.requiere_escalamiento}")
        print(f"   🗣️ Texto para TTS: {datos.resumen_para_tts}")
# %%
