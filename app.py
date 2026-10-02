"""Interfaz web del GIC con Flask + plantillas Jinja2.

Ejecutar:  python app.py   y abrir http://127.0.0.1:5000
"""
import os
from pathlib import Path

from flask import (Flask, abort, flash, redirect, render_template, request,
                   send_file, url_for)
from werkzeug.utils import secure_filename

from gic.excepciones import ClienteNoEncontradoError, ErroresValidacion, GICError
from gic.modelos import ClientePremium, TIPOS
from gic.persistencia import RepositorioSQLite
from gic.registro import obtener_logger
from gic.servicios import GestorClientes, Notificador, ValidadorIdentidad

BASE = Path(__file__).resolve().parent
log = obtener_logger("web")


def datos_formulario(form) -> dict:
    """Convierte el formulario HTML al diccionario que entiende la fábrica."""
    datos = {k: form.get(k, "").strip() for k in (
        "tipo", "rut", "nombre", "email", "telefono", "nivel", "puntos",
        "razon_social", "rut_empresa", "empleados")}
    datos["direccion"] = {k: form.get(k, "").strip()
                          for k in ("calle", "numero", "comuna", "region")}
    return {k: v for k, v in datos.items() if v != ""}


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv("GIC_SECRET", "cambia-esta-clave-en-produccion"),
        DB_PATH=str(BASE / "data" / "gic.db"),
        VALIDAR_EN_LINEA=os.getenv("GIC_VALIDAR_EN_LINEA", "1") == "1",
        EXPORT_DIR=str(BASE / "data" / "exportaciones"),
        MAX_CONTENT_LENGTH=2 * 1024 * 1024,
    )
    if config:
        app.config.update(config)
    Path(app.config["DB_PATH"]).parent.mkdir(parents=True, exist_ok=True)

    gestor = GestorClientes(
        RepositorioSQLite(app.config["DB_PATH"]),
        ValidadorIdentidad(habilitado=app.config["VALIDAR_EN_LINEA"]),
        app.config.get("NOTIFICADOR") or Notificador(
            carpeta_simulacion=str(Path(app.config["DB_PATH"]).parent / "bandeja_salida")),
    )
    app.extensions["gestor"] = gestor

    @app.context_processor
    def globales():
        return {"tipos": list(TIPOS), "niveles": list(ClientePremium.NIVELES)}

    @app.errorhandler(GICError)
    def error_dominio(error):
        log.warning("Error no controlado del dominio: %s", error.mensaje)
        flash(error.mensaje, "error")
        return redirect(url_for("lista"))

    @app.get("/")
    def lista():
        tipo = request.args.get("tipo") or None
        texto = request.args.get("q", "").strip() or None
        return render_template("clientes/lista.html", clientes=gestor.listar(tipo, texto),
                               resumen=gestor.resumen(), tipo_activo=tipo, texto=texto or "")

    @app.route("/clientes/nuevo", methods=["GET", "POST"])
    def nuevo():
        datos = {}
        errores = {}
        if request.method == "POST":
            datos = datos_formulario(request.form)
            try:
                cliente, avisos = gestor.crear(datos)
                flash(f"Cliente {cliente.nombre} creado.", "ok")
                for aviso in avisos:
                    flash(aviso, "info")
                return redirect(url_for("detalle", id_cliente=cliente.id))
            except ErroresValidacion as error:
                errores = error.errores
            except GICError as error:
                errores[error.campo or "general"] = error.mensaje
        return render_template("clientes/formulario.html", datos=datos, errores=errores,
                               editando=False)

    @app.route("/clientes/<int:id_cliente>/editar", methods=["GET", "POST"])
    def editar(id_cliente):
        cliente = _buscar(id_cliente)
        datos = cliente.to_dict()
        errores = {}
        if request.method == "POST":
            datos = {**datos_formulario(request.form), "rut": cliente.rut}
            try:
                gestor.editar(id_cliente, datos)
                flash("Cambios guardados.", "ok")
                return redirect(url_for("detalle", id_cliente=id_cliente))
            except ErroresValidacion as error:
                errores = error.errores
            except GICError as error:
                errores[error.campo or "general"] = error.mensaje
        return render_template("clientes/formulario.html", datos=datos, errores=errores,
                               editando=True, id_cliente=id_cliente)

    @app.get("/clientes/<int:id_cliente>")
    def detalle(id_cliente):
        cliente = _buscar(id_cliente)
        monto = request.args.get("monto", type=float) or 100000
        return render_template("clientes/detalle.html", c=cliente, monto=monto)

    @app.post("/clientes/<int:id_cliente>/eliminar")
    def eliminar(id_cliente):
        cliente = _buscar(id_cliente)
        gestor.eliminar(id_cliente)
        flash(f"Cliente {cliente.nombre} eliminado.", "ok")
        return redirect(url_for("lista"))

    @app.get("/exportar/<formato>")
    def exportar(formato):
        if formato not in ("json", "csv"):
            abort(404)
        ruta = gestor.exportar(str(Path(app.config["EXPORT_DIR"]) / f"clientes.{formato}"))
        return send_file(ruta, as_attachment=True)

    @app.post("/importar")
    def importar():
        archivo = request.files.get("archivo")
        if not archivo or not archivo.filename.endswith((".json", ".csv")):
            flash("Elige un archivo .json o .csv para importar.", "error")
            return redirect(url_for("lista"))
        destino = Path(app.config["EXPORT_DIR"]) / secure_filename(archivo.filename)
        destino.parent.mkdir(parents=True, exist_ok=True)
        archivo.save(destino)
        r = gestor.importar(str(destino))
        flash(f"Importados: {r['importados']}. Duplicados omitidos: {r['duplicados']}.", "ok")
        for e in r["errores"][:5]:
            flash(e, "error")
        return redirect(url_for("lista"))

    @app.get("/actividad")
    def actividad():
        return render_template("actividad.html",
                               operaciones=gestor.repo.ultimas_operaciones(40))

    def _buscar(id_cliente):
        try:
            return gestor.obtener(id_cliente)
        except ClienteNoEncontradoError:
            abort(404)

    @app.errorhandler(404)
    def no_encontrado(_):
        return render_template("404.html"), 404

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
