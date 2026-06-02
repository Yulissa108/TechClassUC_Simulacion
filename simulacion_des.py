# simulacion_des.py
"""
Módulo: simulacion_des.py
Contiene la lógica del motor de simulación de eventos discretos (DES) usando SimPy.
"""
import random
import simpy
from cliente import Cliente
from servidor import CentroSoporte

def proceso_cliente(env, cliente, centro, tasa_servicio, lista_metricas, tiempo_calentamiento):
    """
    Modela el ciclo de vida de un cliente: llega, pide técnico, espera en cola,
    es atendido durante un tiempo aleatorio y se va.
    """
    # El cliente solicita un técnico disponible
    with centro.tecnicos.request() as peticion:
        yield peticion  # Espera aquí si todos los técnicos están ocupados
        
        # En este punto, el técnico toma al cliente (Inicia atención)
        cliente.tiempo_inicio_atencion = env.now
        
        # El tiempo que tarda el técnico sigue una distribución Exponencial (mu)
        tiempo_servicio = random.expovariate(tasa_servicio)
        yield env.timeout(tiempo_servicio)  # Pasa el tiempo de atención
        
        # Termina la atención y el cliente se retira
        cliente.tiempo_fin_atencion = env.now
        centro.clientes_atendidos += 1
        
        # REQUERIMIENTO: Solo guardamos métricas si el cliente llegó DESPUÉS 
        # del período de calentamiento (para evitar el sesgo del estado vacío)
        if cliente.tiempo_llegada >= tiempo_calentamiento:
            lista_metricas.append({
                'wq': cliente.tiempo_espera_cola,
                'w': cliente.tiempo_sistema,
                'llegada': cliente.tiempo_llegada
            })

def generador_clientes(env, tasa_llegada, tasa_servicio, centro, lista_metricas, tiempo_calentamiento):
    """
    Genera clientes continuamente siguiendo un Proceso de Poisson (tiempos entre llegadas exponenciales).
    """
    id_cliente = 1
    while True:
        # El tiempo hasta que llega el próximo cliente es exponencial (lambda)
        tiempo_entre_llegadas = random.expovariate(tasa_llegada)
        yield env.timeout(tiempo_entre_llegadas)
        
        # Nace un nuevo cliente
        nuevo_cliente = Cliente(id_cliente, env.now)
        
        # Se activa su proceso en el entorno de SimPy de forma independiente
        env.process(proceso_cliente(env, nuevo_cliente, centro, tasa_servicio, lista_metricas, tiempo_calentamiento))
        id_cliente += 1

def correr_una_replica(semilla, tasa_llegada, tasa_servicio, num_tecnicos, tiempo_sim, tiempo_calentamiento):
    """
    Ejecuta una sola corrida (réplica) de la simulación con una semilla específica.
    Devuelve los promedios obtenidos en esta corrida.
    """
    # Fijamos la semilla para que esta réplica sea reproducible
    random.seed(semilla)
    
    # Creamos el entorno de SimPy y el recurso de los técnicos
    env = simpy.Environment()
    centro = CentroSoporte(env, num_tecnicos)
    
    # Lista interna para recolectar los datos de cada cliente
    lista_metricas = []
    
    # Activamos el generador de clientes en el entorno
    env.process(generador_clientes(env, tasa_llegada, tasa_servicio, centro, lista_metricas, tiempo_calentamiento))
    
    # Corre la simulación hasta el límite de tiempo de la jornada (8 horas)
    env.run(until=tiempo_sim)
    
    # Si por alguna razón no se registraron clientes estables, evitamos dividir por cero
    if not lista_metricas:
        return 0.0, 0.0, 0.0, []
    
    # --- CÁLCULO DE MÉTRICAS DE LA RÉPLICA ---
    # Promedio de tiempos de espera (Wq) y en el sistema (W)
    wq_promedio = sum(m['wq'] for m in lista_metricas) / len(lista_metricas)
    w_promedio = sum(m['w'] for m in lista_metricas) / len(lista_metricas)
    
    # Tiempo útil de análisis (restando el calentamiento)
    tiempo_monitoreado = tiempo_sim - tiempo_calentamiento
    
    # Usamos la Ley de Little para estimar el número promedio de clientes en cola (Lq) y en sistema (L)
    lq_promedio = sum(m['wq'] for m in lista_metricas) / tiempo_monitoreado
    l_promedio = sum(m['w'] for m in lista_metricas) / tiempo_monitoreado
    
    # Factor de utilización estimado (rho) de los técnicos en esta réplica
    rho_estimado = (l_promedio - lq_promedio) / num_tecnicos
    # Forzar que el valor quede en un rango lógico [0, 1] por fluctuaciones de la simulación
    rho_estimado = min(max(rho_estimado, 0.0), 1.0)
    
    return wq_promedio, lq_promedio, rho_estimado, lista_metricas