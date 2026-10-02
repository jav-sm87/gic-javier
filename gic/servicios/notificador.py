"""Envío de emails de bienvenida.

Con las variables SMTP_HOST, SMTP_PORT, SMTP_USER y SMTP_PASSWORD
configuradas (por ejemplo una contraseña de aplicación de Gmail) envía
el correo real. Sin ellas trabaja en modo simulación: guarda el correo
en data/bandeja_salida/ para poder revisarlo.
"""
import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

from ..excepciones import ServicioExternoError
from ..modelos import Cliente
from ..registro import obtener_logger

log = obtener_logger("notificaciones")


class Notificador:
    def __init__(self, host=None, puerto=None, usuario=None, clave=None,
                 carpeta_simulacion="data/bandeja_salida"):
        self.host = host or os.getenv("SMTP_HOST")
        self.puerto = int(puerto or os.getenv("SMTP_PORT", 587))
        self.usuario = usuario or os.getenv("SMTP_USER")
        self.clave = clave or os.getenv("SMTP_PASSWORD")
        self.carpeta_simulacion = Path(carpeta_simulacion)

    @property
    def modo_real(self) -> bool:
        return bool(self.host and self.usuario and self.clave)

    def construir_mensaje(self, cliente: Cliente) -> EmailMessage:
        msg = EmailMessage()
        msg["Subject"] = "Bienvenido/a a SolutionTech"
        msg["From"] = self.usuario or "no-reply@solutiontech.cl"
        msg["To"] = cliente.email
        msg.set_content(cliente.mensaje_bienvenida())  # polimorfismo: texto según tipo
        return msg

    def enviar_bienvenida(self, cliente: Cliente) -> str:
        msg = self.construir_mensaje(cliente)
        if not self.modo_real:
            self.carpeta_simulacion.mkdir(parents=True, exist_ok=True)
            nombre = f"{datetime.now():%Y%m%d_%H%M%S}_{cliente.rut}.eml"
            (self.carpeta_simulacion / nombre).write_bytes(bytes(msg))
            log.info("Bienvenida simulada para %s (%s)", cliente.email, nombre)
            return "simulado"
        try:
            with smtplib.SMTP(self.host, self.puerto, timeout=10) as smtp:
                smtp.starttls()
                smtp.login(self.usuario, self.clave)
                smtp.send_message(msg)
        except (smtplib.SMTPException, OSError) as error:
            log.error("Fallo SMTP al enviar a %s: %s", cliente.email, error)
            raise ServicioExternoError("No se pudo enviar el email de bienvenida") from error
        log.info("Bienvenida enviada a %s", cliente.email)
        return "enviado"
