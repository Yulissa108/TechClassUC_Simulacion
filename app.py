# app.py
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

# Aquí le pasamos explícitamente la ruta de guardado segura para la web
generar_graficas(resultados_mc, datos_ejemplo, matriz_sensibilidad, lista_lambdas, lista_c, ruta_guardado=GRAFICAS_DIR)

# --- EXTRACCIÓN DE DATOS PARA LAS TARJETAS DINÁMICAS ---
# Convertimos los valores a formatos amigables para las tarjetas ejecutivas
wq_simulado_minutos = resultados_mc['Wq']['media'] * 60
lq_simulado_clientes = resultados_mc['Lq']['media']
utilizacion_porcentaje = resultados_mc['rho']['media'] * 100

# El diseño visual de tu página web ejecutiva corregido con Tarjetas Modernas
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>TechClassUC - Panel de Simulación</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background-color: #0b0f19; color: #f4f6f9; }
        .container { max-width: 1000px; margin: auto; }
        h1 { color: #00d2ff; font-size: 28px; font-weight: 700; border-bottom: 2px solid #1e293b; padding-bottom: 15px; margin-bottom: 5px; }
        .subtitle { color: #94a3b8; font-size: 14px; margin-bottom: 30px; }
        h2 { color: #ffffff; font-size: 20px; font-weight: 600; margin-top: 40px; margin-bottom: 20px; }
        
        /* Contenedor de Tarjetas KPI */
        .grid-kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 40px; }
        .card-kpi { background: #1e293b; border: 1px solid #334155; padding: 25px 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); position: relative; overflow: hidden; }
        .card-kpi h3 { margin: 0; color: #94a3b8; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
        .card-kpi .value { font-size: 32px; font-weight: 700; color: #00f2fe; margin: 15px 0 5px 0; }
        .card-kpi .unit { font-size: 16px; font-weight: 500; color: #00f2fe; }
        .card-kpi .subtext { font-size: 12px; color: #64748b; }
        
        /* Barra de progreso de utilización */
        .progress-bar-bg { background: #334155; border-radius: 4px; height: 6px; width: 100%; margin-top: 15px; }
        .progress-bar-fill { background: #00f2fe; height: 100%; border-radius: 4px; width: {{ utilizacion | round(1) }}%; }

        /* Contenedor de Gráficas */
        .grid-graficas { display: grid; grid-template-columns: 1fr 1fr; gap: 25px; margin-top: 20px; }
        .card-grafica { background: #1e293b; border: 1px solid #334155; padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
        .card-grafica h3 { margin-top: 0; margin-bottom: 15px; color: #ffffff; font-size: 15px; font-weight: 600; }
        .card-grafica img { max-width: 100%; height: auto; border-radius: 8px; border: 1px solid #334155; }
        .full-width { grid-column: span 2; }
        
        /* Acordeón para el reporte completo por si el profesor quiere auditar los datos */
        details { background: #111827; border: 1px solid #1e293b; padding: 15px; border-radius: 8px; margin-top: 30px; cursor: pointer; }
        details summary { font-weight: 600; color: #94a3b8; }
        pre { background: #000000; color: #a7f3d0; padding: 15px; border-radius: 6px; overflow-x: auto; font-size: 13px; font-family: monospace; text-align: left; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>TechClassUC: Panel de Simulación en la Nube</h1>
        <div class="subtitle"><strong>Entorno de Despliegue de Infraestructura:</strong> Servidor Distribuido en Render</div>
        
        <h2>Métricas Clave – Montecarlo ({{ n_replicas }} Réplicas)</h2>
        <div class="grid-kpis">
            <div class="card-kpi">
                <h3>Wq Simulado</h3>
                <div class="value">{{ wq_min | round(2) }} <span class="unit">min</span></div>
                <div class="subtext">Tiempo de espera promedio en cola</div>
            </div>
            <div class="card-kpi">
                <h3>Lq Simulado</h3>
                <div class="value">{{ lq_cli | round(2) }} <span class="unit">clientes</span></div>
                <div class="subtext">Cantidad promedio en fila</div>
            </div>
            <div class="card-kpi">
                <h3>Utilización ρ</h3>
                <div class="value">{{ utilizacion | round(1) }}<span class="unit">%</span></div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill"></div>
                </div>
            </div>
            <div class="card-kpi">
                <h3>Parámetros Base</h3>
                <div class="value" style="font-size: 18px; color: #e2e8f0; margin-top: 25px;">
                    λ = {{ lam_b }} | μ = {{ mu_b }}<br>
                    <span style="font-size: 13px; color: #64748b;">c = {{ c_b }} técnicos — 480 min</span>
                </div>
            </div>
        </div>
        
        <h2>Tablero de Gráficas Estadísticas Exportadas</h2>
        <div class="grid-graficas">
            <div class="card-grafica full-width">
                <h3>Mapa de Calor: Análisis de Sensibilidad (Wq Minutos)</h3>
                <img src="/graficas/grafica_5_heatmap_sensibilidad.png" alt="Heatmap">
            </div>
            <div class="card-grafica">
                <h3>Curva de Capacidad (Wq vs c)</h3>
                <img src="/graficas/grafica_3_capacidad_wq.png" alt="Capacidad">
            </div>
            <div class="card-grafica">
                <h3>Utilización del Sistema (ρ vs λ)</h3>
                <img src="/graficas/grafica_4_utilizacion_rho.png" alt="Utilización">
            </div>
            <div class="card-grafica">
                <h3>Evolución Temporal de Clientes</h3>
                <img src="/graficas/grafica_1_evolucion_temporal.png" alt="Evolución">
            </div>
            <div class="card-grafica">
                <h3>Verificación del TCL (Wq)</h3>
                <img src="/graficas/grafica_2_distribucion_wq.png" alt="TCL">
            </div>
        </div>

        <details>
            <summary>Ver Reporte Técnico de Validación Analítica M/M/c (Consola)</summary>
            <pre>{{ reporte }}</pre>
        </details>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(
        HTML_TEMPLATE, 
        reporte=REPORTE_TEXTO,
        wq_min=wq_simulado_minutos,
        lq_cli=lq_simulado_clientes,
        utilizacion=utilizacion_porcentaje,
        n_replicas=N_REPLICAS,
        lam_b=LAMBDA_BASE,
        mu_b=MU_BASE,
        c_b=C_BASE
    )

@app.route('/graficas/<filename>')
def obtener_grafica(filename):
    return send_from_directory(GRAFICAS_DIR, filename)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
