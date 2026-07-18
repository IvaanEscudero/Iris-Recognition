# Archivo encargado de comparar plantillas biométricas y calcular distancias de Hamming utilizando TileDB.
from constantes import RUTA_BD, UMBRAL_DIST_HM
from os import path, cpu_count
import numpy as np
import tiledb
from json import loads

def ObtenerContextoTileDB():
    """
    Descripción:
        Genera un contexto optimizado para extraer el máximo rendimiento de TileDB.
        Delega la carga de trabajo a los hilos nativos de C++ y evita bloqueos de Windows.
    """
    config = tiledb.Config()
    config["vfs.file.enable_filelocks"] = "false"
    config["sm.memory_budget"] = str(128 * 1024 * 1024) # Buffer de 128 MB
    
    # Exprimir los hilos internos de C++ para lectura paralela desde el disco
    hilos = str(max(1, (cpu_count() or 4) - 1))
    config["sm.num_reader_threads"] = hilos
    config["sm.compute_concurrency_level"] = hilos
    
    return tiledb.Ctx(config)

def Emparejar(plantilla_extr, mascara_extr, ruta_bd=RUTA_BD, umbral=UMBRAL_DIST_HM):
    """
    Descripción:
        Comparar la plantilla extraída con la base de datos TileDB completa.
        Flujo secuencial en Python, pero vectorizado en C (NumPy) y multihilo en C++ (TileDB).
    """
    if not path.exists(ruta_bd) or tiledb.object_type(ruta_bd) != "array":
        return 0

    ctx = ObtenerContextoTileDB()


    with tiledb.DenseArray(ruta_bd, mode='r', ctx=ctx) as array:
        dominio = array.nonempty_domain()
        
        if dominio is None:
            return 0
            
        idx_max = dominio[0][1] + 1
        
        # Cargamos toda la BD en RAM en un solo movimiento bloqueante
        datos_bd = array[0:idx_max, :, :]
        
        plantillas = datos_bd['template']
        mascaras = datos_bd['mask']
        
        textos_ids = array.meta.get("ids", "[]")
        nombres_usuarios = loads(textos_ids)

    num_usuarios = plantillas.shape[0]
    if num_usuarios == 0:
        return 0

    
    # Creamos la matriz para guardar las distancias de todos los usuarios a la vez
    dist_hm = np.full((17, num_usuarios), np.nan)
    
    # Evaluamos las 17 rotaciones (-8 a +8)
    for s, desplazamientos in enumerate(range(-8, 9)):
        plantilla_desp = DesplazarBits(plantilla_extr, desplazamientos)
        mascara_desp = DesplazarBits(mascara_extr, desplazamientos)
        
        # Broadcasting 3D a toda la base de datos simultáneamente
        mascara_combinada = np.logical_or(mascara_desp, mascaras)
        bits_mascara = np.sum(mascara_combinada, axis=(1, 2))
        bits_totales = plantilla_desp.size - bits_mascara
        
        diferencias = np.logical_xor(plantilla_desp, plantillas)
        diferencias = np.logical_and(diferencias, np.logical_not(mascara_combinada))
        bits_diferentes = np.sum(diferencias, axis=(1, 2))
        
        with np.errstate(divide='ignore', invalid='ignore'):
            dist_hm[s, :] = bits_diferentes / bits_totales
            
    # Extraemos la distancia mínima (mejor alineamiento) para cada usuario de la BD
    distancias_minimas = np.nanmin(dist_hm, axis=0)

   
    # Nos quedamos solo con los que superan el umbral (y descartamos errores/NaN)
    ind_validos = np.where((distancias_minimas >= 0) & (distancias_minimas <= umbral))[0]

    if len(ind_validos) == 0:
        return 0

    distancias_filtradas = distancias_minimas[ind_validos]
    nombres_filtrados = [nombres_usuarios[idx] for idx in ind_validos]
    
    # Ordenar los resultados de mayor a menor similitud (menor distancia es mejor)
    ind_orden = np.argsort(distancias_filtradas)
    res = [(nombres_filtrados[idx], distancias_filtradas[idx]) for idx in ind_orden]
    return res

def CalcularDistanciaHamming(plantilla_1, mascara_1, plantilla_2, mascara_2):
    """
    Descripción:
        Calcular la distancia de Hamming 1 a 1 entre dos plantillas de iris.
    """
    dist = np.nan

    for despl in range(-8, 9):
        plantilla_1_desp = DesplazarBits(plantilla_1, despl)
        mascara_1_desp = DesplazarBits(mascara_1, despl)

        mascara_combinada = np.logical_or(mascara_1_desp, mascara_2)
        bits_mascara = np.sum(mascara_combinada == 1)
        bits_totales = plantilla_1_desp.size - bits_mascara

        diferencias = np.logical_xor(plantilla_1_desp, plantilla_2)
        diferencias = np.logical_and(diferencias, np.logical_not(mascara_combinada))
        bits_diferentes = np.sum(diferencias == 1)

        if bits_totales == 0:
            dist_actual = np.nan
        else:
            dist_actual = bits_diferentes / bits_totales
            if np.isnan(dist) or dist_actual < dist:
                dist = dist_actual
                
    return dist

def DesplazarBits(plantilla, num_despl):
    """
    Descripción:
        Desplazar los patrones de bits del iris de forma circular.
    """
    salto = 2 * num_despl
    return np.roll(plantilla, shift=salto, axis=1)

def CargarHamming(id_usuario, plantilla_extr, mascara_extr, ruta_bd=RUTA_BD):
    """
    Descripción:
        Abre TileDB con el contexto seguro, extrae a un solo usuario y calcula su distancia.
    """
    try:
        ctx = ObtenerContextoTileDB()
        
        with tiledb.DenseArray(ruta_bd, mode='r', ctx=ctx) as array:
            textos_ids = array.meta.get("ids", "[]")
            lista_ids = loads(textos_ids)
            
            if id_usuario not in lista_ids:
                return (id_usuario, -1)
                
            idx = lista_ids.index(id_usuario)
            
            datos = array[idx:idx+1, :, :]
            plantilla = datos['template'][0]
            mascara = datos['mask'][0]

        distancia_hm = CalcularDistanciaHamming(plantilla_extr, mascara_extr, plantilla, mascara)
        return (id_usuario, distancia_hm)
        
    except Exception as e:
        print(f"Error interno en CargarHamming: {e}")
        return (id_usuario, -1)