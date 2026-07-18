# Detectar líneas y bordes mediante la Transformada de Radon y detección de bordes para delimitar los párpados
import numpy as np
import cv2

def TransformadaRadon(img, rango_theta):
    """
    DESCRIPCIÓN:
        Simular la Transformada de Radon utilizando rotaciones de OpenCV.
        Proyectar las intensidades de la imagen a lo largo de diferentes ángulos.
        
    INPUT:
        img         - Imagen de entrada (matriz de bordes binaria o de intensidades).
        rango_theta - Vector de ángulos en grados (0-180) a evaluar.
        
    OUTPUT:
        sinograma   - Matriz resultante de Radon (distancia x ángulo).
    """
    alto, ancho = img.shape
    
    
    # Evitar el recorte de las esquinas al rotar la imagen mediante pitagoras para crear un lienzo expandido
    diagonal = int(np.ceil(np.sqrt(alto ** 2 + ancho ** 2)))
    
    # Calcular los márgenes de relleno necesarios para centrar la imagen
    pad_alto = (diagonal - alto) // 2
    pad_ancho = (diagonal - ancho) // 2
    
    # Añadir bordes negros para centrar la imagen en un lienzo cuadrado grande usando OpenCV
    img_expandida = cv2.copyMakeBorder(img, pad_alto, pad_alto, pad_ancho, pad_ancho, cv2.BORDER_CONSTANT, value=0)
    
    # Calcular las coordenadas del centro del nuevo lienzo expandido
    centro = (img_expandida.shape[1] // 2, img_expandida.shape[0] // 2)
    
    # Proyecciones de cada ángulo
    sinograma = []
    
    for angulo in rango_theta:
        # Calcular matriz de rotación y aplicar rotación afín
        m_rotacion = cv2.getRotationMatrix2D(centro, -angulo, 1.0)
        img_rotada = cv2.warpAffine(img_expandida, m_rotacion, 
                                       (img_expandida.shape[1], img_expandida.shape[0]), 
                                       flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        
        # Sumar las intensidades a lo largo del eje vertical para simular la integral del rayo de Radon
        proyeccion = np.sum(img_rotada, axis=0)
        sinograma.append(proyeccion)
    
    # Convertir a matriz y trasponer para obtener dimensiones [distancia, angulo]
    sinograma = np.array(sinograma).T
    return sinograma

def CoordenadasLinea(lineas, tam_img):
    """
    DESCRIPCIÓN:
        Encontrar las coordenadas X e Y de los puntos que forman una línea detectada.

    INPUT:
        lineas     - Parámetros de la línea en forma polar.
        tam_img    - Tupla con las dimensiones de la imagen original.

    OUTPUT:
        x          - Matriz de coordenadas X de la línea.
        y          - Matriz de coordenadas Y de la línea recortada a los bordes.
    """
    # Generar vector de coordenadas X
    x = np.arange(tam_img[1])
    
    # Calcular coordenadas Y correspondientes a partir de la ecuación de la recta
    y = (-lineas[0, 2] - lineas[0, 0] * x) / lineas[0, 1]

    # Limitar las coordenadas Y para no desbordar los límites de la imagen usando truncamiento rápido
    y = np.clip(y, 0, tam_img[0] - 1)

    return x, y


def FiltroCanny(img, sigma, vert, horz):
    """
    DESCRIPCIÓN:
        Extraer los bordes de la imagen usando el operador de Sobel y suavizado Gaussiano de OpenCV.
        Implementación orientada a resaltar bordes horizontales o verticales específicamente.

    INPUT:
        img    - La imagen en escala de grises.
        sigma  - Desviación estándar para el filtro Gaussiano.
        vert   - Multiplicador para activar/desactivar bordes verticales.
        horz   - Multiplicador para activar/desactivar bordes horizontales.

    OUTPUT:
        gradiente   - Amplitud del gradiente de la imagen.
        orientacion - Ángulos de orientación de los bordes en grados (0-180).
    """
    # Calcular tamaño del filtro y aplicar suavizado Gaussiano nativo de OpenCV
    # Regla del 99.7%: En estadística, la regla del 68-95-99.7 para la campana de Gauss. Apuntes.
    tam_filtro = int(6 * sigma + 1)
    if tam_filtro % 2 == 0:  # Asegurar que el filtro sea impar
        tam_filtro += 1
        
    img_suavizada = cv2.GaussianBlur(img, (tam_filtro, tam_filtro), sigmaX=sigma, sigmaY=sigma, borderType=cv2.BORDER_CONSTANT)
    
    # Aplicar el operador de Sobel
    sobel_x = cv2.Sobel(img_suavizada, cv2.CV_64F, dx=1, dy=0, ksize=3)
    sobel_y = cv2.Sobel(img_suavizada, cv2.CV_64F, dx=0, dy=1, ksize=3)

    # El kernel de Sobel de OpenCV devuelve valores que son el doble del método 
    # matricial manual original. Dividimos entre 2.0 para mantener la equivalencia 
    # matemática exacta para el resto del algoritmo.
    eje_x = (sobel_x / 2.0) * vert
    eje_y = (sobel_y / 2.0) * horz

    # Calcular la magnitud y el ángulo del gradiente
    gradiente, orientacion = cv2.cartToPolar(eje_x, -eje_y, angleInDegrees=True)
    
    # Limitar los ángulos al rango [0, 180)
    orientacion = orientacion % 180

    return gradiente, orientacion


def AjustarGamma(img, gamma):
    """
    DESCRIPCIÓN:
        Ajustar el valor gamma de una imagen para alterar su contraste general.

    INPUT:
        img    - Matriz de la imagen de entrada.
        gamma  - Valor del ajuste gamma matemático.

    OUTPUT:
        imagen_gamma - Imagen resultante tras la corrección de contraste.
    """
    # Normalizar entre 0 y 1, y aplicar cálculo de potencia usando funciones de OpenCV
    img_norm = cv2.normalize(img, None, alpha=0.0, beta=1.0, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_64F)
    img_gamma = cv2.pow(img_norm, 1.0 / gamma)
    
    return img_gamma


def SupresionNoMaximos(img, orientacion, r):
    """
    DESCRIPCIÓN:
        Realizar supresión de no-máximos para afinar los bordes detectados mediante interpolación bilineal.

    INPUT:
        img         - Imagen con los bordes engrosados.
        orientacion - Ángulos de orientación de los bordes.
        r           - Radio de vecindad para interpolar los valores máximos.

    OUTPUT:
        imagen_salida - Imagen procesada con los bordes afinados.
    """
    # Preasignar tamaños
    filas, columnas = img.shape
    img_salida = np.zeros([filas, columnas])
    r_entero = np.ceil(r).astype(int)

    
    # Radianes
    angulo = np.arange(181) * np.pi / 180
    # Pre-calcular desplazamientos de X e Y respecto al centro para cada ángulo posible
    despl_x = r * np.cos(angulo)
    despl_y = r * np.sin(angulo)

    # Extraer la parte fraccional de los desplazamientos para usarla en la interpolación bilineal
    fraccion_h = despl_x - np.floor(despl_x)
    fraccion_v = despl_y - np.floor(despl_y)

    # Truncar los ángulos de orientación para usarlos como índices enteros
    orientacion = np.fix(orientacion)

    # Crear mallas espaciales para las coordenadas dentro del margen
    columna, fila = np.meshgrid(np.arange(r_entero, columnas - r_entero),
                                np.arange(r_entero, filas - r_entero))

    # Extraer el ángulo de orientación específico para cada píxel de la malla
    ori = orientacion[fila, columna].astype(int)

    # PRimer vecino
    # Calcular las coordenadas flotantes (sub-píxel) del vecino en la dirección del gradiente
    x = columna + despl_x[ori]
    y = fila - despl_y[ori]

    # Calcular las coordenadas de los cuatro píxeles enteros más cercanos (suelo y techo)
    fx = np.floor(x).astype(int)
    cx = np.ceil(x).astype(int)
    fy = np.floor(y).astype(int)
    cy = np.ceil(y).astype(int)

    # Extraer las intensidades de esos cuatro píxeles colindantes
    top_l = img[fy, fx]
    top_r = img[fy, cx]
    bot_l = img[cy, fx]
    bot_r = img[cy, cx]

    # Interpolar bilinealmente horizontalmente la fila superior y la inferior
    prom_sup = top_l + fraccion_h[ori] * (top_r - top_l)
    prom_inf = bot_l + fraccion_h[ori] * (bot_r - bot_l)

    # Interpolar verticalmente para obtener el valor exacto del primer vecino sub-píxel (v1)
    v1 = prom_sup + fraccion_v[ori] * (prom_inf - prom_sup)

    mapa_candidato = img[fila, columna] > v1

    # Segundo vecino
    # interpolar calculando las coordenadas flotantes del vecino en la dirección contraria (180 grados)
    x = columna - despl_x[ori]
    y = fila + despl_y[ori]

    # Calcular las coordenadas de los cuatro píxeles enteros más cercanos
    fx = np.floor(x).astype(int)
    cx = np.ceil(x).astype(int)
    fy = np.floor(y).astype(int)
    cy = np.ceil(y).astype(int)

    # Extraer las intensidades de los cuatro píxeles colindantes
    top_l = img[fy, fx]
    top_r = img[fy, cx]
    bot_l = img[cy, fx]
    bot_r = img[cy, cx]

    # Interpolar horizontal y verticalmente para obtener el valor del segundo vecino sub-píxel (v2)
    prom_sup = top_l + fraccion_h[ori] * (top_r - top_l)
    prom_inf = bot_l + fraccion_h[ori] * (bot_r - bot_l)
    v2 = prom_sup + fraccion_v[ori] * (prom_inf - prom_sup)

    # Decisión final
    # Evaluar si el píxel central también es mayor que su segundo vecino
    mapa_activo = img[fila, columna] > v2
    
    # Combinar lógicamente: mantener el píxel SOLO si es un máximo local en ambas direcciones
    mapa_activo = mapa_activo * mapa_candidato
    
    # Aplicar la máscara booleana: los máximos conservan su intensidad, el resto se vuelve cero (negro)
    img_salida[fila, columna] = img[fila, columna] * mapa_activo

    return img_salida


def UmbralHisteresis(img, umbral_sup, umbral_inf):
    """
    DESCRIPCIÓN:
        Aplicar umbralización por histéresis para conectar bordes débiles a bordes fuertes.
        
    INPUT:
        img        - Imagen de entrada con los bordes (tras supresión de no-máximos).
        umbral_sup - Límite superior para considerar un píxel como borde fuerte.
        umbral_inf - Límite inferior para considerar un píxel como candidato a borde.
        
    OUTPUT:
        borde_final - Imagen binaria con los bordes definitivos detectados.
    """
    # Definir los límites de la imagen
    filas, columnas = img.shape
    total_px = filas * columnas
    lim_sup = total_px - filas
    lim_inf = filas + 1

    # Aplanar la matriz a 1D para evitar bucles anidados y agilizar el acceso en memoria
    blanco_negro = img.ravel()

    # Encontrar todos los píxeles que superan el umbral superior
    px_fuertes = np.where(blanco_negro > umbral_sup)[0]
    num_px = px_fuertes.size

    # Inicializar pila para almacenar las coordenadas a revisar
    pila = np.zeros(total_px, dtype=int)
    
    # Cargar todos los bordes seguros iniciales en la base de la pila
    pila[0:num_px] = px_fuertes
    puntero = num_px
    
    # Marcar los bordes fuertes iniciales como analizados (-1)
    for i in range(num_px):
        blanco_negro[px_fuertes[i]] = -1

    # Definir los saltos de índice para alcanzar los 8 vecinos topológicos en un array 1D
    # (Izquierda, Derecha, Diagonales superiores, Arriba, Diagonales inferiores, Abajo)
    vecinos = np.array([-1, 1, -filas - 1, -filas, -filas + 1, filas - 1, filas, filas + 1])

    # Recorrer píxeles conectados rastreando la continuidad del borde hasta vaciar la pila
    while puntero != 0:

        # Extraer el último píxel añadido a la pila
        v = int(pila[puntero - 1])
        puntero -= 1

        # Verificar que el píxel no esté en los extremos absolutos de la imagen para no desbordar la memoria
        if lim_inf < v < lim_sup:
            indices = vecinos + v

            # Evaluar cada uno de los 8 vecinos
            for l in range(8):
                ind = indices[l]
                # Comprobar si el vecino supera el umbral inferior (es un candidato válido conectado a un borde fuerte)
                if blanco_negro[ind] > umbral_inf:
                    # Añadir el nuevo píxel válido a la pila para explorar sus propios vecinos luego
                    puntero += 1
                    pila[puntero - 1] = ind

                    # Marcar el píxel como borde definitivo y procesado (-1)
                    blanco_negro[ind] = -1

    # Reestructurar la salida aislando los bordes aceptados
    borde_final = (blanco_negro == -1)

    # Vuelta a la forma bidimensional
    borde_final = np.reshape(borde_final, [filas, columnas])
    
    return borde_final

def EncontrarLinea(img):
    """
    DESCRIPCIÓN:
        Encontrar la línea recta más prominente en una imagen (ideal para párpados).
        Aplicar detección de bordes y Transformada de Radon.

    INPUT:
        img    - La imagen original de entrada en escala de grises.

    OUTPUT:
        lineas - Matriz con los parámetros de la línea detectada en forma polar.
    """
    # Preprocesar la imagen encontrando bordes y direcciones
    # (El 1 final activa los bordes horizontales y el 0 anula los verticales, ideal para párpados)
    img_bordes, orientacion = FiltroCanny(img, 2, 0, 1)
    
    # Ajustar gamma, suprimir no-máximos y aplicar histéresis
    img_gamma = AjustarGamma(img_bordes, 1.9)
    # Afinar los bordes gruesos a un solo píxel mediante supresión de no-máximos
    img_sup = SupresionNoMaximos(img_gamma, orientacion, 1.5)
    # Conectar y filtrar los bordes definitivos usando umbrales de histéresis
    img_final = UmbralHisteresis(img_sup, 0.2, 0.15)

    # Calcular la Transformada de Radon para encontrar rectas
    theta = np.arange(180)
    m_radon = TransformadaRadon(img_final.astype(np.float32), theta) 
    
    # Definir el eje de distancias continuas respecto al centro del sinograma
    mitad_tam = m_radon.shape[0] // 2
    eje_x = np.arange(-mitad_tam, mitad_tam + 1, 1)

    # Localizar el valor máximo (la recta que contiene la mayor cantidad de píxeles concurrentes)
    valor_max = np.max(m_radon)
    if valor_max > 25:
        ind = np.where(m_radon.ravel() == valor_max)[0]
    else:
        # Si no hay resultados concluyentes
        return np.array([])

    # Aplanar la matriz de Radon para agilizar la ordenación y búsqueda
    v_radon = m_radon.ravel()
    
    # Ordenar de mayor a menor para asegurar que tomamos los picos absolutos
    orden = np.argsort(-v_radon[ind])
    elem = ind.shape[0]

    # Extraer el índice lineal (1D) del pico más fuerte
    k = ind[orden[0:elem]]
    
    # Desenredar el índice unidimensional a coordenadas bidimensionales
    y, x = np.unravel_index(k, m_radon.shape)
    t = -theta[x] * np.pi / 180

    # Obtener la distancia radial exacta (rho) desde el centro
    r = eje_x[y]

    # Convertir a parámetros polares para la línea
    lineas = np.vstack([np.cos(t), np.sin(t), -r]).transpose()

    # Calcular las coordenadas centrales de la imagen original
    centro_x = img.shape[1] / 2 - 1
    centro_y = img.shape[0] / 2 - 1

    # Trasladar el origen matemático de las rectas encontradas al centro real de la foto
    lineas[:, 2] = lineas[:, 2] - lineas[:, 0] * centro_x - lineas[:, 1] * centro_y
    
    return lineas
