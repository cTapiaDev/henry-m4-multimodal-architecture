from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class CalidadEscaneo(str, Enum):
    NITIDO_DIGITAL = "NITIDO_DIGITAL"
    MANUSCRITO_LEGIBLE = "MANUSCRITO_LEGIBLE"
    BORROSO_O_INCOMPLETO = "BORROSO_O_INCOMPLETO"
    ILEGIBLE_CRITICO = "ILEGIBLE_CRITICO"


class DecisionRuteo(str, Enum):
    APROBACION_DIRECTA = "APROBACION_DIRECTA_STP"
    REVISION_HUMANA_HITL = "INTERRUPT_REVISION_HUMANA_HITL"
    RECHAZO_REESCANEO = "RECHAZO_SOLICITAR_NUEVA_IMAGEN"


class EvidenciaVisualCampo(BaseModel):
    campo: str = Field(..., description="Nombre técnico del campo inspeccionado en el formulario")
    transcripcion_literal: Optional[str] = Field(
        None,
        description="Texto exacto tal como se observa en la imagen (incluyendo tachones o dudas), o None si está en blanco/ilegible",
    )
    es_manuscrito: bool = Field(False, description="True si el trazo fue hecho a mano alzada")
    confianza_optica: float = Field(
        ..., ge=0.0, le=1.0, description="Nivel de certeza visual sobre la lectura de este campo (0.0 a 1.0)"
    )
    observacion_anomalia: Optional[str] = Field(
        None, description="Detalle de borrones, tachaduras, sellos superpuestos o recortes de página"
    )


class SolicitudCreditoBancario(BaseModel):
    id_formulario: str = Field(..., description="Código identificador único del documento escaneado")
    calidad_global: CalidadEscaneo = Field(..., description="Diagnóstico general de la calidad visual del escaneo")
    evidencias_visuales: list[EvidenciaVisualCampo] = Field(
        ..., description="Registro obligatorio de inspección ocular antes de normalizar los tipos de datos"
    )
    nombre_solicitante: str = Field(..., min_length=3, description="Nombre completo del titular solicitante")
    identificador_tributario: Optional[str] = Field(
        None, description="RUT/CUIT/DNI del solicitante. Debe ser None si el campo está borroso o vacío (Abstención)"
    )
    ingreso_mensual_declarado: Optional[float] = Field(
        None, description="Ingreso mensual neto en USD. None si no es legible con certeza"
    )
    monto_credito_solicitado: float = Field(
        ..., description="Monto total del crédito solicitado en USD"
    )
    plazo_meses: int = Field(..., ge=6, le=360, description="Plazo de pago solicitado en meses")
    posee_firma_autografa: bool = Field(..., description="True únicamente si se visualiza trazo de firma en el recuadro")
    confianza_global_extraccion: float = Field(
        ..., ge=0.0, le=1.0, description="Promedio ponderado de confianza sobre los campos críticos del negocio"
    )

    @field_validator("nombre_solicitante")
    @classmethod
    def validar_nombre_completo(cls, valor: str) -> str:
        limpio = " ".join(valor.strip().split())
        if len(limpio.split()) < 2:
            raise ValueError(
                f"El nombre '{limpio}' parece incompleto. Debe incluir al menos nombre y apellido según el documento."
            )
        return limpio

    @model_validator(mode="after")
    def verificar_coherencia_financiera_y_visual(self) -> "SolicitudCreditoBancario":
        # Regla 1: Detectar errores clásicos de OCR/VLM con separadores decimales en escritura a mano
        if self.ingreso_mensual_declarado is not None:
            ratio_deuda_ingreso = self.monto_credito_solicitado / self.ingreso_mensual_declarado
            if ratio_deuda_ingreso > 45.0:
                evidencia_monto = next(
                    (e.transcripcion_literal for e in self.evidencias_visuales if e.campo == "monto_credito_solicitado"),
                    "N/A",
                )
                raise ValueError(
                    f"Inconsistencia financiera severa: El monto solicitado (${self.monto_credito_solicitado:,.2f}) "
                    f"supera en {ratio_deuda_ingreso:.1f} veces el ingreso mensual (${self.ingreso_mensual_declarado:,.2f}). "
                    f"En tu evidencia visual transcribiste '{evidencia_monto}'. Verifica si confundiste una coma decimal "
                    f"manuscrita (ej. ',00') con ceros adicionales y corrige el float."
                )

        # Regla 2: Coherencia entre calidad borrosa y exceso de confianza (alucinación de certeza)
        if self.calidad_global == CalidadEscaneo.BORROSO_O_INCOMPLETO and self.confianza_global_extraccion > 0.75:
            raise ValueError(
                f"Contradicción de incertidumbre: Clasificaste el documento como '{self.calidad_global.value}', "
                f"pero asignaste una confianza global alta ({self.confianza_global_extraccion}). "
                f"Si hay campos borrosos o ausentes, debes abstenerte (usar None) y ajustar la confianza <= 0.75."
            )

        return self


class ResultadoPipelineVision(BaseModel):
    archivo_origen: str
    intentos_utilizados: int
    bitacora_errores_pydantic: list[str]
    decision_ruteo: DecisionRuteo
    motivo_ruteo: str
    datos_validados: Optional[SolicitudCreditoBancario] = None


# 🟢 -------------------------------------------------------------------------
# 🟢 CONTRATOS PARA AUDIO (STT -> LLM -> TTS) - Módulo 4 Lección 2
# 🟢 -------------------------------------------------------------------------

class ResumenLlamadaSoporte(BaseModel):
    id_llamada: str = Field(..., description="ID único de la llamada")
    motivo_principal_llamada: str = Field(..., description="Clasificación del problema técnico central")
    entidades_afectadas: list[str] = Field(..., description="Ej: 'cuenta', 'tarjeta', 'login'")
    resumen_para_tts: str = Field(..., description="Resumen limpio y profesional para ser leído por una IA de voz")
    requiere_escalamiento: bool = Field(..., description="True si requiere atención técnica o humana")

    @model_validator(mode="after")
    def verificar_perdida_de_contexto(self) -> "ResumenLlamadaSoporte":
        """
        Evita el Efecto Cascada: Si la transcripción cruda hablaba de un problema técnico, 
        el LLM no puede hacer un resumen genérico como "El cliente pidió que lo llamen".
        """
        resumen_lower = self.resumen_para_tts.lower()
        
        # Validar si el LLM omitió la urgencia técnica
        if "llamen de vuelta" in resumen_lower or "volver a llamar" in resumen_lower:
            if not any(keyword in resumen_lower for keyword in ["cuenta", "acceso", "problema", "detalle"]):
                raise ValueError(
                    "Pérdida de Intención Crítica (Alucinación por Omisión): El resumen generado ignora "
                    "el problema técnico del usuario y solo menciona que lo llamen. Re-analiza la transcripción "
                    "fonética y extrae el motivo real del problema."
                )
        return self


# 🟢 Contratos Pydantic v2 para Clase 3: MCP (Tools, Gobernanza y Auditoría)
class SolicitudReembolsoMCP(BaseModel):
    id_compra: str = Field(..., pattern=r"^ORD-\d+$", description="ID de orden con formato ORD-XXX")
    dias_desde_compra: int = Field(..., ge=0, le=365, description="Días transcurridos desde la compra")
    porcentaje_consumido: float = Field(..., ge=0.0, le=100.0, description="Porcentaje consumido del producto digital")
    monto_usd: float = Field(..., gt=0, description="Monto del reembolso en dólares")
    aprobacion_supervisor: Optional[str] = Field(
        None, description="Código de firma humana obligatorio si monto_usd > 500"
    )

    @model_validator(mode="after")
    def validar_gobernanza_financiera(self) -> "SolicitudReembolsoMCP":
        if self.monto_usd > 500.0 and not self.aprobacion_supervisor:
            raise ValueError(
                f"GOBERNANZA MCP BLOQUEADA: El reembolso de ${self.monto_usd} USD supera el límite automático "
                "de $500 USD. Se requiere 'aprobacion_supervisor' (Human-in-the-Loop)."
            )
        return self


class RespuestaAgenteMCP(BaseModel):
    decision: Literal["REEMBOLSO_APROBADO", "REEMBOLSO_RECHAZADO", "REQUIERE_ESCALAMIENTO_HUMANO"]
    politica_aplicada: str = Field(..., description="Versión del Resource MCP consultado")
    id_auditoria_mcp: str = Field(..., description="ID único de trazabilidad generado por el servidor MCP")
    mensaje_al_cliente: str = Field(..., description="Explicación clara y fiel a la política oficial")


class RegistroAuditoriaMCP(BaseModel):
    id_evento: str
    timestamp: str
    transporte: Literal["STDIO", "HTTP_SSE"]
    metodo_jsonrpc: str
    version_recurso: str
    estado: Literal["EXITO", "BLOQUEADO_POR_PYDANTIC"]
    detalle: str


# 🟢 Contratos Pydantic v2 para Clase 4: Ingeniería Bajo Restricciones (SLA < 600ms, Tokenización y LoRA)
from typing import Literal
from pydantic import BaseModel, Field, model_validator


class PropuestaArquitecturaSLA(BaseModel):
    nombre_equipo: str
    enfoque_tokenizacion: Literal["BPE_BYTE_LEVEL", "WORDPIECE_ESTATICO"]
    metodo_adaptacion: Literal["FULL_FINE_TUNING", "PEFT_LORA_MAS_RAG"]
    tamano_modelo_billones: float = Field(..., gt=0, description="Tamaño del modelo en billones de parámetros (ej. 8.0)")
    usa_cuantizacion_int4: bool
    usa_cache_semantico: bool
    presupuesto_max_mensual_usd: float = Field(default=150.0, gt=0)

    latencia_estimada_ms: float = 0.0
    costo_adaptacion_mensual_usd: float = 0.0
    tasa_tokens_desconocidos_unk: float = 0.0

    @model_validator(mode="after")
    def auditar_restricciones_negocio(self) -> "PropuestaArquitecturaSLA":
        # 1. Auditoría de Tokenización (Requisito: nuevos términos cada mes)
        if self.enfoque_tokenizacion == "WORDPIECE_ESTATICO":
            self.tasa_tokens_desconocidos_unk = 18.5
            raise ValueError(
                "RECHAZO DE TOKENIZACIÓN: 'WORDPIECE_ESTATICO' genera 18.5% de tokens [UNK] ante jerga nueva mensual. "
                "Debes elegir 'BPE_BYTE_LEVEL' para descomponer palabras nuevas sin perder información."
            )
        self.tasa_tokens_desconocidos_unk = 0.0

        # 2. Auditoría de Adaptación y Costo (Requisito: muy bajo costo mensual)
        if self.metodo_adaptacion == "FULL_FINE_TUNING":
            self.costo_adaptacion_mensual_usd = self.tamano_modelo_billones * 320.0
        else:
            # PEFT/LoRA entrena < 0.2% de los pesos
            self.costo_adaptacion_mensual_usd = self.tamano_modelo_billones * 4.5

        if self.costo_adaptacion_mensual_usd > self.presupuesto_max_mensual_usd:
            raise ValueError(
                f"VIOLACIÓN DE PRESUPUESTO: El método '{self.metodo_adaptacion}' cuesta "
                f"${self.costo_adaptacion_mensual_usd:.2f} USD/mes (Límite: ${self.presupuesto_max_mensual_usd:.2f} USD). "
                "Usa 'PEFT_LORA_MAS_RAG' para cumplir el bajo costo."
            )

        # 3. Auditoría de Latencia (Requisito estricto: < 600 ms)
        latencia_base = self.tamano_modelo_billones * 55.0  # ~55ms por cada 1B de parámetros en FP16
        if self.usa_cuantizacion_int4:
            latencia_base *= 0.48
        if self.usa_cache_semantico:
            latencia_base *= 0.65

        self.latencia_estimada_ms = round(latencia_base + 45.0, 1)  # +45ms de red/tokenización

        if self.latencia_estimada_ms >= 600.0:
            raise ValueError(
                f"VIOLACIÓN DE SLA DE LATENCIA: El diseño tarda {self.latencia_estimada_ms} ms (Máximo permitido: 600 ms). "
                "Reduce el tamaño del modelo (SLM 3B-8B), activa cuantización INT4 o Caché Semántico."
            )
        return self


class StartupServingProposal(BaseModel):
    team_name: str = Field(..., description="Nombre del equipo o grupo de trabajo")
    adaptation_method: Literal["LORA_PEFT", "FULL_FINE_TUNING"]
    serving_pattern: Literal["SERVERLESS_AUTOSCALE_WARM", "SERVERLESS_PURO_COLD", "SERVER_BASED_24_7"]
    bottleneck_type: Literal["CPU_BOUND", "IO_BOUND"]
    optimization_tool: Literal["CPROFILE", "ASYNCIO"]

    estimated_monthly_cost_usd: float = 0.0
    handles_300_rpm_spike: bool = False

    @model_validator(mode="after")
    def validate_startup_architecture(self) -> "StartupServingProposal":
        # 1. Validar Adaptación (Startup con presupuesto ajustado)
        if self.adaptation_method == "FULL_FINE_TUNING":
            raise ValueError(
                "RECHAZO DE ADAPTACIÓN: 'FULL_FINE_TUNING' es inviable para la startup. "
                "Además, en picos de 300 solicitudes/minuto, los adaptadores 'LORA_PEFT' pesan pocos MB "
                "y permiten levantar contenedores rápido sin duplicar el modelo base."
            )

        # 2. Validar Patrón de Serving (Tráfico de 3 req/hora a 300 req/minuto)
        if self.serving_pattern == "SERVER_BASED_24_7":
            self.estimated_monthly_cost_usd = 3850.0
            raise ValueError(
                f"DESPERDICIO FINANCIERO: 'SERVER_BASED_24_7' cuesta ${self.estimated_monthly_cost_usd} USD/mes "
                "pagando GPUs ociosas cuando solo entran 3 solicitudes por hora en la noche."
            )
        if self.serving_pattern == "SERVERLESS_PURO_COLD":
            self.estimated_monthly_cost_usd = 180.0
            self.handles_300_rpm_spike = False
            raise ValueError(
                "FALLO POR COLD START: 'SERVERLESS_PURO_COLD' escala desde 0, pero demora ~22 segundos en "
                "cargar el LLM en la GPU cuando explota el pico viral de 300 solicitudes/minuto. "
                "Usa 'SERVERLESS_AUTOSCALE_WARM' (con 1 instancia tibia o arquitectura híbrida)."
            )

        self.estimated_monthly_cost_usd = 310.0
        self.handles_300_rpm_spike = True

        # 3. Validar coherencia entre Cuello de Botella y Herramienta (cProfile vs asyncio)
        if self.bottleneck_type == "CPU_BOUND" and self.optimization_tool == "ASYNCIO":
            raise ValueError(
                "ERROR CONCEPTUAL GRAVE: Elegiste 'ASYNCIO' para un cuello de botella 'CPU_BOUND'. "
                "Si el procesador está al 100% limpiando texto en Python, asyncio NO acelera nada. "
                "Debes diagnosticar con 'CPROFILE' y optimizar el algoritmo."
            )
        if self.bottleneck_type == "IO_BOUND" and self.optimization_tool == "CPROFILE":
            raise ValueError(
                "HERRAMIENTA INCORRECTA: Si el cuello de botella es 'IO_BOUND' (esperar respuestas de red del LLM "
                "a 300 req/min), necesitas concurrencia asíncrona con 'ASYNCIO' para procesar en paralelo."
            )

        return self