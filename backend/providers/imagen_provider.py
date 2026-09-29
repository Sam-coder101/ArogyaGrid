"""
ArogyaGrid — Imagen Provider
==============================
Interface for awareness poster image generation.
- USE_REAL_IMAGEN=true: calls Imagen 3 via Vertex AI
  STUB → real implementation:
         from vertexai.preview.vision_models import ImageGenerationModel
         model = ImageGenerationModel.from_pretrained("imagegeneration@006")
         images = model.generate_images(prompt=..., number_of_images=1)
         images[0].save(location=output_path)
- USE_REAL_IMAGEN=false (default): generates a placeholder PNG with
  the poster text rendered using Pillow — clearly labelled as a stub.

The poster content (facts, prevention steps) comes from pre-approved
health-authority fact templates, not free Gemini generation — this is
the guardrail described in agent.md §6.
"""
import io
import base64
from typing import Optional, Dict


def generate_poster(
    prompt: str,
    output_path: Optional[str] = None,
) -> dict:
    """
    Returns {image_base64, image_path, stub_mode} dict.

    STUB → Imagen 3 (Vertex AI) when USE_REAL_IMAGEN=true.
    """
    import sys, pathlib, os
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    import config

    if config.USE_REAL_IMAGEN:
        # STUB → Imagen 3
        # import vertexai
        # from vertexai.preview.vision_models import ImageGenerationModel
        # vertexai.init(project=config.GOOGLE_PROJECT_ID, location=config.GOOGLE_REGION)
        # model = ImageGenerationModel.from_pretrained("imagegeneration@006")
        # images = model.generate_images(prompt=prompt, number_of_images=1, aspect_ratio="9:16")
        # buf = io.BytesIO(); images[0]._pil_image.save(buf, format="PNG")
        # return {"image_base64": base64.b64encode(buf.getvalue()).decode(), "stub_mode": False}
        raise NotImplementedError("Imagen 3 not wired. Set USE_REAL_IMAGEN=false.")

    # STUB: render a poster using Pillow
    try:
        from PIL import Image, ImageDraw, ImageFont
        import textwrap

        width, height = 800, 1200
        bg_color = (20, 60, 100)        # deep blue
        accent   = (255, 200, 0)        # gold
        white    = (255, 255, 255)

        img  = Image.new("RGB", (width, height), bg_color)
        draw = ImageDraw.Draw(img)

        # Header bar
        draw.rectangle([0, 0, width, 120], fill=(10, 40, 80))
        draw.text((40, 20), "ArogyaGrid Health Alert", fill=accent)
        draw.text((40, 65), "Ministry of Health & Family Welfare", fill=(200, 200, 200))

        # Stub watermark band
        draw.rectangle([0, 120, width, 160], fill=(180, 0, 0))
        draw.text((40, 132), "[STUB] Real poster: Imagen 3 via Vertex AI  |  Set USE_REAL_IMAGEN=true", fill=white)

        # Poster body — wrapped prompt text
        y = 185
        for line in textwrap.wrap(prompt, width=55):
            draw.text((40, y), line, fill=white)
            y += 32
            if y > height - 200:
                break

        # Footer
        draw.rectangle([0, height - 120, width, height], fill=(10, 40, 80))
        draw.text((40, height - 100), "For health information, contact your nearest PHC.", fill=(200, 200, 200))
        draw.text((40, height - 60), "Powered by ArogyaGrid  |  GDG India Hackathon 2026", fill=accent)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        img_bytes = buf.getvalue()

        # Save to file if path provided
        if output_path:
            pathlib.Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(img_bytes)

        return {
            "image_base64": base64.b64encode(img_bytes).decode(),
            "image_path": output_path,
            "stub_mode": True,
        }
    except ImportError:
        return {
            "image_base64": "",
            "image_path": None,
            "stub_mode": True,
            "error": "Pillow not installed — run pip install Pillow",
        }
