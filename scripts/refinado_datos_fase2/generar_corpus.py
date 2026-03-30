import os
import re
import json
import sqlite3
import pandas as pd
from pathlib import Path

# ==========================================
# 1. CONFIGURACIÓN DE RUTAS
# ==========================================
BASE_DIR = "/home/juan_romero/projects/ocr_project"
DATA_DIR = os.path.join(BASE_DIR, "data_final")
METADATA_DIR = os.path.join(BASE_DIR, "metadata")
DB_PATH = os.path.join(BASE_DIR, "db", "documentsfase2.db") # Reemplaza con el nombre de tu .db
EXPORT_PATH = os.path.join(BASE_DIR, "exports", "corpus_seleccionado_1870_1886.xlsx")

# ==========================================
# 2. FUNCIONES DE PROCESAMIENTO DE TEXTO
# ==========================================
def limpiar_texto(texto):
    texto = texto.lower()
    texto = re.sub(r'-\s*\n\s*', '', texto)
    return texto

def calcular_dispersion(texto, palabra, num_bloques=10):
    palabras = texto.split()
    if not palabras:
        return "0/10"
    
    tamano_bloque = max(1, len(palabras) // num_bloques)
    bloques = [palabras[i:i + tamano_bloque] for i in range(0, len(palabras), tamano_bloque)]
    
    bloques_con_palabra = sum(1 for bloque in bloques if any(palabra in p for p in bloque))
    return f"{bloques_con_palabra}/{num_bloques}"

# ==========================================
# 3. EXTRACCIÓN HÍBRIDA (JSON + BASE DE DATOS)
# ==========================================
def obtener_metadatos_completos(identificador, ano_carpeta):
    """
    Extrae la información requerida combinando el JSON y la base de datos SQL.
    """
    datos = {
        "periodico": "",
        "descripcion": "",
        "numero": "",
        "link": "",
        "ano": ano_carpeta # Usado como respaldo si la BD falla
    }

    # A. Buscar en el archivo JSON (Metadata)
    try:
        archivos_json = list(Path(METADATA_DIR).glob(f"*_{identificador}.json"))
        if archivos_json:
            with open(archivos_json[0], 'r', encoding='utf-8') as f:
                meta_json = json.load(f)
                datos["periodico"] = meta_json.get("periodico", "")
                datos["descripcion"] = meta_json.get("descripcion_objeto", "")
                datos["numero"] = meta_json.get("titulo_numero", "")
                datos["link"] = meta_json.get("download_url", "")
    except Exception as e:
        print(f"Error leyendo JSON para {identificador}: {e}")

    # B. Buscar en la Base de Datos SQLite (Para Año y Número)
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # ATENCIÓN: Ajusta 'nombre_tabla', 'columna_ano' y 'columna_numero' a los nombres reales de tu .db
        query = """
            SELECT year, numero 
            FROM docs 
            WHERE child_id = ?
        """
        cursor.execute(query, (identificador,))
        resultado = cursor.fetchone()
        conn.close()

        if resultado:
            db_ano, db_num = resultado
            if db_ano:
                datos["ano"] = db_ano
            # Si el JSON no traía número, usamos el de la BD
            if not datos["numero"] and db_num:
                datos["numero"] = db_num
                
    except Exception as e:
        # Si la consulta falla (ej. tabla no configurada), continuará silenciosamente usando los datos del JSON/Carpeta
        pass

    return datos

# ==========================================
# 4. LÓGICA DE SELECCIÓN Y PIPELINE
# ==========================================
def procesar_corpus():
    print("Iniciando escaneo de archivos OCR...")
    documentos_por_ano = {}
    
    regex_estudiante = r'\b[ce]studiant[es]\b'
    regex_juventud = r'\b[ji]uventud(?:es)?\b'

    for ruta_txt in Path(DATA_DIR).rglob('input/*.txt'):
        carpeta_instancia = ruta_txt.parent.parent.name
        
        match = re.search(r'_(\d{4})_(\d+)$', carpeta_instancia)
        if not match:
            continue
            
        ano = int(match.group(1))
        identificador = match.group(2)

        if not (1870 <= ano <= 1886):
            continue

        try:
            with open(ruta_txt, 'r', encoding='utf-8') as f:
                texto = limpiar_texto(f.read())
        except Exception:
            continue

        f_estudiante = len(re.findall(regex_estudiante, texto))
        f_juventud = len(re.findall(regex_juventud, texto))

        if f_estudiante == 0 and f_juventud == 0:
            continue

        coocurrencia = 1.5 if (f_estudiante > 0 and f_juventud > 0) else 1.0
        puntaje = ((5 * f_estudiante) + (1 * f_juventud)) * coocurrencia

        disp_est = calcular_dispersion(texto, "estudiant") if f_estudiante > 0 else "0/10"
        disp_juv = calcular_dispersion(texto, "juventud") if f_juventud > 0 else "0/10"
        texto_dispersion = f"Est:{disp_est} | Juv:{disp_juv}"

        if ano not in documentos_por_ano:
            documentos_por_ano[ano] = []
            
        documentos_por_ano[ano].append({
            'ano': ano,
            'id_archivo': identificador,
            'puntaje': puntaje,
            'subcorpus': f"Pts: {puntaje} | Disp: {texto_dispersion}", 
            'palabra_I': 'juventud' if f_juventud > 0 else '',
            'palabra_II': 'estudiante' if f_estudiante > 0 else ''
        })

    # ==========================================
    # 5. CONSOLIDACIÓN Y SELECCIÓN TOP 30
    # ==========================================
    archivos_finales = []
    print("Filtrando los 30 mejores documentos por año y extrayendo metadatos...")
    
    for ano in sorted(documentos_por_ano.keys()):
        docs_ordenados = sorted(documentos_por_ano[ano], key=lambda x: x['puntaje'], reverse=True)
        top_30 = docs_ordenados[:30]
        
        for doc in top_30:
            # En este punto cruzamos con JSON y DB solo los 30 ganadores para ahorrar tiempo
            doc['metadatos'] = obtener_metadatos_completos(doc['id_archivo'], doc['ano'])
            archivos_finales.append(doc)
            
        print(f"Año {ano}: {len(top_30)} documentos consolidados.")

    generar_excel(archivos_finales)

def generar_excel(datos):
    """
    Construye el DataFrame respetando estrictamente las instrucciones del historiador.
    """
    filas = []
    for doc in datos:
        meta = doc['metadatos']
        
        fila = {
            "SUBCORPUS": doc['subcorpus'],
            "TÍTULO DE LA PUBLICACIÓN SERIADA": meta['periodico'],
            "IMPRENTA": "",
            "IMPRESOR": "",
            "CARACTERÍSTICAS MATERIALES": "",
            "AÑO": meta['ano'],
            "VOL.": "",
            "NUM": meta['numero'],
            "MES": "",
            "Página inicio": "",
            "Página final": "",
            "Autor": "",
            "Título del artículo: Subtítulo": "",
            "Resumen": "",
            "CITAS CLAVE": "",
            "PALABRAS CLAVE I": doc['palabra_I'],
            "PALABRAS CLAVE II": doc['palabra_II'],
            "PALABRAS CLAVE III": "",
            "DESCRIPCIÓN DE LA PUBLICACIÓN": meta['descripcion'],
            "link de acceso": meta['link']
        }
        filas.append(fila)

    # Las columnas se inyectan exactamente en este orden
    orden_columnas = [
        "SUBCORPUS", "TÍTULO DE LA PUBLICACIÓN SERIADA", "IMPRENTA", "IMPRESOR", 
        "CARACTERÍSTICAS MATERIALES", "AÑO", "VOL.", "NUM", "MES", "Página inicio", 
        "Página final", "Autor", "Título del artículo: Subtítulo", "Resumen", 
        "CITAS CLAVE", "PALABRAS CLAVE I", "PALABRAS CLAVE II", "PALABRAS CLAVE III", 
        "DESCRIPCIÓN DE LA PUBLICACIÓN", "link de acceso"
    ]
    
    df = pd.DataFrame(filas, columns=orden_columnas)
    
    os.makedirs(os.path.dirname(EXPORT_PATH), exist_ok=True)
    df.to_excel(EXPORT_PATH, index=False)
    print(f"\n¡Proceso completado! Archivo estructurado guardado en:\n{EXPORT_PATH}")

if __name__ == "__main__":
    procesar_corpus()
