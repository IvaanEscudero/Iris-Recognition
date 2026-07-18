"""
Script para registrar una única imagen de iris en la base de datos de forma segura.
"""
from os import path, makedirs
from argparse import ArgumentParser
from fnc.extraerCaracteristicas import ExtraerCaracteristicas
from gestorBD.crearUsuario import CrearUsuario
from constantes import RUTA_BD

def Registrar(ruta_imagen, nombre_usuario):

    if not path.exists(ruta_imagen):
        return -1 # Archivo no encontrado

    extensiones_validas = ('.jpg', '.jpeg', '.png', '.bmp')
    if not ruta_imagen.lower().endswith(extensiones_validas):
        return -2 # Archivo no valido

    if not path.exists(RUTA_BD):
        makedirs(RUTA_BD) # Si no existe la ruta, crearla

    plantilla, mascara, _ = ExtraerCaracteristicas(ruta_imagen)
    
    nombre_archivo_original = path.basename(ruta_imagen)
    
    CrearUsuario(plantilla, mascara, nombre_usuario, exinfo=nombre_archivo_original)
    
    return nombre_archivo_original


def main(ruta_imagen, nombre_usuario):


    print(f"\n--- REGISTRO INDIVIDUAL DE USUARIO ---")
    print(f"Identidad a registrar: {nombre_usuario}")
    print(f"Archivo de origen: {ruta_imagen}")

    try:
        resultado = Registrar(ruta_imagen, nombre_usuario)

        if resultado == -1:
            print(f"ERROR: No se encontró el archivo '{ruta_imagen}'.")
            return
        
        if resultado == -2:
            print(f"ERROR: El archivo debe ser una imagen válida (.jpg, .png, .bmp).")
            return

        print(f"\n ¡Usuario '{nombre_usuario}' registrado correctamente!")
        print(f"   -> Archivo base procesado: {resultado}")
        print(f"   -> Guardado en directorio: {RUTA_BD}")
        print(f"\n IMPORTANTE: El usuario se ha guardado como un archivo individual (.npz).")
        print(f"   Si tienes una base de datos unificada, recuerda ejecutar 'compilar.py' ")
        print(f"   para que este nuevo usuario se integre en el bloque principal.\n")
        
    except ValueError as ve:
        print(f"\n ERROR DE SEGMENTACIÓN:{ve}")
    except Exception as e:
        print(f"\nERROR CRÍTICO AL REGISTRAR: {e}")

if __name__ == "__main__":
    parser = ArgumentParser(description="Registrar un único usuario en la base de datos biométrica.")
    parser.add_argument('imagen', type=str, help="Ruta de la imagen del ojo a registrar (.jpg, .png).")
    parser.add_argument('id_usuario', type=str, help="Identificador único del usuario y ojo (ej: '001_L').")
    args = parser.parse_args()

    main(args.imagen, args.id_usuario)