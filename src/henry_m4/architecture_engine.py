import time
import tiktoken

from .config import get_settings


class SimuladorAtencionTransformer:

    ESCENARIOS_SLIDE_4 = {
        "deportes": {
            "oracion": "A pesar de su lesión, el delantero marcó el gol de la victoria.",
            "token_foco": "su",
            "pesos_atencion": {
                "delantero": 0.58,
                "lesión": 0.24,
                "marcó": 0.11,
                "gol": 0.05,
                "A pesar": 0.02,
            },
            "explicacion": "La cabeza de atención resuelve la correferencia: conecta 'su' con 'delantero' aunque estén separados.",
        },
        "finanzas": {
            "oracion": "El banco no prestará dinero a clientes con puntajes de crédito bajos.",
            "token_foco": "banco",
            "pesos_atencion": {
                "dinero": 0.42,
                "crédito": 0.35,
                "prestará": 0.16,
                "clientes": 0.05,
                "bajos": 0.02,
            },
            "explicacion": "Desambiguación semántica: 'dinero' y 'crédito' empujan el vector de 'banco' lejos de un asiento de plaza.",
        },
        "medicina": {
            "oracion": "La hipertensión es común en adultos mayores con diabetes.",
            "token_foco": "hipertensión",
            "pesos_atencion": {
                "diabetes": 0.46,
                "adultos": 0.29,
                "mayores": 0.18,
                "común": 0.07,
            },
            "explicacion": "Asociación clínica: conecta patologías comórbidas ('hipertensión' <-> 'diabetes') y el grupo etario.",
        },
    }

    @classmethod
    def renderizar_mapa_atencion(cls, clave: str) -> str:
        datos = cls.ESCENARIOS_SLIDE_4[clave]
        lineas = [
            f"📝 Oración : \"{datos['oracion']}\"",
            f"🎯 Token donde mira el modelo: ['{datos['token_foco']}']",
            "📊 Distribución de pesos de Self-Attention (Softmax):",
        ]
        for token_destino, peso in datos["pesos_atencion"].items():
            barras = "█" * int(peso * 30)
            lineas.append(f"   ├── {token_destino:<12} : {peso:>5.0%} | {barras}")
        lineas.append(f"💡 Insight : {datos['explicacion']}\n")
        return "\n".join(lineas)


class LaboratorioTokenizacion:
    """Compara BPE (Byte-Pair Encoding real con tiktoken) vs WordPiece estático ante jerga mensual."""

    VOCABULARIO_ESTATICO_WORDPIECE = {
        "hola", "quiero", "activar", "el", "plan", "con", "descuento", "en", "mi", "cuenta", "soporte", "error"
    }

    @classmethod
    def comparar_enfoques(cls, frase_con_jerga_mensual: str) -> dict:
        codificador_bpe = tiktoken.encoding_for_model("gpt-4o")
        ids_bpe = codificador_bpe.encode(frase_con_jerga_mensual)
        subtokens_bpe = [codificador_bpe.decode([i]).strip() for i in ids_bpe]

        # Simulación de WordPiece con vocabulario cerrado sin reentrenar este mes
        palabras = frase_con_jerga_mensual.replace(",", "").replace(".", "").split()
        tokens_wordpiece = []
        unk_detectados = 0
        for p in palabras:
            limpia = p.lower()
            if limpia in cls.VOCABULARIO_ESTATICO_WORDPIECE:
                tokens_wordpiece.append(p)
            elif limpia.startswith("plan") and len(limpia) > 4:
                tokens_wordpiece.extend(["plan", "##[UNK]"])
                unk_detectados += 1
            else:
                tokens_wordpiece.append("[UNK]")
                unk_detectados += 1

        return {
            "frase_original": frase_con_jerga_mensual,
            "bpe_cantidad_tokens": len(ids_bpe),
            "bpe_subtokens": subtokens_bpe,
            "wordpiece_tokens": tokens_wordpiece,
            "wordpiece_unk_perdidos": unk_detectados,
        }


class CalculadoraAdaptacionLoRA:
    """Compara Full Fine-Tuning vs PEFT/LoRA en parámetros entrenables, VRAM y costo mensual."""

    @staticmethod
    def comparar_metodos(parametros_totales_billones: float = 8.0, rango_lora_r: int = 16) -> dict:
        total_params = int(parametros_totales_billones * 1_000_000_000)
        factor_lora = (rango_lora_r / 16.0) * 0.0018
        params_lora = int(total_params * factor_lora)

        return {
            "modelo_base": f"Llama/Mistral {parametros_totales_billones}B",
            "full_fine_tuning": {
                "parametros_entrenables": f"{total_params:,} (100%)",
                "vram_minima_gb": round(parametros_totales_billones * 16.0, 1),
                "costo_mensual_estimado_usd": round(parametros_totales_billones * 320.0, 2),
                "riesgo": "Olvido catastrófico y alto costo por cada cambio de mes.",
            },
            "peft_lora": {
                "rango_r": rango_lora_r,
                "parametros_entrenables": f"{params_lora:,} ({factor_lora * 100:.2f}%)",
                "vram_minima_gb": round(parametros_totales_billones * 1.2, 1),
                "costo_mensual_estimado_usd": round(parametros_totales_billones * 4.5, 2),
                "ventaja": "Se entrena un adaptador ligero por mes en 1 GPU barata sin tocar el modelo base.",
            },
        }


class BenchmarkLatenciaSLA:
    """Mide si cumplimos el SLA < 600ms con Caché Semántico + Inferencia Rápida (Live/Offline)."""

    def __init__(self, forzar_live: bool = False):
        self.settings = get_settings()
        self.usar_live = forzar_live or self.settings.is_live
        self._cache_semantico = {
            "como reinicio mi clave": "Ve a Configuración > Seguridad > Cambiar clave. Recibirás un código SMS."
        }

    def consultar_con_presupuesto_600ms(self, consulta_cliente: str) -> dict:
        inicio = time.perf_counter()
        clave_normalizada = consulta_cliente.lower().strip("¿?.! ")

        # Nivel 1: Caché Semántico (Ultra rápido < 25ms)
        if clave_normalizada in self._cache_semantico:
            time.sleep(0.012)
            latencia_ms = round((time.perf_counter() - inicio) * 1000, 1)
            return {
                "ruta": "NIVEL 1: Caché Semántico (Hit en Memoria)",
                "latencia_ms": latencia_ms,
                "cumple_sla_600ms": latencia_ms < 600.0,
                "respuesta": self._cache_semantico[clave_normalizada],
            }

        # Nivel 2: Inferencia en Vivo con SLM rápido (Groq Plan A por velocidad <600ms -> Gemini Plan B -> Offline Plan C)
        if self.usar_live and self.settings.groq_api_key:
            try:
                from groq import Groq

                g_client = Groq(api_key=self.settings.groq_api_key)
                resp = g_client.chat.completions.create(
                    model="allam-2-7b",
                    messages=[
                        {"role": "system", "content": "Responde en máximo 18 palabras como soporte técnico."},
                        {"role": "user", "content": consulta_cliente},
                    ],
                    max_tokens=45,
                    temperature=0.0,
                )
                latencia_ms = round((time.perf_counter() - inicio) * 1000, 1)
                return {
                    "ruta": "NIVEL 2 (LIVE): SLM en Groq LPU (allam-2-7b)",
                    "latencia_ms": latencia_ms,
                    "cumple_sla_600ms": latencia_ms < 600.0,
                    "respuesta": resp.choices[0].message.content.strip(),
                }
            except Exception as e:
                print(f"⚠️ Groq Live no disponible ({e}). Usando simulación determinista de baja latencia...")

        # Nivel 3: Simulación Offline
        time.sleep(0.285)  # Simula 285ms de inferencia
        latencia_ms = round((time.perf_counter() - inicio) * 1000, 1)
        return {
            "ruta": "NIVEL 3 (OFFLINE SIM): SLM 8B Cuantizado INT4 + LoRA Mensual",
            "latencia_ms": latencia_ms,
            "cumple_sla_600ms": latencia_ms < 600.0,
            "respuesta": "He activado tu paquete mensual en el sistema. El cambio se reflejará en 5 minutos.",
        }