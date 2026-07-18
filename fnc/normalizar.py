# Normalizar la región del iris desenrollando el anillo circular en un bloque rectangular polar de dimensiones constantes.
from constantes import RES_RADIAL, RES_ANGULAR
from cv2 import circle
import numpy as np

def Normalizar(img, x_iris, y_iris, r_iris, x_pupila, y_pupila,
                r_pupila, res_radial = RES_RADIAL, res_angular = RES_ANGULAR):
    """
    DESCRIPCIÓN:
        Normalizar la región del iris transformando las coordenadas cartesianas del anillo 
        circular en un bloque rectangular polar (Modelo Rubber Sheet de Daugman).

    INPUT:
        img         - Imagen original de entrada del iris (puede contener ruido como nan).
        x_iris      - Coordenada X del centro del círculo que define el límite del iris.
        y_iris      - Coordenada Y del centro del círculo que define el límite del iris.
        r_iris      - Radio del círculo que define el límite exterior del iris.
        x_pupila    - Coordenada X del centro del círculo que define el límite de la pupila.
        y_pupila    - Coordenada Y del centro del círculo que define el límite de la pupila.
        r_pupila    - Radio del círculo que define el límite interior de la pupila.
        res_radial  - Resolución radial (dimensión vertical de la matriz polar).
        res_angular - Resolución angular (dimensión horizontal de la matriz polar).

    OUTPUT:
        m_polar     - Representación normalizada de la textura del iris en 2D.
        ruido_polar - Máscara booleana normalizada que indica las zonas de ruido ocluidas.
    """
    px_radio = res_radial + 2
    div_angulares = res_angular - 1

    theta = np.linspace(0, 2 * np.pi, div_angulares + 1)

    # Calcular el desplazamiento físico del centro de la pupila respecto al centro del iris
    ox = x_pupila - x_iris
    oy = y_pupila - y_iris

    # Determinar el signo direccional para la corrección trigonométrica
    if ox <= 0:
        sgn = -1
    else:
        sgn = 1
    
    if ox == 0 and oy > 0:
        sgn = 1

    a = np.ones(div_angulares + 1) * (ox**2 + oy**2)

    # Calcular el ángulo de desviación evitando divisiones por cero
    if ox == 0:
        phi = np.pi / 2
    else:
        phi = np.arctan(oy / ox)

    b = sgn * np.cos(np.pi - phi - theta)

    # Calcular matemáticamente el radio exterior del iris en función del ángulo dinámico
    vector_r = np.sqrt(a) * b + np.sqrt(a * b**2 - (a - r_iris**2))
    vector_r = vector_r - r_pupila

    # Generar la matriz radial aplicando Broadcasting de NumPy
    gradiente = np.linspace(0, 1, px_radio)[:, np.newaxis]
    matriz_r = gradiente * vector_r
    matriz_r = matriz_r + r_pupila

    # Excluir los valores exactos de las fronteras (pupila/iris e iris/esclerótica)
    # para no introducir ruido del blanco del ojo o del negro de la pupila
    matriz_r = matriz_r[1 : px_radio - 1, :]

    # Calcular la ubicación cartesiana exacta de cada punto de dato extraído del anillo
    xo = matriz_r * np.cos(theta)
    yo = matriz_r * np.sin(theta)

    # Trasladar al centro de la pupila y limitar las coordenadas para no desbordar la imagen
    xo = np.round(x_pupila + xo).astype(int)
    xo = np.clip(xo, 0, img.shape[1] - 1)
    
    yo = np.round(y_pupila - yo).astype(int)
    yo = np.clip(yo, 0, img.shape[0] - 1)

    # Extraer los valores de intensidad fotográfica hacia la representación polar normalizada
    m_polar = img[yo, xo]
    m_polar = m_polar / 255.0

    # Crear la matriz de ruido identificando dónde quedaron alojados los nans
    ruido_polar = np.isnan(m_polar)

    # Dibujar el patrón circular de extracción sobre la imagen original como debug 
    img[yo, xo] = 255

    # Dibujar los límites analizados sobre la foto
    circle(img, (x_iris, y_iris), r_iris, 255, 1)           # cv2
    circle(img, (x_pupila, y_pupila), r_pupila, 255, 1)     # cv2

    # Reemplazar los valores nan por una intensidad media neutra antes de codificar con filtros Gabor
    m_polar[ruido_polar] = 0.5
    prom = np.mean(m_polar)
    m_polar[ruido_polar] = prom

    return m_polar, ruido_polar


"""
def CoordenadasCirculo(centro, radio, tam_img, num_lados=600):
    
    DESCRIPCIÓN:
        Encontrar las coordenadas cartesianas de un círculo a partir de su centro y radio.
        (Refactorizada para servir como utilidad matemática externa si es requerida).

    INPUT:
        centro    - Tupla o lista con las coordenadas (X, Y) del centro del círculo.
        radio     - Radio del círculo en píxeles.
        tam_img   - Tamaño de la imagen para asegurar que las coordenadas no se desbordan.
        num_lados - Número de puntos matemáticos del polígono que emulará al círculo.

    OUTPUT:
        x, y      - Matrices unidimensionales con las coordenadas del círculo.
    
    # Crear un espacio angular
    a = np.linspace(0, 2 * np.pi, 2 * num_lados + 1)
    
    # Proyectar el radio mediante trigonometría
    x = np.round(radio * np.cos(a) + centro[0]).astype(int)
    y = np.round(radio * np.sin(a) + centro[1]).astype(int)

    # Limitar los valores para que no desborden los límites de la imagen usando NumPy
    x = np.clip(x, 0, tam_img[1] - 1)
    y = np.clip(y, 0, tam_img[0] - 1)

    return x, y
    """