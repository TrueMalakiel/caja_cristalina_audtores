"""
FILE: external_auditor/ast_explorer.py
RESPONSABILIDAD: Análisis de Flujo de Datos por Rebanado Inverso y Resolución Estática de Herencia.
ARQUITECTURA: SOLID - Arquitectura de 2-Pasadas (1. Discovery de Jerarquía, 2. Extracción de Linaje).
"""

import ast
import logging
from pathlib import Path
from typing import Optional, Set, Dict, Any, List

from external_auditor.lineage_schema import LineageGraph, FunctionNode, DataSpoke

# Carga segura de módulos acoplados (Fail-Safe)
try:
    from external_auditor.inspect_pydantic import safe_extract_schema_metadata
except ImportError:
    safe_extract_schema_metadata = None

try:
    from external_auditor.inheritance_resolver import StaticInheritanceResolver
except ImportError:
    StaticInheritanceResolver = None

# Constante Centralizada (Idealmente se importaría de config.py, pero se mantiene para aislamiento)
from external_auditor.config import STD_LIBS_AND_EXTERNALS

logger = logging.getLogger(__name__)


# ==============================================================================
# PASS 1: DISCOVERY DE JERARQUÍA (ÉPICA 1)
# ==============================================================================
class HierarchyVisitor(ast.NodeVisitor):
    """
    HU-1.1 y HU-1.2: Recorre el AST exclusivamente para mapear importaciones,
    registrar clases, sus bases resueltas y los métodos que definen.
    """
    def __init__(self, current_filepath: str, module_name: str, class_hierarchy: Dict, walker: 'ProjectWalker'):
        self.current_filepath = current_filepath
        self.module_name = module_name
        self.class_hierarchy = class_hierarchy
        self.walker = walker
        self.import_map: Dict[str, str] = {}
        self.current_class_context: Optional[str] = None

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module and node.module.split('.')[0] not in STD_LIBS_AND_EXTERNALS:
            for alias in node.names:
                local_name = alias.asname or alias.name
                self.import_map[local_name] = f"{node.module}.{alias.name}"
            self.walker.queue_import(node.module)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            if alias.name.split('.')[0] not in STD_LIBS_AND_EXTERNALS:
                local_name = alias.asname or alias.name
                self.import_map[local_name] = alias.name
                self.walker.queue_import(alias.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        full_class_name = f"{self.module_name}.{node.name}"
        previous_class = self.current_class_context
        self.current_class_context = full_class_name

        resolved_bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                if base.id in self.import_map:
                    resolved_bases.append(self.import_map[base.id])
                else:
                    resolved_bases.append(f"{self.module_name}.{base.id}")
            elif isinstance(base, ast.Attribute):
                base_str = self._extract_semantic_name(base)
                resolved_bases.append(f"external.{base_str}")

        self.class_hierarchy[full_class_name] = {
            "bases": resolved_bases,
            "methods": set(),
            "file": self.current_filepath
        }

        if safe_extract_schema_metadata:
            full_file_path = str(Path(self.walker.project_root) / self.current_filepath)
            reflex_metadata = safe_extract_schema_metadata(full_file_path, self.module_name)
            for prop in reflex_metadata.get("properties", []):
                self.class_hierarchy[full_class_name]["methods"].add(prop)
            for val in reflex_metadata.get("validators", []):
                self.class_hierarchy[full_class_name]["methods"].add(val)

        self.generic_visit(node)
        self.current_class_context = previous_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if self.current_class_context:
            self.class_hierarchy[self.current_class_context]["methods"].add(node.name)
        self.generic_visit(node)

    def _extract_semantic_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            base_name = self._extract_semantic_name(node.value)
            return f"{base_name}.{node.attr}" if base_name else node.attr
        return ""


# ==============================================================================
# PASS 2: EXTRACCIÓN DE LINAJE (ÉPICA 2 & 3)
# ==============================================================================
class LineageASTVisitor(ast.NodeVisitor):
    """
    HU-2.2: Recorre el AST construyendo el grafo bipartito. 
    Usa el StaticInheritanceResolver para encontrar los métodos canónicos y colapsar nodos.
    """
    def __init__(self, graph: LineageGraph, current_filepath: str, module_name: str, walker: 'ProjectWalker'):
        self.graph = graph
        self.current_filepath = current_filepath
        self.module_name = module_name
        self.walker = walker
        self.resolver = walker.resolver
        self.current_function_context = "global"
        self.current_class_context = "global"

    def _resolve_call_canonical_uid(self, func_node: ast.AST) -> str:
        func_name = self._extract_semantic_name(func_node)
        if not isinstance(func_node, ast.Attribute):
            return func_name

        receptor_str = self._extract_semantic_name(func_node.value)
        method_name = func_node.attr

        if self.resolver and self.current_class_context != "global":
            if receptor_str in ("self", "super()"):
                owner = self.resolver.find_canonical_method_owner(self.current_class_context, method_name)
                if owner:
                    return f"{owner}.{method_name}"
        return func_name

    def visit_ClassDef(self, node: ast.ClassDef):
        previous_class = self.current_class_context
        self.current_class_context = f"{self.module_name}.{node.name}"

        if safe_extract_schema_metadata:
            full_file_path = str(Path(self.walker.project_root) / self.current_filepath)
            reflex_metadata = safe_extract_schema_metadata(full_file_path, self.module_name)
            
            for prop_name in reflex_metadata.get("properties", []):
                owner = self.current_class_context
                if self.resolver:
                    owner = self.resolver.find_canonical_method_owner(self.current_class_context, prop_name) or owner
                prop_uid = f"{owner}.{prop_name}"
                virtual_node = FunctionNode(uid=prop_uid, file_origin=self.current_filepath, line_number=node.lineno, node_type="Property")
                self.graph.add_node(virtual_node)
                
            for val_name in reflex_metadata.get("validators", []):
                owner = self.current_class_context
                if self.resolver:
                    owner = self.resolver.find_canonical_method_owner(self.current_class_context, val_name) or owner
                val_uid = f"{owner}.{val_name}"
                virtual_node = FunctionNode(uid=val_uid, file_origin=self.current_filepath, line_number=node.lineno, node_type="Validator")
                self.graph.add_node(virtual_node)

        self.generic_visit(node)
        self.current_class_context = previous_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        previous_function = self.current_function_context
        
        if self.current_class_context != "global":
            owner = self.current_class_context
            if self.resolver:
                owner = self.resolver.find_canonical_method_owner(self.current_class_context, node.name) or owner
            self.current_function_context = f"{owner}.{node.name}"
        else:
            self.current_function_context = node.name
            
        func_node = FunctionNode(uid=self.current_function_context, file_origin=self.current_filepath, line_number=node.lineno, node_type="Standard")
        self.graph.add_node(func_node)
        
        self.generic_visit(node)
        self.current_function_context = previous_function

    def visit_Assign(self, node: ast.Assign):
        generator_uid = None

        if isinstance(node.value, ast.Call):
            generator_uid = self._resolve_call_canonical_uid(node.value.func)
            
            base_module = generator_uid.split('.')[0] if generator_uid else ""
            if base_module in STD_LIBS_AND_EXTERNALS:
                ext_node = FunctionNode(uid=generator_uid, file_origin="External", line_number=0, node_type="External")
                self.graph.add_node(ext_node)
            elif generator_uid:
                self.graph.add_node(FunctionNode(uid=generator_uid, file_origin=self.current_filepath, line_number=node.lineno, node_type="Inferred_Call"))
            
            if node.value.keywords:
                for kwarg in node.value.keywords:
                    if kwarg.arg:
                        kwarg_spoke_uid = f"{generator_uid}.{kwarg.arg}"
                        spoke = DataSpoke(uid=kwarg_spoke_uid, semantic_path=kwarg_spoke_uid, file_origin=self.current_filepath, line_number=node.lineno)
                        self.graph.add_spoke(spoke)
                        self.graph.add_edge_consumes(spoke.uid, generator_uid)

        for target_node in node.targets:
            spoke_uid = self._extract_semantic_name(target_node)
            if not spoke_uid:
                continue
                
            data_spoke = DataSpoke(uid=spoke_uid, semantic_path=spoke_uid, file_origin=self.current_filepath, line_number=node.lineno)
            self.graph.add_spoke(data_spoke)
            
            if generator_uid:
                self.graph.add_edge_generates(generator_uid, data_spoke.uid)
                
            if self.current_function_context != "global":
                self.graph.add_edge_consumes(data_spoke.uid, self.current_function_context)

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        canonical_uid = self._resolve_call_canonical_uid(node.func)
        func_name_raw = self._extract_semantic_name(node.func)
        
        if "super()." in func_name_raw and self.current_function_context != "global":
            super_node = FunctionNode(uid=canonical_uid, file_origin=self.current_filepath, line_number=node.lineno, node_type="Super_Call")
            self.graph.add_node(super_node)
            
            dummy_spoke = f"{canonical_uid}_Result"
            self.graph.add_edge_generates(func_node_uid=canonical_uid, spoke_uid=dummy_spoke)
            self.graph.add_edge_consumes(spoke_uid=dummy_spoke, node_uid=self.current_function_context)

        self.generic_visit(node)

    def _extract_semantic_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            base_name = self._extract_semantic_name(node.value)
            return f"{base_name}.{node.attr}" if base_name else node.attr
        elif isinstance(node, ast.Subscript):
            base_name = self._extract_semantic_name(node.value)
            if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                return f"{base_name}.{node.slice.value}"
            return base_name
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "super":
                return "super()"
            return self._extract_semantic_name(node.func)
        return ""


# ==============================================================================
# ORQUESTADOR DEL WALKER (ÉPICA 1.3)
# ==============================================================================
class ProjectWalker:
    """
    Orquestador de 2 Pasadas. 
    Asegura que la jerarquía esté completamente descubierta antes de inferir linaje.
    """
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.visited_modules: Dict[str, str] = {}  
        self.import_queue: Set[str] = set()
        
        self.class_hierarchy: Dict[str, Dict] = {}
        self.resolver = None
        self.graph = LineageGraph()

    def queue_import(self, module_notation: str) -> None:
        if module_notation not in self.visited_modules:
            self.import_queue.add(module_notation)

    def explore_file(self, rel_path: str) -> None:
        """
        [CORRECCIÓN DE INTEGRACIÓN]: Wrapper de compatibilidad para mantener 
        el contrato original de main_auditor.py. 
        """
        module_notation = rel_path.replace('.py', '').replace('/', '.').replace('\\', '.')
        self.explore_project(module_notation)

    def explore_project(self, entry_module: str) -> None:
        """Punto de entrada. Ejecuta el Discovery (Pass 1) y luego el Slicing (Pass 2)."""
        self.queue_import(entry_module)

        logger.info("Iniciando PASS 1: Discovery de Jerarquías de Clases y Dependencias...")
        while self.import_queue:
            module_notation = self.import_queue.pop()
            if module_notation in self.visited_modules:
                continue
            self._parse_file_pass1(module_notation)

        logger.info(f"PASS 1 completado. Clases descubiertas: {len(self.class_hierarchy)}")

        if StaticInheritanceResolver:
            self.resolver = StaticInheritanceResolver(self.class_hierarchy)
            logger.info("StaticInheritanceResolver inicializado exitosamente.")

        logger.info("Iniciando PASS 2: Extracción de Linaje y Graph Folding...")
        for module_notation, filepath in self.visited_modules.items():
            self._parse_file_pass2(module_notation, filepath)

    def _parse_file_pass1(self, module_notation: str) -> None:
        rel_path = module_notation.replace('.', '/') + '.py'
        full_path = (self.project_root / rel_path).resolve()
        
        if not full_path.exists() or not full_path.is_file():
            return

        self.visited_modules[module_notation] = rel_path
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(full_path))
            visitor = HierarchyVisitor(rel_path, module_notation, self.class_hierarchy, self)
            visitor.visit(tree)
        except Exception as e:
            logger.error(f"Root Cause: Falla estructural en Pass 1 para {rel_path}. Detalle: {e}")

    def _parse_file_pass2(self, module_notation: str, rel_path: str) -> None:
        full_path = (self.project_root / rel_path).resolve()
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(full_path))
            visitor = LineageASTVisitor(self.graph, rel_path, module_notation, self)
            visitor.visit(tree)
        except Exception as e:
            logger.error(f"Root Cause: Falla de extracción en Pass 2 para {rel_path}. Detalle: {e}")