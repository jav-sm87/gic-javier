"""Subclases concretas de Cliente (herencia + polimorfismo)."""
from ..excepciones import ValidacionError
from ..validaciones import validar_rut, validar_texto
from .cliente import Cliente
from .direccion import Direccion


class ClienteRegular(Cliente):
    TIPO = "regular"

    def calcular_descuento(self, monto: float) -> float:
        return 0.0

    def beneficios(self) -> list[str]:
        return ["Soporte por correo"]


class ClientePremium(Cliente):
    TIPO = "premium"
    NIVELES = {"plata": 0.10, "oro": 0.15, "platino": 0.20}

    def __init__(self, *args, nivel: str = "plata", puntos: int = 0, **kwargs):
        super().__init__(*args, **kwargs)  # reutiliza toda la validación de Cliente
        self.nivel = nivel
        self.puntos = puntos

    @property
    def nivel(self) -> str:
        return self.__nivel

    @nivel.setter
    def nivel(self, valor: str):
        valor = (valor or "").lower()
        if valor not in self.NIVELES:
            raise ValidacionError("Nivel premium inválido (plata, oro o platino)", "nivel")
        self.__nivel = valor

    @property
    def puntos(self) -> int:
        return self.__puntos

    @puntos.setter
    def puntos(self, valor):
        try:
            valor = int(valor)
        except (TypeError, ValueError) as error:
            raise ValidacionError("Los puntos deben ser un número entero", "puntos") from error
        if valor < 0:
            raise ValidacionError("Los puntos no pueden ser negativos", "puntos")
        self.__puntos = valor

    def acumular_puntos(self, monto: float) -> int:
        self.puntos += int(monto // 1000)
        return self.puntos

    def calcular_descuento(self, monto: float) -> float:
        return round(monto * self.NIVELES[self.nivel], 2)

    def beneficios(self) -> list[str]:
        return [f"Descuento {int(self.NIVELES[self.nivel] * 100)}%",
                "Soporte prioritario", "Acumulación de puntos"]

    def to_dict(self) -> dict:
        datos = super().to_dict()
        datos.update(nivel=self.nivel, puntos=self.puntos)
        return datos


class ClienteCorporativo(Cliente):
    TIPO = "corporativo"

    def __init__(self, *args, razon_social: str = "", rut_empresa: str = "",
                 empleados: int = 1, **kwargs):
        super().__init__(*args, **kwargs)
        self.razon_social = validar_texto(razon_social, "razón social", 3, 100)
        self.rut_empresa = validar_rut(rut_empresa)
        self.empleados = empleados

    @property
    def empleados(self) -> int:
        return self.__empleados

    @empleados.setter
    def empleados(self, valor):
        try:
            valor = int(valor)
        except (TypeError, ValueError) as error:
            raise ValidacionError("Empleados debe ser un número entero", "empleados") from error
        if valor < 1:
            raise ValidacionError("La empresa debe tener al menos 1 empleado", "empleados")
        self.__empleados = valor

    def calcular_descuento(self, monto: float) -> float:
        # Descuento por volumen: 5% base + 1% cada 50 empleados, tope 25%
        tasa = min(0.05 + (self.empleados // 50) * 0.01, 0.25)
        return round(monto * tasa, 2)

    def beneficios(self) -> list[str]:
        return ["Descuento por volumen", "Ejecutivo de cuenta dedicado", "Facturación mensual"]

    def mensaje_bienvenida(self) -> str:
        base = super().mensaje_bienvenida()
        return f"{base} Gracias por confiar en nosotros como {self.razon_social}."

    def __str__(self) -> str:
        return f"{super().__str__()} | {self.razon_social}"

    def to_dict(self) -> dict:
        datos = super().to_dict()
        datos.update(razon_social=self.razon_social, rut_empresa=self.rut_empresa,
                     empleados=self.empleados)
        return datos


def _valor(datos: dict, clave: str, defecto):
    """Usa el defecto solo si el dato falta (un 0 explícito se respeta y se valida)."""
    valor = datos.get(clave)
    return defecto if valor in (None, "") else valor


TIPOS = {c.TIPO: c for c in (ClienteRegular, ClientePremium, ClienteCorporativo)}


def crear_cliente(datos: dict) -> Cliente:
    """Fábrica: construye la subclase correcta a partir de un diccionario."""
    tipo = (datos.get("tipo") or "").lower()
    if tipo not in TIPOS:
        raise ValidacionError(f"Tipo de cliente desconocido: {tipo!r}", "tipo")
    comunes = dict(
        rut=datos.get("rut"), nombre=datos.get("nombre"), email=datos.get("email"),
        telefono=datos.get("telefono"),
        direccion=Direccion.from_dict(datos.get("direccion") or {}),
        id_cliente=datos.get("id"), fecha_registro=datos.get("fecha_registro"),
    )
    if tipo == "premium":
        return ClientePremium(**comunes, nivel=_valor(datos, "nivel", "plata"),
                              puntos=_valor(datos, "puntos", 0))
    if tipo == "corporativo":
        return ClienteCorporativo(**comunes, razon_social=datos.get("razon_social"),
                                  rut_empresa=datos.get("rut_empresa"),
                                  empleados=_valor(datos, "empleados", 1))
    return ClienteRegular(**comunes)


def revisar_datos(datos: dict) -> None:
    """Valida campo por campo y lanza ErroresValidacion con TODOS los errores.

    Se usa antes de crear o editar para que la interfaz pueda marcar cada
    campo con problema en una sola pasada.
    """
    from ..excepciones import ErroresValidacion
    from ..validaciones import validar_email, validar_telefono

    errores = {}
    tipo = (datos.get("tipo") or "").lower()

    def validar_tipo():
        if tipo not in TIPOS:
            raise ValidacionError("Elige un tipo de cliente válido", "tipo")

    def validar_nivel():
        if _valor(datos, "nivel", "plata").lower() not in ClientePremium.NIVELES:
            raise ValidacionError("Nivel premium inválido (plata, oro o platino)", "nivel")

    chequeos = {
        "tipo": validar_tipo,
        "rut": lambda: validar_rut(datos.get("rut")),
        "nombre": lambda: validar_texto(datos.get("nombre"), "nombre", 2, 80),
        "email": lambda: validar_email(datos.get("email")),
        "telefono": lambda: validar_telefono(datos.get("telefono")),
    }
    direccion = datos.get("direccion") or {}
    for campo, etiqueta, maximo in (("calle", "calle", 80), ("numero", "número", 10),
                                    ("comuna", "comuna", 50), ("region", "región", 50)):
        minimo = 1 if campo == "numero" else 3
        chequeos[campo] = (lambda c=campo, e=etiqueta, mn=minimo, mx=maximo:
                           validar_texto(direccion.get(c), e, mn, mx))
    if tipo == "premium":
        chequeos["nivel"] = validar_nivel
    if tipo == "corporativo":
        chequeos["razon_social"] = lambda: validar_texto(datos.get("razon_social"),
                                                         "razón social", 3, 100)
        chequeos["rut_empresa"] = lambda: validar_rut(datos.get("rut_empresa"))

    for campo, chequeo in chequeos.items():
        try:
            chequeo()
        except ValidacionError as error:
            errores[campo] = error.mensaje
    if errores:
        raise ErroresValidacion(errores)
