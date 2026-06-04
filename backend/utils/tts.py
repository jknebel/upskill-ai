import os
import base64
import logging

logger = logging.getLogger(__name__)

def generate_podcast_audio(script: list) -> str:
    """
    Génère un fichier audio (base64) à partir du script du podcast
    en utilisant Google Cloud Text-to-Speech avec 2 voix distinctes.
    
    Retourne la chaîne en base64 de l'audio concaténé, ou None en cas d'erreur.
    """
    try:
        from google.cloud import texttospeech
    except ImportError:
        logger.warning("google-cloud-texttospeech n'est pas installé.")
        return None

    try:
        # Vérifier si on peut instancier le client (besoin des credentials GCP)
        client = texttospeech.TextToSpeechClient()
    except Exception as e:
        logger.warning(f"Impossible d'initialiser le client GCP TTS (vérifiez vos credentials) : {e}")
        return None

    # Configuration des voix pour les deux hôtes
    # Hôte A : Voix féminine Neural2
    voice_a = texttospeech.VoiceSelectionParams(
        language_code="fr-FR",
        name="fr-FR-Neural2-A"
    )
    # Hôte B : Voix masculine Neural2
    voice_b = texttospeech.VoiceSelectionParams(
        language_code="fr-FR",
        name="fr-FR-Neural2-D"
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    combined_audio_content = b""

    try:
        for line in script:
            speaker = line.get("speaker", "Hôte A")
            text = line.get("text", "")

            if not text:
                continue

            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            if speaker == "Hôte A":
                voice = voice_a
            else:
                voice = voice_b

            response = client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )
            
            combined_audio_content += response.audio_content

        if not combined_audio_content:
            return None

        # Convertir en base64 pour l'envoyer au frontend facilement
        audio_base64 = base64.b64encode(combined_audio_content).decode('utf-8')
        return f"data:audio/mp3;base64,{audio_base64}"
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération TTS : {e}")
        return None
