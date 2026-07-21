# from utils.models_IA import ModelsIA
# from dotenv import load_dotenv
# import os
# from langchain.agents import create_agent
# from langchain.messages import HumanMessage
# import time

# load_dotenv()  # Load environment variables from .env file
# model = os.environ.get("MODEL")


# ModelsIA_instance = ModelsIA(model_env=model)
# print("Modelo:", ModelsIA_instance.get_model())

# agente = create_agent(
#     model=ModelsIA_instance.get_model(),
#     tools=[]
# )

# query = {"messages": [HumanMessage(content="¿Quien es Zeus?")]}

# start_time = time.time()
# response = agente.invoke(query)
# end_time = time.time()

# print("Respuesta del agente:", response["messages"][-1].content)
# print(f"Tiempo de ejecución: {end_time - start_time:.2f} segundos")


from services.business_case_agent import BusinessCaseAgent
from services.requirements_agent import RequirementsAgent

from dotenv import load_dotenv


load_dotenv()  # Carga las variables de entorno desde el archivo .env


# 1. Instancias el agente (lee el prompt e inicializa Ollama internamente)
agent_requirements = RequirementsAgent()
agent_business_case = BusinessCaseAgent()
agent_requirements_2 = RequirementsAgent()  # Ejemplo de uso con un modelo específico

# 2. Consumes la respuesta cuando lo necesites
user_story = """
PROVEEDOR CLOUD PREFERIDO: Azure

OBJETIVOS ESTRATÉGICOS:
- Aumentar los clientes
- Reportes en powerBI para el seguimento a campañas

1. CARACTERÍSTICAS DE LOS DATOS:
- Fuentes de Información:
  * Orígenes y tipos: SAP ERP Oracle DB, MySQL
  * Criticidad: SAP crítica
- Volumetría:
  * Registros estimados: 100k transacciones diarias
  * Almacenamiento total: No especificado
  * Crecimiento anual esperado: No especificado
- Frecuencia de Actualización: Batch (Diario)
- Disponibilidad Requerida:
  * Horario de operación: No especificado
  * SLA esperado: 99.9% SLA
  * Tiempo de indisponibilidad máx (RTO): No especificado
- Latencia Máxima Aceptable: No especificado
- Retención de Información: No especificado

CAPAS DE LA ARQUITECTURA DISPONIBLES (Requerimientos específicos):
- Captura e Ingesta: Captura de datos desde base de datos relacional y API REST
- Almacenamiento: Landing, Bronze, Silver, Gold, datawarehousing analitico
- Procesamiento: ETLs con databricks
- Gobierno de Datos: No especificado
- Seguridad: No especificado
- Consumo: Reportes BI, endpoints API consumo de ML
- Operación: No especificado
"""
respuesta_agente_1 = agent_requirements.get_response(user_story)
respuesta_agente_2 = agent_business_case.get_response(respuesta_agente_1)
respuesta_agente_3 = agent_requirements.get_response(respuesta_agente_2)


print(respuesta_agente_1)