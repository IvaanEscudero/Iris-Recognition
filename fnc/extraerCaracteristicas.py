from fnc.normalizar import Normalizar
from fnc.segmentar import Segmentar
from fnc.codificar import Codificar
from fnc.filtrar import ValidarOjo
from cv2 import imread
import constantes

def ExtraerCaracteristicas(nom_img, umbral_pest = constantes.UMBRAL_PESTANA):
	"""
    DESCRIPCIÓN:
        Extraer las características matemáticas únicas de una imagen de iris.

    INPUT:
        nom_img         - Ruta completa o nombre del archivo de la imagen del ojo a procesar.
        umbral_pest		- Valor de umbral (0-255) para el aislamiento de las pestañas. Por defecto, UMBRAL_PESTANA.

    OUTPUT:
        plantilla       - Plantilla biométrica binaria (template) extraída del iris.
        mascara         - Máscara binaria que indica las zonas de ruido (párpados, pestañas, reflejos).
        nom_img         - El mismo nombre de archivo de entrada (útil para el seguimiento en procesos paralelos).
    """
	# Leer la imagen con cv2
	# 0: Imagen RGB. 1:Imagen en escala de grises
	img = imread(nom_img, 0) 
	# Comprobar si la imagen se ha leído correctamente
	if img is None:
		raise ValueError(f"No se pudo leer la imagen en la ruta: {nom_img}")
	
	# Filtro de seguridad semántico utilizando clasificadores en cascada de Haar
	#if not ValidarOjo(img):
	#	print(f"La imagen en la ruta {nom_img} no parece ser un ojo humano.")
	#	raise ValueError(f"La imagen en la ruta {nom_img} no parece ser un ojo humano.")

	# Ejecutar segmentación (detectar pupila e iris y aislar ruido)
	# cir_: [y, x, radio]
	cir_iris, cir_pupila, img_ruido = Segmentar(img, umbral_pest)

	# Ejecutar normalización (desenrollar el anillo circular del iris a un rectángulo polar)
	m_polar, m_ruido = Normalizar(img_ruido, cir_iris[1], cir_iris[0], cir_iris[2],
										 cir_pupila[1], cir_pupila[0], cir_pupila[2],
										 constantes.RES_RADIAL, constantes.RES_ANGULAR)

	# Ejecutar codificación de características (aplicar filtros matemáticos Log-Gabor)
	plantilla, mascara = Codificar(m_polar, m_ruido, constantes.LONG_ONDA_MIN, constantes.SIGMA_ONF)

	return plantilla, mascara, nom_img