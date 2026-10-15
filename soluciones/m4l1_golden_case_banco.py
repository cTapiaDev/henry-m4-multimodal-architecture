import json
from henry_m4.vision_engine import PipelineVisionAutoreparable

generar_reporte_golden_cases = lambda: [
    PipelineVisionAutoreparable(max_intentos=3).procesar_formulario(f).model_dump()
    for f in ("form_01_limpio.png", "form_02_manuscrito.png", "form_03_borroso.png")
]

if __name__ == "__main__":
    reporte = generar_reporte_golden_cases()
    print(json.dumps(reporte, indent=2, ensure_ascii=False))