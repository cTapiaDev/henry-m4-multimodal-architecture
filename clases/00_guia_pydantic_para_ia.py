# 🟢 Guía práctica e interactiva de Pydantic v2 aplicada a Ingeniería de IA (9 Escenarios Reales)
# %% [markdown]
# # 🛡️ Guía de Bolsillo: Pydantic v2 para AI Engineers (9 Escenarios Reales)
#
# En Ingeniería de IA, **Pydantic NO se usa solo para validar formularios web**:
# es nuestra **camisa de fuerza** para controlar la incertidumbre de los LLMs, VLMs (Visión) y modelos STT (Audio).
#
# Cada celda de este archivo es **100% independiente**. Puedes ejecutar cualquiera con `Run Cell`.

# %% [1] ESCENARIO 1: El "Traductor de Basura" (Coerción de Tipos y Límites Numéricos)
# 🟢 Escenario 1: Coerción automática de tipos y validación de rangos con Field
from pydantic import BaseModel, Field, ValidationError


class ExtraccionBasica(BaseModel):
    id_transaccion: int
    monto_usd: float = Field(..., gt=0, description="El monto siempre debe ser mayor a 0")
    confianza_ia: float = Field(..., ge=0.0, le=1.0, description="Probabilidad entre 0.0 y 1.0")
    aprobado: bool


# 1. El LLM devuelve strings en lugar de números y booleanos (algo muy común en JSONs crudos)
payload_sucio_llm = {
    "id_transaccion": "9081",
    "monto_usd": "1540.75",
    "confianza_ia": "0.92",
    "aprobado": "true",
}

objeto_limpio = ExtraccionBasica.model_validate(payload_sucio_llm)
print("✅ Coerción exitosa (de strings a tipos nativos de Python):")
print(f"   Monto (float real): {objeto_limpio.monto_usd + 100} | Aprobado (bool real): {objeto_limpio.aprobado}")

# 2. ¿Qué pasa si el LLM alucina una confianza de 1.5 (150%) o un monto negativo?
try:
    ExtraccionBasica.model_validate({"id_transaccion": 1, "monto_usd": -50, "confianza_ia": 1.5, "aprobado": False})
except ValidationError as err:
    print("\n❌ Bloqueo por fuera de rango:")
    for e in err.errors():
        print(f"   Campo '{e['loc'][0]}': {e['msg']}")


# %% [2] ESCENARIO 2: La "Jaula de Opciones" para Clasificación y Routers (Literal y Enum)
# 🟢 Escenario 2: Restricción estricta de vocabulario de salida con Literal y Enum
from enum import Enum
from typing import Literal
from pydantic import BaseModel, ValidationError


class DepartamentoDestino(str, Enum):
    SOPORTE_TECNICO = "SOPORTE_TECNICO"
    PREVENCION_FRAUDE = "PREVENCION_FRAUDE"
    FACTURACION = "FACTURACION"


class RouterTicketCliente(BaseModel):
    urgencia: Literal["BAJA", "MEDIA", "ALTA", "CRITICA"]
    departamento: DepartamentoDestino
    justificacion_breve: str


# 1. Caso válido
ruteo_ok = RouterTicketCliente(
    urgencia="CRITICA",
    departamento="PREVENCION_FRAUDE",
    justificacion_breve="Cliente reporta cargos no reconocidos en su tarjeta.",
)
print(f"✅ Ruteo válido: Urgencia {ruteo_ok.urgencia} -> {ruteo_ok.departamento.value}")

# 2. El LLM se pone "creativo" e inventa una urgencia que rompería nuestro if/else
try:
    RouterTicketCliente(
        urgencia="SUPER_URGENTE_POR_FAVOR",
        departamento="SOPORTE_TECNICO",
        justificacion_breve="No puede entrar a la app.",
    )
except ValidationError as err:
    print(f"\n❌ El LLM intentó inventar una categoría no permitida:\n   {err.errors()[0]['msg']}")


# %% [3] ESCENARIO 3: Visión y OCR — Abstención Controlada (Optional) y Listas Anidadas
# 🟢 Escenario 3: Modelos anidados para facturas y uso de Optional[T] = None para abstención óptica
from typing import Optional
from pydantic import BaseModel, Field


class ItemBoleta(BaseModel):
    descripcion: str
    cantidad: int = Field(..., ge=1)
    precio_unitario: Optional[float] = Field(
        None, description="Dejar en null si hay una mancha o rotura sobre el precio."
    )


class BoletaEscaneadaVLM(BaseModel):
    rut_emisor: Optional[str] = Field(None, description="null si el timbre está borroso")
    items: list[ItemBoleta]
    requiere_revision_humana: bool = False


# Simulamos la respuesta del VLM ante una boleta con el segundo precio manchado
respuesta_vlm = {
    "rut_emisor": "76.123.456-7",
    "items": [
        {"descripcion": "Licencia Cloud Anual", "cantidad": 1, "precio_unitario": 1200.0},
        {"descripcion": "Soporte Premium (Manchado)", "cantidad": 1, "precio_unitario": None},
    ],
}

boleta = BoletaEscaneadaVLM.model_validate(respuesta_vlm)
if any(item.precio_unitario is None for item in boleta.items):
    boleta.requiere_revision_humana = True

print(f"✅ Boleta procesada con {len(boleta.items)} ítems.")
print(f"🔍 ¿Hay campos con Abstención Visual (None)?: {boleta.items[1].precio_unitario is None}")
print(f"🧭 ¿Derivar a Human-in-the-Loop?: {boleta.requiere_revision_humana}")


# %% [4] ESCENARIO 4: Audio Básico — Limpieza de Muletillas y Formatos con @field_validator
# 🟢 Escenario 4: Uso de @field_validator para sanear un campo individual proveniente de STT
import re
from pydantic import BaseModel, field_validator


class DatosContactoVoz(BaseModel):
    nombre_cliente: str
    telefono_dictado: str
    transcripcion_limpia: str

    @field_validator("telefono_dictado")
    @classmethod
    def normalizar_telefono(cls, valor: str) -> str:
        # Extraemos solo los dígitos aunque Whisper haya puesto espacios, guiones o palabras
        solo_numeros = re.sub(r"\D", "", valor)
        if len(solo_numeros) < 8:
            raise ValueError(f"El teléfono '{valor}' está incompleto. Se perdieron dígitos en el audio.")
        return f"+{solo_numeros}"

    @field_validator("transcripcion_limpia")
    @classmethod
    def eliminar_muletillas_stt(cls, valor: str) -> str:
        # Limpiamos muletillas típicas de audio antes de guardar en base de datos
        limpio = re.sub(r"\b(eh+|este+|mmm+|o sea)\b", "", valor, flags=re.IGNORECASE)
        return re.sub(r"\s+", " ", limpio).strip()


contacto = DatosContactoVoz(
    nombre_cliente="Carlos",
    telefono_dictado="56 9 8765-4321",
    transcripcion_limpia="Ehhh hola, este... necesito ayuda con, o sea, mi clave.",
)
print("✅ Campos saneados automáticamente por @field_validator:")
print(f"   📞 Teléfono formateado : {contacto.telefono_dictado}")
print(f"   📝 Texto sin muletillas: '{contacto.transcripcion_limpia}'")


# %% [5] ESCENARIO 5: Contratos Legales y Finanzas — Auditoría Cruzada con @model_validator
# 🟢 Escenario 5: Uso de @model_validator(mode='after') para cruzar múltiples campos (Ideal para Proyecto Final)
from datetime import date
from typing import Optional
from pydantic import BaseModel, ValidationError, model_validator


class AnalisisContratoLegal(BaseModel):
    id_documento: str
    fecha_inicio: date
    fecha_termino: date
    posee_clausula_multa: bool
    monto_multa_usd: Optional[float] = None

    @model_validator(mode="after")
    def auditar_coherencia_legal(self) -> "AnalisisContratoLegal":
        # Regla 1: Coherencia temporal
        if self.fecha_termino <= self.fecha_inicio:
            raise ValueError(
                f"Incoherencia temporal: La fecha de término ({self.fecha_termino}) "
                f"no puede ser anterior o igual a la de inicio ({self.fecha_inicio})."
            )
        # Regla 2: Coherencia condicional entre dos campos
        if self.posee_clausula_multa and (self.monto_multa_usd is None or self.monto_multa_usd <= 0):
            raise ValueError(
                "Incoherencia contractual: Se indicó 'posee_clausula_multa=True', "
                "pero no se especificó un 'monto_multa_usd' válido."
            )
        return self


try:
    AnalisisContratoLegal(
        id_documento="CONT-2026-09",
        fecha_inicio="2026-05-01",
        fecha_termino="2026-12-31",
        posee_clausula_multa=True,
        monto_multa_usd=None,  # <-- El LLM olvidó extraer el monto de la multa
    )
except ValidationError as err:
    print("🛡️ @model_validator atrapó una contradicción entre dos campos del contrato:")
    print(f"   ❌ {err.errors()[0]['msg']}")


# %% [6] ESCENARIO 6: Agentes que Escriben Código o SQL — Firewall de Ciberseguridad
# 🟢 Escenario 6: Prevención de ejecución de código destructivo (Text-to-SQL Guardrail)
import re
from pydantic import BaseModel, ValidationError, field_validator


class ConsultaSQLAgente(BaseModel):
    explicacion_al_usuario: str
    sql_generado: str

    @field_validator("sql_generado")
    @classmethod
    def firewall_sql_solo_lectura(cls, query: str) -> str:
        comandos_prohibidos = r"\b(DROP|DELETE|UPDATE|INSERT|ALTER|TRUNCATE|GRANT|EXEC)\b"
        hallazgo = re.search(comandos_prohibidos, query, flags=re.IGNORECASE)
        if hallazgo:
            raise ValueError(
                f"ALERTA DE SEGURIDAD: El agente intentó ejecutar el comando destructivo '{hallazgo.group(0)}'. "
                "Solo se permiten consultas SELECT de lectura."
            )
        if not query.strip().upper().startswith("SELECT"):
            raise ValueError("La consulta debe iniciar estrictamente con 'SELECT'.")
        return query


try:
    ConsultaSQLAgente(
        explicacion_al_usuario="Voy a limpiar los registros duplicados.",
        sql_generado="DELETE FROM clientes WHERE estado = 'inactivo';",
    )
except ValidationError as err:
    print("🛑 FIREWALL ACTIVADO ANTES DE TOCAR LA BASE DE DATOS:")
    print(f"   {err.errors()[0]['msg']}")


# %% [7] ESCENARIO 7: El Puente con las APIs (De Clase Python a JSON Schema para el LLM)
# 🟢 Escenario 7: Demostración de model_json_schema() y model_validate_json()
import json
from pydantic import BaseModel, Field


class HallazgoSeguridad(BaseModel):
    archivo: str = Field(..., description="Ruta del archivo analizado")
    linea: int = Field(..., ge=1, description="Número de línea del bug")
    severidad: str = Field(..., pattern="^(BAJA|ALTA)$")


# 1. ¿Qué le enviamos realmente a Gemini / OpenAI cuando pasamos `response_schema=HallazgoSeguridad`?
esquema_para_api = HallazgoSeguridad.model_json_schema()
print("📤 1. Lo que Pydantic genera para obligar al LLM a cumplir la estructura (JSON Schema):")
print(json.dumps(esquema_para_api, indent=2, ensure_ascii=False))

# 2. ¿Cómo recibimos el string JSON que responde la API y lo volvemos objeto Python?
respuesta_string_api = '{"archivo": "auth.py", "linea": 42, "severidad": "ALTA"}'
objeto_validado = HallazgoSeguridad.model_validate_json(respuesta_string_api)
print(f"\n📥 2. Objeto reconstruido con autocompletado: {objeto_validado.archivo} (Línea {objeto_validado.linea})")


# %% [8] ESCENARIO 8: Pipeline de Voz (Groq STT -> Gemini -> TTS) ante Palabras Perdidas o Sin Lógica
# 🟢 Escenario 8: Aduana semántica cuando el audio omite un verbo clave o cambia el contexto ("anguila")
from typing import Literal, Optional
from pydantic import BaseModel, Field, ValidationError, model_validator


class DecisionAgenteVozBancario(BaseModel):
    transcripcion_recibida: str
    calidad_contexto: Literal["CLARO", "FALTA_VERBO_CRITICO", "TERMINO_FUERA_DE_DOMINIO"]
    accion_bancaria: Optional[Literal["BLOQUEAR_TARJETA", "TRANSFERIR", "ENVIAR_PLANILLA"]] = None
    terminos_sospechosos: list[str] = Field(default_factory=list)
    accion_pipeline: Literal["EJECUTAR_ACCION", "REINTENTAR_STT_CON_PROMPT", "PEDIR_ACLARACION_TTS"]
    texto_salida_tts: str

    @model_validator(mode="after")
    def proteger_ejecucion_voz(self) -> "DecisionAgenteVozBancario":
        # Caso A: Se comió el verbo en el audio (ej: "Quiero [___] mi tarjeta ahora")
        if self.calidad_contexto == "FALTA_VERBO_CRITICO":
            if self.accion_bancaria is not None or self.accion_pipeline != "PEDIR_ACLARACION_TTS":
                raise ValueError(
                    "Peligro por Omisión Acústica: Falta el verbo de acción en el audio. "
                    "PROHIBIDO adivinar 'accion_bancaria'. Debes fijar accion_bancaria=None, "
                    "accion_pipeline='PEDIR_ACLARACION_TTS' y preguntar al usuario en 'texto_salida_tts'."
                )
            if "?" not in self.texto_salida_tts:
                raise ValueError("El 'texto_salida_tts' debe contener una pregunta clara para que el cliente repita.")

        # Caso B: Whisper inventó una palabra absurda para el banco (ej: "Manda la anguila mañana")
        if self.calidad_contexto == "TERMINO_FUERA_DE_DOMINIO":
            if self.accion_pipeline == "EJECUTAR_ACCION":
                raise ValueError(
                    f"Incoherencia de Dominio detectada en {self.terminos_sospechosos}. "
                    "No ejecutes la acción; solicita 'REINTENTAR_STT_CON_PROMPT' inyectando vocabulario bancario a Groq."
                )
        return self


# Prueba 1: El cliente dijo "Quiero [RUIDO] mi tarjeta" y el LLM intentó adivinar que quería bloquearla
try:
    DecisionAgenteVozBancario(
        transcripcion_recibida="Hola, quiero mi tarjeta de crédito ahora mismo",
        calidad_contexto="FALTA_VERBO_CRITICO",
        accion_bancaria="BLOQUEAR_TARJETA",  # <-- El LLM intentó adivinar y bloquear la tarjeta!
        accion_pipeline="EJECUTAR_ACCION",
        texto_salida_tts="Perfecto, he bloqueado tu tarjeta.",
    )
except ValidationError as err:
    print("🛑 Caso Omisión de Palabra: Pydantic impidió que el LLM adivinara y bloqueara la tarjeta:")
    print(f"   ❌ {err.errors()[0]['msg']}\n")

# Prueba 2: Cómo debe pasar correctamente hacia el TTS cuando falta una palabra
decision_segura = DecisionAgenteVozBancario(
    transcripcion_recibida="Hola, quiero mi tarjeta de crédito ahora mismo",
    calidad_contexto="FALTA_VERBO_CRITICO",
    accion_bancaria=None,
    accion_pipeline="PEDIR_ACLARACION_TTS",
    texto_salida_tts="Disculpa, hubo ruido en la línea y no escuché qué deseas hacer con tu tarjeta. ¿Quieres bloquearla o consultar el saldo?",
)
print("✅ Respuesta segura autorizada para el motor TTS:")
print(f"   🧭 Acción Pipeline : {decision_segura.accion_pipeline}")
print(f"   🗣️ Voz TTS al cliente: '{decision_segura.texto_salida_tts}'")


# %% [9] ESCENARIO 9: Circuit Breaker por Anomalía de Densidad de Tokens (Groq STT -> Tiktoken -> Pydantic)
# 🟢 Escenario 9: Detener el pipeline ANTES de llamar al LLM si un segmento de la oración consume demasiados tokens
import tiktoken
from pydantic import BaseModel, Field, ValidationError, model_validator


class AuditoriaDensidadTranscripcion(BaseModel):
    segmentos_oracion: list[str] = Field(
        ..., description="Frases o grupos de palabras que componen la transcripción de Groq"
    )
    umbral_max_tokens_por_palabra: float = Field(
        default=1.65,
        description="En español limpio, 1 palabra consume ~1.1 a 1.3 tokens. Más de 1.65 indica fragmentación anormal.",
    )

    @model_validator(mode="after")
    def detectar_anomalia_tokenizacion(self) -> "AuditoriaDensidadTranscripcion":
        codificador = tiktoken.encoding_for_model("gpt-4o")
        reporte_segmentos = []

        for segmento in self.segmentos_oracion:
            palabras = [p for p in segmento.strip().split() if p]
            if not palabras:
                continue
            tokens = codificador.encode(segmento)
            densidad = len(tokens) / len(palabras)
            tokens_legibles = [codificador.decode([t]).replace(" ", " █") for t in tokens]

            reporte_segmentos.append((segmento, len(palabras), len(tokens), densidad, tokens_legibles))

            if densidad > self.umbral_max_tokens_por_palabra:
                raise ValueError(
                    f"CIRCUIT BREAKER ACTIVADO — Anomalía de Densidad de Tokens en el grupo: '{segmento}'. "
                    f"Consumió {len(tokens)} tokens para solo {len(palabras)} palabras "
                    f"(Densidad: {densidad:.2f} tokens/palabra > umbral {self.umbral_max_tokens_por_palabra}). "
                    f"Fragmentación detectada: {tokens_legibles}. "
                    "Se detiene el envío a Gemini para evitar Efecto Cascada; re-procesar segmento de audio."
                )
        return self


# Simulamos una transcripción dividida en 3 bloques de palabras (el segundo bloque viene corrupto por el STT)
bloques_stt = [
    "El cliente dijo que",                                # Bloque 1: Sano (4 palabras -> 4 tokens -> Densidad 1.00)
    "tenía probrema para a ceder a los detayes",          # Bloque 2: Roto (8 palabras -> 14 tokens -> Densidad 1.75 ¡ANOMALÍA!)
    "de su cuenta bancaria",                              # Bloque 3: Sano (4 palabras -> 4 tokens -> Densidad 1.00)
]

try:
    AuditoriaDensidadTranscripcion(segmentos_oracion=bloques_stt)
except ValidationError as err:
    print("⚡ CIRCUIT BREAKER DE PYDANTIC DETUVO EL PROCESO ANTES DE LLAMAR A GEMINI:")
    print(f"   🛑 {err.errors()[0]['msg']}")