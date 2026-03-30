from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time

SEARCH_URLS = [
    # aquí pondrás tus URLs
    "https://babel.banrepcultural.org/digital/search/searchterm/estudiante!1872-1886/field/all!date/mode/all!exact/conn/and!and/order/date/ad/asc",
    "https://babel.banrepcultural.org/digital/search/searchterm/estudiantil!1872-1886/field/all!date/mode/all!exact/conn/and!and/order/date/ad/asc",
    "https://babel.banrepcultural.org/digital/search/searchterm/juventud!1872-1886/field/all!date/mode/all!exact/conn/and!and/order/date/ad/asc",
    "https://babel.banrepcultural.org/digital/search/searchterm/joven!1872-1886/field/all!date/mode/all!exact/conn/and!and/order/date/ad/asc",
    "https://babel.banrepcultural.org/digital/search/searchterm/universidad!1872-1886/field/all!date/mode/all!exact/conn/and!and/order/date/ad/asc",
    "https://babel.banrepcultural.org/digital/search/searchterm/colegio!1872-1886/field/all!date/mode/all!exact/conn/and!and/order/date/ad/asc",
]

def main():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--ignore-certificate-errors")

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

    with open("periodicos_unicos.txt", "w", encoding="utf-8") as f:
        for r in results:
            f.write(r + "\n")

    print(f"Periódicos únicos detectados: {len(results)}")

if __name__ == "__main__":
    main()
