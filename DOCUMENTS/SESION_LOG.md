# SESION_LOG.md
> Registro cronológico de cada sesión de trabajo.
> Formato: una entrada por sesión. Actualizar al terminar, no durante.

---

## Plantilla de entrada

```
## [FECHA] — Sesión [N]
**Fase:** [0-5]
**Objetivo de la sesión:** [qué querías lograr]
**Lo que se hizo:**
- 
**Lo que funcionó:**
- 
**Lo que no funcionó / problemas encontrados:**
- 
**Próximo paso:**
**Archivos creados/modificados:**
- 
**Preguntas abiertas para la próxima sesión:**
- 
```

---

## 11/04/2026 — Sesión 1
**Fase:** 0 (planificación)
**Objetivo de la sesión:** Definir arquitectura del pipeline mejorado con ML y organizar documentación del proyecto.
**Lo que se hizo:**
- Conversación con Claude sobre el estado actual del proyecto
- Definición de la arquitectura en 5 fases
- Creación de los 4 archivos `.md` de documentación
- Comprensión de los límites de uso de Claude y estrategia de trabajo
**Lo que funcionó:**
- La arquitectura propuesta integra bien el trabajo historiográfico ya hecho con los objetivos de ML
**Lo que no funcionó / problemas encontrados:**
- Repositorio de GitHub no fue accesible durante la sesión (límite de tasa)
**Próximo paso:** Completar los campos marcados con [COMPLETAR] en CONTEXTO_PROYECTO.md y DECISIONES.md. Luego iniciar Fase 1 con diagnóstico del CER actual.
**Archivos creados/modificados:**
- `DOCUMENTS/CONTEXTO_PROYECTO.md`
- `DOCUMENTS/PIPELINE_ESTADO.md`
- `DOCUMENTS/DECISIONES.md`
- `DOCUMENTS/SESION_LOG.md`
**Preguntas abiertas para la próxima sesión:**
- ¿Cuáles son los períodos históricos prioritarios exactos?
- ¿Qué páginas del corpus tienen ya transcripción manual para usarlas como muestra de evaluación de CER?


## 14/04/2026 — Sesión 2
**Fase:** 0
**Objetivo de la sesión:** Descarga Fase 3
**Lo que se hizo:**
- 1.  Agregar --no-sandbox y --disable-dev-shm-usage. Además, si estás ejecutando esto en un servidor sin monitor o en una terminal pura (como WSL), Chrome necesita ejecutarse en modo invisible (--headless). Cambios en la función main.
```
    def main():
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--ignore-certificate-errors")
        
        # --- ARGUMENTOS CLAVE PARA LINUX/SNAP ---
        options.add_argument("--no-sandbox") # Desactiva el sandbox, vital para Snap
        options.add_argument("--disable-dev-shm-usage") # Soluciona problemas de memoria compartida
        options.add_argument("--headless=new") # Ejecuta Chrome en segundo plano (sin interfaz)
        options.add_argument("--disable-gpu") # Recomendado cuando se usa headless
        # ----------------------------------------

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

        seen = set()
        results = []

        for url in SEARCH_URLS:
            driver.get(url)
            time.sleep(5)

            links = driver.find_elements(
                By.CSS_SELECTOR,
                "a.SearchResult-container[href*='/digital/collection/']"
            )

            for a in links:
                href = a.get_attribute("href")
                if not href:
                    continue

                # normalizar: quitar /rec/x
                base = href.split("/rec/")[0]

                if base not in seen:
                    seen.add(base)
                    results.append(base)

        driver.quit()

        with open("periodicos_unicos_fase_3.txt", "w", encoding="utf-8") as f:
            for r in results:
                f.write(r + "\n")

        print(f"Periódicos únicos detectados: {len(results)}")
```
    
2. Las anteriores mejores dejaron congelado el programa por "standoff" (webdriver_manager descargó el driver, este intentó abrir el Chromium de Snap, y se quedaron esperando infinitamente a comunicarse porque Snap bloquea los puertos internos que Selenium usa por defecto para hablar con el navegador).
Para ello fue necesario: 
- Indicarle explícitamente al script dónde está el navegador (binary_location).
- Abrir un puerto de depuración (--remote-debugging-port=9222) para que el driver tenga una vía libre de comunicación que Snap no bloquee.
- Intentar usar el driver que ya viene empaquetado con Snap, en lugar de descargar uno nuevo que pueda tener versiones incompatibles.
También: 
- Añadí unos print() antes de la inicialización y en las visitas. Así, si se vuelve a quedar pegado, sabrás exactamente en qué línea ocurrió en lugar de ver una pantalla en negro.

- Implementé una verificación os.path.exists(): si Ubuntu ya tiene el driver correcto instalado por Snap, lo usa. Si no, recae en ChromeDriverManager.

- Añadí el --remote-debugging-port=9222 que es el salvavidas para la comunicación entre procesos en entornos restringidos.
 3.  Se busca hacer que el script sea multiplataforma, pues inicialmente estaba pensando para funcionar exclusivamente en Windows. 
Para lograr esto, se uso la librería nativa platform de Python. Esta librería detecta en qué sistema operativo se está ejecutando el script y, basándonos en eso, se aplican  las configuraciones restrictivas de Snap solo si estamos en Linux, dejando a Windows con la configuración estándar que fluye sin problemas.
También se ha separado la creación del navegador en su propia función (setup_driver)
4. Modificación de a función setup_driver() para forzar el modo "Headless" (invisible) y asignarle una carpeta temporal al perfil de Chrome, evadiendo las restricciones de Snap.

**Lo que funcionó:**
5. Hubo muhcos conflictos con Chromium en su versión snap por lo que se opto por intalar la version .deb de Chrome para correr el programa.
6. Se le agregaron elementos para que el Web Scrapper funcione a través de la paginación del sitio de donde se extrae la información.
**Lo que no funcionó / problemas encontrados:**
- Fallas por incompatibilidad (error DevToolsActivePort file doesn't exist) que he tenido con el script merge_search_results.py: ChromeDriver está intentando levantar la versión de Chromium instalada a través de Snap, y esta se está "crasheando" inmediatamente al abrir. Esto ocurre principalmente por dos razones: restricciones de seguridad del "sandbox" de Snap o problemas de gestión de memoria compartida en Linux.
**Próximo paso:**
Esperar que se descargue el corpus para proceder con el OCR
**Archivos creados/modificados:**
- modificados:     logs/corpus_config.json
	borrados:        logs/manual_download_urls.txt
	modificados:     logs/metadata_errors.log
	modificados:     logs/metadata_state.json
	borrados:        logs/ocr.log
	borrados:        logs/qc_report.json
	borrados:        logs/qc_report.txt

**Preguntas abiertas para la próxima sesión:**
- ¿Cómo consolidar todo el corpus que no se pudo descargar? 


