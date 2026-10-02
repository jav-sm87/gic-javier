"""Exportación e importación de clientes en JSON y CSV.

ArchivoCSV hereda de ArchivoJSON el contrato exportar/importar y
sobrescribe el formato: otro ejemplo de polimorfismo.
"""
import csv
import json
from pathlib import Path

from ..excepciones import PersistenciaError
from ..modelos import Cliente


class ArchivoJSON:
    extension = ".json"

    def __init__(self, ruta: str | Path):
        self.ruta = Path(ruta)

    def exportar(self, clientes: list[Cliente]) -> Path:
        try:
            self.ruta.parent.mkdir(parents=True, exist_ok=True)
            self._escribir([c.to_dict() for c in clientes])
        except OSError as error:
            raise PersistenciaError(f"No se pudo escribir {self.ruta.name}") from error
        return self.ruta

    def importar(self) -> list[dict]:
        try:
            return self._leer()
        except FileNotFoundError as error:
            raise PersistenciaError(f"No existe el archivo {self.ruta.name}") from error
        except (OSError, ValueError, KeyError) as error:
            raise PersistenciaError(f"El archivo {self.ruta.name} tiene un formato inválido") from error

    def _escribir(self, registros: list[dict]) -> None:
        self.ruta.write_text(json.dumps(registros, ensure_ascii=False, indent=2), encoding="utf-8")

    def _leer(self) -> list[dict]:
        datos = json.loads(self.ruta.read_text(encoding="utf-8"))
        if not isinstance(datos, list):
            raise ValueError("Se esperaba una lista de clientes")
        return datos


class ArchivoCSV(ArchivoJSON):
    extension = ".csv"
    COLUMNAS = ["id", "tipo", "rut", "nombre", "email", "telefono", "calle", "numero",
                "comuna", "region", "nivel", "puntos", "razon_social", "rut_empresa",
                "empleados", "fecha_registro"]

    def _escribir(self, registros: list[dict]) -> None:
        with self.ruta.open("w", newline="", encoding="utf-8-sig") as f:
            escritor = csv.DictWriter(f, fieldnames=self.COLUMNAS, delimiter=";",
                                      extrasaction="ignore")
            escritor.writeheader()
            for r in registros:
                escritor.writerow({**r, **r["direccion"]})

    def _leer(self) -> list[dict]:
        with self.ruta.open(newline="", encoding="utf-8-sig") as f:
            filas = list(csv.DictReader(f, delimiter=";"))
        registros = []
        for fila in filas:
            fila = {k: v for k, v in fila.items() if v not in (None, "")}
            fila["direccion"] = {k: fila.pop(k, "") for k in ("calle", "numero", "comuna", "region")}
            fila.pop("id", None)
            registros.append(fila)
        return registros
