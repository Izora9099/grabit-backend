"""
Shared image upload utility.

Validates, converts, and renames every uploaded image to WebP before storage.
Call `process_image_upload(file)` in any serializer that accepts image/file uploads.
"""
import io
import uuid
from typing import Optional

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image

# Magic-byte signatures for accepted formats
_MAGIC = {
    b"\xff\xd8\xff": "JPEG",
    b"\x89PNG": "PNG",
    b"RIFF": "WEBP",  # RIFF????WEBP — checked further below
}
_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
_MAX_DIM = 1800  # longest side cap; reduces storage ~4–8× vs phone-native resolution


def _detect_format(data: bytes) -> Optional[str]:
    if data[:3] == b"\xff\xd8\xff":
        return "JPEG"
    if data[:4] == b"\x89PNG":
        return "PNG"
    # RIFF <4-byte size> WEBP
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "WEBP"
    return None


def process_image_upload(file) -> InMemoryUploadedFile:
    """
    Accepts a Django UploadedFile, validates it, converts to WebP, and
    returns a new InMemoryUploadedFile ready to be saved by any field.

    Raises ValidationError for files that are too large or not valid images.
    """
    if file.size > _MAX_BYTES:
        raise ValidationError("Image must be 5 MB or smaller before conversion.")

    header = file.read(12)
    file.seek(0)

    if _detect_format(header) is None:
        raise ValidationError(
            "Invalid image file. Only JPEG, PNG, and WebP are accepted."
        )

    try:
        img = Image.open(file)
        img.verify()  # catches corrupt / truncated files
        file.seek(0)
        img = Image.open(file)  # re-open after verify (verify exhausts the stream)
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA" if img.mode in ("RGBA", "LA", "P") else "RGB")
        if img.width > _MAX_DIM or img.height > _MAX_DIM:
            img.thumbnail((_MAX_DIM, _MAX_DIM), Image.LANCZOS)
    except Exception:
        raise ValidationError("Could not read the uploaded file as an image.")

    output = io.BytesIO()
    img.save(output, format="WEBP", quality=82, method=6)
    output.seek(0)

    filename = f"{uuid.uuid4().hex}.webp"
    return InMemoryUploadedFile(
        file=output,
        field_name=None,
        name=filename,
        content_type="image/webp",
        size=output.getbuffer().nbytes,
        charset=None,
    )
