"""GestorClientes: coordina modelos, repositorio y servicios externos.

Agrega clientes (los administra pero no los crea ni los destruye en
memoria por sí mismo) y depende de abstracciones inyectadas en el
constructor, lo que permite reemplazarlas por dobles en las pruebas.
"""
from ..excepciones import ClienteDuplicadoError, GICError, ServicioExternoError
from ..modelos import Cliente, crear_cliente, revisar_datos
from ..persistencia import ArchivoCSV, ArchivoJSON, RepositorioClientes
from ..registro import obtener_logger
from .notificador import Notificador
from .validador_externo import ValidadorIdentidad

log = obtener_logger("gestor")


class GestorClientes:
    def __init__(self, repositorio: RepositorioClientes,
                 validador: ValidadorIdentidad | None = None,
                 notificador: Notificador | None = None):
        self.repo = repositorio
        self.validador = validador or ValidadorIdentidad(habilitado=False)
        self.notificador = notificador or Notificador()

    def _auditar(self, operacion: str, detalle: str) -> None:
        log.info("%s: %s", operacion, detalle)
        self.repo.registrar_auditoria(operacion, detalle)

    # ---- CRUD ----
    def crear(self, datos: dict, notificar: bool = True) -> tuple[Cliente, list[str]]:
        revisar_datos(datos)            # reporta todos los errores juntos
        cliente = crear_cliente(datos)  # construye el objeto ya validado
        avisos = self.validador.validar(cliente.rut, cliente.email)  # valida en línea
        self.repo.agregar(cliente)
        self._auditar("CREAR", str(cliente))
        if notificar:
            try:
                estado = self.notificador.enviar_bienvenida(cliente)
                avisos.append(f"Email de bienvenida {estado}.")
            except ServicioExternoError as error:
                avisos.append(error.mensaje)
        return cliente, avisos

    def editar(self, id_cliente: int, datos: dict) -> Cliente:
        actual = self.repo.obtener(id_cliente)
        datos = {**actual.to_dict(), **datos, "id": id_cliente, "rut": actual.rut}
        revisar_datos(datos)
        cliente = crear_cliente(datos)
        if cliente.email != actual.email:
            self.validador.validar(cliente.rut, cliente.email)
        self.repo.actualizar(cliente)
        self._auditar("EDITAR", str(cliente))
        return cliente

    def eliminar(self, id_cliente: int) -> None:
        cliente = self.repo.obtener(id_cliente)
        self.repo.eliminar(id_cliente)
        self._auditar("ELIMINAR", str(cliente))

    def obtener(self, id_cliente: int) -> Cliente:
        return self.repo.obtener(id_cliente)

    def listar(self, tipo=None, texto=None) -> list[Cliente]:
        return self.repo.listar(tipo, texto)

    def resumen(self) -> dict:
        clientes = self.listar()
        conteo = {"regular": 0, "premium": 0, "corporativo": 0}
        for c in clientes:
            conteo[c.TIPO] += 1
        return {"total": len(clientes), **conteo}

    # ---- archivos ----
    def exportar(self, ruta: str) -> str:
        formato = ArchivoCSV if str(ruta).endswith(".csv") else ArchivoJSON
        destino = formato(ruta).exportar(self.listar())
        self._auditar("EXPORTAR", destino.name)
        return str(destino)

    def importar(self, ruta: str) -> dict:
        formato = ArchivoCSV if str(ruta).endswith(".csv") else ArchivoJSON
        resultado = {"importados": 0, "duplicados": 0, "errores": []}
        for i, registro in enumerate(formato(ruta).importar(), start=1):
            registro.pop("id", None)
            try:
                self.repo.agregar(crear_cliente(registro))
                resultado["importados"] += 1
            except ClienteDuplicadoError:
                resultado["duplicados"] += 1
            except GICError as error:
                resultado["errores"].append(f"Fila {i}: {error.mensaje}")
        self._auditar("IMPORTAR", f"{resultado['importados']} clientes desde {ruta}")
        return resultado
