from henry_m4.schemas import DecisionRuteo
from henry_m4.vision_engine import PipelineVisionAutoreparable


def test_formulario_limpio_aprobacion_directa() -> None:
    pipeline = PipelineVisionAutoreparable()
    res = pipeline.procesar_formulario("form_01_limpio.png")
    assert res.intentos_utilizados == 1
    assert res.decision_ruteo == DecisionRuteo.APROBACION_DIRECTA


def test_formulario_manuscrito_se_autorepara_en_intento_dos() -> None:
    pipeline = PipelineVisionAutoreparable()
    res = pipeline.procesar_formulario("form_02_manuscrito.png")
    assert res.intentos_utilizados == 2
    assert len(res.bitacora_errores_pydantic) == 1
    assert res.datos_validados is not None
    assert res.datos_validados.monto_credito_solicitado == 15000.0


def test_formulario_borroso_aplica_abstencion_y_rutea_a_humano() -> None:
    pipeline = PipelineVisionAutoreparable()
    res = pipeline.procesar_formulario("form_03_borroso.png")
    assert res.datos_validados is not None
    assert res.datos_validados.identificador_tributario is None
    assert res.datos_validados.ingreso_mensual_declarado is None
    assert res.decision_ruteo == DecisionRuteo.REVISION_HUMANA_HITL