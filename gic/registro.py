"""Configuración del registro de actividad (logs) del sistema."""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

_CONFIGURADO = False


def obtener_logger(nombre: str = "gic") -> logging.Logger:
    """Devuelve un logger hijo de 'gic' que escribe en logs/gic.log (rotativo)."""
    global _CONFIGURADO
    raiz = logging.getLogger("gic")
    if not _CONFIGURADO:
        carpeta = Path(__file__).resolve().parent.parent / "logs"
        carpeta.mkdir(exist_ok=True)
        formato = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        archivo = RotatingFileHandler(
            carpeta / "gic.log", maxBytes=500_000, backupCount=3, encoding="utf-8"
        )
        archivo.setFormatter(formato)
        consola = logging.StreamHandler()
        consola.setFormatter(formato)
        consola.setLevel(logging.WARNING)
        raiz.addHandler(archivo)
        raiz.addHandler(consola)
        raiz.setLevel(logging.INFO)
        _CONFIGURADO = True
    return raiz if nombre == "gic" else raiz.getChild(nombre)
