"""Jerarquía de excepciones personalizadas del GIC.

Todas heredan de GICError, así la interfaz puede capturar cualquier
error del dominio con un solo except y mostrar un mensaje amigable.
"""


class GICError(Exception):
    """Error base del sistema."""

    def __init__(self, mensaje: str, campo: str | None = None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.campo = campo


class ValidacionError(GICError):
    """Un dato ingresado no cumple el formato esperado."""


class EmailInvalidoError(ValidacionError):
    def __init__(self, mensaje="El email no tiene un formato válido"):
        super().__init__(mensaje, campo="email")


class TelefonoInvalidoError(ValidacionError):
    def __init__(self, mensaje="El teléfono debe tener el formato +56 9 XXXX XXXX"):
        super().__init__(mensaje, campo="telefono")


class DireccionInvalidaError(ValidacionError):
    def __init__(self, mensaje="La dirección está incompleta"):
        super().__init__(mensaje, campo="direccion")


class RutInvalidoError(ValidacionError):
    def __init__(self, mensaje="El RUT no es válido"):
        super().__init__(mensaje, campo="rut")


class ClienteDuplicadoError(GICError):
    """Ya existe un cliente con el mismo RUT o email."""


class ClienteNoEncontradoError(GICError):
    """No existe el cliente solicitado."""


class PersistenciaError(GICError):
    """Falla al leer o escribir en la base de datos o en archivos."""


class ServicioExternoError(GICError):
    """Falla de comunicación con una API externa."""


class ErroresValidacion(ValidacionError):
    """Agrupa varios errores de un formulario para mostrarlos todos juntos."""

    def __init__(self, errores: dict[str, str]):
        super().__init__(f"Hay {len(errores)} dato(s) por corregir")
        self.errores = errores
