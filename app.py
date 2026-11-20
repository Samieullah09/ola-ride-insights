import base64
import glob
import os
from pathlib import Path
import sqlite3

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from queries import QUERIES

BASE = Path(__file__).parent  # all files are looked up next to app.py, wherever you run it from


def find_file(name):
    # look for an image in assets/, icons/, logo/ or beside app.py
    for folder in ("assets", "icons", "logo", ""):
        p = BASE / folder / name
        if p.exists():
            return p
    return None


st.set_page_config(page_title="Ola Ride Insights", page_icon=str(find_file("ola_logo_circle.png") or "🚖"),
                   layout="wide", initial_sidebar_state="expanded")

# Paste your Power BI "Publish to web" link here (leave empty to show screenshots only)
POWERBI_URL = ""

# ---------- theme: deep space navy + cyan / violet / pink ----------
CYAN, VIOLET, PINK, MINT, AMBER, SLATE = "#22D3EE", "#A78BFA", "#F472B6", "#34D399", "#FBBF24", "#64748B"
TEXT, MUTED, GRID = "#E6EDF7", "#8A97B1", "rgba(148,163,184,.14)"
STATUS_COLORS = {"Success": CYAN, "Canceled by Driver": AMBER, "Canceled by Customer": PINK, "Driver Not Found": SLATE}
VEHICLE_COLORS = [CYAN, VIOLET, PINK, MINT, AMBER, "#60A5FA", "#FB7185"]
ICONS = {"Prime Sedan": "prime_sedan", "Prime SUV": "prime_suv", "Prime Plus": "prime_plus",
         "Mini": "mini", "Auto": "auto", "Bike": "bike", "eBike": "ebike"}
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
SLOTS = ["Late Night", "Morning", "Afternoon", "Evening", "Night"]

# width="stretch" needs Streamlit 1.50+, older versions use use_container_width
STRETCH = {"width": "stretch"} if tuple(int(x) for x in st.__version__.split(".")[:2]) >= (1, 50) \
    else {"use_container_width": True}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=JetBrains+Mono:wght@400;600&family=Inter:wght@400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #050816; }

/* ---- animated aurora + grid background (slow, soft glow) ---- */
.stApp::before { content:""; position:fixed; inset:-20%; z-index:0; pointer-events:none;
  background:
    radial-gradient(500px 420px at 15% 20%, rgba(34,211,238,.16), transparent 70%),
    radial-gradient(560px 460px at 85% 15%, rgba(167,139,250,.18), transparent 70%),
    radial-gradient(520px 440px at 70% 90%, rgba(244,114,182,.12), transparent 70%);
  animation: aurora 16s ease-in-out infinite alternate; }
.stApp::after { content:""; position:fixed; inset:0; z-index:0; pointer-events:none;
  background-image: linear-gradient(rgba(148,163,184,.05) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(148,163,184,.05) 1px, transparent 1px);
  background-size: 56px 56px;
  -webkit-mask-image: radial-gradient(ellipse at 50% 30%, #000 30%, transparent 85%);
          mask-image: radial-gradient(ellipse at 50% 30%, #000 30%, transparent 85%);
  animation: breathe 8s ease-in-out infinite alternate; }
@keyframes aurora { from { transform: translate3d(-2%, -1%, 0) scale(1); } to { transform: translate3d(3%, 2%, 0) scale(1.08); } }
@keyframes breathe { from { opacity:.35; } to { opacity:1; } }

.block-container { padding-top: 1.1rem; max-width: 1560px; position: relative; z-index: 1; }
header[data-testid="stHeader"] { background: transparent; }
h1,h2,h3 { font-family: 'Orbitron', sans-serif !important; color: #E6EDF7; letter-spacing: .05em; }

/* ---- sidebar ---- */
section[data-testid="stSidebar"] { background: linear-gradient(180deg,#0A1024,#070B1A); border-right: 1px solid rgba(34,211,238,.18); }
section[data-testid="stSidebar"] > div { padding-top: .6rem; }
.sb-logo { text-align:center; padding:6px 0 2px; }
.sb-logo img { width:78px; filter: drop-shadow(0 0 14px rgba(34,211,238,.55)); animation: pulse 3.5s ease-in-out infinite; }
@keyframes pulse { 50% { filter: drop-shadow(0 0 26px rgba(167,139,250,.8)); } }
.sb-title { font-family:'Orbitron',sans-serif; text-align:center; letter-spacing:.28em; font-size:13px; color:#22D3EE; margin:4px 0 2px; }
.sb-sub { text-align:center; font-family:'JetBrains Mono',monospace; font-size:10px; color:#8A97B1; letter-spacing:.14em; margin-bottom:10px; }
.sb-sec { font-family:'JetBrains Mono',monospace; font-size:11px; letter-spacing:.16em; color:#8A97B1; text-transform:uppercase; margin:16px 0 4px; }
.sb-sec::before { content:"◆ "; color:#A78BFA; }
.sb-card { margin-top:14px; margin-bottom:16px; padding:14px 16px; border-radius:14px; border:1px solid rgba(34,211,238,.28);
  background: linear-gradient(160deg, rgba(34,211,238,.10), rgba(167,139,250,.08)); box-shadow: 0 0 24px rgba(34,211,238,.10); }
.sb-card .n { font-family:'Orbitron',sans-serif; font-size:22px; color:#E6EDF7; }
.sb-card .m { font-family:'JetBrains Mono',monospace; font-size:11px; color:#8A97B1; }
.sb-bar { height:6px; border-radius:6px; background:rgba(148,163,184,.18); margin-top:10px; overflow:hidden; }
.sb-bar > div { height:100%; border-radius:6px; background: linear-gradient(90deg,#22D3EE,#A78BFA,#F472B6); box-shadow:0 0 10px #22D3EE; }
span[data-baseweb="tag"] { background: rgba(34,211,238,.16) !important; border:1px solid rgba(34,211,238,.35); }
span[data-baseweb="tag"] span { color:#E6EDF7 !important; }
div[data-baseweb="select"] > div, div[data-testid="stDateInput"] > div > div { background:#0B1226 !important; border-color: rgba(148,163,184,.25) !important; }
.stButton > button, .stDownloadButton > button { border:1px solid rgba(34,211,238,.45); background: rgba(34,211,238,.08);
  color:#E6EDF7; border-radius:10px; transition: all .25s; }
.stButton > button:hover, .stDownloadButton > button:hover { border-color:#22D3EE; box-shadow:0 0 18px rgba(34,211,238,.45); color:#fff; }

/* ---- hero ---- */
.hero { position:relative; display:flex; align-items:center; gap:24px; padding:16px 24px; margin-bottom:16px; border-radius:18px;
  background: linear-gradient(100deg, rgba(15,23,42,.92), rgba(11,18,38,.85)); overflow:hidden;
  border:1px solid rgba(34,211,238,.25); box-shadow: 0 0 40px rgba(34,211,238,.10), inset 0 0 40px rgba(167,139,250,.05); }
.hero::after { content:""; position:absolute; left:0; right:0; bottom:0; height:2px;
  background: linear-gradient(90deg, transparent, #22D3EE, #A78BFA, #F472B6, transparent); box-shadow:0 0 14px #22D3EE; animation: breathe 4s ease-in-out infinite alternate; }
.hero img { height:46px; filter: drop-shadow(0 0 10px rgba(34,211,238,.6)); }
.hero .t { font-family:'Orbitron',sans-serif; font-size:20px; letter-spacing:.2em; color:#E6EDF7; }
.hero .s { font-family:'JetBrains Mono',monospace; font-size:11px; letter-spacing:.2em; color:#8A97B1; margin-top:3px; }
.hero .live { margin-left:auto; font-family:'JetBrains Mono',monospace; font-size:12px; color:#22D3EE; padding:7px 14px;
  border:1px solid rgba(34,211,238,.4); border-radius:999px; background:rgba(34,211,238,.08); }
.hero .live::before { content:""; display:inline-block; width:8px; height:8px; border-radius:50%; background:#34D399;
  margin-right:9px; box-shadow:0 0 10px #34D399; animation: blink 1.6s infinite; }
@keyframes blink { 50% { opacity:.25; } }

/* ---- KPI + vehicle cards ---- */
.kpi { --c:#22D3EE; min-height:112px; padding:14px 18px; border-radius:16px; position:relative; overflow:hidden;
  background: linear-gradient(160deg, rgba(15,23,42,.88), rgba(11,18,38,.78)); border:1px solid rgba(148,163,184,.18); transition: all .28s; }
.kpi::before { content:""; position:absolute; left:0; top:0; right:0; height:2px; background:var(--c); box-shadow:0 0 14px var(--c); }
.kpi:hover { transform: translateY(-3px); border-color:var(--c); box-shadow: 0 0 26px color-mix(in srgb, var(--c) 40%, transparent); }
.kpi .l { font-family:'JetBrains Mono',monospace; font-size:10px; letter-spacing:.14em; color:#8A97B1; text-transform:uppercase; }
.kpi .v { font-family:'Orbitron',sans-serif; font-size:26px; color:#E6EDF7; margin-top:6px; text-shadow:0 0 18px color-mix(in srgb, var(--c) 55%, transparent); }
.kpi .s { font-size:12px; color:#8A97B1; margin-top:3px; }
.vcard { text-align:center; padding:14px 6px 12px; border-radius:16px; background: linear-gradient(160deg, rgba(15,23,42,.88), rgba(11,18,38,.78));
  border:1px solid rgba(148,163,184,.18); transition: all .28s; }
.vcard:hover { border-color:#A78BFA; box-shadow:0 0 24px rgba(167,139,250,.35); transform:translateY(-4px); }
.vcard img { height:42px; margin-bottom:6px; filter: drop-shadow(0 0 8px rgba(34,211,238,.45)); }
.vcard .n { font-size:13px; color:#E6EDF7; font-weight:600; }
.vcard .m { font-family:'JetBrains Mono',monospace; font-size:11px; color:#8A97B1; line-height:1.5; }

.ptitle { font-family:'JetBrains Mono',monospace; font-size:12px; letter-spacing:.16em; color:#8A97B1; text-transform:uppercase; margin:22px 0 4px 2px; }
.ptitle::before { content:"◆ "; color:#22D3EE; text-shadow:0 0 8px #22D3EE; }
.insight { border-left:3px solid #A78BFA; background: linear-gradient(90deg, rgba(167,139,250,.12), rgba(15,23,42,.4)); padding:11px 16px;
  border-radius:0 12px 12px 0; color:#C7D2E6; font-size:14px; margin:12px 0 4px; }
.insight b { color:#22D3EE; }

/* ---- tabs ---- */
div[data-baseweb="tab-list"] { gap:6px; border-bottom:1px solid rgba(148,163,184,.15); }
button[data-baseweb="tab"] { font-family:'JetBrains Mono',monospace; letter-spacing:.08em; color:#8A97B1; border-radius:10px 10px 0 0; padding:10px 16px; }
button[data-baseweb="tab"]:hover { color:#E6EDF7; background:rgba(34,211,238,.06); }
button[data-baseweb="tab"][aria-selected="true"] { color:#22D3EE; background:rgba(34,211,238,.08); text-shadow:0 0 10px rgba(34,211,238,.7); }
div[data-baseweb="tab-highlight"] { background: linear-gradient(90deg,#22D3EE,#A78BFA); box-shadow:0 0 12px #22D3EE; height:3px; }
[data-testid="stDataFrame"] { border:1px solid rgba(148,163,184,.2); border-radius:12px; }
[data-testid="stPlotlyChart"] { border:1px solid rgba(148,163,184,.12); border-radius:16px; background: rgba(11,18,38,.45); padding:6px 4px 0; }
.foot { text-align:center; color:#5B6784; font-family:'JetBrains Mono',monospace; font-size:11px; letter-spacing:.14em; margin:34px 0 6px; }
</style>
"""


# ---------- data ----------
@st.cache_data
def load_data():
    df = pd.read_csv(BASE / "ola_clean.csv", parse_dates=["Date"])
    df["Day"] = df["Date"].dt.date
    df["Route"] = df["Pickup_Location"] + " → " + df["Drop_Location"]
    return df


@st.cache_resource
def get_connection():
    # In-memory SQLite copy of the table, so the SQL tab works anywhere (no MySQL needed)
    df = load_data().drop(columns=["Time", "Day", "Route"]).rename(columns={"Date": "Booking_DateTime"})
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    df.to_sql("bookings", conn, index=False)
    return conn


@st.cache_data
def img64(name):
    p = find_file(os.path.basename(name))
    if p is None:  # missing image: return a 1px transparent PNG instead of crashing
        return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    return base64.b64encode(p.read_bytes()).decode()


# ---------- helpers ----------
def inr(x):
    if x >= 1e7:
        return f"₹{x / 1e7:.2f} Cr"
    if x >= 1e5:
        return f"₹{x / 1e5:.2f} L"
    return f"₹{x:,.0f}"


def kpi(col, label, value, sub="", color=CYAN):
    col.markdown(f'<div class="kpi" style="--c:{color}"><div class="l">{label}</div><div class="v">{value}</div>'
                 f'<div class="s">{sub or "&nbsp;"}</div></div>', unsafe_allow_html=True)


def title(text):
    st.markdown(f'<div class="ptitle">{text}</div>', unsafe_allow_html=True)


def insight(html):
    st.markdown(f'<div class="insight">{html}</div>', unsafe_allow_html=True)


CHART_NO = [0]  # counter so every chart gets its own unique key


def show(fig, height=340, legend=True):
    CHART_NO[0] += 1
    fig.update_layout(
        height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", colorway=VEHICLE_COLORS,
        font=dict(color="#C7D2E6", family="Inter"), margin=dict(l=10, r=50, t=26, b=10), showlegend=legend,
        legend=dict(orientation="h", y=-0.22, title=None), hoverlabel=dict(bgcolor="#0B1226", font_color=TEXT, bordercolor=CYAN),
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, title=None)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, title=None)
    st.plotly_chart(fig, config={"displayModeBar": False}, key=f"chart_{CHART_NO[0]}", **STRETCH)


def bar(data, x, y, horizontal=False, color=CYAN, text_fmt=None, **kw):
    fig = px.bar(data, x=y if horizontal else x, y=x if horizontal else y,
                 orientation="h" if horizontal else "v", color_discrete_sequence=[color], **kw)
    fig.update_traces(marker_line_width=1, marker_line_color=color, opacity=.9, textposition="outside",
                      textfont_color="#C7D2E6", texttemplate=text_fmt, cliponaxis=False)
    if horizontal:
        fig.update_yaxes(autorange="reversed")
    return fig


def glow_line(fig, x, y, color, name=None):
    # a wide faint line under a thin bright one gives a neon glow
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines", line=dict(color=color, width=9), opacity=.18, hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines", line=dict(color=color, width=2.4), name=name,
                             fill="tozeroy"))


# ---------- sidebar filters ----------
def reset_filters():
    for k in ("f_vehicle", "f_status", "f_slot", "f_day", "f_date"):
        st.session_state.pop(k, None)


def sidebar_filters(df):
    sb = st.sidebar
    sb.markdown(f'<div class="sb-logo"><img src="data:image/png;base64,{img64("assets/ola_logo_circle.png")}"></div>'
                '<div class="sb-title">CONTROL PANEL</div><div class="sb-sub">FILTER EVERYTHING · LIVE</div>',
                unsafe_allow_html=True)
    dmin, dmax = df["Day"].min(), df["Day"].max()

    sb.markdown('<div class="sb-sec">Date range</div>', unsafe_allow_html=True)
    picked = sb.date_input("Date range", (dmin, dmax), min_value=dmin, max_value=dmax, key="f_date", label_visibility="collapsed")
    start, end = (picked[0], picked[-1]) if len(picked) else (dmin, dmax)

    sb.markdown('<div class="sb-sec">Vehicle type</div>', unsafe_allow_html=True)
    veh = sb.multiselect("Vehicle type", sorted(df["Vehicle_Type"].unique()), key="f_vehicle",
                         placeholder="All vehicles", label_visibility="collapsed")
    sb.markdown('<div class="sb-sec">Booking status</div>', unsafe_allow_html=True)
    sta = sb.multiselect("Booking status", sorted(df["Booking_Status"].unique()), key="f_status",
                         placeholder="All statuses", label_visibility="collapsed")
    sb.markdown('<div class="sb-sec">Time of day</div>', unsafe_allow_html=True)
    slot = sb.multiselect("Time of day", SLOTS, key="f_slot", placeholder="Any time", label_visibility="collapsed")
    sb.markdown('<div class="sb-sec">Day of week</div>', unsafe_allow_html=True)
    day = sb.multiselect("Day of week", DAYS, key="f_day", placeholder="Every day", label_visibility="collapsed")
    sb.button("↺  Reset all filters", on_click=reset_filters, **STRETCH)

    m = (df["Day"] >= start) & (df["Day"] <= end)
    for col, chosen in (("Vehicle_Type", veh), ("Booking_Status", sta), ("Time_Slot", slot), ("Day_Name", day)):
        if chosen:  # empty selection means "no filter"
            m &= df[col].isin(chosen)
    out = df[m]
    pct = len(out) / len(df)
    sb.markdown(f'<div class="sb-card"><div class="n">{len(out):,}</div><div class="m">of {len(df):,} rides in view · {pct:.0%}</div>'
                f'<div class="sb-bar"><div style="width:{max(pct * 100, 1.5):.1f}%"></div></div></div>', unsafe_allow_html=True)
    sb.download_button("⬇  Download filtered data", out.drop(columns=["Day", "Route"]).to_csv(index=False),
                       "ola_filtered.csv", "text/csv", **STRETCH)
    sb.caption("Empty filter = show all")
    return out


# ---------- tabs ----------
def tab_overview(d):
    ok = d[d["Booking_Status"] == "Success"]
    c = st.columns(6)
    kpi(c[0], "Total rides", f"{len(d):,}", color=CYAN)
    kpi(c[1], "Success rate", f"{len(ok) / len(d):.1%}", f"{len(ok):,} completed", MINT)
    kpi(c[2], "Success revenue", inr(ok["Booking_Value"].sum()), color=VIOLET)
    kpi(c[3], "Avg booking value", f"₹{ok['Booking_Value'].mean():,.0f}", "successful rides", PINK)
    kpi(c[4], "Total distance", f"{ok['Ride_Distance'].sum() / 1e5:.1f} L km", "successful rides", AMBER)
    kpi(c[5], "Avg driver rating", f"{d['Driver_Ratings'].mean():.2f}", "out of 5", CYAN)

    a, b = st.columns([1.7, 1])
    with a:
        title("Ride volume per day")
        daily = d.groupby("Day").size().reset_index(name="Rides")
        fig = go.Figure()
        glow_line(fig, daily["Day"], daily["Rides"], CYAN)
        fig.update_traces(fillcolor="rgba(34,211,238,.10)", selector=dict(fill="tozeroy"))
        fig.update_yaxes(rangemode="tozero")
        show(fig, 350, legend=False)
    with b:
        title("Booking status")
        s = d["Booking_Status"].value_counts().reset_index()
        fig = px.pie(s, names="Booking_Status", values="count", hole=0.68,
                     color="Booking_Status", color_discrete_map=STATUS_COLORS)
        fig.update_traces(textinfo="percent", marker_line_color="#050816", marker_line_width=3)
        fig.add_annotation(text=f"<b>{len(d):,}</b><br><span style='font-size:11px;color:#8A97B1'>RIDES</span>",
                           showarrow=False, font=dict(size=22, color=TEXT))
        show(fig, 350)

    a, b = st.columns(2)
    with a:
        title("Hourly demand")
        hr = d.groupby("Hour").size().reindex(range(24), fill_value=0).reset_index(name="Rides")
        peak = hr.loc[hr["Rides"].idxmax()]
        fig = bar(hr, "Hour", "Rides")
        fig.update_traces(texttemplate=None, marker_color=[AMBER if h == peak["Hour"] else CYAN for h in hr["Hour"]],
                          marker_line_color=[AMBER if h == peak["Hour"] else CYAN for h in hr["Hour"]])
        fig.update_xaxes(dtick=2)
        show(fig, 320, legend=False)
        insight(f"Peak hour is <b>{int(peak['Hour']):02d}:00</b> with {int(peak['Rides']):,} bookings.")
    with b:
        title("Top 10 pickup locations")
        p = d["Pickup_Location"].value_counts().head(10).reset_index()
        show(bar(p, "Pickup_Location", "count", horizontal=True, color=VIOLET, text_fmt="%{x:,}"), 320, legend=False)
        insight(f"<b>{p.iloc[0, 0]}</b> is the busiest pickup point ({p.iloc[0, 1]:,} bookings).")


def tab_vehicles(d):
    ok = d[d["Booking_Status"] == "Success"]
    g = ok.groupby("Vehicle_Type").agg(Rides=("Booking_ID", "count"), Dist=("Ride_Distance", "sum"),
                                       AvgDist=("Ride_Distance", "mean"), Value=("Booking_Value", "sum"),
                                       CustRating=("Customer_Rating", "mean")).reset_index()
    title("Fleet snapshot (successful rides)")
    cols = st.columns(7)
    for col, name in zip(cols, ICONS):
        row = g[g["Vehicle_Type"] == name]
        if row.empty:
            continue
        r = row.iloc[0]
        col.markdown(f'<div class="vcard"><img src="data:image/png;base64,{img64(f"assets/{ICONS[name]}.png")}">'
                     f'<div class="n">{name}</div><div class="m">{int(r.Rides):,} rides<br>{r.AvgDist:.1f} km avg</div></div>',
                     unsafe_allow_html=True)

    a, b = st.columns(2)
    with a:
        title("Top 5 vehicle types by ride distance (km)")
        show(bar(g.nlargest(5, "Dist"), "Vehicle_Type", "Dist", horizontal=True, text_fmt="%{x:,.0f}"), legend=False)
    with b:
        title("Average customer rating by vehicle type")
        s = g.sort_values("CustRating", ascending=False)
        fig = bar(s, "Vehicle_Type", "CustRating", color=VIOLET, text_fmt="%{y:.2f}")
        fig.update_yaxes(range=[0, 5])
        show(fig, legend=False)
    a, b = st.columns(2)
    with a:
        title("Average ride distance by vehicle type (km)")
        s = g.sort_values("AvgDist", ascending=False)
        fig = bar(s, "Vehicle_Type", "AvgDist", text_fmt="%{y:.1f}")
        cols_ = [AMBER if v < 15 else CYAN for v in s["AvgDist"]]
        fig.update_traces(marker_color=cols_, marker_line_color=cols_)
        show(fig, legend=False)
    with b:
        title("Successful booking value by vehicle type")
        show(bar(g.sort_values("Value", ascending=False), "Vehicle_Type", "Value", color=PINK, text_fmt="%{y:.3s}"), legend=False)
    short = g[g["AvgDist"] < 15]
    if len(short):
        insight(f"<b>{short.iloc[0].Vehicle_Type}</b> trips are short: {short.iloc[0].AvgDist:.1f} km on average "
                f"vs about 25 km for the other vehicles.")


def tab_revenue(d):
    ok = d[d["Booking_Status"] == "Success"]
    pay = ok[ok["Payment_Method"] != "Not Applicable"].groupby("Payment_Method")["Booking_Value"].sum().reset_index()
    top = pay.loc[pay["Booking_Value"].idxmax()]
    c = st.columns(4)
    kpi(c[0], "Success revenue", inr(ok["Booking_Value"].sum()), color=CYAN)
    kpi(c[1], "Avg successful booking", f"₹{ok['Booking_Value'].mean():,.0f}", color=MINT)
    kpi(c[2], "Top payment method", top["Payment_Method"], f"{top['Booking_Value'] / pay['Booking_Value'].sum():.0%} of revenue", VIOLET)
    kpi(c[3], "Best distance day", str(ok.groupby("Day")["Ride_Distance"].sum().idxmax()), color=AMBER)

    a, b, c3 = st.columns(3)
    with a:
        title("Revenue by payment method")
        show(bar(pay.sort_values("Booking_Value"), "Payment_Method", "Booking_Value", horizontal=True, text_fmt="%{x:.3s}"), legend=False)
    with b:
        title("Payment contribution %")
        fig = px.pie(pay, names="Payment_Method", values="Booking_Value", hole=0.65, color_discrete_sequence=[CYAN, VIOLET, PINK, AMBER])
        fig.update_traces(textinfo="percent", marker_line_color="#050816", marker_line_width=3)
        show(fig)
    with c3:
        title("Top 5 customers by booking value")
        t = ok.groupby("Customer_ID")["Booking_Value"].sum().nlargest(5).reset_index()
        show(bar(t, "Customer_ID", "Booking_Value", horizontal=True, color=PINK, text_fmt="%{x:,.0f}"), legend=False)
    a, b = st.columns([1.4, 1])
    with a:
        title("Ride distance per day (km)")
        dist = ok.groupby("Day")["Ride_Distance"].sum().reset_index()
        show(bar(dist, "Day", "Ride_Distance"), legend=False)
    with b:
        title("Revenue by vehicle type")
        v = ok.groupby("Vehicle_Type")["Booking_Value"].sum().sort_values().reset_index()
        show(bar(v, "Vehicle_Type", "Booking_Value", horizontal=True, color=MINT, text_fmt="%{x:.3s}"), legend=False)
    cum = ok.groupby("Day")["Booking_Value"].sum().cumsum().reset_index()
    title("Cumulative revenue through the month")
    fig = go.Figure()
    glow_line(fig, cum["Day"], cum["Booking_Value"], VIOLET)
    fig.update_traces(fillcolor="rgba(167,139,250,.10)", selector=dict(fill="tozeroy"))
    show(fig, 280, legend=False)


def tab_cancel(d):
    cust = d[d["Booking_Status"] == "Canceled by Customer"]
    drv = d[d["Booking_Status"] == "Canceled by Driver"]
    nf = d[d["Booking_Status"] == "Driver Not Found"]
    inc = d[d["Incomplete_Rides"] == "Yes"]
    c = st.columns(5)
    kpi(c[0], "Cancelled by customer", f"{len(cust):,}", color=PINK)
    kpi(c[1], "Cancelled by driver", f"{len(drv):,}", color=AMBER)
    kpi(c[2], "Driver not found", f"{len(nf):,}", color=SLATE)
    kpi(c[3], "Cancellation rate", f"{(len(cust) + len(drv)) / len(d):.1%}", "customer + driver", VIOLET)
    kpi(c[4], "Incomplete rides", f"{len(inc):,}", color=CYAN)

    a, b = st.columns(2)
    with a:
        title("Cancellation reasons: customers")
        r = cust[cust["Canceled_Rides_by_Customer"] != "Not Applicable"]["Canceled_Rides_by_Customer"].value_counts().reset_index()
        show(bar(r, "Canceled_Rides_by_Customer", "count", horizontal=True, color=PINK, text_fmt="%{x:,}"), 320, legend=False)
    with b:
        title("Cancellation reasons: drivers")
        r = drv[drv["Canceled_Rides_by_Driver"] != "Not Applicable"]["Canceled_Rides_by_Driver"].value_counts().reset_index()
        show(bar(r, "Canceled_Rides_by_Driver", "count", horizontal=True, color=AMBER, text_fmt="%{x:,}"), 320, legend=False)
    both = d[d["Booking_Status"].isin(["Canceled by Customer", "Canceled by Driver"])]
    a, b = st.columns(2)
    with a:
        title("Cancellations by hour")
        h = both.groupby(["Hour", "Booking_Status"]).size().reset_index(name="Rides")
        show(px.bar(h, x="Hour", y="Rides", color="Booking_Status", color_discrete_map=STATUS_COLORS))
    with b:
        title("Cancellations by vehicle type")
        v = both.groupby(["Vehicle_Type", "Booking_Status"]).size().reset_index(name="Rides")
        show(px.bar(v, x="Vehicle_Type", y="Rides", color="Booking_Status", color_discrete_map=STATUS_COLORS))
    title("Incomplete rides: reasons")
    r = inc["Incomplete_Rides_Reason"].value_counts().reset_index()
    a, b = st.columns(2)
    with a:
        show(bar(r, "Incomplete_Rides_Reason", "count", horizontal=True, color=SLATE, text_fmt="%{x:,}"), 270, legend=False)
    with b:
        insight(f"<b>{len(inc):,}</b> rides started but were not completed. Most common reason: <b>{r.iloc[0, 0]}</b>.")


def tab_ratings(d):
    r = d.dropna(subset=["Driver_Ratings"])
    c = st.columns(4)
    kpi(c[0], "Avg driver rating", f"{d['Driver_Ratings'].mean():.2f}", color=CYAN)
    kpi(c[1], "Avg customer rating", f"{d['Customer_Rating'].mean():.2f}", color=PINK)
    kpi(c[2], "Min driver rating", f"{r['Driver_Ratings'].min():.1f}", color=AMBER)
    kpi(c[3], "Max driver rating", f"{r['Driver_Ratings'].max():.1f}", color=MINT)

    a, b = st.columns(2)
    for col, name, label, colr in ((a, "Driver_Ratings", "Driver ratings distribution", CYAN),
                                   (b, "Customer_Rating", "Customer ratings distribution", PINK)):
        with col:
            title(label)
            x = d[name].dropna().round(1).value_counts().sort_index().reset_index()
            x[name] = x[name].map("{:.1f}".format)  # sorted numerically first, then shown as text
            show(bar(x, name, "count", color=colr), legend=False)

    g = d.groupby("Vehicle_Type").agg(Driver=("Driver_Ratings", "mean"), Customer=("Customer_Rating", "mean"),
                                      Min=("Driver_Ratings", "min"), Max=("Driver_Ratings", "max")).reset_index()
    a, b = st.columns([1.3, 1])
    with a:
        title("Customer vs driver rating by vehicle type")
        s = g.sort_values("Driver")
        fig = go.Figure()
        for i, row in s.iterrows():  # dumbbell: the line shows the gap between the two ratings
            fig.add_trace(go.Scatter(x=[row.Driver, row.Customer], y=[row.Vehicle_Type] * 2, mode="lines",
                                     line=dict(color="rgba(148,163,184,.45)", width=3), showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=s["Driver"], y=s["Vehicle_Type"], mode="markers", name="Driver",
                                 marker=dict(color=CYAN, size=15, line=dict(color="#050816", width=2))))
        fig.add_trace(go.Scatter(x=s["Customer"], y=s["Vehicle_Type"], mode="markers", name="Customer",
                                 marker=dict(color=PINK, size=15, line=dict(color="#050816", width=2))))
        lo = min(s["Driver"].min(), s["Customer"].min()) - 0.02
        hi = max(s["Driver"].max(), s["Customer"].max()) + 0.02
        fig.update_xaxes(range=[lo, hi], tickformat=".2f")
        show(fig, 360)
        insight("Axis is zoomed to the 3.9 to 4.1 range, so small gaps are visible. Both sides rate each other close to <b>4.0</b>.")
    with b:
        title("Rating table")
        t = g.rename(columns={"Vehicle_Type": "Vehicle", "Driver": "Avg Driver", "Customer": "Avg Customer",
                              "Min": "Min Driver", "Max": "Max Driver"})
        st.dataframe(t.style.format({"Avg Driver": "{:.2f}", "Avg Customer": "{:.2f}",
                                     "Min Driver": "{:.1f}", "Max Driver": "{:.1f}"}), hide_index=True, **STRETCH)


def tab_hotspots(d):
    title("Demand heatmap: avg rides per day of week × hour")
    # July 2024 has five Mon/Tue/Wed, so divide by the number of such days to compare weekdays fairly
    n_days = d.groupby("Day_Name")["Day"].nunique().reindex(DAYS)
    pv = d.groupby(["Day_Name", "Hour"]).size().unstack(fill_value=0).reindex(DAYS).reindex(columns=range(24), fill_value=0)
    pv = pv.div(n_days, axis=0).fillna(0).round(0)
    fig = go.Figure(go.Heatmap(z=pv.values, x=[f"{h:02d}" for h in pv.columns], y=pv.index, xgap=3, ygap=3,
                               colorscale=[[0, "#0B1226"], [.35, "#2B3A8F"], [.65, "#A78BFA"], [1, "#22D3EE"]],
                               colorbar=dict(thickness=10, len=.8), hovertemplate="%{y} %{x}:00<br>%{z:,.0f} avg rides<extra></extra>"))
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(type="category")
    show(fig, 330, legend=False)
    a, b = st.columns(2)
    with a:
        title("Top 10 routes (pickup → drop)")
        r = d["Route"].value_counts().head(10).reset_index()
        show(bar(r, "Route", "count", horizontal=True, color=MINT, text_fmt="%{x:,}"), 380, legend=False)
    with b:
        title("Rides by time of day")
        t = d.groupby(["Time_Slot", "Booking_Status"]).size().reset_index(name="Rides")
        show(px.bar(t, x="Time_Slot", y="Rides", color="Booking_Status", color_discrete_map=STATUS_COLORS,
                    category_orders={"Time_Slot": SLOTS}), 380)
    a, b = st.columns(2)
    with a:
        title("Top 10 drop locations")
        p = d["Drop_Location"].value_counts().head(10).reset_index()
        show(bar(p, "Drop_Location", "count", horizontal=True, color=VIOLET, text_fmt="%{x:,}"), 340, legend=False)
    with b:
        title("Average rides per day, by weekday")
        w = (d.groupby("Day_Name").size() / n_days).reindex(DAYS).fillna(0).round(0).reset_index(name="Rides")
        show(bar(w, "Day_Name", "Rides", color=PINK), 340, legend=False)


def tab_search(df):
    title("Search rides")
    a, b = st.columns([2, 1])
    text = a.text_input("Booking ID or Customer ID", placeholder="e.g. CID954071 or CNR2940424040")
    area = b.text_input("Pickup or drop area", placeholder="e.g. Whitefield")
    out = df
    if text.strip():  # partial match on either ID, ignoring case
        t = text.strip().upper()
        out = out[out["Booking_ID"].str.upper().str.contains(t, regex=False)
                  | out["Customer_ID"].str.upper().str.contains(t, regex=False)]
    if area.strip():  # partial match on pickup or drop location
        k = area.strip().lower()
        out = out[out["Pickup_Location"].str.lower().str.contains(k, regex=False)
                  | out["Drop_Location"].str.lower().str.contains(k, regex=False)]
    if not (text.strip() or area.strip()):
        st.info("Type a Booking ID, a Customer ID or an area name to search all 103,024 rides.")
        return
    st.caption(f"{len(out):,} rides found (showing up to 500)")
    cols = ["Booking_ID", "Date", "Customer_ID", "Vehicle_Type", "Booking_Status", "Pickup_Location",
            "Drop_Location", "Booking_Value", "Payment_Method", "Ride_Distance"]
    st.dataframe(out[cols].head(500), hide_index=True, **STRETCH)
    if len(out) == 1:  # one match: show every field of the booking
        title("Booking details")
        st.dataframe(out.drop(columns=["Day", "Route", "Time"]).iloc[0].astype(str).to_frame("Value"), **STRETCH)


def tab_sql():
    title("SQL queries from the brief")
    name = st.selectbox("Choose a question", list(QUERIES), label_visibility="collapsed")
    query = QUERIES[name]
    st.code(query, language="sql")
    result = pd.read_sql_query(query, get_connection())
    st.caption(f"{len(result):,} rows")
    st.dataframe(result, **STRETCH)
    st.download_button("Download result as CSV", result.to_csv(index=False), "result.csv", "text/csv")

    title("SQL playground (read-only)")
    with st.expander("Table `bookings` columns"):
        cols = pd.read_sql_query("PRAGMA table_info(bookings)", get_connection())[["name", "type"]]
        st.dataframe(cols, hide_index=True, **STRETCH)
    custom = st.text_area("Write your own SELECT query on the table `bookings`",
                          "SELECT Vehicle_Type, COUNT(*) AS Rides\nFROM bookings\nGROUP BY Vehicle_Type\nORDER BY Rides DESC",
                          height=120)
    if st.button("▶  Run query"):
        if not custom.strip().lower().startswith("select"):
            st.error("Only SELECT queries are allowed.")
        else:
            try:
                out = pd.read_sql_query(custom, get_connection())
                st.dataframe(out.head(1000), **STRETCH)
            except Exception as e:
                st.error(f"Query failed: {e}")


def tab_powerbi():
    title("Power BI dashboard")
    if POWERBI_URL:
        components.iframe(POWERBI_URL, height=720)
    # Screenshots saved as dashboard/1_overall.png, dashboard/2_vehicle_type.png, ...
    files = sorted(glob.glob(str(BASE / "dashboard" / "*.png")))
    if files:
        names = [os.path.splitext(os.path.basename(f))[0].split("_", 1)[-1].replace("_", " ").title() for f in files]
        for tab, file in zip(st.tabs(names), files):
            tab.image(file)
        st.caption("Static screenshots of the dashboard. The interactive version is in powerbi/dashboard.pbix (open in Power BI Desktop).")
    elif not POWERBI_URL:
        st.info("Add a Power BI link in POWERBI_URL, or put the 5 page screenshots in the dashboard folder "
                "(1_overall.png, 2_vehicle_type.png, 3_revenue.png, 4_cancellation.png, 5_ratings.png).")


def main():
    CHART_NO[0] = 0
    st.markdown(CSS, unsafe_allow_html=True)
    df = load_data()
    data = sidebar_filters(df)
    st.markdown(f'<div class="hero"><img src="data:image/png;base64,{img64("assets/ola_wordmark_white.png")}">'
                f'<div><div class="t">RIDE INSIGHTS</div><div class="s">JULY 2024 · BENGALURU · {len(df):,} BOOKINGS</div></div>'
                f'<span class="live">{len(data):,} RIDES IN VIEW</span></div>', unsafe_allow_html=True)
    if data.empty:
        st.warning("No rides match these filters. Use 'Reset all filters' in the sidebar.")
        data = None

    names = ["Overview", "Vehicles", "Revenue", "Cancellations", "Ratings", "Hotspots", "Search", "SQL Lab", "Power BI"]
    tabs = st.tabs(names)
    for tab, fn in zip(tabs[:6], [tab_overview, tab_vehicles, tab_revenue, tab_cancel, tab_ratings, tab_hotspots]):
        with tab:
            if data is not None:
                fn(data)
    with tabs[6]:
        tab_search(df)
    with tabs[7]:
        tab_sql()
    with tabs[8]:
        tab_powerbi()
    st.markdown('<div class="foot">OLA RIDE INSIGHTS · BUILT BY SAMIEULLAH KHAN · PYTHON · SQL · POWER BI · STREAMLIT</div>',
                unsafe_allow_html=True)


if __name__ == "__main__":
    main()