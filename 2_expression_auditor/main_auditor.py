"""
FILE: expression_auditor/main_auditor.py
RESPONSABILIDAD: CLI y Orquestador del Expression-Level Slicing Auditor.
ARQUITECTURA: SOLID - Orquestador Puro (Delega a Parsers, Visitors y Generators).
"""

import argparse
import sys
import logging
import ast
from pathlib import Path

# [FIX ARQUITECTÓNICO CRÍTICO]: Inyección dinámica del PYTHONPATH
# Permite ejecutar el script desde la terminal sin romper las importaciones absolutas.
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Configuración de constantes para códigos de salida
EXIT_SUCCESS = 0
EXIT_ERROR = 1

# Configuración de Logging Industrial
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] EXP_AUDITOR: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

def parse_cli_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Expression Auditor - Micro-Linaje de Ecuaciones Físicas para EUR Simulator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--project-root", 
        required=True, 
        help="Ruta absoluta o relativa a la raíz del proyecto (necesaria para resolver paths)."
    )
    parser.add_argument(
        "--rdf", 
        required=True, 
        help="Ruta al archivo lineage_output.xml generado por external_auditor."
    )
    parser.add_argument(
        "--output", 
        default="physical_edges.csv", 
        help="Archivo destino CSV para el grafo de ecuaciones."
    )
    return parser.parse_args()

def validate_io_paths(project_root_str: str, rdf_path_str: str) -> bool:
    """Fail-Safe I/O: Pre-validación de los recursos en disco."""
    project_root_path = Path(project_root_str).resolve()
    if not project_root_path.exists() or not project_root_path.is_dir():
        logger.error(f"Root Cause: El directorio raíz del proyecto no existe -> {project_root_path}")
        return False

    rdf_full_path = Path(rdf_path_str).resolve()
    if not rdf_full_path.exists() or not rdf_full_path.is_file():
        logger.error(f"Root Cause: El archivo RDF de índice no se encuentra -> {rdf_full_path}")
        return False

    return True

def main() -> int:
    args = parse_cli_arguments()
    logger.info("Iniciando Expression-Level Slicing Auditor...")
    
    # 1. Validación de Rutas
    if not validate_io_paths(args.project_root, args.rdf):
        return EXIT_ERROR

    # 2. Carga Segura de Dependencias Internas (Despliegue Modular)
    try:
        from expression_auditor.lineage_schema import LineageGraph
        from expression_auditor.rdf_parser import RDFIndexParser
        from expression_auditor.expression_visitor import ExpressionVisitor
        from expression_auditor.rdf_builder import RDFGenerator
    except ImportError as e:
        logger.error(
            f"Root Cause: Faltan submódulos estructurales de expression_auditor. Detalle: {e}"
        )
        return EXIT_ERROR

    # 3. Fase 1: Extracción del Índice desde RDF
    logger.info("Fase 1: Extrayendo índice de funciones objetivo desde RDF...")
    index_parser = RDFIndexParser(args.rdf)
    targets_by_file = index_parser.parse_and_group_by_file()

    if not targets_by_file:
        logger.warning("No se identificaron archivos a procesar. Verifique el archivo RDF provisto.")
        return EXIT_SUCCESS

    # 4. Fase 2: Slicing de Expresiones (Micro-Linaje)
    logger.info("Fase 2: Ejecutando Expression-Level Slicing sobre el código fuente...")
    global_graph = LineageGraph()
    project_root_path = Path(args.project_root).resolve()
    
    files_processed = 0
    
    # Iteramos archivo por archivo, instanciando un visitor para cada uno
    for file_rel_path, target_functions in targets_by_file.items():
        full_path = project_root_path / file_rel_path

        if not full_path.exists():
            logger.warning(f"[Fail-Safe] Archivo fuente no encontrado: {full_path}. Omitiendo Slicing.")
            continue

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                source_code = f.read()

            tree = ast.parse(source_code, filename=str(full_path))
            
            # Pasamos la lista de funciones que este visitor debe activar en Modo Suspendido
            visitor = ExpressionVisitor(global_graph, file_rel_path, target_functions)
            visitor.visit(tree)
            
            files_processed += 1
            
        except SyntaxError as e:
            logger.error(f"Root Cause: Error de sintaxis parseando {file_rel_path}. Detalle: {e}")
        except Exception as e:
            logger.error(f"Root Cause: Excepción no controlada en visitor para {file_rel_path}. Detalle: {e}")

    total_equations = len([n for n in global_graph.nodes.values() if getattr(n, "node_type", "") == "Equation"])
    total_spokes = len(global_graph.spokes)
    logger.info(f"Slicing completado en {files_processed} archivos. Ecuaciones: {total_equations}, Variables Físicas: {total_spokes}.")

    # 5. Fase 3: Construcción y Exportación del CSV
    logger.info("Fase 3: Exportando grafo físico de ecuaciones...")
    try:
        generator = RDFGenerator(global_graph)
        # Delegamos a la exportación específica de CSV
        generator.export(output_path_str=args.output, format_type="csv")
        logger.info(f"Auditoría de expresiones finalizada con éxito. Output -> {args.output}")
    except Exception as e:
        logger.error(f"Root Cause: Fallo durante la exportación del CSV: {e}")
        return EXIT_ERROR

    return EXIT_SUCCESS

if __name__ == "__main__":
    sys.exit(main())