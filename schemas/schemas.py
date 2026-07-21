from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class Node(BaseModel):
    id: int = Field(description="ID único del nodo.")
    label: str = Field(description="Nombre visible del componente.")
    type: Literal["rect", "ellipse", "db", "queue"] = Field(description="Forma geométrica del nodo.")
    x: float = Field(description="Coordenada horizontal.")
    y: float = Field(description="Coordenada vertical.")
    ci: int = Field(description="Identificador de categoría o capa visual.")
    groupId: Optional[int] = Field(None, description="ID del grupo al que pertenece.")
    icon: str = Field(description="Ruta del icono relativo al proveedor.")

class Edge(BaseModel):
    id: int = Field(description="ID único de la conexión.")
    from_node: int = Field(..., alias="from", description="ID del nodo origen.")
    to: int = Field(description="ID del nodo destino.")
    label: str = Field(description="Texto descriptivo sobre la línea.")
    color: str = Field(description="Color en formato HEX.")
    thickness: float = Field(description="Grosor de la línea.")
    lineStyle: Literal["solid", "dashed", "dotted"] = Field(description="Estilo visual.")
    startArrow: Literal["none", "arrow", "dot", "bar", "dia"] = Field(description="Flecha inicio.")
    endArrow: Literal["none", "arrow", "dot", "bar", "dia"] = Field(description="Flecha final.")

    class Config:
        populate_by_name = True

class Group(BaseModel):
    id: int = Field(description="ID único del grupo.")
    label: str = Field(description="Nombre de la sección.")
    x: float; y: float; w: float; h: float
    ci: int

class ArchitectureDiagram(BaseModel):
    nodes: List[Node]
    edges: List[Edge]
    groups: List[Group]
    nid: int; eid: int; gid: int