"""Dirección postal. Es parte de un Cliente (composición): nace y muere con él."""
from ..excepciones import DireccionInvalidaError, ValidacionError
from ..validaciones import validar_texto


class Direccion:
    def __init__(self, calle: str, numero: str, comuna: str, region: str):
        try:
            self.calle = validar_texto(calle, "calle", 3, 80)
            self.numero = validar_texto(numero, "número", 1, 10)
            self.comuna = validar_texto(comuna, "comuna", 3, 50)
            self.region = validar_texto(region, "región", 3, 50)
        except ValidacionError as error:
            raise DireccionInvalidaError(f"Dirección inválida: {error.mensaje}") from error

    def to_dict(self) -> dict:
        return {"calle": self.calle, "numero": self.numero,
                "comuna": self.comuna, "region": self.region}

    @classmethod
    def from_dict(cls, datos: dict) -> "Direccion":
        return cls(datos.get("calle"), datos.get("numero"),
                   datos.get("comuna"), datos.get("region"))

    def __str__(self) -> str:
        return f"{self.calle} {self.numero}, {self.comuna}, {self.region}"

    def __eq__(self, otra) -> bool:
        return isinstance(otra, Direccion) and self.to_dict() == otra.to_dict()
