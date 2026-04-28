"""
FILE: external_auditor/lineage_schema.py
RESPONSABILIDAD: Definición de los contratos de datos (SSoT) para el grafo de linaje.
ARQUITECTURA: SOLID - Schema-First, Inmutabilidad estricta (frozen=True).
"""

from dataclasses import dataclass, field
from typing import Dict, Set

@dataclass(frozen=True)
class FunctionNode:
    """
    Representa un Nodo de Función en el grafo bipartito.
    Puede ser una función estándar, un método de clase, un validador Pydantic,
    una propiedad dinámica (@property) o una llamada a una librería externa.
    """
    uid: str
    file_origin: str
    line_number: int
    node_type: str = "Standard"  # Tipos: Standard, Property, Validator, External, Inferred_Call, Super_Call


@dataclass(frozen=True)
class DataSpoke:
    """
    Representa un Atributo de Dato (Spoke) en el grafo bipartito.
    Encapsula la variable o el atributo de clase rastreado a lo largo del pipeline.
    """
    uid: str
    semantic_path: str
    file_origin: str
    line_number: int


@dataclass
class LineageGraph:
    """
    Estructura de datos intermedia y agnóstica que actúa como puente 
    entre el analizador de código (AST Walker) y el generador de ontologías (RDF Builder).
    Maneja las relaciones de adyacencia de forma segura.
    """
    nodes: Dict[str, FunctionNode] = field(default_factory=dict)
    spokes: Dict[str, DataSpoke] = field(default_factory=dict)
    
    # Listas de Adyacencia Direccionales (Nodos Bipartitos)
    # Diccionarios que mapean un UID de origen hacia un Set de UIDs de destino (evita duplicados)
    generates: Dict[str, Set[str]] = field(default_factory=dict)  # node_uid -> Set[spoke_uid]
    consumes: Dict[str, Set[str]] = field(default_factory=dict)   # spoke_uid -> Set[node_uid]

    def add_node(self, node: FunctionNode) -> None:
        """Registra o actualiza un nodo de función en el grafo."""
        self.nodes[node.uid] = node

    def add_spoke(self, spoke: DataSpoke) -> None:
        """Registra o actualiza un atributo de dato en el grafo."""
        self.spokes[spoke.uid] = spoke

    def add_edge_generates(self, node_uid: str, spoke_uid: str) -> None:
        """
        Crea una arista direccional indicando que una Función (Nodo)
        genera, retorna o muta a un Dato (Spoke).
        """
        if node_uid not in self.generates:
            self.generates[node_uid] = set()
        self.generates[node_uid].add(spoke_uid)

    def add_edge_consumes(self, spoke_uid: str, node_uid: str) -> None:
        """
        Crea una arista direccional indicando que un Dato (Spoke)
        es utilizado como input o consumido por una Función (Nodo).
        """
        if spoke_uid not in self.consumes:
            self.consumes[spoke_uid] = set()
        self.consumes[spoke_uid].add(node_uid)