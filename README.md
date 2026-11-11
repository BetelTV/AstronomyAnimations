# Animações Sol–Terra–Lua

Modelos 3D interativos do sistema Sol-Terra-Lua, recriados em Python a partir de dois modelos do GeoGebra
desenvolvidos em um TCC de Licenciatura em Física.

| Página | Conteúdo |
|---|---|
| `index.html` | Página inicial |
| `modelo1.html` | Translação: Terra e Lua vistas de fora, fases da Lua e alertas de possíveis eclipses |
| `modelo2_anual.html` | Esfera celeste ao longo do ano, declinação do Sol (senoide) e analema |
| `modelo2_diario.html` | Movimento diário aparente do Sol e da Lua |

## Como gerar o site

```bash
pip install plotly numpy
python gerar_site.py
```

As páginas são criadas na pasta `docs/`. Para publicar: **Settings → Pages → Deploy from a branch → `main` / `docs`**.

## Ajustes rápidos (em `gerar_site.py`)

- `figura_modelo2_anual(data_inicial=..., hora_local=12, com_excentricidade=True)`: ano, horário do analema e
  inclusão da excentricidade (com `False`, o analema fica um "8" simétrico, só pelo efeito da inclinação do eixo).
- `figura_modelo2(data_inicial=..., hora_inicial=...)`: data e hora de partida do modelo diário.
- `LATITUDE`: latitude do observador (o arquivo original usa ≈ −11,31°).
- `R_LUA`: raio da órbita lunar no Modelo 1 (exagerado para visualização).
