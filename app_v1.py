from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Definición de los pasos del formulario para dinámicas de UI
STEPS = [
    {"num": 1, "title": "Objetivos Estratégicos"},
    {"num": 2, "title": "Características de los Datos"},
    {"num": 3, "title": "Capas Tecnológicas Requeridas"},
    {"num": 4, "title": "Generar Configuración"}
]

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Captura de datos del formulario
        form = request.form
        
        # Procesamiento y formateo de la plantilla final para el Agente de IA
        output_prompt = f"""PROVEEDOR CLOUD PREFERIDO: {form.get('cloud_provider', 'No especificado')}

OBJETIVOS ESTRATÉGICOS:
- {form.get('objetivos_negocio', 'No especificado')}
- {form.get('iniciativas_datos', 'No especificado')}

1. CARACTERÍSTICAS DE LOS DATOS:
- Fuentes de Información:
  * Orígenes y tipos: {form.get('fuentes_origen', 'No especificado')}
  * Criticidad: {form.get('criticidad_fuentes', 'No especificado')}
- Volumetría:
  * Registros estimados: {form.get('vol_registros', 'No especificado')}
  * Almacenamiento total: {form.get('vol_almacenamiento', 'No especificado')}
  * Crecimiento anual esperado: {form.get('vol_crecimiento', 'No especificado')}
- Frecuencia de Actualización: {form.get('frecuencia_actualizacion', 'No especificado')}
- Disponibilidad Requerida:
  * Horario de operación: {form.get('disp_horario', 'No especificado')}
  * SLA esperado: {form.get('disp_sla', 'No especificado')}
  * Tiempo de indisponibilidad máx (RTO): {form.get('disp_rto', 'No especificado')}
- Latencia Máxima Aceptable: {form.get('latencia_maxima', 'No especificado')}
- Retención de Información: {form.get('retencion_info', 'No especificado')}

CAPAS DE LA ARQUITECTURA DISPONIBLES (Requerimientos específicos):
- Captura e Ingesta: {form.get('capa_ingesta', 'No especificado')}
- Almacenamiento: {form.get('capa_almacenamiento', 'No especificado')}
- Procesamiento: {form.get('capa_procesamiento', 'No especificado')}
- Gobierno de Datos: {form.get('capa_gobierno', 'No especificado')}
- Seguridad: {form.get('capa_seguridad', 'No especificado')}
- Consumo: {form.get('capa_consumo', 'No especificado')}
- Operación: {form.get('capa_operacion', 'No especificado')}"""

        return render_template("index_v1.html", steps=STEPS, result=output_prompt, form_data=form)
        
    return render_template("index_v1.html", steps=STEPS, result=None, form_data={})

if __name__ == "__main__":
    app.run(debug=True, port=5000)