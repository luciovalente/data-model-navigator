from __future__ import annotations

import html
import json
from pathlib import Path

from datamodel_navigator.models import DataModel


def build_viewer_html(model: DataModel) -> str:
    payload = json.dumps(model.to_dict(), ensure_ascii=False)
    # Keep JSON valid in <script type="application/json"> while avoiding accidental tag close.
    safe_payload = payload.replace('</', '<\\/')
    safe_payload = html.escape(payload)
    return f"""<!doctype html>
<html lang='it'>
<head>
  <meta charset='utf-8' />
  <meta name='viewport' content='width=device-width, initial-scale=1' />
  <title>Data Model Navigator</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; display: grid; grid-template-columns: 320px 1fr; height: 100vh; }}
    #left {{ border-right: 1px solid #ddd; overflow: auto; padding: 12px; }}
    #canvas {{ position: relative; overflow: auto; background: #fafafa; }}
    .entity {{ border: 1px solid #999; border-radius: 6px; background: white; padding: 6px 10px; margin-bottom: 8px; cursor: pointer; }}
    .entity h4 {{ margin: 0 0 6px; font-size: 14px; }}
    .field {{ font-size: 12px; color: #444; }}
    svg {{ position: absolute; inset: 0; pointer-events: none; }}
    .node {{ position: absolute; width: 220px; background: #fff; border: 1px solid #666; border-radius: 8px; padding: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
    .node.selected {{ border-color: #0057d8; box-shadow: 0 0 0 2px rgba(0,87,216,.2); }}
  </style>
</head>
<body>
  <aside id='left'>
    <h3>Entità</h3>
    <div id='list'></div>
  </aside>
  <main id='canvas'>
    <svg id='links'></svg>
  </main>
  <script id='model-data' type='application/json'>{safe_payload}</script>
  <script>
    const model = JSON.parse(document.getElementById('model-data').textContent);
    const canvas = document.getElementById('canvas');
    const list = document.getElementById('list');
    const linksSvg = document.getElementById('links');

    const positions = new Map();
    model.entities.forEach((entity, idx) => {{
      positions.set(entity.id, {{x: 40 + (idx % 3) * 260, y: 40 + Math.floor(idx / 3) * 220}});
    }});

    function draw() {{
      canvas.querySelectorAll('.node').forEach(e => e.remove());
      linksSvg.innerHTML = '';
      linksSvg.setAttribute('width', canvas.scrollWidth || 1200);
      linksSvg.setAttribute('height', canvas.scrollHeight || 900);

      for (const entity of model.entities) {{
        const pos = positions.get(entity.id);
        const div = document.createElement('div');
        div.className = 'node';
        div.style.left = pos.x + 'px';
        div.style.top = pos.y + 'px';
        div.dataset.entity = entity.id;
        div.innerHTML = `<h4>${{entity.name}}</h4>` + entity.attributes.slice(0, 10).map(a => `<div class='field'>${{a.name}}: ${{a.type}}</div>`).join('');
        div.onclick = () => {{
          canvas.querySelectorAll('.node').forEach(n => n.classList.remove('selected'));
          div.classList.add('selected');
        }};
        canvas.appendChild(div);
      }}

      for (const rel of model.relationships) {{
        const from = positions.get(rel.from_entity); const to = positions.get(rel.to_entity);
        if (!from || !to) continue;
        const x1 = from.x + 220; const y1 = from.y + 40;
        const x2 = to.x; const y2 = to.y + 40;
        const line = document.createElementNS('http://www.w3.org/2000/svg','line');
        line.setAttribute('x1', x1); line.setAttribute('y1', y1);
        line.setAttribute('x2', x2); line.setAttribute('y2', y2);
        line.setAttribute('stroke', '#1976d2'); line.setAttribute('stroke-width', '2');
        linksSvg.appendChild(line);
      }}

      list.innerHTML = '';
      for (const entity of model.entities) {{
        const card = document.createElement('div');
        card.className = 'entity';
        card.innerHTML = `<h4>${{entity.name}}</h4><div class='field'>${{entity.source_system}} • ${{entity.source_type}}</div>`;
        card.onclick = () => {{
          const node = canvas.querySelector(`[data-entity='${{entity.id}}']`);
          if (node) {{
            node.scrollIntoView({{behavior: 'smooth', block: 'center', inline: 'center'}});
            node.click();
          }}
        }};
        list.appendChild(card);
      }}
    }}
    draw();
  </script>
</body>
</html>
"""


def write_viewer(model: DataModel, path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(build_viewer_html(model), encoding="utf-8")
    return p
