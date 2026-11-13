# Sol, Terra e Lua em movimento

Modelos 3D interativos do sistema Sol–Terra–Lua, recriados a partir de dois modelos do GeoGebra desenvolvidos no
Trabalho de Conclusão de Curso de **Matheus Fagioli** (2021), Licenciatura em Ciências Naturais e Matemática.

**Site:** https://betelTV.github.io/AstronomyAnimations/

| Página | O que mostra |
|---|---|
| `modelo1.html` | Terra e Lua vistas de fora: fases pela iluminação real, eixo inclinado 23,44°, órbita lunar inclinada 5,145°, nodos e épocas de eclipse. **Cones de sombra** (umbra, penumbra e antumbra da Lua; umbra e penumbra da Terra) com Terra e Lua em escala real entre si, diagnóstico do eclipse (total, anular, parcial, penumbral ou quanto a sombra passou longe) e botões para ir ao eclipse anterior/próximo. Passo de 1 hora. |
| `modelo2.html` | Céu do observador: latitude, longitude, data e hora livres (passo de 1 minuto); **mapa-múndi** para escolher o local com um clique, com dia/noite, Sol e Lua a pino; tabela de dados; altura do Sol e da Lua no dia; declinação do Sol no ano; analema no céu e analema “equação do tempo × declinação”. |

## Estrutura

```
src/              código das páginas (HTML + JavaScript)
  astro.js        cálculos astronômicos (Sol, Lua, tempo sideral, altura/azimute, nascer/pôr)
  modelo1.html    Modelo 1 (Three.js)
  modelo2.html    Modelo 2 (Three.js + gráficos)
  vendor/         biblioteca Three.js (licença MIT) e mundo.json (contornos dos países, Natural Earth, domínio público)
docs/             site pronto, publicado pelo GitHub Pages (gerado a partir de src/)
gerar_site.py     monta docs/ e injeta os parâmetros (locais, ano inicial)
efemerides.py     os mesmos cálculos em Python: gera tabelas CSV para conferir ou usar em aula/artigo
```

## Como usar

```bash
python gerar_site.py            # atualiza docs/ depois de mexer em src/ ou nos parâmetros
python gerar_site.py --servir   # idem, e abre o site em http://localhost:8000
python efemerides.py --lat -23.55 --lon -46.63 --fuso -3 --data 2026-11-11
python efemerides.py --ano 2026 --hora 12:00 --saida analema.csv
```

Os arquivos de `docs/` não abrem com duplo clique (o navegador bloqueia módulos JavaScript locais).
Use `python gerar_site.py --servir` ou o endereço do GitHub Pages.

## Atalhos pela URL (para preparar aulas)

- `modelo1.html#dia=172&camera=terra&exagero=3`
- `modelo1.html#ano=2026&sombras=1&eclipse=1` (abre no primeiro eclipse do ano, com os cones de sombra)
- `modelo2.html#lat=-23.55&lon=-46.63&fuso=-3&data=2026-06-21&hora=12:00&camera=olho&analema=eot`
- `modelo2.html#hora=09:00&tocar=diario` (abre já desenhando o analema)

## Precisão

Fórmulas de baixa precisão (Astronomical Almanac para o Sol; termos principais de Meeus para a Lua):
erro típico abaixo de 0,1° para o Sol e de cerca de 0,3° para a Lua, suficiente para fins didáticos.
A paralaxe da Lua e a refração atmosférica não são consideradas (exceto no critério de nascer/pôr do Sol, −0,833°).
