# Nota: Ojo con las mayúsculas
# Parámetros de rutas
RUTA_BD = 'BD_Iris/'                 # Ruta de la base de datos
RUTA_INPUT = 'CASIA-Iris-Interval/'  # Ruta de las imagenes de los iris

# Parámetros para filtrar ojos
ESCALA = 1.02 #1.05
MIN_VECINOS = 2 #2
MIN_DIMENSION = 30 #40

# Parámetros para segmentación
UMBRAL_PESTANA = 80

# Parámetros para normalización
RES_RADIAL = 20     # RESolución
RES_ANGULAR = 240   # RESolución

# Parámetros de codificación de características (Filtros de Gabor)
LONG_ONDA_MIN = 18
SIGMA_ONF = 0.5

# Parámetros de emparejamiento
"""
 Umbral distancia de Hamming. 
 Seleccionar un valor entre 0.0 y 1.0
    0.0: Es la misma imagen
    A partir de 0.45 la probabilidad de dos 
    IrisCode se asemejen se eleva mucho.
    Se recomiendo un umbral máximo de 0.37
"""
UMBRAL_DIST_HM = 0.31 #0.37