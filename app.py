import os
import sys
import math
import numpy as np
from flask import Flask, render_template_string, send_from_directory, request

app = Flask(__name__)

# Configuración de rutas seguras para almacenamiento en la nube (Render)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GRAFICAS_DIR = os.path.join(BASE_DIR, "static_graficas")

if not os.path.exists(GRAFICAS_DIR):
    os.makedirs(GRAFICAS_DIR)

# Capturador de logs clásicos de consola
class CapturaConsola:
    def __init__(self):
        self.texto = ""
    def write(self, string):
        self.texto += string
    def flush(self):
        pass

# Importamos las funciones, variables y listas base de tu simulación real
from main import main, LAMBDA_BASE, MU_BASE, C_BASE, T_SIM_HORAS, T_WARM_HORAS, N_REPLICAS, SEMILLA_BASE, lista_lambdas, lista_c
import montecarlo
import sensibilidad
from visualizacion import generar_graficas

# =========================================================================
# 🎨 DISEÑO DE DASHBOARD DE ALTO IMPACTO VISUAL
# =========================================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>TechClassUC - Panel Científico de Simulación</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background-color: #0b0f19; color: #f4f6f9; }
        .container { max-width: 1200px; margin: auto; }
        h1 { color: #00d2ff; font-size: 28px; font-weight: 700; border-bottom: 2px solid #1e293b; padding-bottom: 15px; margin-bottom: 5px; }
        .subtitle { color: #94a3b8; font-size: 14px; margin-bottom: 30px; }
        h2 { color: #ffffff; font-size: 20px; font-weight: 600; margin-top: 45px; margin-bottom: 20px; display: flex; align-items: center; }
        h2::before { content: "■"; color: #00f2fe; margin-right: 10px; font-size: 14px; }
        
        /* Panel de Parametrización Dinámica */
        .panel-control { background: #111827; border: 1px solid #1e293b; padding: 22px; border-radius: 12px; margin-bottom: 35px; box-shadow: 0 4px 15px rgba(0,0,0,0.4); }
        .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 15px; align-items: flex-end; }
        .form-group { display: flex; flex-direction: column; }
        .form-group label { font-size: 11px; color: #94a3b8; font-weight: 600; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.05em; }
        .form-group input { background: #1e293b; border: 1px solid #334155; color: #ffffff; padding: 10px; border-radius: 6px; font-size: 14px; font-family: monospace; }
        .form-group input:focus { border-color: #00d2ff; outline: none; }
        .btn-submit { background: linear-gradient(90deg, #00f2fe, #4facfe); border: none; color: #ffffff; font-weight: 700; font-size: 13px; padding: 11px; border-radius: 6px; cursor: pointer; transition: transform 0.2s; text-transform: uppercase; letter-spacing: 0.05em; }
        .btn-submit:hover { transform: scale(1.02); }
        
        /* Grid de KPIs principales */
        .grid-kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 35px; }
        .card-kpi { background: #1e293b; border: 1px solid #334155; padding: 22px 18px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
        .card-kpi h3 { margin: 0; color: #94a3b8; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
        .card-kpi .value { font-size: 30px; font-weight: 700; color: #00f2fe; margin: 10px 0 5px 0; }
        .card-kpi .unit { font-size: 15px; font-weight: 500; color: #00f2fe; }
        .card-kpi .ic-box { font-size: 11px; color: #38bdf8; background: rgba(56, 189, 248, 0.1); padding: 4px 8px; border-radius: 6px; display: inline-block; margin-top: 5px; font-family: monospace; }
        
        .progress-bar-bg { background: #334155; border-radius: 4px; height: 6px; width: 100%; margin-top: 15px; }
        .progress-bar-fill { background: linear-gradient(90deg, #00f2fe, #4facfe); height: 100%; border-radius: 4px; width: {{ (rho_sim * 100) | round(1) }}%; }

        /* Estilos de Tablas Científicas */
        .table-responsive { width: 100%; overflow-x: auto; margin-bottom: 40px; border-radius: 12px; border: 1px solid #334155; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
        table { width: 100%; border-collapse: collapse; text-align: left; background-color: #1e293b; }
        th { background-color: #0f172a; color: #38bdf8; padding: 14px 16px; font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 2px solid #334155; }
        td { padding: 14px 16px; border-bottom: 1px solid #334155; font-size: 14px; color: #e2e8f0; }
        tr:hover { background-color: #243249; }
        .badge-error { background-color: rgba(16, 185, 129, 0.15); color: #34d399; padding: 4px 8px; border-radius: 6px; font-weight: 600; font-family: monospace; }
        .badge-error.high { background-color: rgba(239, 68, 68, 0.15); color: #f87171; }
        .font-mono { font-family: 'Courier New', Courier, monospace; font-weight: bold; }

        /* Contenedor de Gráficas */
        .grid-graficas { display: grid; grid-template-columns: 1fr 1fr; gap: 25px; margin-top: 20px; margin-bottom: 50px; }
        .card-grafica { background: #1e293b; border: 1px solid #334155; padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
        .card-grafica h3 { margin-top: 0; margin-bottom: 15px; color: #ffffff; font-size: 15px; font-weight: 600; }
        .card-grafica img { max-width: 100%; height: auto; border-radius: 8px; border: 1px solid #334155; }
        .full-width { grid-column: span 2; }
        
        details { background: #111827; border: 1px solid #1e293b; padding: 15px; border-radius: 8px; margin-top: 30px; cursor: pointer; }
        details summary { font-weight: 600; color: #94a3b8; }
        pre { background: #000000; color: #a7f3d0; padding: 15px; border-radius: 6px; overflow-x: auto; font-size: 13px; font-family: monospace; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>TechClassUC: Panel de Simulación Avanzada</h1>
        <div class="subtitle"><strong>Cumplimiento de Requerimientos:</strong> Entorno Web para Validación de Modelos Estocásticos</div>
        
        <div class="panel-control">
            <form method="POST" action="/">
                <div class="form-grid">
                    <div class="form-group">
                        <label>Tasa de Llegada (λ)</label>
                        <input type="number" step="0.01" name="lambda_base" value="{{ lam_b }}" required>
                    </div>
                    <div class="form-group">
                        <label>Capacidad Servicio (μ)</label>
                        <input type="number" step="0.01" name="mu_base" value="{{ mu_b }}" required>
                    </div>
                    <div class="form-group">
                        <label>Nº Técnicos (c)</label>
                        <input type="number" min="1" name="c_base" value="{{ c_b }}" required>
                    </div>
                    <div class="form-group">
                        <label>Jornada Horas (T)</label>
                        <input type="number" min="1" name="t_sim" value="{{ t_sim }}" required>
                    </div>
                    <div class="form-group">
                        <label>Réplicas Montecarlo (N)</label>
                        <input type="number" min="2" name="n_replicas" value="{{ n_replicas }}" required>
                    </div>
                    <button type="submit" class="btn-submit">🚀 Ejecutar</button>
                </div>
            </form>
        </div>
        
        <h2>Métricas de Desempeño Global (Montecarlo)</h2>
        <div class="grid-kpis">
            <div class="card-kpi">
                <h3>Espera en Cola (Wq)</h3>
                <div class="value">{{ (wq_sim * 60) | round(2) }} <span class="unit">min</span></div>
                <div class="ic-box">IC: [{{ wq_ic_inf | round(2) }}, {{ wq_ic_sup | round(2) }}]</div>
            </div>
            <div class="card-kpi">
                <h3>Clientes en Fila (Lq)</h3>
                <div class="value">{{ lq_sim | round(2) }} <span class="unit">cli</span></div>
                <div class="ic-box">IC: [{{ lq_ic_inf | round(2) }}, {{ lq_ic_sup | round(2) }}]</div>
            </div>
            <div class="card-kpi">
                <h3>Utilización Promedio (ρ)</h3>
                <div class="value">{{ (rho_sim * 100) | round(1) }}<span class="unit">%</span></div>
                <div class="progress-bar-bg"><div class="progress-bar-fill"></div></div>
            </div>
            <div class="card-kpi">
                <h3>Muestreo Montecarlo</h3>
                <div class="value" style="font-size: 22px; color: #34d399; margin-top: 15px;">
                    N = {{ n_replicas }} <span style="font-size:12px; color:#94a3b8;">corridas</span>
                </div>
                <div class="ic-box" style="color:#a7f3d0; background:rgba(16,185,129,0.1);">N Mínimo Requerido: {{ n_min }}</div>
            </div>
        </div>

        <h2>Módulo 4: Tabla de Validación Analítica ($M/M/c$ vs Simulación)</h2>
        <div class="table-responsive">
            <table>
                <thead>
                    <tr>
                        <th>Métrica del Sistema (Parámetros Base)</th>
                        <th>Modelo Teórico ($M/M/c$)</th>
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
                        <td><strong>Clientes Promedio en Cola (Lq)</strong></td>
                        <td class="font-mono">{{ lq_teo | round(4) }}</td>
                        <td class="font-mono">{{ lq_sim | round(4) }}</td>
                        <td class="font-mono" style="color: #38bdf8;">[{{ lq_ic_inf | round(4) }}, {{ lq_ic_sup | round(4) }}]</td>
                        <td><span class="badge-error {% if err_lq > 5 %}high{% endif %}">{{ err_lq | round(2) }} %</span></td>
                    </tr>
                    <tr>
                        <td><strong>Clientes Totales en el Sistema (L)</strong></td>
                        <td class="font-mono">{{ l_teo | round(4) }}</td>
                        <td class="font-mono">{{ l_sim | round(4) }}</td>
                        <td class="font-mono" style="color: #38bdf8;">—</td>
                        <td><span class="badge-error {% if err_l > 5 %}high{% endif %}">{{ err_l | round(2) }} %</span></td>
                    </tr>
                    <tr>
                        <td><strong>Tiempo Promedio en Cola (Wq)</strong></td>
                        <td class="font-mono">{{ (wq_teo * 60) | round(2) }} min</td>
                        <td class="font-mono">{{ (wq_sim * 60) | round(2) }} min</td>
                        <td class="font-mono" style="color: #38bdf8;">[{{ wq_ic_inf | round(2) }}, {{ wq_ic_sup | round(2) }}] min</td>
                        <td><span class="badge-error {% if err_wq > 5 %}high{% endif %}">{{ err_wq | round(2) }} %</span></td>
                    </tr>
                    <tr>
                        <td><strong>Tiempo Total en el Sistema (W)</strong></td>
                        <td class="font-mono">{{ (w_teo * 60) | round(2) }} min</td>
                        <td class="font-mono">{{ (w_sim * 60) | round(2) }} min</td>
                        <td class="font-mono" style="color: #38bdf8;">—</td>
                        <td><span class="badge-error {% if err_w > 5 %}high{% endif %}">{{ err_w | round(2) }} %</span></td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <h2>Módulo 5 y 6: Tablero Estadístico y Gráficas del Sistema</h2>
        <div class="grid-graficas">
            <div class="card-grafica full-width">
                <h3>Mapa de Calor: Análisis de Sensibilidad (Wq Minutos según Escenarios)</h3>
                <img src="/graficas/grafica_5_heatmap_sensibilidad.png" alt="Heatmap">
            </div>
            <div class="card-grafica">
                <h3>Curva de Capacidad: Tiempo Wq vs Técnicos (c)</h3>
                <img src="/graficas/grafica_3_capacidad_wq.png" alt="Capacidad">
            </div>
            <div class="card-grafica">
                <h3>Factor de Utilización (ρ) vs Tasa de Llegada (λ)</h3>
                <img src="/graficas/grafica_4_utilizacion_rho.png" alt="Utilización">
            </div>
            <div class="card-grafica">
                <h3>Evolución Temporal Dinámica del Sistema (SimPy)</h3>
                <img src="/graficas/grafica_1_evolucion_temporal.png" alt="Evolución">
            </div>
            <div class="card-grafica">
                <h3>Verificación Teorema Central del Límite (Normalidad de Medias)</h3>
                <img src="/graficas/grafica_2_distribucion_wq.png" alt="TCL">
            </div>
        </div>

        <details>
            <summary>Ver Log Crudo de Consola (Auditoría Técnica del Sistema)</summary>
            <pre>{{ reporte }}</pre>
        </details>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def home():
    # 1. Ajustamos las variables por defecto usando los parámetros de main.py
    lambda_actual = LAMBDA_BASE
    mu_actual = MU_BASE
    c_actual = C_BASE
    t_sim_actual = T_SIM_HORAS
    n_replicas_actual = N_REPLICAS
    semilla_actual = SEMILLA_BASE
    t_warm_actual = T_WARM_HORAS

    # 2. Si hay un envío por el formulario, recolectamos los valores que ingresaste
    if request.method == 'POST':
        lambda_actual = float(request.form.get('lambda_base', LAMBDA_BASE))
        mu_actual = float(request.form.get('mu_base', MU_BASE))
        c_actual = int(request.form.get('c_base', C_BASE))
        t_sim_actual = int(request.form.get('t_sim', T_SIM_HORAS))
        n_replicas_actual = int(request.form.get('n_replicas', N_REPLICAS))

    # 3. Lanzamos el capturador clásico para tus logs dinámicos
    old_stdout = sys.stdout
    captura = CapturaConsola()
    sys.stdout = captura

    # Ejecutamos el núcleo de simulación con tus parámetros dinámicos
    resultados_mc, datos_ejemplo = montecarlo.correr_replicas(
        n_replicas_actual, semilla_actual, lambda_actual, mu_actual, c_actual, t_sim_actual, t_warm_actual
    )
    
    matriz_sensibilidad = sensibilidad.realizar_analisis_sensibilidad(
        n_replicas_actual, semilla_actual, lista_lambdas, lista_c, mu_actual, t_sim_actual, t_warm_actual
    )

    # Regeneramos las 5 gráficas en la ruta estática con los datos calculados
    generar_graficas(resultados_mc, datos_ejemplo, matriz_sensibilidad, lista_lambdas, lista_c, ruta_guardado=GRAFICAS_DIR)

    sys.stdout = old_stdout
    REPORTE_TEXTO = captura.texto

    # =========================================================================
    # 📊 PROCESAMIENTO ESTADÍSTICO AVANZADO CON PARÁMETROS DINÁMICOS
    # =========================================================================
    rho_sim = resultados_mc['rho']['media']
    lq_sim  = resultados_mc['Lq']['media']
    wq_sim  = resultados_mc['Wq']['media']  # En horas

    l_sim   = lq_sim + (lambda_actual / mu_actual)
    w_sim   = wq_sim + (1 / mu_actual)

    # Valores Teóricos Analíticos Exactos (Modelo M/M/c)
    rho_teo = lambda_actual / (c_actual * mu_actual)

    # Validación analítica matemática para evitar desbordamientos si rho >= 1
    if rho_teo < 1:
        suma_p0 = sum([(lambda_actual / mu_actual)**n / math.factorial(n) for n in range(c_actual)])
        suma_p0 += ((lambda_actual / mu_actual)**c_actual / (math.factorial(c_actual) * (1 - rho_teo)))
        p0_teo = 1 / suma_p0

        lq_teo = (p0_teo * ((lambda_actual / mu_actual)**c_actual) * rho_teo) / (math.factorial(c_actual) * ((1 - rho_teo)**2))
        wq_teo = lq_teo / lambda_actual
        l_teo  = lq_teo + (lambda_actual / mu_actual)
        w_teo  = wq_teo + (1 / mu_actual)
    else:
        # Valores de bandera en caso de saturación total del sistema
        p0_teo = 0.0
        lq_teo = wq_teo = l_teo = w_teo = 99.99

    # Errores Relativos Porcentuales (%)
    err_rho = abs(rho_teo - rho_sim) / rho_teo * 100 if rho_teo > 0 else 0
    err_lq  = abs(lq_teo - lq_sim) / lq_teo * 100 if lq_teo > 0 else 0
    err_wq  = abs(wq_teo - wq_sim) / wq_teo * 100 if wq_teo > 0 else 0
    err_l   = abs(l_teo - l_sim) / l_teo * 100 if l_teo > 0 else 0
    err_w   = abs(w_teo - w_sim) / w_teo * 100 if w_teo > 0 else 0

    # Intervalos de Confianza al 95% 
    wq_ic_inf, wq_ic_sup = resultados_mc['Wq']['ic_inf'] * 60, resultados_mc['Wq']['ic_sup'] * 60  # Minutos
    lq_ic_inf, lq_ic_sup = resultados_mc['Lq']['ic_inf'], resultados_mc['Lq']['ic_sup']
    rho_ic_inf, rho_ic_sup = resultados_mc['rho']['ic_inf'] * 100, resultados_mc['rho']['ic_sup'] * 100

    # Cálculo del Número Mínimo de Réplicas (Módulo 3 - Requerimiento 5.3)
    valores_wq = resultados_mc['Wq']['valores']
    media_wq = np.mean(valores_wq)
    desviacion_wq = np.std(valores_wq, ddof=1)
    if media_wq > 0:
        n_minimo_calculado = ((1.96 * desviacion_wq) / (0.05 * media_wq)) ** 2
        n_minimo_calculado = max(10, math.ceil(n_minimo_calculado))
    else:
        n_minimo_calculado = 30

    # 4. Renderizamos la plantilla HTML inyectando las nuevas variables dinámicas
    return render_template_string(
        HTML_TEMPLATE, 
        reporte=REPORTE_TEXTO,
        rho_sim=rho_sim, lq_sim=lq_sim, wq_sim=wq_sim, l_sim=l_sim, w_sim=w_sim,
        rho_teo=rho_teo, lq_teo=lq_teo, wq_teo=wq_teo, l_teo=l_teo, w_teo=w_teo,
        err_rho=err_rho, err_lq=err_lq, err_wq=err_wq, err_l=err_l, err_w=err_w,
        wq_ic_inf=wq_ic_inf, wq_ic_sup=wq_ic_sup,
        lq_ic_inf=lq_ic_inf, lq_ic_sup=lq_ic_sup,
        rho_ic_inf=rho_ic_inf, rho_ic_sup=rho_ic_sup,
        n_replicas=n_replicas_actual, lam_b=lambda_actual, mu_b=mu_actual, c_b=c_actual,
        t_sim=t_sim_actual, n_min=n_minimo_calculado
    )

@app.route('/graficas/<filename>')
def obtener_grafica(filename):
    return send_from_directory(GRAFICAS_DIR, filename)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
