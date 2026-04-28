"""
FILE: expression_auditor/rdf_parser.py
RESPONSABILIDAD: Leer el grafo RDF/XML del external_auditor y extraer las funciones objetivo.
ARQUITECTURA: SOLID - Data Access Layer (Agnóstico al AST).
"""

import logging
from pathlib import Path
from typing import Dict, List, Set
from rdflib import Graph

# Configuración del Logger
logger = logging.getLogger(__name__)

# Namespace base esperado en el RDF de entrada
EUR_BASE_URI = "http://www.damavzla.org/ontologies/eur_simulator#"


class RDFIndexParser:
    """
    Lee el archivo lineage_output.xml generado por el external_auditor
    y construye un índice agrupado por archivo (fileLocation) con los nombres
    de las funciones que el ExpressionVisitor debe inspeccionar.
    """

    def __init__(self, rdf_filepath_str: str):
        self.rdf_filepath = Path(rdf_filepath_str).resolve()
        self.graph = Graph()
        # Estructura: { "modules/archivo.py": ["calculate_poes", "update_state"] }
        self.targets_by_file: Dict[str, Set[str]] = {}

    def parse_and_group_by_file(self) -> Dict[str, List[str]]:
        """
        Ejecuta la lectura y consulta SPARQL. Retorna el índice maestro para el orquestador.
        """
        # 1. Fail-Safe I/O: Validación de existencia
        if not self.rdf_filepath.exists() or not self.rdf_filepath.is_file():
            logger.error(
                f"Root Cause: El archivo de índice RDF no existe o no es accesible -> {self.rdf_filepath}. "
                "Debe ejecutar el external_auditor primero."
            )
            return {}

        # 2. Fail-Safe I/O: Carga y Parseo del XML
        try:
            logger.info(f"Cargando índice RDF desde {self.rdf_filepath}...")
            self.graph.parse(str(self.rdf_filepath), format="xml")
        except Exception as error:
            logger.error(f"Root Cause: Falla al parsear el XML/RDF. Archivo corrupto o formato inválido. Detalle: {error}")
            return {}

        # 3. Extracción de Nodos mediante SPARQL
        sparql_query = """
        PREFIX eur: <http://www.damavzla.org/ontologies/eur_simulator#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?label ?fileLoc
        WHERE {
            ?node rdf:type eur:FunctionNode .
            ?node rdfs:label ?label .
            ?node eur:fileLocation ?fileLoc .
        }
        """
        
        try:
            query_results = self.graph.query(sparql_query)
            
            for row in query_results:
                raw_label = str(row.label)
                file_location = str(row.fileLoc)

                # Filtrar nodos que no pertenecen a nuestro código fuente
                if file_location == "External" or not file_location.endswith(".py"):
                    continue

                # Limpieza del label: Si es "UnifiedPhysicsEngine.calculate_poes", nos quedamos con "calculate_poes"
                # Esto facilita el match en ast.FunctionDef(name="calculate_poes")
                canonical_func_name = raw_label.split('.')[-1]

                # Agrupación por archivo
                if file_location not in self.targets_by_file:
                    self.targets_by_file[file_location] = set()
                
                self.targets_by_file[file_location].add(canonical_func_name)

            # Convertir Sets a Lists para inmutabilidad del contrato en fases posteriores
            final_index = {file_loc: list(funcs) for file_loc, funcs in self.targets_by_file.items()}
            
            total_targets = sum(len(funcs) for funcs in final_index.values())
            logger.info(f"Índice construido exitosamente: {total_targets} funciones objetivo agrupadas en {len(final_index)} archivos.")
            
            return final_index

        except Exception as error:
            logger.error(f"Root Cause: Fallo al ejecutar la consulta SPARQL sobre el grafo en memoria. Detalle: {error}")
            return {}