import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import requests

from gic.excepciones import EmailInvalidoError, ServicioExternoError
from gic.modelos import crear_cliente
from gic.persistencia import RepositorioSQLite
from gic.servicios import GestorClientes, Notificador, ValidadorIdentidad
from tests import datos


def sesion_falsa(respuesta=None, error=None):
    sesion = MagicMock()
    if error:
        sesion.get.side_effect = error
    else:
        sesion.get.return_value.json.return_value = respuesta
    return sesion


class TestValidadorIdentidad(unittest.TestCase):
    def test_email_aprobado_por_la_api(self):
        v = ValidadorIdentidad(sesion=sesion_falsa({"format": True, "dns": True,
                                                    "disposable": False}))
        self.assertEqual(v.validar("12.345.678-5", "pedro@correo.cl"), [])

    def test_email_desechable_rechazado(self):
        v = ValidadorIdentidad(sesion=sesion_falsa({"format": True, "dns": True,
                                                    "disposable": True}))
        with self.assertRaises(EmailInvalidoError):
            v.validar("12.345.678-5", "x@mailinator.com")

    def test_dominio_inexistente_rechazado(self):
        v = ValidadorIdentidad(sesion=sesion_falsa({"format": True, "dns": False}))
        with self.assertRaises(EmailInvalidoError):
            v.validar("12.345.678-5", "x@dominioquenoexiste.cl")

    def test_api_caida_no_detiene_el_registro(self):
        v = ValidadorIdentidad(sesion=sesion_falsa(error=requests.ConnectionError("sin red")))
        avisos = v.validar("12.345.678-5", "pedro@correo.cl")
        self.assertEqual(len(avisos), 1)


class TestNotificador(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cliente = crear_cliente(datos.premium())

    def tearDown(self):
        self.tmp.cleanup()

    def test_modo_simulacion_guarda_el_correo(self):
        n = Notificador(host="", usuario="", clave="", carpeta_simulacion=self.tmp.name)
        self.assertEqual(n.enviar_bienvenida(self.cliente), "simulado")
        archivos = list(Path(self.tmp.name).glob("*.eml"))
        self.assertEqual(len(archivos), 1)
        self.assertIn("Descuento 15%", archivos[0].read_text(encoding="utf-8"))

    @patch("gic.servicios.notificador.smtplib.SMTP")
    def test_modo_real_usa_smtp(self, smtp):
        n = Notificador(host="smtp.test", usuario="u@test.cl", clave="x")
        self.assertEqual(n.enviar_bienvenida(self.cliente), "enviado")
        smtp.return_value.__enter__.return_value.send_message.assert_called_once()

    @patch("gic.servicios.notificador.smtplib.SMTP", side_effect=OSError("timeout"))
    def test_fallo_smtp_lanza_error_propio(self, _):
        n = Notificador(host="smtp.test", usuario="u@test.cl", clave="x")
        with self.assertRaises(ServicioExternoError):
            n.enviar_bienvenida(self.cliente)


class TestGestorClientes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = RepositorioSQLite(str(Path(self.tmp.name) / "g.db"))
        self.notificador = MagicMock(spec=Notificador)
        self.notificador.enviar_bienvenida.return_value = "simulado"
        self.gestor = GestorClientes(self.repo, ValidadorIdentidad(habilitado=False),
                                     self.notificador)

    def tearDown(self):
        self.tmp.cleanup()

    def test_crear_envia_bienvenida_y_audita(self):
        cliente, avisos = self.gestor.crear(datos.premium())
        self.notificador.enviar_bienvenida.assert_called_once_with(cliente)
        self.assertEqual(self.repo.ultimas_operaciones()[0]["operacion"], "CREAR")
        self.assertIn("Email de bienvenida simulado.", avisos)

    def test_fallo_de_email_no_impide_crear(self):
        self.notificador.enviar_bienvenida.side_effect = ServicioExternoError("SMTP caído")
        cliente, avisos = self.gestor.crear(datos.regular())
        self.assertIsNotNone(cliente.id)
        self.assertIn("SMTP caído", avisos)

    def test_editar_cambia_tipo_y_conserva_rut(self):
        c, _ = self.gestor.crear(datos.regular())
        editado = self.gestor.editar(c.id, {"tipo": "premium", "nivel": "platino",
                                            "rut": "99.999.999-9"})
        self.assertEqual(editado.TIPO, "premium")
        self.assertEqual(editado.rut, "11111111-1")

    def test_resumen_y_eliminar(self):
        for d in (datos.regular(), datos.premium(), datos.corporativo()):
            self.gestor.crear(d, notificar=False)
        self.assertEqual(self.gestor.resumen(),
                         {"total": 3, "regular": 1, "premium": 1, "corporativo": 1})
        self.gestor.eliminar(self.gestor.listar()[0].id)
        self.assertEqual(self.gestor.resumen()["total"], 2)

    def test_exportar_e_importar_omitiendo_duplicados(self):
        self.gestor.crear(datos.regular(), notificar=False)
        ruta = self.gestor.exportar(str(Path(self.tmp.name) / "c.json"))
        resultado = self.gestor.importar(ruta)
        self.assertEqual(resultado["duplicados"], 1)
        self.assertEqual(resultado["importados"], 0)


if __name__ == "__main__":
    unittest.main()
