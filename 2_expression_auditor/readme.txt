Módulo: 2_expression_auditor

Descripción General
Este módulo constituye la segunda fase (Pass 2: Slicing) del pipeline de auditoría estática para la arquitectura de "Caja Cristalina". Su responsabilidad es ejecutar un Expression-Level Slicing, recorriendo el Árbol de Sintaxis Abstracta (AST) en un "Modo Suspendido".
Su objetivo es extraer el micro-linaje de las ecuaciones físicas (variables de entrada, operaciones y variables de salida), ignorando el ruido algorítmico y las variables de control temporal (como contadores de bucles o índices).

Componentes Clave
config.py: Centraliza las reglas de negocio y los patrones de filtrado (Expression-Level Filtering) para identificar magnitudes físicas válidas dentro del código.

expression_visitor.py: Implementa el visitor contextual del AST que extrae dependencias de los lados derecho (RHS) e izquierdo (LHS) de las asignaciones, conectando el flujo termodinámico real.

rdf_parser.py: Módulo de acceso a datos que consume el índice generado por la Fase 1, determinando con precisión qué funciones objetivo deben ser analizadas (Slicing Contextual).

rdf_builder.py: Capa de exportación que consolida el LineageGraph en memoria y genera las matrices topológicas (CSV) compatibles con herramientas de análisis de redes (ej. Gephi).

main_auditor.py: El orquestador (CLI) que coordina la carga del índice, el escrutinio de los archivos fuente y la exportación de los resultados.

Relación con el Artículo Científico
Este módulo es la herramienta metodológica que genera la evidencia empírica central del manuscrito "Propuesta de Arquitectura con Gobernanza Emergente: Caja Cristalina":
Validación de ADR-3 y ADR-4: Demuestra algorítmicamente que los axiomas físicos y las variables dimensionales están centralizados y son rastreables (Escenarios de Evaluación 1 y 3 de la metodología ATAM).
Generación de la Tabla 2: La matriz de datos extraída por el expression_visitor.py es la fuente directa de la topología "Micro-Linaje Extraído para el Cálculo de POES" documentada en el artículo.
Reducción de Deuda Técnica Semántica: Prueba empíricamente que la arquitectura propuesta permite extraer el Grafo de Conocimiento Físico sin necesidad de ejecutar el simulador ni una sola vez.

⚠️ Nota de Privacidad y Propiedad Industrial
Este repositorio contiene exclusivamente los algoritmos de análisis estático (herramientas de auditoría). El código fuente del Sistema de Referencia Arquitectónico (el simulador de yacimientos), así como las ecuaciones derivadas propietarias y sus factores de ajuste, constituyen propiedad intelectual industrial estratégica y han sido deliberadamente excluidos para el escrutinio público.
