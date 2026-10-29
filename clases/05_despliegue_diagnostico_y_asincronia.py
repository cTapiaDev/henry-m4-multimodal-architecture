# 🟢 Clase 5: Adaptación Avanzada, Arquitecturas de Serving, cProfile y Concurrencia con asyncio
# %% [markdown]
# # 🚀 Clase 5: Adaptación Avanzada y Arquitecturas de Serving (M4L5)
# **Caso de Estudio:** Startup de resumen de documentos con tráfico impredecible:
# de **3 solicitudes por hora** a picos virales de **300 solicitudes por minuto**.

# %% [1] "¿Escala o Falla?" (Serverless vs Server-Based ante Tráfico Viral)
# 🟢 Simulación de costos y caídas cuando el tráfico salta de 3 req/hora a 300 req/minuto
import os
import sys
from pathlib import Path

if Path.cwd().name == "clases":
    os.chdir(Path.cwd().parent)
src_path = str(Path.cwd() / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import importlib
import henry_m4.schemas
import henry_m4.serving_engine

importlib.reload(henry_m4.schemas)
importlib.reload(henry_m4.serving_engine)

from henry_m4.serving_engine import (
    TrafficServingSimulator,
    CpuProfilingLab,
    AsyncioConcurrencyLab,
)
from henry_m4.schemas import StartupServingProposal
from pydantic import ValidationError

print("📊 LABORATORIO 1: ¿ESCALA O FALLA? — SERVERLESS vs SERVER-BASED")
print("=" * 90)
for item in TrafficServingSimulator.evaluate_traffic_scenarios():
    print(f"🌪️ Escenario: {item['scenario']}")
    print(f"   🏢 Server-Based Fijo (24/7)        : {item['server_based_fixed']}")
    print(f"   ❄️ Serverless Puro (Scale-to-Zero) : {item['serverless_pure']}")
    print(f"   🔥 Serverless + Instancia Tibia    : {item['serverless_warm_hybrid']}\n")


# %% [2] Diagnóstico de Cuellos de Botella CPU-Bound con cProfile
# 🟢 Uso de cProfile para cazar la función exacta que frena el pre-procesamiento de documentos
sample_document = (
    "Informe Financiero Trimestral: La startup registró un aumento de 10x en solicitudes de resumen "
    "durante el lanzamiento del lunes por la mañana.   Se requiere optimizar el pipeline de texto. " * 15
)

audit_result = CpuProfilingLab.run_cprofile_audit(sample_document)

print("🔍 LABORATORIO 2: DIAGNÓSTICO DE CPU CON cProfile")
print("=" * 90)
print(f"🐢 Tiempo Pipeline Lento (CPU-bound) : {audit_result['slow_time_ms']} ms")
print(f"⚡ Tiempo Pipeline Optimizado        : {audit_result['optimized_time_ms']} ms\n")
print("📋 REPORTE OFICIAL DE cProfile (Ordenado por 'tottime' - Tiempo interno puro en CPU):")
print("-" * 90)
print(audit_result["cprofile_report"])
print("💡 Conclusión: cProfile revela sin adivinar que '_clean_document_slow_cpu_bottleneck' consumió casi el 100% del CPU.")


# %% [3] Concurrencia Asíncrona con asyncio para Cuellos I/O-Bound
# 🟢 Comparación en vivo: Procesar una ráfaga de 12 resúmenes de forma Secuencial vs asyncio.gather()
concurrency_report = await AsyncioConcurrencyLab.compare_sync_vs_async_batch(num_requests=12)

print("⚡ LABORATORIO 3: SECUENCIAL SÍNCRONO vs CONCURRENCIA ASÍNCRONA")
print("=" * 90)
print(f"📦 Lote recibido en el pico de tráfico : {concurrency_report['num_requests']} documentos simultáneos")
print(f"🐢 Ejecución Síncrona Secuencial       : {concurrency_report['sync_total_ms']} ms (Bloquea el hilo esperando cada red)")
print(f"🚀 Ejecución Asíncrona (asyncio.gather): {concurrency_report['async_total_ms']} ms (Espera todas las llamadas en paralelo)")
print(f"📈 Aceleración obtenida (Speedup)      : {concurrency_report['speedup_factor']}x más rápido con el mismo hardware")


# %% [4] Auditor Pydantic para el Plan de 3 Puntos
# 🟢 Validación en vivo de las decisiones de los equipos (Adaptación + Serving + Optimización)
print("⚖️ LABORATORIO 4: AUDITORÍA DE ARQUITECTURA PARA LA STARTUP")
print("=" * 90)

# Caso 1: Un equipo confunde CPU-bound con asyncio o elige Server-based 24/7
try:
    StartupServingProposal(
        team_name="Equipo A (Diseño con Errores Conceptuales)",
        adaptation_method="LORA_PEFT",
        serving_pattern="SERVERLESS_AUTOSCALE_WARM",
        bottleneck_type="CPU_BOUND",
        optimization_tool="ASYNCIO",  # <-- Error: asyncio no arregla cuellos de CPU
    )
except ValidationError as err:
    print("❌ Propuesta Equipo A RECHAZADA por Pydantic:")
    print(f"   Motivo: {err.errors()[0]['msg']}\n")

# Caso 2: El Plan Ganador de los 3 Puntos de la Slide 10
winning_plan = StartupServingProposal(
    team_name="Equipo B (Arquitectura Elástica de Alto Rendimiento)",
    adaptation_method="LORA_PEFT",
    serving_pattern="SERVERLESS_AUTOSCALE_WARM",
    bottleneck_type="IO_BOUND",
    optimization_tool="ASYNCIO",
)
print("✅ Propuesta Equipo B APROBADA PARA EL PICO DE 300 REQ/MIN:")
print(f"   🧬 Punto <1> Adaptación : {winning_plan.adaptation_method} (Adaptador ligero de rápida carga en VRAM)")
print(f"   ☁️ Punto <2> Serving    : {winning_plan.serving_pattern} (${winning_plan.estimated_monthly_cost_usd} USD/mes)")
print(f"   ⚡ Punto <3> Performance: Cuello {winning_plan.bottleneck_type} resuelto con {winning_plan.optimization_tool}")


# %% [5] DEMO HÍBRIDA (LIVE / OFFLINE): Ráfaga Asíncrona Real de Resúmenes con asyncio.gather
# 🟢 Disparo simultáneo de 3 documentos hacia el LLM sin bloquear el Event Loop
import asyncio
from dotenv import load_dotenv

load_dotenv(override=True)
async_engine = AsyncioConcurrencyLab(force_live=True)

incoming_docs = [
    ("Noticia Celebridad Viral", "El artículo sobre la gira mundial rompió récords con 10x más lecturas en 30 minutos."),
    ("Reporte Lunes 09:00 AM", "Todos los equipos corporativos ingresaron simultáneamente para resumir minutas semanales."),
    ("Demo Cliente Enterprise", "La demostración en vivo se compartió en redes y atrajo a miles de usuarios concurrentes."),
]

t_start = time.perf_counter()
batch_results = await asyncio.gather(
    *[async_engine.summarize_document_hybrid_async(title, text) for title, text in incoming_docs]
)
total_wall_ms = round((time.perf_counter() - t_start) * 1000, 1)

print("🌐 LABORATORIO 5: RÁFAGA ASÍNCRONA EN VIVO (3 Documentos en Paralelo con asyncio.gather)")
print("=" * 90)
for res in batch_results:
    print(f"📄 {res['documento']} [{res['modo']}] ({res['latencia_ms']} ms):")
    print(f"   💬 {res['resumen']}")
print("-" * 90)
print(f"⏱️ Tiempo total de reloj (Wall Time) para los 3 documentos en paralelo: {total_wall_ms} ms")