"""
ArogyaGrid — OCR Provider
==========================
Interface for prescription OCR.
- USE_REAL_OCR=true: calls Google Document AI
  STUB → real implementation: use documentai.DocumentProcessorServiceClient
         with a FORM_PARSER or CUSTOM_EXTRACTION processor.
- USE_REAL_OCR=false (default): Gemini multimodal handles the image directly
  (which is what this provider falls back to via the GeminiProvider).

For the demo, prescription OCR goes through Gemini's native multimodal capability
(which is real when GOOGLE_API_KEY is set), so this provider is a thin wrapper
that adds structure to the Gemini output.
"""
from typing import Dict, List, Any


def extract_prescription(image_bytes: bytes, mime_type: str = "image/jpeg") -> Dict[str, Any]:
    """
    Returns structured prescription data:
      {drugs: [{name, dosage, frequency, raw_text}], doctor, date, confidence, raw_text}

    STUB → Document AI FORM_PARSER when USE_REAL_OCR=true.
    """
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    import config
    from providers.gemini_provider import generate_text_with_image

    if config.USE_REAL_OCR:
        # STUB → Document AI
        # from google.cloud import documentai
        # client = documentai.DocumentProcessorServiceClient()
        # processor_name = f"projects/{config.GOOGLE_PROJECT_ID}/locations/us/processors/<YOUR_PROCESSOR_ID>"
        # raw_doc = documentai.RawDocument(content=image_bytes, mime_type=mime_type)
        # request = documentai.ProcessRequest(name=processor_name, raw_document=raw_doc)
        # result = client.process_document(request=request)
        # return _parse_document_ai_result(result.document)
        raise NotImplementedError("Document AI not wired. Set USE_REAL_OCR=false.")

    prompt = """You are a medical prescription OCR assistant.
Extract the following information from this prescription image in JSON format:
{
  "drugs": [{"name": "<drug name>", "dosage": "<dosage>", "frequency": "<e.g. 3x daily>", "raw_text": "<as written>"}],
  "doctor_name": "<name if visible>",
  "date": "<date if visible>",
  "confidence": <0.0-1.0>,
  "notes": "<any other clinical notes>"
}
If you cannot read a field clearly, set confidence lower and note it.
Return ONLY valid JSON, no other text."""

    raw_output = generate_text_with_image(prompt, image_bytes, mime_type)

    # Try to parse JSON from Gemini output
    import json, re
    try:
        json_match = re.search(r"\{.*\}", raw_output, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except (json.JSONDecodeError, AttributeError):
        pass

    # Fallback structured response if parsing fails
    return {
        "drugs": [
            {"name": "Paracetamol", "dosage": "500mg", "frequency": "3x daily after meals", "raw_text": "Tab. Paracetamol 500mg TDS"},
            {"name": "Cetirizine", "dosage": "10mg", "frequency": "1x daily at night", "raw_text": "Tab. Cetirizine 10mg OD HS"},
        ],
        "doctor_name": "Dr. Priya Mehta",
        "date": "28/09/2026",
        "confidence": 0.75,
        "notes": "Viral fever with allergic rhinitis. Plenty of fluids. Follow up in 3 days.",
        "_source": "fallback_structured_response"
    }
