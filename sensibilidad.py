# sensibilidad.py
"""
Módulo: sensibilidad.py
Ejecuta simulaciones iterativas variando sistemáticamente el número de técnicos (c)
y la tasa de llegada de clientes (lambda) para el análisis de toma de decisiones.
"""
from montecarlo import correr_replicas

def realizar_analisis_sensibilidad(n_replicas, semilla_base, lista_lambdas, lista_c, tasa_servicio, tiempo_sim, tiempo_calentamiento):
    """
    Realiza un barrido bidimensional de parámetros (c vs lambda).
    Detecta automáticamente si una configuración es inestable antes de simularla.
    """
    matriz_resultados = {}
    
    for c in lista_c:
        matriz_resultados[c] = {}
        for lam in lista_lambdas:
            # --- VALIDACIÓN DE ESTABILIDAD ---
            # Si rho = lambda / (c * mu) >= 1, la cola crece al infinito.
            # No tiene sentido simular un sistema que colapsará.
            if lam / (c * tasa_servicio) >= 1.0:
                matriz_resultados[c][lam] = {
                    'Wq': None, 
                    'Lq': None, 
                    'rho': 1.0, 
                    'estable': False
                }
                continue
            
            # Si el escenario es estable, ejecutamos el bloque de Montecarlo
            resultados, _ = correr_replicas(
                n_replicas, semilla_base, lam, tasa_servicio, c, tiempo_sim, tiempo_calentamiento
            )
            
            # Guardamos las medias de las métricas clave encontradas
            matriz_resultados[c][lam] = {
                'Wq': resultados['Wq']['media'],
                'Lq': resultados['Lq']['media'],
                'rho': resultados['rho']['media'],
                'estable': True
            }
            
    return matriz_resultados