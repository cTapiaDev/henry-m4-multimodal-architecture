# Motor de Clase 5: Simulador de Serving, Diagnóstico CPU con cProfile y Concurrencia I/O con asyncio
import asyncio
import cProfile
import io
import pstats
import re
import time

from .config import get_settings


class TrafficServingSimulator:
    """Simula el comportamiento de arquitecturas Serverless vs Server-based"""

    @staticmethod
    def evaluate_traffic_scenarios() -> list[dict]:
        return [
            {
                "scenario": "Valle Nocturno (3 solicitudes / hora)",
                "server_based_fixed": "Costo alto ($5.30/h quemados con GPU al 1% de uso) | Latencia: 180 ms",
                "serverless_pure": "Costo $0.02/h (Escala a 0) | Latencia 1ra petición: 18,500 ms (Cold Start)",
                "serverless_warm_hybrid": "Costo bajo ($0.42/h con 1 instancia tibia) | Latencia: 190 ms (Sin Cold Start)",
            },
            {
                "scenario": "Pico Viral / Celebridad 10x (300 solicitudes / minuto)",
                "server_based_fixed": "COLAPSO (HTTP 503): La GPU única satura la cola a las 45 solicitudes/min",
                "serverless_pure": "DEGRADACIÓN: Las primeras 80 solicitudes sufren Timeouts de 20s mientras levantan GPUs",
                "serverless_warm_hybrid": "ESCALADO EXITOSO: Instancia tibia + Burst Serverless absorben las 300 req/min",
            },
        ]


class CpuProfilingLab:
    """Demuestra cómo cProfile detecta un cuello de botella CPU-bound en el pre-procesamiento de documentos."""

    @staticmethod
    def _validate_metadata_fast(raw_text: str) -> bool:
        return len(raw_text) > 10

    @staticmethod
    def _clean_document_slow_cpu_bottleneck(raw_text: str) -> str:
        # Cuello de botella intencional CPU-bound: compilación repetitiva y bucle ineficiente en Python puro
        cleaned = raw_text
        for _ in range(4500):
            cleaned = re.sub(r"\s+", " ", cleaned)
            cleaned = "".join([char for char in cleaned if char.isprintable()])
        return cleaned.strip()

    @staticmethod
    def _clean_document_optimized(raw_text: str) -> str:
        # Versión optimizada vectorizada / directa en C
        return " ".join(raw_text.split())

    @classmethod
    def run_slow_pipeline(cls, sample_doc: str) -> str:
        cls._validate_metadata_fast(sample_doc)
        return cls._clean_document_slow_cpu_bottleneck(sample_doc)

    @classmethod
    def run_cprofile_audit(cls, sample_doc: str) -> dict:
        profiler = cProfile.Profile()
        start_slow = time.perf_counter()
        profiler.enable()
        cls.run_slow_pipeline(sample_doc)
        profiler.disable()
        slow_ms = round((time.perf_counter() - start_slow) * 1000, 2)

        stream = io.StringIO()
        stats = pstats.Stats(profiler, stream=stream).sort_stats("tottime")
        stats.print_stats(6)

        start_fast = time.perf_counter()
        cls._clean_document_optimized(sample_doc)
        fast_ms = round((time.perf_counter() - start_fast) * 1000, 4)

        return {
            "slow_time_ms": slow_ms,
            "optimized_time_ms": fast_ms,
            "cprofile_report": stream.getvalue(),
        }


class AsyncioConcurrencyLab:
    """Compara procesamiento Secuencial Bloqueante vs Concurrencia Asíncrona (asyncio) en tareas I/O-bound."""

    def __init__(self, force_live: bool = False):
        self.settings = get_settings()
        self.use_live = force_live or self.settings.is_live

    @staticmethod
    def _simulate_sync_io_call(doc_id: int, network_delay_sec: float = 0.18) -> str:
        time.sleep(network_delay_sec)
        return f"Doc #{doc_id:02d} resumido (Síncrono)"

    @staticmethod
    async def _simulate_async_io_call(doc_id: int, network_delay_sec: float = 0.18) -> str:
        await asyncio.sleep(network_delay_sec)
        return f"Doc #{doc_id:02d} resumido (Asíncrono)"

    @classmethod
    async def compare_sync_vs_async_batch(cls, num_requests: int = 12) -> dict:
        # 1. Ejecución Síncrona Secuencial (Bloqueante)
        t0_sync = time.perf_counter()
        sync_results = [cls._simulate_sync_io_call(i) for i in range(1, num_requests + 1)]
        sync_total_ms = round((time.perf_counter() - t0_sync) * 1000, 1)

        # 2. Ejecución Concurrente con asyncio.gather (No bloqueante)
        t0_async = time.perf_counter()
        tasks = [cls._simulate_async_io_call(i) for i in range(1, num_requests + 1)]
        async_results = await asyncio.gather(*tasks)
        async_total_ms = round((time.perf_counter() - t0_async) * 1000, 1)

        return {
            "num_requests": num_requests,
            "sync_total_ms": sync_total_ms,
            "async_total_ms": async_total_ms,
            "speedup_factor": round(sync_total_ms / max(async_total_ms, 1.0), 1),
            "sample_output": async_results[:3],
        }

    async def summarize_document_hybrid_async(self, doc_title: str, doc_content: str) -> dict:
        start_time = time.perf_counter()

        if self.use_live and self.settings.groq_api_key:
            try:
                from groq import AsyncGroq

                client = AsyncGroq(api_key=self.settings.groq_api_key)
                response = await client.chat.completions.create(
                    model="allam-2-7b",
                    messages=[
                        {
                            "role": "system",
                            "content": "Eres un motor de resúmenes ejecutivos en español. Resume en máximo 15 palabras.",
                        },
                        {"role": "user", "content": f"Documento ({doc_title}): {doc_content}"},
                    ],
                    max_tokens=40,
                    temperature=0.0,
                )
                elapsed_ms = round((time.perf_counter() - start_time) * 1000, 1)
                return {
                    "documento": doc_title,
                    "modo": "LIVE (AsyncGroq Concurrency)",
                    "latencia_ms": elapsed_ms,
                    "resumen": response.choices[0].message.content.strip(),
                }
            except Exception as exc:
                print(f"⚠️ {doc_title}: API Live ocupada ({exc}). Activando respaldo asíncrono Offline...")

        # Respaldo Offline Asíncrono determinista
        await asyncio.sleep(0.22)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 1)
        return {
            "documento": doc_title,
            "modo": "OFFLINE_SIM (Async Event Loop)",
            "latencia_ms": elapsed_ms,
            "resumen": f"Resumen ejecutivo validado para '{doc_title}': puntos clave extraídos sin bloqueo de I/O.",
        }