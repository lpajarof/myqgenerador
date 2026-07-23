"""Tool de resolución de iconos de arquitectura cloud.

El paquete `diagrams` trae originalmente una carpeta
`resources/<proveedor>/<categoria>/<servicio>.png` con los iconos oficiales
de AWS, Azure, GCP, on-prem, etc., pero vive dentro del entorno virtual
(`.venv/`), que no se sube al repositorio ni se despliega. Por eso esa
carpeta se copió a `static/images/icons/resources/` (sí versionada), que es
de donde se sirve en todos los entornos. Los agentes de LangChain no tienen
forma de "ver" ese sistema de archivos, así que suelen alucinar rutas de
icono plausibles pero inexistentes (p. ej. "azure/analytics/dynamics-365.png",
que no existe; el real es "azure/security/key-vaults.png" y no
"azure/security/key-vault.png"). Esta tool le da al agente una forma de
buscar en el índice real y devolver una ruta que sí existe.
"""

import difflib
import os
import re
from functools import lru_cache

from langchain_core.tools import tool

RESOURCES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "static", "images", "icons", "resources",
)

_PROVIDER_ALIASES = {
    "aws": "aws",
    "amazon": "aws",
    "amazon web services": "aws",
    "azure": "azure",
    "microsoft azure": "azure",
    "microsoft": "azure",
    "gcp": "gcp",
    "google cloud": "gcp",
    "google cloud platform": "gcp",
    "google": "gcp",
    "onprem": "onprem",
    "on-prem": "onprem",
    "on premise": "onprem",
    "on-premise": "onprem",
    "generic": "generic",
    "k8s": "k8s",
    "kubernetes": "k8s",
    "saas": "saas",
    "oci": "oci",
    "oracle": "oci",
    "ibm": "ibm",
    "alibaba": "alibabacloud",
    "alibaba cloud": "alibabacloud",
    "elastic": "elastic",
    "firebase": "firebase",
    "multi-cloud": "generic",
    "multi cloud": "generic",
    "multi-cloud / agnóstico": "generic",
}


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return text.strip()


def _tokens(text: str) -> set[str]:
    return set(_normalize(text).split())


@lru_cache(maxsize=1)
def _build_index() -> list[dict]:
    """Escanea resources/ una sola vez y arma un índice en memoria."""
    index = []
    if not os.path.isdir(RESOURCES_DIR):
        return index

    for root, _dirs, files in os.walk(RESOURCES_DIR):
        for filename in files:
            if not filename.lower().endswith(".png"):
                continue
            abs_path = os.path.join(root, filename)
            rel_path = os.path.relpath(abs_path, RESOURCES_DIR).replace(os.sep, "/")
            parts = rel_path.split("/")
            provider = parts[0] if len(parts) > 0 else ""
            category = parts[1] if len(parts) > 2 else ""
            service = os.path.splitext(filename)[0]
            index.append({
                "path": rel_path,
                "provider": provider,
                "category": category,
                "service": service,
                "tokens": _tokens(service) | _tokens(category),
            })
    return index


def _resolve_provider(provider: str | None) -> str | None:
    if not provider:
        return None
    key = _normalize(provider)
    if key in _PROVIDER_ALIASES:
        return _PROVIDER_ALIASES[key]
    # coincidencia por nombre de carpeta directo (p.ej. "gis", "openstack")
    known_providers = {entry["provider"] for entry in _build_index()}
    if key in known_providers:
        return key
    return None


def buscar_icono(component_name: str, provider: str | None = None, top_k: int = 5) -> dict:
    """Busca en la carpeta resources/ de `diagrams` la(s) ruta(s) de icono
    real(es) más parecidas a un componente/tecnología cloud.

    Args:
        component_name: Nombre del componente o tecnología a buscar
            (p. ej. "Data Factory", "Key Vault", "Power BI", "Dynamics 365").
        provider: Proveedor cloud preferido para acotar la búsqueda
            (aws | azure | gcp | onprem | generic | k8s | saas | ...).
            Si se omite, busca en todos los proveedores.
        top_k: Número máximo de coincidencias a devolver.

    Returns:
        dict con:
            - "best_match": ruta relativa (str) de la mejor coincidencia,
              lista para usar en el campo `icon` del nodo, o None si no
              hubo ninguna coincidencia razonable.
            - "candidates": lista de hasta `top_k` rutas candidatas
              ordenadas de mayor a menor similitud.
    """
    index = _build_index()
    if not index:
        return {
            "best_match": None,
            "candidates": [],
            "error": f"No se encontró la carpeta de recursos en {RESOURCES_DIR}",
        }

    resolved_provider = _resolve_provider(provider)
    pool = index
    if resolved_provider:
        scoped = [entry for entry in index if entry["provider"] == resolved_provider]
        if scoped:
            pool = scoped

    query_norm = _normalize(component_name)
    query_tokens = _tokens(component_name)

    scored = []
    for entry in pool:
        service_norm = _normalize(entry["service"])
        if query_tokens:
            # Similitud promedio: para cada palabra de la consulta, la mejor
            # coincidencia entre las palabras del nombre del icono. Evita que
            # cadenas cortas den "ratio" alto por azar (p. ej. "dynamics 365"
            # vs "genomics" con SequenceMatcher completo).
            per_token = [
                max((difflib.SequenceMatcher(None, qt, et).ratio() for et in entry["tokens"]), default=0.0)
                for qt in query_tokens
            ]
            token_score = sum(per_token) / len(per_token)
        else:
            token_score = 0.0
        substring_bonus = 0.15 if query_norm and query_norm in service_norm else 0.0
        score = token_score + substring_bonus
        scored.append((score, entry["path"]))

    scored.sort(key=lambda item: item[0], reverse=True)
    candidates = [path for score, path in scored[:top_k] if score > 0]
    best_match = candidates[0] if candidates and scored[0][0] >= 0.55 else None

    return {"best_match": best_match, "candidates": candidates}


@tool
def resolver_icono_cloud(component_name: str, provider: str | None = None) -> str:
    """Devuelve la ruta real de icono (formato 'proveedor/categoria/servicio.png')
    para un componente de arquitectura cloud, buscando en el índice real de
    iconos disponibles en el paquete `diagrams`. Úsala SIEMPRE antes de
    escribir el campo `icon` de un nodo: nunca inventes una ruta de icono a
    partir de tu conocimiento general, porque el archivo podría no existir.

    Args:
        component_name: Nombre del componente/tecnología (p. ej. "Azure Data
            Factory", "Key Vault", "Power BI", "S3", "BigQuery").
        provider: Proveedor cloud del componente (aws, azure, gcp, onprem,
            generic, k8s, saas, etc). Si no se conoce, se puede omitir.

    Returns:
        La ruta relativa del icono más parecido encontrado (str), o el
        string "null" si no se encontró ninguna coincidencia razonable
        (en ese caso el nodo debe usar `icon: null`).
    """
    result = buscar_icono(component_name, provider)
    return result["best_match"] or "null"
