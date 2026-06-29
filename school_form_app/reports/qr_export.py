"""
QR code export utilities.

This module creates a QR code image from a Google Form responder URL.

The QR code is saved as a PNG file, for example:

    qr_codes/qr_code_<form_id>.png
"""

from pathlib import Path

import qrcode


def create_qr_code(
    url: str,
    output_path: str,
) -> str:
    """
    Create a QR code image from a URL.

    Args:
        url:
            The URL that should be encoded into the QR code.

        output_path:
            Path where the PNG file should be saved.

    Returns:
        The final output path as a string.
    """

    if not url:
        raise ValueError("URL is empty. Cannot create QR code.")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )

    qr.add_data(url)
    qr.make(fit=True)

    image = qr.make_image(
        fill_color="black",
        back_color="white",
    )

    image.save(output)

    return str(output)


def get_qr_code_output_path(form_id: str) -> Path:
    """
    Build a default QR code path for a Google Form.

    Example:

        qr_codes/qr_code_abc123.png
    """

    qr_codes_dir = Path("qr_codes")
    qr_codes_dir.mkdir(exist_ok=True)

    return qr_codes_dir / f"qr_code_{form_id}.png"