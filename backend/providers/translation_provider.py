"""
ArogyaGrid — Translation Provider
====================================
Interface for multilingual translation.
- USE_REAL_TRANSLATE=true: calls Cloud Translation API
  STUB → real implementation:
         from google.cloud import translate_v2 as translate
         client = translate.Client()
         result = client.translate(text, target_language=target_lang)
         return result["translatedText"]
- USE_REAL_TRANSLATE=false (default): Uses Gemini for translation
  (real when GOOGLE_API_KEY is set), or returns the original text
  with a [STUB] label if Gemini is also unavailable.
"""
from typing import Optional


LANGUAGE_NAMES = {
    "hi": "Hindi", "bn": "Bengali", "ta": "Tamil", "te": "Telugu",
    "mr": "Marathi", "gu": "Gujarati", "kn": "Kannada", "ml": "Malayalam",
    "pa": "Punjabi", "or": "Odia", "en": "English",
}


def translate_text(text: str, target_lang: str = "hi", source_lang: str = "en") -> str:
    """
    Translate text to target_lang.

    STUB → Cloud Translation API when USE_REAL_TRANSLATE=true.
    Falls back to Gemini translation (real if API key available).
    """
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    import config

    if target_lang == "en" or target_lang == source_lang:
        return text

    if config.USE_REAL_TRANSLATE:
        # STUB → Cloud Translation API
        # from google.cloud import translate_v2 as translate
        # client = translate.Client()
        # result = client.translate(text, target_language=target_lang)
        # return result["translatedText"]
        raise NotImplementedError("Cloud Translation not wired. Set USE_REAL_TRANSLATE=false.")

    # Use Gemini for translation (real if API key set)
    from providers.gemini_provider import generate_text
    lang_name = LANGUAGE_NAMES.get(target_lang, target_lang)
    prompt = (
        f"Translate the following health information text to {lang_name}. "
        f"Keep it simple and accessible for a rural patient with low health literacy. "
        f"Preserve any medical terms in brackets after the translation.\n\n"
        f"Text to translate:\n{text}"
    )
    return generate_text(prompt, temperature=0.2)
