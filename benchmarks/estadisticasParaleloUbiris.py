# Realiza una prueba de aciertos y errores para un conjunto de imagenes (num_muestras) aleatorias (Estructura UBIRIS + Multiprocesamiento).
from json import loads
from tiledb import object_type, DenseArray
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from constantes import RUTA_INPUT, RUTA_BD, UMBRAL_DIST_HM
from fnc.extraerCaracteristicas import ExtraerCaracteristicas
from fnc.emparejar import Emparejar
from argparse import ArgumentParser
from os import path, scandir
from random import sample
from multiprocessing import Pool, cpu_count
from numpy import repeat

# =====================================================================
# FUNCION WORKER PARA MULTIPROCESAMIENTO
# Debe estar en el nivel superior del archivo para poder ser serializada
# =====================================================================
def WorkerExtractorEstadisticas(ruta_img):
    """
    Extrae las características de una imagen aislada para multiprocesamiento.
    """
    try:
        template, mask, _ = ExtraerCaracteristicas(ruta_img)
        
        # Igualar dimensiones geométricas para la comparación XOR en Emparejar
        if mask.shape[1] < template.shape[1]:
            mask = repeat(mask, 2, axis=1)
            
        return (True, ruta_img, template, mask, "")
    except Exception as e:
        return (False, ruta_img, None, None, str(e))

# =====================================================================

def ObtenerImagenesEstadisticas(ruta='ubiris1/UBIRIS_800_600/'):
    """
    DESCRIPCIÓN:
        Recorre las carpetas buscando imágenes con la estructura de UBIRIS
        (Sessao_X -> Sujeto -> Img_...).
    OUTPUT:
        todas_imagenes: Lista de tuplas (ruta_completa, id_real).
    """
    todas_imagenes = []

    if not path.exists(ruta):
        print(f"Error: No se encuentra la carpeta {ruta}")
        return None

    try:
        carpetas_sessao = [d for d in scandir(ruta) if d.is_dir() and d.name.lower().startswith("sessao")]
    except FileNotFoundError:
        return None

    for sessao in sorted(carpetas_sessao, key=lambda d: d.name):
        try:
            carpetas_sujetos = [d for d in scandir(sessao.path) if d.is_dir()]
        except FileNotFoundError:
            continue
            
        for sujeto in sorted(carpetas_sujetos, key=lambda d: d.name):
            id_real = f"{sujeto.name}"
            
            try:
                for img in scandir(sujeto.path):
                    if img.is_file() and img.name.lower().endswith(('.jpg', '.png', '.bmp', '.jpeg')):
                        todas_imagenes.append((img.path, id_real))
            except FileNotFoundError:
                pass

    if not todas_imagenes:
        return None
    return todas_imagenes

def ObtenerEstadisticas(todas_imagenes, num_muestras, umbral, callback=None):
    """
    DESCRIPCIÓN:
        Extrae en paralelo las caract. del iris y compara secuencialmente 
        con la BBDD para evaluar FTE, FRR, FAR y Aciertos.
    """
    stats = {
        'fte': 0,       
        'frr': 0,       
        'far': 0,       
        'aciertos': 0 
    }
    
    if not path.exists(RUTA_BD) or object_type(RUTA_BD) != "array":
        print("Error: La base de datos TileDB no existe. Ejecute el registro primero.")
        return stats
        
    metadata_bd = {}
    try:
        with DenseArray(RUTA_BD, mode='r') as array:
            ids_comp = loads(array.meta.get("ids", "[]"))
            orig_comp = loads(array.meta.get("exinfos", "[]"))
            
            for idx in range(len(ids_comp)):
                id_usuario = str(ids_comp[idx])
                archivo = str(orig_comp[idx])
                
                if id_usuario not in metadata_bd:
                    metadata_bd[id_usuario] = []
                metadata_bd[id_usuario].append(archivo)
    except Exception as e:
        print(f"Aviso: No se pudieron cargar los metadatos de TileDB: {e}")

    num_muestras_reales = min(num_muestras, len(todas_imagenes))
    muestras_elegidas = sample(todas_imagenes, num_muestras_reales)
    
    # Crear un diccionario para recuperar el ID real a partir de la ruta
    mapa_ids = {ruta: id_real for ruta, id_real in muestras_elegidas}
    rutas_a_procesar = list(mapa_ids.keys())

    # Configurar el Pool de procesos
    hilos = max(1, (cpu_count() or 4) - 1)
    print(f"\nIniciando extracción paralela con {hilos} hilos de CPU...")
    pool = Pool(processes=hilos)
    
    procesadas = 0

    # imap_unordered va devolviendo las imagenes según terminan (más rápido)
    for resultado in pool.imap_unordered(WorkerExtractorEstadisticas, rutas_a_procesar):
        exito, ruta_img, template, mask, error_msg = resultado
        id_real = mapa_ids[ruta_img]
        nombre_img = path.basename(ruta_img)
        
        procesadas += 1
        msg = f"Muestra {procesadas} de {num_muestras_reales} completada"
        if callback: callback(msg)
        else: print(f"\r{msg}", end="")
        
        if not exito:
            stats['fte'] += 1
            continue
            
        # Comparación (Realizada por el proceso principal para proteger la memoria RAM)
        try:
            resultados = Emparejar(template, mask, RUTA_BD, umbral)
            
            if resultados == 0 or resultados is None:
                stats['frr'] += 1
                continue
                
            match_valido = False
            for match_id, _ in resultados:
                # Omitir el auto-emparejamiento con exactamente la misma imagen
                if match_id in metadata_bd:
                    archivos_asociados = metadata_bd[match_id]
                    if len(archivos_asociados) == 1 and archivos_asociados[0] == nombre_img:
                        continue
                
                if match_id == id_real:
                    stats['aciertos'] += 1
                else:
                    stats['far'] += 1
                
                match_valido = True
                break 
                
            if not match_valido:
                stats['frr'] += 1

        except Exception as e:
            stats['fte'] += 1

    pool.close()
    pool.join()
    print() # Salto de línea limpio tras el contador
    return stats

def MostrarEstadisticas(stats, total):
    print("\n" + "="*55)
    print("Estadísticas de Precisión (Benchmark)")
    print("="*55)
    print(f"{'Muestras evaluadas:':<40} {total:>5}")
    print("-" * 55)
    
    if total > 0:
        fte_pct = (stats['fte'] / total) * 100
        aciertos_pct = (stats['aciertos'] / total) * 100
        frr_pct = (stats['frr'] / total) * 100
        far_pct = (stats['far'] / total) * 100
        
        print(f"{'FTE (Fallos Extracción/Comparación):':<40} {stats['fte']:>5} ({fte_pct:>6.2f}%)")
        print(f"{'FRR (Falsos Rechazos):':<40} {stats['frr']:>5} ({frr_pct:>6.2f}%)")
        print(f"{'FAR (Falsos Positivos):':<40} {stats['far']:>5} ({far_pct:>6.2f}%)")
        print(f"{'Aciertos:':<40} {stats['aciertos']:>5} ({aciertos_pct:>6.2f}%)")
    print("="*55)

def GenerarGraficoEstadisticas(stats, total, umbral):
    if total > 0:
        fte_pct = (stats['fte'] / total) * 100
        aciertos_pct = (stats['aciertos'] / total) * 100
        frr_pct = (stats['frr'] / total) * 100
        far_pct = (stats['far'] / total) * 100
    else:
        fte_pct = aciertos_pct = frr_pct = far_pct = 0

    categorias = ['FTE\n(Fallo Extracción)', 'FRR\n(Falso Rechazo)', 'FAR\n(Falso Positivo)', 'Aciertos']
    porcentajes = [fte_pct, frr_pct, far_pct, aciertos_pct]
    colores = ['gray', 'orange', 'red', 'green']

    fig, ax = plt.subplots(figsize=(9, 6))
    barras = ax.bar(categorias, porcentajes, color=colores, edgecolor='black')

    ax.set_ylim(0, 110) 
    ax.set_ylabel('Porcentaje (%)', fontweight='bold')
    
    ax.set_title(f'Rendimiento del Sistema Biométrico\nMuestras evaluadas: {total} | Umbral de Hamming: {umbral}', 
                 fontweight='bold', pad=15)

    for barra in barras:
        altura = barra.get_height()
        ax.annotate(f'{altura:.2f}%',
                    xy=(barra.get_x() + barra.get_width() / 2, altura),
                    xytext=(0, 5), 
                    textcoords="offset points",
                    ha='center', va='bottom', fontweight='bold')

    ax.grid(axis='y', linestyle='--', alpha=0.7)
    return fig

def main(num_muestras, umbral):
    if num_muestras <= 0:
        print("Error: El número de muestras debe ser mayor a 0.")
        return

    print(f"Evaluación con {num_muestras} muestras (Umbral: {umbral}).")

    todas_imagenes = ObtenerImagenesEstadisticas()
    if todas_imagenes is None:
        print("Error: No se pudieron obtener las imagenes o no se encontró la estructura de directorios.")
        return

    stats = ObtenerEstadisticas(todas_imagenes, num_muestras, umbral)
    MostrarEstadisticas(stats, num_muestras)

    fig = GenerarGraficoEstadisticas(stats, num_muestras, umbral)
    plt.show()
   
if __name__ == "__main__":
    parser = ArgumentParser(description="Evaluar la tasa de aciertos y rechazos del sistema de reconocimiento de iris (UBIRIS Multiproceso).")
    parser.add_argument('num_muestras', type=int, nargs='?', default=10, 
                        help="Número de muestras a procesar (por defecto: 10)")
    parser.add_argument('umbral', type=float, nargs='?', default=UMBRAL_DIST_HM, 
                        help="Valor umbral para la distancia de Hamming en la comparación de dos ojos "
                        "(por defecto: {})".format(UMBRAL_DIST_HM))
    
    args = parser.parse_args()
    main(args.num_muestras, args.umbral)