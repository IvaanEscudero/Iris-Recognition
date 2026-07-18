# Delimitar matemáticamente las fronteras del iris, utilizando el operador íntegro-diferencial de Daugman.
from scipy.signal import fftconvolve
import numpy as np
import cv2

def BuscarLimiteInterior(imagen):    
    """
    DESCRIPCIÓN:
        Busca el límite interior del iris (la frontera entre la pupila y el iris).
        Aplica un operador íntegro-diferencial en dos fases (gruesa y fina) 
        para encontrar el centro exacto y el radio de la pupila.
        
    INPUT:
        imagen - La imagen original del ojo en formato de matriz 2D (escala de grises).
        
    OUTPUT:
        y_int - Coordenada Y del centro geométrico de la pupila.
        x_int - Coordenada X del centro geométrico de la pupila.
        r_int - Radio de la pupila en píxeles.
    """
    img_trabajo = imagen.copy()

    # Umbralización para detectar brillos (reflejos de flash) fuertes en la pupila
    _, mascara = cv2.threshold(img_trabajo, 180, 255, cv2.THRESH_BINARY)

    # Si hay brillos, aplicar funciones morfológicas e inpainting para rellenarlos
    if cv2.countNonZero(mascara) > 10: 
        nucleo = np.ones((3,3), np.uint8)
        mascara = cv2.dilate(mascara, nucleo, iterations=1)
        img_trabajo = cv2.inpaint(img_trabajo, mascara, 3, cv2.INPAINT_TELEA)

    # ---- Búsqueda gruesa (precisión a nivel de "saltos" para ahorrar tiempo) ----
    alto = img_trabajo.shape[0]
    ancho = img_trabajo.shape[1]
    sector = ancho / 4      # Ancho del margen externo donde se excluye la búsqueda
    radio_min = 10
    radio_max = sector * 0.8
    salto = 4               # Precisión de la búsqueda gruesa, en píxeles

    # Calcular dimensiones del espacio de Hough 3D (y, x, radio)
    tam = np.array([np.floor((alto - 2 * sector) / salto),
                    np.floor((ancho - 2 * sector) / salto),
                    np.floor((radio_max - radio_min) / salto)]).astype(int)

    # Resolución angular de la integración circular
    precision_integracion = 1
    angulos = np.arange(0, 2 * np.pi, precision_integracion)
    
    # Crear mallas tridimensionales de coordenadas
    x, y, r = np.meshgrid(np.arange(tam[1]),
                          np.arange(tam[0]),
                          np.arange(tam[2]))
                          
    y = sector + y * salto
    x = sector + x * salto
    r = radio_min + r * salto
    
    # Integrar los valores de los píxeles en circunferencias
    espacio_hough = IntegralContornoCircular(img_trabajo, y, x, r, angulos)

    # Derivada parcial del Espacio de Hough respecto al radio (R)
    # Matemáticamente es equivalente a aplicar un operador diferencial de bordes
    derivada_radio = espacio_hough - espacio_hough[:, :, np.insert(np.arange(espacio_hough.shape[2]-1), 0, 0)]

    # Blur en 3D
    tam_filtro = 3       
    # Scipy porque ni cv2 ni numpy posee funciones nativas en espacios 3D
    derivada_suavizada = fftconvolve(derivada_radio, np.ones([tam_filtro, tam_filtro, tam_filtro]), mode="same")

    # Encontrar la coordenada 3D que ha dado el máximo valor de gradiente
    indice_maximo = np.argmax(derivada_suavizada.ravel())
    y_max, x_max, r_max = np.unravel_index(indice_maximo, derivada_suavizada.shape)

    y_int = sector + y_max * salto
    x_int = sector + x_max * salto
    r_int = radio_min + (r_max - 1) * salto

    # ---- Búsqueda fina (precisión sub-píxel alrededor del punto encontrado) ----
    precision_integracion = 0.1     
    angulos = np.arange(0, 2 * np.pi, precision_integracion)
    
    x, y, r = np.meshgrid(np.arange(salto * 2),
                          np.arange(salto * 2),
                          np.arange(salto * 2))
                          
    y = y_int - salto + y
    x = x_int - salto + x
    r = r_int - salto + r
    
    espacio_hough = IntegralContornoCircular(img_trabajo, y, x, r, angulos)

    # Volver a derivar y suavizar
    derivada_radio = espacio_hough - espacio_hough[:, :, np.insert(np.arange(espacio_hough.shape[2]-1), 0, 0)]
    derivada_suavizada = fftconvolve(derivada_radio, np.ones([tam_filtro, tam_filtro, tam_filtro]), mode="same")
    
    indice_maximo = np.argmax(derivada_suavizada.ravel())
    y_max, x_max, r_max = np.unravel_index(indice_maximo, derivada_suavizada.shape)

    # Ajuste final de coordenadas
    y_int = y_int - salto + y_max
    x_int = x_int - salto + x_max
    r_int = r_int - salto + r_max - 1

    return y_int, x_int, r_int



def BuscarLimiteExterior(imagen, y_int, x_int, r_int):
    """
    DESCRIPCIÓN:
        Busca el límite exterior del iris (frontera entre el iris y la esclerótica).
        Utiliza el centro de la pupila como punto de anclaje inicial y restringe
        la búsqueda a zonas donde no interfieren los párpados.

    INPUT:
        imagen  - La imagen original del ojo en escala de grises.
        y_int   - Coordenada Y del centro de la pupila calculada previamente.
        x_int   - Coordenada X del centro de la pupila calculada previamente.
        r_int   - Radio de la pupila calculado previamente.

    OUTPUT:
        y_ext   - Coordenada Y del centro del círculo del iris.
        x_ext   - Coordenada X del centro del círculo del iris.
        r_ext   - Radio exterior del iris en píxeles.
    """
    # Desplazamiento máximo permitido del centro del iris respecto al de la pupila (15% según Daugman 2004)
    despl_max = np.round(r_int * 0.15).astype(int)

    # Rango estimado del radio del iris basado en la proporción biológica (Daugman 2004)
    r_min = np.round(r_int / 0.8).astype(int)
    r_max = np.round(r_int / 0.3).astype(int)

    # Regiones angulares válidas para la integración (evita el párpado superior e inferior)
    region_integracion = np.array([[2/6, 4/6], [8/6, 10/6]]) * np.pi

    # Resolución de la integración circular
    precision_integracion = 0.05
    
    # Unir los dos arcos angulares de los laterales del ojo
    angulos = np.concatenate([np.arange(region_integracion[0,0], region_integracion[0,1], precision_integracion),
                              np.arange(region_integracion[1,0], region_integracion[1,1], precision_integracion)],
                              axis=0)
                              
    x, y, r = np.meshgrid(np.arange(2 * despl_max),
                          np.arange(2 * despl_max),
                          np.arange(r_max - r_min))
                          
    y = y_int - despl_max + y
    x = x_int - despl_max + x
    r = r_min + r
    
    espacio_hough = IntegralContornoCircular(imagen, y, x, r, angulos)

    # Derivada parcial del Espacio de Hough respecto a R
    derivada_radio = espacio_hough - espacio_hough[:, :, np.insert(np.arange(espacio_hough.shape[2]-1), 0, 0)]

    # Difuminado 3D (Mayor máscara porque el borde exterior del iris es menos nítido)
    tam_filtro = 7  
    derivada_suavizada = fftconvolve(derivada_radio, np.ones([tam_filtro, tam_filtro, tam_filtro]), mode="same")

    indice_maximo = np.argmax(derivada_suavizada.ravel())
    y_indice, x_indice, r_indice = np.unravel_index(indice_maximo, derivada_suavizada.shape)

    y_ext = y_int - despl_max + y_indice + 1
    x_ext = x_int - despl_max + x_indice + 1
    r_ext = r_min + r_indice - 1

    return y_ext, x_ext, r_ext



def IntegralContornoCircular(imagen, y_cen, x_cen, r, angulos):
    """
    DESCRIPCIÓN:
        Realiza una integral de contorno a lo largo de una circunferencia.
        Utiliza una aproximación discreta de suma de Riemann para sumar 
        las intensidades de los píxeles a lo largo del perímetro circular.

    INPUT:
        imagen   - La imagen del ojo sobre la que se calculará la integral.
        y_centro - Matriz de coordenadas Y del centro del círculo a evaluar.
        x_centro - Matriz de coordenadas X del centro del círculo a evaluar.
        r        - Matriz con los radios del círculo a evaluar.
        angulos  - Lista de ángulos de la circunferencia a sumar (en radianes, de 0 a 2pi).

    OUTPUT:
        suma_intensidades - El resultado matemático de la integral de contorno.
    """
    # Pre-reservar memoria para las coordenadas perimetrales
    y = np.zeros([len(angulos), r.shape[0], r.shape[1], r.shape[2]], dtype=int)
    x = np.zeros([len(angulos), r.shape[0], r.shape[1], r.shape[2]], dtype=int)
    
    # Calcular los puntos del perímetro usando senos y cosenos
    for i in range(len(angulos)):
        ang = angulos[i]
        y[i, :, :, :] = np.round(y_cen - np.cos(ang) * r).astype(int)
        x[i, :, :, :] = np.round(x_cen + np.sin(ang) * r).astype(int)

    # Adaptar Y para no salir de los bordes verticales de la imagen
    ind = np.where(y < 0)
    y[ind] = 0
    ind = np.where(y >= imagen.shape[0])
    y[ind] = imagen.shape[0] - 1

    # Adaptar X para no salir de los bordes horizontales de la imagen
    ind = np.where(x < 0)
    x[ind] = 0
    ind = np.where(x >= imagen.shape[1])
    x[ind] = imagen.shape[1] - 1

    # Mapear los píxeles perimetrales y sumar verticalmente (colapsar el eje de los ángulos)
    intensidades = imagen[y, x]
    suma_intensidades = np.sum(intensidades, axis=0)
    
    return suma_intensidades.astype(float)