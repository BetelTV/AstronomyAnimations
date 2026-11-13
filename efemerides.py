#!/usr/bin/env python3
"""
efemerides.py — as mesmas fórmulas do site (src/astro.js), em Python.

Gera uma tabela (CSV) com a posição do Sol e da Lua para um lugar, hora a hora ou dia a dia.

Exemplos:
    python efemerides.py --lat -23.55 --lon -46.63 --fuso -3 --data 2026-11-11
        -> tabela hora a hora do dia 11/11/2026 em São Paulo
    python efemerides.py --lat -23.55 --lon -46.63 --fuso -3 --ano 2026 --hora 12:00 --saida analema.csv
        -> um ponto por dia, sempre ao meio-dia (dados do analema)
"""
import argparse
import csv
import math
import sys
from datetime import date, datetime, timedelta

RAD, DEG = math.pi / 180, 180 / math.pi
sen = lambda x: math.sin(x * RAD)
cos = lambda x: math.cos(x * RAD)
n360 = lambda x: x % 360
n180 = lambda x: (x + 180) % 360 - 180


def jd_local(d: date, minutos: float, fuso: float) -> float:
    return (datetime(d.year, d.month, d.day) - datetime(1970, 1, 1)).total_seconds() / 86400 + 2440587.5 \
        + (minutos - fuso * 60) / 1440


def sol(d):
    g = n360(357.529 + 0.98560028 * d)
    q = n360(280.459 + 0.98564736 * d)
    L = n360(q + 1.915 * sen(g) + 0.020 * sen(2 * g))
    R = 1.00014 - 0.01671 * cos(g) - 0.00014 * cos(2 * g)
    eps = 23.439 - 0.00000036 * d
    ra = n360(math.atan2(cos(eps) * sen(L), cos(L)) * DEG)
    dec = math.asin(sen(eps) * sen(L)) * DEG
    return dict(lon=L, R=R, eps=eps, ra=ra, dec=dec, eot=n180(q - ra) * 4)


def lua(d):
    Lp, Mp = 218.3165 + 13.17639648 * d, 134.9634 + 13.06499295 * d
    F, D, M = 93.2721 + 13.22935024 * d, 297.8502 + 12.19074912 * d, 357.5291 + 0.98560028 * d
    # maiores termos das tabelas 47.A e 47.B de Meeus (iguais aos de src/astro.js)
    lon = n360(Lp + 6.288774 * sen(Mp) + 1.274027 * sen(2 * D - Mp) + 0.658314 * sen(2 * D)
               + 0.213618 * sen(2 * Mp) - 0.185116 * sen(M) - 0.114332 * sen(2 * F) + 0.058793 * sen(2 * D - 2 * Mp)
               + 0.057066 * sen(2 * D - M - Mp) + 0.053322 * sen(2 * D + Mp) + 0.045758 * sen(2 * D - M)
               - 0.040923 * sen(M - Mp) - 0.034720 * sen(D) - 0.030383 * sen(M + Mp) + 0.015327 * sen(2 * D - 2 * F)
               - 0.012528 * sen(Mp + 2 * F) + 0.010980 * sen(Mp - 2 * F) + 0.010675 * sen(4 * D - Mp)
               + 0.010034 * sen(3 * Mp) + 0.008548 * sen(4 * D - 2 * Mp) - 0.007888 * sen(2 * D + M - Mp)
               - 0.006766 * sen(2 * D + M) - 0.005163 * sen(D - Mp) + 0.004987 * sen(D + M)
               + 0.004036 * sen(2 * D - M + Mp))
    lat = (5.128122 * sen(F) + 0.280602 * sen(Mp + F) + 0.277693 * sen(Mp - F) + 0.173237 * sen(2 * D - F)
           + 0.055413 * sen(2 * D - Mp + F) + 0.046271 * sen(2 * D - Mp - F) + 0.032573 * sen(2 * D + F)
           + 0.017198 * sen(2 * Mp + F) + 0.009266 * sen(2 * D + Mp - F) + 0.008822 * sen(2 * Mp - F)
           + 0.008216 * sen(2 * D - M - F) + 0.004324 * sen(2 * D - 2 * Mp - F) + 0.004200 * sen(2 * D + Mp + F)
           - 0.003359 * sen(2 * D + M - F))
    dist = (385000.56 - 20905.355 * cos(Mp) - 3699.111 * cos(2 * D - Mp) - 2955.968 * cos(2 * D)
            - 569.925 * cos(2 * Mp) + 48.888 * cos(M) - 3.149 * cos(2 * F) + 246.158 * cos(2 * D - 2 * Mp)
            - 152.138 * cos(2 * D - M - Mp) - 170.733 * cos(2 * D + Mp) - 204.586 * cos(2 * D - M)
            - 129.620 * cos(M - Mp) + 108.743 * cos(D) + 104.755 * cos(M + Mp) + 10.321 * cos(2 * D - 2 * F)
            + 79.661 * cos(Mp - 2 * F) - 34.782 * cos(4 * D - Mp) - 23.210 * cos(3 * Mp) - 21.636 * cos(4 * D - 2 * Mp)
            + 24.208 * cos(2 * D + M - Mp) + 30.824 * cos(2 * D + M) - 8.379 * cos(D - Mp) - 16.675 * cos(D + M)
            - 12.831 * cos(2 * D - M + Mp))
    return dict(lon=lon, lat=lat, dist=dist)


def ecl_para_eq(lon, lat, eps):
    x = cos(lat) * cos(lon)
    y = cos(eps) * cos(lat) * sen(lon) - sen(eps) * sen(lat)
    z = sen(eps) * cos(lat) * sen(lon) + cos(eps) * sen(lat)
    return n360(math.atan2(y, x) * DEG), math.asin(z) * DEG


def horizonte(ra, dec, lat, lst):
    H = lst - ra
    cima = sen(lat) * sen(dec) + cos(lat) * cos(dec) * cos(H)
    norte = cos(lat) * sen(dec) - sen(lat) * cos(dec) * cos(H)
    leste = -cos(dec) * sen(H)
    return math.asin(max(-1, min(1, cima))) * DEG, n360(math.atan2(leste, norte) * DEG)


def instante(jd, lat, lon):
    d = jd - 2451545.0
    s, l = sol(d), lua(d)
    lst = n360(280.46061837 + 360.98564736629 * d + lon)
    s_alt, s_az = horizonte(s["ra"], s["dec"], lat, lst)
    l_ra, l_dec = ecl_para_eq(l["lon"], l["lat"], s["eps"])
    l_alt, l_az = horizonte(l_ra, l_dec, lat, lst)
    dl = n360(l["lon"] - s["lon"])
    elong = math.acos(cos(l["lat"]) * cos(dl)) * DEG
    return dict(sol_alt=s_alt, sol_az=s_az, sol_dec=s["dec"], eq_tempo_min=s["eot"],
                lua_alt=l_alt, lua_az=l_az, lua_dec=l_dec, lua_iluminacao=(1 - cos(elong)) / 2,
                lua_lat_ecliptica=l["lat"])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lat", type=float, default=-23.55)
    ap.add_argument("--lon", type=float, default=-46.63)
    ap.add_argument("--fuso", type=float, default=-3)
    ap.add_argument("--data", help="AAAA-MM-DD: tabela hora a hora deste dia")
    ap.add_argument("--ano", type=int, help="tabela dia a dia deste ano (use com --hora)")
    ap.add_argument("--hora", default="12:00", help="HH:MM para a tabela anual")
    ap.add_argument("--passo", type=int, default=60, help="minutos entre linhas na tabela diária")
    ap.add_argument("--saida", help="arquivo CSV (padrão: mostra na tela)")
    a = ap.parse_args()

    linhas = []
    if a.ano:
        hh, mm = map(int, a.hora.split(":"))
        d = date(a.ano, 1, 1)
        while d.year == a.ano:
            linhas.append(dict(data=d.isoformat(), hora=a.hora, **instante(jd_local(d, hh * 60 + mm, a.fuso), a.lat, a.lon)))
            d += timedelta(days=1)
    else:
        d = date.fromisoformat(a.data) if a.data else date.today()
        for m in range(0, 1441, a.passo):
            linhas.append(dict(data=d.isoformat(), hora=f"{m // 60:02d}:{m % 60:02d}",
                               **instante(jd_local(d, m, a.fuso), a.lat, a.lon)))
    for ln in linhas:
        for k, v in ln.items():
            if isinstance(v, float):
                ln[k] = round(v, 3)
    saida = open(a.saida, "w", newline="", encoding="utf-8") if a.saida else sys.stdout
    w = csv.DictWriter(saida, fieldnames=list(linhas[0]), delimiter=";")
    w.writeheader()
    w.writerows(linhas)
    if a.saida:
        print(f"{len(linhas)} linhas salvas em {a.saida}")


if __name__ == "__main__":
    main()
