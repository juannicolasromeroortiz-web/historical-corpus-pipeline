#!/usr/bin/env python3
import subprocess
from pathlib import Path

# ===============================
# CONFIGURACIÓN DE RUTAS
# ===============================
BASE = Path(__file__).resolve().parents[2]  # raíz del proyecto
EXPORTS_DIR = BASE / "exports"
EXPORTS_DIR.mkdir(exist_ok=True)

SCRIPTS_DIR = BASE / "scripts" / "INDEX"

# ===============================
# INPUT DE KEYWORDS
# ===============================
def input_keywords():
    print("Introduce las keywords que quieres usar para la indexación (separadas por coma):")
    kw_input = input().strip()
    keywords = [kw.strip() for kw in kw_input.split(",") if kw.strip()]
    if not keywords:
        print("No se ingresó ninguna keyword. Se usará la default: ['estudiante']")
        keywords = ["estudiante"]
    print(f"Keywords a usar: {keywords}")
    return keywords

# ===============================
# FUNCIÓN PARA EJECUTAR SCRIPTS
# ===============================
def run_script(script_name, env_vars=None, silent=False):
    """Ejecuta un script de python con opcional diccionario de variables de entorno"""
    script_path = SCRIPTS_DIR / script_name
    cmd = ["python3", str(script_path)]

    import os
    env = os.environ.copy()
    if env_vars:
        env.update(env_vars)

    if silent:
        subprocess.run(
            cmd,
            check=True,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    else:
        subprocess.run(cmd, check=True, env=env)


# ===============================
# ORQUESTACIÓN DEL PIPELINE
# ===============================
def main():
    # 1. Pedir keywords
    keywords = input_keywords()
    
    # Pasar keywords al pipeline usando variable de entorno
    kw_env = {"KEYWORDS": ",".join(keywords)}

    print("\n=== 1. Conteo exacto y generación de subcorpus ===")
    run_script("extract_for_excel.py", env_vars=kw_env)
    
    print("\n=== 2. Generar timeline temática ===")
    run_script("timeline_tematica.py", env_vars=kw_env)
    
    print("\n==3. Preparación de constelaciones semánticas (SpaCy) ===")
    run_script("constelaciones_spacy.py", env_vars=kw_env, silent=True)
    
    print("\n==4. Detección de episodios discursivos ===")
    run_script("episodios_discursivos.py", env_vars=kw_env)
    
    print("\n=== 5. Clustering conceptual ligero ===")
    run_script("clustering_ligero.py", env_vars=kw_env)
    
    print("\n=== 6. Generación de snippets inteligentes ===")
    run_script("semantic_snippet_selector.py", env_vars=kw_env)
    
    print("\n=== 7. Creación de subcorpus a partir de palabras clave ===")
    run_script("build_subcorpus_fase3.py", env_vars=kw_env)
    run_script("build_subcorpus_references.py", env_vars=kw_env, silent=True)
    
    
    print("\n== 8. Generación de tabla de investigación base ===")
    run_script("extract_excel_fields.py", env_vars=kw_env)
    
    print("\n✔ Pipeline completo ejecutado. Archivos exportados en:", EXPORTS_DIR)

# ===============================
if __name__ == "__main__":
    main()

