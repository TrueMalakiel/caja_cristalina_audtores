"""
FILE: external_auditor/inheritance_resolver.py
RESPONSABILIDAD: Resolución estática de herencia (MRO simplificado) y métodos canónicos.
ARQUITECTURA: SOLID - Pure Functions, Memoization, Fail-Safe Recursion.
"""

import logging
from typing import Dict, List, Set, Optional, Any

# Configuración del Logger
logger = logging.getLogger(__name__)


class StaticInheritanceResolver:
    """
    Motor de inferencia que calcula el dueño canónico de un método escalando 
    el árbol de herencia estático sin ejecutar código Python ni cargar estado global.
    """

    def __init__(self, class_hierarchy: Dict[str, Dict[str, Any]]):
        """
        Inicializa el resolutor con el diccionario construido en la Pass 1 del AST Walker.
        Estructura esperada: { "clase": {"bases": [...], "methods": set(...)} }
        """
        self.class_hierarchy = class_hierarchy
        self._canonical_method_cache: Dict[str, Optional[str]] = {}
        self._mro_cache: Dict[str, List[str]] = {}

    def _compute_static_mro(self, class_name: str) -> List[str]:
        """
        Calcula el Method Resolution Order (MRO) estático simplificado.
        Sube por el árbol de bases hasta encontrar la raíz o una clase externa opaca.
        Aplica memoización para evitar recomputaciones costosas.
        """
        if class_name in self._mro_cache:
            return self._mro_cache[class_name]

        mro_list: List[str] = []
        current_class: str = class_name
        visited_classes: Set[str] = set()

        # Fail-Safe Recursion: El set visited_classes evita bucles infinitos por herencia circular
        while current_class and current_class not in visited_classes:
            mro_list.append(current_class)
            visited_classes.add(current_class)

            # Si la clase no fue parseada (es de una librería externa), detenemos el ascenso
            if current_class not in self.class_hierarchy:
                break

            bases: List[str] = self.class_hierarchy[current_class].get("bases", [])
            
            if not bases:
                break
                
            # MVP (HU-1.3): Mitigación de Herencia Múltiple. 
            # Se registra en modo debug y se asume la base primaria (index 0).
            if len(bases) > 1:
                logger.debug(
                    f"[MRO] Herencia múltiple detectada en {current_class}. "
                    f"Seleccionando base primaria: {bases[0]}"
                )
            
            current_class = bases[0]

        self._mro_cache[class_name] = mro_list
        return mro_list

    def find_canonical_method_owner(self, class_name: str, method_name: str) -> Optional[str]:
        """
        HU-2.1: Devuelve el nombre completo de la clase MÁS ALTA (ancestro principal)
        en la cadena de herencia que define explícitamente el método solicitado.
        Esto permite aplicar Graph Folding (Agregación) a métodos sobrescritos.
        """
        cache_key = f"{class_name}::{method_name}"
        if cache_key in self._canonical_method_cache:
            return self._canonical_method_cache[cache_key]

        mro_list = self._compute_static_mro(class_name)
        canonical_owner_name: Optional[str] = None

        # Recorremos el MRO desde la clase invocada hacia arriba en el árbol
        for ancestor_class_name in mro_list:
            if ancestor_class_name not in self.class_hierarchy:
                continue
                
            defined_methods: Set[str] = self.class_hierarchy[ancestor_class_name].get("methods", set())
            
            if method_name in defined_methods:
                # Actualizamos el dueño. Al omitir la instrucción 'break', garantizamos 
                # sobreescribir el valor hasta llegar a la clase padre más alta de la cadena.
                canonical_owner_name = ancestor_class_name

        self._canonical_method_cache[cache_key] = canonical_owner_name
        return canonical_owner_name

    def is_method_overridden(self, class_name: str, method_name: str) -> bool:
        """
        HU-2.3: Verifica si la clase actual sobrescribe un método que ya existía 
        en alguna de sus clases base. Crucial para resolver la topología de 'super()'.
        """
        if class_name not in self.class_hierarchy:
            return False
            
        defined_methods: Set[str] = self.class_hierarchy[class_name].get("methods", set())
        if method_name not in defined_methods:
            # La clase actual no define este método en absoluto
            return False
            
        bases: List[str] = self.class_hierarchy[class_name].get("bases", [])
        if not bases:
            # Es una clase raíz, por ende no sobrescribe a nadie
            return False
            
        # Revisamos el MRO a partir de la clase base inmediata
        base_mro_list = self._compute_static_mro(bases[0])
        for ancestor_class_name in base_mro_list:
            if ancestor_class_name not in self.class_hierarchy:
                continue
                
            ancestor_methods: Set[str] = self.class_hierarchy[ancestor_class_name].get("methods", set())
            if method_name in ancestor_methods:
                return True
                
        return False