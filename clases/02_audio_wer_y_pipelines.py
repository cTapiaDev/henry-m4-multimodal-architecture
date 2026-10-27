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

# %% [markdown]
# ---
# ### 🎙️ DEMO INTERACTIVA EN VIVO: Habla con el Agente de Voz (Micrófono -> Groq -> Gemini/Groq -> edge-tts)
# Ejecuta esta celda, habla al micrófono el tiempo que necesites y presiona ENTER para que la IA te responda.
# ---

# %% [5] Grabación de Voz Libre y Respuesta Sintetizada
import os
import importlib
from pathlib import Path
from dotenv import load_dotenv

import henry_m4.audio_engine
importlib.reload(henry_m4.audio_engine)

from henry_m4.config import get_settings
from henry_m4.audio_engine import PipelineAudioSoporte, GrabadorYAsistenteVozLive


if Path.cwd().name == "clases":
    os.chdir(Path.cwd().parent)
load_dotenv(override=True)

settings = get_settings()
asistente = GrabadorYAsistenteVozLive()
pipeline = PipelineAudioSoporte(max_intentos=3, forzar_live=True)

print("=" * 80)
print("🎙️ ASISTENTE DE VOZ BANCARIO EN VIVO")
print("1. Habla al micrófono sin límite de tiempo.")
print("2. Cuando termines, presiona ENTER en el cuadro de arriba para detener.")
print("=" * 80)

ruta_wav = asistente.grabar_microfono_libre()

print("\n🔄 Procesando audio con Groq Whisper y validando con Gemini...")
resultado_voz = pipeline.procesar_llamada(ruta_wav)

print(f"\n📝 Lo que entendió Groq Whisper de tu voz:")
print(f"   > {resultado_voz['transcripcion_obtenida']}")

if resultado_voz['datos']:
    datos_agente = resultado_voz['datos']
    texto_respuesta = datos_agente.resumen_para_tts
    
    print(f"\n✅ Respuesta estructurada:")
    print(f"   🏷️ Motivo: {datos_agente.motivo_principal_llamada}")
    print(f"   🗣️ Texto para hablarte: '{texto_respuesta}'")
    
    print("\n🔊 Sintetizando voz neuronal de respuesta...")
    ruta_respuesta_mp3 = await asistente.sintetizar_voz_neuronal(texto_respuesta)
    
    print("▶️ Reproduciendo respuesta del agente...")
    if os.name == 'nt':
        os.system(f'start {ruta_respuesta_mp3}')
    else:
        os.system(f'afplay {ruta_respuesta_mp3}')
else:
    print("❌ El pipeline no pudo validar la respuesta de audio.")
# %%
