"""
FILE: expression_auditor/config.py
RESPONSABILIDAD: Centralizar la configuración y patrones de filtrado para el Micro-Linaje.
ARQUITECTURA: SOLID - Separation of Concerns. Extrae las reglas de negocio y magic strings.
"""

from typing import List

# ==============================================================================
# 1. FILTROS DE VARIABLES FÍSICAS (Expression-Level Filtering)
# ==============================================================================
# EXP-1.3 / EXP-2.3: Patrones para identificar magnitudes físicas dentro de las ecuaciones.
# El ExpressionVisitor ignorará variables de control temporal (ej. i, j, temp, iter) 
# asegurando que el grafo resultante solo contenga topología termodinámica/volumétrica.
PHYSICAL_VARIABLE_PATTERNS: List[str] = [
    "*.poes*",
    "*.eur*",
    "*.q0*",
    "*area*",
    "*thickness*",
    "*porosity*",
    "*permeability*",
    "*viscosity*",
    "*phi*",
    "*sw*",
    "*sat*",
    "*pressure*",
    "*temperature*",
    "*compressibility*",
    "*fvf*",       # Formation Volume Factor
    "*gor*",       # Gas-Oil Ratio
    "*recovery_factor*"
]

# ==============================================================================
# 2. FILTROS DE FUNCIONES DE CÁLCULO
# ==============================================================================
# EXP-1.3: Patrones de nombres de funciones que indican operaciones matemáticas
# o mutaciones de estado físico, utilizados para pre-filtrar el análisis.
CALCULATION_FUNCTION_PATTERNS: List[str] = [
    "calculate_*",
    "update_*",
    "_get_*",
    "compute_*",
    "evaluate_*"
]