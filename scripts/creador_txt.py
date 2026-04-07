import os
import csv
import fitz  # PyMuPDF
import re

# --- CONFIGURACIÓN DE RUTAS ---
carpeta_origen = r"/home/juan-romero/Descargas/PDFS_SIN_OCR" 
carpeta_txt = os.path.join(carpeta_origen, "TXT_Limpios")
archivo_salida = "resultados_revision_final.csv"

# Crear la carpeta de salida si no existe
if not os.path.exists(carpeta_txt):
    os.makedirs(carpeta_txt)

palabras_clave = {
    "Juventud": r"juventud", 
    "Estudiante": r"estudiante",
    "Joven": r"j[oó]ven"
}

resultados = []

if not os.path.exists(carpeta_origen):
    print(f"❌ ERROR: La carpeta {carpeta_origen} no existe.")
else:
    archivos = [f for f in os.listdir(carpeta_origen) if f.lower().endswith(".pdf")]
    print(f"📂 Procesando {len(archivos)} archivos. Generando TXT limpios...")

    for archivo in archivos:
        ruta_completa = os.path.join(carpeta_origen, archivo)
        conteos_archivo = {clave: 0 for clave in palabras_clave}
        
        try:
            with fitz.open(ruta_completa) as pdf:
                texto_total = ""
                for pagina in pdf:
                    # Extraemos el texto de la página
                    bloques = pagina.get_text("blocks")
                    # Unimos los bloques eliminando saltos de línea internos que rompen palabras
                    for b in bloques:
                        texto_total += b[4].replace("\n", " ") + " "

                # LIMPIEZA EXTRA: Quitar múltiples espacios y normalizar
                texto_limpio = re.sub(r'\s+', ' ', texto_total).strip()

                # 1. GUARDAR EL ARCHIVO TXT (Para AntConc)
                nombre_txt = archivo.replace(".pdf", ".txt")
                ruta_txt = os.path.join(carpeta_txt, nombre_txt)
                with open(ruta_txt, "w", encoding="utf-8") as f_txt:
                    f_txt.write(texto_limpio)
            
            print(f"✅ {archivo} -> TXT generado")
            
        except Exception as e:
            print(f"❌ Error en {archivo}: {e}")

    # Guardar resultados CSV

    print(f"\n🚀 ¡Todo listo!")
    print(f"1. Los TXT están en: {carpeta_txt}")
    
