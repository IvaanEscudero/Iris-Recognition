# Archivo encargado de gestionar el registro y la inserción de nuevos usuarios en la base de datos TileDB.
from tiledb import object_type, Dim, ArraySchema, Domain, DenseArray, Attr, Config, Ctx, libtiledb
from numpy import int32, int8, expand_dims, repeat
from constantes import RUTA_BD, RES_RADIAL, RES_ANGULAR
from json import dumps, loads
from os import path
from time import sleep

def CrearUsuario(plantilla, mascara, nom, exinfo, ruta_destino=RUTA_BD, res_angular=RES_ANGULAR, res_radial=RES_RADIAL):
    if mascara.shape[1] < plantilla.shape[1]:
        mascara = repeat(mascara, 2, axis=1)

    if not path.exists(ruta_destino) or object_type(ruta_destino) != "array":
    
        config = Config()
        config["vfs.file.enable_filelocks"] = "false" 
        ctx = Ctx(config)
        
        # --- SOLUCIÓN: Orden correcto y expansión a * 2 ---
        dim_usr = Dim(name="usuario", domain=(0, 99999), tile=100, dtype=int32)
        dim_fila = Dim(name="fila", domain=(0, res_radial - 1), tile=res_radial, dtype=int32)
        dim_columna = Dim(name="columna", domain=(0, (res_angular * 2) - 1), tile=(res_angular * 2), dtype=int32)
        
        schema = ArraySchema(
            domain=Domain(dim_usr, dim_fila, dim_columna), 
            attrs=[
                Attr(name="template", dtype=int8), 
                Attr(name="mask", dtype=int8)
            ]
        )
        
        DenseArray.create(ruta_destino, schema, ctx=ctx)
        print("Base de datos creada con éxito.")
        sleep(0.1)

    with DenseArray(ruta_destino, mode='r') as array:
        dominio = array.nonempty_domain()
        
        if dominio is None:
            idx = 0
            lista_ids = []
            lista_exinfo = []
        else:
            idx = dominio[0][1] + 1
            lista_ids = loads(array.meta.get("ids", "[]"))
            lista_exinfo = loads(array.meta.get("exinfos", "[]"))

    plantilla_3d = expand_dims(plantilla, axis=0)
    mascara_3d = expand_dims(mascara, axis=0)

    lista_ids.append(nom)
    lista_exinfo.append(exinfo)

    max_reintentos = 5
    for intento in range(max_reintentos):
        try:
            with DenseArray(ruta_destino, mode='w') as array:
                array[idx:idx+1, :, :] = {"template": plantilla_3d, "mask": mascara_3d}
                
                array.meta["ids"] = dumps(lista_ids)
                array.meta["exinfos"] = dumps(lista_exinfo)
            break
            
        except libtiledb.TileDBError as error_tiledb:
            if intento < max_reintentos - 1:
                sleep(0.1) 
            else:
                raise Exception(f"Fallo crítico tras {max_reintentos} intentos. Windows bloquea el archivo: {error_tiledb}")

def Main():
    print("\nRegistrando usuarios...")
    for i in range(3):
        p_falsa = random.randint(0, 2, (RES_RADIAL, RES_ANGULAR * 2), dtype=int8)
        m_falsa = random.randint(0, 2, (RES_RADIAL, RES_ANGULAR), dtype=int8)
        CrearUsuario(p_falsa, m_falsa, i, i)
    print("Usuarios registrados.")

if __name__ == "__main__":
    from numpy import random
    Main()