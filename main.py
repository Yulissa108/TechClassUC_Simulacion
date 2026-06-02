# main.py
"""
Módulo Principal: main.py
Punto de entrada oficial que coordina, ejecuta y despliega los resultados
de la simulación de colas para TechClassUC de forma local y en la nube.
"""
import sys
from analitico import calcular_mmc, comparar_con_simulacion
from montecarlo import correr_replicas
from sensibilidad import realizar_analisis_sensibilidad
from visualizacion import generar_graficas

# =========================================================================
# PARÁMETROS GLOBALES DEL PROYECTO (Accesibles para el Servidor Web)
# =========================================================================
LAMBDA_BASE = 10.0          # Tasa de llegada: 10 clientes por hora
MU_BASE = 4.0               # Tasa de servicio: 4 clientes por hora por técnico
C_BASE = 3                  # Cantidad inicial: 3 técnicos operativos

T_SIM_MINUTOS = 480.0       # Jornada completa de 8 horas (en minutos)
T_WARM_MINUTOS = 60.0       # Período de calentamiento de 1 hora (en minutos)

# Pasamos los tiempos a horas para sincronizarlos con las tasas por hora
T_SIM_HORAS = T_SIM_MINUTOS / 60.0
T_WARM_HORAS = T_WARM_MINUTOS / 60.0

N_REPLICAS = 30             # Cantidad de jornadas para el Montecarlo
SEMILLA_BASE = 42           # Semilla inicial para reproducibilidad

# Escenarios para el Análisis de Sensibilidad Operativa
lista_lambdas = [8.0, 10.0, 12.0] 
lista_c = [2, 3, 4, 5]             # Opciones de asignación de técnicos


def main():
    print("=" * 65)
    print("      SISTEMA DE SIMULACIÓN COMPUTACIONAL - TECHCLASSUC")
    print("=" * 65)

    # -------------------------------------------------------------------------
    # 2. VALIDACIÓN DE ESTABILIDAD DEL SISTEMA BASE
    # -------------------------------------------------------------------------
    rho_teorico = LAMBDA_BASE / (C_BASE * MU_BASE)
    print(f"[CONFIG] Iniciando con: λ={LAMBDA_BASE}/h, μ={MU_BASE}/h, c={C_BASE} técnicos.")
    print(f"[CONFIG] Factor de Utilización Teórico Inicial: ρ = {rho_teorico:.4f}")
    
    if rho_teorico >= 1.0:
        print(f"\n[ERROR CRÍTICO] El sistema base configurado es INESTABLE (ρ = {rho_teorico:.2f} >= 1).")
        print("La cola crecerá de forma infinita. Simulación abortada por seguridad.")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # 3. EJECUCIÓN DE RÉPLICAS DE MONTECARLO
    # -------------------------------------------------------------------------
    print("\n>>> Procesando las 30 réplicas independientes de Montecarlo...")
    resultados_mc, datos_ejemplo = correr_replicas(
        n_replicas=N_REPLICAS,
        semilla_base=SEMILLA_BASE,
        tasa_llegada=LAMBDA_BASE,
        tasa_servicio=MU_BASE,
        num_tecnicos=C_BASE,
        tiempo_sim=T_SIM_HORAS,
        tiempo_calentamiento=T_WARM_HORAS
    )

    # -------------------------------------------------------------------------
    # 4. VALIDACIÓN MATEMÁTICA ANALÍTICA (M/M/c)
    # -------------------------------------------------------------------------
    print(">>> Calculando métricas exactas mediante Teoría de Colas...")
    resultados_analiticos = calcular_mmc(LAMBDA_BASE, MU_BASE, C_BASE)
    tabla_comparativa = comparar_con_simulacion(resultados_analiticos, resultados_mc)

    # --- IMPRESIÓN DE LA TABLA DE VALIDACIÓN ---
    print("\n" + "="*55)
    print(f"       TABLA COMPARATIVA: VALIDACIÓN ANALÍTICA M/M/c ")
    print("="*55)
    print(f"{'Métrica':<10} | {'Teórico':<10} | {'Simulado (Media)':<16} | {'Error Rel %':<12}")
    print("-"*55)
    for metrica, datos in tabla_comparativa.items():
        print(f"{metrica:<10} | {datos['Teórico']:<10.4f} | {datos['Simulado']:<16.4f} | {datos['Error_Rel_%']:<12.2f}%")
    print("="*55)

    # --- IMPRESIÓN DE INTERVALOS DE CONFIANZA ---
    print("\n" + "="*55)
    print("     INTERVALOS DE CONFIANZA AL 95% (MONTECARLO) ")
    print("="*55)
    for m in ['Wq', 'Lq', 'rho']:
        # Convertimos los tiempos (Wq) a minutos para que los entienda la dirección
        media_pantalla = resultados_mc[m]['media'] * 60 if m == 'Wq' else resultados_mc[m]['media']
        inf_pantalla = resultados_mc[m]['ic_inf'] * 60 if m == 'Wq' else resultados_mc[m]['ic_inf']
        sup_pantalla = resultados_mc[m]['ic_sup'] * 60 if m == 'Wq' else resultados_mc[m]['ic_sup']
        unidad = "minutos" if m == 'Wq' else "clientes" if m == 'Lq' else "de capacidad"
        
        print(f"{m:<5}: Media = {media_pantalla:.3f} {unidad}")
        print(f"       I.C. 95% = [{inf_pantalla:.3f} , {sup_pantalla:.3f}] {unidad}\n")
    print(f"Número mínimo de réplicas calculado para error < 5%: {resultados_mc['N_minimo']}")
    print("="*55)

    # -------------------------------------------------------------------------
    # 5. ANÁLISIS DE SENSIBILIDAD OPERATIVA
    # -------------------------------------------------------------------------
    print("\n>>> Ejecutando análisis de sensibilidad variable...")
    matriz_sensibilidad = realizar_analisis_sensibilidad(
        N_REPLICAS, SEMILLA_BASE, lista_lambdas, lista_c, MU_BASE, T_SIM_HORAS, T_WARM_HORAS
    )

    # -------------------------------------------------------------------------
    # 6. EXPORTACIÓN DE GRÁFICAS ESTADÍSTICAS
    # -------------------------------------------------------------------------
    print(">>> Diseñando e imprimiendo el tablero de gráficas...")
    # Agregamos la ruta local por defecto para evitar problemas en ejecuciones directas
    generar_graficas(resultados_mc, datos_ejemplo, matriz_sensibilidad, lista_lambdas, lista_c)
    # -------------------------------------------------------------------------
    # 7. CONCLUSIONES DE NEGOCIO (PREGUNTAS DIRECTIVAS)
    # -------------------------------------------------------------------------
    print("\n" + "="*65)
    print("             CONCLUSIONES FINALES PARA LA DIRECCIÓN")
    print("="*65)
    
    # Evaluar cuántos técnicos hacen que Wq < 10 minutos
    c_optimo = C_BASE
    for c in lista_c:
        if matriz_sensibilidad[c][10.0]['estable']:
            wq_m = matriz_sensibilidad[c][10.0]['Wq'] * 60
            if wq_m <= 10.0:
                c_optimo = c
                break
                
    wq_inicial_minutos = resultados_mc['Wq']['media'] * 60
    print(f"1. ¿Cuántos técnicos se necesitan para no superar los 10 min de espera?")
    print(f"   RESPUESTA: Se requieren exactamente {c_optimo} técnicos.")
    print(f"   (Con los {C_BASE} técnicos actuales la espera real es de {wq_inicial_minutos:.2f} minutos, incumpliendo la meta).")
    
    print(f"\n2. ¿Cómo varía la utilización si la tasa de llegada sube un 20% (λ = 12)?")
    if matriz_sensibilidad[3][12.0]['estable']:
        rho_alta = matriz_sensibilidad[3][12.0]['rho'] * 100
        print(f"   RESPUESTA: La utilización subiría críticamente al {rho_alta:.1f}%.")
    else:
        print(f"   RESPUESTA CRÍTICA: Si la demanda sube un 20%, mantener 3 técnicos colapsará")
        print(f"   el sistema por completo (ρ >= 100%). La cola tenderá al infinito.")
        
    print(f"\n3. ¿Qué ocurre con la cola en escenarios de alta demanda?")
    print(f"   RESPUESTA: Debido a la naturaleza estocástica del negocio, pequeños aumentos")
    print(f"   en la demanda causan un crecimiento exponencial en la fila. Con λ = 12,")
    print(f"   es mandatorio programar al menos c = 4 técnicos para estabilizar la operación.")
    print("="*65)


if __name__ == "__main__":
    main()