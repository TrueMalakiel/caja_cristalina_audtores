AST-RDF Data Lineage Auditor
Patrón Arquitectónico: Gobernanza de Caja Cristalina

⚠️ Industrial Case Study Disclaimer (Aviso de Propiedad Industrial)
ESTE REPOSITORIO CONTIENE EXCLUSIVAMENTE LAS HERRAMIENTAS DE AUDITORÍA Y LA EVIDENCIA TOPOLÓGICA OFUSCADA.
El Sistema de Referencia Arquitectónico (SRA) analizado en el artículo —un simulador de yacimientos petrolíferos basado en Python—, así como sus motores estocásticos, algoritmos de presentación y ecuaciones derivadas de dominio, constituyen propiedad intelectual industrial estratégica y privada.
Para cumplir con los principios de reproducibilidad científica (Open Science) sin comprometer el know-how industrial, este repositorio proporciona libremente los algoritmos de análisis estático (AST Explorers) y los conjuntos de datos agregados (Supernodos) que demuestran la viabilidad arquitectónica de la propuesta. El código fuente operativo del simulador no está incluido ni disponible para distribución pública.

1. Contexto Académico y Funcionalidad
La adopción de asistentes de codificación basados en Modelos de Lenguaje de Gran Escala (LLMs) introduce un riesgo crítico en el software científico: la Física Alucinada (generación de código sintácticamente correcto que viola principios de conservación física o termodinámica).
Este repositorio alberga el AST-RDF Data Lineage Auditor, una herramienta metodológica diseñada para validar empíricamente el patrón arquitectónico de Gobernanza de Caja Cristalina. El sistema no requiere ejecutar las simulaciones; en su lugar, utiliza un análisis de "Expression-Level Slicing" y resolución de herencia estática para transformar el código fuente en un Grafo de Conocimiento Físico auditable, detectando las invariantes y contratos ontológicos de forma algorítmica.

2. Estructura del Repositorio
El pipeline de auditoría se divide en tres módulos principales:
1_external_auditor/: Módulo de "Discovery". Escanea la jerarquía de clases, resuelve el Method Resolution Order (MRO) estático y detecta invariantes de validación (Pydantic/Ontológicas).
2_expression_auditor/: Módulo de "Slicing". Opera en un Modo Suspendido sobre el AST (Árbol de Sintaxis Abstracta) para extraer el micro-linaje de las ecuaciones físicas, ignorando el ruido de control algorítmico.
3_empirical_evidence/: Contiene la evidencia empírica exportada tras auditar el simulador privado. Incluye:
lineage_supernodes.csv y lineage_super_edges.csv: Topología algorítmica usando Graph Folding (Supernodos) para proteger la propiedad intelectual.
canonical_lineage.csv: Prueba normativa de trazabilidad directa (alineado con exigencias PRMS/DAMA-DMBOK).
eur_architecture_ontology_graph.svg: Renderizado vectorial del grafo de conocimiento físico (Correspondiente a las Figuras 1 y 2 del artículo).

3. Guía de Reproducibilidad (Usage)
Instalación de Dependencias
Asegúrese de tener un entorno Python 3.9+ e instale los requisitos:
pip install -r requirements.txt

Ejecución de los Auditores en Proyectos Propios
Si desea aplicar este patrón arquitectónico para auditar su propio simulador o base de código, puede ejecutar la CLI indicando el directorio raíz de su proyecto:
# Paso 1: Generar el Índice RDF y descubrir jerarquías
python 1_external_auditor/main_auditor.py --project-root /ruta/a/su/proyecto --entry su_modulo.principal --output lineage_output.xml --format xml
# Paso 2: Extraer el Grafo de Ecuaciones Físicas (Micro-Linaje)
python 2_expression_auditor/main_auditor.py --project-root /ruta/a/su/proyecto --rdf lineage_output.xml --output physical_edges.csv

Visualización de la Evidencia Empírica
Para validar los resultados discutidos en el artículo científico (Figuras 1 y 2):
Explore directamente el archivo eur_architecture_ontology_graph.svg en la carpeta 3_empirical_evidence/ para una previsualización inmediata de la topología renderizada.
Importe los archivos lineage_supernodes.csv, lineage_super_edges.csv o canonical_lineage.csv en un software de análisis de redes (ej. Gephi) para escrutinio algorítmico interactivo.
Estos archivos revelan la integración contractual y la trazabilidad de la incertidumbre entre los distintos silos del sistema sin revelar la lógica algorítmica profunda.

4. Licencia
Las herramientas de auditoría (1_external_auditor y 2_expression_auditor) contenidas en este repositorio se distribuyen bajo la licencia MIT, permitiendo su uso, modificación y distribución para fines académicos o comerciales. (Nota: Esta licencia no aplica al SRA / Simulador externo analizado, el cual retiene todos los derechos reservados).
