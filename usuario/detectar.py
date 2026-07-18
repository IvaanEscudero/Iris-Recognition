# Prueba de detección de iris, muestra la imagen original con las regiones de iris y pupila detectadas
from argparse import ArgumentParser
from fnc.segmentar import Segmentar
from fnc.filtrar import ValidarOjo
import cv2

def Detectar(ruta_imagen):
    img = cv2.imread(ruta_imagen, cv2.IMREAD_GRAYSCALE)

    if img is None:
        return -1 # Imagen no encontrada o formato inválido
    
    if not ValidarOjo(img):
        return -2 # La imagen no parece ser un ojo humano
    
    try:
        ciriris, cirpupil, _ = Segmentar(img)
    except Exception as e:
        raise RuntimeError(f"Fallo en la segmentación:{e}")
    
    y_iris, x_iris, r_iris = ciriris
    y_pupil, x_pupil, r_pupil = cirpupil

    img_color = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    # Dibujar límite del Iris (AZUL)
    cv2.circle(img_color, (x_iris, y_iris), r_iris, (255, 0, 0), 1)
    cv2.circle(img_color, (x_iris, y_iris), 2, (255, 0, 0), 1) # Centro

    # Dibujar límite de la Pupila (VERDE)
    cv2.circle(img_color, (x_pupil, y_pupil), r_pupil, (0, 255, 0), 1)
    cv2.circle(img_color, (x_pupil, y_pupil), 2, (0, 255, 0), 1) # Centro


    return img_color, ciriris, cirpupil

def main(imagen_prueba):

    print(f"\n--- PRUEBA DE DETECCIÓN CON: {imagen_prueba} ---\n")
    
    try:
        resultado = Detectar(imagen_prueba)

        if resultado == -1:
            print(f">>> ERROR: No se pudo cargar la imagen '{imagen_prueba}'. Verifica la ruta.")
            return
        
        img_color, ciriris, cirpupil = Detectar(imagen_prueba)

        y_iris, x_iris, r_iris = ciriris
        y_pupil, x_pupil, r_pupil = cirpupil

        print(f"Iris detectado: Centro({x_iris}, {y_iris}), Radio: {r_iris}")
        print(f"Pupila detectada: Centro({x_pupil}, {y_pupil}), Radio: {r_pupil}")

        cv2.imshow(f"Resultado: {imagen_prueba}", img_color)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

        cv2.imwrite('resultado_prueba.jpg', img_color)

    except RuntimeError as re:
        print(f">>> ERROR DE PROCESAMIENTO:\n{re}")
    except Exception as e:
        print(f">>> ERROR CRÍTICO INESPERADO:\n{e}")    

if __name__ == "__main__":
    parser = ArgumentParser(description="Prueba de autenticación de iris por terminal.")
    parser.add_argument("imagen", type=str, help="Ruta de la imagen a autenticar (ej: foto.jpg)")
    args = parser.parse_args()
    
    main(args.imagen)