"""Datos de ejemplo compartidos por las pruebas."""

DIRECCION = {"calle": "Av. Libertador", "numero": "456", "comuna": "Rancagua",
             "region": "O'Higgins"}


def regular(**cambios):
    base = {"tipo": "regular", "rut": "11.111.111-1", "nombre": "ana rojas",
            "email": "ana@correo.cl", "telefono": "+56 9 1111 2222",
            "direccion": dict(DIRECCION)}
    return {**base, **cambios}


def premium(**cambios):
    base = dict(tipo="premium", rut="12.345.678-5", nombre="Pedro Díaz",
                email="pedro@correo.cl", nivel="oro", puntos=100)
    return regular(**{**base, **cambios})


def corporativo(**cambios):
    base = dict(tipo="corporativo", rut="9.876.543-3", nombre="Carla Muñoz",
                email="carla@empresa.cl", razon_social="Andes Tech SpA",
                rut_empresa="76.086.428-5", empleados=120)
    return regular(**{**base, **cambios})
