# 🎓 SUNEDU Scraper - Automatización de Obtención de Grados y Títulos con DNI

## ⚠️ Aviso Legal
Este software ha sido desarrollado con fines educativos y de automatización de procesos administrativos propios. 
El uso excesivo o malintencionado de herramientas de scraping puede violar los términos de servicio del sitio web objetivo. 
Úsalo con responsabilidad y establece pausas prudentes si procesas grandes volúmenes de datos

## 📋 Descripción
Este proyecto es una herramienta de automatización desarrollada en Python para realizar consultas masivas en el portal en línea de la **SUNEDU** (Superintendencia Nacional de Educación Superior Universitaria).

El script permite verificar una lista de personas (mediante su DNI) cuenta con grados académicos o títulos profesionales registrados, manejando automáticamente las validaciones de seguridad y extraer los datos de los mismos.

## 🚀 Características Principales

* **Evasión de Cloudflare:** Utiliza `undetected-chromedriver` para superar la validación "Verifica que eres un ser humano" sin interacción manual.
* **Manejo de Iframes:** Navegación inteligente dentro de los marcos incrustados del portal.
* **Limpieza de Datos:**
    * Normaliza DNIs (agrega ceros a la izquierda si faltan).
    * Separa campos (Grado, Fechas, Institución, País) en columnas limpias.
    * Distingue correctamente el título académico ignorando textos vacios.
* **Resiliencia:** Sistema de reintentos automático ante errores de conexión o bloqueos temporales.
* **Manejo de Excepciones:** Gestiona avisos de "No se encontraron resultados" y alertas de seguridad.

---

## 🛠️ Tecnologías y Librerías

Breve reseña de las librerías utilizadas en este proyecto:

| Librería | Propósito |
| :--- | :--- |
| **`pandas`** | El corazón del manejo de datos. Se utiliza para leer el archivo Excel de entrada, manipular la información en memoria (DataFrames) y exportar el reporte final limpio y estructurado. |
| **`undetected_chromedriver`** | Una versión modificada del driver de Chrome. Es vital para este proyecto ya que evita que el sistema de seguridad de SUNEDU (Cloudflare) detecte que el navegador está siendo controlado por un robot. |
| **`selenium`** | Framework de automatización. Permite controlar el navegador: hacer clic en botones, rellenar el campo DNI, esperar a que carguen las tablas y extraer el texto HTML. |
| **`openpyxl`** | Dependencia necesaria para que *pandas* pueda leer y escribir archivos `.xlsx` modernos. |
| **`os`** | sistema operativo (SO), permitiéndote realizar tareas como manipular archivos, directorios, ejecutar comandos del sistema y obtener información del entorno.

---

## 📋 Requisitos Previos

1.  Tener instalado **Python 3.x**.
2.  Tener instalado el navegador **Google Chrome**.
3.  Instalar las dependencias del proyecto ejecutando:

```bash
pip install pandas openpyxl selenium undetected-chromedriver setuptools
```

## ⚙️ Estructura del Archivo de Entrada
El script busca un archivo llamado dni_lista.xlsx en la misma carpeta. 
Debe tener la siguiente estructura simple:
*  Nombre del archivo: dni_lista.xlsx
*  Hoja: Hoja1 (por defecto).
*  Encabezado: Una columna llamada **dni** .
  

<img width="418" height="394" alt="image" src="https://github.com/user-attachments/assets/55fe0007-d454-40a3-bb54-48efb534183c" />

Nota: No importa si el Excel eliminó el cero inicial (ej. 1234567), el script lo corregirá automáticamente a 01234567.

## 🚀Uso
Clona este repositorio o descarga el script.
Coloca tu archivo **dni_lista.xlsx** en la carpeta del proyecto.
Ejecuta el script principal:

```bash
python sunedu_scraper.py
```

Asegúrate de reemplazar sunedu_scraper.py con el nombre real de tu archivo .py
Se abrirá una ventana de Chrome, no la cierres ni la minimices, el robot trabajará solo.
Al finalizar, se generará el archivo **resultado_dni.xlsx** .

## 📊 Datos Extraídos (Columnas de Salida)
El archivo generado **resultado_dni.xlsx** contendrá las siguientes columnas ordenadas:

1.  Graduado:
2.  Nombre completo de la persona.
3.  DNI: Número de documento validado (8 dígitos).
4.  Grado: El nombre exacto del grado o título obtenido (ej. BACHILLER EN INGENIERÍA DE SISTEMAS).
5.  Fecha Diploma:
6.  Fecha de emisión del diploma.
7.  Fecha Matricula:
8.  Fecha de primera matrícula (si está disponible).
9.  Fecha Egreso: Fecha de egreso (si está disponible).
10.  Institucion: Universidad o institución que otorga el grado.
11.  Pais: País de la institución.
    


