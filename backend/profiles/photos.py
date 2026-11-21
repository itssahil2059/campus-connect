"""Profile photo pipeline: check the upload, clean it, shrink it, save it.

Every photo goes through the same steps, whatever the student uploads:

  1. Size check (<= 10 MB) before Pillow touches the file.
  2. Open it with Pillow: proves it's a real JPEG/PNG/WebP/HEIC image, not
     just a file named .jpg. Pillow's decompression-bomb limit stays on, so a
     tiny file that expands to billions of pixels is refused.
  3. Rotate it upright (phones store "rotate me" in EXIF instead of rotating
     the pixels), then build a brand-new RGB image with no metadata at all:
     no EXIF, no GPS location, no camera details.
  4. Main photo: longest side at most 1080 px, JPEG, quality lowered step by
     step until it's ~300 KB (always under 1 MB).
  5. Thumbnail: 200x200 center crop, JPEG (~10-20 KB), for lists and cards.

Files are saved through Django's default storage with random UUID names, so
moving to S3 later is a settings change (django-storages), not a code change.
"""

import io
import uuid
import warnings

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from PIL import Image, ImageOps, UnidentifiedImageError

try:  # HEIC/HEIF (iPhone photos). Optional so a missing wheel can't break the app.
    from pillow_heif import register_heif_opener

    register_heif_opener()
    HEIC_SUPPORTED = True
except ImportError:  # pragma: no cover
    HEIC_SUPPORTED = False

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
MAIN_MAX_SIDE = 1080
MAIN_TARGET_BYTES = 300 * 1024  # aim for ~200-300 KB
MAIN_MAX_BYTES = 1024 * 1024  # hard limit: always under 1 MB
MAIN_QUALITIES = (85, 80, 75, 70, 65, 60, 55, 50, 45, 40)
THUMB_SIZE = 200
THUMB_QUALITY = 75

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"} | ({"HEIF"} if HEIC_SUPPORTED else set())
WRONG_TYPE = (
    "Please upload a JPG, PNG, WebP or HEIC photo."
    if HEIC_SUPPORTED
    else "Please upload a JPG or PNG."
)
TOO_LARGE = "That photo is too large. The maximum size is 10 MB."
TOO_MANY_PIXELS = "That image is too large to process. Please upload a smaller photo."

PHOTO_DIR = "profile_photos"


class PhotoError(ValueError):
    """The upload isn't an acceptable photo. str(error) is safe to show users."""


def _open_image(upload):
    """Open and fully decode the upload, or raise PhotoError."""
    if upload.size > MAX_UPLOAD_BYTES:
        raise PhotoError(TOO_LARGE)
    try:
        # Treat Pillow's "this might be a decompression bomb" warning as an
        # error too (it otherwise only raises at 2x the limit).
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            upload.seek(0)
            image = Image.open(upload)
            if image.format not in ALLOWED_FORMATS:
                raise PhotoError(WRONG_TYPE)
            image.load()  # decode the pixels now: catches truncated/corrupt files
    except PhotoError:
        raise
    except (Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise PhotoError(TOO_MANY_PIXELS)
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError):
        # Not an image at all (e.g. a PDF renamed .jpg), or a broken one.
        raise PhotoError(WRONG_TYPE)
    return image


def _clean_rgb(image):
    """Upright, RGB, and with every bit of metadata dropped."""
    image = ImageOps.exif_transpose(image)
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        # JPEG has no transparency: put see-through parts on white, not black.
        rgba = image.convert("RGBA")
        clean = Image.new("RGB", rgba.size, (255, 255, 255))
        clean.paste(rgba, mask=rgba.getchannel("A"))
    else:
        rgb = image.convert("RGB")
        # Copy only the pixels into a fresh image, so no EXIF/XMP/ICC/GPS
        # metadata can ride along into the saved file.
        clean = Image.new("RGB", rgb.size)
        clean.paste(rgb)
    return clean


def _jpeg_bytes(image, quality):
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=quality, optimize=True, progressive=True)
    return buffer.getvalue()


def _main_photo(image):
    image = image.copy()
    image.thumbnail((MAIN_MAX_SIDE, MAIN_MAX_SIDE), Image.Resampling.LANCZOS)
    # Lower the quality step by step until it's small enough.
    for quality in MAIN_QUALITIES:
        data = _jpeg_bytes(image, quality)
        if len(data) <= MAIN_TARGET_BYTES:
            return data
    # Still big (very detailed photo): shrink the pixels until under 1 MB.
    while len(data) > MAIN_MAX_BYTES:
        image = image.resize((image.width * 4 // 5, image.height * 4 // 5), Image.Resampling.LANCZOS)
        data = _jpeg_bytes(image, MAIN_QUALITIES[-1])
    return data


def _thumbnail(image):
    square = ImageOps.fit(image, (THUMB_SIZE, THUMB_SIZE), Image.Resampling.LANCZOS)
    return _jpeg_bytes(square, THUMB_QUALITY)


def process_photo(upload):
    """Validate an uploaded file and return (main_jpeg_bytes, thumb_jpeg_bytes)."""
    image = _clean_rgb(_open_image(upload))
    return _main_photo(image), _thumbnail(image)


def photo_files(upload):
    """process_photo(), wrapped as ContentFiles with fresh random names."""
    main, thumb = process_photo(upload)
    name = uuid.uuid4().hex  # never the student's name or the original filename
    return (
        ContentFile(main, name=f"{name}.jpg"),
        ContentFile(thumb, name=f"{name}_thumb.jpg"),
    )


def delete_files(*names):
    """Delete stored files by name, ignoring blanks and files already gone."""
    for name in names:
        if name:
            default_storage.delete(name)
