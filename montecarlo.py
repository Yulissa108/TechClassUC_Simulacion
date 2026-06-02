# montecarlo.py
"""
Módulo: montecarlo.py
Se encarga de ejecutar N réplicas independientes de Montecarlo, 
extrayendo promedios, desviaciones estándar e intervalos de confianza.
"""
import math
import numpy as np
from simulacion_des import correr_una_replica

def correr_replicas(n_replicas, semilla_base, tasa_llegada, tasa_servicio, num_tecnicos, tiempo_sim, tiempo_calentamiento):
    """
    Ejecuta múltiples réplicas de la simulación DES usando semillas consecutivas.
    Calcula estadísticas consolidadas con Intervalos de Confianza (I.C.) al 95%.
    """
    wq_replicas = []
    lq_replicas = []
    rho_replicas = []
    datos_ejemplo_grafica = None

    # Corremos las N jornadas de trabajo independientes
    for i in range(n_replicas):
        semilla = semilla_base + i
        wq, lq, rho, datos_detallados = correr_una_replica(
            semilla, tasa_llegada, tasa_servicio, num_tecnicos, tiempo_sim, tiempo_calentamiento
        )
        wq_replicas.append(wq)
        lq_replicas.append(lq)
        rho_replicas.append(rho)
        
        # Guardamos los datos detallados del primer día (índice 0) 
        # para poder dibujar la gráfica de evolución temporal más adelante
        if i == 0:
            datos_ejemplo_grafica = datos_detallados

    # Diccionario donde organizaremos el reporte estadístico final
    resultados = {}
    
    # Procesamos las tres métricas clave usando operaciones matemáticas estables de numpy
    for nombre, datos in [('Wq', wq_replicas), ('Lq', lq_replicas), ('rho', rho_replicas)]:
        media = np.mean(datos)
        # ddof=1 asegura que calcule la desviación estándar muestral (correcta para estadística)
        desv_est = np.std(datos, ddof=1) if len(datos) > 1 else 0.0
        
        # Error estándar de la media y margen de error para un 95% de confianza (Z = 1.96)
        error_estandar = desv_est / math.sqrt(n_replicas)
        margen_error = 1.96 * error_estandar
        
        resultados[nombre] = {
            'media': media,
            'desv': desv_est,
            'ic_inf': media - margen_error,
            'ic_sup': media + margen_error,
            'valores': datos  # Guardamos la lista completa para verificar normalidad (TCL)
        }
    
    # --- REQUERIMIENTO MÓDULO 3: Número mínimo de réplicas para error relativo <= 5% ---
    media_wq = resultados['Wq']['media']
    desv_wq = resultados['Wq']['desv']
    
    if media_wq > 0 and desv_wq > 0:
        # El error absoluto permitido es el 5% del valor de la media encontrada
        error_absoluto_deseado = 0.05 * media_wq
        # Fórmula estadística para tamaño de muestra: n = (Z*sigma / E)^2
        n_minimo = ((1.96 * desv_wq) / error_absoluto_deseado) ** 2
        resultados['N_minimo'] = math.ceil(n_minimo)
    else:
        resultados['N_minimo'] = n_replicas

    return resultados, datos_ejemplo_grafica