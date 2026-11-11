#!/usr/bin/env python3
"""
gerar_site.py
Gera docs/index.html com as duas animações do TCC (Modelos 1 e 2 do GeoGebra),
recriadas em Python (NumPy + Plotly).

Uso:
    pip install plotly numpy
    python gerar_site.py
Depois publique a pasta docs/ com o GitHub Pages.

Parâmetros extraídos dos arquivos .ggb:
    Modelo 1: raio da órbita da Terra = 1, raio da órbita da Lua = 0,25 (exagerado),
              inclinação da órbita lunar = 5,145°, inclinação do eixo da Terra = 23,44°,
              razão Lua/Terra = 0,731936 / 0,05475 ≈ 13,37 voltas por ano.
    Modelo 2: esfera celeste de raio 1 centrada no observador, polo celeste sul a ~11,31°
              de altura (latitude ≈ -11,31°), obliquidade 23°26', órbita da Lua inclinada
              5°9' com regressão dos nodos (período 18,6 anos), Sol/Lua com razões de
              velocidade 1 : 13,37 : 366,25 em relação à rotação diária.
"""
import os
from datetime import datetime

import numpy as np
import plotly.graph_objects as go

DEG = np.pi / 180.0
ANO = 365.2422        # dias
MES_SIDERAL = 27.3217  # dias
MES_SINODICO = 29.5306
DIA_SIDERAL = 23.9345  # horas
REGRESSAO_NODOS = 6798.4  # dias (18,61 anos)

FONTE = "system-ui, -apple-system, Segoe UI, Roboto, sans-serif"


def nome_fase(elong):
    """Nome da fase da Lua a partir da elongação (0° = nova, 180° = cheia)."""
    e = elong % 360
    if e < 7 or e >= 353:
        return "Lua nova"
    if e < 83:
        return "Lua crescente"
    if e < 97:
        return "Quarto crescente"
    if e < 173:
        return "Lua gibosa crescente"
    if e < 187:
        return "Lua cheia"
    if e < 263:
        return "Lua gibosa minguante"
    if e < 277:
        return "Quarto minguante"
    return "Lua minguante"



def arredondar(fig, casas=4):
    """Reduz o tamanho do HTML arredondando as coordenadas (diferença invisível na tela)."""
    def arr(tr):
        for eixo in ("x", "y", "z"):
            v = getattr(tr, eixo, None)
            if v is not None and not isinstance(v, str):
                try:
                    setattr(tr, eixo, np.round(np.asarray(v, dtype=float), casas).tolist())
                except (TypeError, ValueError):
                    pass
    for tr in fig.data:
        arr(tr)
    for fr in fig.frames:
        for tr in fr.data:
            arr(tr)
    return fig


def botoes_e_slider(passos, duracao_ms, tam_rotulo=11):
    return dict(
        updatemenus=[dict(
            type="buttons", direction="left", x=0.0, y=-0.02, xanchor="left", yanchor="top",
            pad=dict(r=6, t=6),
            buttons=[
                dict(label="▶ Reproduzir", method="animate",
                     args=[None, dict(frame=dict(duration=duracao_ms, redraw=True),
                                      transition=dict(duration=0), fromcurrent=True,
                                      mode="immediate")]),
                dict(label="⏸ Pausar", method="animate",
                     args=[[None], dict(frame=dict(duration=0, redraw=False),
                                        transition=dict(duration=0), mode="immediate")]),
            ])],
        sliders=[dict(
            active=0, x=0.18, y=-0.02, len=0.8, xanchor="left", yanchor="top",
            pad=dict(t=6, b=6), font=dict(size=tam_rotulo),
            currentvalue=dict(prefix=passos["prefixo"], font=dict(size=13)),
            steps=[dict(label=lab, method="animate",
                        args=[[nome], dict(frame=dict(duration=0, redraw=True),
                                           transition=dict(duration=0), mode="immediate")])
                   for nome, lab in passos["passos"]])],
    )


# ---------------------------------------------------------------------------
# MODELO 1 — Sol, Terra e Lua visto de fora (movimentos de translação)
# ---------------------------------------------------------------------------
INC_LUA = 5.145 * DEG
OBLIQ = 23.44 * DEG
R_LUA = 0.25


def posicoes_modelo1(t):
    """t em dias. Sol na origem, Terra em órbita circular de raio 1 no plano z = 0."""
    th = 2 * np.pi * t / ANO
    terra = np.array([np.cos(th), np.sin(th), 0.0])
    # A órbita da Lua tem plano fixo no espaço (nodos ao longo do eixo y), como no .ggb
    u = np.array([np.cos(INC_LUA), 0.0, np.sin(INC_LUA)])
    v = np.array([0.0, 1.0, 0.0])
    phi = np.pi + 2 * np.pi * t / MES_SIDERAL  # começa em Lua nova
    lua = terra + R_LUA * (np.cos(phi) * u + np.sin(phi) * v)
    return terra, lua, u, v


def info_modelo1(t):
    terra, lua, _, _ = posicoes_modelo1(t)
    d = lua - terra
    lon_sol = np.arctan2(-terra[1], -terra[0])
    lon_lua = np.arctan2(d[1], d[0])
    elong = (np.degrees(lon_lua - lon_sol)) % 360
    ilum = (1 - np.cos(np.radians(elong))) / 2 * 100
    lat = np.degrees(np.arcsin(d[2] / np.linalg.norm(d)))
    perto_conj = elong < 12 or elong > 348
    perto_opos = abs(elong - 180) < 12
    eclipse = ""
    if abs(lat) < 1.6 and perto_conj:
        eclipse = "  •  ⚠ Alinhamento no nodo: possível ECLIPSE SOLAR"
    elif abs(lat) < 1.6 and perto_opos:
        eclipse = "  •  ⚠ Alinhamento no nodo: possível ECLIPSE LUNAR"
    return elong, ilum, lat, eclipse


def figura_modelo1():
    s = np.linspace(0, 2 * np.pi, 361)
    orb_terra = go.Scatter3d(
        x=np.cos(s), y=np.sin(s), z=np.zeros_like(s), mode="lines",
        line=dict(color="rgba(0,150,200,0.6)", width=3, dash="dot"),
        name="Órbita da Terra", hoverinfo="skip")
    # disco da eclíptica (plano translúcido)
    th = np.linspace(0, 2 * np.pi, 61)
    disco = go.Mesh3d(
        x=np.r_[0, np.cos(th)], y=np.r_[0, np.sin(th)], z=np.zeros(62),
        i=[0] * 61, j=list(range(1, 62)), k=[(n % 61) + 1 for n in range(1, 62)],
        color="#9ad7ff", opacity=0.08, name="Plano da eclíptica", hoverinfo="skip",
        showlegend=True)

    s_din = np.linspace(0, 2 * np.pi, 97)

    def dinamicos(t):
        terra, lua, u, v = posicoes_modelo1(t)
        anel = np.array([terra + R_LUA * (np.cos(a) * u + np.sin(a) * v) for a in s_din])
        eixo = np.array([terra - 0.11 * np.array([np.sin(OBLIQ), 0, np.cos(OBLIQ)]),
                         terra + 0.11 * np.array([np.sin(OBLIQ), 0, np.cos(OBLIQ)])])
        sol = go.Scatter3d(x=[0], y=[0], z=[0], mode="markers+text", text=["Sol"],
                           textposition="bottom center",
                           marker=dict(size=18, color="#ffc400",
                                       line=dict(color="#ff9100", width=2)),
                           name="Sol")
        ter = go.Scatter3d(x=[terra[0]], y=[terra[1]], z=[terra[2]], mode="markers",
                           marker=dict(size=8, color="#1e88e5", line=dict(color="#0d47a1", width=1)),
                           name="Terra")
        moon = go.Scatter3d(x=[lua[0]], y=[lua[1]], z=[lua[2]], mode="markers",
                            marker=dict(size=5, color="#9e9e9e", line=dict(color="#424242", width=1)),
                            name="Lua")
        ring = go.Scatter3d(x=anel[:, 0], y=anel[:, 1], z=anel[:, 2], mode="lines",
                            line=dict(color="rgba(230,80,120,0.9)", width=3),
                            name="Órbita da Lua (inclinada 5,145°)", hoverinfo="skip")
        ax = go.Scatter3d(x=eixo[:, 0], y=eixo[:, 1], z=eixo[:, 2], mode="lines",
                          line=dict(color="#2e7d32", width=5), name="Eixo da Terra (23,44°)",
                          hoverinfo="skip")
        l_se = go.Scatter3d(x=[0, terra[0]], y=[0, terra[1]], z=[0, terra[2]], mode="lines",
                            line=dict(color="rgba(255,160,0,0.7)", width=2, dash="dash"),
                            name="Linha Sol–Terra", hoverinfo="skip")
        l_tl = go.Scatter3d(x=[terra[0], lua[0]], y=[terra[1], lua[1]], z=[terra[2], lua[2]],
                            mode="lines", line=dict(color="rgba(120,120,120,0.8)", width=2),
                            name="Linha Terra–Lua", hoverinfo="skip")
        return [sol, ter, moon, ring, ax, l_se, l_tl]

    def legenda(t):
        elong, ilum, lat, ecl = info_modelo1(t)
        return (f"<b>Dia {int(t)}</b> do ciclo  •  {nome_fase(elong)} ({ilum:.0f}% iluminada)"
                f"  •  latitude eclíptica da Lua: {lat:+.1f}°{ecl}")

    dias = list(range(0, 366))
    fig = go.Figure(data=[orb_terra, disco] + dinamicos(0))
    idx = list(range(2, 9))
    fig.frames = [go.Frame(name=str(t), data=dinamicos(t), traces=idx,
                           layout=go.Layout(annotations=[dict(
                               text=legenda(t), x=0.5, y=1.0, xref="paper", yref="paper",
                               xanchor="center", yanchor="bottom", showarrow=False,
                               font=dict(size=14))]))
                  for t in dias]
    fig.update_layout(
        annotations=[dict(text=legenda(0), x=0.5, y=1.0, xref="paper", yref="paper",
                          xanchor="center", yanchor="bottom", showarrow=False,
                          font=dict(size=14))],
        scene=dict(aspectmode="manual", aspectratio=dict(x=1, y=1, z=0.45),
                   xaxis=dict(visible=False, range=[-1.3, 1.3]),
                   yaxis=dict(visible=False, range=[-1.3, 1.3]),
                   zaxis=dict(visible=False, range=[-0.6, 0.6]),
                   camera=dict(eye=dict(x=0.7, y=-0.85, z=0.45))),
        margin=dict(l=0, r=0, t=40, b=80), height=640,
        legend=dict(orientation="v", y=0.98, x=0.0, xanchor="left", yanchor="top",
                    bgcolor="rgba(255,255,255,0.7)", font=dict(size=12)),
        font=dict(family=FONTE), paper_bgcolor="white",
        **botoes_e_slider(dict(prefixo="Dia: ",
                               passos=[(str(t), str(t)) for t in range(0, 366, 10)]), 35))
    return fig


# ---------------------------------------------------------------------------
# MODELO 2 — Esfera celeste vista do observador (movimento aparente)
# ---------------------------------------------------------------------------
LATITUDE = -11.31 * DEG   # polo celeste sul a ~11,31° de altura, como no arquivo
OBLIQ2 = (23 + 26 / 60) * DEG
INC_LUA2 = (5 + 9 / 60) * DEG

N_POLO = np.array([0.0, np.cos(LATITUDE), np.sin(LATITUDE)])  # polo celeste norte
E1 = np.array([1.0, 0.0, 0.0])                                # Leste
E2 = np.cross(N_POLO, E1)


def ecl_para_eq(v):
    x, y, z = v
    return np.array([x, y * np.cos(OBLIQ2) - z * np.sin(OBLIQ2),
                     y * np.sin(OBLIQ2) + z * np.cos(OBLIQ2)])


def eq_para_horizonte(v, alpha):
    X = np.cos(alpha) * E1 + np.sin(alpha) * E2
    Y = -np.sin(alpha) * E1 + np.cos(alpha) * E2
    return v[0] * X + v[1] * Y + v[2] * N_POLO


def lua_na_ecliptica(omega, u, inc=INC_LUA2):
    return np.array([np.cos(omega) * np.cos(u) - np.sin(omega) * np.sin(u) * np.cos(inc),
                     np.sin(omega) * np.cos(u) + np.cos(omega) * np.sin(u) * np.cos(inc),
                     np.sin(u) * np.sin(inc)])


def figura_modelo2(data_inicial=datetime(2026, 11, 11), hora_inicial=6.0, horas=48, passo_h=0.5):
    doy = data_inicial.timetuple().tm_yday
    lam0 = 2 * np.pi * (doy - 79.0) / ANO              # longitude eclíptica do Sol
    d2000 = (data_inicial - datetime(2000, 1, 1, 12)).total_seconds() / 86400 + hora_inicial / 24
    omega0 = np.radians((125.04452 - 0.0529538083 * d2000) % 360)   # nodo ascendente médio
    fase0 = ((d2000 - 5.2597) / MES_SINODICO) % 1.0    # 0 = lua nova
    u0 = lam0 + 2 * np.pi * fase0 - omega0

    # ângulo inicial do céu: Sol com ângulo horário H0 = (hora - 12) * 15°
    s_eq = ecl_para_eq(np.array([np.cos(lam0), np.sin(lam0), 0.0]))
    ra_sol = np.arctan2(s_eq[1], s_eq[0])
    H0 = (hora_inicial - 12) * 15 * DEG
    alpha0 = -H0 - np.pi / 2 - ra_sol

    w = 2 * np.pi / DIA_SIDERAL

    def estado(th):
        alpha = alpha0 - w * th
        lam = lam0 + 2 * np.pi * th / (24 * ANO)
        u = u0 + 2 * np.pi * th / (24 * MES_SIDERAL)
        om = omega0 - 2 * np.pi * th / (24 * REGRESSAO_NODOS)
        return alpha, lam, u, om

    s = np.linspace(0, 2 * np.pi, 361)

    # --- elementos estáticos ---
    a = np.linspace(0, 2 * np.pi, 49)
    b = np.linspace(0, np.pi, 25)
    esfera = go.Surface(x=np.outer(np.cos(a), np.sin(b)), y=np.outer(np.sin(a), np.sin(b)),
                        z=np.outer(np.ones_like(a), np.cos(b)), opacity=0.07, showscale=False,
                        colorscale=[[0, "#8fc7e8"], [1, "#8fc7e8"]], hoverinfo="skip",
                        name="Esfera celeste", showlegend=True)
    horiz_disc = go.Mesh3d(x=np.r_[0, np.cos(s[:-1])], y=np.r_[0, np.sin(s[:-1])],
                           z=np.zeros(361), i=[0] * 360, j=list(range(1, 361)),
                           k=[(n % 360) + 1 for n in range(1, 361)],
                           color="#6d6d6d", opacity=0.25, name="Plano do horizonte",
                           hoverinfo="skip", showlegend=True)
    horiz_lin = go.Scatter3d(x=np.cos(s), y=np.sin(s), z=np.zeros_like(s), mode="lines",
                             line=dict(color="black", width=4), name="Horizonte", hoverinfo="skip")
    eq_pts = np.array([np.cos(t) * E1 + np.sin(t) * E2 for t in s])
    equador = go.Scatter3d(x=eq_pts[:, 0], y=eq_pts[:, 1], z=eq_pts[:, 2], mode="lines",
                           line=dict(color="#2e9e4f", width=4), name="Equador celeste",
                           hoverinfo="skip")
    cardeais = go.Scatter3d(
        x=[0, 0, 1, -1], y=[1, -1, 0, 0], z=[0, 0, 0, 0], mode="markers+text",
        text=["N", "S", "L", "O"], textposition="top center",
        textfont=dict(size=15, color="black"), marker=dict(size=4, color="black"),
        name="Pontos cardeais", hoverinfo="skip")
    polos = go.Scatter3d(
        x=[0, N_POLO[0], -N_POLO[0]], y=[0, N_POLO[1], -N_POLO[1]], z=[1, N_POLO[2], -N_POLO[2]],
        mode="markers+text", text=["Zênite", "Polo N", "Polo S"],
        textposition="middle right", marker=dict(size=4, color=["#555", "#2e9e4f", "#2e9e4f"]),
        name="Polos e zênite", hoverinfo="skip")

    s_din = np.linspace(0, 2 * np.pi, 145)

    def dinamicos(th):
        alpha, lam, u, om = estado(th)
        ecl = np.array([eq_para_horizonte(ecl_para_eq(np.array([np.cos(t), np.sin(t), 0.0])), alpha)
                        for t in s_din])
        orb = np.array([eq_para_horizonte(ecl_para_eq(lua_na_ecliptica(om, t)), alpha) for t in s_din])
        sol = eq_para_horizonte(ecl_para_eq(np.array([np.cos(lam), np.sin(lam), 0.0])), alpha)
        lua = eq_para_horizonte(ecl_para_eq(lua_na_ecliptica(om, u)), alpha)
        nodo_a = eq_para_horizonte(ecl_para_eq(np.array([np.cos(om), np.sin(om), 0.0])), alpha)
        nodo_d = -nodo_a
        return [
            go.Scatter3d(x=ecl[:, 0], y=ecl[:, 1], z=ecl[:, 2], mode="lines",
                         line=dict(color="#ff9933", width=5), name="Eclíptica", hoverinfo="skip"),
            go.Scatter3d(x=orb[:, 0], y=orb[:, 1], z=orb[:, 2], mode="lines",
                         line=dict(color="#e0457b", width=3), name="Órbita da Lua (5°9')",
                         hoverinfo="skip"),
            go.Scatter3d(x=[sol[0]], y=[sol[1]], z=[sol[2]], mode="markers",
                         marker=dict(size=11, color="#ffc400", line=dict(color="#ff9100", width=2)),
                         name="Sol"),
            go.Scatter3d(x=[lua[0]], y=[lua[1]], z=[lua[2]], mode="markers",
                         marker=dict(size=8, color="#b0b0b0", line=dict(color="#333", width=1)),
                         name="Lua"),
            go.Scatter3d(x=[nodo_a[0], nodo_d[0]], y=[nodo_a[1], nodo_d[1]], z=[nodo_a[2], nodo_d[2]],
                         mode="markers", marker=dict(size=4, color="#e0457b", symbol="diamond"),
                         name="Nodos lunares", hoverinfo="skip"),
            go.Scatter3d(x=[0, sol[0]], y=[0, sol[1]], z=[0, sol[2]], mode="lines",
                         line=dict(color="rgba(255,170,0,0.6)", width=2, dash="dash"),
                         name="Direção do Sol", hoverinfo="skip", showlegend=False),
            go.Scatter3d(x=[0, lua[0]], y=[0, lua[1]], z=[0, lua[2]], mode="lines",
                         line=dict(color="rgba(120,120,120,0.7)", width=2, dash="dash"),
                         name="Direção da Lua", hoverinfo="skip", showlegend=False),
        ], sol, lua

    def legenda(th):
        _, sol, lua = dinamicos(th)
        hora = (hora_inicial + th) % 24
        h_sol = np.degrees(np.arcsin(sol[2]))
        h_lua = np.degrees(np.arcsin(lua[2]))
        d = int((hora_inicial + th) // 24)
        estado_sol = "☀ acima do horizonte" if h_sol > 0 else "abaixo do horizonte"
        estado_lua = "acima" if h_lua > 0 else "abaixo"
        return (f"<b>{int(hora):02d}h{int(round((hora % 1) * 60)):02d}</b> (dia {d + 1})  •  "
                f"Sol: altura {h_sol:+.0f}° ({estado_sol})  •  Lua: altura {h_lua:+.0f}° ({estado_lua})")

    passos = np.arange(0, horas + 1e-9, passo_h)
    base, _, _ = dinamicos(0)
    fig = go.Figure(data=[esfera, horiz_disc, horiz_lin, equador, cardeais, polos] + base)
    idx = list(range(6, 13))
    fig.frames = [go.Frame(name=f"{th:g}", data=dinamicos(th)[0], traces=idx,
                           layout=go.Layout(annotations=[dict(
                               text=legenda(th), x=0.5, y=1.0, xref="paper", yref="paper",
                               xanchor="center", yanchor="bottom", showarrow=False,
                               font=dict(size=14))]))
                  for th in passos]
    fig.update_layout(
        annotations=[dict(text=legenda(0), x=0.5, y=1.0, xref="paper", yref="paper",
                          xanchor="center", yanchor="bottom", showarrow=False, font=dict(size=14))],
        scene=dict(aspectmode="cube",
                   xaxis=dict(visible=False, range=[-1.15, 1.15]),
                   yaxis=dict(visible=False, range=[-1.15, 1.15]),
                   zaxis=dict(visible=False, range=[-1.15, 1.15]),
                   camera=dict(eye=dict(x=0.75, y=-1.45, z=0.55))),
        margin=dict(l=0, r=0, t=40, b=80), height=680,
        legend=dict(orientation="v", y=0.98, x=0.0, xanchor="left", yanchor="top",
                    bgcolor="rgba(255,255,255,0.7)", font=dict(size=12)),
        font=dict(family=FONTE), paper_bgcolor="white",
        **botoes_e_slider(dict(prefixo="Horas desde o início: ",
                               passos=[(f"{th:g}", f"{th:g}") for th in passos[::4]]), 80))
    return fig


# ---------------------------------------------------------------------------
# MODELO 2 ANUAL — esfera celeste + declinação do Sol + analema
# ---------------------------------------------------------------------------
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def sol_dia(d, com_excentricidade=True):
    """Posição aparente do Sol. d = dias desde J2000.0 (array ou escalar).
    Retorna: longitude eclíptica verdadeira, longitude média, declinação (rad),
    equação do tempo (minutos). A equação do centro (excentricidade) é opcional."""
    L = np.radians((280.4665 + 0.98564736 * d) % 360)
    M = np.radians((357.5291 + 0.98560028 * d) % 360)
    C = (np.radians(1.9148 * np.sin(M) + 0.0200 * np.sin(2 * M) + 0.0003 * np.sin(3 * M))
         if com_excentricidade else 0.0)
    if not com_excentricidade:
        L = np.radians((280.4665 + 0.98564736 * d) % 360)
        lam = L
    else:
        lam = L + C
    ra = np.arctan2(np.cos(OBLIQ2) * np.sin(lam), np.cos(lam))
    dec = np.arcsin(np.sin(OBLIQ2) * np.sin(lam))
    eot = np.degrees((L - ra + np.pi) % (2 * np.pi) - np.pi) * 4.0
    return lam, L, dec, eot


def estacao_sul(lam):
    q = int((np.degrees(lam) % 360) // 90)
    return ["outono", "inverno", "primavera", "verão"][q]


def figura_modelo2_anual(data_inicial=datetime(2026, 1, 1), hora_local=12.0, n_dias=365,
                         com_excentricidade=True):
    """Esfera celeste ao longo de um ano, sempre na mesma hora solar média (padrão: meio-dia),
    com gráfico da declinação do Sol (senoide) e o analema (declinação x equação do tempo)."""
    from datetime import timedelta
    from plotly.subplots import make_subplots

    d0 = (data_inicial - datetime(2000, 1, 1, 12)).total_seconds() / 86400
    dias = np.arange(n_dias)
    lam, L, dec, eot = sol_dia(d0 + dias, com_excentricidade)
    lam = np.unwrap(lam)
    dec_g = np.degrees(dec)
    # céu orientado de modo que o Sol MÉDIO esteja sempre na mesma hora solar média
    H0 = (hora_local - 12) * 15 * DEG
    alpha = -H0 - np.pi / 2 - L

    def sol_h(j):
        v = np.array([np.cos(lam[j]), np.sin(lam[j]), 0.0])
        return eq_para_horizonte(ecl_para_eq(v), alpha[j])

    omega0 = np.radians((125.04452 - 0.0529538083 * d0) % 360)
    fase0 = ((d0 - 5.2597) / MES_SINODICO) % 1.0
    u0 = lam[0] + 2 * np.pi * fase0 - omega0

    def lua_h(j):
        u = u0 + 2 * np.pi * j / MES_SIDERAL
        om = omega0 - 2 * np.pi * j / REGRESSAO_NODOS
        return eq_para_horizonte(ecl_para_eq(lua_na_ecliptica(om, u)), alpha[j]), om

    pts_sol = np.array([sol_h(j) for j in dias])
    s = np.linspace(0, 2 * np.pi, 361)
    s_din = np.linspace(0, 2 * np.pi, 121)

    # ---- marcos do ano (equinócios e solstícios) e inícios de mês ----
    q = np.floor(np.degrees(lam) / 90.0)
    idx_marcos = [j for j in range(1, n_dias) if q[j] > q[j - 1]]
    nomes_marcos = {0: "Equinócio de março", 1: "Solstício de junho",
                    2: "Equinócio de setembro", 3: "Solstício de dezembro"}
    txt_marcos = [nomes_marcos[int(q[j]) % 4] for j in idx_marcos]
    inicios_mes = []
    for ano in range(data_inicial.year, data_inicial.year + 2):
        for m in range(1, 13):
            dd = (datetime(ano, m, 1) - data_inicial).days
            if 0 <= dd < n_dias:
                inicios_mes.append((dd, MESES[m - 1]))

    # ---- traços estáticos da cena 3D ----
    a = np.linspace(0, 2 * np.pi, 49)
    b = np.linspace(0, np.pi, 25)
    t_esfera = go.Surface(x=np.outer(np.cos(a), np.sin(b)), y=np.outer(np.sin(a), np.sin(b)),
                          z=np.outer(np.ones_like(a), np.cos(b)), opacity=0.07, showscale=False,
                          colorscale=[[0, "#8fc7e8"], [1, "#8fc7e8"]], hoverinfo="skip",
                          name="Esfera celeste", showlegend=True)
    t_disco = go.Mesh3d(x=np.r_[0, np.cos(s[:-1])], y=np.r_[0, np.sin(s[:-1])], z=np.zeros(361),
                        i=[0] * 360, j=list(range(1, 361)), k=[(n % 360) + 1 for n in range(1, 361)],
                        color="#6d6d6d", opacity=0.25, name="Plano do horizonte",
                        hoverinfo="skip", showlegend=True)
    t_hor = go.Scatter3d(x=np.cos(s), y=np.sin(s), z=np.zeros_like(s), mode="lines",
                         line=dict(color="black", width=4), name="Horizonte", hoverinfo="skip")
    eq_pts = np.array([np.cos(t) * E1 + np.sin(t) * E2 for t in s])
    t_equador = go.Scatter3d(x=eq_pts[:, 0], y=eq_pts[:, 1], z=eq_pts[:, 2], mode="lines",
                             line=dict(color="#2e9e4f", width=4), name="Equador celeste",
                             hoverinfo="skip")
    t_card = go.Scatter3d(x=[0, 0, 1, -1], y=[1, -1, 0, 0], z=[0, 0, 0, 0], mode="markers+text",
                          text=["N", "S", "L", "O"], textposition="top center",
                          textfont=dict(size=15, color="black"), marker=dict(size=4, color="black"),
                          name="Pontos cardeais", hoverinfo="skip")
    t_polos = go.Scatter3d(x=[0, N_POLO[0], -N_POLO[0]], y=[0, N_POLO[1], -N_POLO[1]],
                           z=[1, N_POLO[2], -N_POLO[2]], mode="markers+text",
                           text=["Zênite", "Polo N", "Polo S"], textposition="middle right",
                           marker=dict(size=4, color=["#555", "#2e9e4f", "#2e9e4f"]),
                           name="Polos e zênite", hoverinfo="skip")
    t_analema3d = go.Scatter3d(x=pts_sol[:, 0], y=pts_sol[:, 1], z=pts_sol[:, 2], mode="lines",
                               line=dict(color="rgba(255,153,51,0.45)", width=3, dash="dot"),
                               name=f"Analema ({hora_local:g}h solar média)", hoverinfo="skip")

    def dinamicos(j):
        al = alpha[j]
        ecl = np.array([eq_para_horizonte(ecl_para_eq(np.array([np.cos(t), np.sin(t), 0.0])), al)
                        for t in s_din])
        lua, om = lua_h(j)
        orb = np.array([eq_para_horizonte(ecl_para_eq(lua_na_ecliptica(om, t)), al) for t in s_din])
        sol = pts_sol[j]
        na = eq_para_horizonte(ecl_para_eq(np.array([np.cos(om), np.sin(om), 0.0])), al)
        tr = pts_sol[: j + 1]
        return [
            go.Scatter3d(x=ecl[:, 0], y=ecl[:, 1], z=ecl[:, 2], mode="lines",
                         line=dict(color="#ff9933", width=4), name="Eclíptica", hoverinfo="skip"),
            go.Scatter3d(x=orb[:, 0], y=orb[:, 1], z=orb[:, 2], mode="lines",
                         line=dict(color="#e0457b", width=2), name="Órbita da Lua (5°9')",
                         hoverinfo="skip"),
            go.Scatter3d(x=[sol[0]], y=[sol[1]], z=[sol[2]], mode="markers",
                         marker=dict(size=10, color="#ffc400", line=dict(color="#ff9100", width=2)),
                         name="Sol"),
            go.Scatter3d(x=[lua[0]], y=[lua[1]], z=[lua[2]], mode="markers",
                         marker=dict(size=7, color="#b0b0b0", line=dict(color="#333", width=1)),
                         name="Lua"),
            go.Scatter3d(x=[na[0], -na[0]], y=[na[1], -na[1]], z=[na[2], -na[2]], mode="markers",
                         marker=dict(size=4, color="#e0457b", symbol="diamond"),
                         name="Nodos lunares", hoverinfo="skip"),
            go.Scatter3d(x=[0, sol[0]], y=[0, sol[1]], z=[0, sol[2]], mode="lines",
                         line=dict(color="rgba(255,170,0,0.6)", width=2, dash="dash"),
                         hoverinfo="skip", showlegend=False),
            go.Scatter3d(x=[0, lua[0]], y=[0, lua[1]], z=[0, lua[2]], mode="lines",
                         line=dict(color="rgba(120,120,120,0.7)", width=2, dash="dash"),
                         hoverinfo="skip", showlegend=False),
            go.Scatter3d(x=tr[:, 0], y=tr[:, 1], z=tr[:, 2], mode="lines",
                         line=dict(color="#d84315", width=6), name="Percurso do Sol até a data",
                         hoverinfo="skip"),
        ]

    # ---- gráficos laterais ----
    t_dec = go.Scatter(x=dias, y=dec_g, mode="lines", line=dict(color="#ff9933", width=3),
                       name="Declinação do Sol", showlegend=False,
                       hovertemplate="dia %{x}: %{y:.1f}°<extra></extra>")
    t_marcos = go.Scatter(x=idx_marcos, y=[dec_g[j] for j in idx_marcos], mode="markers",
                          marker=dict(size=8, color="#1e3a5f"), text=txt_marcos, showlegend=False,
                          hovertemplate="%{text}<extra></extra>")
    t_analema = go.Scatter(x=eot, y=dec_g, mode="lines", line=dict(color="rgba(255,153,51,0.5)", width=2),
                           showlegend=False, hoverinfo="skip")
    t_meses = go.Scatter(x=[eot[d] for d, _ in inicios_mes], y=[dec_g[d] for d, _ in inicios_mes],
                         mode="markers+text", text=[m for _, m in inicios_mes], textposition="middle right",
                         textfont=dict(size=10, color="#555"), marker=dict(size=4, color="#555"),
                         showlegend=False, hoverinfo="skip")

    def dinamicos_2d(j):
        return [
            go.Scatter(x=[j], y=[dec_g[j]], mode="markers",
                       marker=dict(size=12, color="#d84315", line=dict(color="white", width=1)),
                       showlegend=False),
            go.Scatter(x=[j, j], y=[-27, 27], mode="lines",
                       line=dict(color="rgba(216,67,21,0.4)", width=1, dash="dot"), showlegend=False,
                       hoverinfo="skip"),
            go.Scatter(x=eot[: j + 1], y=dec_g[: j + 1], mode="lines",
                       line=dict(color="#d84315", width=3), showlegend=False, hoverinfo="skip"),
            go.Scatter(x=[eot[j]], y=[dec_g[j]], mode="markers",
                       marker=dict(size=11, color="#ffc400", line=dict(color="#d84315", width=2)),
                       showlegend=False),
        ]

    def cabecalho(j):
        dt = data_inicial + timedelta(days=int(j))
        return (f"<b>{dt.day} {MESES[dt.month - 1]} {dt.year}</b> ({hora_local:g}h solar média)  •  "
                f"{estacao_sul(lam[j])} no hemisfério sul  •  declinação do Sol: {dec_g[j]:+.1f}°  •  "
                f"equação do tempo: {eot[j]:+.1f} min")

    fig = make_subplots(rows=2, cols=2, column_widths=[0.56, 0.44], vertical_spacing=0.16,
                        horizontal_spacing=0.07,
                        specs=[[{"type": "scene", "rowspan": 2}, {"type": "xy"}],
                               [None, {"type": "xy"}]])
    for t in [t_esfera, t_disco, t_hor, t_equador, t_card, t_polos, t_analema3d]:  # 0..6
        fig.add_trace(t, row=1, col=1)
    for t in dinamicos(0):                                                          # 7..14
        fig.add_trace(t, row=1, col=1)
    fig.add_trace(t_dec, row=1, col=2)                                              # 15
    fig.add_trace(t_marcos, row=1, col=2)                                           # 16
    d2 = dinamicos_2d(0)
    fig.add_trace(d2[0], row=1, col=2)                                              # 17
    fig.add_trace(d2[1], row=1, col=2)                                              # 18
    fig.add_trace(t_analema, row=2, col=2)                                          # 19
    fig.add_trace(d2[2], row=2, col=2)                                              # 20
    fig.add_trace(d2[3], row=2, col=2)                                              # 21
    fig.add_trace(t_meses, row=2, col=2)                                            # 22

    idx = list(range(7, 15)) + [17, 18, 20, 21]

    def quadro(j):
        d2j = dinamicos_2d(j)
        return go.Frame(
            name=str(j), traces=idx,
            data=dinamicos(j) + [d2j[0], d2j[1], d2j[2], d2j[3]],
            layout=go.Layout(annotations=[dict(text=cabecalho(j), x=0.5, y=1.0, xref="paper",
                                               yref="paper", xanchor="center", yanchor="bottom",
                                               showarrow=False, font=dict(size=13))]))

    fig.frames = [quadro(j) for j in dias]

    fig.update_xaxes(row=1, col=2, range=[0, n_dias - 1], tickvals=[d for d, _ in inicios_mes],
                     ticktext=[m for _, m in inicios_mes], title_text="Data", showgrid=True,
                     gridcolor="#eee")
    fig.update_yaxes(row=1, col=2, range=[-27, 27], title_text="Declinação do Sol (°)",
                     tickvals=[-23.44, 0, 23.44], gridcolor="#eee", zeroline=False)
    for y, estilo in ((-23.44, "dot"), (23.44, "dot"), (0, "solid")):
        fig.add_shape(type="line", x0=0, x1=n_dias - 1, y0=y, y1=y, xref="x", yref="y",
                      line=dict(color="#999", width=1, dash=estilo))
    xr = max(abs(eot).max() * 1.35, 20)
    fig.update_xaxes(row=2, col=2, range=[-xr, xr], title_text="Equação do tempo (minutos)",
                     gridcolor="#eee", zeroline=True, zerolinecolor="#bbb")
    fig.update_yaxes(row=2, col=2, range=[-27, 27], title_text="Declinação (°)",
                     gridcolor="#eee", zeroline=True, zerolinecolor="#bbb")

    passos = [(str(j), (data_inicial + timedelta(days=j)).strftime("%d/%m")) for j in range(0, n_dias, 15)]
    fig.update_layout(
        annotations=[dict(text=cabecalho(0), x=0.5, y=1.0, xref="paper", yref="paper",
                          xanchor="center", yanchor="bottom", showarrow=False, font=dict(size=13))],
        scene=dict(aspectmode="cube",
                   xaxis=dict(visible=False, range=[-1.15, 1.15]),
                   yaxis=dict(visible=False, range=[-1.15, 1.15]),
                   zaxis=dict(visible=False, range=[-1.15, 1.15]),
                   camera=dict(eye=dict(x=0.75, y=-1.45, z=0.55))),
        margin=dict(l=0, r=10, t=40, b=80), height=720,
        legend=dict(orientation="v", y=0.98, x=0.0, xanchor="left", yanchor="top",
                    bgcolor="rgba(255,255,255,0.7)", font=dict(size=11)),
        font=dict(family=FONTE), paper_bgcolor="white", plot_bgcolor="white",
        **botoes_e_slider(dict(prefixo="Data: ", passos=passos), 40, tam_rotulo=9))
    return fig


# ---------------------------------------------------------------------------
# Páginas HTML (uma por modelo + página inicial)
# ---------------------------------------------------------------------------
BASE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titulo} | Animações Sol-Terra-Lua</title>
<style>
  :root {{ --cor:#1e3a5f; --fundo:#f6f8fb; }}
  body {{ margin:0; font-family:{fonte}; background:var(--fundo); color:#1c1c1c; line-height:1.55; }}
  header {{ background:var(--cor); color:white; padding:26px 20px 14px; text-align:center; }}
  header h1 {{ margin:0 0 4px; font-size:1.6rem; }}
  header p {{ margin:0 0 12px; opacity:.85; }}
  nav {{ display:flex; gap:8px; justify-content:center; flex-wrap:wrap; }}
  nav a {{ color:white; text-decoration:none; padding:7px 14px; border-radius:8px;
           border:1px solid rgba(255,255,255,.35); font-size:.95rem; }}
  nav a.atual {{ background:white; color:var(--cor); font-weight:600; }}
  main {{ max-width:1250px; margin:0 auto; padding:18px; }}
  .painel {{ background:white; border-radius:12px; padding:14px; box-shadow:0 1px 6px rgba(0,0,0,.08); }}
  .nota {{ font-size:.95rem; color:#33475b; margin:10px 4px 2px; }}
  .cartoes {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:16px; }}
  .cartao {{ background:white; border-radius:12px; padding:18px; box-shadow:0 1px 6px rgba(0,0,0,.08);
             text-decoration:none; color:inherit; border-top:5px solid var(--cor); }}
  .cartao:hover {{ box-shadow:0 3px 12px rgba(0,0,0,.15); }}
  .cartao h2 {{ margin:0 0 6px; font-size:1.15rem; color:var(--cor); }}
  footer {{ text-align:center; font-size:.85rem; color:#667; padding:18px; }}
</style>
</head>
<body>
<header>
  <h1>Sol, Terra e Lua em movimento</h1>
  <p>Modelos 3D interativos desenvolvidos a partir de um TCC em Licenciatura em Física</p>
  <nav>{nav}</nav>
</header>
<main>
{conteudo}
</main>
<footer>Gerado com Python · Plotly · Hospedado no GitHub Pages</footer>
</body>
</html>
"""

PAGINAS = [
    ("index.html", "Início"),
    ("modelo1.html", "Modelo 1 · Translação"),
    ("modelo2_anual.html", "Modelo 2 · Ano e analema"),
    ("modelo2_diario.html", "Modelo 2 · Um dia"),
]


def escrever(pasta, arquivo, titulo, conteudo):
    nav = "".join(f'<a href="{a}"{" class=atual" if a == arquivo else ""}>{n}</a>' for a, n in PAGINAS)
    html = BASE.format(titulo=titulo, fonte=FONTE, nav=nav, conteudo=conteudo)
    caminho = os.path.join(pasta, arquivo)
    with open(caminho, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"  {arquivo}: {len(html) / 1e6:.1f} MB")


def main():
    pasta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
    os.makedirs(pasta, exist_ok=True)
    cfg = {"responsive": True, "displaylogo": False}

    def fig_html(fig, div):
        fig = arredondar(fig)
        return fig.to_html(full_html=False, include_plotlyjs="cdn", div_id=div, auto_play=False, config=cfg)

    print("Gerando páginas...")
    inicio = """
<div class="cartoes">
  <a class="cartao" href="modelo1.html"><h2>Modelo 1 · Translação</h2>
  Sol, Terra e Lua vistos de fora: fases da Lua, órbita lunar inclinada em 5,145° e alertas de possíveis eclipses.</a>
  <a class="cartao" href="modelo2_anual.html"><h2>Modelo 2 · Ano e analema</h2>
  O céu visto da Terra ao longo de um ano, com a declinação do Sol (senoide) e o analema.</a>
  <a class="cartao" href="modelo2_diario.html"><h2>Modelo 2 · Um dia</h2>
  Movimento diário aparente do Sol e da Lua na esfera celeste, de hora em hora.</a>
</div>
<p class="nota">Os modelos foram criados originalmente no GeoGebra (2021) e recriados em Python com NumPy e Plotly.
São modelos didáticos: as escalas de distância e tamanho não são reais.</p>"""
    escrever(pasta, "index.html", "Início", inicio)

    nota1 = """<p class="nota"><b>O que você está vendo:</b> a Terra dá uma volta em torno do Sol em um ano e a Lua dá cerca de
13 voltas em torno da Terra nesse período. O plano da órbita lunar é inclinado 5,145° em relação à eclíptica; por isso
os eclipses só ocorrem quando a Lua está perto da linha dos nodos. Arraste para girar, use a roda do mouse para aproximar
e o controle deslizante para escolher o dia. A distância Terra–Lua está exagerada para facilitar a visualização.</p>"""
    escrever(pasta, "modelo1.html", "Modelo 1",
             f'<div class="painel">{fig_html(figura_modelo1(), "fig1")}{nota1}</div>')

    nota_a = """<p class="nota"><b>O que você está vendo:</b> à esquerda, a esfera celeste vista do observador, sempre no mesmo horário
(meio-dia solar médio). Como o dia solar é mais longo que o dia sideral, a eclíptica gira lentamente ao longo do ano e o Sol
percorre a linha laranja pontilhada: o <b>analema</b>. No alto, à direita, a declinação do Sol ao longo do ano forma uma
senoide entre −23,44° e +23,44°. Embaixo, o analema em gráfico: a declinação em função da <b>equação do tempo</b>, a diferença entre
o tempo solar aparente e o tempo solar médio. O formato de "8" assimétrico vem de dois efeitos: a inclinação do eixo da Terra
(que alonga o "8" no sentido norte–sul e cria o cruzamento) e a excentricidade da órbita (que torna um dos laços maior que o outro).</p>"""
    escrever(pasta, "modelo2_anual.html", "Modelo 2 · Ano e analema",
             f'<div class="painel">{fig_html(figura_modelo2_anual(), "fig3")}{nota_a}</div>')

    nota2 = """<p class="nota"><b>O que você está vendo:</b> a esfera celeste centrada no observador (você está no centro).
A rotação aparente do céu leva o Sol e a Lua a nascer no lado leste (L) e se pôr no lado oeste (O). O Sol percorre a eclíptica
ao longo do ano e a Lua percorre uma órbita inclinada 5°9' em relação a ela, com os nodos recuando um ciclo completo a cada 18,6 anos.</p>"""
    escrever(pasta, "modelo2_diario.html", "Modelo 2 · Um dia",
             f'<div class="painel">{fig_html(figura_modelo2(), "fig2")}{nota2}</div>')
    print("Pronto: abra docs/index.html")


if __name__ == "__main__":
    main()
