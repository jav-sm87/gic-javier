"""Validadores reutilizables. Cada función normaliza el dato o lanza una excepción."""
import re

from .excepciones import (
    EmailInvalidoError,
    RutInvalidoError,
    TelefonoInvalidoError,
    ValidacionError,
)

_PATRON_EMAIL = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def validar_texto(valor, campo: str, minimo: int = 2, maximo: int = 80) -> str:
    if valor is None or not str(valor).strip():
        raise ValidacionError(f"El campo {campo} es obligatorio", campo=campo)
    valor = " ".join(str(valor).split())
    if not minimo <= len(valor) <= maximo:
        raise ValidacionError(
            f"El campo {campo} debe tener entre {minimo} y {maximo} caracteres", campo=campo
        )
    return valor


def validar_email(email: str) -> str:
    email = (email or "").strip().lower()
    if not _PATRON_EMAIL.match(email) or ".." in email:
        raise EmailInvalidoError()
    return email


def validar_telefono(telefono: str) -> str:
    """Acepta celulares chilenos con o sin +56 y espacios. Devuelve +569XXXXXXXX."""
    digitos = re.sub(r"[\s\-()]", "", telefono or "")
    if digitos.startswith("+56"):
        digitos = digitos[3:]
    elif digitos.startswith("56") and len(digitos) == 11:
        digitos = digitos[2:]
    if not re.fullmatch(r"9\d{8}", digitos):
        raise TelefonoInvalidoError()
    return f"+56{digitos}"


def calcular_dv(cuerpo: int) -> str:
    """Dígito verificador del RUT con el algoritmo módulo 11."""
    suma, factor = 0, 2
    for digito in reversed(str(cuerpo)):
        suma += int(digito) * factor
        factor = 2 if factor == 7 else factor + 1
    resto = 11 - (suma % 11)
    return {11: "0", 10: "K"}.get(resto, str(resto))


def validar_rut(rut: str) -> str:
    """Valida un RUT chileno y lo devuelve normalizado como 12345678-K."""
    limpio = re.sub(r"[.\s]", "", (rut or "")).upper()
    coincidencia = re.fullmatch(r"(\d{7,8})-?([\dK])", limpio)
    if not coincidencia:
        raise RutInvalidoError("El RUT debe tener el formato 12.345.678-9")
    cuerpo, dv = coincidencia.groups()
    if calcular_dv(int(cuerpo)) != dv:
        raise RutInvalidoError("El dígito verificador del RUT no coincide")
    return f"{int(cuerpo)}-{dv}"
