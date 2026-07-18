# Realiza una prueba de rendimiento de todas las fases del reconocimiento de iris (Estructura CASIA-Twins)
from fnc.normalizar import Normalizar
from fnc.emparejar import Emparejar
from fnc.segmentar import Segmentar
from fnc.codificar import Codificar
from argparse import ArgumentParser
import matplotlib.pyplot as plt
from time import perf_counter
from os import scandir, path
from random import choice
from cv2 import imread
from numpy import repeat
from constantes import RUTA_INPUT, UMBRAL_PESTANA, RES_ANGULAR, RES_RADIAL, UMBRAL_DIST_HM, LONG_ONDA_MIN, SIGMA_ONF, RUTA_BD

def ObtenerImagenes(ruta=RUTA_INPUT):
    """
    DESCRIPCIÓN:
        Recorre buscando imágenes con la estructura de CASIA-Twins
        (Raíz -> Par_Gemelos -> [1L, 1R, 2L, 2R] -> Imagen).
    INPUT:
        ruta: Directorio raíz de Twins.
    OUTPUT:
        todas_imagenes - Lista con las rutas absolutas de todas las imagenes
        None           - Si no existe la carpeta o la lista resultante está vacía.
    """
    todas_imagenes = []
    
    if not path.exists(ruta):
        print(f"Error: No se encuentra la carpeta {ruta}")
        return None

    # Buscar las carpetas de los pares de gemelos (ej. /01, /02...)
    try:
        carpetas_pares = [d for d in scandir(ruta) if d.is_dir()]
    except FileNotFoundError:
        return None

    for par in sorted(carpetas_pares, key=lambda d: d.name):
        # Iterar sobre las 4 posibles variantes (Gemelo 1 o 2, Ojo L o R)
        for ojo_gemelo in ('1L', '1R', '2L', '2R'):
            ruta_ojo = path.join(par.path, ojo_gemelo)
            
            if not path.exists(ruta_ojo) or not path.isdir(ruta_ojo):
                continue
            
            try:
                for archivo in scandir(ruta_ojo):
                    if archivo.is_file() and archivo.name.lower().endswith(('.jpg', '.png', '.bmp', '.jpeg')):
                        todas_imagenes.append(archivo.path)
            except FileNotFoundError:
                pass
                
    if not todas_imagenes:
        print("No se encontraron imágenes en la estructura de directorios de Twins.")
        return None

    return todas_imagenes

def MedicionTiempos(todas_imagenes, num_iteraciones, callback=None):
    """
    DESCRIPCIÓN:
        Mide el tiempo de ejecución de cada fase del reconocimiento de iris para un num determinado de iteraciones
    """

    # Diccionario para guardar los tiempos acumulados
    tiempos = {
        'segmentacion': 0.0,
        'normalizacion': 0.0,
        'codificacion': 0.0,
        'comparacion': 0.0
    }

    exitos = 0

    for i in range(num_iteraciones):
        msg = f"Iteración {i+1} de {num_iteraciones}"
        if callback: callback(msg)

        # Escoger una imagen aleatoria por iteración
        ruta_img = choice(todas_imagenes)

        # cv2
        img = imread(ruta_img, 0)
        try:
            # Detección iris
            ini = perf_counter() 
            ciriris, cirpupil, img_con_ruido = Segmentar(img, UMBRAL_PESTANA)
            fin = perf_counter()
            tiempos['segmentacion'] += (fin - ini)

            # Polares
            ini = perf_counter()
            m_polar, m_ruido = Normalizar(img_con_ruido, ciriris[1], ciriris[0], ciriris[2],
                                                 cirpupil[1], cirpupil[0], cirpupil[2],
                                                 RES_RADIAL, RES_ANGULAR)
            fin = perf_counter()
            tiempos['normalizacion'] += (fin - ini)

            # Filtros de Gabor y ajuste geométrico
            ini = perf_counter()
            plantilla, mascara = Codificar(m_polar, m_ruido, LONG_ONDA_MIN, SIGMA_ONF)
            
            # Igualar dimensiones geométricas para la comparación en TileDB
            if mascara.shape[1] < plantilla.shape[1]:
                mascara = repeat(mascara, 2, axis=1)
                
            fin = perf_counter()
            tiempos['codificacion'] += (fin - ini)

            # Comparación
            ini = perf_counter()
            _ = Emparejar(plantilla, mascara, RUTA_BD, umbral=UMBRAL_DIST_HM)
            fin = perf_counter()
            tiempos['comparacion'] += (fin - ini)

            exitos += 1

        except Exception as e:
            print(f"Error en la iteración {i+1}: {e}")

    return tiempos, exitos

def MostrarTiempos(tiempos, exitos):
    """
    DESCRIPCIÓN:
        Muestra con formato el tiempo de ejecución de cada fase
    """
    tiempo_total_medio = sum(tiempos.values()) / exitos
    
    print("\n"+("="*50))
    print(f"Tiempo medio total: {tiempo_total_medio:.4f} segundos")
    print("-" * 50)
    
    for fase, tiempo_acumulado in tiempos.items():
        tiempo_medio = tiempo_acumulado / exitos
        porcentaje = (tiempo_medio / tiempo_total_medio) * 100
        
        # Mostrarlo bonito, primera en mayúscula
        nombre_limpio = fase.title()
        
        # Sangría
        print(f"{nombre_limpio.ljust(15)}: {tiempo_medio:.4f}s | {porcentaje:5.1f}%")
        
    print("="*50)

def GenerarGraficoTiempos(tiempos, exitos):
    """
    DESCRIPCIÓN:
        Genera un gráfico de barras con el porcentaje de tiempo que consume
        cada fase del sistema de reconocimiento.
    """
    tiempo_total_medio = sum(tiempos.values()) / exitos
    
    categorias = []
    porcentajes = []
    
    # Calcular porcentajes para la gráfica
    for fase, tiempo_acumulado in tiempos.items():
        tiempo_medio = tiempo_acumulado / exitos
        porcentaje = (tiempo_medio / tiempo_total_medio) * 100
        
        # Capitalizar la primera letra ('segmentacion' -> 'Segmentacion')
        categorias.append(fase.title())
        porcentajes.append(porcentaje)
        
    colores = ['#4A90E2', '#50E3C2', '#F5A623', '#D0021B'] 

    # Crear la figura
    fig, ax = plt.subplots(figsize=(9, 6))
    barras = ax.bar(categorias, porcentajes, color=colores, edgecolor='black')

    # Configuraciones visuales
    ax.set_ylim(0, max(porcentajes) + 15) 
    ax.set_ylabel('Porcentaje del Tiempo Total (%)', fontweight='bold')
    
    # Añadir título con iteraciones y tiempo medio total
    ax.set_title(f'Rendimiento del Sistema: Distribución de Tiempos (CASIA-Twins)\nIteraciones: {exitos} | Tiempo Medio Total: {tiempo_total_medio:.4f}s', 
                 fontweight='bold', pad=15)

    # Añadir el valor numérico (porcentaje y segundos) encima de cada barra
    for barra, nombre_fase in zip(barras, tiempos.keys()):
        altura = barra.get_height()
        tiempo_fase_medio = tiempos[nombre_fase] / exitos
        
        ax.annotate(f'{altura:.1f}%\n({tiempo_fase_medio:.4f}s)',
                    xy=(barra.get_x() + barra.get_width() / 2, altura),
                    xytext=(0, 5), 
                    textcoords="offset points",
                    ha='center', va='bottom', fontweight='bold')

    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    return fig

def main(num_iteraciones):
    """
    DESCRIPCIÓN:
        Flujo principal del programa.
    """
    if num_iteraciones <= 0:
        print("Error: El número de iteraciones debe ser mayor a 0.")
        return
    
    print(f"Evaluación con {num_iteraciones} iteraciones (CASIA-Twins).")

    todas_imagenes = ObtenerImagenes()
    if todas_imagenes is None:
        return

    tiempos, exitos = MedicionTiempos(todas_imagenes, num_iteraciones)

    if exitos > 0:
        MostrarTiempos(tiempos, exitos)
        fig = GenerarGraficoTiempos(tiempos, exitos)
        plt.show()
    else:
        print("No se pudo completar ninguna iteración para medir tiempos.")

# Lectura por consola
if __name__ == "__main__":
    parser = ArgumentParser(description="Evaluar el tiempo de ejecución del sistema de reconocimiento de iris (CASIA-Twins).")
    parser.add_argument('num_iteraciones', type=int, nargs='?', default=10, 
                        help="Número de iteraciones a procesar (por defecto: 10)")
                        
    args = parser.parse_args()
    main(args.num_iteraciones)