import tiktoken
import json
from pydantic import ValidationError
from .schemas import ResumenLlamadaSoporte
from .config import get_settings

# 1. Simulador Visual de Tokenización (BPE)
def diagnosticar_tokenizacion(texto: str) -> list[str]:
    """Divide el texto en tokens exactos como los vería GPT-4 o un modelo LLM moderno."""
    codificador = tiktoken.encoding_for_model("gpt-4o")
    tokens = codificador.encode(texto)
    # Reemplazamos el caracter especial de espacio para que se vea claro en consola
    return [codificador.decode([t]).replace(" ", " █") for t in tokens]


# 2. Simulador de STT (Speech-to-Text) y WER
class STTOfflineSimulator:
    @staticmethod
    def transcribir_audio(id_audio: str) -> dict[str, str]:
        # Simulamos la transcripción rota de la diapositiva 9 del curso
        if id_audio == "audio_soporte_01":
            return {
                "texto_limpio_ideal": "El cliente dijo que tenía problema para acceder a los detalles de su cuenta. Por favor llámalo mañana.",
                "transcripcion_cruda": "El cliente dijo que tenía probrema para a ceder a los detayes de su cuenta. Por favor yamalo mañana."
            }
        # Simulamos el error fonético de la diapositiva 4
        elif id_audio == "audio_granja_02":
            return {
                "texto_limpio_ideal": "Por favor, envía el correo de bienvenida y filtra el perfil de la franja.",
                "transcripcion_cruda": "Por favor, envía el correo de bienvenido y filetea el perfil de la granja."
            }
        return {"texto_limpio_ideal": "", "transcripcion_cruda": ""}

    @staticmethod
    def auditar_wer(crudo: str) -> list[str]:
        """Auditoría determinista simple para mostrar los 3 tipos de errores (Sustitución, Inserción, Omisión)"""
        if "probrema" in crudo:
            return [
                "Sustitución (S) : 'problema' -> 'probrema'",
                "Inserción (I)   : 'acceder'  -> 'a' + 'ceder' (Error de segmentación de palabra)",
                "Sustitución (S) : 'detalles' -> 'detayes'",
                "Sustitución (S) : 'llámalo'  -> 'yamalo' (Yeísmo)"
            ]
        return ["Sustitución (S): 'filtra' -> 'filetea'", "Sustitución (S): 'franja' -> 'granja'"]


# 3. Pipeline End-to-End con Self-Healing
class PipelineAudioSoporte:
    def __init__(self, max_intentos: int = 3, forzar_live: bool = False):
        self.max_intentos = max_intentos
        self.settings = get_settings()
        self.usar_live = forzar_live or self.settings.is_live

    def _obtener_transcripcion(self, id_o_ruta: str) -> str:
        if self.usar_live and self.settings.groq_api_key:
            try:
                whisper = ModeloGroqWhisperLive(self.settings.groq_api_key)
                return whisper.transcribir(id_o_ruta)
            except Exception as e:
                print(f"\n⚠️ Groq Whisper falló ({e}). Activando STT simulado...")
        
        # Fallback Offline (si es una ruta mp3, usamos el caso 1 simulado por defecto)
        id_simulado = id_o_ruta if not id_o_ruta.endswith(".mp3") else "audio_soporte_01"
        return STTOfflineSimulator.transcribir_audio(id_simulado).get("transcripcion_cruda", "")

    def _obtener_payload_llm(self, transcripcion: str, intento: int, error_previo: str | None) -> dict:
        if self.usar_live and self.settings.gemini_api_key:
            try:
                gemini = ModeloGeminiResumenLive(self.settings.gemini_api_key, self.settings.gemini_model)
                return gemini.resumir(transcripcion, error_previo)
            except Exception as e:
                print(f"\n⚠️ Gemini saturado o sin cuota. Cayendo a LLM simulado offline...")
        
        # Simulación Offline
        if intento == 1:
            return {
                "id_llamada": "CALL-OFF-1", 
                "motivo_principal_llamada": "Solicitud genérica", 
                "entidades_afectadas": [], 
                "resumen_para_tts": "El cliente pidió que lo llamen de vuelta mañana.", 
                "requiere_escalamiento": False
            }
        return {
            "id_llamada": "CALL-OFF-1", 
            "motivo_principal_llamada": "Problema de acceso a cuenta", 
            "entidades_afectadas": ["cuenta"], 
            "resumen_para_tts": "El cliente reporta problemas técnicos para acceder a los detalles de su cuenta.", 
            "requiere_escalamiento": True
        }

    def procesar_llamada(self, id_o_ruta: str) -> dict:
        transcripcion_cruda = self._obtener_transcripcion(id_o_ruta)
        
        errores = []
        error_actual = None
        
        for intento in range(1, self.max_intentos + 1):
            payload = self._obtener_payload_llm(transcripcion_cruda, intento, error_actual)
            try:
                resultado_validado = ResumenLlamadaSoporte.model_validate(payload)
                return {
                    "estado": "EXITO",
                    "intentos": intento,
                    "transcripcion_obtenida": transcripcion_cruda,
                    "errores_atrapados": errores,
                    "datos": resultado_validado
                }
            except ValidationError as err:
                msg = err.errors()[0]["msg"]
                errores.append(f"Intento {intento}: {msg}")
                error_actual = msg
                
        return {
            "estado": "FALLO", 
            "intentos": self.max_intentos, 
            "transcripcion_obtenida": transcripcion_cruda, 
            "errores_atrapados": errores, 
            "datos": None
        }


class ModeloGroqWhisperLive:
    def __init__(self, api_key: str):
        from groq import Groq
        self.client = Groq(api_key=api_key)

    def transcribir(self, ruta_audio: str) -> str:
        with open(ruta_audio, "rb") as f:
            transcripcion = self.client.audio.transcriptions.create(
                file=(ruta_audio.split('/')[-1], f.read()),
                model="whisper-large-v3",
                language="es",
                response_format="text"
            )
        return transcripcion


class ModeloGeminiResumenLive:
    def __init__(self, api_key: str, model_name: str):
        from google import genai
        from google.genai import types
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.types = types

    def resumir(self, transcripcion: str, error_previo: str | None = None) -> dict:
        prompt_sistema = "Eres un agente de soporte. Extrae los datos de la transcripción y genera un resumen."
        prompt_usuario = f"Transcripción de la llamada: '{transcripcion}'"
        
        if error_previo:
            prompt_usuario += f"\n\nATENCIÓN: Tu intento anterior falló con este error de validación:\n{error_previo}\nRe-analiza y corrige."

        configuracion = self.types.GenerateContentConfig(
            system_instruction=prompt_sistema,
            response_mime_type="application/json",
            response_schema=ResumenLlamadaSoporte,
            temperature=0.0,
        )

        respuesta = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt_usuario,
            config=configuracion,
        )
        return json.loads(respuesta.text)

class ModeloGroqResumenLive:
    def __init__(self, api_key: str):
        from groq import Groq
        self.client = Groq(api_key=api_key)

    def resumir(self, transcripcion: str, error_previo: str | None = None) -> dict:
        from .schemas import ResumenLlamadaSoporte
        esquema_json = json.dumps(ResumenLlamadaSoporte.model_json_schema())
        
        prompt_sistema = (
            "Eres un agente de soporte técnico bancario. "
            "Extrae los datos de la transcripción y responde ESTRICTAMENTE en formato JSON "
            f"cumpliendo con este esquema: {esquema_json}"
        )
        prompt_usuario = f"Transcripción de la llamada: '{transcripcion}'"
        
        if error_previo:
            prompt_usuario += f"\n\nATENCIÓN: Tu intento anterior falló con este error de validación de Pydantic:\n{error_previo}\nCorrige el JSON."

        respuesta = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario}
            ],
            model="allam-2-7b",
            response_format={"type": "json_object"},
            temperature=0.0
        )
        return json.loads(respuesta.choices[0].message.content)


class PipelineAudioSoporte:
    def __init__(self, max_intentos: int = 3, forzar_live: bool = False):
        self.max_intentos = max_intentos
        self.settings = get_settings()
        self.usar_live = forzar_live or self.settings.is_live

    def _obtener_transcripcion(self, id_o_ruta: str) -> str:
        if self.usar_live and self.settings.groq_api_key:
            whisper = ModeloGroqWhisperLive(self.settings.groq_api_key)
            return whisper.transcribir(id_o_ruta)
        # Fallback Offline
        return STTOfflineSimulator.transcribir_audio(id_o_ruta).get("transcripcion_cruda", "")

    def _obtener_payload_llm(self, transcripcion: str, intento: int, error_previo: str | None) -> dict:
        if self.usar_live:
            if self.settings.gemini_api_key:
                try:
                    gemini = ModeloGeminiResumenLive(self.settings.gemini_api_key, self.settings.gemini_model)
                    return gemini.resumir(transcripcion, error_previo)
                except Exception as e:
                    print(f"\n⚠️ Gemini falló (Error 503). Activando PLAN B: Groq...")

            if self.settings.groq_api_key:
                try:
                    groq_llm = ModeloGroqResumenLive(self.settings.groq_api_key)
                    return groq_llm.resumir(transcripcion, error_previo)
                except Exception as e:
                    print(f"\n⚠️ Groq LLM también falló ({e}). Activando PLAN C: Simulación Offline...")

        # 🔴 PLAN C: Simulación Offline
        if intento == 1:
            return {
                "id_llamada": "CALL-OFF-1", 
                "motivo_principal_llamada": "Solicitud genérica", 
                "entidades_afectadas": [], 
                "resumen_para_tts": "El cliente pidió que lo llamen de vuelta mañana.", 
                "requiere_escalamiento": False
            }
        return {
            "id_llamada": "CALL-OFF-1", 
            "motivo_principal_llamada": "Problema de acceso a cuenta", 
            "entidades_afectadas": ["cuenta"], 
            "resumen_para_tts": "Hola, veo que tienes problemas para acceder a tu cuenta. Un especialista te contactará de inmediato.", 
            "requiere_escalamiento": True
        }

    def procesar_llamada(self, id_o_ruta: str) -> dict:
        transcripcion_cruda = self._obtener_transcripcion(id_o_ruta)
        
        errores = []
        error_actual = None
        
        for intento in range(1, self.max_intentos + 1):
            payload = self._obtener_payload_llm(transcripcion_cruda, intento, error_actual)
            try:
                resultado_validado = ResumenLlamadaSoporte.model_validate(payload)
                return {
                    "estado": "EXITO",
                    "intentos": intento,
                    "transcripcion_obtenida": transcripcion_cruda,
                    "errores_atrapados": errores,
                    "datos": resultado_validado
                }
            except ValidationError as err:
                msg = err.errors()[0]["msg"]
                errores.append(f"Intento {intento}: {msg}")
                error_actual = msg
                
        return {"estado": "FALLO", "intentos": self.max_intentos, "transcripcion_obtenida": transcripcion_cruda, "errores_atrapados": errores, "datos": None}



# 🟢 -------------------------------------------------------------------------
# 🟢 MÓDULO INTERACTIVO DE VOZ EN VIVO (Micrófono -> Groq -> Gemini -> edge-tts)
# 🟢 -------------------------------------------------------------------------
import asyncio
import queue
import numpy as np
from pathlib import Path
import sounddevice as sd
from scipy.io.wavfile import write
import edge_tts
from .config import get_settings

class GrabadorYAsistenteVozLive:
    def __init__(self):
        self.settings = get_settings()

    def grabar_microfono_libre(self, ruta_salida: str = "assets/audios/input_mic.wav", fs: int = 44100):
        cola_audio = queue.Queue()

        # Función que recolecta el audio en pedacitos mientras hablas
        def callback(indata, frames, time, status):
            cola_audio.put(indata.copy())

        print("\n🎙️ ¡GRABANDO! Habla libremente el tiempo que necesites...")
        print("🛑 ATENCIÓN: Mira la parte de ARRIBA de tu VS Code. Presiona ENTER en la caja de texto para detener.")

        # Iniciamos el stream de grabación en segundo plano
        with sd.InputStream(samplerate=fs, channels=1, dtype='int16', callback=callback):
            input("Presiona ENTER aquí para detener la grabación...")

        # Vaciamos la cola y unimos todos los pedazos de audio
        datos_audio = []
        while not cola_audio.empty():
            datos_audio.append(cola_audio.get())
        
        audio_final = np.concatenate(datos_audio, axis=0)

        Path(ruta_salida).parent.mkdir(parents=True, exist_ok=True)
        write(ruta_salida, fs, audio_final)
        print(f"✅ Grabación detenida. Audio guardado en: {ruta_salida}")
        return ruta_salida

    async def sintetizar_voz_neuronal(self, texto: str, ruta_mp3: str = "assets/audios/output_respuesta.mp3") -> str:
        Path(ruta_mp3).parent.mkdir(parents=True, exist_ok=True)
        
        try:
            voz_seleccionada = "es-MX-DaliaNeural" 
            communicate = edge_tts.Communicate(texto, voz_seleccionada)
            await communicate.save(ruta_mp3)
            print(f"🔊 Audio de respuesta generado (Voz Neuronal): {ruta_mp3}")
            return ruta_mp3
            
        except Exception as e:
            print(f"\n⚠️ Microsoft Edge TTS falló ({e}). Activando voz de respaldo (gTTS)...")
            from gtts import gTTS
            tts = gTTS(text=texto, lang='es', tld='es')
            tts.save(ruta_mp3)
            print(f"🔊 Audio de respuesta generado (Voz Estándar): {ruta_mp3}")
            return ruta_mp3