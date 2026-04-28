"""
FILE: expression_auditor/rdf_builder.py
RESPONSABILIDAD: Generación de exportables (CSV) para el micro-linaje de ecuaciones físicas.
ARQUITECTURA: SOLID - Presentation/Export Layer. Consume el LineageGraph y exporta la topología.
"""

import logging
import csv
from pathlib import Path

# Importamos el contrato de datos
from expression_auditor.lineage_schema import LineageGraph

logger = logging.getLogger(__name__)


class RDFGenerator:
    """
    Exportador que convierte el LineageGraph de expresiones (Micro-Linaje)
    en un formato de red dirigido (CSV) compatible con Gephi.
    Nota: Mantiene el nombre RDFGenerator por compatibilidad de interfaz con el orquestador.
    """

    def __init__(self, lineage_graph: LineageGraph):
        self.lineage_graph = lineage_graph

    def export_expression_csv(self, output_path_str: str) -> bool:
        """
        EXP-3.2: Exporta un grafo de ecuaciones a formato CSV.
        Cuenta iteraciones (Weight) en caso de que la misma ecuación se evalúe múltiples veces.
        """
        output_path = Path(output_path_str).resolve()
        
        # Diccionario para agrupar y ponderar aristas: (Source, Target, Type) -> Weight
        edge_tally = {}
        
        # Procesar Consumes (Inputs): Variable -> Ecuación
        for spoke_uid, node_uids in self.lineage_graph.consumes.items():
            for node_uid in node_uids:
                key = (spoke_uid, node_uid, "consumes")
                edge_tally[key] = edge_tally.get(key, 0) + 1

        # Procesar Generates (Outputs): Ecuación -> Variable
        for node_uid, spoke_uids in self.lineage_graph.generates.items():
            for spoke_uid in spoke_uids:
                key = (node_uid, spoke_uid, "generates")
                edge_tally[key] = edge_tally.get(key, 0) + 1
                    
        try:
            # Garantizar que el directorio destino existe
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Exportando grafo CSV de expresiones físicas en -> {output_path}")
            with open(output_path, mode='w', newline='', encoding='utf-8') as csv_file:
                writer = csv.writer(csv_file)
                # Cabeceras estándar requeridas por la historia de usuario
                writer.writerow(["Source", "Target", "Type", "Weight"])
                
                for (source, target, edge_type), weight in edge_tally.items():
                    writer.writerow([source, target, edge_type, weight])
                    
            logger.info(f"CSV exportado exitosamente con {len(edge_tally)} aristas topológicas.")
            return True
            
        except IOError as error:
            # Fail-Safe I/O y Root Cause First
            logger.error(f"Root Cause: Falla de I/O al intentar escribir el archivo CSV de expresiones. Permisos o ruta inaccesible. Detalle: {error}")
            return False
        except Exception as error:
            logger.error(f"Root Cause: Error inesperado durante la generación del CSV. Detalle: {error}")
            return False

    def export(self, output_path_str: str, format_type: str = "csv") -> bool:
        """
        EXP-3.3: Enrutador principal de exportación con Fail-Safe I/O.
        Por defecto para el expression_auditor, el formato principal es CSV.
        """
        format_type = format_type.lower()
        
        if format_type == "csv":
            return self.export_expression_csv(output_path_str)
        else:
            logger.warning(
                f"Formato '{format_type}' no está optimizado en el Expression Auditor. "
                "Generando CSV por defecto."
            )
            return self.export_expression_csv(output_path_str)