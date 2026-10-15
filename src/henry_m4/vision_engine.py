from typing import Any
from pydantic import ValidationError
from .schemas import (
    CalidadEscaneo,
    DecisionRuteo,
    ResultadoPipelineVision,
    SolicitudCreditoBancario,
)


class ModeloGuionadoVision:
    """
    Equivalente multimodal de ModeloGuionado / ModeloReglas del Módulo 3.
    Permite reproducir en clase y en tests unitarios los 3 escenarios reales sin consumir saldo de API:
    1. 'form_01_limpio.png': Escaneo limpio digital.
    2. 'form_02_manuscrito.png': Escritura a mano donde el VLM confunde '15.000,00' con '1500000.0' en el intento 1, y se corrige en el intento 2 tras recibir el traceback de Pydantic.
    3. 'form_03_borroso.png': Documento con mancha de café sobre el ingreso mensual y sin firma.
    """

    @staticmethod
    def invocar_extraccion(nombre_archivo: str, intento: int, ultimo_error_validacion: str | None = None) -> dict[str, Any]:
        # Caso 1: Formulario digital limpio
        if "limpio" in nombre_archivo:
            return {
                "id_formulario": "SOL-2026-001",
                "calidad_global": "NITIDO_DIGITAL",
                "evidencias_visuales": [
                    {
                        "campo": "nombre_solicitante",
                        "transcripcion_literal": "Martina Gómez Rojas",
                        "es_manuscrito": False,
                        "confianza_optica": 0.99,
                        "observacion_anomalia": None,
                    },
                    {
                        "campo": "ingreso_mensual_declarado",
                        "transcripcion_literal": "USD 3,200.00",
                        "es_manuscrito": False,
                        "confianza_optica": 0.98,
                        "observacion_anomalia": None,
                    },
                    {
                        "campo": "monto_credito_solicitado",
                        "transcripcion_literal": "USD 12,000.00",
                        "es_manuscrito": False,
                        "confianza_optica": 0.99,
                        "observacion_anomalia": None,
                    },
                ],
                "nombre_solicitante": "Martina Gómez Rojas",
                "identificador_tributario": "18.452.931-K",
                "ingreso_mensual_declarado": 3200.0,
                "monto_credito_solicitado": 12000.0,
                "plazo_meses": 24,
                "posee_firma_autografa": True,
                "confianza_global_extraccion": 0.98,
            }

        # Caso 2: Formulario manuscrito con falla intencional en el Intento 1 (coma decimal manuscrita)
        if "manuscrito" in nombre_archivo:
            if intento == 1:
                return {
                    "id_formulario": "SOL-2026-002",
                    "calidad_global": "MANUSCRITO_LEGIBLE",
                    "evidencias_visuales": [
                        {
                            "campo": "ingreso_mensual_declarado",
                            "transcripcion_literal": "$ 2.500,00 (letra cursiva)",
                            "es_manuscrito": True,
                            "confianza_optica": 0.88,
                            "observacion_anomalia": "Trazo inclinado pero legible",
                        },
                        {
                            "campo": "monto_credito_solicitado",
                            "transcripcion_literal": "$ 15.000,00",
                            "es_manuscrito": True,
                            "confianza_optica": 0.84,
                            "observacion_anomalia": "Coma decimal manuscrita muy pequeña",
                        },
                    ],
                    "nombre_solicitante": "Roberto Sánchez Vera",
                    "identificador_tributario": "14.221.890-4",
                    "ingreso_mensual_declarado": 2500.0,
                    "monto_credito_solicitado": 1500000.0,  # <-- ERROR INTENCIONAL: 1.5 millones en vez de 15 mil
                    "plazo_meses": 36,
                    "posee_firma_autografa": True,
                    "confianza_global_extraccion": 0.86,
                }
            else:
                return {
                    "id_formulario": "SOL-2026-002",
                    "calidad_global": "MANUSCRITO_LEGIBLE",
                    "evidencias_visuales": [
                        {
                            "campo": "ingreso_mensual_declarado",
                            "transcripcion_literal": "$ 2.500,00 (letra cursiva)",
                            "es_manuscrito": True,
                            "confianza_optica": 0.88,
                            "observacion_anomalia": "Trazo inclinado pero legible",
                        },
                        {
                            "campo": "monto_credito_solicitado",
                            "transcripcion_literal": "$ 15.000,00 (corregido tras re-inspeccionar coma decimal)",
                            "es_manuscrito": True,
                            "confianza_optica": 0.91,
                            "observacion_anomalia": "Se confirma que los dos últimos ceros corresponden a centavos (,00)",
                        },
                    ],
                    "nombre_solicitante": "Roberto Sánchez Vera",
                    "identificador_tributario": "14.221.890-4",
                    "ingreso_mensual_declarado": 2500.0,
                    "monto_credito_solicitado": 15000.0,  # <-- CORREGIDO POR SELF-HEALING
                    "plazo_meses": 36,
                    "posee_firma_autografa": True,
                    "confianza_global_extraccion": 0.89,
                }

        # Caso 3: Formulario con campo borroso / manchado (Abstención visual obligatoria)
        return {
            "id_formulario": "SOL-2026-003",
            "calidad_global": "BORROSO_O_INCOMPLETO",
            "evidencias_visuales": [
                {
                    "campo": "identificador_tributario",
                    "transcripcion_literal": None,
                    "es_manuscrito": True,
                    "confianza_optica": 0.15,
                    "observacion_anomalia": "Desenfoque de movimiento severo en la esquina superior derecha",
                },
                {
                    "campo": "ingreso_mensual_declarado",
                    "transcripcion_literal": None,
                    "es_manuscrito": True,
                    "confianza_optica": 0.10,
                    "observacion_anomalia": "Mancha oscura cubre completamente los dígitos del sueldo mensual",
                },
            ],
            "nombre_solicitante": "Lucía Fernández Castro",
            "identificador_tributario": None,
            "ingreso_mensual_declarado": None,
            "monto_credito_solicitado": 8500.0,
            "plazo_meses": 18,
            "posee_firma_autografa": False,
            "confianza_global_extraccion": 0.42,
        }


enrutar_solicitud = lambda solicitud: (
    (
        DecisionRuteo.RECHAZO_REESCANEO,
        "Calidad óptica crítica. Se rechaza automáticamente y se solicita nueva captura al cliente.",
    )
    if solicitud.calidad_global == CalidadEscaneo.ILEGIBLE_CRITICO
    else (
        DecisionRuteo.REVISION_HUMANA_HITL,
        "Interrupt activado: Existen campos nulos por abstención visual, falta firma o confianza < 0.85. Pasa a bandeja de oficial de riesgo.",
    )
    if (
        solicitud.ingreso_mensual_declarado is None
        or solicitud.identificador_tributario is None
        or not solicitud.posee_firma_autografa
        or solicitud.confianza_global_extraccion < 0.85
    )
    else (
        DecisionRuteo.APROBACION_DIRECTA,
        "Straight-Through Processing (STP): Datos completos, firma verificada, validación financiera superada y confianza >= 0.85.",
    )
)


class PipelineVisionAutoreparable:
    def __init__(self, max_intentos: int = 3) -> None:
        self.max_intentos = max_intentos
        self.modelo_offline = ModeloGuionadoVision()

    def procesar_formulario(self, nombre_archivo: str) -> ResultadoPipelineVision:
        errores_acumulados: list[str] = []
        ultimo_error: str | None = None

        for intento in range(1, self.max_intentos + 1):
            payload_crudo = self.modelo_offline.invocar_extraccion(
                nombre_archivo=nombre_archivo,
                intento=intento,
                ultimo_error_validacion=ultimo_error,
            )
            try:
                solicitud_validada = SolicitudCreditoBancario.model_validate(payload_crudo)
                decision, motivo = enrutar_solicitud(solicitud_validada)
                return ResultadoPipelineVision(
                    archivo_origen=nombre_archivo,
                    intentos_utilizados=intento,
                    bitacora_errores_pydantic=errores_acumulados,
                    decision_ruteo=decision,
                    motivo_ruteo=motivo,
                    datos_validados=solicitud_validada,
                )
            except ValidationError as err:
                mensaje_compacto = "; ".join([f"{e['loc']}: {e['msg']}" for e in err.errors()])
                errores_acumulados.append(f"Intento {intento}: {mensaje_compacto}")
                ultimo_error = mensaje_compacto

        return ResultadoPipelineVision(
            archivo_origen=nombre_archivo,
            intentos_utilizados=self.max_intentos,
            bitacora_errores_pydantic=errores_acumulados,
            decision_ruteo=DecisionRuteo.REVISION_HUMANA_HITL,
            motivo_ruteo="Se agotaron los reintentos de autorreparación sin superar el contrato de Pydantic.",
            datos_validados=None,
        )