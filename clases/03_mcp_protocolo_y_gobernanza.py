# %% [markdown]
# # 🔌 Clase 3: Model Context Protocol (MCP) — Control, Gobernanza y Confiabilidad
# **Caso de Estudio (Diapositiva 4):** *"¿Puedo solicitar un reembolso por un producto digital después de 3 días?"*

# %% [1] EL PROBLEMA: El Caos de las Integraciones Ad-Hoc (Diapositiva 4)
# 🟢 Demostración de respuestas contradictorias cuando cada bot tiene prompts y scripts desconectados
import importlib
import json
import henry_m4.schemas
import henry_m4.mcp_engine

importlib.reload(henry_m4.schemas)
importlib.reload(henry_m4.mcp_engine)

from henry_m4.mcp_engine import SimuladorCaosAdHoc, ServidorMCPReembolsos, OrquestadorClienteMCP

pregunta_slide_4 = "¿Puedo solicitar un reembolso por un producto digital después de 3 días?"
print(f"❓ PREGUNTA DEL CLIENTE: '{pregunta_slide_4}'\n")
print("💥 RESULTADO EN ARQUITECTURA AD-HOC (Sin MCP - Cada equipo programó su propio bot):")
print("=" * 85)

for caso in SimuladorCaosAdHoc.consultar_agentes_desconectados(pregunta_slide_4):
    print(f"🤖 {caso['agente']}:")
    print(f"   💬 Respuesta: \"{caso['respuesta']}\"")
    print(f"   🚨 Riesgo   : {caso['riesgo']}\n")


# %% [2] LA SOLUCIÓN MCP: Las 3 Primitivas (Resources, Tools y Prompts - Diapositiva 5)
# 🟢 Uso de un Servidor MCP único como fuente de verdad para todos los agentes
servidor_mcp = ServidorMCPReembolsos(transporte="STDIO")

# 1. Lectura del RESOURCE (Solo lectura, versionado y gobernable)
recurso_oficial = servidor_mcp.leer_resource("reembolsos://politicas/productos-digitales")
print("📘 1. PRIMITIVA RESOURCE (Documento oficial centralizado):")
print(f"   URI: {recurso_oficial['uri']} ({recurso_oficial['version']})")
print(f"   Contenido: {recurso_oficial['contenido']}\n")

# 2. Ejecución de la TOOL para dos clientes distintos que compraron hace 3 días
orden_cliente_a = servidor_mcp.obtener_orden_db("ORD-101")  # 3 días, 12.5% consumido
orden_cliente_b = servidor_mcp.obtener_orden_db("ORD-202")  # 3 días, 65.0% consumido

res_a = servidor_mcp.llamar_tool("evaluar_reembolso_digital", orden_cliente_a)
res_b = servidor_mcp.llamar_tool("evaluar_reembolso_digital", orden_cliente_b)

print("🛠️ 2. PRIMITIVA TOOL (Evaluación determinista validada con Pydantic):")
print(f"   Cliente A (ORD-101 | 3 días | 12.5% uso) -> {res_a['decision_oficial']} ({res_a['explicacion_tecnica']})")
print(f"   Cliente B (ORD-202 | 3 días | 65.0% uso) -> {res_b['decision_oficial']} ({res_b['explicacion_tecnica']})")


# %% [3] BAJO EL CAPÓ: Modelos de Transporte MCP (STDIO vs HTTP/Streaming - Diapositiva 5)
# 🟢 Comparación del mensaje JSON-RPC 2.0 viajando por consola local (STDIO) vs nube (HTTP/SSE)
paquetes = ServidorMCPReembolsos.simular_paquete_transporte(
    metodo="tools/call",
    params={"name": "evaluar_reembolso_digital", "arguments": orden_cliente_a},
)

print("🔌 MODELO DE TRANSPORTE 1: STDIO (Ideal para Claude Desktop, VS Code, Cursor en local)")
print("-" * 85)
print(paquetes["STDIO (Local Subprocess Pipe)"])

print("\n🌐 MODELO DE TRANSPORTE 2: HTTP / SSE Streaming (Ideal para microservicios en producción)")
print("-" * 85)
print(paquetes["HTTP_SSE (Remote Cloud Stream)"])


# %% [4] GOBERNANZA Y AUDITORÍA: Bloqueo de Acciones Peligrosas y Trazabilidad (Diapositivas 7 y 9)
# 🟢 Qué ocurre cuando el LLM intenta reembolsar $1,200 USD sin firma de un supervisor humano
orden_corporativa = servidor_mcp.obtener_orden_db("ORD-999")  # Monto: $1,200 USD sin firma de supervisor
intento_bloqueado = servidor_mcp.llamar_tool("evaluar_reembolso_digital", orden_corporativa)

print("🛡️ PRUEBA DE GOBERNANZA FINANCIERA EN EL SERVIDOR MCP:")
print(json.dumps(intento_bloqueado, indent=2, ensure_ascii=False))

print("\n📋 TABLA DE AUDITORÍA CENTRALIZADA DEL SERVIDOR MCP (Audit Trail):")
print("-" * 95)
for log in servidor_mcp.audit_logs:
    icono = "✅" if log.estado == "EXITO" else "🛑"
    print(f"{icono} [{log.id_evento}] {log.timestamp} | {log.transporte} | {log.metodo_jsonrpc:<14} | {log.detalle}")


# %% [5] DEMO EN VIVO (HÍBRIDA): Host LLM + Servidor MCP en Acción (Diapositiva 9)
# 🟢 El LLM recibe la pregunta del cliente, consulta el servidor MCP y entrega una respuesta auditada
cliente_mcp = OrquestadorClienteMCP(servidor=servidor_mcp, forzar_live=True)

respuesta_final = cliente_mcp.resolver_consulta_reembolso(
    id_compra="ORD-101",
    pregunta_usuario="Hola, compré el curso digital hace 3 días (Orden ORD-101), apenas vi el primer módulo. ¿Me pueden reembolsar?",
)

print("🤖 RESPUESTA FINAL DEL AGENTE CONECTADO A MCP (Validada por Pydantic):")
print(json.dumps(respuesta_final.model_dump(), indent=2, ensure_ascii=False))


# %% [6] ACTIVIDAD PRÁCTICA PARA ALUMNOS: Diseña tu propia Regla de Gobernanza en MCP
# 🟢 Reto individual: Modifica los parámetros o agrega una validación para evitar abuso de reembolsos
print("🎯 RETO PRÁCTICO PARA EXPERIMENTAR:")
print("1. Prueba cambiar 'aprobacion_supervisor' en la orden ORD-999 para que el servidor MCP apruebe los $1,200 USD.")
print("2. En 'schemas.py' (SolicitudReembolsoMCP), agrega una regla en @model_validator que bloquee reembolsos")
print("   si 'dias_desde_compra == 0' y 'porcentaje_consumido > 80' (Detección de fraude por descarga masiva).")

orden_999_autorizada = {
    "id_compra": "ORD-999",
    "dias_desde_compra": 2,
    "porcentaje_consumido": 5.0,
    "monto_usd": 1200.0,
    "aprobacion_supervisor": "SUP-CARLOS-OK",  # <-- Firma humana inyectada
}
resultado_autorizado = servidor_mcp.llamar_tool("evaluar_reembolso_digital", orden_999_autorizada)
print("\n🔓 Resultado al incluir firma del supervisor en ORD-999:")
print(json.dumps(resultado_autorizado, indent=2, ensure_ascii=False))