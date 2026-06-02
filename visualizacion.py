# visualizacion.py
"""
Módulo: visualizacion.py
Se encarga de procesar los datos de las simulaciones y exportar de forma autónoma
las 5 gráficas requeridas por la guía en formato PNG.
"""
import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def generar_graficas(resultados_mc, datos_ejemplo, matriz_sensibilidad, lista_lambdas, lista_c, ruta_guardado="."):
    # Configuramos el estilo visual base para que se vea limpio y académico
    sns.set_theme(style="whitegrid")
    
    # -------------------------------------------------------------------------
    # GRÁFICA 1: Evolución temporal del número de clientes (Réplica representativa)
    # -------------------------------------------------------------------------
    plt.figure(figsize=(9, 5))
    if datos_ejemplo:
        tiempos = [m['llegada'] for m in datos_ejemplo]
        # Aproximación del volumen dinámico de la cola a lo largo de las horas
        clientes_en_tiempo = np.cumsum([1] * len(tiempos)) - np.arange(len(tiempos))
        plt.plot(tiempos, clientes_en_tiempo, color='darkcyan', linewidth=2, label='Clientes en sistema')
    plt.title("Evolución Temporal del Número de Clientes en el Sistema", fontsize=12, fontweight='bold')
    plt.xlabel("Reloj de Simulación (Horas)", fontsize=10)
    plt.ylabel("Cantidad de Clientes", fontsize=10)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(ruta_guardado, "grafica_1_evolucion_temporal.png"), dpi=150)
    plt.close()

    # -------------------------------------------------------------------------
    # GRÁFICA 2: Histogramas de tiempos de espera Wq (Verificación TCL)
    # -------------------------------------------------------------------------
    plt.figure(figsize=(8, 5))
    valores_wq_minutos = [v * 60 for v in resultados_mc['Wq']['valores']] # Pasamos a minutos
    sns.histplot(valores_wq_minutos, kde=True, color='royalblue', bins=10, edgecolor='black')
    media_wq_m = resultados_mc['Wq']['media'] * 60
    plt.axvline(media_wq_m, color='crimson', linestyle='--', linewidth=2, label=f"Media μ: {media_wq_m:.2f} min")
    plt.title("Distribución de Medias de Wq entre Réplicas (Verificación TCL)", fontsize=12, fontweight='bold')
    plt.xlabel("Tiempo Promedio de Espera Wq (Minutos)", fontsize=10)
    plt.ylabel("Frecuencia (Jornadas)", fontsize=10)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(ruta_guardado, "grafica_2_distribucion_wq.png"), dpi=150)
    plt.close()

    # -------------------------------------------------------------------------
    # GRÁFICA 3: Curva de Capacidad (Wq promedio vs número de servidores c)
    # -------------------------------------------------------------------------
    plt.figure(figsize=(8, 5))
    # Analizamos para la lambda base = 10 clientes/hora
    c_estables = [c for c in lista_c if matriz_sensibilidad[c][10.0]['stable']]
    wq_minutos = [matriz_sensibilidad[c][10.0]['Wq'] * 60 for c in c_estables]
    
    plt.plot(c_estables, wq_minutos, marker='o', markersize=8, color='firebrick', linewidth=2.5, label='Tiempo de Espera')
    plt.axhline(10.0, color='forestgreen', linestyle=':', linewidth=2, label='Umbral Límite Directivo (10 min)')
    plt.title("Curva de Capacidad: Tiempo de Espera Wq vs Cantidad de Técnicos (λ = 10)", fontsize=12, fontweight='bold')
    plt.xlabel("Número de Técnicos Asignados (c)", fontsize=10)
    plt.ylabel("Wq Promedio (Minutos)", fontsize=10)
    plt.xticks(lista_c)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(ruta_guardado, "grafica_3_capacidad_wq.png"), dpi=150)
    plt.close()

    # -------------------------------------------------------------------------
    # GRÁFICA 4: Factor de Utilización (ρ) vs Tasa de Llegada (λ)
    # -------------------------------------------------------------------------
    plt.figure(figsize=(8, 5))
    for c in lista_c:
        lambdas_validas = [lam for lam in lista_lambdas if matriz_sensibilidad[c][lam]['estable']]
        rhos = [matriz_sensibilidad[c][lam]['rho'] for lam in lambdas_validas]
        plt.plot(lambdas_validas, rhos, marker='s', label=f"c = {c} Técnicos")
    
    plt.axhline(1.0, color='black', linestyle='--', alpha=0.7, label='Límite de Saturación (ρ = 1.0)')
    plt.title("Factor de Utilización del Sistema (ρ) vs Tasa de Llegada (λ)", fontsize=12, fontweight='bold')
    plt.xlabel("Tasa de Llegada λ (Clientes / Hora)", fontsize=10)
    plt.ylabel("Factor de Utilización promedio (ρ)", fontsize=10)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(ruta_guardado, "grafica_4_utilizacion_rho.png"), dpi=150)
    plt.close()

    # -------------------------------------------------------------------------
    # GRÁFICA 5: Heatmap del Análisis de Sensibilidad para Wq (Minutos)
    # -------------------------------------------------------------------------
    plt.figure(figsize=(9, 6))
    grid_wq = np.zeros((len(lista_c), len(lista_lambdas)))
    
    for i, c in enumerate(lista_c):
        for j, lam in enumerate(lista_lambdas):
            val = matriz_sensibilidad[c][lam]['Wq']
            grid_wq[i, j] = val * 60 if val is not None else np.nan

    sns.heatmap(grid_wq, annot=True, fmt=".1f", cmap="YlOrRd", cbar=True,
                xticklabels=[f"{lam} (Base)" if lam==10.0 else f"{lam} (+20%)" if lam==12.0 else f"{lam}" for lam in lista_lambdas], 
                yticklabels=lista_c, mask=np.isnan(grid_wq),
                cbar_kws={'label': 'Tiempo de Espera en Cola (Minutos)'}, annot_kws={'size': 11, 'weight': 'bold'})
    
    plt.title("Mapa de Calor: Wq en Minutos según Escenarios Operativos", fontsize=12, fontweight='bold')
    plt.xlabel("Tasa de Llegada de Clientes λ (Clientes / Hora)", fontsize=10)
    plt.ylabel("Número de Técnicos Disponibles (c)", fontsize=10)
    plt.tight_layout()
    plt.savefig(os.path.join(ruta_guardado, "grafica_5_heatmap_sensibilidad.png"), dpi=150)
    plt.close()
    
    print("[INFO] ¡Las 5 gráficas profesionales han sido exportadas con éxito en formato PNG!")
