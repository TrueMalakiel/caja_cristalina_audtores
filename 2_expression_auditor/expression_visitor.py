"""
FILE: expression_auditor/expression_visitor.py
RESPONSABILIDAD: Expression-Level Slicing. Extrae el micro-linaje de ecuaciones físicas.
ARQUITECTURA: SOLID - Modo Suspendido (Context-Aware) y Sub-Visitors Recursivos.
"""

import ast
import logging
import fnmatch
from typing import Set, List

# Importamos los contratos de datos (Asumimos que lineage_schema.py fue duplicado en esta carpeta)
from expression_auditor.lineage_schema import LineageGraph, FunctionNode, DataSpoke

# Fail-Safe I/O: Intentar importar configuraciones, aplicar fallback si aún no existe el módulo
try:
    from expression_auditor.config import PHYSICAL_VARIABLE_PATTERNS
except ImportError:
    logging.warning("No se encontró expression_auditor.config. Usando patrones físicos por defecto.")
    PHYSICAL_VARIABLE_PATTERNS = [
        "*.poes*", "*.eur*", "*.q0*", "*area*", "*thickness*", 
        "*porosity*", "*permeability*", "*viscosity*", "*phi*", "*sw*"
    ]

logger = logging.getLogger(__name__)


class RHSVariableExtractor(ast.NodeVisitor):
    """
    HU-2.2: Sub-visitor recursivo dedicado exclusivamente a recorrer el 
    Lado Derecho (Right-Hand Side) de una asignación para recolectar dependencias.
    """
    def __init__(self):
        self.extracted_names: Set[str] = set()

    def visit_Name(self, node: ast.Name):
        self.extracted_names.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        try:
            # Aprovechamos ast.unparse para obtener la cadena completa (ej. self.facies.porosity)
            self.extracted_names.add(ast.unparse(node))
        except Exception:
            pass # Ignoramos fallos silenciosamente (Fail-Safe)
            
        # Continuamos bajando en el árbol para atrapar sub-atributos.
        # El filtro posterior se encargará de descartar las partes irrelevantes (como "self").
        self.generic_visit(node)

    def get_physical_variables(self) -> List[str]:
        """
        HU-2.3: Filtra las variables recolectadas usando la configuración de dominio.
        Ignora variables de control (i, j, temp) manteniendo solo magnitudes físicas.
        """
        physical_vars = set()
        for name in self.extracted_names:
            for pattern in PHYSICAL_VARIABLE_PATTERNS:
                # Evaluamos coincidencia por comodín o si la palabra clave está dentro del nombre
                if fnmatch.fnmatch(name, pattern) or pattern.replace("*", "") in name:
                    physical_vars.add(name)
                    break
        return list(physical_vars)


class ExpressionVisitor(ast.NodeVisitor):
    """
    HU-2.1: Visitor principal operando en "Modo Suspendido".
    Recorre todo el archivo, pero solo activa la extracción de ecuaciones
    cuando entra en el scope de una función objetivo.
    """
    def __init__(self, graph: LineageGraph, current_filepath: str, target_functions: List[str]):
        self.graph = graph
        self.current_filepath = current_filepath
        self.target_functions = set(target_functions)
        
        # Flags de estado para Modo Suspendido
        self.in_target_function = False
        self.current_function_name = ""

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Activa el modo de extracción si la función está en el índice RDF."""
        previous_state = self.in_target_function
        previous_func = self.current_function_name

        if node.name in self.target_functions:
            self.in_target_function = True
            self.current_function_name = node.name
            logger.debug(f"Modo Extracción ACTIVADO para la función: {node.name}")

        self.generic_visit(node)

        # Restaurar estado al salir del scope de la función
        self.in_target_function = previous_state
        self.current_function_name = previous_func

    def _process_equation(self, lhs_node: ast.AST, rhs_node: ast.AST, lineno: int):
        """Lógica centralizada para construir el grafo de la ecuación."""
        try:
            # HU-2.4: Generación de identificadores legibles
            lhs_str = ast.unparse(lhs_node).strip()
            rhs_str = ast.unparse(rhs_node).strip()

            # HU-2.2: Extraer dependencias de entrada
            extractor = RHSVariableExtractor()
            extractor.visit(rhs_node)
            
            # HU-2.3: Filtrar dependencias físicas
            physical_inputs = extractor.get_physical_variables()

            # Verificar si el LHS (resultado) es una variable física
            is_lhs_physical = any(
                fnmatch.fnmatch(lhs_str, pattern) or pattern.replace("*", "") in lhs_str 
                for pattern in PHYSICAL_VARIABLE_PATTERNS
            )

            # Si la ecuación no involucra variables físicas ni de entrada ni de salida, la ignoramos
            if not physical_inputs and not is_lhs_physical:
                return

            # HU-2.4: Crear Nodo Operador (Ecuación)
            equation_uid = f"{lhs_str} = {rhs_str}"
            eq_node = FunctionNode(
                uid=equation_uid,
                file_origin=self.current_filepath,
                line_number=lineno,
                node_type="Equation"
            )
            self.graph.add_node(eq_node)

            # HU-2.5: Conectar el destino (LHS) como Output (Generates)
            lhs_spoke = DataSpoke(
                uid=lhs_str,
                semantic_path=lhs_str,
                file_origin=self.current_filepath,
                line_number=lineno
            )
            self.graph.add_spoke(lhs_spoke)
            self.graph.add_edge_generates(eq_node.uid, lhs_spoke.uid)

            # HU-2.5: Conectar los orígenes (RHS) como Inputs (Consumes)
            for physical_input in physical_inputs:
                rhs_spoke = DataSpoke(
                    uid=physical_input,
                    semantic_path=physical_input,
                    file_origin=self.current_filepath,
                    line_number=lineno
                )
                self.graph.add_spoke(rhs_spoke)
                self.graph.add_edge_consumes(rhs_spoke.uid, eq_node.uid)

        except Exception as error:
            logger.warning(
                f"[Fail-Safe] Falla al procesar ecuación en línea {lineno} "
                f"de {self.current_filepath}. Detalle: {error}"
            )

    def visit_Assign(self, node: ast.Assign):
        """Procesa asignaciones estándar (ej. a = b + c)"""
        if self.in_target_function:
            for target in node.targets:
                self._process_equation(target, node.value, node.lineno)
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign):
        """Procesa asignaciones aumentadas (ej. a += b)"""
        if self.in_target_function:
            self._process_equation(node.target, node.value, node.lineno)
        self.generic_visit(node)