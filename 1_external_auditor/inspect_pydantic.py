"""
FILE: external_auditor/inspect_pydantic.py
RESPONSABILIDAD: Módulo de Reflexión Segura para extraer metadatos (properties, validators) sin ejecutar simulaciones.
ARQUITECTURA: SOLID - Aislamiento de dependencias mediante importlib (Fail-Safe I/O).
"""

import inspect
import importlib.util
import sys
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

def safe_extract_schema_metadata(file_path: str, module_name: str) -> Dict[str, List[str]]:
    """
    Carga un módulo Python en un entorno aislado y extrae:
    1. Nombres de propiedades dinámicas (@property).
    2. Nombres de validadores Pydantic v2 (@model_validator, @field_validator).

    Retorna un diccionario con listas planas de strings para inyectarse 
    como nodos virtuales en el AST Explorer.
    """
    metadata: Dict[str, List[str]] = {
        "properties": [],
        "validators": []
    }

    try:
        # 1. Carga segura del módulo (Sin ejecutar el entrypoint global)
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            logger.debug(f"[FAIL-SAFE] No se pudo crear la especificación para {file_path}")
            return metadata

        module = importlib.util.module_from_spec(spec)
        
        # Inyección temporal en sys.modules para permitir resolución interna de dependencias locales
        sys.modules[module_name] = module
        
        # Ejecución aislada del módulo (lee las definiciones, no ejecuta lógica imperativa)
        spec.loader.exec_module(module)

        # 2. Inspección de todas las clases dentro del módulo
        for cls_name, cls_obj in inspect.getmembers(module, inspect.isclass):
            
            # Evitar inspeccionar clases importadas de otros archivos (ej. BaseModel)
            if getattr(cls_obj, '__module__', '') != module_name:
                continue

            # 3. Extracción de @property
            for prop_name, attr_obj in inspect.getmembers(cls_obj):
                if isinstance(attr_obj, property):
                    metadata["properties"].append(prop_name)

            # 4. Extracción de Pydantic Validators (v2)
            if hasattr(cls_obj, '__pydantic_decorators__'):
                decorators = getattr(cls_obj, '__pydantic_decorators__')
                
                # Extraer model_validators
                if hasattr(decorators, 'model_validators'):
                    for val_name in decorators.model_validators.keys():
                        metadata["validators"].append(val_name)
                        
                # Extraer field_validators
                if hasattr(decorators, 'field_validators'):
                    for val_name in decorators.field_validators.keys():
                        metadata["validators"].append(val_name)

    except Exception as e:
        # Capturamos silenciosamente para no detener el recorrido del AST Walker
        # Fail-Safe I/O: Previene que dependencias faltantes arruinen la auditoría completa
        logger.debug(f"[FAIL-SAFE] Reflexión omitida para {file_path}. Detalle: {e}")

    return metadata