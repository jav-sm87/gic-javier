"""Clase base abstracta Cliente."""
from abc import ABC, abstractmethod
from datetime import datetime

from ..validaciones import validar_email, validar_rut, validar_telefono, validar_texto
from .direccion import Direccion


class Cliente(ABC):
    """Cliente genérico de SolutionTech.

    Los atributos son privados (doble guion bajo) y se exponen con
    propiedades que validan cada asignación: es imposible dejar un
    cliente en un estado inválido.
    """

    TIPO = "base"

    def __init__(self, rut, nombre, email, telefono, direccion: Direccion,
                 id_cliente: int | None = None, fecha_registro: str | None = None):
        self.__id = id_cliente
        self.__rut = validar_rut(rut)
        self.nombre = nombre
        self.email = email
        self.telefono = telefono
        self.direccion = direccion  # composición
        self.__fecha_registro = fecha_registro or datetime.now().strftime("%Y-%m-%d %H:%M")

    # ---- propiedades (encapsulación) ----
    @property
    def id(self):
        return self.__id

    @id.setter
    def id(self, valor: int):
        if self.__id is not None:
            raise AttributeError("El id de un cliente no se puede cambiar")
        self.__id = valor

    @property
    def rut(self) -> str:
        return self.__rut  # solo lectura: el RUT identifica al cliente

    @property
    def nombre(self) -> str:
        return self.__nombre

    @nombre.setter
    def nombre(self, valor: str):
        self.__nombre = validar_texto(valor, "nombre", 2, 80).title()

    @property
    def email(self) -> str:
        return self.__email

    @email.setter
    def email(self, valor: str):
        self.__email = validar_email(valor)

    @property
    def telefono(self) -> str:
        return self.__telefono

    @telefono.setter
    def telefono(self, valor: str):
        self.__telefono = validar_telefono(valor)

    @property
    def direccion(self) -> Direccion:
        return self.__direccion

    @direccion.setter
    def direccion(self, valor):
        self.__direccion = valor if isinstance(valor, Direccion) else Direccion.from_dict(valor)

    @property
    def fecha_registro(self) -> str:
        return self.__fecha_registro

    # ---- comportamiento polimórfico ----
    @abstractmethod
    def calcular_descuento(self, monto: float) -> float:
        """Monto de descuento que corresponde al cliente sobre una compra."""

    @abstractmethod
    def beneficios(self) -> list[str]:
        """Beneficios asociados al tipo de cliente."""

    def mensaje_bienvenida(self) -> str:
        return (f"Hola {self.nombre}, te damos la bienvenida a SolutionTech. "
                f"Tus beneficios: {', '.join(self.beneficios())}.")

    def precio_final(self, monto: float) -> float:
        return round(monto - self.calcular_descuento(monto), 2)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "tipo": self.TIPO, "rut": self.rut, "nombre": self.nombre,
            "email": self.email, "telefono": self.telefono,
            "direccion": self.direccion.to_dict(), "fecha_registro": self.fecha_registro,
        }

    # ---- métodos especiales ----
    def __str__(self) -> str:
        return f"[{self.TIPO.capitalize()}] {self.nombre} ({self.rut}) - {self.email}"

    def __repr__(self) -> str:
        return f"{type(self).__name__}(rut={self.rut!r}, nombre={self.nombre!r})"

    def __eq__(self, otro) -> bool:
        # Dos clientes son el mismo si comparten RUT, sin importar su tipo
        return isinstance(otro, Cliente) and self.rut == otro.rut

    def __hash__(self) -> int:
        return hash(self.rut)
