from henry_m4.schemas import DecisionRuteo
from henry_m4.vision_engine import PipelineVisionAutoreparable


def verificar_m4l1() -> int:
    pipeline = PipelineVisionAutoreparable(max_intentos=3)

    r1 = pipeline.procesar_formulario("form_01_limpio.png")
    assert r1.intentos_utilizados == 1
    assert r1.decision_ruteo == DecisionRuteo.APROBACION_DIRECTA

    r2 = pipeline.procesar_formulario("form_02_manuscrito.png")
    assert r2.intentos_utilizados == 2
    assert r2.datos_validados is not None
    assert r2.datos_validados.monto_credito_solicitado == 15000.0
    assert r2.decision_ruteo == DecisionRuteo.APROBACION_DIRECTA

    r3 = pipeline.procesar_formulario("form_03_borroso.png")
    assert r3.intentos_utilizados == 1
    assert r3.datos_validados is not None
    assert r3.datos_validados.ingreso_mensual_declarado is None
    assert r3.decision_ruteo == DecisionRuteo.REVISION_HUMANA_HITL

    print("✅ Verificación M4L1 completada: Contratos visuales, Self-Healing y Routing funcionando al 100%.")
    return 0


if __name__ == "__main__":
    raise SystemExit(verificar_m4l1())