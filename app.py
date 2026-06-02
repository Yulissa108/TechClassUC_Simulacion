import os
import sys
from flask import Flask, render_template_string, send_from_directory

app = Flask(__name__)

# Definimos una ruta absoluta segura para guardar las gráficas dentro del servidor
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GRAFICAS_DIR = os.path.join(BASE_DIR, "static_graficas")

if not os.path.exists(GRAFICAS_DIR):
    os.makedirs(GRAFICAS_DIR)

# Clase auxiliar para capturar lo que main.py escribe en la consola
class CapturaConsola:
    def __init__(self):
        self.texto = ""
    def write(self, string):
        self.texto += string
    def flush(self):
        pass

# Redirigimos la consola para guardar tu reporte en texto
old_stdout = sys.stdout
captura = CapturaConsola()
sys.stdout = captura

# Importamos y ejecutamos tu simulación real
from main import main, LAMBDA_BASE, MU_BASE, C_BASE, T_SIM_HORAS, T_WARM_HORAS, N_REPLICAS, SEMILLA_BASE, lista_lambdas, lista_c
main() 

sys.stdout = old_stdout
REPORTE_TEXTO = captura.texto

# Forzamos la regeneración de las imágenes dentro de la carpeta que la web conoce
import montecarlo
import sensibilidad
from visualizacion import generar_graficas

resultados_mc, datos_ejemplo = montecarlo.correr_replicas(N_REPLICAS, SEMILLA_BASE, LAMBDA_BASE, MU_BASE, C_BASE, T_SIM_HORAS, T_WARM_HORAS)
matriz_sensibilidad = sensibilidad.realizar_analisis_sensibilidad(N_REPLICAS, SEMILLA_BASE, lista_lambdas, lista_c, MU_BASE, T_SIM_HORAS, T_WARM_HORAS)
generar_graficas(resultados_mc, datos_ejemplo, matriz_sensibilidad, lista_lambdas, lista_c)
# El diseño visual de tu página web ejecutiva
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>TechClassUC - Panel de Simulación</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; margin: 40px; background-color: #f4f6f9; color: #333; }
        .container { max-width: 900px; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin: auto; }
        h1 { color: #0056b3; border-bottom: 2px solid #0056b3; padding-bottom: 10px; }
        pre { background: #282c34; color: #abb2bf; padding: 20px; border-radius: 6px; overflow-x: auto; font-size: 14px; line-height: 1.5; }
        .grid-graficas { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 30px; }
        .card { background: #fff; border: 1px solid #ddd; padding: 10px; border-radius: 6px; text-align: center; }
        .card img { max-width: 100%; height: auto; border-radius: 4px; border: 1px solid #eee; }
        .full-width { grid-column: span 2; }
    </style>
</head>
<body>
    <div class="container">
        <h1>TechClassUC: Panel de Simulación en la Nube</h1>
        <p><strong>Entorno de Despliegue:</strong> Servidor Web en Render</p>
        
        <h2>Reporte Consolidado del Sistema</h2>
        <pre>{{ reporte }}</pre>
        
        <h2>Tablero de Gráficas Estadísticas Exportadas</h2>
        <div class="grid-graficas">
            <div class="card full-width">
                <h3>Mapa de Calor: Análisis de Sensibilidad (Wq Minutos)</h3>
                <img src="/graficas/grafica_5_heatmap_sensibilidad.png" alt="Heatmap">
            </div>
            <div class="card">
                <h3>Curva de Capacidad (Wq vs c)</h3>
                <img src="/graficas/grafica_3_capacidad_wq.png" alt="Capacidad">
            </div>
            <div class="card">
                <h3>Utilización del Sistema (ρ vs λ)</h3>
                <img src="/graficas/grafica_4_utilizacion_rho.png" alt="Utilización">
            </div>
            <div class="card">
                <h3>Evolución Temporal de Clientes</h3>
                <img src="/graficas/grafica_1_evolucion_temporal.png" alt="Evolución">
            </div>
            <div class="card">
                <h3>Verificación del TCL (Wq)</h3>
                <img src="/graficas/grafica_2_distribucion_wq.png" alt="TCL">
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, reporte=REPORTE_TEXTO)

@app.route('/graficas/<filename>')
def obtener_grafica(filename):
    return send_from_directory(GRAFICAS_DIR, filename)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
