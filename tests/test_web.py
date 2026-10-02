import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from app import create_app
from tests import datos


def formulario(d: dict) -> dict:
    plano = {k: v for k, v in d.items() if k != "direccion"}
    plano.update(d["direccion"])
    return plano


class TestWeb(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        notificador = MagicMock()
        notificador.enviar_bienvenida.return_value = "simulado"
        self.app = create_app({
            "TESTING": True, "DB_PATH": str(Path(self.tmp.name) / "web.db"),
            "VALIDAR_EN_LINEA": False, "EXPORT_DIR": self.tmp.name,
            "NOTIFICADOR": notificador,
        })
        self.web = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def test_lista_vacia(self):
        r = self.web.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("Todavía no hay clientes".encode(), r.data)

    def test_crear_desde_formulario(self):
        r = self.web.post("/clientes/nuevo", data=formulario(datos.premium()),
                          follow_redirects=True)
        self.assertIn(b"Pedro D", r.data)
        self.assertIn("creado".encode(), r.data)

    def test_formulario_muestra_error_de_validacion(self):
        r = self.web.post("/clientes/nuevo",
                          data=formulario(datos.regular(email="malo")))
        self.assertEqual(r.status_code, 200)
        self.assertIn("El email no tiene un formato válido".encode(), r.data)
        self.assertIn("Revisa los campos marcados".encode(), r.data)

    def test_eliminar_y_404(self):
        self.web.post("/clientes/nuevo", data=formulario(datos.regular()))
        r = self.web.post("/clientes/1/eliminar", follow_redirects=True)
        self.assertIn("eliminado".encode(), r.data)
        self.assertEqual(self.web.get("/clientes/1").status_code, 404)

    def test_exportar_csv(self):
        self.web.post("/clientes/nuevo", data=formulario(datos.corporativo()))
        r = self.web.get("/exportar/csv")
        self.assertEqual(r.status_code, 200)
        self.assertIn("Andes Tech SpA".encode(), r.data)
        r.close()


if __name__ == "__main__":
    unittest.main()
