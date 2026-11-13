// app.js — partes comuns às páginas: funcionamento offline, botão "Instalar o app" e controles recolhíveis no celular.

// 1) service worker (guarda o site para usar sem internet)
if ("serviceWorker" in navigator) {
  addEventListener("load", () => navigator.serviceWorker.register("sw.js").catch(() => {}));
}

// 2) instalação como app
const instalado = matchMedia("(display-mode: standalone)").matches || navigator.standalone === true;
let pedidoInstalacao = null;
addEventListener("beforeinstallprompt", (ev) => {
  ev.preventDefault(); pedidoInstalacao = ev;
  document.querySelectorAll("[data-instalar]").forEach((b) => (b.hidden = false));
});
addEventListener("appinstalled", () => {
  pedidoInstalacao = null;
  document.querySelectorAll("[data-instalar], [data-dica-ios]").forEach((b) => (b.hidden = true));
});
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-instalar]").forEach((b) => b.addEventListener("click", async () => {
    if (!pedidoInstalacao) return;
    pedidoInstalacao.prompt(); await pedidoInstalacao.userChoice; pedidoInstalacao = null; b.hidden = true;
  }));
  // iPhone/iPad não têm o botão automático: mostra como instalar pelo Safari
  const ios = /iphone|ipad|ipod/i.test(navigator.userAgent) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  if (ios && !instalado) document.querySelectorAll("[data-dica-ios]").forEach((d) => (d.hidden = false));

  // 3) no celular, os controles começam recolhidos para a cena aparecer na primeira tela
  const barras = document.querySelectorAll(".barra");
  if (!barras.length) return;
  const botao = document.createElement("button");
  botao.className = "botaoControles"; botao.type = "button";
  barras[0].before(botao);
  const celular = matchMedia("(max-width: 700px)");
  const aplicar = (recolher) => {
    document.body.classList.toggle("controles-recolhidos", recolher);
    botao.textContent = recolher ? "⚙ Mostrar controles ▾" : "⚙ Esconder controles ▴";
    botao.setAttribute("aria-expanded", String(!recolher));
    dispatchEvent(new Event("resize")); // a cena 3D se ajusta ao novo espaço
  };
  botao.addEventListener("click", () => aplicar(!document.body.classList.contains("controles-recolhidos")));
  aplicar(celular.matches);
  celular.addEventListener("change", (e) => aplicar(e.matches));
});
