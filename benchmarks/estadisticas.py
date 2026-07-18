# Realiza una prueba de aciertos y errores para un conjunto de imagenes (num_muestras) aleatorias.
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

def ObtenerImagenesEstadisticas(ruta=RUTA_INPUT):
    """
    DESCRIPCIÓN:
        Recorre las carpetas de ruta buscando imágenes de ojos ('L' y 'R') para cada usuario.
    INPUT:

    OUTPUT:
        todas_imagenes: Lista de tuplas con la ruta completa y el ID real del usuario.
        None: Si no existe la carpeta o la lista resultante está vacía.
    """
    todas_imagenes = []

    # Existe la carpeta?
    if not path.exists(ruta):
        print(f"Error: No se encuentra la carpeta {ruta}")
        return None

    # Recorrer las carpetas de los usuarios (/001, /002...)
    for usuario in scandir(ruta):
        # Ignorar los archivos que no sean carpetas
        if usuario.is_dir():
            # Recorrer las carpetas de los ojos Izquierdo y Derecho (/001/L, /001/R, /002/L, /002/R...)
            for ojo in ('L', 'R'):

                ruta_ojo = path.join(usuario.path, ojo)
                try:
                    # Recorrer las imagenes de cada ojo de cada usuario (/001/L/S1001L01.jpg, /001/R/S1001R01.jpg...)
                    for img in scandir(ruta_ojo):
                        if img.is_file():
                            # Guardamos la tupla con la ruta y el ID (/001/L/S1001L01.jpg, 001_L)
                            todas_imagenes.append((img.path, f"{usuario.name}_{ojo}"))
                except FileNotFoundError:
                    # Si en algún ojo no hay imagenes, pasamos al siguiente ojo o usuario
                    pass

    # Si no ha encontrado ninguna imagen
    if not todas_imagenes:
        return None
    
    return todas_imagenes

def ObtenerEstadisticas(todas_imagenes, num_muestras,umbral,callback=None):
    """
    DESCRIPCIÓN:
        Extrae las caract. del iris y compara con la BBDD para un num determinado de muestras aleatorias.
        Lleva el conteo de si es fte, frr, far o acierto.
    INPUT:
        todas_imagenes: Tuplas con la ruta de las imgs y ID del usuario.
        num_muestras: Num de muestras aleatorias que se van a extraer.
        umbral: Límite max de la distancia de Hamming.
    OUTPUT:
        stats: Diccionario con conteo de fte, frr, far y aciertos.
    """
    # Diccionario para contar aciertos o fallos.
    stats = {
        'fte': 0,       # Fail to enroll / Fallo de extracción o comparación
        'frr': 0,       # Fail rejection rate / Falsos rechazos
        'far': 0,       # False acceptance rate / Falsos positivos
        'aciertos': 0 
        }
    
  # Comprobar estado de la base de datos antes de iniciar
    if not path.exists(RUTA_BD) or object_type(RUTA_BD) != "array":
        print("Error: La base de datos TileDB no existe. Ejecute el registro primero.")
        return stats
    metadata_bd = {}
    try:
        with DenseArray(RUTA_BD, mode='r') as array:
            textos_ids = array.meta.get("ids", "[]")
            textos_exinfo = array.meta.get("exinfos", "[]")
            
            ids_comp = loads(textos_ids)
            orig_comp = loads(textos_exinfo)
            
            for idx in range(len(ids_comp)):
                id_usuario = str(ids_comp[idx])
                archivo = str(orig_comp[idx])
                
                if id_usuario not in metadata_bd:
                    metadata_bd[id_usuario] = []
                metadata_bd[id_usuario].append(archivo)
                
    except Exception as e:
        print(f"Aviso: No se pudieron cargar los metadatos de TileDB: {e}")

    # 1. Protección: Evitar pedir más muestras de las imágenes que realmente hay en la carpeta
    num_muestras_reales = min(num_muestras, len(todas_imagenes))

    # 2. Muestreo SIN reemplazo: Coger N imágenes únicas de golpe para no repetir
    muestras_elegidas = sample(todas_imagenes, num_muestras_reales)
    for i, (ruta_img, id_real) in enumerate(muestras_elegidas):
        nombre_img = path.basename(ruta_img)
        msg=f"Muestra {i+1} de {num_muestras}"
        if callback: callback(msg)
        
        # Extracción: Segmentación, Normalización y Codificación
        try:
            template, mask, _ = ExtraerCaracteristicas(ruta_img)
        except Exception:
            #FTE (Fallo al extraer características)
            stats['fte'] += 1
            continue
            
        # Comparación con BBDD
        try:
            resultados = Emparejar(template, mask, RUTA_BD, umbral)
            
            # Resultados vacíos o ninguno válido 
            # (Debería acertar pues escoge una muestra que ya está en BBDD)
            if resultados == 0 or resultados is None:
                #FRR (Falso Rechazo: Ninguna coincidencia superó el umbral o BD vacía)          
                stats['frr'] += 1
                continue
                
            # Valorar tipo de coincidencia
            match_valido = False
            for match_id, _ in resultados:
                # Obtener metadatos con el usuario que ha hecho match con la BBDD compilada
                if match_id in metadata_bd:
                    archivos_asociados = metadata_bd[match_id]
                    if len(archivos_asociados) == 1 and archivos_asociados[0] == nombre_img:
                        continue
                
                if match_id == id_real:
                    #Acierto
                    stats['aciertos'] += 1
                else:
                    
                    #FAR (Falso Positivo: Confundido con otra persona)
                    stats['far'] += 1
                
                match_valido = True
                break # Solo evaluamos la mejor coincidencia distinta
                
            if not match_valido:
                # Si el único match era la propia foto y no hay más, falso rechazo
                #FRR (Solo se encontró la misma foto, no reconoció otras del mismo ojo)
                stats['frr'] += 1

        # Errores durante la comparación con BBDD
        except Exception as e:
            stats['fte'] += 1
            print(f"Error en matching: {e}")

    return stats

def MostrarEstadisticas(stats, total):
    """
    DESCRIPCIÓN:
        Imprime por consola con formato los datos de estadisticas del sistema.
    INPUT:
        stats: Diccionario con conteo de fte, frr, far y aciertos.
        total: Num de muestras.
    OUTPUT:
        
    """
    print("\n" + "="*55)
    print("Estadísticas")
    print("="*55)
    
    procesados = total - stats['fte']
    
    print(f"{'Muestras evaluadas:':<40} {total:>5}")
    print("-" * 55)
    
    # Porcentajes sobre el total de intentos
    if total > 0:
        fte_pct = (stats['fte'] / total) * 100
        aciertos_pct = (stats['aciertos'] / total) * 100
        frr_pct = (stats['frr'] / total) * 100
        far_pct = (stats['far'] / total) * 100
        
        # Enseñar bonito con sangrías
        print(f"{'FTE (Fallos Extracción/Comparación):':<40} {stats['fte']:>5} ({fte_pct:>6.2f}%)")
        print(f"{'FRR (Falsos Rechazos):':<40} {stats['frr']:>5} ({frr_pct:>6.2f}%)")
        print(f"{'FAR (Falsos Positivos):':<40} {stats['far']:>5} ({far_pct:>6.2f}%)")
        print(f"{'Aciertos:':<40} {stats['aciertos']:>5} ({aciertos_pct:>6.2f}%)")
    
    print("="*55)

def GenerarGraficoEstadisticas(stats, total, umbral):
    """
    DESCRIPCIÓN:
        Genera un gráfico de barras con los porcentajes de cada estado
        de clasificación (FTE, FRR, FAR, ACIERTO).
    INPUT:
        stats: Diccionario con los conteos.
        total: Número total de muestras.
        umbral: Valor del umbral de Hamming.
    OUTPUT:
        fig: Objeto de la figura de Matplotlib
    """
    # Cálculos de porcentajes respetando tu lógica original
    
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

    # Crear la figura
    fig, ax = plt.subplots(figsize=(9, 6))
    barras = ax.bar(categorias, porcentajes, color=colores, edgecolor='black')

    # Configuraciones visuales del gráfico
    ax.set_ylim(0, 110) # Damos margen arriba para que quepan las etiquetas de texto
    ax.set_ylabel('Porcentaje (%)', fontweight='bold')
    
    # Añadir título con Muestras y Umbral
    ax.set_title(f'Rendimiento del Sistema Biométrico\nMuestras evaluadas: {total} | Umbral de Hamming: {umbral}', 
                 fontweight='bold', pad=15)

    # Añadir el valor numérico exacto justo encima de cada barra
    for barra in barras:
        altura = barra.get_height()
        ax.annotate(f'{altura:.2f}%',
                    xy=(barra.get_x() + barra.get_width() / 2, altura),
                    xytext=(0, 5),  # 5 puntos de desplazamiento hacia arriban
                    textcoords="offset points",
                    ha='center', va='bottom', fontweight='bold')

    # Añadir una cuadrícula horizontal de fondo para facilitar la lectura
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    return fig

def main(num_muestras, umbral):
    """
    DESCRIPCIÓN:
        Flujo principal del archivo.
    INPUT:
        num_muestras: Num de muestras a procesar.
        umbral: Límite max de la distancia de Hamming.
    OUTPUT:
        
    """

    if num_muestras <= 0:
        print("Error: El número de muestras debe ser mayor a 0.")
        return

    print(f"Evaluación con {num_muestras} muestras (Umbral: {umbral}).")

    todas_imagenes = ObtenerImagenesEstadisticas()
    if todas_imagenes is None:
        print("Error: No se pudieron obtener las imagenes.")
        return

    stats = ObtenerEstadisticas(todas_imagenes, num_muestras, umbral)
    MostrarEstadisticas(stats, num_muestras)

    fig = GenerarGraficoEstadisticas(stats, num_muestras, umbral)
    plt.show()
   
# Lectura por consola
if __name__ == "__main__":
    parser = ArgumentParser(description="Evaluar la tasa de aciertos y rechazos del sistema de reconocimiento de iris.")
    parser.add_argument('num_muestras', type=int, nargs='?', default=10, 
                        help="Número de muestras a procesar (por defecto: 10)")
    parser.add_argument('umbral', type=float, nargs='?', default=UMBRAL_DIST_HM, 
                        help="Valor umbral para la distancia de Hamming en la comparación de dos ojos "
                        "(por defecto: {})".format(UMBRAL_DIST_HM))
    
    args = parser.parse_args()
    
    main(args.num_muestras, args.umbral)