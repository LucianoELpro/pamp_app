import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import gspread
from plotly.subplots import make_subplots
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

st.set_page_config(
    page_title="PAMP 2026 — Dashboard",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Paleta y tema global ───────────────────────────────────────────────────────
C = {
    "azul1": "#1F4E79", "azul2": "#2E75B6", "azul3": "#5B9BD5", "azul4": "#BDD7EE",
    "verde1": "#375623", "verde2": "#548235", "verde3": "#70AD47", "verde4": "#A9D18E",
    "rojo1":  "#A50000", "rojo2":  "#C00000", "rojo3":  "#E04040",
    "naranja":"#C55A11", "amarillo":"#F4B942",
    "gris1":  "#2F2F2F", "gris2":  "#595959", "gris3":  "#A6A6A6", "gris4":  "#E8ECF0",
    "fondo":  "#F4F7FB", "blanco": "#FFFFFF",
}

FONT = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"

def chart_layout(fig, title="", height=340, show_legend=True, margin=None):
    m = margin or dict(l=16, r=16, t=48 if title else 16, b=16)
    fig.update_layout(
        title=dict(text=title, font=dict(family=FONT, size=13, color=C["azul1"]),
                   x=0, xanchor="left", pad=dict(l=4)),
        height=height,
        plot_bgcolor=C["blanco"],
        paper_bgcolor=C["blanco"],
        font=dict(family=FONT, size=11, color=C["gris1"]),
        showlegend=show_legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.04,
                    xanchor="left", x=0,
                    font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
        margin=m,
        hoverlabel=dict(bgcolor=C["azul1"], font_color=C["blanco"],
                        font_family=FONT, font_size=12,
                        bordercolor=C["azul1"]),
        xaxis=dict(showgrid=False, zeroline=False, showline=False,
                   tickfont=dict(size=10, color=C["gris2"])),
        yaxis=dict(showgrid=True, gridcolor=C["gris4"], zeroline=False,
                   showline=False, tickfont=dict(size=10, color=C["gris2"])),
    )
    return fig

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

  html, body, [class*="css"] {{ font-family: {FONT}; }}

  /* Fondo general */
  .stApp {{ background-color: {C["fondo"]}; }}

  /* Sidebar */
  [data-testid="stSidebar"] {{
      background: linear-gradient(180deg, {C["azul1"]} 0%, #163d60 100%);
  }}
  [data-testid="stSidebar"] * {{ color: {C["blanco"]} !important; }}
  [data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {{
      background-color: {C["azul3"]} !important;
  }}
  [data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,0.2); }}
  [data-testid="stSidebar"] label {{ color: rgba(255,255,255,0.75) !important; font-size: 0.8rem !important; }}

  /* Header */
  .dash-header {{
      background: linear-gradient(135deg, {C["azul1"]} 0%, {C["azul2"]} 100%);
      border-radius: 12px; padding: 20px 28px; margin-bottom: 20px;
      box-shadow: 0 4px 20px rgba(31,78,121,0.25);
  }}
  .dash-title {{ font-size: 1.6rem; font-weight: 700; color: #fff; margin: 0; letter-spacing: -0.3px; }}
  .dash-sub   {{ font-size: 0.85rem; color: rgba(255,255,255,0.75); margin-top: 4px; }}

  /* KPI cards */
  .kpi-row {{ display: flex; gap: 12px; margin-bottom: 8px; }}
  .kpi {{
      flex: 1; border-radius: 10px; padding: 14px 16px;
      background: {C["blanco"]}; border: 1px solid {C["gris4"]};
      box-shadow: 0 2px 8px rgba(0,0,0,0.06);
      display: flex; flex-direction: column; align-items: center; text-align: center;
  }}
  .kpi-val  {{ font-size: 1.7rem; font-weight: 700; line-height: 1.1; }}
  .kpi-lbl  {{ font-size: 0.7rem; color: {C["gris2"]}; margin-top: 5px;
               text-transform: uppercase; letter-spacing: 0.5px; font-weight: 500; }}
  .kpi-bar  {{ width: 100%; height: 3px; border-radius: 2px; margin-top: 10px; }}

  .kpi-blue   {{ border-top: 3px solid {C["azul2"]};   }} .kpi-blue   .kpi-val {{ color: {C["azul2"]};   }}
  .kpi-green  {{ border-top: 3px solid {C["verde3"]};  }} .kpi-green  .kpi-val {{ color: {C["verde2"]};  }}
  .kpi-red    {{ border-top: 3px solid {C["rojo2"]};   }} .kpi-red    .kpi-val {{ color: {C["rojo2"]};   }}
  .kpi-orange {{ border-top: 3px solid {C["naranja"]}; }} .kpi-orange .kpi-val {{ color: {C["naranja"]}; }}

  /* Chart cards */
  .chart-card {{
      background: {C["blanco"]}; border-radius: 12px;
      border: 1px solid {C["gris4"]};
      box-shadow: 0 2px 10px rgba(0,0,0,0.06);
      padding: 4px 4px 0; margin-bottom: 4px;
  }}

  /* Section header */
  .sec-hdr {{
      font-size: 0.8rem; font-weight: 700; text-transform: uppercase;
      letter-spacing: 1px; color: {C["azul1"]};
      border-left: 4px solid {C["azul3"]}; padding-left: 10px;
      margin: 20px 0 10px;
  }}

  /* Tabla */
  [data-testid="stDataFrame"] {{ border-radius: 10px; overflow: hidden; }}

  /* Input busqueda */
  .stTextInput > div > div {{ border-radius: 8px; border-color: {C["gris4"]}; }}
</style>
""", unsafe_allow_html=True)

# ── Datos ──────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_data():
    # Conectar a Google Sheets usando los secrets de Streamlit
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )
    client = gspread.authorize(creds)
    
    # Abrir el Sheet y la hoja específica
    sheet = client.open("BASE_DATOS_LIMPIA").worksheet("BASE DE DATOS")
    
    # Convertir a DataFrame
    df = pd.DataFrame(sheet.get_all_records())
    
    # Limpieza de datos (igual que antes)
    for col in ["Programado", "Ejecutado", "Acta", "Informe", "C.O."]:
        if col in df.columns:
            df[col] = df[col].fillna("NO").astype(str).str.upper().str.strip()
    df["Completo"]   = df["Completo"].fillna("NO").astype(str).str.upper().str.strip()
    df["Mes"]        = df["Mes"].fillna("SIN MES").astype(str).str.upper().str.strip()
    df["Región"]     = df["Región"].fillna("SIN REGIÓN").astype(str).str.upper().str.strip()
    df["TipoEquipo"] = df["TipoEquipo"].fillna("SIN TIPO").astype(str).str.upper().str.strip()
    df["Estado del Equipo (Operativo / Inoperativo)"] = \
        df["Estado del Equipo (Operativo / Inoperativo)"].fillna("NO DEFINIDO").astype(str)
    df["Proveedor"]  = df["Proveedor"].fillna("SIN PROVEEDOR").astype(str)
    for col in ["INGRESO UNITARIO 2", "GASTO", "Utilidad"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df

df_full = load_data()
MESES = ["ENERO","FEBRERO","MARZO","ABRIL","MAYO","JUNIO",
         "JULIO","AGOSTO","SEPTIEMBRE","OCTUBRE","NOVIEMBRE","DICIEMBRE"]

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔧 PAMP 2026")
    st.markdown("---")
    st.markdown("**Filtros**")

    regiones  = sorted(df_full["Región"].unique())
    sel_region = st.multiselect("Región", regiones, default=regiones)

    meses_disp = [m for m in MESES if m in df_full["Mes"].unique()]
    sel_mes = st.multiselect("Mes", meses_disp, default=meses_disp)

    tipos = sorted(df_full["TipoEquipo"].unique())
    sel_tipo = st.multiselect("Tipo de Equipo", tipos, default=tipos)

    estados = sorted(df_full["Estado del Equipo (Operativo / Inoperativo)"].unique())
    sel_estado = st.multiselect("Estado del Equipo", estados, default=estados)

    st.markdown("---")
    st.markdown("**Filtros clave**")
    prog_opt = st.selectbox("Programado", ["TODOS", "SI", "NO"])
    ejec_opt = st.selectbox("Ejecutado",  ["TODOS", "SI", "NO"])
    st.markdown("---")
    st.caption("Dashboard v1.2 · 2026")

# ── Filtrar ────────────────────────────────────────────────────────────────────
df = df_full.copy()
if sel_region: df = df[df["Región"].isin(sel_region)]
if sel_mes:    df = df[df["Mes"].isin(sel_mes)]
if sel_tipo:   df = df[df["TipoEquipo"].isin(sel_tipo)]
if sel_estado: df = df[df["Estado del Equipo (Operativo / Inoperativo)"].isin(sel_estado)]
if prog_opt != "TODOS": df = df[df["Programado"] == prog_opt]
if ejec_opt != "TODOS": df = df[df["Ejecutado"]  == ejec_opt]

# ── Métricas ───────────────────────────────────────────────────────────────────
total        = len(df)
prog_si      = (df["Programado"] == "SI").sum()
prog_no      = (df["Programado"] == "NO").sum()
ejec_si      = (df["Ejecutado"]  == "SI").sum()
ejec_no      = (df["Ejecutado"]  == "NO").sum()
ejec_de_prog = len(df[(df["Programado"] == "SI") & (df["Ejecutado"] == "SI")])
pct_prog     = round(prog_si / total * 100, 1) if total else 0
pct_ejec     = round(ejec_si / total * 100, 1) if total else 0
pct_avance   = round(ejec_de_prog / prog_si * 100, 1) if prog_si else 0
utilidad     = df["Utilidad"].sum()
ingreso      = df["INGRESO UNITARIO 2"].sum()
gasto        = df["GASTO"].sum()

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="dash-header">
  <div class="dash-title">Plan Anual de Mantenimiento Preventivo — PAMP 2026</div>
  <div class="dash-sub">Mostrando <b>{total:,}</b> de <b>{len(df_full):,}</b> registros · Datos actualizados</div>
</div>
""", unsafe_allow_html=True)

# ── KPIs ───────────────────────────────────────────────────────────────────────
def kpi_html(val, lbl, cls):
    return f"""<div class="kpi {cls}">
        <div class="kpi-val">{val}</div>
        <div class="kpi-lbl">{lbl}</div>
    </div>"""

avance_cls = "kpi-green" if pct_avance >= 70 else ("kpi-orange" if pct_avance >= 40 else "kpi-red")
util_cls   = "kpi-green" if utilidad   >= 0  else "kpi-red"

kpis_html = (
    kpi_html(f"{total:,}",          "Total Registros",       "kpi-blue")
  + kpi_html(f"{prog_si:,}",        "Programados",           "kpi-green")
  + kpi_html(f"{prog_no:,}",        "No Programados",        "kpi-red")
  + kpi_html(f"{ejec_si:,}",        "Ejecutados",            "kpi-green")
  + kpi_html(f"{ejec_no:,}",        "No Ejecutados",         "kpi-red")
  + kpi_html(f"{pct_avance}%",      "Avance Ejec / Prog",    avance_cls)
  + kpi_html(f"S/{utilidad:,.0f}",  "Utilidad Total",        util_cls)
)
st.markdown(f'<div class="kpi-row">{kpis_html}</div>', unsafe_allow_html=True)

# ── Sección: Prog vs Ejec ──────────────────────────────────────────────────────
st.markdown('<div class="sec-hdr">Programado vs Ejecutado — Análisis Central</div>', unsafe_allow_html=True)

col_a, col_b, col_c = st.columns([1, 1, 2], gap="medium")

with col_a:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    fig = go.Figure(go.Pie(
        labels=["Programado", "No Programado"], values=[prog_si, prog_no],
        hole=0.62,
        marker=dict(colors=[C["azul2"], C["gris4"]],
                    line=dict(color=C["blanco"], width=2)),
        textinfo="none", hovertemplate="<b>%{label}</b><br>%{value:,} equipos (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="Programados", font=dict(family=FONT, size=13, color=C["azul1"]),
                   x=0.5, xanchor="center"),
        height=280, margin=dict(l=8, r=8, t=40, b=8),
        showlegend=False, paper_bgcolor=C["blanco"], plot_bgcolor=C["blanco"],
        annotations=[dict(text=f"<b>{pct_prog}%</b>", x=0.5, y=0.48,
                          font=dict(size=22, color=C["azul2"], family=FONT),
                          showarrow=False),
                     dict(text="programado", x=0.5, y=0.35,
                          font=dict(size=10, color=C["gris3"], family=FONT),
                          showarrow=False)],
        hoverlabel=dict(bgcolor=C["azul1"], font_color=C["blanco"], font_family=FONT),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

with col_b:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    fig = go.Figure(go.Pie(
        labels=["Ejecutado", "No Ejecutado"], values=[ejec_si, ejec_no],
        hole=0.62,
        marker=dict(colors=[C["verde3"], C["gris4"]],
                    line=dict(color=C["blanco"], width=2)),
        textinfo="none", hovertemplate="<b>%{label}</b><br>%{value:,} equipos (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="Ejecutados", font=dict(family=FONT, size=13, color=C["azul1"]),
                   x=0.5, xanchor="center"),
        height=280, margin=dict(l=8, r=8, t=40, b=8),
        showlegend=False, paper_bgcolor=C["blanco"], plot_bgcolor=C["blanco"],
        annotations=[dict(text=f"<b>{pct_ejec}%</b>", x=0.5, y=0.48,
                          font=dict(size=22, color=C["verde2"], family=FONT),
                          showarrow=False),
                     dict(text="ejecutado", x=0.5, y=0.35,
                          font=dict(size=10, color=C["gris3"], family=FONT),
                          showarrow=False)],
        hoverlabel=dict(bgcolor=C["verde1"], font_color=C["blanco"], font_family=FONT),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

with col_c:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    tipo_pv = (df.groupby("TipoEquipo")
               .agg(Programado=("Programado", lambda x: (x=="SI").sum()),
                    Ejecutado =("Ejecutado",  lambda x: (x=="SI").sum()))
               .sort_values("Programado", ascending=False).head(10).reset_index())

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Programado", x=tipo_pv["TipoEquipo"], y=tipo_pv["Programado"],
        marker=dict(color=C["azul3"], line=dict(color=C["azul2"], width=0)),
        hovertemplate="<b>%{x}</b><br>Programado: <b>%{y:,}</b><extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Ejecutado", x=tipo_pv["TipoEquipo"], y=tipo_pv["Ejecutado"],
        marker=dict(color=C["verde3"], line=dict(color=C["verde2"], width=0)),
        hovertemplate="<b>%{x}</b><br>Ejecutado: <b>%{y:,}</b><extra></extra>",
    ))
    chart_layout(fig, "Prog. vs Ejec. por Tipo de Equipo (Top 10)", height=280, margin=dict(l=8,r=8,t=48,b=8))
    fig.update_layout(barmode="group", xaxis_tickangle=-30,
                      bargap=0.25, bargroupgap=0.08)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

# ── Prog vs Ejec por Mes (ancho completo) ─────────────────────────────────────
st.markdown('<div class="chart-card">', unsafe_allow_html=True)
mes_pv = (df.groupby("Mes")
          .agg(Programado=("Programado", lambda x: (x=="SI").sum()),
               Ejecutado =("Ejecutado",  lambda x: (x=="SI").sum()))
          .reindex(MESES, fill_value=0).reset_index())
mes_pv = mes_pv[mes_pv["Programado"] + mes_pv["Ejecutado"] > 0]
mes_pv["pct"] = (mes_pv["Ejecutado"] / mes_pv["Programado"].replace(0, np.nan) * 100).fillna(0).round(1)

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Bar(
    name="Programado", x=mes_pv["Mes"], y=mes_pv["Programado"],
    marker=dict(color=C["azul3"]),
    hovertemplate="<b>%{x}</b><br>Programado: <b>%{y:,}</b><extra></extra>",
), secondary_y=False)
fig.add_trace(go.Bar(
    name="Ejecutado", x=mes_pv["Mes"], y=mes_pv["Ejecutado"],
    marker=dict(color=C["verde3"]),
    hovertemplate="<b>%{x}</b><br>Ejecutado: <b>%{y:,}</b><extra></extra>",
), secondary_y=False)
fig.add_trace(go.Scatter(
    name="% Avance", x=mes_pv["Mes"], y=mes_pv["pct"],
    mode="lines+markers+text", yaxis="y2",
    line=dict(color=C["naranja"], width=2.5),
    marker=dict(size=8, color=C["naranja"], symbol="circle",
                line=dict(color=C["blanco"], width=2)),
    text=[f"{v}%" for v in mes_pv["pct"]],
    textposition="top center",
    textfont=dict(size=10, color=C["naranja"], family=FONT),
    hovertemplate="<b>%{x}</b><br>% Avance: <b>%{y:.1f}%</b><extra></extra>",
), secondary_y=True)

chart_layout(fig, "Programado vs Ejecutado por Mes  ·  Línea = % Avance mensual", height=360,
             margin=dict(l=12, r=12, t=50, b=12))
fig.update_layout(
    barmode="group", bargap=0.2, bargroupgap=0.08,
    yaxis2=dict(title="", overlaying="y", side="right",
                range=[0, 130], showgrid=False,
                tickfont=dict(size=10, color=C["naranja"])),
)
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
st.markdown('</div>', unsafe_allow_html=True)

# ── Avance por Región  +  Finanzas por Mes ────────────────────────────────────
st.markdown('<div class="sec-hdr">Avance por Región · Análisis Financiero</div>', unsafe_allow_html=True)

col_r, col_f = st.columns([1, 1.4], gap="medium")

with col_r:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    reg_pv = (df.groupby("Región")
              .agg(Programado=("Programado", lambda x: (x=="SI").sum()),
                   Ejecutado =("Ejecutado",  lambda x: (x=="SI").sum()))
              .reset_index())
    reg_pv["pct"] = (reg_pv["Ejecutado"] / reg_pv["Programado"].replace(0, np.nan) * 100).fillna(0).round(1)
    reg_pv = reg_pv.sort_values("pct", ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Programado", y=reg_pv["Región"], x=reg_pv["Programado"],
        orientation="h", marker=dict(color=C["azul4"]),
        hovertemplate="<b>%{y}</b><br>Programado: <b>%{x:,}</b><extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Ejecutado", y=reg_pv["Región"], x=reg_pv["Ejecutado"],
        orientation="h", marker=dict(color=C["verde3"]),
        hovertemplate="<b>%{y}</b><br>Ejecutado: <b>%{x:,}</b> (%{customdata[0]}%)<extra></extra>",
        customdata=reg_pv[["pct"]].values,
    ))
    chart_layout(fig, "Avance por Región", height=340, margin=dict(l=8,r=8,t=48,b=8))
    fig.update_layout(barmode="overlay", xaxis_title="Equipos",
                      yaxis=dict(showgrid=False))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

with col_f:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    mes_fin = (df.groupby("Mes")
               .agg(Ingreso=("INGRESO UNITARIO 2","sum"),
                    Gasto=("GASTO","sum"), Utilidad=("Utilidad","sum"),
                    Equipos=("Mes","count"))
               .reindex(MESES, fill_value=0).reset_index())
    mes_fin = mes_fin[mes_fin["Equipos"] > 0]

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(
        name="Ingreso", x=mes_fin["Mes"], y=mes_fin["Ingreso"],
        marker=dict(color=C["azul3"]),
        hovertemplate="<b>%{x}</b><br>Ingreso: <b>S/ %{y:,.2f}</b><extra></extra>",
    ), secondary_y=False)
    fig.add_trace(go.Bar(
        name="Gasto", x=mes_fin["Mes"], y=mes_fin["Gasto"],
        marker=dict(color=C["rojo3"], opacity=0.85),
        hovertemplate="<b>%{x}</b><br>Gasto: <b>S/ %{y:,.2f}</b><extra></extra>",
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        name="Utilidad", x=mes_fin["Mes"], y=mes_fin["Utilidad"],
        mode="lines+markers",
        line=dict(color=C["verde2"], width=2.5),
        marker=dict(size=7, color=C["verde2"], line=dict(color=C["blanco"], width=2)),
        hovertemplate="<b>%{x}</b><br>Utilidad: <b>S/ %{y:,.2f}</b><extra></extra>",
    ), secondary_y=True)

    chart_layout(fig, "Ingresos · Gastos · Utilidad por Mes", height=340,
                 margin=dict(l=8,r=8,t=48,b=8))
    fig.update_layout(
        barmode="group", bargap=0.2,
        yaxis2=dict(overlaying="y", side="right", showgrid=False,
                    tickfont=dict(size=10, color=C["verde2"])),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

# ── Tipos + Estado operativo ───────────────────────────────────────────────────
st.markdown('<div class="sec-hdr">Distribución de Equipos</div>', unsafe_allow_html=True)
col_t, col_e = st.columns([1.2, 1], gap="medium")

with col_t:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    tipo_cnt = df["TipoEquipo"].value_counts().head(12).reset_index()
    tipo_cnt.columns = ["Tipo", "Cantidad"]

    BLUES = [C["azul1"], C["azul2"], C["azul3"], "#7AB0D8", "#9DC3E6",
             C["azul4"], "#D0E5F5", "#A8CEEB", "#5490C0", "#3A6EA5",
             "#2860A0", "#1D5090"]
    fig = go.Figure(go.Bar(
        x=tipo_cnt["Cantidad"], y=tipo_cnt["Tipo"], orientation="h",
        marker=dict(color=BLUES[:len(tipo_cnt)]),
        text=tipo_cnt["Cantidad"], textposition="outside",
        textfont=dict(size=10, color=C["gris2"]),
        hovertemplate="<b>%{y}</b><br>%{x:,} equipos<extra></extra>",
    ))
    chart_layout(fig, "Top 12 Tipos de Equipo", height=360, show_legend=False,
                 margin=dict(l=8,r=40,t=48,b=8))
    fig.update_layout(yaxis=dict(showgrid=False), xaxis=dict(showgrid=True, gridcolor=C["gris4"]))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

with col_e:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    estado_cnt = df["Estado del Equipo (Operativo / Inoperativo)"].value_counts().reset_index()
    estado_cnt.columns = ["Estado", "Cantidad"]
    color_map = {
        "OPERATIVO":          C["verde3"],
        "INOPERATIVO":        C["rojo2"],
        "OPERATIVO OBSERVADO":C["naranja"],
        "NO DEFINIDO":        C["gris3"],
    }
    fig = go.Figure(go.Pie(
        labels=estado_cnt["Estado"], values=estado_cnt["Cantidad"],
        marker=dict(
            colors=[color_map.get(e, C["azul3"]) for e in estado_cnt["Estado"]],
            line=dict(color=C["blanco"], width=2)
        ),
        textinfo="percent", textfont=dict(size=11, family=FONT),
        hovertemplate="<b>%{label}</b><br>%{value:,} equipos (%{percent})<extra></extra>",
        pull=[0.04 if e == "INOPERATIVO" else 0 for e in estado_cnt["Estado"]],
    ))
    fig.update_layout(
        title=dict(text="Estado Operativo de Equipos",
                   font=dict(family=FONT, size=13, color=C["azul1"]),
                   x=0, xanchor="left", pad=dict(l=4)),
        height=360, margin=dict(l=8,r=8,t=48,b=8),
        paper_bgcolor=C["blanco"], plot_bgcolor=C["blanco"],
        legend=dict(orientation="v", x=1, y=0.5, font=dict(size=10, family=FONT)),
        hoverlabel=dict(bgcolor=C["azul1"], font_color=C["blanco"], font_family=FONT),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

# ── Tabla ──────────────────────────────────────────────────────────────────────
st.markdown('<div class="sec-hdr">Datos Detallados</div>', unsafe_allow_html=True)

cols_tabla = [
    "Orden PAM 2026", "CodigoEquipo", "Inmueble", "TipoEquipo",
    "NombreGrupoMantenimiento", "Región", "Mes",
    "Estado del Equipo (Operativo / Inoperativo)",
    "Programado", "Ejecutado", "Acta", "Informe", "C.O.", "Completo",
    "INGRESO UNITARIO 2", "GASTO", "Utilidad",
    "Proveedor", "Fecha Inicio", "Fecha Fin",
]
cols_tabla = [c for c in cols_tabla if c in df.columns]

busqueda = st.text_input("🔍  Buscar en la tabla (Inmueble, Código, Tipo, Proveedor...)", "")
df_tabla = df[cols_tabla].copy()
if busqueda:
    mask = df_tabla.astype(str).apply(
        lambda col: col.str.contains(busqueda, case=False, na=False)
    ).any(axis=1)
    df_tabla = df_tabla[mask]

st.dataframe(
    df_tabla.reset_index(drop=True),
    use_container_width=True, height=440,
    column_config={
        "INGRESO UNITARIO 2": st.column_config.NumberColumn("Ingreso (S/)", format="S/ %.2f"),
        "GASTO":              st.column_config.NumberColumn("Gasto (S/)",   format="S/ %.2f"),
        "Utilidad":           st.column_config.NumberColumn("Utilidad (S/)",format="S/ %.2f"),
        "Fecha Inicio":       st.column_config.DateColumn("Fecha Inicio",   format="DD/MM/YYYY"),
        "Fecha Fin":          st.column_config.DateColumn("Fecha Fin",      format="DD/MM/YYYY"),
    }
)
st.markdown(f"<span style='color:{C['gris2']};font-size:0.85rem'><b>{len(df_tabla):,}</b> registros mostrados</span>",
            unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
csv = df_tabla.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    "⬇️  Descargar tabla filtrada (CSV)", data=csv,
    file_name="pamp_2026_filtrado.csv", mime="text/csv",
)
