import sys
from pathlib import Path
from henry_m4.vision_engine import PipelineVisionAutoreparable

def probar_imagen_unica(ruta_archivo: str) -> None:
    ruta = Path(ruta_archivo)
    if not ruta.exists():
        print(f"❌ No se encontró el archivo: {ruta}. Verifica la ruta.")
        return

    pipeline = PipelineVisionAutoreparable(max_intentos=3, forzar_live=True)
    
    print("\n" + "=" * 80)
    print(f"👁️ Procesando imagen real: {ruta.name}")
    resultado = pipeline.procesar_formulario(str(ruta))
    
    print(f"🧭 Decisión de Ruteo : {resultado.decision_ruteo.value}")
    print(f"📝 Motivo de Ruteo   : {resultado.motivo_ruteo}")
    print(f"🔄 Intentos          : {resultado.intentos_utilizados}")
    
    if resultado.datos_validados:
        datos = resultado.datos_validados
        print(f"👤 Titular extraído  : {datos.nombre_solicitante}")
        print(f"💰 Ingreso Mensual   : {datos.ingreso_mensual_declarado} (Abstención si es None)")
        print(f"✍️  Firma detectada   : {datos.posee_firma_autografa}")
        print(f"📊 Confianza Global  : {datos.confianza_global_extraccion}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("⚠️ Uso: uv run python scripts/probar_vision_real.py <ruta_de_la_imagen>")
    else:
        probar_imagen_unica(sys.argv[1])