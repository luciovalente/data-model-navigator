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
      grid-template-columns: 340px 1fr 360px;
      height: 100vh;
      overflow: hidden;
    }
    #left {
      border-right: 1px solid var(--border);
      background: var(--panel-bg);
      overflow: auto;
      padding: 14px;
    }
    #right {
      border-left: 1px solid var(--border);
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
      transition: border-color 120ms ease, box-shadow 120ms ease;
    }
    .entity-card.active {
      border-color: var(--accent);
      box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.15);
    }
    .entity-card label {
      display: grid;
      grid-template-columns: auto 1fr;
      gap: 8px;
      align-items: start;
      cursor: pointer;
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
    .btn {
      border: 1px solid var(--accent);
      background: #eff6ff;
      color: #1e40af;
      border-radius: 8px;
      padding: 8px 10px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      width: 100%;
      margin-bottom: 10px;
    }
    .btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    .relationship-card {
      border: 1px solid var(--border);
      background: #fff;
      border-radius: 8px;
      padding: 8px;
      font-size: 13px;
      line-height: 1.4;
      margin-bottom: 8px;
    }
    .relationship-title { font-weight: 700; }
    .empty-state {
      color: var(--muted);
      font-size: 13px;
      background: #fff;
      border: 1px dashed var(--border);
      border-radius: 8px;
      padding: 10px;
    }
    #fallback {
      display: none;
      padding: 16px;
      color: #92400e;
      background: #fffbeb;
      border-bottom: 1px solid #fcd34d;
      font-weight: 600;
    }
    #fallback-content {
      display: none;
      padding: 16px;
      overflow: auto;
      height: 100%;
      background: #fff;
    }
    .fallback-entity {
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px;
      margin-bottom: 10px;
    }
    .fallback-entity-title {
      font-weight: 700;
      margin-bottom: 6px;
    }
    .fallback-rel {
      font-size: 13px;
      color: var(--muted);
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
    <div id='fallback'>Modalità compatibilità: libreria vis-network non disponibile. Mostro entità e relazioni in formato elenco.</div>
    <div id='network'></div>
    <div id='fallback-content'></div>
  </main>

  <aside id='right'>
    <h3 class='section-title'>Relazioni Entità</h3>
    <div id='relationships-panel' class='empty-state'>
      Seleziona una o più entità dalla lista a sinistra per vedere le relazioni in ingresso/uscita.
    </div>
    <h3 class='section-title' style='margin-top:16px;'>Export campi entità selezionate</h3>
    <button id='export-excel' class='btn' disabled>Esporta in Excel (.xlsx)</button>
    <div class='empty-state'>
      L'export include: Entità, Campo, Tipo, Nullable, Sistema sorgente, Tipo sorgente.
    </div>
  </aside>

  <script id='model-data' type='application/json'>__MODEL_PAYLOAD__</script>
  <script src='https://unpkg.com/vis-network/standalone/umd/vis-network.min.js'></script>
  <script src='https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js'></script>
  <script>
    const model = JSON.parse(document.getElementById('model-data').textContent);
    const entitiesById = new Map(model.entities.map(entity => [entity.id, entity]));
    const entitiesByName = new Map(model.entities.map(entity => [entity.name, entity]));
    const selectedEntityIds = new Set();

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

    function getEntityId(entityRef) {
      if (entitiesById.has(entityRef)) {
        return entityRef;
      }
      if (entitiesByName.has(entityRef)) {
        return entitiesByName.get(entityRef).id;
      }
      return null;
    }

    const normalizedRelationships = model.relationships
      .map((rel, idx) => {
        const fromId = getEntityId(rel.from_entity);
        const toId = getEntityId(rel.to_entity);
        if (!fromId || !toId) {
          return null;
        }
        return {
          id: rel.id || `rel-${idx}`,
          fromId,
          toId,
          from_field: rel.from_field,
          to_field: rel.to_field,
          confidence: rel.confidence,
          source: rel.source,
        };
      })
      .filter(Boolean);

    const edges = new vis.DataSet(
      normalizedRelationships.map((rel, idx) => ({
        id: `rel-${idx}`,
        from: rel.fromId,
        to: rel.toId,
        arrows: 'to',
        label: `${rel.from_field || '?'} → ${rel.to_field || '?'}`,
        font: { align: 'middle', size: 10 },
        color: { color: '#3b82f6', highlight: '#2563eb' },
        smooth: { type: 'cubicBezier', roundness: 0.2 }
      }))
    );

    const networkContainer = document.getElementById('network');
    const fallback = document.getElementById('fallback');
    const fallbackContent = document.getElementById('fallback-content');

    function renderFallbackContent() {
      const relationshipsByEntity = new Map(model.entities.map(entity => [entity.id, []]));
      normalizedRelationships.forEach(rel => {
        if (relationshipsByEntity.has(rel.fromId)) {
          relationshipsByEntity.get(rel.fromId).push(rel);
        }
        if (relationshipsByEntity.has(rel.toId) && rel.toId !== rel.fromId) {
          relationshipsByEntity.get(rel.toId).push(rel);
        }
      });

      fallbackContent.innerHTML = model.entities.map(entity => {
        const rels = relationshipsByEntity.get(entity.id) || [];
        const relMarkup = rels.length === 0
          ? "<div class='fallback-rel'>Nessuna relazione.</div>"
          : rels.map(rel => {
            const fromEntity = entitiesById.get(rel.fromId);
            const toEntity = entitiesById.get(rel.toId);
            return `<div class='fallback-rel'>${fromEntity.name}.${rel.from_field || '?'} → ${toEntity.name}.${rel.to_field || '?'}</div>`;
          }).join('');

        return `
          <div class='fallback-entity'>
            <div class='fallback-entity-title'>${entity.name}</div>
            <div class='meta'>${entity.source_system} • ${entity.source_type}</div>
            ${relMarkup}
          </div>
        `;
      }).join('');
    }

    if (!window.vis || !window.vis.Network) {
      fallback.style.display = 'block';
      networkContainer.style.display = 'none';
      fallbackContent.style.display = 'block';
      renderFallbackContent();
    } else {
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
        normalizedRelationships.map((rel, idx) => ({
          id: `rel-${idx}`,
          from: rel.fromId,
          to: rel.toId,
          arrows: 'to',
          label: `${rel.from_field || '?'} → ${rel.to_field || '?'}`,
          font: { align: 'middle', size: 10 },
          color: { color: '#3b82f6', highlight: '#2563eb' },
          smooth: { type: 'cubicBezier', roundness: 0.2 }
        }))
      );

      const network = new vis.Network(networkContainer, { nodes, edges }, {
        layout: { improvedLayout: true },
        interaction: { dragNodes: true, dragView: true, zoomView: true, hover: true, multiselect: true },
        physics: { enabled: false },
      });

      const relationshipsPanel = document.getElementById('relationships-panel');
      const exportBtn = document.getElementById('export-excel');

      function updateRelationshipPanel() {
        if (selectedEntityIds.size === 0) {
          relationshipsPanel.className = 'empty-state';
          relationshipsPanel.innerHTML = 'Seleziona una o più entità dalla lista a sinistra per vedere le relazioni in ingresso/uscita.';
          exportBtn.disabled = true;
          return;
        }

        const selected = Array.from(selectedEntityIds);
        const visibleRelationships = normalizedRelationships.filter(rel => selected.includes(rel.fromId) || selected.includes(rel.toId));

        exportBtn.disabled = false;

        if (visibleRelationships.length === 0) {
          relationshipsPanel.className = 'empty-state';
          relationshipsPanel.innerHTML = 'Nessuna relazione trovata per le entità selezionate.';
          return;
        }

        relationshipsPanel.className = '';
        relationshipsPanel.innerHTML = visibleRelationships.map(rel => {
          const fromEntity = entitiesById.get(rel.fromId);
          const toEntity = entitiesById.get(rel.toId);
          return `
            <div class='relationship-card'>
              <div class='relationship-title'>${fromEntity.name}.${rel.from_field || '?'} → ${toEntity.name}.${rel.to_field || '?'}</div>
              <div>source: ${rel.source || 'n/a'} • confidence: ${(rel.confidence ?? 0).toFixed(2)}</div>
            </div>
          `;
        }).join('');
      }

      function exportSelectedEntities() {
        const selectedEntities = model.entities.filter(entity => selectedEntityIds.has(entity.id));
        if (selectedEntities.length === 0) {
          return;
        }

        const rows = selectedEntities.flatMap(entity => {
          if (!entity.attributes || entity.attributes.length === 0) {
            return [{
              Entita: entity.name,
              Campo: '',
              Tipo: '',
              Nullable: '',
              SistemaSorgente: entity.source_system,
              TipoSorgente: entity.source_type,
            }];
          }
          return entity.attributes.map(attribute => ({
            Entita: entity.name,
            Campo: attribute.name,
            Tipo: attribute.type,
            Nullable: attribute.nullable,
            SistemaSorgente: entity.source_system,
            TipoSorgente: entity.source_type,
          }));
        });

        if (window.XLSX && window.XLSX.utils) {
          const sheet = XLSX.utils.json_to_sheet(rows);
          const workbook = XLSX.utils.book_new();
          XLSX.utils.book_append_sheet(workbook, sheet, 'CampiEntita');
          XLSX.writeFile(workbook, 'entita_selezionate.xlsx');
          return;
        }

        const header = Object.keys(rows[0]);
        const csv = [
          header.join(','),
          ...rows.map(row => header.map(key => JSON.stringify(row[key] ?? '')).join(',')),
        ].join('\n');
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'entita_selezionate.csv';
        a.click();
        URL.revokeObjectURL(a.href);
      }

      const listEl = document.getElementById('entity-list');
      model.entities.forEach(entity => {
        const card = document.createElement('div');
        card.className = 'entity-card';
        card.innerHTML = `
          <label>
            <input type='checkbox' data-entity-id='${entity.id}' />
            <span><strong>${entity.name}</strong><div class='meta'>${entity.source_system} • ${entity.source_type}</div></span>
          </label>
        `;
        const checkbox = card.querySelector('input');

        checkbox.addEventListener('change', () => {
          if (checkbox.checked) {
            selectedEntityIds.add(entity.id);
            card.classList.add('active');
          } else {
            selectedEntityIds.delete(entity.id);
            card.classList.remove('active');
          }
          network.selectNodes(Array.from(selectedEntityIds));
          updateRelationshipPanel();
        });

        card.addEventListener('dblclick', () => {
          network.focus(entity.id, { scale: 1, animation: { duration: 250 } });
        });
        listEl.appendChild(card);
      });

      exportBtn.addEventListener('click', exportSelectedEntities);
      updateRelationshipPanel();

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
