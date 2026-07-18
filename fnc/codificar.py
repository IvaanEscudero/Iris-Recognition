# Extraer y codificar las características matemáticas de la región del iris en una plantilla binaria utilizando filtros de Gabor.
import numpy as np
import cv2
from constantes import LONG_ONDA_MIN, SIGMA_ONF 

def ConvolucionGabor(img, long_onda_min=LONG_ONDA_MIN, sigma_onf=SIGMA_ONF):
    """
    DESCRIPCIÓN:
        Convolucionar cada fila de una imagen con filtros log-Gabor 1D utilizando la transformada de Fourier.

    INPUT:
        img               - La imagen a convolucionar.
        long_onda_min     - Longitud de onda del filtro base.
        sigma_onf         - Relación entre la desviación estándar de la gaussiana y la frecuencia central.

    OUTPUT:
        parte_real        - Matriz con la parte real del resultado de la convolución.
        parte_imaginaria  - Matriz con la parte imaginaria del resultado de la convolución.
    """
    # Preasignar tamaños
    filas, n_datos = img.shape
    log_gabor = np.zeros(n_datos, dtype=np.float32)

    # Generar valores de frecuencia de 0 a 0.5
    radio = np.arange(n_datos / 2 + 1) / (n_datos / 2) / 2
    radio[0] = 1

    # Calcular el componente radial del filtro
    f0 = 1.0 / long_onda_min
    # Ecuación fundamental Filtro Log-Gabor
    log_gabor[0 : int(n_datos / 2) + 1] = np.exp((- (np.log(radio / f0)) ** 2) / (2 * np.log(sigma_onf) ** 2))
    log_gabor[0] = 0.0

    # Convertir imagen a tipo flotante para procesar con OpenCV
    imagen_f32 = np.float32(img)

    # Aplicar Transformada de Fourier Discreta (DFT) por filas usando OpenCV
    dft = cv2.dft(imagen_f32, flags=cv2.DFT_ROWS | cv2.DFT_COMPLEX_OUTPUT)

    # Preparar el filtro para multiplicar por los 2 canales espectrales (real e imaginario)
    log_gabor_2d = np.zeros((filas, n_datos, 2), dtype=np.float32)
    log_gabor_2d[:, :, 0] = log_gabor
    log_gabor_2d[:, :, 1] = log_gabor

    # Multiplicar espectros en el dominio de la frecuencia con OpenCV
    dft_filtrado = cv2.multiply(dft, log_gabor_2d)

    # Aplicar Transformada de Fourier Inversa (IDFT) por filas usando OpenCV
    idft = cv2.idft(dft_filtrado, flags=cv2.DFT_ROWS | cv2.DFT_SCALE | cv2.DFT_COMPLEX_OUTPUT)

    # Extraer parte real e imaginaria directamente
    parte_real = idft[:, :, 0]
    parte_imaginaria = idft[:, :, 1]

    return parte_real, parte_imaginaria

def Codificar(m_polar, m_ruido, long_onda_min=LONG_ONDA_MIN, sigma_onf=SIGMA_ONF):
    """
    DESCRIPCIÓN:
        Generar la plantilla biométrica del iris y la máscara de ruido a partir de la región polar normalizada.

    INPUT:
        m_polar         - Región del iris normalizada (matriz 2D).
        m_ruido         - Región de ruido normalizada (matriz 2D).
        long_onda_min   - Longitud de onda base para el filtro log-Gabor.
        sigma_onf       - Parámetro de ancho de banda del filtro.

    OUTPUT:
        plantilla         - Plantilla biométrica binaria del iris.
        mascara           - Máscara binaria de ruido del iris.
    """
    # Convolucionar región normalizada con filtros de Gabor
    parte_real, parte_imaginaria = ConvolucionGabor(m_polar, long_onda_min, sigma_onf)

    filas = m_polar.shape[0]
    columnas = m_polar.shape[1]
    
    # Inicializar matrices de salida
    plantilla = np.zeros((filas, 2 * columnas), dtype=np.uint8)
    mascara = np.zeros((filas, 2 * columnas), dtype=np.uint8)

    # Cuantificar fase
    h1 = parte_real > 0
    h2 = parte_imaginaria > 0

    # Calcular amplitud matemática con OpenCV para descartar información de fase inútil
    amplitud = cv2.magnitude(parte_real, parte_imaginaria)
    h3 = amplitud < 0.0001

    # Construir plantilla biométrica y máscara de ruido
    # Si h1 = [ A, B, C ]
    # Si h2 = [ X, Y, Z ]
    # Plantilla tendrá el doble de ancho = [ A, X, B, Y, C, Z ]
    plantilla[:, 0::2] = h1
    plantilla[:, 1::2] = h2

    # si un píxel está tapado O el cálculo matemático no es fiable, 
    # se marca como un 1 (píxel inútil o ruido). 
    # Luego, ese resultado se entrelaza en las columnas pares e impares de la máscara final.
    mascara[:, 0::2] = m_ruido | h3
    mascara[:, 1::2] = m_ruido | h3

    return plantilla, mascara