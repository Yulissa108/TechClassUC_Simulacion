# cliente.py
"""
Módulo: cliente.py
Define la clase Cliente y sus marcas de tiempo para calcular los tiempos de espera.
"""

class Cliente:
    def __init__(self, id_cliente, tiempo_llegada):
        """
        Inicializa un cliente con su identificador y el momento exacto en que llega.
        """
        self.id = id_cliente
        self.tiempo_llegada = tiempo_llegada
        self.tiempo_inicio_atencion = None
        self.tiempo_fin_atencion = None

    @property
    def tiempo_espera_cola(self):
        """Calcula Wq: El tiempo que pasó el cliente haciendo fila."""
        if self.tiempo_inicio_atencion is not None:
            return self.tiempo_inicio_atencion - self.tiempo_llegada
        return 0.0

    @property
    def tiempo_sistema(self):
        """Calcula W: El tiempo total (fila + atención del técnico)."""
        if self.tiempo_fin_atencion is not None:
            return self.tiempo_fin_atencion - self.tiempo_llegada
        return 0.0