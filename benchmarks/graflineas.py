# Script para generar el gráfico de evolución de la Tasa de Aciertos por repositorio
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

def GenerarGraficoPrecision(datos_repositorios):
    """
    DESCRIPCIÓN:
        Genera un gráfico de líneas que relaciona el número de imágenes de una BBDD
        con su respectiva Tasa de Aciertos (%).
    INPUT:
        datos_repositorios: Lista de tuplas con el formato 
                            (Nombre_BBDD, Numero_Imagenes, Porcentaje_Aciertos)
    """
    # 1. Ordenar los datos por número de imágenes (eje X) de menor a mayor
    datos_ordenados = sorted(datos_repositorios, key=lambda x: x[1])

    # 2. Extraer las listas de coordenadas
    nombres = [dato[0] for dato in datos_ordenados]
    num_imagenes = [dato[1] for dato in datos_ordenados]
    aciertos = [dato[2] for dato in datos_ordenados]

    # 3. Configurar la figura
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 4. Dibujar la línea de Aciertos (Verde con círculos)
    ax.plot(num_imagenes, aciertos, marker='o', linestyle='-', color='#008000', 
            linewidth=2, markersize=8, markerfacecolor='#32CD32', markeredgecolor='black',
            label='Tasa de Aciertos')

    # 5. Diccionario de posiciones manuales para evitar solapamientos
    # Formato: "Nombre": (Desplazamiento_X, Desplazamiento_Y, Alineación_H, Alineación_V)
    posiciones_manuales = {
        "UBIRIS": (-15, 15, 'right', 'bottom'),           # Arriba a la izquierda
        "CASIA-ThousandMini": (0, -15, 'center', 'top'),  # Como estaba (Abajo centro)
        "CASIA-LampMini": (0, 15, 'center', 'bottom'),    # Como estaba (Arriba centro)
        "CASIA-Interval": (15, 15, 'left', 'bottom'),     # Arriba a la derecha
        "CASIA-Twins": (15, -15, 'left', 'top'),          # Abajo a la derecha
        "PolyU": (0, -15, 'center', 'top'),               # Como estaba (Abajo centro)
        "CASIA-Lamp": (0, 15, 'center', 'bottom'),        # Como estaba (Arriba centro)
        "CASIA-Thousand": (0, -15, 'center', 'top')       # Como estaba (Abajo centro)
    }

    # 6. Añadir las etiquetas con sus posiciones específicas
    for i, nombre in enumerate(nombres):
        texto_etiqueta = f"{nombre}\n({aciertos[i]:.2f}%)"
        
        # Extraer la configuración del diccionario (o usar un valor por defecto si falta alguna)
        despl_x, despl_y, align_h, align_v = posiciones_manuales.get(nombre, (0, 15, 'center', 'bottom'))
            
        ax.annotate(texto_etiqueta,
                    xy=(num_imagenes[i], aciertos[i]),
                    xytext=(despl_x, despl_y), 
                    textcoords="offset points",
                    ha=align_h, va=align_v, 
                    fontweight='bold', fontsize=9,
                    # Caja de fondo para asegurar legibilidad
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="none", alpha=0.85))

    # 7. Configuraciones visuales del gráfico
    # Damos un margen extra a la derecha e izquierda para que las nuevas posiciones no se corten
    ax.set_xlim(left=-500, right=max(num_imagenes) * 1.15)
    
    # Ajustamos el Y desde -10 para que las etiquetas de abajo no se salgan del marco
    ax.set_ylim(bottom=-10, top=115)

    ax.set_title('Evolución de la Tasa de Aciertos vs Volumen de Datos', 
                 fontweight='bold', pad=15, fontsize=14)
    ax.set_xlabel('Número de Imágenes en la Base de Datos', fontweight='bold', fontsize=11)
    ax.set_ylabel('Tasa de Aciertos (%)', fontweight='bold', fontsize=11)

    # Cuadrícula para facilitar la lectura
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Añadir la leyenda
    ax.legend(loc='upper right', fontsize=11, framealpha=0.9)

    return fig

def main():
    datos_prueba = [
        ("UBIRIS", 1876, 89.14),
        ("CASIA-Thousand", 20000, 5.70),
        ("CASIA-Interval", 2639, 98.56),
        ("CASIA-Lamp", 16212, 21.60),
        ("CASIA-Twins", 3183, 51.47),
        ("PolyU", 6270, 72.30),
        ("CASIA-LampMini", 2374, 49.96),
        ("CASIA-ThousandMini", 2000, 23.80)
    ]

    print("Generando gráfico de evolución de precisión...")
    fig = GenerarGraficoPrecision(datos_prueba)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()