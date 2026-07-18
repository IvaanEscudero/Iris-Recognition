# Archivo encargado de probar la autenticación de un iris contra la base de datos TileDB
from fnc.extraerCaracteristicas import ExtraerCaracteristicas
from constantes import RUTA_BD, UMBRAL_DIST_HM
from fnc.emparejar import Emparejar
from argparse import ArgumentParser
from tiledb import object_type
from os import path

def Autenticar(ruta_imagen):
    """
    Descripción:
        Comprueba si una imagen de iris tiene coincidencias en la BBDD TileDB.
    """
    # 1. Extraer la plantilla biométrica de la foto de prueba
    plantilla, mascara, _ = ExtraerCaracteristicas(ruta_imagen)
    
    # 2. Buscar posibles candidatos en TileDB (Devuelve una lista de IDs)
    resultados = Emparejar(plantilla, mascara, RUTA_BD, UMBRAL_DIST_HM)

    # Si la matriz vuelve vacía (0) o es una lista vacía, denegar
    if resultados == 0 or not resultados:
        return 0 # No hay coincidencias o BD vacía
    
    # 3. Coger el mejor candidato (el primero de la lista)
    #identidad_coincidente = resultados[0]
    
    # 4. Usar la función auxiliar de TileDB para recuperar la distancia de Hamming exacta
    #_, distancia = CargarHamming(identidad_coincidente, plantilla, mascara, RUTA_BD)

    #return identidad_coincidente, distancia
    return resultados[0]

def main(imagen_prueba):

    print(f"--- INTENTO DE ACCESO CON: {imagen_prueba} ---")

    # Validar primero si TileDB existe (para dar un error más limpio al usuario)
    if not path.exists(RUTA_BD) or object_type(RUTA_BD) != "array":
        print(">>> ERROR CRÍTICO: La base de datos TileDB no existe o está vacía. Ejecuta el registro primero.")
        return

    try:
        resultado = Autenticar(imagen_prueba)

        if resultado == 0:
            print(">>> ACCESO DENEGADO")
            print("No hay coincidencias en el sistema o el umbral no se superó.")            
        else:    
            identidad, distancia = resultado
            
            print(f">>> ACCESO CONCEDIDO")
            print(f"Identidad Reconocida (ID TileDB): {identidad}")
            print(f"Distancia de Hamming: {distancia:.4f}")

    except ValueError as ve:
        print(f">>> ACCESO DENEGADO\n{ve}")
    except Exception as e:
        print(f"Ocurrió un error crítico durante la ejecución: {e}")

if __name__ == "__main__":
    parser = ArgumentParser(description="Prueba de autenticación de iris por terminal interactuando con TileDB.")
    parser.add_argument("imagen", type=str, help="Ruta de la imagen a autenticar (ej: S1001L01.jpg)")
    args = parser.parse_args()
    
    main(args.imagen)