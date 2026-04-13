from paddleocr import PaddleOCR
from PIL import Image
import logging

logger = logging.getLogger(__name__)

# Initialize once — Russian + English, angle detection on
_ocr = None


def get_ocr():
    global _ocr
    if _ocr is None:
        _ocr = PaddleOCR(
            use_angle_cls=True,
            lang="ru",
            use_gpu=False,
            show_log=False,
        )
    return _ocr


def recognize_image(image_path: str) -> dict:
    """
    Run OCR on an image file.
    Returns: {"text": str, "confidence": float, "lines": list}
    """
    try:
        ocr = get_ocr()
        result = ocr.ocr(image_path, cls=True)

        if not result or not result[0]:
            return {"text": "", "confidence": 0.0, "lines": []}

        lines = []
        total_conf = 0.0
        texts = []

        for line in result[0]:
            bbox, (text, conf) = line
            lines.append({"text": text, "confidence": conf, "bbox": bbox})
            texts.append(text)
            total_conf += conf

        avg_confidence = total_conf / len(lines) if lines else 0.0
        full_text = "\n".join(texts)

        return {
            "text": full_text,
            "confidence": round(avg_confidence, 4),
            "lines": lines,
        }
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        return {"text": "", "confidence": 0.0, "lines": [], "error": str(e)}
