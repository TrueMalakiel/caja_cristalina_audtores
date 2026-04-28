# Módulo: 1_external_auditor

## Descripción General
Este módulo constituye la primera fase (Pass 1: Discovery) del pipeline de auditoría estática para el patrón arquitectónico "Caja Cristalina". Su función principal es el escrutinio del código fuente para reconstruir la jerarquía de clases, resolver dependencias de herencia y extraer metadatos de validación (Pydantic) sin ejecutar lógica de dominio.

## Componentes Clave
- **ast_explorer.py**: Implementa el `HierarchyVisitor`, encargado de mapear importaciones, definiciones de clases y métodos recorriendo el Árbol de Sintaxis Abstracta (AST).
- **inheritance_resolver.py**: Motor de inferencia que calcula el MRO (Method Resolution Order) estático. Permite identificar al "dueño canónico" de un método o axioma en la cadena de herencia.
- **inspect_pydantic.py**: Módulo de reflexión segura para extraer propiedades y validadores de modelos de datos, inyectándolos como nodos virtuales en el grafo de linaje.
- **lineage_schema.py**: Define los contratos de datos (SSoT) para nodos de función y atributos físicos, asegurando la inmutabilidad de la información capturada.

## Relación con el Paper
Este módulo materializa las decisiones estructurales discutidas en el artículo *"Propuesta de Arquitectura con Gobernanza Emergente: Caja Cristalina"*:
1. **Validación de ADR-1 (Ontología Superior)**: Provee la evidencia técnica de cómo la herencia forzosa de una clase base abstracta permite la trazabilidad estructural.
2. **Fundamento de la Figura 1**: Los datos extraídos por este auditor permiten generar la topología de los Silos Semánticos y su conexión con el núcleo ontológico.
3. **Integridad Semántica**: Al resolver la herencia de forma estática, el auditor garantiza que los contratos de gobernanza definidos en el diseño se cumplen efectivamente en la implementación del código.

## Nota de Privacidad Industrial
Este repositorio contiene exclusivamente las herramientas de auditoría. El Sistema de Referencia Arquitectónico (SRA/Simulador) analizado en el paper constituye propiedad intelectual privada y no está incluido en este módulo.
