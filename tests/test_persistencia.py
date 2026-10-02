import json
import tempfile
import unittest
from pathlib import Path

from gic.excepciones import ClienteDuplicadoError, ClienteNoEncontradoError, PersistenciaError
from gic.modelos import crear_cliente
from gic.persistencia import ArchivoCSV, ArchivoJSON, RepositorioSQLite
from tests import datos


class TestRepositorioSQLite(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = RepositorioSQLite(str(Path(self.tmp.name) / "prueba.db"))

    def tearDown(self):
        self.tmp.cleanup()

    def test_agregar_y_obtener_conserva_el_tipo(self):
        c = self.repo.agregar(crear_cliente(datos.corporativo()))
        leido = self.repo.obtener(c.id)
        self.assertEqual(leido.TIPO, "corporativo")
        self.assertEqual(leido.razon_social, "Andes Tech SpA")
        self.assertEqual(leido.direccion.comuna, "Rancagua")

    def test_rut_duplicado(self):
        self.repo.agregar(crear_cliente(datos.regular()))
        with self.assertRaises(ClienteDuplicadoError):
            self.repo.agregar(crear_cliente(datos.regular(email="otro@correo.cl")))

    def test_actualizar_y_eliminar(self):
        c = self.repo.agregar(crear_cliente(datos.regular()))
        c.nombre = "Ana Rojas Soto"
        self.repo.actualizar(c)
        self.assertEqual(self.repo.obtener(c.id).nombre, "Ana Rojas Soto")
        self.repo.eliminar(c.id)
        with self.assertRaises(ClienteNoEncontradoError):
            self.repo.obtener(c.id)

    def test_listar_con_filtros(self):
        for d in (datos.regular(), datos.premium(), datos.corporativo()):
            self.repo.agregar(crear_cliente(d))
        self.assertEqual(len(self.repo.listar()), 3)
        self.assertEqual(len(self.repo.listar(tipo="premium")), 1)
        self.assertEqual(self.repo.listar(texto="carla")[0].nombre, "Carla Muñoz")

    def test_inyeccion_sql_no_afecta(self):
        self.repo.agregar(crear_cliente(datos.regular()))
        self.assertEqual(self.repo.listar(texto="' OR 1=1 --"), [])
        self.assertEqual(len(self.repo.listar()), 1)

    def test_error_de_conexion(self):
        with self.assertRaises(PersistenciaError):
            RepositorioSQLite("/ruta/que/no/existe/gic.db")


class TestArchivos(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.clientes = [crear_cliente(d) for d in
                         (datos.regular(), datos.premium(), datos.corporativo())]

    def tearDown(self):
        self.tmp.cleanup()

    def test_json_ida_y_vuelta(self):
        archivo = ArchivoJSON(Path(self.tmp.name) / "c.json")
        archivo.exportar(self.clientes)
        recuperados = [crear_cliente(r) for r in archivo.importar()]
        self.assertEqual(recuperados, self.clientes)

    def test_csv_ida_y_vuelta(self):
        archivo = ArchivoCSV(Path(self.tmp.name) / "c.csv")
        archivo.exportar(self.clientes)
        recuperados = [crear_cliente(r) for r in archivo.importar()]
        self.assertEqual([c.TIPO for c in recuperados], ["regular", "premium", "corporativo"])
        self.assertEqual(recuperados[1].nivel, "oro")

    def test_json_corrupto(self):
        ruta = Path(self.tmp.name) / "malo.json"
        ruta.write_text("{esto no es json", encoding="utf-8")
        with self.assertRaises(PersistenciaError):
            ArchivoJSON(ruta).importar()

    def test_archivo_inexistente(self):
        with self.assertRaises(PersistenciaError):
            ArchivoJSON(Path(self.tmp.name) / "nada.json").importar()


if __name__ == "__main__":
    unittest.main()
