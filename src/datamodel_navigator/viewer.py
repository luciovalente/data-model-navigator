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
  <style>
    :root {
      --panel-bg: #f8f9fb;
      --border: #d7dbe2;
      --text: #111827;
      --muted: #6b7280;
      --accent: #241a8d;
      --card-bg: #ffffff;
      --grid: #eceff5;
      --line: #2f2966;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      font-family: Inter, Arial, sans-serif;
      color: var(--text);
      display: grid;
      grid-template-columns: 300px 1fr 360px;
      height: 100vh;
      overflow: hidden;
      background: #f2f4f8;
    }

    #left,
    #right {
      background: var(--panel-bg);
      overflow: auto;
      padding: 14px;
    }

    #left {
      border-right: 1px solid var(--border);
    }

    #right {
      border-left: 1px solid var(--border);
    }

    .section-title {
      margin: 0 0 10px;
      font-size: 13px;
      text-transform: uppercase;
      color: var(--muted);
      letter-spacing: 0.04em;
    }

    #entity-list {
      display: grid;
      gap: 8px;
      margin-bottom: 20px;
    }

    .entity-card {
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 8px 10px;
      background: #fff;
      transition: border-color 120ms ease, box-shadow 120ms ease;
      cursor: pointer;
    }

    .entity-card.active {
      border-color: #3730a3;
      box-shadow: 0 0 0 2px rgba(55, 48, 163, 0.15);
    }

    .entity-card .meta {
      font-size: 12px;
      color: var(--muted);
      margin-top: 4px;
    }

    .search-input {
      width: 100%;
      margin-bottom: 10px;
      border-radius: 8px;
      border: 1px solid var(--border);
      padding: 8px 10px;
      font-size: 13px;
    }

    #board {
      position: relative;
      height: 100%;
      overflow: hidden;
      background:
        radial-gradient(circle at 1px 1px, var(--grid) 1px, transparent 0) 0 0 / 24px 24px,
        #f4f5f9;
    }

    #board-controls {
      position: absolute;
      top: 12px;
      right: 12px;
      z-index: 10;
      display: flex;
      align-items: center;
      gap: 6px;
      background: rgba(255, 255, 255, 0.95);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 6px;
      box-shadow: 0 4px 14px rgba(15, 23, 42, 0.08);
    }

    .zoom-btn {
      border: 1px solid #c7ccda;
      background: #fff;
      width: 32px;
      height: 32px;
      border-radius: 8px;
      cursor: pointer;
      font-size: 20px;
      line-height: 1;
    }

    #zoom-label {
      min-width: 52px;
      text-align: center;
      font-size: 12px;
      color: var(--muted);
      font-weight: 700;
    }

    #canvas {
      position: absolute;
      inset: 0;
      transform-origin: 0 0;
    }

    #connector-layer {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      z-index: 1;
      pointer-events: auto;
    }

    .connector-path {
      pointer-events: stroke;
      cursor: pointer;
      transition: stroke 120ms ease, stroke-width 120ms ease;
    }

    .connector-path:hover {
      stroke: #4338ca;
      stroke-width: 3;
    }

    .connector-path.active {
      stroke: #1d4ed8;
      stroke-width: 3;
    }

    .board-entity {
      position: absolute;
      min-width: 240px;
      background: var(--card-bg);
      border-radius: 14px;
      box-shadow: 0 10px 24px rgba(15, 23, 42, 0.12);
      overflow: hidden;
      z-index: 2;
      user-select: none;
      border: 1px solid #e5e7eb;
    }

    .board-entity.selected {
      box-shadow: 0 0 0 3px rgba(55, 48, 163, 0.25), 0 12px 26px rgba(15, 23, 42, 0.18);
    }

    .board-entity-header {
      background: var(--accent);
      color: white;
      padding: 12px 14px;
      font-weight: 700;
      font-size: 20px;
      letter-spacing: 0.01em;
      cursor: grab;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
    }

    .board-entity.is-postgres .board-entity-header {
      --accent: #b91c1c;
    }

    .board-entity.is-mongo .board-entity-header {
      --accent: #1d4ed8;
    }

    .board-entity-header:active {
      cursor: grabbing;
    }

    .source-pill {
      background: rgba(255, 255, 255, 0.2);
      border-radius: 999px;
      font-size: 11px;
      padding: 2px 8px;
      white-space: nowrap;
      font-weight: 600;
    }

    .entity-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 22px;
    }

    .entity-table td {
      padding: 6px 14px;
      border-bottom: 1px solid #f3f4f6;
      white-space: nowrap;
    }

    .entity-table tr:last-child td {
      border-bottom: none;
    }

    .entity-table td:nth-child(2),
    .entity-table td:nth-child(3) {
      color: #111827;
      font-weight: 700;
      font-size: 18px;
    }

    .entity-table td:nth-child(3) {
      color: #1f2937;
      text-align: right;
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

    .relationship-title {
      font-weight: 700;
    }

    .empty-state {
      color: var(--muted);
      font-size: 13px;
      background: #fff;
      border: 1px dashed var(--border);
      border-radius: 8px;
      padding: 10px;
    }

    .btn {
      border: 1px solid #3730a3;
      background: #ede9fe;
      color: #312e81;
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

    #tips {
      font-size: 12px;
      color: var(--muted);
      line-height: 1.45;
      background: #fff;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 8px;
    }
  </style>
</head>
<body>
  <aside id='left'>
    <h2 style='margin: 0 0 12px;'>Data Model Navigator</h2>
    <h3 class='section-title'>Entità</h3>
    <input id='entity-search' class='search-input' type='search' placeholder='Cerca entità...' />
    <div id='entity-list'></div>
    <h3 class='section-title'>Suggerimenti</h3>
    <div id='tips'>
      • Clicca su una card per selezionarla.<br />
      • Trascina l'intestazione della card per spostarla.<br />
      • Le linee si aggiornano in tempo reale.<br />
      • Cerca entità usando il filtro.<br />
      • Clicca un'entità nella lista per centrarla.
    </div>
  </aside>

  <main id='board'>
    <div id='board-controls'>
      <button id='zoom-out' class='zoom-btn' title='Zoom out'>−</button>
      <div id='zoom-label'>100%</div>
      <button id='zoom-in' class='zoom-btn' title='Zoom in'>+</button>
    </div>
    <div id='canvas'>
      <svg id='connector-layer'></svg>
    </div>
  </main>

  <aside id='right'>
    <h3 class='section-title'>Relazioni Entità</h3>
    <div id='relationships-panel' class='empty-state'>
      Seleziona una o più entità per vedere le relazioni in ingresso/uscita.
    </div>
    <h3 class='section-title' style='margin-top:16px;'>Export campi entità selezionate</h3>
    <button id='export-excel' class='btn' disabled>Esporta in Excel (.xlsx)</button>
    <div class='empty-state'>
      L'export include: Entità, Campo, Tipo, Nullable, Sistema sorgente, Tipo sorgente.
    </div>
  </aside>

  <script id='model-data' type='application/json'>__MODEL_PAYLOAD__</script>
  <script src='https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js'></script>
  <script>
    const model = JSON.parse(document.getElementById('model-data').textContent);
    const entitiesById = new Map(model.entities.map(entity => [entity.id, entity]));
    const entitiesByName = new Map(model.entities.map(entity => [entity.name, entity]));
    const selectedEntityIds = new Set();
    let activeRelationshipId = null;

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

    const board = document.getElementById('board');
    const canvas = document.getElementById('canvas');
    const connectorLayer = document.getElementById('connector-layer');
    const entityElements = new Map();
    const listEntries = new Map();
    let scale = 1;
    let translateX = 0;
    let translateY = 0;

    function applyViewport() {
      canvas.style.transform = `translate(${translateX}px, ${translateY}px) scale(${scale})`;
      document.getElementById('zoom-label').textContent = `${Math.round(scale * 100)}%`;
      drawConnectors();
    }

    function zoomBy(delta) {
      scale = Math.max(0.5, Math.min(2, Number((scale + delta).toFixed(2))));
      applyViewport();
    }

    function centerEntity(entityId) {
      const card = entityElements.get(entityId);
      if (!card) {
        return;
      }
      const x = card.offsetLeft + card.offsetWidth / 2;
      const y = card.offsetTop + card.offsetHeight / 2;
      translateX = board.clientWidth / 2 - x * scale;
      translateY = board.clientHeight / 2 - y * scale;
      applyViewport();
    }

    function attributeRole(attributeName) {
      if (!attributeName) {
        return '';
      }
      const hasOutgoing = normalizedRelationships.some(rel => rel.from_field === attributeName);
      const hasIncoming = normalizedRelationships.some(rel => rel.to_field === attributeName);
      if (hasOutgoing) {
        return 'FK';
      }
      if (hasIncoming) {
        return 'PK';
      }
      return '';
    }

    function createEntityNode(entity, idx) {
      const card = document.createElement('article');
      card.className = 'board-entity';
      const sourceType = `${entity.source_type || ''} ${entity.source_system || ''}`.toLowerCase();
      if (sourceType.includes('postgres')) {
        card.classList.add('is-postgres');
      } else if (sourceType.includes('mongo')) {
        card.classList.add('is-mongo');
      }
      card.dataset.entityId = entity.id;

      const row = Math.floor(idx / 3);
      const col = idx % 3;
      card.style.left = `${50 + col * 320}px`;
      card.style.top = `${40 + row * 280}px`;

      const header = document.createElement('header');
      header.className = 'board-entity-header';
      header.innerHTML = `<span>${entity.name}</span><span class='source-pill'>${entity.source_system || 'unknown'}</span>`;

      const table = document.createElement('table');
      table.className = 'entity-table';
      const rows = (entity.attributes || []).map(attribute => {
        const role = attributeRole(attribute.name);
        return `<tr><td>${attribute.name}</td><td>${attribute.type || ''}</td><td>${role}</td></tr>`;
      }).join('');
      table.innerHTML = rows || "<tr><td colspan='3' style='color:#6b7280;'>Nessun attributo</td></tr>";

      card.appendChild(header);
      card.appendChild(table);
      canvas.appendChild(card);
      entityElements.set(entity.id, card);

      card.addEventListener('click', () => {
        activeRelationshipId = null;
        if (selectedEntityIds.has(entity.id)) {
          selectedEntityIds.delete(entity.id);
        } else {
          selectedEntityIds.add(entity.id);
        }
        syncSelections();
        centerEntity(entity.id);
      });

      enableDrag(card, header);
    }

    function enableDrag(card, handle) {
      let dragging = false;
      let pointerId = null;
      let offsetX = 0;
      let offsetY = 0;

      handle.addEventListener('pointerdown', (event) => {
        dragging = true;
        pointerId = event.pointerId;
        const boardRect = board.getBoundingClientRect();
        offsetX = (event.clientX - boardRect.left - translateX) / scale - card.offsetLeft;
        offsetY = (event.clientY - boardRect.top - translateY) / scale - card.offsetTop;
        handle.setPointerCapture(pointerId);
        event.preventDefault();
      });

      handle.addEventListener('pointermove', (event) => {
        if (!dragging || event.pointerId !== pointerId) {
          return;
        }
        const boardRect = board.getBoundingClientRect();
        const localX = (event.clientX - boardRect.left - translateX) / scale;
        const localY = (event.clientY - boardRect.top - translateY) / scale;
        const x = localX - offsetX;
        const y = localY - offsetY;
        card.style.left = `${x}px`;
        card.style.top = `${y}px`;
        drawConnectors();
      });

      function stopDrag(event) {
        if (event.pointerId !== pointerId) {
          return;
        }
        dragging = false;
        handle.releasePointerCapture(pointerId);
        pointerId = null;
      }

      handle.addEventListener('pointerup', stopDrag);
      handle.addEventListener('pointercancel', stopDrag);
    }

    function getAnchorPoint(entityId, side) {
      const card = entityElements.get(entityId);
      if (side === 'left') {
        return { x: card.offsetLeft, y: card.offsetTop + card.offsetHeight / 2 };
      }
      return { x: card.offsetLeft + card.offsetWidth, y: card.offsetTop + card.offsetHeight / 2 };
    }

    function drawEndpointGlyph(svg, point, direction, kind) {
      const stroke = getComputedStyle(document.documentElement).getPropertyValue('--line').trim() || '#2f2966';
      const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      group.style.pointerEvents = 'none';
      if (kind === 'PK') {
        const a = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        const b = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        [a, b].forEach((line, idx) => {
          const shift = idx === 0 ? 0 : 4;
          line.setAttribute('x1', `${point.x + direction * shift}`);
          line.setAttribute('y1', `${point.y - 8}`);
          line.setAttribute('x2', `${point.x + direction * shift}`);
          line.setAttribute('y2', `${point.y + 8}`);
          line.setAttribute('stroke', stroke);
          line.setAttribute('stroke-width', '2');
          group.appendChild(line);
        });
      } else {
        const l1 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        const l2 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        const l3 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        const endX = point.x + direction * 10;
        [[point.x, point.y, endX, point.y - 8], [point.x, point.y, endX, point.y + 8], [point.x, point.y, endX, point.y]].forEach((coords, idx) => {
          const line = [l1, l2, l3][idx];
          line.setAttribute('x1', `${coords[0]}`);
          line.setAttribute('y1', `${coords[1]}`);
          line.setAttribute('x2', `${coords[2]}`);
          line.setAttribute('y2', `${coords[3]}`);
          line.setAttribute('stroke', stroke);
          line.setAttribute('stroke-width', '2');
          group.appendChild(line);
        });
      }
      svg.appendChild(group);
    }

    function drawConnectors() {
      connectorLayer.innerHTML = '';
      const width = board.clientWidth;
      const height = board.clientHeight;
      connectorLayer.setAttribute('width', `${width}`);
      connectorLayer.setAttribute('height', `${height}`);
      connectorLayer.setAttribute('viewBox', `0 0 ${width} ${height}`);

      normalizedRelationships.forEach(rel => {
        const from = entityElements.get(rel.fromId);
        const to = entityElements.get(rel.toId);
        if (!from || !to) {
          return;
        }

        const fromSide = from.offsetLeft <= to.offsetLeft ? 'right' : 'left';
        const toSide = from.offsetLeft <= to.offsetLeft ? 'left' : 'right';
        const start = getAnchorPoint(rel.fromId, fromSide);
        const end = getAnchorPoint(rel.toId, toSide);

        const delta = Math.max(60, Math.abs(end.x - start.x) * 0.5);
        const c1x = fromSide === 'right' ? start.x + delta : start.x - delta;
        const c2x = toSide === 'left' ? end.x - delta : end.x + delta;

        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', `M ${start.x} ${start.y} C ${c1x} ${start.y}, ${c2x} ${end.y}, ${end.x} ${end.y}`);
        path.setAttribute('fill', 'none');
        path.setAttribute('stroke', '#2f2966');
        path.setAttribute('stroke-width', '2');
        path.classList.add('connector-path');
        if (activeRelationshipId === rel.id) {
          path.classList.add('active');
        }
        path.addEventListener('click', (event) => {
          event.stopPropagation();
          activeRelationshipId = rel.id;
          selectedEntityIds.clear();
          selectedEntityIds.add(rel.fromId);
          selectedEntityIds.add(rel.toId);
          syncSelections();
          drawConnectors();
        });
        connectorLayer.appendChild(path);

        drawEndpointGlyph(connectorLayer, start, fromSide === 'right' ? 1 : -1, 'FK');
        drawEndpointGlyph(connectorLayer, end, toSide === 'left' ? -1 : 1, 'PK');
      });
    }

    function updateRelationshipPanel() {
      const relationshipsPanel = document.getElementById('relationships-panel');
      const exportBtn = document.getElementById('export-excel');

      if (activeRelationshipId) {
        const rel = normalizedRelationships.find(item => item.id === activeRelationshipId);
        if (rel) {
          const fromEntity = entitiesById.get(rel.fromId);
          const toEntity = entitiesById.get(rel.toId);
          relationshipsPanel.className = '';
          relationshipsPanel.innerHTML = `
            <div class='relationship-card'>
              <div class='relationship-title'>Relazione selezionata</div>
              <div><strong>Entità origine:</strong> ${fromEntity.name}</div>
              <div><strong>Campo FK:</strong> ${rel.from_field || '?'}</div>
              <div><strong>Entità destinazione:</strong> ${toEntity.name}</div>
              <div><strong>Campo PK:</strong> ${rel.to_field || '?'}</div>
              <div style='margin-top:6px;'>source: ${rel.source || 'n/a'} • confidence: ${(rel.confidence ?? 0).toFixed(2)}</div>
            </div>
          `;
          exportBtn.disabled = false;
          return;
        }
      }

      if (selectedEntityIds.size === 0) {
        relationshipsPanel.className = 'empty-state';
        relationshipsPanel.innerHTML = 'Seleziona una o più entità per vedere le relazioni in ingresso/uscita.';
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

    function syncSelections() {
      model.entities.forEach(entity => {
        const node = entityElements.get(entity.id);
        const listCard = listEntries.get(entity.id);
        const active = selectedEntityIds.has(entity.id);
        node.classList.toggle('selected', active);
        listCard.classList.toggle('active', active);
      });
      updateRelationshipPanel();
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
      ].join('\\n');
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = 'entita_selezionate.csv';
      a.click();
      URL.revokeObjectURL(a.href);
    }

    const listEl = document.getElementById('entity-list');
    model.entities.forEach((entity, idx) => {
      createEntityNode(entity, idx);

      const card = document.createElement('div');
      card.className = 'entity-card';
      card.innerHTML = `<strong>${entity.name}</strong><div class='meta'>${entity.source_system} • ${entity.source_type}</div>`;
      card.addEventListener('click', () => {
        activeRelationshipId = null;
        if (selectedEntityIds.has(entity.id)) {
          selectedEntityIds.delete(entity.id);
        } else {
          selectedEntityIds.add(entity.id);
        }
        syncSelections();
        centerEntity(entity.id);
      });
      listEl.appendChild(card);
      listEntries.set(entity.id, card);
    });

    window.addEventListener('resize', drawConnectors);
    document.getElementById('export-excel').addEventListener('click', exportSelectedEntities);

    document.getElementById('entity-search').addEventListener('input', (event) => {
      const query = event.target.value.trim().toLowerCase();
      model.entities.forEach((entity) => {
        const card = listEntries.get(entity.id);
        const content = `${entity.name} ${entity.source_system || ''} ${entity.source_type || ''}`.toLowerCase();
        card.style.display = content.includes(query) ? '' : 'none';
      });
    });

    document.getElementById('zoom-in').addEventListener('click', () => zoomBy(0.1));
    document.getElementById('zoom-out').addEventListener('click', () => zoomBy(-0.1));

    syncSelections();
    applyViewport();
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
