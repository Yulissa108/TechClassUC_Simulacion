# servidor.py
"""
Módulo: servidor.py
Define el recurso compartido de los técnicos usando SimPy.
"""
import simpy

class CentroSoporte:
    def __init__(self, env, num_tecnicos):
        """
        Inicializa el centro de soporte con una cantidad 'c' de técnicos disponibles.
        """
        self.env = env
        # simpy.Resource modela los servidores en paralelo que atienden la cola
        self.tecnicos = simpy.Resource(env, capacity=num_tecnicos)
        self.clientes_atendidos = 0