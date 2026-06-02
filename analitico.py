# analitico.py
"""
Módulo: analitico.py
Calcula la solución analítica exacta mediante fórmulas de Teoría de Colas (M/M/c)
y realiza la comparación porcentual contra los datos simulados.
"""
import math

def calcular_mmc(tasa_llegada, tasa_servicio, num_tecnicos):
    """
    Calcula las métricas teóricas exactas para un sistema M/M/c en estado estacionario.
    """
    lam = tasa_llegada
    mu = tasa_servicio
    c = num_tecnicos
    
    # Factor de utilización teórico (rho)
    rho = lam / (c * mu)
    
    # Si el sistema es inestable, no se pueden calcular las fórmulas estables
    if rho >= 1.0:
        return {
            'rho': rho, 'P0': None, 'Lq': None, 'Wq': None, 'L': None, 'W': None
        }
    
    # 1. Calcular P0 (Probabilidad de que el sistema esté completamente vacío)
    suma_p0 = sum([(lam / mu) ** n / math.factorial(n) for n in range(c)])
    termino_c = ((lam / mu) ** c) / (math.factorial(c) * (1 - rho))
    p0 = 1.0 / (suma_p0 + termino_c)
    
    # 2. Calcular Lq (Número promedio de clientes esperando en la cola)
    numerador_lq = (p0 * ((lam / mu) ** c) * rho)
    denominador_lq = (math.factorial(c) * ((1 - rho) ** 2))
    lq = numerador_lq / denominador_lq
    
    # 3. Calcular las demás métricas usando la Ley de Little
    wq = lq / lam                # Tiempo promedio en cola
    w = wq + (1.0 / mu)          # Tiempo promedio total en el sistema
    l = lam * w                  # Número promedio de clientes en el sistema
    
    return {
        'rho': rho,
        'P0': p0,
        'Lq': lq,
        'Wq': wq,
        'L': l,
        'W': w
    }

def comparar_con_simulacion(teorico, simulado):
    """
    Compara los valores de la teoría frente a los promedios de la simulación
    calculando el Error Relativo Porcentual.
    """
    comparativa = {}
    # Evaluamos las 3 métricas críticas del sistema
    metricas = ['rho', 'Lq', 'Wq']
    
    for m in metricas:
        v_teorico = teorico[m]
        v_simulado = simulado[m]['media']
        
        # Fórmula de error relativo: |Teórico - Simulado| / Teórico * 100
        if v_teorico is not None and v_teorico > 0:
            err_rel = (abs(v_teorico - v_simulado) / v_teorico) * 100
        else:
            err_rel = 0.0
            
        comparativa[m] = {
            'Teórico': v_teorico,
            'Simulado': v_simulado,
            'Error_Rel_%': err_rel
        }
        
    return comparativa