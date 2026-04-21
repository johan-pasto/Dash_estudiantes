import pandas as pd
import plotly.express as px
import dash
from dash import html, Input, Output, dcc, State, dash_table
from database import obtenerestudiantes, insertarestudiante
import plotly.graph_objects as go

# ── FUNCIONES AUXILIARES ──────────────────────────────────────────────
def procesar_datos(df):
    """Calcula columnas derivadas para evitar repetir código."""
    if df.empty:
        return df
        
    if all(col in df.columns for col in ['nota1', 'nota2', 'nota3']):
        df['Promedio'] = ((df['nota1'] + df['nota2'] + df['nota3']) / 3).round(2)
    else:
        df['Promedio'] = 0

    df["Desempeño"] = pd.cut(
        df["Promedio"],
        bins=[0, 2.9, 3.5, 4.0, 5.0],
        labels=["Bajo", "Medio", "Alto", "Excelente"],
        include_lowest=True
    ).astype(str)
    
    return df

def _fig_vacia(mensaje):
    fig = go.Figure()
    fig.update_layout(
        annotations=[dict(text=mensaje, x=0.5, y=0.5,
                          xref="paper", yref="paper",
                          showarrow=False, font=dict(size=15, color="gray"))],
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        plot_bgcolor="white", paper_bgcolor="white"
    )
    return fig

# ── LAYOUT MODULARIZADO ───────────────────────────────────────────────
def crear_formulario(carreras_unicas):
    return html.Div([
        html.H3("Agregar nuevo estudiante", style={"marginBottom": "15px"}),
        html.Div([
            html.Div([
                html.Label("Nombre"),
                dcc.Input(id="f_nombre", type="text", placeholder="Nombre completo", style={"width": "100%", "padding": "6px"})
            ], style={"flex": "2", "minWidth": "200px"}),
            html.Div([
                html.Label("Edad"),
                dcc.Input(id="f_edad", type="number", placeholder="Ej: 20", min=15, max=80, style={"width": "100%", "padding": "6px"})
            ], style={"flex": "1", "minWidth": "100px"}),
            html.Div([
                html.Label("Carrera"),
                dcc.Dropdown(id="f_carrera", options=[{"label": c, "value": c} for c in carreras_unicas], placeholder="Seleccionar...", clearable=False)
            ], style={"flex": "2", "minWidth": "180px"}),
            html.Div([
                html.Label("Nota 1"),
                dcc.Input(id="f_nota1", type="number", placeholder="0.0 - 5.0", min=0, max=5, step=0.1, style={"width": "100%", "padding": "6px"})
            ], style={"flex": "1", "minWidth": "100px"}),
            html.Div([
                html.Label("Nota 2"),
                dcc.Input(id="f_nota2", type="number", placeholder="0.0 - 5.0", min=0, max=5, step=0.1, style={"width": "100%", "padding": "6px"})
            ], style={"flex": "1", "minWidth": "100px"}),
            html.Div([
                html.Label("Nota 3"),
                dcc.Input(id="f_nota3", type="number", placeholder="0.0 - 5.0", min=0, max=5, step=0.1, style={"width": "100%", "padding": "6px"})
            ], style={"flex": "1", "minWidth": "100px"}),
        ], style={"display": "flex", "flexWrap": "wrap", "gap": "12px", "alignItems": "flex-end"}),
        html.Br(),
        html.Button("Guardar estudiante", id="btn_guardar", n_clicks=0,
                    style={"backgroundColor": "#2ecc71", "color": "white", "border": "none", "padding": "10px 24px", "borderRadius": "6px", "cursor": "pointer", "fontSize": "15px"}),
        html.Div(id="msg_formulario", style={"marginTop": "10px", "fontWeight": "bold"})
    ], style={"backgroundColor": "#f8f9fa", "border": "1px solid #dee2e6", "borderRadius": "10px", "padding": "20px", "margin": "20px auto", "width": "90%"})

# ── FUNCIÓN PRINCIPAL ─────────────────────────────────────────────────
def creartablero(server):
    df_inicial = procesar_datos(obtenerestudiantes())
    carreras_unicas = sorted(df_inicial["carrera"].unique()) if not df_inicial.empty else []

    # Usa el server de Flask que ya existe
    appnotas = dash.Dash(
        __name__,
        server=server,
        url_base_pathname="/tablero/",
        suppress_callback_exceptions=True
    )

    appnotas.layout = html.Div([
        # Store para guardar los datos en sesión y no saturar la BD
        
        dcc.Store(id="datos_store"), 
        dcc.Store(id="recargar_signal"),

        html.Button("🔄 Recargar BD", id="btn_recargar", n_clicks=0,
                    style={"padding": "8px 16px", "cursor": "pointer", "borderRadius": "6px", "border": "1px solid #dee2e6", "backgroundColor": "white", "fontSize": "14px"}),

        crear_formulario(carreras_unicas),

        html.Div([
            html.Label("Seleccionar carrera"),
            dcc.Dropdown(id="filtro_carrera", options=[{"label": c, "value": c} for c in carreras_unicas], value=carreras_unicas[0] if carreras_unicas else None),
            html.Br(),
            html.Label("Rango de edad"),
            dcc.RangeSlider(id="slider_edad", min=15, max=80, step=1, value=[15, 80], tooltip={"placement": "bottom", "always_visible": True}),
            html.Br(),
            html.Label("Rango promedio"),
            dcc.RangeSlider(id="slider_promedio", min=0, max=5, step=0.1, value=[0, 5], tooltip={"placement": "bottom", "always_visible": True})
        ], style={"width": "70%", "margin": "auto"}),

        html.Br(),
        html.Div(id="kpis", style={"display": "flex", "justifyContent": "space-around"}),
        html.Br(),
        dcc.Input(id="busqueda", type="text", placeholder="Buscar por nombre o carrera...", debounce=True, style={"width": "70%", "margin": "auto", "display": "block", "padding": "8px"}),
        html.Br(),
        
        dcc.Loading(
            dash_table.DataTable(id="tabla", page_size=8, filter_action="native", sort_action="native",
                                 row_selectable="multi", selected_rows=[], style_table={"overflowX": "auto"}, style_cell={"textAlign": "center"}),
            type="circle"
        ),
        html.Br(),
        dcc.Loading(dcc.Graph(id="gra_detallado"), type="default"),
        html.Br(),
        dcc.Tabs([
            dcc.Tab(label="Histograma", children=[dcc.Graph(id="histograma")]),
            dcc.Tab(label="Dispersion", children=[dcc.Graph(id="dispersion")]),
            dcc.Tab(label="Desempeño", children=[dcc.Graph(id="pie")]),
        ])
    ])

    # ── CALLBACKS ─────────────────────────────────────────────────────
    
    # 1. Callback de Formulario
    @appnotas.callback(
        Output("msg_formulario", "children"), Output("msg_formulario", "style"), Output("recargar_signal", "data"),
        Output("f_nombre", "value"), Output("f_edad", "value"), Output("f_carrera", "value"),
        Output("f_nota1", "value"), Output("f_nota2", "value"), Output("f_nota3", "value"),
        Input("btn_guardar", "n_clicks"),
        State("f_nombre", "value"), State("f_edad", "value"), State("f_carrera", "value"),
        State("f_nota1", "value"), State("f_nota2", "value"), State("f_nota3", "value"),
        prevent_initial_call=True
    )
    def guardar_estudiante(n, nombre, edad, carrera, nota1, nota2, nota3):
        vacios = [x for x in [nombre, edad, carrera, nota1, nota2, nota3] if x is None or str(x).strip() == ""]
        if vacios:
            return ("⚠️ Por favor completa todos los campos.", {"color": "#e67e22", "marginTop": "10px", "fontWeight": "bold"}, None, nombre, edad, carrera, nota1, nota2, nota3)
        try:
            insertarestudiante({
                "nombre": str(nombre).strip(), "edad": int(edad), "carrera": carrera,
                "nota1": float(nota1), "nota2": float(nota2), "nota3": float(nota3)
            })
            return ("✅ Estudiante guardado correctamente.", {"color": "#27ae60", "marginTop": "10px", "fontWeight": "bold"}, True, None, None, None, None, None, None)
        except Exception as e:
            return (f"❌ Error al guardar: {str(e)}", {"color": "#e74c3c", "marginTop": "10px", "fontWeight": "bold"}, None, nombre, edad, carrera, nota1, nota2, nota3)

    # 2. Callback para cargar datos de la BD (Solo se ejecuta al cargar o si hay una señal/botón)
    @appnotas.callback(
        Output("datos_store", "data"),
        Input("btn_recargar", "n_clicks"),
        Input("recargar_signal", "data")
    )
    def recargar_datos_bd(n_clicks, signal):
        df = procesar_datos(obtenerestudiantes())
        return df.to_dict("records")

    # 3. Callback Principal: Filtra sobre los datos en memoria (Más rápido)
    @appnotas.callback(
        Output("tabla", "data"), Output("tabla", "columns"), Output("kpis", "children"),
        Output("histograma", "figure"), Output("dispersion", "figure"), Output("pie", "figure"),
        Output("filtro_carrera", "options"),
        Input("datos_store", "data"), # Reacciona a los datos en memoria, no a la BD
        Input("filtro_carrera", "value"), Input("slider_edad", "value"),
        Input("slider_promedio", "value"), Input("busqueda", "value")
    )
    def actualizar_comp(datos_dict, carrera, rangoedad, rangoprome, busqueda):
        if not datos_dict:
            return [], [], [], _fig_vacia("Sin datos"), _fig_vacia("Sin datos"), _fig_vacia("Sin datos"), []
            
        df = pd.DataFrame(datos_dict)
        opciones_carrera = [{"label": c, "value": c} for c in sorted(df["carrera"].unique())]

        # Aplicar filtros
        filtro = df[
            (df["edad"] >= rangoedad[0]) & (df["edad"] <= rangoedad[1]) &
            (df["Promedio"] >= rangoprome[0]) & (df["Promedio"] <= rangoprome[1])
        ]
        
        # Filtro de carrera solo si hay algo seleccionado
        if carrera:
            filtro = filtro[filtro["carrera"] == carrera]

        if busqueda:
            b = str(busqueda).strip().lower()
            if b:
                mask = pd.Series(False, index=filtro.index)
                for col in ['nombre', 'carrera']:
                    if col in filtro.columns:
                        mask |= filtro[col].astype(str).str.lower().str.contains(b, na=False)
                filtro = filtro[mask]

        promedio = round(filtro["Promedio"].mean(), 2) if len(filtro) > 0 else 0
        total = len(filtro)
        maximo = round(filtro["Promedio"].max(), 2) if len(filtro) > 0 else 0

        kpis = [
            html.Div([html.H4("Promedio"), html.H2(promedio)], style={"backgroundColor": "#3498db", "color": "white", "padding": "15px", "borderRadius": "10px"}),
            html.Div([html.H4("Total estudiantes"), html.H2(total)], style={"backgroundColor": "#2ecc71", "color": "white", "padding": "15px", "borderRadius": "10px"}),
            html.Div([html.H4("Máximo"), html.H2(maximo)], style={"backgroundColor": "#e74c3c", "color": "white", "padding": "15px", "borderRadius": "10px"})
        ]

        fig_hist = px.histogram(filtro, x="Promedio", nbins=10, title="Distribución de Promedios") if len(filtro) > 0 else _fig_vacia("No hay estudiantes")
        fig_disp = px.scatter(filtro, x="edad", y="Promedio", color="Desempeño", title="Edad vs Promedio") if len(filtro) > 0 else _fig_vacia("No hay estudiantes")
        fig_pie = px.pie(filtro, names="Desempeño", title="Distribución por Desempeño") if len(filtro) > 0 and filtro["Desempeño"].notna().any() else _fig_vacia("Sin datos")

        return filtro.to_dict("records"), [{"name": i, "id": i} for i in filtro.columns], kpis, fig_hist, fig_disp, fig_pie, opciones_carrera

    # 4. Callback Gráfico Detallado
    @appnotas.callback(
        Output("gra_detallado", "figure"),
        Input("tabla", "derived_virtual_data"),
        Input("tabla", "derived_virtual_selected_rows")
    )
    def actualizar_detalle(rows, selected_rows):
        if not rows:
            return _fig_vacia("Sin datos")

        dff = pd.DataFrame(rows)
        # Ya no calculamos promedio y desempeño aquí porque viene procesado del Store

        if selected_rows:
            dff = dff.iloc[selected_rows]

        if not dff.empty:
            return px.scatter(dff, x="edad", y="Promedio", color="Desempeño", size="Promedio", title="Análisis detallado (Seleccione filas de la tabla)")
        
        return _fig_vacia("Sin datos para mostrar")

    return appnotas