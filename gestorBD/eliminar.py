# Archivo encargado de vaciar el contenido de la base de datos TileDB manteniendo la carpeta raíz.
from os import path, scandir, remove
from argparse import ArgumentParser
from constantes import RUTA_BD
from shutil import rmtree
from json import loads, dumps
from tiledb import object_type,Config,Ctx,DenseArray, Dim, ArraySchema, Domain, Attr
from numpy import int8, int32

def EliminarBD(ruta=RUTA_BD):
    """
    Descripción:
        Borra todos los archivos y subdirectorios dentro de la ruta de la 
        base de datos, pero mantiene la carpeta raíz existente.
        
    Input:
        ruta (str) - Ruta del directorio de la base de datos TileDB.
        
    Output:
        resultado (bool) - Verdadero si se vacía correctamente, Falso si la ruta no existe.
    """
    # Comprobar si existir la ruta física
    if not path.exists(ruta):
        return False

    try:
        # Recorrer cada elemento dentro de la carpeta raíz
        for elemento in scandir(ruta):
            # Borrar archivos de forma individual
            if elemento.is_file():
                remove(elemento.path)
            # Borrar subdirectorios y su contenido de forma recursiva
            elif elemento.is_dir():
                rmtree(elemento.path)
        
        return True
        
    except Exception as e:
        # Capturar errores de acceso o permisos al intentar manipular el contenido
        print(f"Error al vaciar la base de datos: {e}")
        return False

def EliminarUsuarioBD(id_usuario, ruta=RUTA_BD):
    """
    Descripción:
        Elimina todas las plantillas biométricas asociadas a un ID de usuario.
        Reconstruye la matriz densa de TileDB para evitar dejar espacios vacíos (basura).
        
    Input:
        id_usuario (str): El identificador único a borrar (ej. '001_L').
        ruta_bd (str): La ruta donde está guardada la base de datos.
        
    Output:
        int/bool: Devuelve el número de plantillas eliminadas, 0 si no lo encuentra, 
                  o False si la base de datos no existe.
    """
    # 1. Comprobar si la base de datos existe realmente
    if not path.exists(ruta) or object_type(ruta) != "array":
        return False

    # Configurar el contexto anti-bloqueos para Windows
    config = Config()
    config["vfs.file.enable_filelocks"] = "false"
    ctx = Ctx(config)

    # 2. Leer absolutamente todos los datos a la memoria RAM
    with DenseArray(ruta, mode='r', ctx=ctx) as array:
        dominio = array.nonempty_domain()
        
        # Si la BD ya está vacía, no hay nada que borrar
        if dominio is None:
            return 0 
            
        idx_max = dominio[0][1] + 1
        
        datos_bd = array[0:idx_max, :, :]
        plantillas = datos_bd['template']
        mascaras = datos_bd['mask']
        
        lista_ids = loads(array.meta.get("ids", "[]"))
        lista_exinfos = loads(array.meta.get("exinfos", "[]"))

    # 3. Comprobar si el usuario realmente está en el sistema
    if id_usuario not in lista_ids:
        return 0 # El usuario no existe

    # 4. Magia de filtrado: Obtener índices de TODOS EXCEPTO el usuario a borrar
    indices_conservar = [i for i, uid in enumerate(lista_ids) if uid != id_usuario]
    plantillas_borradas = len(lista_ids) - len(indices_conservar)
    
    # 5. Borrar sin piedad la base de datos antigua (carpeta física)
    try:
        rmtree(ruta)
    except Exception as e:
        raise Exception(f"No se pudo eliminar la BD antigua por bloqueos del Sistema Operativo: {e}")

    # 6. Si aún quedan usuarios vivos, reconstruir la base de datos limpia
    if len(indices_conservar) > 0:
        
        # Filtrar las matrices usando indexación avanzada de NumPy (Rapidísimo)
        nuevas_plantillas = plantillas[indices_conservar]
        nuevas_mascaras = mascaras[indices_conservar]
        nuevos_ids = [lista_ids[i] for i in indices_conservar]
        nuevos_exinfos = [lista_exinfos[i] for i in indices_conservar]
        
        # Recrear el esquema exacto que tenías en crear_usuario.py
        dim_usr = Dim(name="usuario", domain=(0, 99999), tile=100, dtype=int32)
        dim_fila = Dim(name="fila", domain=(0, 19), tile=20, dtype=int32)
        dim_columna = Dim(name="columna", domain=(0, 479), tile=480, dtype=int32)
        
        schema = ArraySchema(
            domain=Domain(dim_usr, dim_fila, dim_columna), 
            attrs=[
                Attr(name="template", dtype=int8), 
                Attr(name="mask", dtype=int8)
            ]
        )
        DenseArray.create(ruta, schema, ctx=ctx)

        # Volcar los datos limpios al disco duro
        with DenseArray(ruta, mode='w', ctx=ctx) as w_array:
            w_array[0:len(nuevos_ids), :, :] = {
                "template": nuevas_plantillas,
                "mask": nuevas_mascaras
            }
            w_array.meta["ids"] = dumps(nuevos_ids)
            w_array.meta["exinfos"] = dumps(nuevos_exinfos)
            
    # Devolvemos cuántas plantillas se han eliminado (por si ese usuario tenía varias fotos)
    return plantillas_borradas

def main(ruta=RUTA_BD):
    print(f"Vaciando contenido de la base de datos en {ruta}...")

    if EliminarBD(ruta):
        print("BBDD vaciada")
    else:
        print("No se pudo vaciar la base de datos o la ruta no existe.")

# Iniciar bloque de ejecución principal por consola
if __name__ == '__main__':
    parser = ArgumentParser(description="Vaciar contenido de una base de datos TileDB.")
    parser.add_argument("ruta", type=str, help="Ruta de la carpeta a vaciar.", nargs='?', default=RUTA_BD)
    args = parser.parse_args()
    main(args.ruta)