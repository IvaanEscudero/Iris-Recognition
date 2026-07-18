# Archivo encargado de procesar y registrar masivamente imágenes de iris en paralelo dentro de la base de datos TileDB (Estructura CASIA-Twins).

from tiledb import object_type, Dim, ArraySchema, Domain, DenseArray, Attr, Config, Ctx, TileDBError
from fnc.extraerCaracteristicas import ExtraerCaracteristicas
from constantes import RUTA_BD, RUTA_INPUT, RES_ANGULAR, RES_RADIAL
from os import scandir, path, makedirs
from numpy import int8, int32, array, repeat
from argparse import ArgumentParser
from multiprocessing import Pool
from json import dumps, loads
from time import perf_counter
from tempfile import mkdtemp
from shutil import rmtree

def MostrarEncabezado(hilos, ruta_destino=RUTA_BD, ruta_origen=RUTA_INPUT):
    print(f"--- INICIANDO REGISTRO MASIVO BBDD CASIA-TWINS (PARALELO) ---")
    print(f"Directorio origen: {ruta_origen}")
    print(f"Directorio destino: {ruta_destino}")
    print(f"Hilos a utilizar: {hilos}\n")

def MostrarResumen(exitos, errores):
    print("\n" + "-" * 40)
    print("--- REGISTRO MASIVO COMPLETADO ---")
    print(f"Éxitos: {exitos}")
    print(f"Fallos: {errores}")
    print("-" * 40)

def ProcesarImagenWorker(args):
    ruta_imagen, nombre_usuario, archivo = args
    try:
        template, mask, _ = ExtraerCaracteristicas(ruta_imagen)
        
        # Igualar dimensiones geométricas (la máscara se duplica para coincidir con la fase)
        if mask.shape[1] < template.shape[1]:
            mask = repeat(mask, 2, axis=1)

        return (True, ruta_imagen, template, mask, nombre_usuario, archivo, "")
        
    except Exception as e:
        return (False, ruta_imagen, None, None, nombre_usuario, archivo, str(e))

def PrepararBaseDeDatosTileDB(ruta_destino=RUTA_BD, res_angular=RES_ANGULAR, res_radial=RES_RADIAL):
    if not path.exists(ruta_destino) or object_type(ruta_destino) != "array":
        config = Config()
        config["vfs.file.enable_filelocks"] = "false" 
        ctx = Ctx(config)
        
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

def RealizarRegistroParalelo(hilos, ruta_origen=RUTA_INPUT, ruta_destino=RUTA_BD, callback=None):
    from time import sleep 
    
    registrados_exito = 0 
    errores = 0 
    tareas = [] 
    
    if not path.exists(ruta_origen):
        print(f"ERROR: No se encuentra la carpeta {ruta_origen}")
        return registrados_exito, errores
 
    if not path.exists(ruta_destino):
        makedirs(ruta_destino)

    # --- CAMBIO DE LÓGICA DE NAVEGACIÓN (CASIA-Twins) ---
    # 1. Buscar las carpetas de los pares de gemelos (ej. /01, /02...)
    carpetas_pares = [d.name for d in scandir(ruta_origen) if d.is_dir()]

    for par in sorted(carpetas_pares):
        ruta_par = path.join(ruta_origen, par)
        
        # 2. Iterar sobre las 4 posibles variantes biológicas (Gemelo 1 o 2, Ojo Izquierdo o Derecho)
        for ojo_gemelo in ('1L', '1R', '2L', '2R'):
            ruta_ojo = path.join(ruta_par, ojo_gemelo)
            
            if not path.exists(ruta_ojo) or not path.isdir(ruta_ojo):
                continue
                
            # El ID en la base de datos será Par_GemeloOjo (ej. "01_1L")
            nombre_usuario = f"{par}_{ojo_gemelo}"
            
            # 3. Extraer las imágenes (ej. S3011L01.jpg)
            for archivo in scandir(ruta_ojo):
                if archivo.is_file() and archivo.name.lower().endswith(('.jpg','.png', '.bmp', '.jpeg')):
                    tareas.append((archivo.path, nombre_usuario, archivo.name))
    # -----------------------------------------------

    total_imagenes = len(tareas)
    if total_imagenes == 0:
        print("No se encontraron imágenes válidas para procesar en la estructura de Twins.")
        return registrados_exito, errores

    print(f"Se han encontrado {total_imagenes} imágenes. Iniciando extracción en paralelo...\n")

    PrepararBaseDeDatosTileDB(ruta_destino)

    batch_size = 200
    batch_templates = []
    batch_masks = []
    batch_ids = []
    batch_exinfos = []

    read_config = Config()
    read_config["vfs.file.enable_filelocks"] = "false"
    read_ctx = Ctx(read_config)

    with DenseArray(ruta_destino, mode='r', ctx=read_ctx) as r_array:
        dom = r_array.nonempty_domain()
        start_idx = (dom[0][1] + 1) if dom is not None else 0
        
        meta_ids_str = r_array.meta.get("ids", "[]")
        meta_exinfos_str = r_array.meta.get("exinfos", "[]")
        global_ids = loads(meta_ids_str)
        global_exinfos = loads(meta_exinfos_str)

    def EscribirLoteTileDB():
            nonlocal start_idx, batch_templates, batch_masks, batch_ids, batch_exinfos, global_ids, global_exinfos
            if not batch_templates: return False

            write_config = Config()
            write_config["vfs.file.enable_filelocks"] = "false"
            write_ctx = Ctx(write_config)
            
            exito_escritura = False
            error_critico = None

            try:
                for intento in range(5): 
                    try:
                        with DenseArray(ruta_destino, mode='w', ctx=write_ctx) as w_array:
                            end_idx = start_idx + len(batch_templates) - 1
                            w_array[start_idx:end_idx + 1, :, :] = {
                                "template": array(batch_templates, dtype=int8),
                                "mask": array(batch_masks, dtype=int8)
                            }
                            
                            temp_ids = global_ids + batch_ids
                            temp_exinfos = global_exinfos + batch_exinfos
                            
                            w_array.meta["ids"] = dumps(temp_ids)
                            w_array.meta["exinfos"] = dumps(temp_exinfos)
                            
                            global_ids = temp_ids
                            global_exinfos = temp_exinfos
                            exito_escritura = True
                        
                        break
                        
                    except TileDBError as error_tiledb:
                        error_critico = error_tiledb
                        if intento < 4:
                            sleep(1.0) 
            
            finally:
                batch_templates.clear()
                batch_masks.clear()
                batch_ids.clear()
                batch_exinfos.clear()
                
            if exito_escritura:
                start_idx = end_idx + 1
                return True
            else:
                raise Exception(f"Windows bloqueó el archivo tras 5 reintentos. Detalle: {error_critico}")

    pool = Pool(processes=hilos)
    try:
        for resultado in pool.imap_unordered(ProcesarImagenWorker, tareas):
            exito, ruta_img, plantilla, mascara, usr, arch, error_msj = resultado
            
            if exito:
                batch_templates.append(plantilla)
                batch_masks.append(mascara)
                batch_ids.append(usr)
                batch_exinfos.append(arch)
                
                if len(batch_templates) >= batch_size:
                    lote_actual = len(batch_templates) 
                    try:
                        EscribirLoteTileDB()
                        registrados_exito += lote_actual
                        msg = f"Imagen {registrados_exito} de {total_imagenes} procesadas."
                        if callback: callback(msg)
                    except Exception as e:
                        print(f"[ERROR CRÍTICO AL ESCRIBIR LOTE]: {e}")
                        errores += lote_actual 
            else:
                errores += 1
                print(f"[ERROR DE EXTRACCIÓN] {ruta_img} -> {error_msj}")

        pool.close()
        pool.join()

    except Exception as error_pool:
        pool.terminate()
        pool.join()
        print(f"[ERROR EN EL MULTIPROCESAMIENTO]: {error_pool}")
        return registrados_exito, errores

    if len(batch_templates) > 0:
        lote_final = len(batch_templates)
        try:
            EscribirLoteTileDB()
            registrados_exito += lote_final
            msg = f"Imagen {registrados_exito} de {total_imagenes} procesadas."
            if callback: callback(msg)
        except Exception as e:
            print(f"[ERROR AL ESCRIBIR LOTE FINAL]: {e}")
            errores += lote_final
    else:
        print("No hay imágenes residuales pendientes.")

    return registrados_exito, errores

def MedirTiempo(funcion_objetivo, *args, **kwargs):
    inicio = perf_counter()
    resultados = funcion_objetivo(*args, **kwargs)
    fin = perf_counter()
    
    tiempo_total = fin - inicio
    
    print("\n" + "=" * 40)
    print(f" TIEMPO DE EJECUCIÓN BBDD:")
    print(f" {tiempo_total:.3f} segundos.")
    print("=" * 40)
    
    return resultados

def main(modo_debug):
    hilos_disponibles = 4 

    if modo_debug:
        print("\n[!] MODO DEBUG ACTIVADO")
        carpeta_temporal = mkdtemp(prefix="debug_twins_")
        print(f"[!] Archivos se guardarán temporalmente en: {carpeta_temporal}\n")
        
        MostrarEncabezado(hilos_disponibles, carpeta_temporal, RUTA_INPUT)
        
        try:
            exitos, errores = MedirTiempo(RealizarRegistroParalelo, hilos_disponibles, RUTA_INPUT, carpeta_temporal)
        except KeyboardInterrupt:
            print("\n[!] EJECUCIÓN CANCELADA POR EL USUARIO (Ctrl+C).")
            exitos, errores = 0, 0
        except Exception as error_critico:
            print(f"\n[!] ERROR: {error_critico}")
            exitos, errores = 0, 0
        finally:
            print(f"\n[!] Limpiando archivos generados en modo debug...")
            if path.exists(carpeta_temporal):
                rmtree(carpeta_temporal)
                print(f"[!] Carpeta {carpeta_temporal} eliminada.")
    else:
        MostrarEncabezado(hilos_disponibles, RUTA_BD, RUTA_INPUT)
        exitos, errores = RealizarRegistroParalelo(hilos_disponibles, RUTA_INPUT, RUTA_BD)

    MostrarResumen(exitos, errores)

if __name__ == '__main__':
    parser = ArgumentParser(description="Script de registro masivo BBDD CASIA-Twins en paralelo optimizado para TileDB.")
    parser.add_argument('-d', '--debug', action='store_true', help="Activa el modo debug (carpeta temporal y medición de tiempo).")
    args = parser.parse_args()
    
    main(args.debug)