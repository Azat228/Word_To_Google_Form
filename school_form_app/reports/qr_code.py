from pathlib import Path

import qrcode


def create_qr_code(
    url: str,
    output_path: str,
) -> str:
    if not url:
        raise ValueError("URL is empty. Cannot create QR code.")

    qr = qrcode.QRCode(
        version=None,
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

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    image.save(output)

    return str(output)
def make_google_form_responder_url(form_id: str) -> str:
    form_id = form_id.strip()

    if not form_id:
        raise ValueError("Google Form ID is empty.")

    return f"https://docs.google.com/forms/d/{form_id}/viewform"