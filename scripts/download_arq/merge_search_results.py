from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
import time
import os
import platform

SEARCH_URLS = [
    "https://babel.banrepcultural.org/digital/search/searchterm/juventud!1887-1909/field/all!date/mode/all!exact/conn/and!and/order/date/ad/asc",
    "https://babel.banrepcultural.org/digital/search/searchterm/estudiante!1887-1909/field/all!date/mode/all!exact/conn/and!and/order/date/ad/asc"
]

def setup_driver():
    """Configura y retorna el driver de Chrome dependiendo del sistema operativo."""
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--ignore-certificate-errors")

    sistema = platform.system()
    print(f"🖥️ Sistema operativo detectado: {sistema}")

    if sistema == "Linux":
        print("⚙️ Aplicando configuraciones específicas para Linux/Snap...")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--remote-debugging-port=9222")
        
        # --- LAS CORRECCIONES PARA EL CIERRE INESPERADO ---
        # 1. Forzar ejecución sin ventana (vital en entornos restrictivos de Linux)
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        
        # 2. Crear un perfil temporal limpio en /tmp (Snap sí tiene permisos aquí)
        perfil_temp = f"/tmp/chrome-selenium-{int(time.time())}"
        options.add_argument(f"--user-data-dir={perfil_temp}")
        # --------------------------------------------------

        rutas_snap = {
            "binario": "/snap/bin/chromium",
            "driver": "/snap/bin/chromium.chromedriver"
        }

        # Forzar binario si existe
        if os.path.exists(rutas_snap["binario"]):
            options.binary_location = rutas_snap["binario"]

        # Usar driver de Snap si existe, si no, descargar uno
        if os.path.exists(rutas_snap["driver"]):
            print("🚀 Usando ChromeDriver nativo de Snap...")
            service = Service(executable_path=rutas_snap["driver"])
        else:
            print("⬇️ Descargando ChromeDriver...")
            service = Service(ChromeDriverManager().install())

    else:
        # Configuración para Windows y macOS (se mantiene intacta)
        print("⚙️ Aplicando configuración estándar para Windows/Mac...")
        service = Service(ChromeDriverManager().install())

    print("🌐 Iniciando el navegador...")
    return webdriver.Chrome(service=service, options=options)

def main():
    driver = setup_driver()
    print("✅ ¡Navegador iniciado con éxito!\n")

    seen = set()
    results = []

    for url in SEARCH_URLS:
        print(f"\n🔍 Visitando URL base: {url}")
        driver.get(url)
        
        pagina_actual = 1
        
        # Iniciamos el ciclo de paginación
        while True:
            print(f"   📄 Extrayendo enlaces de la página {pagina_actual}...")
            time.sleep(5)  # Espera a que los resultados de la página carguen

            # 1. Extraer los links de la página actual
            links = driver.find_elements(
                By.CSS_SELECTOR,
                "a.SearchResult-container[href*='/digital/collection/']"
            )

            for a in links:
                href = a.get_attribute("href")
                if not href:
                    continue

                base = href.split("/rec/")[0]
                if base not in seen:
                    seen.add(base)
                    results.append(base)

            # 2. Intentar buscar y hacer clic en el botón "Siguiente"
            try:
                # Buscamos el contenedor <li> del botón usando el aria-label exacto de tu captura
                boton_siguiente = driver.find_element(By.CSS_SELECTOR, "li[aria-label='Next']")
                
                # Verificamos si llegamos a la última página comprobando si tiene la clase "disabled"
                clases = boton_siguiente.get_attribute("class")
                if clases and "disabled" in clases:
                    print(f"   🏁 Última página alcanzada para este término. (Páginas escaneadas: {pagina_actual})")
                    break 
                
                # Si no está deshabilitado, hacemos clic usando Javascript para evitar bloqueos
                driver.execute_script("arguments[0].click();", boton_siguiente)
                pagina_actual += 1
                
            except NoSuchElementException:
                # Por si la estructura de la página cambia repentinamente o no hay paginación del todo
                print(f"   🏁 No se encontró paginación. (Páginas escaneadas: {pagina_actual})")
                break   

    driver.quit()
    print("\n🚪 Navegador cerrado.")

    with open("periodicos_unicos_fase_3.txt", "w", encoding="utf-8") as f:
        for r in results:
            f.write(r + "\n")

    print(f"📄 Archivo guardado. Periódicos únicos totales detectados: {len(results)}")

if __name__ == "__main__":
    main()
