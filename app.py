# app.py
import os
import sys
import math
import numpy as np
from flask import Flask, render_template_string, send_from_directory, request

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GRAFICAS_DIR = os.path.join(BASE_DIR, "static_graficas")

if not os.path.exists(GRAFICAS_DIR):
    os.makedirs(GRAFICAS_DIR)

# Importamos los módulos del proyecto
import main
import montecarlo
import sensibilidad
from visualizacion import generar_graficas

# =========================================================================
# 🎨 DISEÑO DE DASHBOARD INTERACTIVO (FORMULARIO + RESULTADOS)
# =========================================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>TechClassUC - Simulador Dinámico de Colas</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; margin: 40px; background-color: #0b0f19; color: #f4f6f9; }
        .container { max-width: 1200px; margin: auto; }
        h1 { color: #00d2ff; font-size: 26px; border-bottom: 2px solid #1e293b; padding-bottom: 12px; margin-bottom: 25px; }
        h2 { color: #ffffff; font-size: 18px; margin-top: 40px; border-left: 4px solid #00f2fe; padding-left: 10px; }
        p { color: #94a3b8; }
        
        /* Alertas de error de saturación */
        .alert-danger { background-color: rgba(239, 68, 68, 0.2); border: 1px solid #f87171; color: #f87171; padding: 15px; border-radius: 8px; margin-bottom: 20px; font-weight: bold; }
        
        /* Estilos del Formulario Superior */
        .form-container { background: #151f32; border: 1px solid #1e293b; padding: 25px; border-radius: 12px; margin-bottom: 35px; box-shadow: 0 4px 20px rgba(0,0,0,0.4); }
        .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .form-group { display: flex; flex-direction: column; }
        .form-group label { font-size: 12px; color: #38bdf8; text-transform: uppercase; margin-bottom: 6px; font-weight: 600; }
        .form-group input { background: #0f172a; border: 1px solid #334155; padding: 10px; border-radius: 6px; color: #ffffff; font-size: 15px; font-weight: bold; }
        .form-group input:focus { border-color: #00f2fe; outline: none; }
        .btn-simular { background: linear-gradient(90deg, #00f2fe, #4facfe); border: none; color: #0b0f19; font-size: 16px; font-weight: 700; padding: 12px 30px; border-radius: 8px; cursor: pointer; transition: 0.3s; width: 100%; text-transform: uppercase; }
        .btn-simular:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0,242,254,0.4); }

        /* KPIS y Tablas */
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
        .card-grafica img { max-width: 100%; height: auto; border-radius: 8px; background-color: white; }
        .full-width { grid-column: span 2; }
    </style>
</head>
<body>
    <div class="container">
        <h1>TechClassUC: Panel de Simulación Avanzada</h1>
        
        <div class="form-container">
            <form method="POST" action="/">
                <div class="form-grid">
                    <div class="form-group">
                        <label>Tasa de Llegada (&lambda;)</label>
                        <input type="number" step="0.01" name="lambda_val" value="{{ inputs.lam }}" required>
                    </div>
                    <div class="form-group">
                        <label>Tasa de Servicio (&mu;)</label>
                        <input type="number" step="0.01" name="mu_val" value="{{ inputs.mu }}" required>
                    </div>
                    <div class="form-group">
                        <label>Servidores / Canales (c)</label>
                        <input type="number" name="c_val" value="{{ inputs.c }}" min="1" required>
                    </div>
                    <div class="form-group">
                        <label>Número de Réplicas (N)</label>
                        <input type="number" name="n_replicas" value="{{ inputs.n }}" min="2" required>
                    </div>
                </div>
                <button type="submit" class="btn-simular">⚡ Ejecutar Simulación Dinámica</button>
            </form>
        </div>

        {% if error_msg %}
        <div class="alert-danger">
            ⚠️ {{ error_msg }}
        </div>
        {% endif %}

        <p style="color: #34d399; font-weight: bold;">✓ Mostrando resultados para: &lambda;={{inputs.lam}}, &mu;={{inputs.mu}}, c={{inputs.c}}, N={{inputs.n}}</p>

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
                <h3>Estabilización</h3>
                <div class="value" style="color: #34d399; font-size: 22px; margin-top: 5px;">Muestras: {{ inputs.n }}</div>
                <div class="ic-box" style="color: #a7f3d0;">N Mínimo Requerido: {{ n_min }}</div>
            </div>
        </div>

        <h2>Módulo 4: Tabla de Validación Analítica ($M/M/c$ vs Simulación)</h2>
        <div class="table-responsive">
            <table>
                <thead>
                    <tr>
                        <th>Métrica del Sistema</th>
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
        
        <h2>Módulo 5 y 6: Tablero de Gráficas Estadísticas (Dinámicas)</h2>
        <div class="grid-graficas">
            <div class="card-grafica full-width">
                <h3>Análisis de Sensibilidad: Mapa de Calor (Wq Minutos)</h3>
                <img src="/graficas/grafica_5_heatmap_sensibilidad.png?v={{ r_id }}" alt="Heatmap">
            </div>
            <div class="card-grafica">
                <h3>Curva de Capacidad: Wq vs Técnicos (c)</h3>
                <img src="/graficas/grafica_3_capacidad_wq.png?v={{ r_id }}" alt="Capacidad">
            </div>
            <div class="card-grafica">
                <h3>Factor de Utilización (&rho;) vs Tasa de Llegada (&lambda;)</h3>
                <img src="/graficas/grafica_4_utilizacion_rho.png?v={{ r_id }}" alt="Utilización">
            </div>
            <div class="card-grafica">
                <h3>Evolución Temporal (SimPy)</h3>
                <img src="/graficas/grafica_1_evolucion_temporal.png?v={{ r_id }}" alt="Evolución">
            </div>
            <div class="card-grafica">
                <h3>Verificación Teorema Central del Límite</h3>
                <img src="/graficas/grafica_2_distribucion_wq.png?v={{ r_id }}" alt="TCL">
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def home():
    # Asignamos los valores por defecto iniciales de main.py
    lam = main.LAMBDA_BASE
    mu = main.MU_BASE
    c = main.C_BASE
    n = main.N_REPLICAS
    error_msg = None

    if request.method == 'POST':
        try:
            lam = float(request.form.get('lambda_val', lam))
            mu = float(request.form.get('mu_val', mu))
            c = int(request.form.get('c_val', c))
            n = int(request.form.get('n_replicas', n))
        except ValueError:
            pass

    # Validación preventiva de estabilidad del sistema matemático (Evita colapso por saturación)
    if lam >= (c * mu):
        error_msg = f"Aviso de Saturación: El sistema es inestable porque la tasa de llegada (λ={lam}) es mayor o igual que la capacidad máxima de atención (c*μ={c*mu}). Las colas crecerán indefinidamente."

    # =========================================================================
    # EJECUCIÓN CON CONTENCIÓN DE ERRORES MATEMÁTICOS (BLINDADO CONTRA TIMEOUT)
    # =========================================================================
    # Control dinámico del tiempo de simulación si el sistema se encuentra colapsado
    tiempo_sim_seguro = main.T_SIM_HORAS
    if lam >= (c * mu):
        tiempo_sim_seguro = min(1.5, main.T_SIM_HORAS)  # Freno de mano: reduce horas si colapsa
        error_msg = f"Aviso de Saturación Crítica: El sistema es inestable (λ={lam} >= c*μ={c*mu}). Se acortó el tiempo simulado para proteger el servidor."

    try:
        # Corremos la simulación Montecarlo con tiempo seguro
        resultados_mc, datos_ejemplo = montecarlo.correr_replicas(n, main.SEMILLA_BASE, lam, mu, c, tiempo_sim_seguro, main.T_WARM_HORAS)
        
        # Evitamos que los escenarios de sensibilidad escalen a valores infinitos de clientes
        lista_lambdas_dinamica = [max(0.5, lam - 2), lam, min(lam + 1, c*mu + 1), min(lam + 2, c*mu + 2)]
        lista_c_dinamica = [max(1, c - 1), c, c + 1, c + 2]
        
        # Si el sistema está colapsado, reducimos réplicas en la matriz para agilizar la carga
        n_sensibilidad = min(5, n) if lam >= (c * mu) else n
        
        matriz_sensibilidad = sensibilidad.realizar_analisis_sensibilidad(n_sensibilidad, main.SEMILLA_BASE, lista_lambdas_dinamica, lista_c_dinamica, mu, tiempo_sim_seguro, main.T_WARM_HORAS)
        generar_graficas(resultados_mc, datos_ejemplo, matriz_sensibilidad, lista_lambdas_dinamica, lista_c_dinamica, ruta_guardado=GRAFICAS_DIR)

        rho_sim = resultados_mc['rho']['media']
        lq_sim  = resultados_mc['Lq']['media']
        wq_sim  = resultados_mc['Wq']['media']
    except Exception as e:
        error_msg = f"Error en simulación: Valores extremos causaron una indeterminación matemática. Intente aumentar los servidores o reducir la llegada."
        rho_sim, lq_sim, wq_sim = 0.99, 50.0, 1.0

    l_sim   = lq_sim + (lam / mu) if mu > 0 else 0
    w_sim   = wq_sim + (1 / mu) if mu > 0 else 0

    # Analítico Teórico M/M/c
    rho_teo = lam / (c * mu) if mu > 0 else 0.99
    if rho_teo >= 1:
        rho_teo = 0.9999

    try:
        suma_p0 = sum([(lam / mu)**i / math.factorial(i) for i in range(c)])
        suma_p0 += ((lam / mu)**c / (math.factorial(c) * (1 - rho_teo)))
        p0_teo = 1 / suma_p0 if suma_p0 > 0 else 0.001

        lq_teo = (p0_teo * ((lam / mu)**c) * rho_teo) / (math.factorial(c) * ((1 - rho_teo)**2))
        wq_teo = lq_teo / lam if lam > 0 else 0
        l_teo  = lq_teo + (lam / mu)
        w_teo  = wq_teo + (1 / mu)
    except:
        lq_teo, wq_teo, l_teo, w_teo = 0, 0, 0, 0

    # Errores relativos controlados
    err_rho = abs(rho_teo - rho_sim) / rho_teo * 100 if rho_teo > 0 else 0
    err_lq  = abs(lq_teo - lq_sim) / lq_teo * 100 if lq_teo > 0 else 0
    err_wq  = abs(wq_teo - wq_sim) / wq_teo * 100 if wq_teo > 0 else 0
    err_l   = abs(l_teo - l_sim) / l_teo * 100 if l_teo > 0 else 0
    err_w   = abs(w_teo - w_sim) / w_teo * 100 if w_teo > 0 else 0

    # Intervalos seguros
    try:
        wq_ic_inf, wq_ic_sup = resultados_mc['Wq']['ic_inf'] * 60, resultados_mc['Wq']['ic_sup'] * 60
        lq_ic_inf, lq_ic_sup = resultados_mc['Lq']['ic_inf'], resultados_mc['Lq']['ic_sup']
        rho_ic_inf, rho_ic_sup = resultados_mc['rho']['ic_inf'] * 100, resultados_mc['rho']['ic_sup'] * 100
    except:
        wq_ic_inf, wq_ic_sup, lq_ic_inf, lq_ic_sup, rho_ic_inf, rho_ic_sup = 0, 0, 0, 0, 0, 0

    # N Mínimo
    try:
        valores_wq = resultados_mc['Wq']['valores']
        media_wq = np.mean(valores_wq)
        desviacion_wq = np.std(valores_wq, ddof=1)
        n_minimo_calculado = ((1.96 * desviacion_wq) / (0.05 * media_wq)) ** 2 if media_wq > 0 else 30
        n_minimo_calculado = max(10, math.ceil(n_minimo_calculado))
    except:
        n_minimo_calculado = 30

    import random
    rand_id = random.randint(1, 99999)

    return render_template_string(
        HTML_TEMPLATE,
        inputs={'lam': lam, 'mu': mu, 'c': c, 'n': n},
        error_msg=error_msg,
        rho_sim=rho_sim, lq_sim=lq_sim, wq_sim=wq_sim, l_sim=l_sim, w_sim=w_sim,
        rho_teo=rho_teo, lq_teo=lq_teo, wq_teo=wq_teo, l_teo=l_teo, w_teo=w_teo,
        err_rho=err_rho, err_lq=err_lq, err_wq=err_wq, err_l=err_l, err_w=err_w,
        wq_ic_inf=wq_ic_inf, wq_ic_sup=wq_ic_sup,
        lq_ic_inf=lq_ic_inf, lq_ic_sup=lq_ic_sup,
        rho_ic_inf=rho_ic_inf, rho_ic_sup=rho_ic_sup,
        n_min=n_minimo_calculado, r_id=rand_id
    )

@app.route('/graficas/<filename>')
def obtener_grafica(filename):
    return send_from_directory(GRAFICAS_DIR, filename)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
