# Segmentar la región del iris y la pupila, e identificar y aislar las zonas de ruido.
from fnc.limites import BuscarLimiteInterior, BuscarLimiteExterior
from fnc.lineas import EncontrarLinea, CoordenadasLinea
from constantes import UMBRAL_PESTANA
from cv2 import fillPoly
import numpy as np

def Segmentar(img_ojo, umbral_pestanas=UMBRAL_PESTANA):
    """
    DESCRIPCIÓN:
        Segmentar la región del iris a partir de la imagen original del ojo.
        Indicar y enmascarar las regiones con ruido (párpados, pestañas y brillos).

    INPUT:
        img_ojo         - Imagen original del ojo en escala de grises.
        umbral_pestanas - Umbral de intensidad para discriminar las pestañas (píxeles muy oscuros).

    OUTPUT:
        cir_iris      - Coordenadas Y, X y radio del límite exterior del iris.
        cir_pupila    - Coordenadas Y, X y radio del límite interior de la pupila.
        img_con_ruido - Imagen original con la ubicación del ruido marcada con valores NaN.
    """
    # Encontrar el límite interior del iris usando el operador de Daugman
    y_pupila, x_pupila, r_pupila = BuscarLimiteInterior(img_ojo)
    
    # Encontrar el límite exterior del iris usando el centro de la pupila como anclaje
    y_iris, x_iris, r_iris = BuscarLimiteExterior(img_ojo, y_pupila, x_pupila, r_pupila)

    # Empaquetar los límites redondeados a enteros para su uso en matrices
    cir_pupila = [int(np.round(y_pupila)), int(np.round(x_pupila)), int(np.round(r_pupila))]
    cir_iris = [int(np.round(y_iris)), int(np.round(x_iris)), int(np.round(r_iris))]

    # Calcular la caja delimitadora (bounding box) del iris acotada a los bordes de la imagen
    tam_img = img_ojo.shape
    y_min = np.clip(cir_iris[0] - cir_iris[2], 0, tam_img[0] - 1)
    y_max = np.clip(cir_iris[0] + cir_iris[2], 0, tam_img[0] - 1)
    x_min = np.clip(cir_iris[1] - cir_iris[2], 0, tam_img[1] - 1)
    x_max = np.clip(cir_iris[1] + cir_iris[2], 0, tam_img[1] - 1)

    # Recortar la sub-imagen que aísla la zona de interés del iris
    img_iris = img_ojo[y_min : y_max + 1, x_min : x_max + 1]

    # Encontrar las máscaras de oclusión de los párpados superior e inferior
    mascara_sup = EncontrarParpadoSuperior(tam_img, img_iris, y_min, x_min, cir_pupila[0], cir_pupila[2])
    mascara_inf = EncontrarParpadoInferior(tam_img, img_iris, cir_pupila[0], cir_pupila[2], y_min, x_min)

    # Enmascarar la imagen original convirtiéndola a coma flotante para soportar NaN
    img_con_ruido = img_ojo.astype(float)
    
    # Sumar las máscaras (los valores nan propagarán el ruido al sumarse con los píxeles reales)
    img_con_ruido = img_con_ruido + mascara_sup + mascara_inf

    # Indexación booleana (numpy)
    # los pixeles negros por debajo del umbral se marcan como ruido
    img_con_ruido[img_ojo < umbral_pestanas] = np.nan

    return cir_iris, cir_pupila, img_con_ruido


def EncontrarParpadoSuperior(tam_img, img_iris, y_min, x_min, y_pupila, r_pupila):
    """
    DESCRIPCIÓN:
        Generar una máscara matemática para la región ocluida por el párpado superior.

    INPUT:
        tam_img  - Tupla con el tamaño de la imagen original del ojo.
        img_iris - Sub-imagen recortada que contiene la zona del iris.
        y_min    - Coordenada Y mínima de la caja delimitadora del iris.
        x_min    - Coordenada X mínima de la caja delimitadora del iris.
        y_pupila - Coordenada Y del centro de la pupila.
        r_pupila - Radio de la pupila.

    OUTPUT:
        mascara  - Matriz del tamaño de la imagen original con NaN en la zona del párpado y 0 en el resto.
    """
    # Recortar la región específica donde es anatómicamente probable encontrar el párpado superior
    parpado_sup = img_iris[0 : y_pupila - y_min - r_pupila, :]
    
    # Detectar paramétricamente las líneas rectas en la región recortada
    lineas = EncontrarLinea(parpado_sup)
    mascara = np.zeros(tam_img, dtype=float)

    if lineas.size > 0:
        # Obtener las coordenadas continuas de la línea y trasladarlas al sistema de coordenadas original
        x, y = CoordenadasLinea(lineas, parpado_sup.shape)
        y = np.round(y + y_min - 1).astype(int)
        x = np.round(x + x_min - 1).astype(int)

        # Construir un polígono cerrado proyectando la línea hacia el borde superior de la imagen
        puntos = np.column_stack((x, y)).astype(np.int32)
        puntos = np.vstack([puntos, [x[-1], 0], [x[0], 0]])
        
        # Dibujar y rellenar el polígono de oclusión
        mascara_binaria = np.zeros(tam_img, dtype=np.uint8)
        fillPoly(mascara_binaria, [puntos], 1) # cv2
        
        # Indexación booleana (numpy)
        # Asignar ruido exclusivamente a los píxeles contenidos dentro del polígono
        mascara[mascara_binaria == 1] = np.nan

    return mascara


def EncontrarParpadoInferior(tam_img, img_iris, y_pupila, r_pupila, y_min, x_min):
    """
    DESCRIPCIÓN:
        Generar una máscara matemática para la región ocluida por el párpado inferior.

    INPUT:
        tam_img  - Tupla con el tamaño de la imagen original del ojo.
        img_iris - Sub-imagen recortada que contiene la zona del iris.
        y_pupila - Coordenada Y del centro de la pupila.
        r_pupila - Radio de la pupila.
        y_min    - Coordenada Y mínima de la caja delimitadora del iris.
        x_min    - Coordenada X mínima de la caja delimitadora del iris.

    OUTPUT:
        mascara  - Matriz del tamaño de la imagen original con NaN en la zona del párpado y 0 en el resto.
    """
    # Recortar la región inferior específica para aislar la búsqueda del borde
    parpado_inf = img_iris[y_pupila - y_min + r_pupila - 1 : img_iris.shape[0], :]
    
    # Detectar paramétricamente las líneas rectas en la región recortada
    lineas = EncontrarLinea(parpado_inf)
    mascara = np.zeros(tam_img, dtype=float)

    if lineas.size > 0:
        # traslación de sistemas de coordenadas al espacio de la imagen original
        x, y = CoordenadasLinea(lineas, parpado_inf.shape)
        y = np.round(y + y_pupila + r_pupila - 3).astype(int)
        x = np.round(x + x_min - 2).astype(int)

        # Construir un polígono cerrado proyectando la línea hacia el borde inferior de la imagen
        puntos = np.column_stack((x, y)).astype(np.int32)
        puntos = np.vstack([puntos, [x[-1], tam_img[0] - 1], [x[0], tam_img[0] - 1]])
        
        # Rellenar la zona inferior del polígono
        mascara_binaria = np.zeros(tam_img, dtype=np.uint8)
        fillPoly(mascara_binaria, [puntos], 1) # cv2
        
        # Indexación booleana (numpy)
        # Asignar ruido a los píxeles ocluidos por el párpado
        mascara[mascara_binaria == 1] = np.nan

    return mascara