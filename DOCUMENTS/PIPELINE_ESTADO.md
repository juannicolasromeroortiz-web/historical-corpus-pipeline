# PIPELINE_ESTADO.md
> Actualizar este archivo al terminar cada sesión de trabajo.

## Fase actual: 0 → preparando Fase 1

---

## Fase 0 — Base actual ✅
**Qué funciona:**
- Descarga automática de PDFs desde metadata `.json`
- OCR batch con OCRmyPDF → genera `.txt` por número de periódico
- SQLite `.db` con queries por palabras clave
- Script de relevancia por ocurrencia de "Juventud" / "Estudiante"
- Sheets con ~30 archivos/año (1849–1909)
- 500 registros transcritos manualmente

**Limitaciones conocidas:**
- OCR sin preprocesamiento de imagen → calidad variable en tipografías del XIX
- Criterio de selección basado solo en ocurrencia de palabras clave
- Sin normalización del español histórico
- Sin búsqueda semántica

---

## Fase 1 — Mejora del OCR 🔲
**Objetivo:** reducir el Character Error Rate (CER) en documentos del corpus.

**Tareas pendientes:**
- [ ] Seleccionar 10 páginas con transcripción manual existente como muestra de evaluación
- [ ] Medir CER base (sin preprocesamiento) con `ocrevalUAtion` o comparación manual
- [ ] Implementar preprocesamiento con OpenCV: binarización adaptativa + deskewing
- [ ] Medir CER post-preprocesamiento y comparar
- [ ] Construir diccionario de postcorrección (errores típicos OCR en tipografía s. XIX)
- [ ] Aplicar diccionario sobre `.txt` existentes

**Decisiones pendientes:**
- ¿Vale la pena fine-tuning de Tesseract o con el preprocesamiento es suficiente?

**Scripts relevantes:** [AGREGAR rutas cuando existan]

---

## Fase 2 — Normalización lingüística 🔲
**Objetivo:** texto limpio en español normalizado antes del análisis semántico.

**Tareas pendientes:**
- [ ] Instalar y configurar spaCy con modelo `es_core_news_lg`
- [ ] Construir lista de variantes ortográficas del español colombiano 1849–1909
- [ ] Construir expansor de abreviaturas de prensa del XIX
- [ ] Pipeline: `.txt` → `.txt_norm`

---

## Fase 3 — Embeddings semánticos 🔲
**Objetivo:** reemplazar búsqueda por keywords con búsqueda por similitud semántica.

**Tareas pendientes:**
- [ ] Instalar `sentence-transformers` y probar `paraphrase-multilingual-MiniLM-L12-v2`
- [ ] Generar embeddings sobre los 500 registros existentes (resumen + citas clave)
- [ ] Crear índice FAISS
- [ ] Comparar resultados de búsqueda semántica vs búsqueda por keywords actual

---

## Fase 4 — Clasificador historiográfico 🔲
**Objetivo:** automatizar la selección de documentos relevantes según criterio de investigación.

**Tareas pendientes:**
- [ ] Añadir columna `relevante` (1/0) a los 500 registros del Sheets
- [ ] Anotar ~100–200 documentos descartados como ejemplos negativos (relevante=0)
- [ ] Entrenar clasificador (logistic regression o similar) con embeddings + etiquetas
- [ ] Evaluar precisión y recall sobre muestra de validación
- [ ] Aplicar clasificador a documentos no revisados del corpus

---

## Fase 5 — Análisis exploratorio 🔲
**Objetivo:** descubrir patrones temáticos, temporales y discursivos no buscados explícitamente.

**Tareas pendientes:**
- [ ] Topic modeling con BERTopic sobre corpus completo normalizado
- [ ] NER para entidades históricas (personas, instituciones, lugares)
- [ ] Visualización temporal de temas
- [ ] Red de co-ocurrencia de términos por periodo

---

## Problemas abiertos / deuda técnica
| Problema | Fase | Prioridad |
|----------|------|-----------|
| [AGREGAR conforme aparezcan] | | |
