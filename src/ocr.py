"""Offline OCR using the installed Tesseract engine."""
from io import BytesIO
from PIL import Image, ImageOps, ImageEnhance, UnidentifiedImageError
import pytesseract

MAX_BYTES = 12 * 1024 * 1024
MAX_PIXELS = 20_000_000
Image.MAX_IMAGE_PIXELS = MAX_PIXELS


def extract_text(data: bytes) -> str:
    if not data or len(data) > MAX_BYTES:
        raise ValueError('Image must be nonempty and at most 12 MB.')
    try:
        image = Image.open(BytesIO(data))
        if image.format not in ('PNG', 'JPEG', 'WEBP'):
            raise ValueError('Upload a valid PNG, JPG, or WEBP image.')
        if image.width * image.height > MAX_PIXELS:
            raise ValueError('Image exceeds the 20-megapixel limit.')
        image.load()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise ValueError('Upload a valid PNG, JPG, or WEBP image.') from exc
    if image.width * image.height > MAX_PIXELS:
        raise ValueError('Image exceeds the 20-megapixel limit.')
    gray = ImageOps.grayscale(ImageOps.exif_transpose(image))
    gray = ImageOps.autocontrast(gray)
    gray = ImageEnhance.Contrast(gray).enhance(1.4)
    try:
        return pytesseract.image_to_string(gray, config='--psm 11', timeout=8)
    except RuntimeError as exc:
        raise ValueError('OCR timed out; use a smaller or clearer image.') from exc
    except pytesseract.TesseractNotFoundError as exc:
        raise RuntimeError('Tesseract OCR is not installed on the server.') from exc
