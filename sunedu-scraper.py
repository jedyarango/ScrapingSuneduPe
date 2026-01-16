import pandas as pd
import time
import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

# --- CONFIGURACIÓN ---
EXCEL_OUTPUT = "resultado_dni.xlsx"
EXCEL_INPUT = "dni_lista.xlsx"
URL_PRINCIPAL = "https://enlinea.sunedu.gob.pe/"

def manejar_aviso_seguridad(driver):
    """Detecta y cierra el modal de error 'Aviso' (bloqueo de seguridad) si aparece."""
    try:
        aviso = driver.find_elements(By.XPATH, "//div[contains(@class, 'p-dialog')]//span[contains(text(), 'Aviso')]")
        if aviso:
            print("⚠️ Aviso de seguridad detectado. Cerrando...")
            btn_cerrar = driver.find_element(By.CSS_SELECTOR, ".p-dialog-header-close")
            driver.execute_script("arguments[0].click();", btn_cerrar)
            time.sleep(2)
            return True
    except:
        pass
    return False

def detectar_y_gestionar_no_resultados(driver, dni, resultados):
    """
    Detecta si sale el SweetAlert de 'No se encontraron resultados'.
    Si sale: Cierra el modal, guarda el log y retorna True.
    """
    try:
        # Buscamos el texto específico dentro del contenedor de SweetAlert
        alerta_no_data = driver.find_elements(By.XPATH, "//div[@id='swal2-html-container' and contains(., 'No se encontraron resultados')]")
        
        if alerta_no_data:
            print(f"ℹ️ DNI {dni}: No tiene registros en SUNEDU.")
            
            # Intentamos cerrar la alerta haciendo clic en el botón "OK" o "Confirmar" que suele tener SweetAlert
            try:
                btn_ok = driver.find_element(By.CSS_SELECTOR, "button.swal2-confirm")
                btn_ok.click()
            except:
                # Si falla el clic normal, forzamos con JS
                driver.execute_script("document.querySelector('button.swal2-confirm').click();")
            
            time.sleep(1) # Esperar a que se cierre la animación

            # Guardamos el registro vacío
            resultados.append({
                "Graduado": "-", 
                "DNI": dni, 
                "Grado": "No se encontraron resultados con este número de DNI", 
                "Fecha Diploma": "-", "Fecha Matricula": "-", "Fecha Egreso": "-",
                "Institucion": "-", "Pais": "-"
            })
            return True
    except Exception as e:
        pass
    
    return False

def esperar_y_validar_cloudflare(driver):
    """Espera que Cloudflare valide. Reintenta hasta 3 veces internamente."""
    for intento in range(1, 4):
        print(f">>> Verificando Cloudflare (Intento {intento}/3)...")
        time.sleep(4) 
        
        if manejar_aviso_seguridad(driver):
            continue 

        try:
            validado = driver.execute_script(
                'return document.querySelector("div#success")?.style.display === "flex" || '
                'document.querySelector("input[type=checkbox]") === null'
            )
            if validado:
                print("✅ Cloudflare validado.")
                return True
        except:
            pass
        time.sleep(2)
    
    print("❌ Falló validación de Cloudflare tras 3 intentos.")
    return False

def reiniciar_navegacion(driver):
    """Refresca la página y vuelve a entrar al iframe."""
    print("🔄 Reiniciando página y contexto...")
    driver.refresh()
    time.sleep(5)
    try:
        btn_selector = "button[aria-label*='VERIFICA_INSCRITO']"
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, btn_selector))).click()
        
        iframe_xpath = "//iframe[contains(@src, 'constanciasweb.sunedu.gob.pe')]"
        WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, iframe_xpath)))
        print(">>> Contexto restaurado.")
        return True
    except Exception as e:
        print(f"⚠️ Error al restaurar contexto: {e}")
        return False

def main():
    if not os.path.exists(EXCEL_INPUT):
        print(f"❌ Falta el archivo {EXCEL_INPUT}")
        return

    options = uc.ChromeOptions()
    # options.add_argument("--start-maximized") # Opcional: Maximizar para ver mejor
    driver = uc.Chrome(options=options)

    try:
        driver.get(URL_PRINCIPAL)
        
        # 1. ENTRADA INICIAL
        btn_selector = "button[aria-label*='VERIFICA_INSCRITO']"
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, btn_selector))).click()

        iframe_xpath = "//iframe[contains(@src, 'constanciasweb.sunedu.gob.pe')]"
        WebDriverWait(driver, 20).until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, iframe_xpath)))
        
        # Preparación de datos (Relleno de ceros incluido)
        df = pd.read_excel(EXCEL_INPUT)
        dnis = df['dni'].astype(str).str.strip().str.zfill(8).tolist()
        resultados = []

        for dni in dnis:
            print(f"\n{'='*40}")
            print(f"Procesando DNI: {dni}")
            print(f"{'='*40}")
            
            dni_procesado_exito = False

            # --- CICLO MAYOR DE REINTENTOS (2 VIDAS) ---
            for ciclo in range(1, 3): 
                if dni_procesado_exito:
                    break # Si ya terminamos con este DNI, salir del ciclo de vidas

                if ciclo > 1:
                    print(f"⚠️ Iniciando CICLO DE RECUPERACIÓN {ciclo}/2 para el DNI {dni}...")
                    if not reiniciar_navegacion(driver):
                        break # Si no puede reiniciar, saltar DNI

                try:
                    # 3. VALIDACIÓN CLOUDFLARE
                    if not esperar_y_validar_cloudflare(driver):
                        # Si falla cloudflare, forzamos reinicio (pasa al siguiente ciclo del for 'ciclo')
                        continue 

                    # 4. INGRESAR DNI
                    campo_dni = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "DNI")))
                    campo_dni.clear()
                    campo_dni.send_keys(dni)
                    time.sleep(0.5)

                    # 5. BUSCAR
                    btn_buscar = driver.find_element(By.XPATH, "//span[contains(text(), 'Buscar')]")
                    driver.execute_script("arguments[0].click();", btn_buscar)
                    
                    print(">>> Buscando...")
                    time.sleep(2) # Espera breve para que salga la tabla o el aviso

                    # --- CASO A: AVISO DE "NO SE ENCONTRARON RESULTADOS" ---
                    if detectar_y_gestionar_no_resultados(driver, dni, resultados):
                        # Limpiar formulario y salir
                        try:
                            driver.find_element(By.XPATH, "//span[contains(text(), 'Limpiar')]").click()
                        except:
                            pass
                        dni_procesado_exito = True
                        break # Salir del ciclo de intentos, ir al siguiente DNI

                    # --- CASO B: AVISO DE SEGURIDAD (BLOQUEO) ---
                    if manejar_aviso_seguridad(driver):
                        print("⚠️ Bloqueo de seguridad post-búsqueda. Reintentando ciclo...")
                        continue # Reintentar validación

                    # --- CASO C: CAPTURA DE RESULTADOS ---
                    try:
                        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.custom-table")))
                        filas = driver.find_elements(By.CSS_SELECTOR, "table.custom-table tbody tr")
                        
                        if filas:
                            for fila in filas:
                                cols = fila.find_elements(By.TAG_NAME, "td")
                                if len(cols) >= 3:
                                    # Extracción y limpieza
                                    texto_c0 = cols[0].text.strip().split('\n')
                                    nombre = texto_c0[0] if texto_c0 else "-"
                                    dni_clean = texto_c0[1].replace("DNI", "").strip() if len(texto_c0) > 1 else dni

                                    texto_c1 = cols[1].text.strip().split('\n')
                                    grado, f_dip, f_mat, f_egr = "-", "-", "-", "-"
                                    for linea in texto_c1:
                                        if "Fecha de diploma:" in linea: f_dip = linea.replace("Fecha de diploma:", "").strip()
                                        elif "Fecha matrícula:" in linea: f_mat = linea.replace("Fecha matrícula:", "").strip()
                                        elif "Fecha egreso:" in linea: f_egr = linea.replace("Fecha egreso:", "").strip()
                                        elif "Grado o Título" not in linea: grado = linea.strip()

                                    texto_c2 = cols[2].text.strip().split('\n')
                                    inst = texto_c2[0] if texto_c2 else "-"
                                    pais = texto_c2[1] if len(texto_c2) > 1 else "-"

                                    resultados.append({
                                        "Graduado": nombre, "DNI": dni_clean, "Grado": grado,
                                        "Fecha Diploma": f_dip, "Fecha Matricula": f_mat, "Fecha Egreso": f_egr,
                                        "Institucion": inst, "Pais": pais
                                    })
                            print(f"✅ Datos capturados correctamente.")
                            dni_procesado_exito = True
                        
                        # Limpiar para el siguiente
                        try:
                            driver.find_element(By.XPATH, "//span[contains(text(), 'Limpiar')]").click()
                            time.sleep(1)
                        except:
                            pass
                        break # Salir del ciclo, ir al siguiente DNI

                    except TimeoutException:
                        # Si no hay tabla y no hubo aviso de "No resultados", algo raro pasó
                        print("⚠️ Timeout esperando tabla. Posible error de carga.")
                        # Esto provocará que el ciclo continue y se intente de nuevo o se refresque
                
                except Exception as e:
                    print(f"⚠️ Error crítico en ciclo {ciclo}: {e}")
                    # Si falla, el loop 'for ciclo' continuará a la siguiente iteración (reinicio)

            # Si terminaron los 2 ciclos y no hubo éxito
            if not dni_procesado_exito:
                print(f"❌ FRACASO TOTAL con DNI {dni} tras reintentos.")
                resultados.append({"Graduado": "Error Sistema", "DNI": dni, "Grado": "Error tras 6 intentos (reinicio pág)", "Institucion": "-"})
            
            # Guardado parcial por seguridad
            if len(resultados) % 5 == 0:
                pd.DataFrame(resultados).to_excel(EXCEL_OUTPUT, index=False)

        # Guardado final
        pd.DataFrame(resultados).to_excel(EXCEL_OUTPUT, index=False)
        print(f"✅ Finalizado. Archivo creado: {EXCEL_OUTPUT}")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()