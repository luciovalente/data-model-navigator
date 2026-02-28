from __future__ import annotations

import json
from pathlib import Path

from datamodel_navigator.models import DataModel


HTML_TEMPLATE = """<!doctype html>
<html lang='it'>
<head>
  <meta charset='utf-8' />
  <meta name='viewport' content='width=device-width, initial-scale=1' />
  <title>Data Model Navigator</title>
  <link rel='stylesheet' href='https://unpkg.com/vis-network/styles/vis-network.min.css' />
  <style>
    :root {
      --panel-bg: #f8f9fb;
      --border: #d7dbe2;
      --text: #1f2937;
      --muted: #6b7280;
      --accent: #2563eb;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, Arial, sans-serif;
      color: var(--text);
      display: grid;
      grid-template-columns: 360px 1fr;
      height: 100vh;
      overflow: hidden;
    }
    #left {
      border-right: 1px solid var(--border);
      background: var(--panel-bg);
      overflow: auto;
      padding: 14px;
    }
    .section-title {
      margin: 0 0 10px;
      font-size: 14px;
      text-transform: uppercase;
      color: var(--muted);
      letter-spacing: 0.04em;
    }
    #entity-list { display: grid; gap: 8px; margin-bottom: 20px; }
    .entity-card {
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 8px 10px;
      background: #fff;
      cursor: pointer;
      transition: border-color 120ms ease, box-shadow 120ms ease;
    }
    .entity-card:hover {
      border-color: var(--accent);
      box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.15);
    }
    .entity-card .meta { font-size: 12px; color: var(--muted); margin-top: 4px; }
    #colors { display: grid; gap: 8px; margin-bottom: 20px; }
    .color-row {
      display: grid;
      grid-template-columns: 1fr auto;
      align-items: center;
      gap: 10px;
      font-size: 13px;
      background: #fff;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 6px 8px;
    }
    #tips {
      font-size: 12px;
      color: var(--muted);
      line-height: 1.45;
      background: #fff;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 8px;
    }
    #network { height: 100%; width: 100%; background: #ffffff; }
    #fallback {
      display: none;
      padding: 16px;
      color: #b91c1c;
      font-weight: 600;
    }
  </style>
</head>
<body>
  <aside id='left'>
    <h2 style='margin: 0 0 12px;'>Data Model Navigator</h2>
    <h3 class='section-title'>Entità</h3>
    <div id='entity-list'></div>
    <h3 class='section-title'>Colori per sorgente</h3>
    <div id='colors'></div>
    <h3 class='section-title'>Suggerimenti</h3>
    <div id='tips'>
      • Trascina un nodo per spostarlo liberamente.<br />
      • Zoom con rotella o pinch del trackpad.<br />
      • Click su un'entità nella lista per centrarla.<br />
      • Modifica i colori per distinguere i sistemi sorgente.
    </div>
  </aside>

  <main style='position:relative;'>
    <div id='fallback'>Impossibile caricare la libreria del viewer (vis-network).</div>
    <div id='network'></div>
  </main>

  <script id='model-data' type='application/json'>__MODEL_PAYLOAD__</script>
  <script src='https://unpkg.com/vis-network/standalone/umd/vis-network.min.js'></script>
  <script>
    const model = JSON.parse(document.getElementById('model-data').textContent);

    const palette = ['#60a5fa', '#f59e0b', '#34d399', '#f472b6', '#a78bfa', '#f87171', '#22d3ee', '#94a3b8'];
    const sourceTypes = [...new Set(model.entities.map(e => e.source_system || 'unknown'))];
    const sourceColors = new Map(sourceTypes.map((source, idx) => [source, palette[idx % palette.length]]));

    const nodes = new vis.DataSet(
      model.entities.map((entity, idx) => ({
        id: entity.id,
        label: entity.name,
        title: '<b>' + entity.name + '</b><br/>' + (entity.attributes || []).map(a => a.name + ': ' + a.type).join('<br/>'),
        shape: 'box',
        margin: 10,
        color: {
          background: sourceColors.get(entity.source_system || 'unknown'),
          border: '#334155',
          highlight: { background: '#dbeafe', border: '#1d4ed8' }
        },
        font: { color: '#0f172a', size: 14 },
        x: (idx % 4) * 280,
        y: Math.floor(idx / 4) * 180,
        physics: false,
      }))
    );

    const edges = new vis.DataSet(
      model.relationships.map((rel, idx) => ({
        id: `rel-${idx}`,
        from: rel.from_entity,
        to: rel.to_entity,
        arrows: 'to',
        label: rel.name || '',
        font: { align: 'middle', size: 10 },
        color: { color: '#3b82f6', highlight: '#2563eb' },
        smooth: { type: 'cubicBezier', roundness: 0.2 }
      }))
    );

    const networkContainer = document.getElementById('network');
    const fallback = document.getElementById('fallback');

    if (!window.vis || !window.vis.Network) {
      fallback.style.display = 'block';
    } else {
      const network = new vis.Network(networkContainer, { nodes, edges }, {
        layout: { improvedLayout: true },
        interaction: { dragNodes: true, dragView: true, zoomView: true, hover: true, multiselect: true },
        physics: { enabled: false },
      });

      const listEl = document.getElementById('entity-list');
      model.entities.forEach(entity => {
        const card = document.createElement('div');
        card.className = 'entity-card';
        card.innerHTML = `<strong>${entity.name}</strong><div class='meta'>${entity.source_system} • ${entity.source_type}</div>`;
        card.addEventListener('click', () => {
          network.selectNodes([entity.id]);
          network.focus(entity.id, { scale: 1, animation: { duration: 250 } });
        });
        listEl.appendChild(card);
      });

      const colorsEl = document.getElementById('colors');
      sourceTypes.forEach(source => {
        const row = document.createElement('label');
        row.className = 'color-row';
        row.innerHTML = `<span>${source}</span>`;

        const input = document.createElement('input');
        input.type = 'color';
        input.value = sourceColors.get(source);
        input.addEventListener('input', () => {
          sourceColors.set(source, input.value);
          const updates = model.entities
            .filter(e => (e.source_system || 'unknown') === source)
            .map(e => ({ id: e.id, color: { background: input.value, border: '#334155' } }));
          nodes.update(updates);
        });

        row.appendChild(input);
        colorsEl.appendChild(row);
      });

      window.addEventListener('resize', () => network.fit({ animation: false }));
      network.fit({ animation: false });
    }
  </script>
</body>
</html>
"""


def build_viewer_html(model: DataModel) -> str:
    payload = json.dumps(model.to_dict(), ensure_ascii=False)
    safe_payload = payload.replace("</", "<\\/")
    return HTML_TEMPLATE.replace("__MODEL_PAYLOAD__", safe_payload)


def write_viewer(model: DataModel, path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(build_viewer_html(model), encoding="utf-8")
    return p
