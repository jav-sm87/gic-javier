"""Ejemplo práctico de instanciación y uso de métodos (Entregable 1).

Ejecutar:  python ejemplo_poo.py
"""
from gic.excepciones import EmailInvalidoError, RutInvalidoError
from gic.modelos import ClienteCorporativo, ClientePremium, ClienteRegular, Direccion

casa = Direccion("Av. Libertador", "456", "Rancagua", "O'Higgins")

# 1. Instanciación: cada objeto se crea a partir de su clase
ana = ClienteRegular("11.111.111-1", "ana rojas", "Ana@Correo.cl", "9 1111 2222", casa)
pedro = ClientePremium("12.345.678-5", "Pedro Díaz", "pedro@correo.cl", "+56987654321",
                       Direccion("Estado", "120", "Machalí", "O'Higgins"), nivel="oro")
carla = ClienteCorporativo("9.876.543-3", "Carla Muñoz", "cmunoz@andestech.cl",
                           "955550101", Direccion("Providencia", "1650", "Providencia",
                                                  "Metropolitana"),
                           razon_social="Andes Tech SpA", rut_empresa="76.086.428-5",
                           empleados=120)

# 2. __str__: representación legible
print("Clientes creados:")
for cliente in (ana, pedro, carla):
    print("  ", cliente)

# 3. Encapsulación: los setters normalizan y validan
print("\nEmail normalizado:", ana.email, "| Teléfono:", ana.telefono)
try:
    ana.email = "correo-sin-arroba"
except EmailInvalidoError as error:
    print("Asignación rechazada:", error.mensaje)

try:
    ClienteRegular("12.345.678-9", "Error", "e@e.cl", "911112222", casa)
except RutInvalidoError as error:
    print("Instanciación rechazada:", error.mensaje)

# 4. Polimorfismo: el mismo método responde distinto según la clase
print("\nCompra de $100.000:")
for cliente in (ana, pedro, carla):
    print(f"   {type(cliente).__name__:<20} descuento ${cliente.calcular_descuento(100_000):>9,.0f}"
          f"  total ${cliente.precio_final(100_000):>9,.0f}")

# 5. __eq__: dos objetos con el mismo RUT representan al mismo cliente
copia = ClienteRegular("11.111.111-1", "Ana R.", "otra@correo.cl", "911112222", casa)
print("\n¿ana == copia?", ana == copia, "| ¿ana == pedro?", ana == pedro)

# 6. Métodos propios de una subclase
print("Puntos de Pedro tras comprar $25.500:", pedro.acumular_puntos(25_500))
print("\nBienvenida corporativa:\n  ", carla.mensaje_bienvenida())
