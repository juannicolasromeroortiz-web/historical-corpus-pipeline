# CONTEXTO_PROYECTO — Corpus Histórico Prensa Colombiana

## Quién soy
Investigador con formación historiográfica. Nivel Python: intermedio-asistido (adapto scripts, trabajo con asistencia de IA). Quiero aprender ML conforme construyo el proyecto, no solo ejecutar instrucciones.

## Qué es el proyecto
Pipeline de reconocimiento, indexación y análisis semántico de prensa histórica colombiana (1849–1909). El objetivo no es solo extraer texto sino construir una herramienta de investigación que se acerque al archivo con criterio historiográfico, no solo técnico.

**Tema central:** El estudiante como sujeto político en la prensa colombiana del siglo XIX (1847–1871).
**Periodos prioritarios:** 
a. 1847-1870: la conexión entre los estudiantes colombianos y la situación global de 1848 en París. De allí se marca una continuidad hasta la revisión de las reacciones de los estudiantes frente a la reforma educativa de 1870.
b. 1870-1886: ecos de la comuna de parís. Dinámicas estudiantiles durante el federalismo. Guerra de las escuelas de 1876. Aparición del periódico El alcanfor. 
c. 1886-1903: el estudiante durante la regeneración. Reacción de los estudiantes ante el acecho estadounidense. 
d. 1903-1909: antiimperialismo de los estudiantes colombianos. Participación estudiantil en las protestas contra Reyes. Organización del Primer Congreso Internacional de Estudiantes de la Gran Colombia. 

## Stack tecnológico actual
- **OCR:** OCRmyPDF (batch masivo sobre PDFs descargados)
- **Almacenamiento:** SQLite `.db` + archivos `.txt` por número de periódico
- **Metadatos:** archivos `.json` por publicación
- **Selección del corpus:** script de relevancia por ocurrencia de palabras clave ("Juventud", "Estudiante")
- **Registro manual:** Google Sheets con ~30 archivos/año + ~500 registros transcritos con campos: Título, Imprenta, Impresor, Volumen, Año, Número, Fecha, Páginas, Autor, Resumen, Citas clave, Palabras clave, Descripción, URL
- **Repositorio:** https://github.com/juannicolasromeroortiz-web/historical-corpus-pipeline

## Arquitectura objetivo (pipeline en 5 fases)

| Fase | Nombre | Estado |
|------|--------|--------|
| 0 | Base actual (OCR batch + SQLite + keywords) | ✅ Funcionando |
| 1 | Mejora del OCR (OpenCV + Tesseract fine-tuning + diccionario s. XIX) | 🔲 Por iniciar |
| 2 | Normalización lingüística histórica (spaCy + normalizador s. XIX) | 🔲 Por iniciar |
| 3 | Representación semántica — embeddings (SentenceTransformers + FAISS) | 🔲 Por iniciar |
| 4 | Clasificación historiográfica (clasificador entrenado con 500 registros) | 🔲 Por iniciar |
| 5 | Análisis exploratorio (BERTopic, NER, redes temáticas, visualización) | 🔲 Por iniciar |

## Estado actual
- Fase en curso: FASE 1 (Iniciada el 11 de abril de 2026 a las 23:44 hora Colombia)
- Último avance: Proceso de planificación
- Problema específico de esta sesión: Generar la estructura de desarrollo del proyecto.

## Reglas de trabajo con Claude

1. **Sin memoria entre sesiones:** siempre pegar este archivo al inicio de cada chat nuevo.
2. **Una sesión = un problema concreto.** Formular así: "Estoy en Fase X, quiero lograr Y, tengo el problema Z."
3. **Horario óptimo Colombia (GMT-5):** usar Claude después de las 2pm hora colombiana en días de semana para evitar horas pico (los límites se consumen más rápido entre 8am–2pm hora colombiana).
4. **Conversaciones largas consumen más límite.** Si una sesión se extiende mucho, mejor abrir un chat nuevo con este contexto pegado.
5. **Usar Proyectos de Claude:** este archivo va como instrucción permanente en el Proyecto "Corpus Histórico Colombia" en claude.ai.
6. **Para ejecución masiva de scripts** (OCR batch, embeddings sobre todo el corpus): hacerlo en máquina local, no en chat.
