from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from dotenv import load_dotenv
from services.services import generar_diagrama_completo, generar_diagrama_desde_documento
from services.icon_tools import RESOURCES_DIR

load_dotenv()  

app = Flask(__name__)
app.secret_key = "secreto_desarrollo_stitch"


def construir_prompt_estructurado(datos: dict) -> str:
    """Arma el prompt estructurado para el Agente Arquitecto Cloud a partir
    de los requisitos capturados en el formulario por pasos."""
    return f"""PROVEEDOR CLOUD PREFERIDO: {datos.get('cloud_provider', 'No especificado')}

OBJETIVOS ESTRATÉGICOS:
- {datos.get('objetivos_negocio', 'No especificado')}
- {datos.get('iniciativas_datos', 'No especificado')}

1. CARACTERÍSTICAS DE LOS DATOS:
- Fuentes de Información:
  * Orígenes y tipos: {datos.get('fuentes_origen', 'No especificado')}
  * Criticidad: {datos.get('criticidad_fuentes', 'No especificado')}
- Volumetría:
  * Registros estimados: {datos.get('vol_registros', 'No especificado')}
  * Almacenamiento total: {datos.get('vol_almacenamiento', 'No especificado')}
  * Crecimiento anual esperado: {datos.get('vol_crecimiento', 'No especificado')}
- Frecuencia de Actualización: {datos.get('frecuencia_actualizacion', 'No especificado')}
- Disponibilidad Requerida:
  * Horario de operación: {datos.get('disp_horario', 'No especificado')}
  * SLA esperado: {datos.get('disp_sla', 'No especificado')}
  * Tiempo de indisponibilidad máx (RTO): {datos.get('disp_rto', 'No especificado')}
- Latencia Máxima Aceptable: {datos.get('latencia_maxima', 'No especificado')}
- Retención de Información: {datos.get('retencion_info', 'No especificado')}

CAPAS DE LA ARQUITECTURA DISPONIBLES (Requerimientos específicos):
- Captura e Ingesta: {datos.get('capa_ingesta', 'No especificado')}
- Almacenamiento: {datos.get('capa_almacenamiento', 'No especificado')}
- Procesamiento: {datos.get('capa_procesamiento', 'No especificado')}
- Gobierno de Datos: {datos.get('capa_gobierno', 'No especificado')}
- Seguridad: {datos.get('capa_seguridad', 'No especificado')}
- Consumo: {datos.get('capa_consumo', 'No especificado')}
- Operación: {datos.get('capa_operacion', 'No especificado')}"""


@app.route("/")
def index():
    # Renderiza la vista del Workspace principal
    return render_template("index.html")


@app.route("/icons/<path:icon_path>")
def servir_icono(icon_path):
    """Sirve los iconos del paquete `diagrams` (resources/proveedor/categoria/servicio.png)
    para que el canvas pueda mostrarlos; no viven dentro de static/ porque
    pertenecen al entorno virtual, no al proyecto."""
    return send_from_directory(RESOURCES_DIR, icon_path)


@app.route("/api/generar-desde-requisitos", methods=["POST"])
def generar_desde_requisitos():
    """Recibe los requisitos estructurados capturados en el formulario por
    pasos y arma el prompt estructurado para el agente requirements_agent."""
    datos = request.get_json(silent=True)
    if not datos:
        return jsonify({"error": "Se esperaba un cuerpo JSON con los requisitos estructurados."}), 400

    prompt_estructurado = construir_prompt_estructurado(datos)
    print("Prompt estructurado generado:\n", prompt_estructurado)  # Para depuración
    try:
        resultado = generar_diagrama_completo(prompt_estructurado)
    except ValueError as e:
        # Prompt vacío o alguno de los agentes no devolvió un JSON parseable.
        return jsonify({"error": str(e)}), 502
    except Exception as e:
        return jsonify({"error": f"Error generando el diagrama: {e}"}), 500

    return jsonify(resultado)


@app.route("/api/generar-desde-documento", methods=["POST"])
def generar_desde_documento():
    """Recibe el caso de negocio en texto libre (panel Caso de Negocio) y
    ejecuta el pipeline business_case_agent -> requirements_agent -> DiagramAgent para devolver el diagrama."""
    datos = request.get_json(silent=True)
    documento = (datos or {}).get("documento", "")

    try:
        resultado = generar_diagrama_desde_documento(documento)
    except ValueError as e:
        # Documento vacío o alguno de los agentes no devolvió un JSON parseable.
        return jsonify({"error": str(e)}), 502
    except Exception as e:
        return jsonify({"error": f"Error generando el diagrama: {e}"}), 500

    return jsonify(resultado)


if __name__ == "__main__":
    app.run(debug=True, port=5000)