# Iris-Recognition
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Visitar_Perfil-0a66c2?style=for-the-badge&logo=linkedin)](https://www.linkedin.com/in/ivaan-escudero/)

<p align="center">
  <img src="" alt="Detección de un iris" width="600"/>
</p>

> **Reconocimiento Biométrico de Iris (Identificación 1:N)**
> Ejemplo de segmentación de un iris aislando la pupila, el tejido iridiano y delimitando las oclusiones generadas por los párpados y las pestañas para su posterior procesamiento.

---

## Tabla de Contenidos
1. [Sobre Este Proyecto](#sobre-este-proyecto)
2. [Objetivos](#objetivos)
3. [Entorno](#entorno)
4. [Estructura del sistema](#estructura-del-sistema)
5. [Instalación](#instalación)

---

## Sobre Este Proyecto

Este proyecto consiste en el diseño, desarrollo y evaluación de un motor biométrico de reconocimiento de iris orientado a la modalidad de identificación masiva (1:N). El sistema abarca el flujo completo de procesamiento: desde la detección y validación semántica de la imagen ocular, hasta el aislamiento del tejido, su normalización espacial (basada en el modelo de Rubber Sheet de Daugman) y la extracción de características mediante la aplicación de filtros log-Gabor 1D para generar una plantilla biométrica digital.

Para resolver los cuellos de botella computacionales inherentes a la comparación masiva (1:N) que colapsan las bases de datos relacionales, la arquitectura integra una infraestructura de almacenamiento de matrices multidimensionales (TileDB) que permite la extracción y registro concurrente minimizando los tiempos de ejecución. La viabilidad y precisión del algoritmo han sido auditadas empíricamente utilizando repositorios biométricos estandarizados como CASIA-Iris.

## Objetivos

- **Objetivo General:** Diseñar, desarrollar y evaluar experimentalmente un sistema integral de reconocimiento biométrico basado en el iris, optimizando su rendimiento y escalabilidad en entornos de identificación masiva de bases de datos.
- **Implementación algorítmica:** Desarrollar el flujo completo de visión por computador, abarcando la segmentación (operador íntegro-diferencial y transformada de Radon), normalización y codificación.
- **Arquitectura escalable:** Identificar y resolver los cuellos de botella computacionales de la verificación masiva aplicando procesamiento de datos especializado.
- **Evaluación empírica:** Someter el sistema a un entorno automatizado de pruebas estadísticas para auditar tiempos de ejecución y las verdaderas tasas de error (FTE, FRR y FAR).

## Entorno

El desarrollo y evaluación del sistema ha sido llevado a cabo con las siguientes especificaciones y tecnologías:

### Hardware empleado
- **Entorno de Desarrollo:** Intel Core i5-1035G1 (4 núcleos, 8 hilos), 8 GB RAM, bajo Windows 11 x64.
- **Entorno de Pruebas (Rendimiento):** AMD Ryzen 5 5500 (6 núcleos, 12 hilos), 8 GB RAM. (Evaluado tanto en host Windows 11 como en máquina virtual Ubuntu 24.04.1 LTS).

### Herramientas Software
- **Lenguaje:** Python 3.10.4
- **IDE:** Visual Studio Code 1.121.0
- **Librerías principales:**
  - `OpenCV` (4.12.0) - Procesamiento base de imágenes y filtros.
  - `NumPy` (2.2.6) - Computación matricial y operaciones vectorizadas.
  - `SciPy` (1.15.3) - Transformadas rápidas de Fourier y matemática avanzada.
  - `TileDB` (0.36.1) - Base de datos de almacenamiento matricial masivo.
  - `Tkinter` (8.6) - Generación de la Interfaz Gráfica de Usuario (GUI).
  - `Matplotlib` (3.10.9) - Representación de datos y evaluación gráfica.

## Estructura del sistema

La arquitectura del proyecto sigue un diseño modular bajo el principio de separación de responsabilidades:

```text
/ Directorio Raíz
├── fnc/                 # Núcleo matemático del sistema (algoritmos base)
│   ├── segmentar.py     # Detección de fronteras e inicialización del recorte
│   ├── normalizar.py    # Transformación al modelo Rubber Sheet (polar)
│   ├── codificar.py     # Aplicación de filtros Log-Gabor y compresión binaria
│   ├── emparejar.py     # Cálculo de distancias de Hamming (1:N) vectorizado
│   └── ... (auxiliares geométricos y de contorno)
├── usuario/             # Capa de nivel alto para gestión biométrica
│   ├── autenticar.py    # Flujo para validar una identidad contra la DB
│   ├── detectar.py      # Flujo para probar la detección de un iris
│   └── registrarIris.py # Flujo para dar de alta una nueva muestra
├── gestorBD/            # Módulo para el control de la infraestructura de persistencia
│   ├── crear_usuario.py # Inserción de matrices en TileDB
│   ├── eliminar.py      # Purgado y mantenimiento
│   └── registrar_carpeta.py # Ingreso concurrente por lotes para pruebas masivas
├── benchmarks/...       # Entorno de auditoría (Pruebas de Precisión y Rendimiento)
├── BD_Iris/             # Repositorios de imágenes en local (ej. CASIA-Iris-Interval)
├── constantes.py        # Archivo global de parámetros umbral y variables estáticas
├── haarcascade_eye.xml  # Modelo pre-entrenado para el filtro semántico de Haar
└── interfaz.py          # Módulo principal que lanza la GUI interactiva
```

## Instalación

### Pre-requisitos
Asegúrate de contar con **Python 3.10+** y **Git** instalados en tu sistema operativo (Compatible con Windows y Linux).

### Tutorial de clonado e inicialización

1. **Clonar el repositorio:**
   Abre una terminal y ejecuta:
   ```bash
   git clone https://github.com/IvanEscudero/tu-repositorio.git
   cd tu-repositorio
   ```

2. **Crear y activar un entorno virtual (Recomendado):**
   ```bash
   # En Windows
   python -m venv venv
   .\venv\Scripts\activate

   # En Linux/macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install numpy opencv-python scipy tiledb matplotlib
   ```
   
4. **Ejecutar el sistema:**
   Para lanzar la aplicación con la Interfaz Gráfica (GUI), basta con ejecutar desde la raíz del proyecto:
   ```bash
   python interfaz.py
   ```
