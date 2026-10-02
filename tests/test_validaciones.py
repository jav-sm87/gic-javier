import unittest

from gic.excepciones import (EmailInvalidoError, RutInvalidoError, TelefonoInvalidoError,
                             ValidacionError)
from gic.validaciones import (calcular_dv, validar_email, validar_rut, validar_telefono,
                              validar_texto)


class TestValidaciones(unittest.TestCase):
    def test_email_valido_se_normaliza(self):
        self.assertEqual(validar_email("  Juan.Perez@Mail.CL "), "juan.perez@mail.cl")

    def test_email_invalido(self):
        for email in ["sinarroba.cl", "a@b", "a..b@mail.cl", ""]:
            with self.subTest(email=email), self.assertRaises(EmailInvalidoError):
                validar_email(email)

    def test_telefono_formatos_aceptados(self):
        for tel in ["912345678", "+56 9 1234 5678", "56912345678", "(9) 1234-5678"]:
            with self.subTest(tel=tel):
                self.assertEqual(validar_telefono(tel), "+56912345678")

    def test_telefono_invalido(self):
        for tel in ["12345", "+56 2 2345 6789", "abc"]:
            with self.subTest(tel=tel), self.assertRaises(TelefonoInvalidoError):
                validar_telefono(tel)

    def test_digito_verificador(self):
        self.assertEqual(calcular_dv(12345678), "5")
        self.assertEqual(calcular_dv(11111111), "1")

    def test_rut_valido_y_normalizado(self):
        self.assertEqual(validar_rut("12.345.678-5"), "12345678-5")
        self.assertEqual(validar_rut("76086428-5"), "76086428-5")

    def test_rut_con_dv_incorrecto(self):
        with self.assertRaises(RutInvalidoError):
            validar_rut("12.345.678-9")

    def test_texto_obligatorio(self):
        with self.assertRaises(ValidacionError):
            validar_texto("   ", "nombre")


if __name__ == "__main__":
    unittest.main()
