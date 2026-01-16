import pandas as pd
import time
import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# --- CONFIGURACIÓN ---
EXCEL_INPUT = "dni_lista.xlsx"
EXCEL_OUTPUT = "resultado_dni.xlsx"
URL_PRINCIPAL = "https://enlinea.sunedu.gob.pe/"

def manejar_aviso_error(driver):
    """Detecta y cierra el modal de error 'Aviso' si aparece."""
    try:
        # Buscamos el modal de aviso que bloquea la pantalla
        aviso = driver.find_elements(By.XPATH, "//div[contains(@class, 'p-dialog')]//span[contains(text(), 'Aviso')]")
        if aviso:
            print("⚠️ Aviso detectado: 'Debe completar la verificación'. Cerrando y reintentando...")
            # Clic en la 'X' del modal para cerrar
            btn_cerrar = driver.find_element(By.CSS_SELECTOR, ".p-dialog-header-close")
            driver.execute_script("arguments[0].click();", btn_cerrar)
            time.sleep(2)
            return True
    except:
        pass
    return False

def esperar_y_validar_cloudflare(driver):
    """Espera que Cloudflare valide. Reintenta hasta 3 veces si sale el error."""
    for intento in range(1, 4):
        print(f">>> Intento de validación {intento}/3...")
        
        # Espera prudente para que cargue el widget
        time.sleep(5) 
        
        if manejar_aviso_error(driver):
            continue # Si salió el aviso, reintenta este ciclo

        try:
            # Verificamos si Cloudflare ya dio el check verde internamente
            validado = driver.execute_script(
                'return document.querySelector("div#success")?.style.display === "flex" || '
                'document.querySelector("input[type=checkbox]") === null'
            )
            if validado:
                print("✅ Cloudflare validado automáticamente.")
                return True
        except:
            pass
            
        time.sleep(3)
    
    print("❌ No se pudo validar Cloudflare tras 3 intentos.")
    return False

def main():
    if not os.path.exists(EXCEL_INPUT):
        print(f"❌ No existe {EXCEL_INPUT}")
        return

    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options)

    try:
        driver.get(URL_PRINCIPAL)
        
        # 1. ENTRAR AL SERVICIO
        btn_selector = "button[aria-label*='VERIFICA_INSCRITO']"
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, btn_selector))).click()

        # 2. ENTRAR AL IFRAME
        iframe_xpath = "//iframe[contains(@src, 'constanciasweb.sunedu.gob.pe')]"
        WebDriverWait(driver, 20).until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, iframe_xpath)))
        print(">>> Dentro del iframe del Registro Nacional.")

        df = pd.read_excel(EXCEL_INPUT)
        dnis = df['dni'].astype(str).tolist()
        resultados = []

        for dni in dnis:
            print(f"\n--- Consultando DNI: {dni} ---")
            
            # 3. VALIDACIÓN PREVIA DE SEGURIDAD
            if not esperar_y_validar_cloudflare(driver):
                driver.refresh()
                time.sleep(5)
                driver.switch_to.frame(driver.find_element(By.XPATH, iframe_xpath))
                continue

            # 4. INGRESAR DNI
            campo_dni = WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.ID, "DNI")))
            campo_dni.clear()
            campo_dni.send_keys(dni)
            time.sleep(1)

            # 5. CLIC EN BUSCAR
            btn_buscar = driver.find_element(By.XPATH, "//span[contains(text(), 'Buscar')]")
            driver.execute_script("arguments[0].click();", btn_buscar)
            
            # 6. VERIFICAR SI APARECIÓ EL ERROR POST-BÚSQUEDA
            if manejar_aviso_error(driver):
                print(f"⚠️ Reintentando DNI {dni} por bloqueo de seguridad...")
                # Lógica de reintento simple para este DNI
                continue

            # 7. EXTRAER RESULTADOS
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.custom-table")))
                filas = driver.find_elements(By.CSS_SELECTOR, "table.custom-table tbody tr")
                for fila in filas:
                    cols = fila.find_elements(By.TAG_NAME, "td")
                    resultados.append({
                        "DNI": dni,
                        "Graduado": cols[0].text.strip(),
                        "Grado/Título": cols[1].text.strip(),
                        "Institución": cols[2].text.strip()
                    })
                print(f"✅ Éxito para {dni}")
            except:
                print(f"ℹ️ Sin resultados para {dni}")
                resultados.append({"DNI": dni, "Graduado": "No encontrado", "Grado/Título": "-", "Institución": "-"})

            # LIMPIAR PARA EL SIGUIENTE
            driver.find_element(By.XPATH, "//span[contains(text(), 'Limpiar')]").click()
            time.sleep(2)

        pd.DataFrame(resultados).to_excel(EXCEL_OUTPUT, index=False)
        print(f"\n✅ PROCESO COMPLETADO. Datos en {EXCEL_OUTPUT}")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()