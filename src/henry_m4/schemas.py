from enum import Enum
from typing import Optional
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