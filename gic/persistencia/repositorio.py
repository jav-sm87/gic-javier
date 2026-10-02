"""Acceso a datos. El gestor depende de la interfaz RepositorioClientes,
no de SQLite: cambiar de motor solo requiere otra implementación."""
import json
import sqlite3
from abc import ABC, abstractmethod
from contextlib import contextmanager

from ..excepciones import ClienteDuplicadoError, ClienteNoEncontradoError, PersistenciaError
from ..modelos import Cliente, crear_cliente
from ..registro import obtener_logger

log = obtener_logger("persistencia")


class RepositorioClientes(ABC):
    @abstractmethod
    def agregar(self, cliente: Cliente) -> Cliente: ...

    @abstractmethod
    def actualizar(self, cliente: Cliente) -> None: ...

    @abstractmethod
    def eliminar(self, id_cliente: int) -> None: ...

    @abstractmethod
    def obtener(self, id_cliente: int) -> Cliente: ...

    @abstractmethod
    def listar(self, tipo: str | None = None, texto: str | None = None) -> list[Cliente]: ...

    @abstractmethod
    def registrar_auditoria(self, operacion: str, detalle: str) -> None: ...


class RepositorioSQLite(RepositorioClientes):
    _ESQUEMA = """
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT NOT NULL CHECK (tipo IN ('regular','premium','corporativo')),
        rut TEXT NOT NULL UNIQUE,
        nombre TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        telefono TEXT NOT NULL,
        calle TEXT NOT NULL, numero TEXT NOT NULL,
        comuna TEXT NOT NULL, region TEXT NOT NULL,
        extra TEXT NOT NULL DEFAULT '{}',
        fecha_registro TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS auditoria (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT NOT NULL DEFAULT (datetime('now','localtime')),
        operacion TEXT NOT NULL,
        detalle TEXT NOT NULL
    );
    """
    _COMUNES = {"id", "tipo", "rut", "nombre", "email", "telefono",
                "direccion", "fecha_registro"}

    def __init__(self, ruta_db: str = "data/gic.db"):
        self.ruta_db = ruta_db
        with self._conexion() as con:
            con.executescript(self._ESQUEMA)

    @contextmanager
    def _conexion(self):
        """Abre la conexión, confirma o revierte y siempre la cierra."""
        try:
            con = sqlite3.connect(self.ruta_db)
        except sqlite3.Error as error:
            log.error("No se pudo abrir la base %s: %s", self.ruta_db, error)
            raise PersistenciaError("No se pudo conectar con la base de datos") from error
        con.row_factory = sqlite3.Row
        try:
            yield con
            con.commit()
        except sqlite3.IntegrityError as error:
            con.rollback()
            campo = "rut" if "rut" in str(error) else "email"
            raise ClienteDuplicadoError(
                f"Ya existe un cliente con ese {campo.upper() if campo == 'rut' else campo}",
                campo=campo) from error
        except sqlite3.Error as error:
            con.rollback()
            log.error("Error de base de datos: %s", error)
            raise PersistenciaError("Error al operar con la base de datos") from error
        finally:
            con.close()

    # ---- conversión fila <-> objeto ----
    def _a_parametros(self, c: Cliente) -> dict:
        datos = c.to_dict()
        extra = {k: v for k, v in datos.items() if k not in self._COMUNES}
        return {**{k: datos[k] for k in ("tipo", "rut", "nombre", "email", "telefono",
                                           "fecha_registro")},
                **datos["direccion"], "extra": json.dumps(extra, ensure_ascii=False),
                "id": c.id}

    @staticmethod
    def _a_cliente(fila: sqlite3.Row) -> Cliente:
        datos = dict(fila)
        datos["direccion"] = {k: datos.pop(k) for k in ("calle", "numero", "comuna", "region")}
        datos.update(json.loads(datos.pop("extra") or "{}"))
        return crear_cliente(datos)

    # ---- CRUD ----
    def agregar(self, cliente: Cliente) -> Cliente:
        p = self._a_parametros(cliente)
        with self._conexion() as con:
            cur = con.execute(
                """INSERT INTO clientes (tipo, rut, nombre, email, telefono, calle, numero,
                   comuna, region, extra, fecha_registro)
                   VALUES (:tipo, :rut, :nombre, :email, :telefono, :calle, :numero,
                   :comuna, :region, :extra, :fecha_registro)""", p)
            cliente.id = cur.lastrowid
        return cliente

    def actualizar(self, cliente: Cliente) -> None:
        p = self._a_parametros(cliente)
        with self._conexion() as con:
            cur = con.execute(
                """UPDATE clientes SET tipo=:tipo, nombre=:nombre, email=:email,
                   telefono=:telefono, calle=:calle, numero=:numero, comuna=:comuna,
                   region=:region, extra=:extra WHERE id=:id""", p)
            if cur.rowcount == 0:
                raise ClienteNoEncontradoError(f"No existe el cliente {cliente.id}")

    def eliminar(self, id_cliente: int) -> None:
        with self._conexion() as con:
            cur = con.execute("DELETE FROM clientes WHERE id = ?", (id_cliente,))
            if cur.rowcount == 0:
                raise ClienteNoEncontradoError(f"No existe el cliente {id_cliente}")

    def obtener(self, id_cliente: int) -> Cliente:
        with self._conexion() as con:
            fila = con.execute("SELECT * FROM clientes WHERE id = ?", (id_cliente,)).fetchone()
        if fila is None:
            raise ClienteNoEncontradoError(f"No existe el cliente {id_cliente}")
        return self._a_cliente(fila)

    def listar(self, tipo=None, texto=None) -> list[Cliente]:
        sql, params = "SELECT * FROM clientes WHERE 1=1", []
        if tipo:
            sql += " AND tipo = ?"
            params.append(tipo)
        if texto:
            sql += " AND (nombre LIKE ? OR email LIKE ? OR rut LIKE ?)"
            params += [f"%{texto}%"] * 3
        sql += " ORDER BY nombre"
        with self._conexion() as con:
            filas = con.execute(sql, params).fetchall()
        return [self._a_cliente(f) for f in filas]

    def registrar_auditoria(self, operacion: str, detalle: str) -> None:
        with self._conexion() as con:
            con.execute("INSERT INTO auditoria (operacion, detalle) VALUES (?, ?)",
                        (operacion, detalle))

    def ultimas_operaciones(self, limite: int = 15) -> list[dict]:
        with self._conexion() as con:
            filas = con.execute("SELECT fecha, operacion, detalle FROM auditoria "
                                "ORDER BY id DESC LIMIT ?", (limite,)).fetchall()
        return [dict(f) for f in filas]
