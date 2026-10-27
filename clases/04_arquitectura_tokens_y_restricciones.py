# 🟢 Clase 4: Fundamentos Teóricos y Arquitectura — Ingeniería Bajo Restricciones
# %% [markdown]
# # 🧠 Clase 4: Arquitectura Transformer, Tokenización y Adaptación Bajo Restricciones
# **Escenario de Negocio:**
# 1. Tiempo de respuesta **< 600 ms**
# 2. El dominio cambia cada mes (**nuevos términos mensuales**)
# 3. **Costo de entrenamiento muy bajo**

# %% "¿Dónde Mira el Modelo?" (Simulador de Self-Attention)
# 🟢 Visualización de cómo las cabezas de atención conectan palabras para desambiguar el contexto
import os
import sys
from pathlib import Path

# 1. Enrutar el kernel a la raíz del proyecto para que detecte el módulo local
if Path.cwd().name == "clases":
    os.chdir(Path.cwd().parent)
ruta_src = str(Path.cwd() / "src")
if ruta_src not in sys.path:
    sys.path.insert(0, ruta_src)

import importlib
import json
import henry_m4.schemas
import henry_m4.architecture_engine

importlib.reload(henry_m4.schemas)
importlib.reload(henry_m4.architecture_engine)

from henry_m4.architecture_engine import (
    SimuladorAtencionTransformer,
    LaboratorioTokenizacion,
    CalculadoraAdaptacionLoRA,
    BenchmarkLatenciaSLA,
)
from henry_m4.schemas import PropuestaArquitecturaSLA
from pydantic import ValidationError

print("🔍 LABORATORIO 1: ¿DÓNDE MIRA EL MODELO? (Mecanismo de Self-Attention - Slide 4)")
print("=" * 85)
for dominio in ["deportes", "finanzas", "medicina"]:
    print(SimuladorAtencionTransformer.renderizar_mapa_atencion(dominio))


# %% Tokenización BPE vs WordPiece ante Jerga Mensual
# 🟢 Demostración real con tiktoken de por qué BPE sobrevive a palabras nuevas sin caer en [UNK]
frase_mes_actual = "Hola, quiero activar el PlanMegaFibra2026 con cripto-reembolso en mi cuenta"
resultado_tok = LaboratorioTokenizacion.comparar_enfoques(frase_con_jerga_mensual=frase_mes_actual)

print("🧩 LABORATORIO 2: BPE (Byte-Level) vs WORDPIECE ESTÁTICO (Slide 10 - Pregunta <1>)")
print("=" * 85)
print(f"🗣️ Frase del cliente con términos nuevos del mes:\n   \"{resultado_tok['frase_original']}\"\n")
print(f"✅ Enfoque A — Byte-Level BPE ({resultado_tok['bpe_cantidad_tokens']} sub-tokens, 0 pérdidas):")
print(f"   {resultado_tok['bpe_subtokens']}\n")
print(f"❌ Enfoque B — WordPiece Estático ({resultado_tok['wordpiece_unk_perdidos']} palabras destruidas como [UNK]):")
print(f"   {resultado_tok['wordpiece_tokens']}")
print("   🚨 Peligro: El modelo queda ciego ante 'PlanMegaFibra2026' y 'cripto-reembolso' porque ambos se vuelven [UNK].")


# %% Adaptación Mensual de Bajo Costo (Full Fine-Tuning vs PEFT/LoRA)
# 🟢 Comparativa matemática de VRAM y presupuesto para actualizar el chatbot cada mes
comparativa_lora = CalculadoraAdaptacionLoRA.comparar_metodos(parametros_totales_billones=8.0, rango_lora_r=16)

print("💰 LABORATORIO 3: FULL FINE-TUNING vs PEFT / LoRA (Slide 10 - Pregunta <2>)")
print("=" * 85)
print(json.dumps(comparativa_lora, indent=2, ensure_ascii=False))


# %% "El Tribunal de Arquitectura (< 600 ms)"
# 🟢 Validador Pydantic en vivo: Pon a prueba las decisiones de los grupos frente al SLA de 600 ms
print("⚖️ TRIBUNAL DE ARQUITECTURA: Validando propuestas de equipos con Pydantic")
print("=" * 85)

# Propuesta 1: Un equipo propone un modelo gigante o Full Fine-Tuning (Falla las restricciones)
try:
    PropuestaArquitecturaSLA(
        nombre_equipo="Equipo 1 (Diseño Tradicional Pesado)",
        enfoque_tokenizacion="BPE_BYTE_LEVEL",
        metodo_adaptacion="FULL_FINE_TUNING", # <-- Rompe el bajo costo
        tamano_modelo_billones=70.0, # <-- Rompe los 600ms
        usa_cuantizacion_int4=False,
        usa_cache_semantico=False,
    )
except ValidationError as err:
    print("❌ Propuesta Equipo 1 RECHAZADA por el Firewall de Arquitectura:")
    print(f"   Motivo: {err.errors()[0]['msg']}\n")

# Propuesta 2: La Arquitectura Ganadora bajo restricciones
propuesta_ganadora = PropuestaArquitecturaSLA(
    nombre_equipo="Equipo 2 (Arquitectura Ágil Bajo Restricciones)",
    enfoque_tokenizacion="BPE_BYTE_LEVEL",
    metodo_adaptacion="PEFT_LORA_MAS_RAG",
    tamano_modelo_billones=8.0,
    usa_cuantizacion_int4=True,
    usa_cache_semantico=True,
)
print("✅ Propuesta Equipo 2 APROBADA PARA PRODUCCIÓN:")
print(f"   ⏱️ Latencia Estimada : {propuesta_ganadora.latencia_estimada_ms} ms (SLA < 600 ms cumplido)")
print(f"   💵 Costo Mensual LoRA: ${propuesta_ganadora.costo_adaptacion_mensual_usd} USD/mes")
print(f"   🔤 Tasa de [UNK]     : {propuesta_ganadora.tasa_tokens_desconocidos_unk}%")


# %% DEMO HÍBRIDA (LIVE / OFFLINE): Carrera contra el Reloj de los 600 ms (Slide 10 - Pregunta <3>)
# 🟢 Prueba real de velocidad comparando Caché Semántico vs Inferencia en Vivo/Simulada
import os
from pathlib import Path
from dotenv import load_dotenv

if Path.cwd().name == "clases":
    os.chdir(Path.cwd().parent)
load_dotenv(override=True)

benchmark = BenchmarkLatenciaSLA(forzar_live=True)

print("🏎️ CARRERA CONTRA LOS 600 MILISEGUNDOS (Caché Semántico + SLM):")
print("=" * 85)

# Caso A: Pregunta frecuente atrapada por el Caché Semántico
res_cache = benchmark.consultar_con_presupuesto_600ms("¿Cómo reinicio mi clave?")
print(f"1️⃣ Consulta Repetida -> {res_cache['ruta']}")
print(f"   ⏱️ Tiempo: {res_cache['latencia_ms']} ms | ¿Cumple <600ms?: {res_cache['cumple_sla_600ms']}")
print(f"   💬 Respuesta: {res_cache['respuesta']}\n")

# Caso B: Pregunta nueva con jerga mensual que va al modelo ligero
res_modelo = benchmark.consultar_con_presupuesto_600ms("Quiero activar el PlanMegaFibra2026 ahora")
print(f"2️⃣ Consulta Nueva    -> {res_modelo['ruta']}")
print(f"   ⏱️ Tiempo: {res_modelo['latencia_ms']} ms | ¿Cumple <600ms?: {res_modelo['cumple_sla_600ms']}")
print(f"   💬 Respuesta: {res_modelo['respuesta']}")
# %%
