# GIC · Gestor Inteligente de Clientes

Aplicación web en **Python 3 + Flask** para gestionar los clientes de SolutionTech.
Evaluación del Módulo 4 · Javier Soto.

## Qué hace

- Crear, editar, buscar y eliminar clientes desde el navegador.
- Tres tipos de cliente con reglas propias: `ClienteRegular`, `ClientePremium` y `ClienteCorporativo`.
- Valida RUT (dígito verificador), email, teléfono chileno y dirección, mostrando todos los errores a la vez.
- Guarda los datos en **SQLite** y exporta/importa en **JSON** y **CSV**.
- Valida el email en línea con la API pública **Disify** y envía un **correo de bienvenida** por SMTP.
- Registra cada operación en `logs/gic.log` y en una tabla de auditoría (vista *Actividad*).

## Cómo ejecutarlo

```bash
python -m venv venv
venv\Scripts\activate          # Windows  (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
python cargar_ejemplos.py      # opcional: 5 clientes de prueba
python app.py                  # abrir http://127.0.0.1:5000
```

Otros comandos:

```bash
python ejemplo_poo.py                              # ejemplo de instanciación por consola
python -m unittest discover -s tests -t . -v       # 50 pruebas unitarias
```

## Configuración opcional (variables de entorno)

| Variable | Uso |
| --- | --- |
| `GIC_VALIDAR_EN_LINEA` | `1` (defecto) consulta la API Disify; `0` la desactiva |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` | Envío real de correos (ej. Gmail con contraseña de aplicación) |
| `GIC_SECRET` | Clave secreta de Flask |

Sin SMTP configurado, los correos de bienvenida se guardan como `.eml` en `data/bandeja_salida/`.

## Estructura

```
gic-javier/
├── app.py                  # rutas Flask (interfaz web)
├── cargar_ejemplos.py      # datos de prueba
├── ejemplo_poo.py          # demo de instanciación
├── gic/
│   ├── excepciones.py      # jerarquía de errores propios
│   ├── validaciones.py     # RUT, email, teléfono, texto
│   ├── registro.py         # logs rotativos
│   ├── modelos/            # Cliente (abstracta), subclases y Direccion
│   ├── persistencia/       # RepositorioSQLite, ArchivoJSON, ArchivoCSV
│   └── servicios/          # GestorClientes, ValidadorIdentidad, Notificador
├── templates/              # plantillas Jinja2
├── static/estilos.css
├── tests/                  # pruebas unitarias (unittest + mocks)
└── docs/                   # diagrama UML y capturas
```
