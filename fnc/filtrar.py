from cv2 import CascadeClassifier, data
from constantes import ESCALA, MIN_VECINOS, MIN_DIMENSION

def ValidarOjo(img):
    """
    DESCRIPCIÓN:
        Filtro de seguridad semántico utilizando clasificadores en cascada de Haar.
        Comprueba si la imagen de entrada contiene geometría compatible con un ojo humano.
        
    INPUT:
        ruta_imagen - Ruta local del archivo de imagen a analizar.
        
    OUTPUT:
        Booleano - True si detecta al menos un ojo, False si es una imagen no válida.
    """        
    # Cargar el modelo pre-entrenado de OpenCV
    detector_ojos = CascadeClassifier(data.haarcascades + 'haarcascade_eye.xml')
    
    ojos_detectados = detector_ojos.detectMultiScale(
        img, 
        scaleFactor=ESCALA, 
        minNeighbors=MIN_VECINOS, 
        minSize=(MIN_DIMENSION, MIN_DIMENSION)
    )
    
    # Si la lista tiene elementos, es un ojo real
    return len(ojos_detectados) > 0
def main(ruta_imagen):
    print(f"\n--- PRUEBA DE DETECCIÓN CON: {ruta_imagen} ---\n")
    try:
        imagen = imread(ruta_imagen, 0)

        if ValidarOjo(imagen):
            print(f"Ojo detectado: {ruta_imagen}")
        else:
            print(f"La imagen {ruta_imagen} no parece ser un ojo humano.")

        imshow("Resultado:", imagen)
        waitKey(0)
        destroyWindow("Resultado:")
        

    except RuntimeError as re:
        print(f">>> ERROR DE PROCESAMIENTO:\n{re}")
    except Exception as e:
        print(f">>> ERROR CRÍTICO INESPERADO:\n{e}")  
    
if __name__ == "__main__":
    from argparse import ArgumentParser
    from cv2 import imread,imshow, destroyWindow, waitKey
    parser = ArgumentParser(description="Prueba de autenticación de iris por terminal.")
    parser.add_argument("imagen", type=str, help="Ruta de la imagen a autenticar (ej: foto.jpg)")
    args = parser.parse_args()
    
    main(args.imagen)