from datetime import datetime
import json
from pydantic import ValidationError
from .config import get_settings
from .schemas import RegistroAuditoriaMCP, RespuestaAgenteMCP, SolicitudReembolsoMCP


class SimuladorCaosAdHoc:
    """Simula el problema de integraciones Ad-Hoc de la Diapositiva 4."""

    @staticmethod
    def consultar_agentes_desconectados(pregunta: str) -> list[dict]:
        return [
            {
                "agente": "Bot Web Marketing (Prompt hardcodeado v1)",
                "respuesta": "Sí, la mayoría de las empresas permiten reembolsos dentro de los 7 días.",
                "riesgo": "ALUCINACIÓN DE POLÍTICA: Promete 7 días cuando legalmente para productos digitales son 5.",
            },
            {
                "agente": "Bot Soporte WhatsApp (Script Ad-Hoc antiguo)",
                "respuesta": "No, los productos digitales generalmente no son reembolsables.",
                "riesgo": "RECHAZO ILEGAL: Ignora la nueva normativa v2.1 que sí permite reembolso bajo 20% de uso.",
            },
            {
                "agente": "Agente Call Center (Sin acceso a DB)",
                "respuesta": "Depende de la política de reembolsos de la empresa.",
                "riesgo": "RESPUESTA INÚTIL: No resuelve el ticket ni consulta el consumo real del cliente.",
            },
        ]


class ServidorMCPReembolsos:
    """Servidor MCP estandarizado que centraliza Resources, Tools, Prompts y Gobernanza."""

    def __init__(self, transporte: str = "STDIO"):
        self.nombre_servidor = "henry-mcp-refund-server"
        self.version_servidor = "2.1.0"
        self.transporte = "STDIO" if transporte.upper() == "STDIO" else "HTTP_SSE"
        self.audit_logs: list[RegistroAuditoriaMCP] = []

        # Base de datos interna simulada de órdenes de compra
        self._db_ordenes = {
            "ORD-101": {
                "producto": "Curso Master AI Engineering (Digital)",
                "dias_desde_compra": 3,
                "porcentaje_consumido": 12.5,
                "monto_usd": 199.0,
            },
            "ORD-202": {
                "producto": "Bootcamp Full-Stack Licencia Anual (Digital)",
                "dias_desde_compra": 3,
                "porcentaje_consumido": 65.0,
                "monto_usd": 250.0,
            },
            "ORD-999": {
                "producto": "Licencia Corporativa Enterprise AI",
                "dias_desde_compra": 2,
                "porcentaje_consumido": 5.0,
                "monto_usd": 1200.0,
            },
        }

    def _registrar_auditoria(self, metodo: str, estado: str, detalle: str) -> str:
        id_ev = f"MCP-AUDIT-{len(self.audit_logs) + 1:03d}"
        registro = RegistroAuditoriaMCP(
            id_evento=id_ev,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            transporte=self.transporte,
            metodo_jsonrpc=metodo,
            version_recurso="reembolsos://politicas/digitales@v2.1",
            estado=estado,
            detalle=detalle,
        )
        self.audit_logs.append(registro)
        return id_ev

    # 1. PRIMITIVA RESOURCE (Solo lectura - Contexto oficial centralizado)
    def leer_resource(self, uri: str) -> dict:
        id_audit = self._registrar_auditoria("resources/read", "EXITO", f"Lectura de {uri}")
        if uri == "reembolsos://politicas/productos-digitales":
            return {
                "uri": uri,
                "version": "v2.1",
                "id_auditoria": id_audit,
                "contenido": (
                    "POLÍTICA OFICIAL DE REEMBOLSOS DIGITALES (v2.1): "
                    "1) Plazo máximo: Hasta 5 días corridos desde la compra. "
                    "2) Uso máximo permitido: Menos del 20% del contenido digital consumido. "
                    "3) Gobernanza financiera: Todo reembolso mayor a $500 USD requiere firma de supervisor."
                ),
            }
        raise ValueError(f"Resource no encontrado: {uri}")

    # 2. PRIMITIVA TOOL (Ejecución controlada y validada con Pydantic)
    def llamar_tool(self, nombre_tool: str, argumentos: dict) -> dict:
        if nombre_tool != "evaluar_reembolso_digital":
            raise ValueError(f"Tool desconocida: {nombre_tool}")

        try:
            datos = SolicitudReembolsoMCP.model_validate(argumentos)
        except ValidationError as err:
            msg_error = err.errors()[0]["msg"]
            id_audit = self._registrar_auditoria("tools/call", "BLOQUEADO_POR_PYDANTIC", msg_error)
            return {
                "estado_tool": "ERROR_GOBERNANZA",
                "id_auditoria": id_audit,
                "error": msg_error,
            }

        cumple_dias = datos.dias_desde_compra <= 5
        cumple_consumo = datos.porcentaje_consumido < 20.0
        aprobado = cumple_dias and cumple_consumo

        decision = "REEMBOLSO_APROBADO" if aprobado else "REEMBOLSO_RECHAZADO"
        motivo = (
            f"Cumple plazo ({datos.dias_desde_compra}/5 días) y consumo ({datos.porcentaje_consumido}% < 20%)."
            if aprobado
            else f"Incumple requisitos: días={datos.dias_desde_compra} (máx 5), consumo={datos.porcentaje_consumido}% (máx 20%)."
        )

        id_audit = self._registrar_auditoria(
            "tools/call", "EXITO", f"Orden {datos.id_compra} -> {decision} (${datos.monto_usd} USD)"
        )
        return {
            "estado_tool": "OK",
            "id_auditoria": id_audit,
            "orden": datos.id_compra,
            "decision_oficial": decision,
            "politica_version": "v2.1",
            "explicacion_tecnica": motivo,
        }

    # 3. PRIMITIVA PROMPT (Plantilla estandarizada provista por el servidor)
    def obtener_prompt(self, nombre_prompt: str, contexto: dict) -> str:
        self._registrar_auditoria("prompts/get", "EXITO", f"Plantilla {nombre_prompt}")
        return (
            "Actúa como Agente Oficial auditado por MCP. "
            f"Política vigente: {contexto.get('politica')}. "
            f"Resultado de la Tool: {json.dumps(contexto.get('resultado_tool'), ensure_ascii=False)}. "
            "Responde estrictamente en JSON cumpliendo el esquema RespuestaAgenteMCP."
        )

    # INSPECCIÓN DEL CABLE (JSON-RPC 2.0 sobre STDIO vs HTTP/SSE)
    @staticmethod
    def simular_paquete_transporte(metodo: str, params: dict) -> dict:
        payload_jsonrpc = {"jsonrpc": "2.0", "id": 104, "method": metodo, "params": params}
        return {
            "STDIO (Local Subprocess Pipe)": f"stdin -> {json.dumps(payload_jsonrpc, ensure_ascii=False)}\\n",
            "HTTP_SSE (Remote Cloud Stream)": (
                "POST /mcp/v1/messages HTTP/1.1\n"
                "Authorization: Bearer mcp_tok_live_9981\n"
                "Content-Type: application/json\n\n"
                f"{json.dumps(payload_jsonrpc, indent=2, ensure_ascii=False)}"
            ),
        }

    def obtener_orden_db(self, id_compra: str) -> dict:
        return {"id_compra": id_compra, **self._db_ordenes[id_compra]}


class OrquestadorClienteMCP:
    """Host/Cliente MCP que conecta el Servidor MCP con el LLM (Plan A Gemini -> Plan B Groq -> Plan C Offline)."""

    def __init__(self, servidor: ServidorMCPReembolsos, forzar_live: bool = False):
        self.servidor = servidor
        self.settings = get_settings()
        self.usar_live = forzar_live or self.settings.is_live

    def resolver_consulta_reembolso(self, id_compra: str, pregunta_usuario: str) -> RespuestaAgenteMCP:
        # 1. El Host lee el Resource oficial desde MCP
        recurso = self.servidor.leer_resource("reembolsos://politicas/productos-digitales")
        # 2. Obtiene los datos de la orden y ejecuta la Tool MCP validada por Pydantic
        datos_orden = self.servidor.obtener_orden_db(id_compra)
        resultado_tool = self.servidor.llamar_tool("evaluar_reembolso_digital", datos_orden)
        # 3. Obtiene el Prompt estandarizado del servidor MCP
        prompt_mcp = self.servidor.obtener_prompt(
            "resolucion_reembolso", {"politica": recurso["contenido"], "resultado_tool": resultado_tool}
        )

        payload_llm = self._invocar_cerebro(pregunta_usuario, prompt_mcp, resultado_tool)
        return RespuestaAgenteMCP.model_validate(payload_llm)

    def _invocar_cerebro(self, pregunta: str, prompt_mcp: str, resultado_tool: dict) -> dict:
        if self.usar_live:
            # Plan A: Google Gemini
            if self.settings.gemini_api_key:
                try:
                    from google import genai
                    from google.genai import types

                    client = genai.Client(api_key=self.settings.gemini_api_key)
                    resp = client.models.generate_content(
                        model=self.settings.gemini_model,
                        contents=f"{prompt_mcp}\nPregunta del cliente: {pregunta}",
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=RespuestaAgenteMCP,
                            temperature=0.0,
                        ),
                    )
                    return json.loads(resp.text)
                except Exception:
                    print("⚠️ Gemini saturado (503). Saltando a PLAN B (Groq) mantendo el contexto MCP...")

            # Plan B: Groq
            if self.settings.groq_api_key:
                try:
                    from groq import Groq

                    g_client = Groq(api_key=self.settings.groq_api_key)
                    esquema = json.dumps(RespuestaAgenteMCP.model_json_schema(), ensure_ascii=False)
                    resp_g = g_client.chat.completions.create(
                        model="allam-2-7b",
                        messages=[
                            {
                                "role": "system",
                                "content": f"{prompt_mcp}\nREGLA ESTRICTA: Tu respuesta debe ser ÚNICA y EXCLUSIVAMENTE un objeto JSON válido según este esquema: {esquema}. SIN markdown (no uses ```json), SIN saludos, SIN texto adicional."
                            },
                            {"role": "user", "content": pregunta},
                        ],
                        temperature=0.0,
                    )
                    
                    # Extracción a prueba de balas: buscar solo el primer bloque JSON válido
                    texto = resp_g.choices[0].message.content.strip()
                    
                    import re
                    # Busca el contenido desde el primer '{' hasta su respectivo cierre lógico
                    match = re.search(r'\{.*\}', texto, re.DOTALL)
                    if match:
                        texto_limpio = match.group(0)
                        return json.loads(texto_limpio)
                    else:
                        raise ValueError("No se encontró un JSON válido en la respuesta de Groq.")
                        
                except Exception as e:
                    print(f"⚠️ Groq también falló ({e}). Saltando a PLAN C (Simulación Offline MCP)...")

        # Plan C: Respuesta determinista Offline basada en los datos reales del servidor MCP
        if resultado_tool["estado_tool"] == "ERROR_GOBERNANZA":
            return {
                "decision": "REQUIERE_ESCALAMIENTO_HUMANO",
                "politica_aplicada": "reembolsos://politicas/productos-digitales@v2.1",
                "id_auditoria_mcp": resultado_tool["id_auditoria"],
                "mensaje_al_cliente": f"Tu solicitud requiere autorización de un supervisor: {resultado_tool['error']}",
            }

        return {
            "decision": resultado_tool["decision_oficial"],
            "politica_aplicada": f"reembolsos://politicas/productos-digitales@{resultado_tool['politica_version']}",
            "id_auditoria_mcp": resultado_tool["id_auditoria"],
            "mensaje_al_cliente": (
                f"Resultado oficial ({resultado_tool['decision_oficial']}): {resultado_tool['explicacion_tecnica']} "
                f"[Auditoría: {resultado_tool['id_auditoria']}]"
            ),
        }