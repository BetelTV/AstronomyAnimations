// astro.js — cálculos astronômicos de baixa precisão (erro típico < 0,1° para o Sol, ~0,3° para a Lua)
// Fórmulas: Astronomical Almanac (Sol) e Meeus, "Astronomical Algorithms", termos principais (Lua).
export const RAD = Math.PI / 180;
export const DEG = 180 / Math.PI;
const sin = (x) => Math.sin(x * RAD), cos = (x) => Math.cos(x * RAD);
export const norm360 = (x) => ((x % 360) + 360) % 360;
export const norm180 = (x) => ((x + 180) % 360 + 360) % 360 - 180;

// Data juliana a partir de data/hora civil local (ano, mês 1-12, dia, minutos desde 0h, fuso em horas)
export function jdLocal(ano, mes, dia, minutos, fuso) {
  return Date.UTC(ano, mes - 1, dia) / 864e5 + 2440587.5 + (minutos - fuso * 60) / 1440;
}
export const dJ2000 = (jd) => jd - 2451545.0;

export function sol(d) {
  const g = norm360(357.529 + 0.98560028 * d);
  const q = norm360(280.459 + 0.98564736 * d);
  const L = norm360(q + 1.915 * sin(g) + 0.020 * sin(2 * g));
  const R = 1.00014 - 0.01671 * cos(g) - 0.00014 * cos(2 * g);
  const eps = 23.439 - 0.00000036 * d;
  const ra = norm360(Math.atan2(cos(eps) * sin(L), cos(L)) * DEG);
  const dec = Math.asin(sin(eps) * sin(L)) * DEG;
  const eot = norm180(q - ra) * 4; // minutos (tempo solar aparente − tempo solar médio)
  return { lon: L, lat: 0, R, eps, ra, dec, eot, q, g };
}

export function lua(d) {
  const Lp = 218.3165 + 13.17639648 * d;
  const Mp = 134.9634 + 13.06499295 * d;
  const F = 93.2721 + 13.22935024 * d;
  const D = 297.8502 + 12.19074912 * d;
  const M = 357.5291 + 0.98560028 * d;
  const lon = norm360(Lp + 6.289 * sin(Mp) + 1.274 * sin(2 * D - Mp) + 0.658 * sin(2 * D)
    + 0.214 * sin(2 * Mp) - 0.186 * sin(M) - 0.114 * sin(2 * F) - 0.059 * sin(2 * D - 2 * Mp)
    - 0.057 * sin(2 * D - M - Mp) + 0.053 * sin(2 * D + Mp));
  const lat = 5.128 * sin(F) + 0.281 * sin(Mp + F) + 0.278 * sin(Mp - F) + 0.173 * sin(2 * D - F);
  const dist = 385001 - 20905 * cos(Mp) - 3699 * cos(2 * D - Mp) - 2956 * cos(2 * D); // km
  const no = norm360(125.0445 - 0.0529538083 * d); // nodo ascendente médio
  return { lon, lat, dist, no };
}

export function eclParaEq(lon, lat, eps) {
  const x = cos(lat) * cos(lon);
  const y = cos(eps) * cos(lat) * sin(lon) - sin(eps) * sin(lat);
  const z = sin(eps) * cos(lat) * sin(lon) + cos(eps) * sin(lat);
  return { ra: norm360(Math.atan2(y, x) * DEG), dec: Math.asin(z) * DEG };
}

export const tempoSideral = (d, lonObs) => norm360(280.46061837 + 360.98564736629 * d + lonObs);

// Vetor no horizonte local: {leste, norte, cima}, altura e azimute (a partir do Norte, para Leste)
export function horizonte(ra, dec, latObs, lst) {
  const H = lst - ra;
  const cima = sin(latObs) * sin(dec) + cos(latObs) * cos(dec) * cos(H);
  const norte = cos(latObs) * sin(dec) - sin(latObs) * cos(dec) * cos(H);
  const leste = -cos(dec) * sin(H);
  return { leste, norte, cima, alt: Math.asin(Math.max(-1, Math.min(1, cima))) * DEG,
           az: norm360(Math.atan2(leste, norte) * DEG) };
}

export function faseLua(s, l) {
  const dl = norm360(l.lon - s.lon);
  const elong = Math.acos(cos(l.lat) * cos(dl)) * DEG;
  const ilum = (1 - Math.cos(elong * RAD)) / 2;
  const cresc = dl < 180;
  let nome;
  if (dl < 6 || dl > 354) nome = "Lua nova";
  else if (dl < 84) nome = "Crescente";
  else if (dl < 96) nome = "Quarto crescente";
  else if (dl < 174) nome = "Gibosa crescente";
  else if (dl < 186) nome = "Lua cheia";
  else if (dl < 264) nome = "Gibosa minguante";
  else if (dl < 276) nome = "Quarto minguante";
  else nome = "Minguante";
  return { dl, elong, ilum, cresc, nome };
}

// Posições completas para um instante e um lugar
export function instante(jd, latObs, lonObs) {
  const d = dJ2000(jd);
  const s = sol(d), l = lua(d);
  const lst = tempoSideral(d, lonObs);
  const le = eclParaEq(l.lon, l.lat, s.eps);
  return {
    d, lst, s, l,
    solH: horizonte(s.ra, s.dec, latObs, lst),
    luaEq: le,
    luaH: horizonte(le.ra, le.dec, latObs, lst),
    fase: faseLua(s, l),
  };
}

// Nascer/pôr por varredura minuto a minuto ao longo do dia civil
export function nascerPor(jd0, latObs, lonObs, corpo, h0) {
  const alts = [];
  for (let m = 0; m <= 1440; m += 2) {
    const p = instante(jd0 + m / 1440, latObs, lonObs);
    alts.push([m, (corpo === "sol" ? p.solH : p.luaH).alt]);
  }
  let nasc = null, por = null, max = alts[0];
  for (let i = 1; i < alts.length; i++) {
    const [m0, a0] = alts[i - 1], [m1, a1] = alts[i];
    if (a0 < h0 && a1 >= h0 && nasc === null) nasc = m0 + (h0 - a0) / (a1 - a0) * (m1 - m0);
    if (a0 >= h0 && a1 < h0 && por === null) por = m0 + (h0 - a0) / (a1 - a0) * (m1 - m0);
  }
  for (const p of alts) if (p[1] > max[1]) max = p;
  return { nasc, por, culmMin: max[0], culmAlt: max[1], sempreAcima: alts.every(p => p[1] >= h0),
           sempreAbaixo: alts.every(p => p[1] < h0), alts };
}

export const hhmm = (min) => {
  if (min === null || min === undefined || isNaN(min)) return "—";
  min = ((min % 1440) + 1440) % 1440;
  const h = Math.floor(min / 60), m = Math.round(min % 60);
  return `${String(m === 60 ? h + 1 : h).padStart(2, "0")}h${String(m === 60 ? 0 : m).padStart(2, "0")}`;
};
