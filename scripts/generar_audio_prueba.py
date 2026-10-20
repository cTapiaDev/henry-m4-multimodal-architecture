from pathlib import Path
from gtts import gTTS

def crear_audio_prueba():
    carpeta_salida = Path("assets/audios")
    carpeta_salida.mkdir(parents=True, exist_ok=True)
    ruta_audio = carpeta_salida / "llamada_01.mp3"

    texto_a_hablar = "El cliente dijo que tenía probrema para a ceder a los detayes de su cuenta. Por favor yamalo mañana."
    
    tts = gTTS(text=texto_a_hablar, lang='es', tld='es')
    tts.save(ruta_audio)
    
    print(f"✅ Audio real de prueba generado en: {ruta_audio}")

if __name__ == "__main__":
    crear_audio_prueba()