"""Verificación de correo mediante enlaces firmados y API transaccional de Brevo."""
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.core import signing
from django.core.mail import send_mail
from django.urls import reverse

SALT = "principal.verificacion.email.v1"
MAX_AGE = 60 * 60 * 24  # 24 horas


def crear_token(usuario):
    return signing.dumps({"uid": usuario.pk, "email": usuario.email}, salt=SALT)


def validar_token(token):
    return signing.loads(token, salt=SALT, max_age=MAX_AGE)


def enviar_verificacion(usuario, request):
    api_key = getattr(settings, "BREVO_API_KEY", "")
    remitente = getattr(settings, "BREVO_SENDER_EMAIL", "")
    if not api_key or not remitente:
        if settings.DEBUG:
            enlace = request.build_absolute_uri(reverse("verificar_correo", args=[crear_token(usuario)]))
            send_mail(
                subject="Verifica tu correo - Pre-ICFES",
                message=(
                    f"Hola {usuario.username}. Abre este enlace para verificar tu correo "
                    f"(válido 24 horas): {enlace}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[usuario.email],
            )
            return
        raise RuntimeError("Faltan BREVO_API_KEY o BREVO_SENDER_EMAIL")
    enlace = request.build_absolute_uri(reverse("verificar_correo", args=[crear_token(usuario)]))
    payload = {
        "sender": {"email": remitente, "name": getattr(settings, "BREVO_SENDER_NAME", "Pre-ICFES")},
        "to": [{"email": usuario.email}],
        "subject": "Verifica tu correo - Pre-ICFES",
        "textContent": f"Hola {usuario.username}. Verifica tu correo desde este enlace (válido 24 horas): {enlace}",
    }
    solicitud = Request(
        "https://api.brevo.com/v3/smtp/email",
        data=json.dumps(payload).encode("utf-8"),
        headers={"api-key": api_key, "Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urlopen(solicitud, timeout=10) as respuesta:
        if respuesta.status not in (200, 201, 202):
            raise RuntimeError("Brevo no aceptó el mensaje")
