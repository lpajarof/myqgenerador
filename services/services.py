from langchain.agents import create_agent
import os
import re
import json

from services.business_case_agent import BusinessCaseAgent
from services.diagram_agent import DiagramAgent
from services.requirements_agent import RequirementsAgent


def contenido_a_texto(content) -> str:
    """Normaliza el `content` de un mensaje de LangChain a texto plano.

    Algunos modelos (p. ej. Claude con "extended thinking", como
    claude-sonnet-5) no devuelven `content` como string sino como una lista
    de bloques (thinking, text, tool_use, ...). Nos quedamos solo con los
    bloques de texto: son los únicos que sirven para parsear JSON o para
    pasarle la respuesta al siguiente agente. Esto además es obligatorio
    para el segundo caso, porque los bloques "thinking" solo son válidos
    dentro de mensajes de rol assistant en la API de Anthropic — si se
    reenvían tal cual dentro de un HumanMessage al siguiente agente, la API
    responde 400 ("thinking blocks may only be in `assistant` messages").
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        partes = []
        for bloque in content:
            if isinstance(bloque, str):
                partes.append(bloque)
            elif isinstance(bloque, dict) and bloque.get("type") == "text":
                partes.append(bloque.get("text", ""))
        return "".join(partes)
    return str(content) if content else ""


def extraer_bloque_json(texto: str) -> dict:
    """Extrae y parsea el primer bloque ```json ... ``` que aparezca en la
    respuesta de un agente. Si no hay bloque delimitado (el agente devolvió
    JSON "pelado"), intenta parsear el texto completo tal cual."""
    if not texto or not texto.strip():
        raise ValueError("El agente devolvió una respuesta vacía.")

    match = re.search(r"```json\s*(.*?)\s*```", texto, re.DOTALL)
    bloque = match.group(1) if match else texto.strip()

    if not bloque:
        # El bloque ```json ... ``` vino vacío (p. ej. la respuesta se
        # truncó por el límite de tokens del modelo antes de escribir el
        # contenido). json.loads("") da un error críptico, así que lo
        # convertimos en algo accionable.
        raise ValueError(
            "El agente devolvió un bloque JSON vacío (posible corte por límite "
            "de tokens de salida). Intenta de nuevo o reduce el tamaño de la "
            "arquitectura."
        )

    return json.loads(bloque)


def extraer_analisis(texto: str) -> str:
    """Quita el bloque ```json ... ``` embebido en la respuesta de un agente
    (si lo hay) y devuelve el texto explicativo restante, listo para
    mostrarse como Markdown en el panel de análisis."""
    if not texto:
        return ""
    return re.sub(r"```json\s*.*?```", "", texto, flags=re.DOTALL).strip()



def generar_arquitectura(prompt_estructurado: str) -> str:
    """Invoca al agente requirements_agent con los requisitos
    ya estructurados y devuelve su respuesta completa: sustentación
    arquitectónica + bloque JSON de la arquitectura propuesta.

    Pensada para ser llamada desde app.py con el prompt que arma
    `construir_prompt_estructurado`.
    """
    if not prompt_estructurado or not prompt_estructurado.strip():
        raise ValueError("prompt_estructurado no puede estar vacío.")

    agent_requirements = RequirementsAgent()
    respuesta = agent_requirements.get_response(prompt_estructurado)
    return contenido_a_texto(respuesta)


def generar_modelo_conceptual(texto_usuario: str) -> str:
    """Invoca al agente business_case_agent (Data & Business Analyst) con el caso de negocio en
    texto libre y devuelve el modelo conceptual (YAML) generado tal cual,
    para pasarlo como entrada al requirements_agent.

    Pensada para ser llamada desde app.py con el texto que llega de la
    ruta `/api/generar-desde-documento`.
    """
    if not texto_usuario or not texto_usuario.strip():
        raise ValueError("texto_usuario no puede estar vacío.")

    business_case_agent = BusinessCaseAgent()
    respuesta = business_case_agent.get_response(texto_usuario)
    return contenido_a_texto(respuesta)


def _invocar_agente_3(texto_entrada: str) -> dict:
    """Invoca al agente DiagramAgent (Cloud Architecture Diagram Layout Designer) con
    una propuesta de arquitectura en texto (JSON del agente requirements_agent) y devuelve el diagrama con coordenadas,
    formas e iconos ya calculados."""

    diagram_agent = DiagramAgent()

    respuesta = diagram_agent.get_response(texto_entrada)
    return extraer_bloque_json(contenido_a_texto(respuesta))


def generar_diagrama_layout(arquitectura_json: dict) -> dict:
    """Invoca al Agente 3 con el objeto JSON de arquitectura lógica generado
    por el Agente 1 y devuelve el diagrama con layout calculado.

    Pensada para ser llamada desde app.py con el JSON que llega de la
    ruta `/api/generar-diagrama-layout`.
    """
    if not arquitectura_json or not isinstance(arquitectura_json, dict):
        raise ValueError("arquitectura_json debe ser un diccionario válido.")

    return _invocar_agente_3(json.dumps(arquitectura_json))


def generar_diagrama_completo(prompt_estructurado: str) -> dict:
    """Orquesta el pipeline completo a partir de los requisitos ya
    estructurados: requirements_agent (arquitectura lógica justificada) -> DiagramAgent
    (layout con coordenadas, formas e iconos). Devuelve un dict con:
    - "diagrama": nodes/edges/groups listos para el canvas.
    - "analisis": la sustentación arquitectónica (Markdown) del requirements_agent,
      para mostrar en el panel de análisis.
    """
    respuesta_agente_1 = generar_arquitectura(prompt_estructurado)
    arquitectura_json = extraer_bloque_json(respuesta_agente_1)
    return {
        "diagrama": generar_diagrama_layout(arquitectura_json),
        "analisis": extraer_analisis(respuesta_agente_1),
    }


def generar_diagrama_desde_documento(texto_usuario: str) -> dict:
    """Orquesta el pipeline completo a partir de un caso de negocio en texto
    libre: business_case_agent (extrae el modelo conceptual) -> requirements_agent (arquitectura lógica justificada) -> DiagramAgent (layout con
    coordenadas e iconos). Devuelve un dict con:
    - "diagrama": nodes/edges/groups listos para el canvas.
    - "analisis": la sustentación arquitectónica (Markdown) del requirements_agent,
      para mostrar en el panel de análisis.
    """
    modelo_conceptual = generar_modelo_conceptual(texto_usuario)
    diagrama = _invocar_agente_3(modelo_conceptual)

    # El Agente 2 a veces ya envuelve su propia salida en ```yaml ... ```;
    # quitamos esas fences antes de volver a envolverla nosotros, para no
    # terminar con un bloque de código anidado dos veces.
    modelo_sin_fences = re.sub(r"^```[a-zA-Z]*\n?|\n?```$", "", modelo_conceptual.strip())
    analisis = f"## Modelo Conceptual Extraído (Agente 2)\n\n```yaml\n{modelo_sin_fences.strip()}\n```"

    return {
        "diagrama": diagrama,
        "analisis": analisis,
    }