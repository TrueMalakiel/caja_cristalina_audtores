# Módulo: 3_empirical_evidence

## Descripción General
Este módulo contiene los conjuntos de datos resultantes (evidencia empírica) generados por el pipeline de auditoría estática descrito en las Fases 1 y 2.
El propósito de este directorio es proporcionar la Topología Algorítmica y los grafos de dependencias extraídos del Sistema de Referencia Arquitectónico (SRA). Para proteger la propiedad intelectual de las fórmulas y correlaciones exactas, los datos exportados aplican técnicas de Graph Folding (Agregación de Grafos) y Ofuscación Topológica, colapsando la matemática subyacente en "Supernodos" semánticos.

## Componentes Clave
lineage_supernodes.csv y lineage_super_edges.csv: Matrices de datos que representan la red agregada del sistema. Muestran cómo interactúan los contratos a nivel macro entre los distintos Silos Semánticos (Geología, Estocástico, Producción) sin revelar las ecuaciones algebraicas internas.

canonical_lineage.csv: Documenta el linaje estricto y unidireccional de las propiedades físicas clave (ej. factor de recobro, POES, flujo natural q0). Sirve como prueba normativa de transparencia de principio a fin, alineada con los estándares de PRMS y DAMA-DMBOK.

eur_architecture_ontology_graph.svg: Representación gráfica vectorial (renderizada) de la topología extraída, ilustrando la convergencia de las variables físicas a través de los contratos ontológicos.

## Relación con el Artículo Científico
Estos archivos constituyen la prueba empírica irrefutable de los resultados discutidos en el manuscrito "Propuesta de Arquitectura con Gobernanza Emergente: Caja Cristalina":
1. Soporte de las Figuras 1 y 2: Los archivos CSV proporcionados en este directorio son la fuente de datos algorítmica exacta utilizada para renderizar las vistas ontológicas e intra-silo del documento.
2. Trazabilidad Algorítmica (Escenario 1 ATAM): Demuestra la viabilidad de extraer un Grafo de Conocimiento Físico coherente directamente del código fuente, probando que el sistema posee una auditabilidad intrínseca.
3. Verificación Estructural: Valida que la comunicación inter-módulos obedece estrictamente a las restricciones físicas codificadas en los invariantes de clase de la arquitectura.

⚠️ Nota de Privacidad y Propiedad Industrial
Los grafos de red proporcionados en este módulo demuestran la trazabilidad estructural (el "cómo" se conectan los datos), pero han sido deliberadamente filtrados mediante agrupaciones jerárquicas (Graph Folding) para ofuscar el álgebra y las constantes propietarias (el "qué" calculan exactamente). El código fuente del simulador de yacimientos, los motores estocásticos y las correlaciones derivadas constituyen propiedad intelectual industrial estratégica y no están incluidos en este repositorio público.
