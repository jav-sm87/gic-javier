"""Integración con API externa de validación.

1. RUT: se verifica el dígito verificador (módulo 11) localmente.
2. Email: se consulta la API pública Disify (https://disify.com), que
   indica si el dominio existe, si tiene servidor de correo (MX) y si es
   un correo desechable. Si la API no responde, el sistema no se cae:
   registra la advertencia y continúa (degradación controlada).
"""
import requests

from ..excepciones import EmailInvalidoError, ServicioExternoError
from ..registro import obtener_logger
from ..validaciones import validar_rut

log = obtener_logger("api")


class ValidadorIdentidad:
    URL_EMAIL = "https://www.disify.com/api/email/{email}"

    def __init__(self, habilitado: bool = True, timeout: float = 4.0, sesion=None):
        self.habilitado = habilitado
        self.timeout = timeout
        self.sesion = sesion or requests.Session()

    def consultar_email(self, email: str) -> dict:
        """Llama a la API y devuelve su respuesta como diccionario."""
        try:
            resp = self.sesion.get(self.URL_EMAIL.format(email=email), timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError) as error:
            raise ServicioExternoError(f"API de validación no disponible: {error}") from error

    def validar(self, rut: str, email: str) -> list[str]:
        """Valida la identidad del cliente. Lanza excepción si hay un rechazo
        definitivo y devuelve una lista de advertencias si algo no se pudo verificar."""
        validar_rut(rut)
        advertencias = []
        if not self.habilitado:
            return advertencias
        try:
            datos = self.consultar_email(email)
        except ServicioExternoError as error:
            log.warning("%s. Se omite la validación en línea de %s", error.mensaje, email)
            advertencias.append("No se pudo verificar el email en línea; se registró igual.")
            return advertencias
        if datos.get("format") is False:
            raise EmailInvalidoError("La API indica que el email tiene un formato inválido")
        if datos.get("disposable"):
            raise EmailInvalidoError("No se aceptan correos desechables")
        if datos.get("dns") is False:
            raise EmailInvalidoError("El dominio del email no existe o no recibe correos")
        log.info("Email %s validado en línea", email)
        return advertencias
