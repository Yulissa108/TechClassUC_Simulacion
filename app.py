# app.py
import os
import sys
import math
import numpy as np
from flask import Flask, render_template_string, send_from_directory

# Inicialización de la App con la sintaxis corregida dunder
app = Flask(__name__)

# Configuración de rutas estáticas para Render
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GRAFICAS_DIR = os.path.join(BASE_DIR, "static_graficas")

if not os.path.exists(GRAFICAS_DIR):
    os.makedirs(GRAFICAS_DIR)

# Capturador de logs de consola
class CapturaConsola:
    def __init__(self):
        self.texto = ""
    def write(self, string):
        self.texto += string
    def flush(self):
        pass

old_stdout = sys.stdout
captura = CapturaConsola()
sys.stdout = captura

# Ejecución del núcleo de la simulación
from main import main, LAMBDA_BASE, MU_BASE, C_BASE, T_SIM_HORAS, T_WARM_HORAS, N_REPLICAS, SEMILLA_BASE, lista_lambdas, lista_c
main() 

sys.stdout = old_stdout
REPORTE_TEXTO = captura.texto

# Importación de módulos del proyecto
import montecarlo
import sensibilidad
from visualizacion import generar_graficas

# Obtención de datos reales de simulación
resultados_mc, datos_ejemplo = montecarlo.correr_replicas(N_REPLICAS, SEMILLA_BASE, LAMBDA_BASE, MU_BASE, C_BASE, T_SIM_HORAS, T_WARM_HORAS)
matriz_sensibilidad = sensibilidad.realizar_analisis_sensibilidad(N_REPLICAS, SEMILLA_BASE, lista_lambdas, lista_c, MU_BASE, T_SIM_HORAS, T_WARM_HORAS)

# Renderizado de gráficas en el directorio estático
generar_graficas(resultados_mc, datos_ejemplo, matriz_sensibilidad, lista_lambdas, lista_c, ruta_guardado=GRAFICAS_DIR)

# =========================================================================
# 📊 PROCESAMIENTO ESTADÍSTICO DINÁMICO
# =========================================================================

# 1. Medias Directas de la Simulación (Montecarlo)
rho_sim = resultados_mc['rho']['media']
lq_sim  = resultados_mc['Lq']['media']
wq_sim  = resultados_mc['Wq']['media']  # Horas

l_sim   = lq_sim + (LAMBDA_BASE / MU_BASE)
w_sim   = wq_sim + (1 / MU_BASE)

# 2. Valores Analíticos Teóricos (M/M/c)
rho_teo = LAMBDA_BASE / (C_BASE * MU_BASE)

suma_p0 = sum([(LAMBDA_BASE / MU_BASE)**n / math.factorial(n) for n in range(C_BASE)])
suma_p0 += ((LAMBDA_BASE / MU_BASE)**C_BASE / (math.factorial(C_BASE) * (1 - rho_teo)))
p0_teo = 1 / suma_p0

lq_teo = (p0_teo * ((LAMBDA_BASE / MU_BASE)**C_BASE) * rho_teo) / (math.factorial(C_BASE) * ((1 - rho_teo)**2))
wq_teo = lq_teo / LAMBDA_BASE
l_teo  = lq_teo + (LAMBDA_BASE / MU_BASE)
w_teo  = wq_teo + (1 / MU_BASE)

# 3. Errores Relativos Porcentuales
err_rho = abs(rho_teo - rho_sim) / rho_teo * 100
err_lq  = abs(lq_teo - lq_sim) / lq_teo * 100 if lq_teo > 0 else 0
err_wq  = abs(wq_teo - wq_sim) / wq_teo * 100 if wq_teo > 0 else 0
err_l   = abs(l_teo - l_sim) / l_teo * 100 if l_teo > 0 else 0
err_w   = abs(w_teo - w_sim) / w_teo * 100 if w_teo > 0 else 0

# 4. Intervalos de Confianza (Pasados a minutos y porcentajes según corresponda)
wq_ic_inf, wq_ic_sup = resultados_mc['Wq']['ic_inf'] * 60, resultados_mc['Wq']['ic_sup'] * 60
lq_ic_inf, lq_ic_sup = resultados_mc['Lq']['ic_inf'], resultados_mc['Lq']['ic_sup']
rho_ic_inf, rho_ic_sup = resultados_mc['rho']['ic_inf'] * 100, resultados_mc['rho']['ic_sup'] * 100

# 5. Estabilización de Réplicas (Mínimo requerido)
valores_wq = resultados_mc['Wq']['valores']
media_wq = np.mean(valores_wq)
desviacion_wq = np.std(valores_wq, ddof=1)
if media_wq > 0:
    n_minimo_calculado = ((1.96 * desviacion_wq) / (0.05 * media_wq)) ** 2
    n_minimo_calculado = max(10, math.ceil(n_minimo_calculado))
else:
    n_minimo_calculado = 30

# =========================================================================
# 🎨 VARIABLE HTML TOTALMENTE ENLAZADA CON JINJA2
# =========================================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>TechClassUC - Panel de Simulación</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; margin: 40px; background-color: #0b0f19; color: #f4f6f9; }
        .container { max-width: 1200px; margin: auto; }
        h1 { color: #00d2ff; font-size: 26px; border-bottom: 2px solid #1e293b; padding-bottom: 12px; }
        h2 { color: #ffffff; font-size: 18px; margin-top: 40px; }
        
        .grid-kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card-kpi { background: #1e293b; border: 1px solid #334155; padding: 20px; border-radius: 12px; }
        .card-kpi h3 { margin: 0; color: #94a3b8; font-size: 11px; text-transform: uppercase; }
        .card-kpi .value { font-size: 28px; font-weight: 700; color: #00f2fe; margin: 8px 0; }
        .card-kpi .ic-box { font-size: 11px; color: #38bdf8; background: rgba(56, 189, 248, 0.1); padding: 4px 8px; border-radius: 6px; font-family: monospace; }
        
        .table-responsive { width: 100%; overflow-x: auto; margin-bottom: 40px; border-radius: 12px; border: 1px solid #334155; }
        table { width: 100%; border-collapse: collapse; background-color: #1e293b; }
        th { background-color: #0f172a; color: #38bdf8; padding: 12px 14px; font-size: 12px; text-transform: uppercase; border-bottom: 2px solid #334155; }
        td { padding: 12px 14px; border-bottom: 1px solid #334155; font-size: 14px; }
        .badge-error { background-color: rgba(16, 185, 129, 0.15); color: #34d399; padding: 4px 8px; border-radius: 6px; font-family: monospace; font-weight: bold; }
        .badge-error.high { background-color: rgba(239, 68, 68, 0.15); color: #f87171; }
        .font-mono { font-family: monospace; font-weight: bold; }

        .grid-graficas { display: grid; grid-template-columns: 1fr 1fr; gap: 25px; }
        .card-grafica { background: #1e293b; border: 1px solid #334155; padding: 15px; border-radius: 12px; text-align: center; }
        .card-grafica img { max-width: 100%; height: auto; border-radius: 8px; }
        .full-width { grid-column: span 2; }
    </style>
</head>
<body>
    <div class="container">
        <h1>TechClassUC: Panel de Simulación Avanzada</h1>
        <p style="color: #94a3b8;">Entorno Web para Validación de Modelos Estocásticos</p>
        
        <h2>Métricas de Desempeño Global (Montecarlo)</h2>
        <div class="grid-kpis">
            <div class="card-kpi">
                <h3>Espera en Cola (Wq)</h3>
                <div class="value">{{ (wq_sim * 60) | round(2) }} min</div>
                <div class="ic-box">IC: [{{ wq_ic_inf | round(2) }}, {{ wq_ic_sup | round(2) }}]</div>
            </div>
            <div class="card-kpi">
                <h3>Clientes en Fila (Lq)</h3>
                <div class="value">{{ lq_sim | round(2) }} cli</div>
                <div class="ic-box">IC: [{{ lq_ic_inf | round(2) }}, {{ lq_ic_sup | round(2) }}]</div>
            </div>
            <div class="card-kpi">
                <h3>Utilización Promedio (&rho;)</h3>
                <div class="value">{{ (rho_sim * 100) | round(1) }}%</div>
                <div class="ic-box">IC: [{{ rho_ic_inf | round(1) }}%, {{ rho_ic_sup | round(1) }}%]</div>
            </div>
            <div class="card-kpi">
                <h3>Muestreo Corridas</h3>
                <div class="value" style="color: #34d399;">N = {{ n_replicas }}</div>
                <div class="ic-box" style="color: #a7f3d0;">N Mínimo Requerido: {{ n_min }}</div>
            </div>
        </div>

        <h2>Módulo 4: Tabla de Validación Analítica (M/M/c vs Simulación)</h2>
        <div class="table-responsive">
            <table>
                <thead>
                    <tr>
                        <th>Métrica del Sistema</th>
                        <th>Modelo Teórico (M/M/c)</th>
                        <th>Simulación (Media)</th>
                        <th>Intervalo de Confianza (95%)</th>
                        <th>Error Relativo %</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>Factor de Utilización (&rho;)</strong></td>
                        <td class="font-mono">{{ rho_teo | round(4) }}</td>
                        <td class="font-mono">{{ rho_sim | round(4) }}</td>
                        <td class="font-mono" style="color: #38bdf8;">[{{ (rho_ic_inf/100) | round(4) }}, {{ (rho_ic_sup/100) | round(4) }}]</td>
                        <td><span class="badge-error {% if err_rho > 5 %}high{% endif %}">{{ err_rho | round(2) }} %</span></td>
                    </tr>
                    <tr>
                        <td><strong>Clientes en Cola (Lq)</strong></td>
                        <td class="font-mono">{{ lq_teo | round(4) }}</td>
                        <td class="font-mono">{{ lq_sim | round(4) }}</td>
                        <td class="font-mono" style="color: #38bdf8;">[{{ lq_ic_inf | round(4) }}, {{ lq_ic_sup | round(4) }}]</td>
                        <td><span class="badge-error {% if err_lq > 5 %}high{% endif %}">{{ err_lq | round(2) }} %</span></td>
                    </tr>
                    <tr>
                        <td><strong>Clientes en el Sistema (L)</strong></td>
                        <td class="font-mono">{{ l_teo | round(4) }}</td>
                        <td class="font-mono">{{ l_sim | round(4) }}</td>
                        <td class="font-mono" style="color: #38bdf8;">—</td>
                        <td><span class="badge-error {% if err_l > 5 %}high{% endif %}">{{ err_l | round(2) }} %</span></td>
                    </tr>
                    <tr>
                        <td><strong>Tiempo en Cola (Wq)</strong></td>
                        <td class="font-mono">{{ (wq_teo * 60) | round(2) }} min</td>
                        <td class="font-mono">{{ (wq_sim * 60) | round(2) }} min</td>
                        <td class="font-mono" style="color: #38bdf8;">[{{ wq_ic_inf | round(2) }}, {{ wq_ic_sup | round(2) }}] min</td>
                        <td><span class="badge-error {% if err_wq > 5 %}high{% endif %}">{{ err_wq | round(2) }} %</span></td>
                    </tr>
                    <tr>
                        <td><strong>Tiempo en el Sistema (W)</strong></td>
                        <td class="font-mono">{{ (w_teo * 60) | round(2) }} min</td>
                        <td class="font-mono">{{ (w_sim * 60) | round(2) }} min</td>
                        <td class="font-mono" style="color: #38bdf8;">—</td>
                        <td><span class="badge-error {% if err_w > 5 %}high{% endif %}">{{ err_w | round(2) }} %</span></td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <h2>Módulo 5 y 6: Tablero de Gráficas Estadísticas</h2>
        <div class="grid-graficas">
            <div class="card-grafica full-width">
                <h3>Análisis de Sensibilidad: Mapa de Calor (Wq Minutos)</h3>
                <img src="/graficas/grafica_5_heatmap_sensibilidad.png" alt="Heatmap">
            </div>
            <div class="card-grafica">
                <h3>Curva de Capacidad: Wq vs Técnicos (c)</h3>
                <img src="/graficas/grafica_3_capacidad_wq.png" alt="Capacidad">
            </div>
            <div class="card-grafica">
                <h3>Factor de Utilización (&rho;) vs Tasa de Llegada (&lambda;)</h3>
                <img src="/graficas/grafica_4_utilizacion_rho.png" alt="Utilización">
            </div>
            <div class="card-grafica">
                <h3>Evolución Temporal (SimPy)</h3>
                <img src="/graficas/grafica_1_evolucion_temporal.png" alt="Evolución">
            </div>
            <div class="card-grafica">
                <h3>Verificación Teorema Central del Límite</h3>
                <img src="/graficas/grafica_2_distribucion_wq.png" alt="TCL">
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(
        HTML_TEMPLATE, 
        rho_sim=rho_sim, lq_sim=lq_sim, wq_sim=wq_sim, l_sim=l_sim, w_sim=w_sim,
        rho_teo=rho_teo, lq_teo=lq_teo, wq_teo=wq_teo, l_teo=l_teo, w_teo=w_teo,
        err_rho=err_rho, err_lq=err_lq, err_wq=err_wq, err_l=err_l, err_w=err_w,
        wq_ic_inf=wq_ic_inf, wq_ic_sup=wq_ic_sup,
        lq_ic_inf=lq_ic_inf, lq_ic_sup=lq_ic_sup,
        rho_ic_inf=rho_ic_inf, rho_ic_sup=rho_ic_sup,
        n_replicas=N_REPLICAS, n_min=n_minimo_calculado
    )

@app.route('/graficas/<filename>')
def obtener_grafica(filename):
    return send_from_directory(GRAFICAS_DIR, filename)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
