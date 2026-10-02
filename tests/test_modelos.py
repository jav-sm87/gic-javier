import unittest

from gic.excepciones import DireccionInvalidaError, EmailInvalidoError, ValidacionError
from gic.modelos import (Cliente, ClienteCorporativo, ClientePremium, ClienteRegular,
                         Direccion, crear_cliente)
from tests import datos


class TestCliente(unittest.TestCase):
    def setUp(self):
        self.regular = crear_cliente(datos.regular())
        self.premium = crear_cliente(datos.premium())
        self.corporativo = crear_cliente(datos.corporativo())

    def test_no_se_puede_instanciar_la_clase_abstracta(self):
        with self.assertRaises(TypeError):
            Cliente("11.111.111-1", "Ana", "a@b.cl", "912345678",
                    Direccion(**datos.DIRECCION))

    def test_fabrica_crea_la_subclase_correcta(self):
        self.assertIsInstance(self.regular, ClienteRegular)
        self.assertIsInstance(self.premium, ClientePremium)
        self.assertIsInstance(self.corporativo, ClienteCorporativo)

    def test_encapsulacion_valida_al_asignar(self):
        with self.assertRaises(EmailInvalidoError):
            self.regular.email = "correo-malo"
        self.assertEqual(self.regular.email, "ana@correo.cl")  # no cambió

    def test_rut_es_solo_lectura(self):
        with self.assertRaises(AttributeError):
            self.regular.rut = "12.345.678-5"

    def test_atributo_privado_no_es_accesible(self):
        with self.assertRaises(AttributeError):
            _ = self.regular.__email

    def test_str_y_eq(self):
        self.assertEqual(str(self.regular), "[Regular] Ana Rojas (11111111-1) - ana@correo.cl")
        mismo_rut = crear_cliente(datos.regular(email="otro@correo.cl", tipo="premium"))
        self.assertEqual(self.regular, mismo_rut)
        self.assertNotEqual(self.regular, self.premium)

    def test_composicion_direccion(self):
        self.assertIsInstance(self.regular.direccion, Direccion)
        with self.assertRaises(DireccionInvalidaError):
            Direccion("", "1", "Rancagua", "O'Higgins")


class TestPolimorfismo(unittest.TestCase):
    def setUp(self):
        self.clientes = [crear_cliente(datos.regular()), crear_cliente(datos.premium()),
                         crear_cliente(datos.corporativo())]

    def test_descuento_distinto_segun_tipo(self):
        descuentos = [c.calcular_descuento(100_000) for c in self.clientes]
        self.assertEqual(descuentos, [0.0, 15_000.0, 7_000.0])  # 0%, oro 15%, 5%+2%

    def test_tope_descuento_corporativo(self):
        c = crear_cliente(datos.corporativo(empleados=5000))
        self.assertEqual(c.calcular_descuento(100_000), 25_000.0)

    def test_beneficios_y_bienvenida_sobrescritos(self):
        textos = [c.mensaje_bienvenida() for c in self.clientes]
        self.assertIn("Soporte por correo", textos[0])
        self.assertIn("Descuento 15%", textos[1])
        self.assertIn("Andes Tech SpA", textos[2])  # extendido con super()

    def test_to_dict_incluye_campos_propios(self):
        self.assertEqual(self.clientes[1].to_dict()["nivel"], "oro")
        self.assertEqual(self.clientes[2].to_dict()["empleados"], 120)

    def test_premium_acumula_puntos(self):
        self.assertEqual(self.clientes[1].acumular_puntos(25_500), 125)

    def test_validaciones_de_subclases(self):
        with self.assertRaises(ValidacionError):
            crear_cliente(datos.premium(nivel="diamante"))
        with self.assertRaises(ValidacionError):
            crear_cliente(datos.corporativo(empleados=0))
        with self.assertRaises(ValidacionError):
            crear_cliente(datos.regular(tipo="vip"))



class TestRevisionCompleta(unittest.TestCase):
    def test_reporta_todos_los_errores_juntos(self):
        from gic.excepciones import ErroresValidacion
        from gic.modelos import revisar_datos
        malos = datos.corporativo(rut="12.345.678-9", email="x@", telefono="22",
                                  direccion={}, rut_empresa="1-1")
        with self.assertRaises(ErroresValidacion) as ctx:
            revisar_datos(malos)
        self.assertTrue({"rut", "email", "telefono", "calle", "comuna",
                         "rut_empresa"} <= set(ctx.exception.errores))

    def test_datos_correctos_no_lanzan(self):
        from gic.modelos import revisar_datos
        for d in (datos.regular(), datos.premium(), datos.corporativo()):
            revisar_datos(d)


if __name__ == "__main__":
    unittest.main()
