"""Carga clientes de ejemplo para probar la aplicación (sin enviar correos)."""
from app import create_app
from gic.excepciones import ClienteDuplicadoError

EJEMPLOS = [
    {"tipo": "regular", "rut": "11.111.111-1", "nombre": "Ana Rojas", "email": "ana.rojas@correo.cl",
     "telefono": "+56 9 1111 2222",
     "direccion": {"calle": "Av. Libertador", "numero": "456", "comuna": "Rancagua", "region": "O'Higgins"}},
    {"tipo": "premium", "rut": "12.345.678-5", "nombre": "Pedro Díaz", "email": "pedro.diaz@correo.cl",
     "telefono": "9 8765 4321", "nivel": "oro", "puntos": 340,
     "direccion": {"calle": "Calle Estado", "numero": "120", "comuna": "Machalí", "region": "O'Higgins"}},
    {"tipo": "corporativo", "rut": "9.876.543-3", "nombre": "Carla Muñoz", "email": "cmunoz@andestech.cl",
     "telefono": "+56 9 5555 0101", "razon_social": "Andes Tech SpA", "rut_empresa": "76.086.428-5",
     "empleados": 120,
     "direccion": {"calle": "Av. Providencia", "numero": "1650", "comuna": "Providencia", "region": "Metropolitana"}},
    {"tipo": "premium", "rut": "15.678.234-3", "nombre": "Valentina Soto", "email": "vale.soto@correo.cl",
     "telefono": "912340000", "nivel": "platino", "puntos": 1200,
     "direccion": {"calle": "Los Aromos", "numero": "33", "comuna": "Coltauco", "region": "O'Higgins"}},
    {"tipo": "regular", "rut": "18.234.567-9", "nombre": "Matías Fuentes", "email": "mfuentes@correo.cl",
     "telefono": "+56 9 4321 8765",
     "direccion": {"calle": "Pasaje Las Rosas", "numero": "8", "comuna": "Doñihue", "region": "O'Higgins"}},
]

if __name__ == "__main__":
    app = create_app({"VALIDAR_EN_LINEA": False})
    gestor = app.extensions["gestor"]
    for datos in EJEMPLOS:
        try:
            cliente, _ = gestor.crear(datos, notificar=False)
            print("Creado:", cliente)
        except ClienteDuplicadoError:
            print("Ya existía:", datos["nombre"])
