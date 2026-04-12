# DECISIONES.md
> Registro de por qué se eligió cada herramienta o enfoque.
> Esto evita re-debatir decisiones ya tomadas y sirve de memoria metodológica.

---

## Decisiones de arquitectura

### OCR: OCRmyPDF como base
**Decisión:** mantener OCRmyPDF para el batch inicial, mejorar con preprocesamiento OpenCV.
**Razón:** ya funciona y tiene buena integración con Tesseract. Reemplazarlo completo no justifica el costo de re-aprender.
**Alternativa descartada:** Kraken (diseñado para documentos históricos, más flexible, pero curva de aprendizaje mayor). Evaluar en Fase 1 si OCRmyPDF no mejora suficiente con preprocesamiento.
**Fecha:** 11/04/2026

### Embeddings: multilingual-MiniLM
**Decisión:** usar `paraphrase-multilingual-MiniLM-L12-v2` de SentenceTransformers.
**Razón:** modelo multilingüe preentrenado en textos de múltiples épocas, funciona razonablemente con español histórico sin necesidad de entrenar desde cero. Liviano y rápido.
**Alternativa descartada:** entrenar embeddings propios (requiere mucho más datos y cómputo del disponible).
**Fecha:** [POR DEFINIR]

### Índice vectorial: FAISS
**Decisión:** usar FAISS para búsqueda por similitud sobre embeddings.
**Razón:** librería de Facebook AI, eficiente para búsqueda aproximada en corpus de tamaño mediano. No requiere servidor externo.
**Alternativa descartada:** ChromaDB (más simple pero menos control), Pinecone (requiere cuenta cloud).
**Fecha:** [POR DEFINIR]

### Criterio de selección: clasificador entrenado vs keywords
**Decisión:** reemplazar índice de ocurrencia de palabras clave por clasificador entrenado con los 500 registros anotados manualmente.
**Razón:** el criterio de ocurrencia es exhaustivo en palabras pero ciego al contexto. Un clasificador aprende el juicio historiográfico implícito en las selecciones manuales ya realizadas.
**Riesgo asumido:** los 500 registros son todos positivos (relevantes). Necesitamos ejemplos negativos anotados para que el clasificador aprenda el contraste.
**Fecha:** [POR DEFINIR]

---

## Decisiones metodológicas (historiográficas)

### Período cubierto: 1849–1909
**Razón:** a. 1847-1870: la conexión entre los estudiantes colombianos y la situación global de 1848 en París. De allí se marca una continuidad hasta la revisión de las reacciones de los estudiantes frente a la reforma educativa de 1870.
b. 1870-1886: ecos de la comuna de parís. Dinámicas estudiantiles durante el federalismo. Guerra de las escuelas de 1876. Aparición del periódico El alcanfor. 
c. 1886-1903: el estudiante durante la regeneración. Reacción de los estudiantes ante el acecho estadounidense. 
d. 1903-1909: antiimperialismo de los estudiantes colombianos. Participación estudiantil en las protestas contra Reyes. Organización del Primer Congreso Internacional de Estudiantes de la Gran Colombia.

### Palabras clave iniciales: "Juventud", "Estudiante"
**Razón:** términos centrales del discurso sobre la juventud en el período. Punto de entrada para la construcción del corpus, no criterio final de selección.
**Limitación reconocida:** variantes ortográficas, sinónimos del XIX y referencias implícitas no son capturadas. La Fase 3 (embeddings) y Fase 4 (clasificador) buscan superar esta limitación.

### 30 registros de archivos/año como unidad de muestreo
**Razón:** A partir de los archivos digitales de prensa histórica colombiana existentes y la amplitud del periodo de tiempo especificado, se opto por mantener 30 registros de archivos por año (de 1849 a 1909, es decir, un total aproximado de 1830 registros como total) por abarcabilidad por parte de los investigadores. En este caso, se puede definir un universo de investigación mucho más acotado acorde a los tiempos oficiales destinados a esta investigación: como parte de una monitoria de investigación impulsada a nivel institucional, el desarrollo de esta búsqueda está limitada a solo 168 horas de trabajo hasta finales de mayo de 2026.  
**Excepciones:** En algunos casos, por limitaciones a nivel técnico, la selección y posterior registro de los archivos es menor a los 30 archivos límite. 

---

## Plantilla para nuevas decisiones

### [Nombre de la decisión]
**Decisión:**
**Razón:**
**Alternativa descartada:**
**Riesgo asumido:**
**Fecha:**
