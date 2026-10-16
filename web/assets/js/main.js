/**
 * main.js - Orquestador general del Research Lab & CV Interactivo (Edición Editorial)
 */

import { KnowledgeGraph } from './graph.js?v=20261011-4';
import { AIAssistant } from './assistant.js?v=20261011-4';

let cvData = null;
let graphInstance = null;
let assistantInstance = null;

// Cargar data.json con cache-busting para evitar estados obsoletos
async function loadData() {
  try {
    const res = await fetch(`data.json?v=${Date.now()}`);
    if (!res.ok) throw new Error('Error al cargar data.json');
    cvData = await res.json();
    initApp();
  } catch (err) {
    console.error('Error cargando datos:', err);
  }
}

function initApp() {
  renderMetrics();
  initKnowledgeGraph();
  initAssistant();
  renderTimeline('leadership');
  renderPublications('all', '');
  renderProjects('projects');
  renderEducation();
  renderCertifications();
  setupEventListeners();
}

// 1. Renderizar Métricas Instrumentales
function renderMetrics() {
  const container = document.getElementById('metrics-grid');
  if (!container || !cvData.metrics) return;

  container.innerHTML = cvData.metrics.map(m => `
    <div class="p-4 rounded-xl bg-surface-card border border-white/[0.08] hover:border-white/[0.15] transition">
      <div class="font-serif text-3xl sm:text-4xl font-normal text-amber-200">
        ${m.value}
      </div>
      <div class="text-xs font-semibold text-white mt-1">${m.label}</div>
      <div class="font-mono text-[11px] text-slate-400 mt-0.5">${m.subtext}</div>
    </div>
  `).join('');
}

// 2. Inicializar Knowledge Graph Observatory
function initKnowledgeGraph() {
  if (!cvData.knowledgeGraph) return;

  // Actualizar conteos dinámicos en los botones de cluster
  const nodes = cvData.knowledgeGraph.nodes || [];
  const counts = {
    all: nodes.length,
    ia_data_science: nodes.filter(n => n.cluster === 'ia_data_science').length,
    politicas_direccion: nodes.filter(n => n.cluster === 'politicas_direccion').length,
    tecnopedagogia: nodes.filter(n => n.cluster === 'tecnopedagogia').length
  };

  const btnAll = document.querySelector('.cluster-btn[data-cluster="all"]');
  const btnIA = document.querySelector('.cluster-btn[data-cluster="ia_data_science"]');
  const btnPol = document.querySelector('.cluster-btn[data-cluster="politicas_direccion"]');
  const btnTec = document.querySelector('.cluster-btn[data-cluster="tecnopedagogia"]');

  if (btnAll) btnAll.textContent = `Todos (${counts.all})`;
  if (btnIA) btnIA.textContent = `● IA & Data (${counts.ia_data_science})`;
  if (btnPol) btnPol.textContent = `● Políticas (${counts.politicas_direccion})`;
  if (btnTec) btnTec.textContent = `● Tecnopedagogía (${counts.tecnopedagogia})`;

  graphInstance = new KnowledgeGraph('knowledge-graph-container', cvData.knowledgeGraph, {
    onNodeClick: (node) => {
      showNodeDetail(node);
    }
  });

  // Filtros de cluster
  const clusterBtns = document.querySelectorAll('.cluster-btn');
  const setActiveClusterBtn = (activeBtn) => {
    clusterBtns.forEach(b => {
      b.classList.remove('bg-white/[0.15]', 'ring-1', 'ring-white/20', 'font-bold');
      if (b.getAttribute('data-cluster') === 'all') {
        b.classList.remove('bg-white/[0.1]');
        b.classList.add('text-slate-400');
      }
    });
    if (activeBtn) {
      activeBtn.classList.add('bg-white/[0.15]', 'ring-1', 'ring-white/20', 'font-bold');
      if (activeBtn.getAttribute('data-cluster') === 'all') {
        activeBtn.classList.remove('text-slate-400');
        activeBtn.classList.add('text-white');
      }
    }
  };

  clusterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      setActiveClusterBtn(btn);
      const cluster = btn.getAttribute('data-cluster');
      graphInstance.setCluster(cluster);
      if (cluster === 'keywords') {
        const kwNodes = graphInstance.nodes.filter(n => n.cluster === 'keywords' || n.type === 'keyword');
        if (kwNodes.length > 0) {
          graphInstance.focusOnNodes(kwNodes);
        }
      }
    });
  });

  // Controles de zoom
  const zoomIn = document.getElementById('graph-zoom-in');
  const zoomOut = document.getElementById('graph-zoom-out');
  const resetBtn = document.getElementById('reset-graph-btn');

  if (zoomIn) zoomIn.addEventListener('click', () => graphInstance.zoomBy(1.15));
  if (zoomOut) zoomOut.addEventListener('click', () => graphInstance.zoomBy(0.85));

  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      graphInstance.resetView();
      if (btnAll) setActiveClusterBtn(btnAll);
      const panel = document.getElementById('node-detail-panel');
      if (panel) panel.classList.add('hidden');
    });
  }

  // Cerrar panel de detalle
  const closeDetailBtn = document.getElementById('close-detail-btn');
  if (closeDetailBtn) {
    closeDetailBtn.addEventListener('click', () => {
      document.getElementById('node-detail-panel').classList.add('hidden');
      if (graphInstance) graphInstance.clearKeywordHighlight();
    });
  }
}

let currentDetailNode = null;

function showNodeDetail(node) {
  currentDetailNode = node;
  const panel = document.getElementById('node-detail-panel');
  if (!panel) return;

  const titleEl = document.getElementById('detail-node-title');
  const clusterEl = document.getElementById('detail-node-cluster');
  const descEl = document.getElementById('detail-node-desc');
  const kwsEl = document.getElementById('detail-node-keywords');
  const linksEl = document.getElementById('detail-node-links');

  titleEl.textContent = node.label;
  descEl.textContent = node.info || 'Elemento del espacio latente de investigación y trayectoria.';

  let clusterName = 'Dimensión General';
  let badgeClass = 'bg-white/[0.06] text-slate-300 border border-white/[0.08]';
  if (node.cluster === 'ia_data_science') {
    clusterName = 'IA & Data Science';
    badgeClass = 'bg-sky-500/10 text-sky-400 border border-sky-500/20';
  } else if (node.cluster === 'politicas_direccion') {
    clusterName = 'Políticas & Dirección';
    badgeClass = 'bg-purple-500/10 text-purple-400 border border-purple-500/20';
  } else if (node.cluster === 'tecnopedagogia') {
    clusterName = 'Tecnopedagogía & Aprendizaje';
    badgeClass = 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
  } else if (node.cluster === 'keywords' || node.type === 'keyword') {
    clusterName = 'Palabra Clave Transversal';
    badgeClass = 'bg-amber-500/10 text-amber-400 border border-amber-500/20';
  }

  clusterEl.textContent = clusterName;
  clusterEl.className = `font-mono text-[10px] uppercase tracking-wider px-2.5 py-0.5 rounded ${badgeClass}`;

  // Si el nodo seleccionado es directamente una palabra clave, abrir la vista de exploración de esa palabra clave
  if (node.type === 'keyword' || node.cluster === 'keywords') {
    exploreKeyword(node.label.replace('...', '').trim(), null);
    panel.classList.remove('hidden');
    return;
  }

  // Renderizar Palabras Clave del Nodo (Pills Clicables para navegar)
  let nodeKws = (node.keywords && node.keywords.length > 0) ? [...node.keywords] : [];
  if (nodeKws.length === 0) {
    const hay = ((node.label || '') + ' ' + (node.info || '')).toLowerCase();
    if (node.cluster === 'ia_data_science') nodeKws.push('IA & Data Science');
    else if (node.cluster === 'politicas_direccion') nodeKws.push('Políticas Públicas', 'Gobernanza Digital');
    else if (node.cluster === 'tecnopedagogia') nodeKws.push('Tecnopedagogía', 'E-Learning');

    if (hay.includes('deep learning') || hay.includes('llm') || hay.includes('lenguaje') || hay.includes('inteligencia artificial') || hay.includes('ia')) {
      if (!nodeKws.includes('Deep Learning & LLMs')) nodeKws.push('Deep Learning & LLMs');
    }
    if (hay.includes('cognitivo') || hay.includes('cdm') || hay.includes('psicométrico')) {
      if (!nodeKws.includes('Diagnóstico Cognitivo & CDM')) nodeKws.push('Diagnóstico Cognitivo & CDM');
    }
    if (hay.includes('neuro') || hay.includes('ontolog')) {
      if (!nodeKws.includes('Modelos Neuro-Simbólicos')) nodeKws.push('Modelos Neuro-Simbólicos');
    }
    if (hay.includes('moodle') || hay.includes('lms')) {
      if (!nodeKws.includes('LMS Moodle a Escala')) nodeKws.push('LMS Moodle a Escala');
    }
    if (hay.includes('sabana') || hay.includes('uoc') || hay.includes('universidad') || hay.includes('docencia')) {
      if (!nodeKws.includes('Calidad y Docencia Universitaria')) nodeKws.push('Calidad y Docencia Universitaria');
    }
  }

  if (kwsEl) {
    if (nodeKws.length > 0) {
      kwsEl.innerHTML = `
        <div class="text-[10px] font-mono uppercase tracking-wider text-amber-400 font-semibold mb-2 flex items-center gap-1.5">
          <i class="fa-solid fa-tags text-[10px]"></i> Palabras clave (${nodeKws.length}):
        </div>
        <div class="flex flex-wrap gap-1.5">
          ${nodeKws.map(kw => `
            <button class="node-kw-pill px-2.5 py-1 rounded-lg bg-amber-500/15 hover:bg-amber-500/30 active:scale-95 text-amber-300 hover:text-white border border-amber-500/30 text-[11px] font-mono transition flex items-center gap-1.5 cursor-pointer shadow-sm" data-keyword="${kw}" title="Explorar nodos con '${kw}'">
              <i class="fa-solid fa-tag text-[9px] opacity-75"></i>
              <span>${kw}</span>
            </button>
          `).join('')}
        </div>
      `;
      kwsEl.querySelectorAll('.node-kw-pill').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          const kw = btn.getAttribute('data-keyword');
          exploreKeyword(kw, node);
        });
      });
    } else {
      kwsEl.innerHTML = '';
    }
  }

  // Elementos relacionados del CV
  const query = node.label.toLowerCase().replace('...', '').trim();
  const searchInText = (txt) => (txt || '').toLowerCase().includes(query);

  const relatedPubs = (cvData.publications || []).filter(p => 
    searchInText(p.title) || (p.keywords && p.keywords.some(k => searchInText(k)))
  );

  const relatedProjects = (cvData.projects || []).filter(p => 
    searchInText(p.title) || searchInText(p.organization) || (p.tags && p.tags.some(t => searchInText(t)))
  );

  const relatedCerts = (cvData.certifications || []).filter(c => 
    searchInText(c.title) || (c.skills && c.skills.some(s => searchInText(s)))
  );

  linksEl.innerHTML = '';
  if (relatedPubs.length > 0) {
    linksEl.innerHTML += `<div class="font-mono text-[10px] uppercase tracking-wider text-amber-400 mt-2">Publicaciones indexadas:</div>`;
    relatedPubs.slice(0, 2).forEach(rp => {
      linksEl.innerHTML += `
        <div class="p-2 rounded-lg bg-white/[0.03] border border-white/[0.06] text-xs mt-1">
          <div class="font-semibold text-white line-clamp-1">${rp.title}</div>
          <div class="font-mono text-[10px] text-slate-400 mt-0.5">${rp.year || ''} • ${rp.publisher || 'Artículo'}</div>
        </div>
      `;
    });
  }

  if (relatedProjects.length > 0) {
    linksEl.innerHTML += `<div class="font-mono text-[10px] uppercase tracking-wider text-purple-400 mt-2">Iniciativas y Proyectos:</div>`;
    relatedProjects.slice(0, 2).forEach(rp => {
      linksEl.innerHTML += `
        <div class="p-2 rounded-lg bg-white/[0.03] border border-white/[0.06] text-xs mt-1">
          <div class="font-semibold text-white line-clamp-1">${rp.title}</div>
          <div class="font-mono text-[10px] text-slate-400 mt-0.5">${rp.organization} (${rp.year})</div>
        </div>
      `;
    });
  }

  if (relatedCerts.length > 0) {
    linksEl.innerHTML += `<div class="font-mono text-[10px] uppercase tracking-wider text-sky-400 mt-2">Credenciales y Méritos:</div>`;
    relatedCerts.slice(0, 2).forEach(rc => {
      linksEl.innerHTML += `
        <div class="p-2 rounded-lg bg-white/[0.03] border border-white/[0.06] text-xs mt-1">
          <div class="font-semibold text-white line-clamp-1">${rc.title}</div>
          <div class="font-mono text-[10px] text-slate-400 mt-0.5">${rc.issuer} (${rc.year})</div>
        </div>
      `;
    });
  }

  panel.classList.remove('hidden');
}

function exploreKeyword(kw, originNode) {
  if (!graphInstance || !kw) return;

  // 1. Iluminar en el canvas los nodos con esta palabra clave y centrar cámara
  graphInstance.highlightKeyword(kw);

  const panel = document.getElementById('node-detail-panel');
  if (!panel) return;

  const titleEl = document.getElementById('detail-node-title');
  const clusterEl = document.getElementById('detail-node-cluster');
  const descEl = document.getElementById('detail-node-desc');
  const kwsEl = document.getElementById('detail-node-keywords');
  const linksEl = document.getElementById('detail-node-links');

  clusterEl.textContent = 'Exploración por Palabra Clave';
  clusterEl.className = 'font-mono text-[10px] uppercase tracking-wider px-2.5 py-0.5 rounded bg-amber-500/15 text-amber-300 border border-amber-500/30';

  titleEl.innerHTML = `<span class="flex items-center gap-2"><i class="fa-solid fa-tag text-amber-400 text-sm"></i> ${kw}</span>`;
  
  // Buscar nodos del grafo que contengan esta palabra clave
  const kwLower = kw.toLowerCase();
  const matchingGraphNodes = (graphInstance.nodes || []).filter(n => {
    if (n.type === 'cluster_root' || n.type === 'root') return false;
    const nodeKws = (n.keywords || []).map(k => String(k).toLowerCase());
    return n.label.toLowerCase().includes(kwLower) ||
           nodeKws.some(k => k.includes(kwLower) || kwLower.includes(k));
  });

  descEl.innerHTML = `
    Navegando entre <strong>${matchingGraphNodes.length} nodos del grafo</strong> que comparten este concepto clave.
    Haz clic en cualquiera para viajar a él directamente en el espacio latente:
  `;

  // Botón para volver al nodo de origen si existe
  if (kwsEl) {
    if (originNode) {
      kwsEl.innerHTML = `
        <button id="back-to-origin-btn" class="w-full text-left px-3 py-1.5 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] border border-white/[0.08] text-xs text-slate-300 hover:text-white transition flex items-center justify-between cursor-pointer">
          <span>← Volver a: <strong>${originNode.label}</strong></span>
          <i class="fa-solid fa-rotate-left text-[10px]"></i>
        </button>
      `;
      const backBtn = document.getElementById('back-to-origin-btn');
      if (backBtn) {
        backBtn.addEventListener('click', () => {
          graphInstance.clearKeywordHighlight();
          showNodeDetail(originNode);
        });
      }
    } else {
      kwsEl.innerHTML = `
        <button id="reset-kw-highlight-btn" class="w-full text-left px-3 py-1.5 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] border border-white/[0.08] text-xs text-slate-300 hover:text-white transition flex items-center justify-between cursor-pointer">
          <span>← Restablecer vista del grafo</span>
          <i class="fa-solid fa-expand text-[10px]"></i>
        </button>
      `;
      const rstBtn = document.getElementById('reset-kw-highlight-btn');
      if (rstBtn) {
        rstBtn.addEventListener('click', () => {
          graphInstance.clearKeywordHighlight();
          panel.classList.add('hidden');
        });
      }
    }
  }

  // Lista de Nodos clicables para navegar
  const typeBadgeMeta = {
    publication: { label: "Publicación", color: "text-amber-400 bg-amber-500/10 border-amber-500/20" },
    project: { label: "Proyecto", color: "text-purple-400 bg-purple-500/10 border-purple-500/20" },
    repository: { label: "Repositorio", color: "text-sky-400 bg-sky-500/10 border-sky-500/20" },
    blog_post: { label: "Ensayo Quartz", color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20" },
    certification: { label: "Certificación", color: "text-blue-400 bg-blue-500/10 border-blue-500/20" },
    pillar: { label: "Pilar", color: "text-indigo-400 bg-indigo-500/10 border-indigo-500/20" },
    keyword: { label: "Palabra Clave", color: "text-amber-400 bg-amber-500/10 border-amber-500/20" }
  };

  linksEl.innerHTML = `
    <div class="space-y-1.5 mt-2">
      ${matchingGraphNodes.map(mn => {
        const meta = typeBadgeMeta[mn.type] || { label: mn.type || "Nodo", color: "text-slate-400 bg-white/[0.05] border-white/[0.08]" };
        const isCurrent = originNode && originNode.id === mn.id;
        return `
          <div class="p-2.5 rounded-xl ${isCurrent ? 'bg-amber-500/15 border-amber-500/40' : 'bg-white/[0.03] hover:bg-white/[0.08] border-white/[0.06] hover:border-amber-400/40'} border transition cursor-pointer group node-jump-item" data-node-id="${mn.id}">
            <div class="flex items-center justify-between text-[10px] font-mono mb-1">
              <span class="px-1.5 py-0.2 rounded border text-[9px] ${meta.color}">${meta.label}</span>
              <span class="text-amber-400/70 group-hover:text-amber-300 transition flex items-center gap-1 font-sans text-[11px]">
                ${isCurrent ? '● Nodo actual' : 'Ver nodo →'}
              </span>
            </div>
            <div class="font-semibold text-white text-xs group-hover:text-amber-200 transition line-clamp-1">${mn.label}</div>
            <div class="text-[10px] text-slate-400 line-clamp-1 mt-0.5">${mn.info || ''}</div>
          </div>
        `;
      }).join('')}
    </div>
  `;

  // Asignar listeners de navegación a cada tarjeta de nodo
  linksEl.querySelectorAll('.node-jump-item').forEach(item => {
    item.addEventListener('click', () => {
      const nodeId = item.getAttribute('data-node-id');
      if (nodeId && graphInstance) {
        graphInstance.selectNodeById(nodeId);
      }
    });
  });

  panel.classList.remove('hidden');
}

// 3. Inicializar Asistente de IA
function initAssistant() {
  assistantInstance = new AIAssistant(cvData, 'ai-chat-root');
}

// 4. Renderizar Timeline (Ledger de Liderazgo vs Docencia)
function renderTimeline(mode) {
  const container = document.getElementById('timeline-content');
  if (!container) return;

  if (mode === 'leadership') {
    const list = cvData.workExperience || [];
    container.innerHTML = list.map(item => `
      <div class="p-5 rounded-xl bg-surface-card border border-white/[0.08] hover:border-white/[0.14] transition">
        <div class="flex flex-col sm:flex-row sm:items-baseline justify-between gap-1 mb-2">
          <div>
            <span class="font-mono text-xs font-semibold text-emerald-400 tracking-wider">${item.period}</span>
            <h3 class="font-serif text-lg font-bold text-white mt-0.5">${item.organization}</h3>
            ${item.unit ? `<span class="text-xs text-slate-400">${item.unit}</span>` : ''}
          </div>
          <span class="inline-block px-3 py-1 rounded-full bg-white/[0.04] text-xs font-mono text-slate-300 border border-white/[0.06] self-start sm:self-auto">
            ${item.role}
          </span>
        </div>
        <p class="text-xs sm:text-[13px] text-slate-300 leading-relaxed mt-2 font-sans">
          ${item.description}
        </p>
        ${item.links && item.links.length > 0 ? `
          <div class="mt-3 flex flex-wrap gap-2 pt-2 border-t border-white/[0.04]">
            ${item.links.map(l => `
              <a href="${l.url}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-white/[0.04] hover:bg-emerald-500/10 text-emerald-400 hover:text-emerald-300 border border-white/[0.08] hover:border-emerald-500/30 font-mono text-[11px] transition">
                <i class="fa-brands fa-google-drive"></i>
                <span>${l.label || 'Ver Respaldo'}</span>
                <i class="fa-solid fa-arrow-up-right-from-square text-[9px] opacity-70"></i>
              </a>
            `).join('')}
          </div>
        ` : ''}
      </div>
    `).join('');
  } else {
    const list = cvData.teachingExperience || [];
    container.innerHTML = list.map(item => `
      <div class="p-5 rounded-xl bg-surface-card border border-white/[0.08] hover:border-white/[0.14] transition">
        <div class="flex flex-col sm:flex-row sm:items-baseline justify-between gap-1 mb-2">
          <div>
            <span class="font-mono text-xs font-semibold text-sky-400 tracking-wider">${item.period}</span>
            <h3 class="font-serif text-lg font-bold text-white mt-0.5">${item.institution}</h3>
          </div>
          <span class="inline-block px-3 py-1 rounded-full bg-white/[0.04] text-xs font-mono text-slate-300 border border-white/[0.06] self-start sm:self-auto">
            ${item.role}
          </span>
        </div>
        ${item.subjects ? `
          <div class="mt-2 mb-2 p-3 rounded-lg bg-white/[0.03] border border-white/[0.06] text-xs">
            <span class="font-mono font-semibold text-sky-400">Asignaturas:</span>
            <span class="text-slate-200 ml-1">${item.subjects}</span>
          </div>
        ` : ''}
        <p class="text-xs sm:text-[13px] text-slate-300 leading-relaxed font-sans">
          ${item.description}
        </p>
        ${item.links && item.links.length > 0 ? `
          <div class="mt-3 flex flex-wrap gap-2 pt-2 border-t border-white/[0.04]">
            ${item.links.map(l => `
              <a href="${l.url}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-white/[0.04] hover:bg-sky-500/10 text-sky-400 hover:text-sky-300 border border-white/[0.08] hover:border-sky-500/30 font-mono text-[11px] transition">
                <i class="fa-brands fa-google-drive"></i>
                <span>${l.label || 'Ver Respaldo'}</span>
                <i class="fa-solid fa-arrow-up-right-from-square text-[9px] opacity-70"></i>
              </a>
            `).join('')}
          </div>
        ` : ''}
      </div>
    `).join('');
  }
}

// 5. Renderizar Publicaciones (Buscador + DOI + BibTeX)
function renderPublications(clusterFilter = 'all', searchQuery = '') {
  const container = document.getElementById('publications-grid');
  if (!container || !cvData.publications) return;

  let filtered = cvData.publications;
  if (clusterFilter !== 'all') {
    filtered = filtered.filter(p => p.cluster === clusterFilter);
  }
  if (searchQuery.trim()) {
    const q = searchQuery.toLowerCase();
    filtered = filtered.filter(p => 
      p.title.toLowerCase().includes(q) ||
      p.authors.some(a => a.toLowerCase().includes(q)) ||
      (p.venue && p.venue.toLowerCase().includes(q))
    );
  }

  if (filtered.length === 0) {
    container.innerHTML = `<div class="col-span-2 p-8 text-center text-slate-400 font-mono text-xs">No se localizaron registros para los criterios especificados.</div>`;
    return;
  }

  container.innerHTML = filtered.map(pub => {
    const isSpringer = pub.publisher && pub.publisher.includes('Springer');
    const badgeClass = pub.cluster === 'ia_data_science' ? 'text-sky-400 border-sky-500/20 bg-sky-500/10' : 'text-emerald-400 border-emerald-500/20 bg-emerald-500/10';

    return `
      <div class="p-5 rounded-xl bg-surface-card border border-white/[0.08] hover:border-white/[0.14] transition flex flex-col justify-between group">
        <div>
          <div class="flex items-center justify-between gap-2 mb-2">
            <span class="font-mono text-[10px] uppercase tracking-wider px-2 py-0.5 rounded border ${badgeClass}">
              ${pub.year} · ${pub.type}
            </span>
            ${isSpringer ? `<span class="font-mono text-[10px] text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">SPRINGER NATURE</span>` : ''}
          </div>
          
          <h4 class="font-serif text-base font-medium text-white group-hover:text-amber-300 transition leading-snug">
            ${pub.title}
          </h4>

          <div class="text-xs text-slate-400 mt-2 font-sans">
            <span class="font-medium text-slate-300">Autores:</span> ${pub.authors.join(', ')}
          </div>

          <div class="text-xs text-slate-400 mt-1 font-sans">
            <span class="font-medium text-slate-300">Publicado en:</span> <em class="text-slate-300">${pub.venue || pub.publisher}</em>
          </div>

          ${pub.abstract ? `
            <details class="mt-3 text-xs text-slate-300 font-sans">
              <summary class="cursor-pointer text-amber-400/90 hover:text-amber-300 font-mono text-[11px]">Resumen (Abstract)</summary>
              <p class="mt-2 text-slate-400 text-xs leading-relaxed bg-white/[0.02] p-3 rounded-lg border border-white/[0.06]">
                ${pub.abstract}
              </p>
            </details>
          ` : ''}
        </div>

        <div class="mt-4 pt-3 border-t border-white/[0.06] flex items-center justify-between gap-2 font-mono text-xs">
          ${pub.url ? `
            <a href="${pub.url}" target="_blank" class="text-sky-400 hover:text-sky-300 flex items-center gap-1.5 text-[11px]">
              <i class="fa-solid fa-arrow-up-right-from-square text-[9px]"></i>
              ${pub.doi ? `DOI: ${pub.doi}` : 'Ver publicación'}
            </a>
          ` : `<span></span>`}

          <button class="copy-bib-btn text-slate-400 hover:text-white px-2.5 py-1 rounded bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.06] transition flex items-center gap-1.5 text-[11px]" data-bib="${encodeURIComponent(pub.bibtex)}">
            <i class="fa-solid fa-copy text-[10px]"></i>
            <span>BibTeX</span>
          </button>
        </div>
      </div>
    `;
  }).join('');

  container.querySelectorAll('.copy-bib-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const bibText = decodeURIComponent(btn.getAttribute('data-bib'));
      navigator.clipboard.writeText(bibText).then(() => {
        const span = btn.querySelector('span');
        const oldText = span.textContent;
        span.textContent = '¡Copiado!';
        btn.classList.add('text-emerald-400');
        setTimeout(() => {
          span.textContent = oldText;
          btn.classList.remove('text-emerald-400');
        }, 1800);
      });
    });
  });
}

// 6. Renderizar Proyectos, Repositorios GitHub y Recursos Digitales
function renderProjects(mode) {
  const container = document.getElementById('projects-grid');
  if (!container) return;

  if (mode === 'projects') {
    const list = cvData.projects || [];
    container.innerHTML = list.map(p => `
      <div class="p-5 rounded-xl bg-surface-card border border-white/[0.08] hover:border-white/[0.14] transition flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between gap-2 mb-2 font-mono text-[10px]">
            <span class="px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">
              ${p.year}
            </span>
            ${p.badge ? `<span class="text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">${p.badge}</span>` : ''}
          </div>

          <h4 class="font-serif text-base font-bold text-white leading-snug">
            ${p.title}
          </h4>

          <div class="text-xs text-slate-400 mt-1 font-sans">
            <strong>Entidad:</strong> ${p.organization}
          </div>

          ${p.tags && p.tags.length > 0 ? `
            <div class="flex flex-wrap gap-1 mt-3 font-mono text-[10px]">
              ${p.tags.map(t => `<span class="px-2 py-0.5 rounded bg-white/[0.04] text-slate-300 border border-white/[0.04]">${t}</span>`).join('')}
            </div>
          ` : ''}
        </div>

        ${p.links && p.links.length > 0 ? `
          <div class="mt-4 pt-3 border-t border-white/[0.06] flex flex-wrap gap-2 font-mono text-xs">
            ${p.links.map(l => `
              <a href="${l.url}" target="_blank" class="text-sky-400 hover:text-sky-300 flex items-center gap-1 text-[11px]">
                <i class="fa-solid fa-arrow-up-right-from-square text-[9px]"></i> ${l.label}
              </a>
            `).join('')}
          </div>
        ` : ''}
      </div>
    `).join('');
  } else if (mode === 'repos') {
    const list = cvData.githubRepositories || [];
    container.innerHTML = list.map(repo => `
      <div class="p-5 rounded-xl bg-surface-card border border-white/[0.08] hover:border-white/[0.14] transition flex flex-col justify-between group">
        <div>
          <div class="flex items-center justify-between gap-2 mb-2 font-mono text-[10px]">
            <span class="px-2 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20">
              ${repo.badge || 'OPEN SOURCE'}
            </span>
            <span class="text-slate-400 flex items-center gap-1">
              <i class="fa-brands fa-github"></i> marchelo2212
            </span>
          </div>

          <h4 class="font-serif text-base font-bold text-white group-hover:text-amber-300 transition leading-snug">
            ${repo.title}
          </h4>

          <div class="font-mono text-xs text-slate-400 mt-1">
            repo: <span class="text-slate-200">${repo.name}</span>
          </div>

          <p class="text-xs text-slate-300 mt-2 leading-relaxed font-sans">
            ${repo.description}
          </p>

          ${repo.tags && repo.tags.length > 0 ? `
            <div class="flex flex-wrap gap-1 mt-3 font-mono text-[10px]">
              ${repo.tags.map(t => `<span class="px-2 py-0.5 rounded bg-white/[0.04] text-slate-300 border border-white/[0.04]">${t}</span>`).join('')}
            </div>
          ` : ''}
        </div>

        <div class="mt-4 pt-3 border-t border-white/[0.06] flex items-center justify-between font-mono text-xs">
          <a href="${repo.url}" target="_blank" class="text-sky-400 hover:text-sky-300 flex items-center gap-1.5 text-[11px]">
            <i class="fa-brands fa-github text-xs"></i> Repositorio
          </a>
          <span class="text-[10px] text-slate-400">${repo.category}</span>
        </div>
      </div>
    `).join('');
  } else if (mode === 'resources') {
    const list = cvData.digitalResources || [];
    container.innerHTML = list.map(r => `
      <div class="p-5 rounded-xl bg-surface-card border border-white/[0.08] hover:border-white/[0.14] transition flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between gap-2 mb-2 font-mono text-[10px]">
            <span class="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              ${r.category}
            </span>
            <span class="text-slate-400">${r.role}</span>
          </div>

          <h4 class="font-serif text-base font-bold text-white leading-snug">
            ${r.title}
          </h4>

          <div class="text-xs text-slate-400 mt-1 font-sans">
            ${r.institution}
          </div>

          <p class="text-xs text-slate-300 mt-2 leading-relaxed font-sans">
            ${r.description}
          </p>

          ${r.tags && r.tags.length > 0 ? `
            <div class="flex flex-wrap gap-1 mt-3 font-mono text-[10px]">
              ${r.tags.map(t => `<span class="px-2 py-0.5 rounded bg-white/[0.04] text-slate-300 border border-white/[0.04]">${t}</span>`).join('')}
            </div>
          ` : ''}
        </div>

        ${r.links && r.links.length > 0 ? `
          <div class="mt-4 pt-3 border-t border-white/[0.06] flex flex-wrap gap-3 font-mono text-xs">
            ${r.links.map(l => `
              <a href="${l.url}" target="_blank" class="text-emerald-400 hover:text-emerald-300 flex items-center gap-1 text-[11px]">
                <i class="fa-solid fa-link text-[9px]"></i> ${l.label}
              </a>
            `).join('')}
          </div>
        ` : ''}
      </div>
    `).join('');
  } else if (mode === 'blog') {
    const list = cvData.digitalGardenPosts || [];
    container.innerHTML = list.map(post => `
      <div class="p-5 rounded-xl bg-surface-card border border-white/[0.08] hover:border-emerald-500/30 transition flex flex-col justify-between group">
        <div>
          <div class="flex items-center justify-between gap-2 mb-2 font-mono text-[10px]">
            <span class="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold">
              ${post.badge || 'ENSAYO'}
            </span>
            <span class="text-slate-400 flex items-center gap-1 font-mono">
              <i class="fa-solid fa-seedling text-emerald-400 text-[10px]"></i> ${post.collection}
            </span>
          </div>

          <h4 class="font-serif text-base font-bold text-white group-hover:text-emerald-300 transition leading-snug">
            ${post.title}
          </h4>

          <p class="text-xs text-slate-300 mt-2 leading-relaxed font-sans">
            ${post.description}
          </p>

          ${post.tags && post.tags.length > 0 ? `
            <div class="flex flex-wrap gap-1 mt-3 font-mono text-[10px]">
              ${post.tags.map(t => `<span class="px-2 py-0.5 rounded bg-white/[0.04] text-slate-300 border border-white/[0.04]">${t}</span>`).join('')}
            </div>
          ` : ''}
        </div>

        <div class="mt-4 pt-3 border-t border-white/[0.06] flex items-center justify-between font-mono text-xs">
          <a href="${post.url}" target="_blank" class="text-emerald-400 hover:text-emerald-300 flex items-center gap-1.5 text-[11px] font-medium">
            <i class="fa-solid fa-arrow-up-right-from-square text-[9px]"></i> Leer en Quartz
          </a>
          <span class="text-[10px] text-slate-400">${post.year}</span>
        </div>
      </div>
    `).join('');
  }
}

// 7. Renderizar Educación Universitaria
function renderEducation() {
  const container = document.getElementById('education-list');
  if (!container || !cvData.education) return;

  container.innerHTML = cvData.education.map(e => `
    <div class="p-3.5 rounded-xl bg-surface-card border border-white/[0.08] flex items-start justify-between gap-3">
      <div>
        <span class="font-mono text-[10px] uppercase tracking-wider text-amber-400">${e.year}</span>
        <h4 class="text-xs font-bold text-white font-serif mt-0.5">${e.degree}</h4>
        <div class="text-xs text-slate-400 font-sans">${e.institution}</div>
      </div>
      <span class="font-mono text-[10px] px-2 py-0.5 rounded ${e.status === 'En curso' ? 'bg-sky-500/15 text-sky-400 border border-sky-500/20' : 'bg-white/[0.04] text-slate-400'}">
        ${e.status}
      </span>
    </div>
  `).join('');
}

/// 7b. Renderizar Distinciones, Certificaciones y Méritos
let currentCertFilter = 'all';
let currentCertSearchQuery = '';

function renderCertifications(filterType = currentCertFilter, searchQuery = currentCertSearchQuery) {
  currentCertFilter = filterType;
  currentCertSearchQuery = (searchQuery !== undefined ? searchQuery : currentCertSearchQuery).trim().toLowerCase();
  const container = document.getElementById('certificates-list');
  if (!container || !cvData.certifications) return;

  // Actualizar conteos dinámicos en los botones de filtro
  const allCerts = cvData.certifications;
  const certCounts = {
    all: allCerts.length,
    Meri: allCerts.filter(c => c.docType === 'Meri').length,
    Inves: allCerts.filter(c => c.docType === 'Inves').length,
    Cert: allCerts.filter(c => c.docType === 'Cert').length,
    CurEst: allCerts.filter(c => c.docType === 'CurEst').length,
    CursImp: allCerts.filter(c => c.docType === 'CursImp').length,
    CertTra: allCerts.filter(c => c.docType === 'CertTra').length,
    Contra: allCerts.filter(c => c.docType === 'Contra').length
  };
  const certLabels = {
    all: "Todos",
    Meri: "Méritos",
    Inves: "Investigación",
    Cert: "Certificaciones",
    CurEst: "Cursos Estudiados",
    CursImp: "Cursos Impartidos",
    CertTra: "Laboral",
    Contra: "Contratos"
  };
  document.querySelectorAll('.cert-filter-btn').forEach(btn => {
    const type = btn.getAttribute('data-type');
    if (type && certCounts[type] !== undefined) {
      btn.textContent = `${certLabels[type]} (${certCounts[type]})`;
    }
  });

  const filtered = allCerts.filter(c => {
    if (currentCertFilter !== 'all' && c.docType !== currentCertFilter) return false;
    if (currentCertSearchQuery) {
      const hay = [
        c.title || '',
        c.issuer || '',
        c.role || '',
        c.docType || '',
        c.year || '',
        ...(c.skills || [])
      ].join(' ').toLowerCase();
      if (!hay.includes(currentCertSearchQuery)) return false;
    }
    return true;
  });

  // Ordenar estrictamente por año y mes descendente (más reciente primero)
  filtered.sort((a, b) => {
    const keyA = `${(a.year || '0000')}-${String(a.month || '00').padStart(2, '0')}-${a.date || ''}`;
    const keyB = `${(b.year || '0000')}-${String(b.month || '00').padStart(2, '0')}-${b.date || ''}`;
    return keyB.localeCompare(keyA);
  });

  const typeMeta = {
    Meri: { label: "Mérito", color: "text-amber-400 bg-amber-500/10 border-amber-500/20", icon: "fa-solid fa-medal" },
    Inves: { label: "Investigación", color: "text-purple-400 bg-purple-500/10 border-purple-500/20", icon: "fa-solid fa-microscope" },
    Cert: { label: "Certificación", color: "text-sky-400 bg-sky-500/10 border-sky-500/20", icon: "fa-solid fa-certificate" },
    CurEst: { label: "Curso Estudiado", color: "text-blue-400 bg-blue-500/10 border-blue-500/20", icon: "fa-solid fa-graduation-cap" },
    CursImp: { label: "Curso Impartido", color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20", icon: "fa-solid fa-chalkboard-user" },
    CertTra: { label: "Laboral", color: "text-orange-400 bg-orange-500/10 border-orange-500/20", icon: "fa-solid fa-briefcase" },
    Contra: { label: "Contrato", color: "text-teal-400 bg-teal-500/10 border-teal-500/20", icon: "fa-solid fa-file-contract" }
  };

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="p-6 rounded-xl bg-surface-card border border-white/[0.06] text-center text-slate-400 font-mono text-xs">
        No se encontraron registros que coincidan con la búsqueda o filtro.
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(c => {
    const meta = typeMeta[c.docType] || { label: c.docType || "Credencial", color: "text-slate-400 bg-white/[0.04] border-white/[0.08]", icon: "fa-solid fa-certificate" };
    
    let icon = meta.icon;
    let iconColor = meta.color;
    const tLower = (c.title || '').toLowerCase();
    const iLower = (c.issuer || '').toLowerCase();

    if (iLower.includes('google')) {
      icon = 'fa-brands fa-google';
      iconColor = 'text-sky-400 bg-sky-500/15 border-sky-500/30';
    } else if (iLower.includes('moodle')) {
      icon = 'fa-solid fa-graduation-cap';
      iconColor = 'text-emerald-400 bg-emerald-500/15 border-emerald-500/30';
    } else if (c.cluster === 'ia_data_science' || tLower.includes('ia') || tLower.includes('inteligencia')) {
      icon = 'fa-solid fa-brain';
      iconColor = 'text-sky-400 bg-sky-500/15 border-sky-500/30';
    }

    const driveBtn = c.driveUrl ? `
      <a href="${c.driveUrl}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-lg bg-emerald-500/15 text-emerald-300 hover:bg-emerald-500/25 border border-emerald-500/30 text-[10px] font-mono transition" title="Ver documento oficial en Google Drive">
        <i class="fa-brands fa-google-drive text-[10px]"></i>
        <span>Ver en Drive</span>
        <i class="fa-solid fa-arrow-up-right-from-square text-[8px] opacity-70"></i>
      </a>
    ` : (c.verificationUrl ? `
      <a href="${c.verificationUrl}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-white/[0.05] text-slate-300 hover:text-white border border-white/[0.1] text-[10px] font-mono transition">
        <span>Verificar</span>
        <i class="fa-solid fa-arrow-up-right-from-square text-[8px] opacity-70"></i>
      </a>
    ` : '');

    const roleBadge = c.role ? `
      <span class="font-mono text-[9px] px-1.5 py-0.5 rounded bg-white/[0.03] text-slate-300 border border-white/[0.05]">${c.role}</span>
    ` : '';

    const hoursBadge = c.hours ? `
      <span class="font-mono text-[9px] px-1.5 py-0.5 rounded bg-white/[0.04] text-slate-400 border border-white/[0.06]">${c.hours}h</span>
    ` : '';

    const skillsHtml = (c.skills && c.skills.length > 0) ? `
      <div class="flex flex-wrap gap-1 mt-2">
        ${c.skills.map(s => `<span class="px-1.5 py-0.5 rounded bg-white/[0.03] text-[9px] text-slate-400 border border-white/[0.05] font-mono">${s}</span>`).join('')}
      </div>
    ` : '';

    return `
      <div class="p-3.5 rounded-xl bg-surface-card border border-white/[0.08] hover:border-white/[0.15] transition flex items-start gap-3">
        <div class="w-8 h-8 rounded-lg ${iconColor} flex items-center justify-center flex-shrink-0 text-sm border">
          <i class="${icon}"></i>
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center justify-between gap-2 flex-wrap mb-0.5">
            <div class="flex items-center gap-1.5">
              <span class="font-mono text-[9px] px-1.5 py-0.5 rounded font-semibold border ${meta.color}">${meta.label}</span>
              <span class="font-mono text-[10px] text-slate-400">${c.year || ''}</span>
            </div>
            <div class="flex items-center gap-1.5">
              ${hoursBadge}
              ${driveBtn}
            </div>
          </div>
          <h4 class="font-semibold text-white text-xs leading-snug mt-1">${c.title}</h4>
          <div class="text-xs text-slate-400 mt-1 flex items-center gap-2 flex-wrap">
            <span>${c.issuer}</span>
            ${roleBadge}
          </div>
          ${skillsHtml}
        </div>
      </div>
    `;
  }).join('');
}

// 8. Event Listeners
function setupEventListeners() {
  // Tabs de Timeline
  const leadBtn = document.getElementById('tab-leadership-btn');
  const teachBtn = document.getElementById('tab-teaching-btn');

  if (leadBtn && teachBtn) {
    leadBtn.addEventListener('click', () => {
      leadBtn.className = 'px-4 py-2 rounded-lg bg-emerald-600/90 text-white font-medium transition';
      teachBtn.className = 'px-4 py-2 rounded-lg text-slate-400 hover:text-white transition';
      renderTimeline('leadership');
    });

    teachBtn.addEventListener('click', () => {
      teachBtn.className = 'px-4 py-2 rounded-lg bg-sky-600/90 text-white font-medium transition';
      leadBtn.className = 'px-4 py-2 rounded-lg text-slate-400 hover:text-white transition';
      renderTimeline('teaching');
    });
  }

  // Tabs de Proyectos vs Repositorios vs Recursos Digitales vs Ensayos Quartz
  const showProjBtn = document.getElementById('show-projects-btn');
  const showReposBtn = document.getElementById('show-repos-btn');
  const showResBtn = document.getElementById('show-resources-btn');
  const showBlogBtn = document.getElementById('show-blog-btn');

  const activeTabClass = 'px-3.5 py-1.5 rounded-xl bg-purple-600 text-white font-medium transition shadow-md';
  const inactiveTabClass = 'px-3.5 py-1.5 rounded-xl bg-surface-card hover:bg-surface-raised text-slate-400 hover:text-white border border-white/[0.08] transition';

  const resetProjectTabs = () => {
    if (showProjBtn) showProjBtn.className = inactiveTabClass;
    if (showReposBtn) showReposBtn.className = inactiveTabClass;
    if (showResBtn) showResBtn.className = inactiveTabClass;
    if (showBlogBtn) showBlogBtn.className = inactiveTabClass;
  };

  if (showProjBtn && showReposBtn && showResBtn) {
    showProjBtn.addEventListener('click', () => {
      resetProjectTabs();
      showProjBtn.className = activeTabClass;
      renderProjects('projects');
    });

    showReposBtn.addEventListener('click', () => {
      resetProjectTabs();
      showReposBtn.className = 'px-3.5 py-1.5 rounded-xl bg-sky-600 text-white font-medium transition shadow-md';
      renderProjects('repos');
    });

    showResBtn.addEventListener('click', () => {
      resetProjectTabs();
      showResBtn.className = 'px-3.5 py-1.5 rounded-xl bg-emerald-600 text-white font-medium transition shadow-md';
      renderProjects('resources');
    });

    if (showBlogBtn) {
      showBlogBtn.addEventListener('click', () => {
        resetProjectTabs();
        showBlogBtn.className = 'px-3.5 py-1.5 rounded-xl bg-emerald-700 text-white font-medium transition shadow-md';
        renderProjects('blog');
      });
    }
  }

  // Filtros de Publicaciones
  const pubSearch = document.getElementById('pub-search-input');
  const pubCluster = document.getElementById('pub-cluster-filter');

  const onPubFilterChange = () => {
    const query = pubSearch ? pubSearch.value : '';
    const cluster = pubCluster ? pubCluster.value : 'all';
    renderPublications(cluster, query);
  };

  if (pubSearch) pubSearch.addEventListener('input', onPubFilterChange);
  if (pubCluster) pubCluster.addEventListener('change', onPubFilterChange);

  // Switcher de Vista Dual
  const interactiveBtn = document.getElementById('view-interactive-btn');
  const classicBtn = document.getElementById('view-classic-btn');

  if (interactiveBtn && classicBtn) {
    interactiveBtn.addEventListener('click', () => {
      interactiveBtn.className = 'flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/[0.1] text-white font-medium transition';
      classicBtn.className = 'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-slate-400 hover:text-white transition';
      const el = document.getElementById('research-lab');
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    });

    classicBtn.addEventListener('click', () => {
      classicBtn.className = 'flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/[0.1] text-white font-medium transition';
      interactiveBtn.className = 'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-slate-400 hover:text-white transition';
      const el = document.getElementById('timeline-sec');
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    });
  }

  // Filtros de Certificaciones & Méritos por Tipo
  const certFilterBtns = document.querySelectorAll('.cert-filter-btn');
  certFilterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const type = btn.getAttribute('data-type');
      certFilterBtns.forEach(b => {
        b.className = 'cert-filter-btn px-2.5 py-1 rounded-lg bg-white/[0.04] text-slate-400 hover:text-white border border-white/[0.06] transition';
      });
      btn.className = 'cert-filter-btn px-2.5 py-1 rounded-lg bg-amber-500/20 text-amber-300 border border-amber-500/30 transition font-medium';
      renderCertifications(type);
    });
  });

  // Buscador reactivo de Certificaciones
  const certSearchInput = document.getElementById('cert-search-input');
  if (certSearchInput) {
    certSearchInput.addEventListener('input', (e) => {
      renderCertifications(currentCertFilter, e.target.value);
    });
  }
}

// 9. Inicializar Barra Lateral y Navegación ScrollSpy
function initSidebar() {
  const navLinks = document.querySelectorAll('.sidebar-nav-link');
  const sectionIds = [
    'hero',
    'research-lab',
    'ai-assistant-sec',
    'timeline-sec',
    'publications-sec',
    'projects-sec',
    'education-sec'
  ];
  
  const sections = sectionIds.map(id => document.getElementById(id)).filter(Boolean);

  const desktopReadingLabel = document.getElementById('reading-percentage-label');
  const mobileReadingLabel = document.getElementById('mobile-reading-percentage-label');
  const progressBar = document.getElementById('reading-progress-bar');
  const mobileProgressBar = document.getElementById('mobile-reading-progress-bar');

  // Actualización de progreso de lectura global robusta (cross-browser)
  const updateScrollProgress = () => {
    const scrollTop = window.scrollY || window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;
    const scrollHeight = Math.max(
      document.body.scrollHeight || 0,
      document.documentElement.scrollHeight || 0,
      document.body.offsetHeight || 0,
      document.documentElement.offsetHeight || 0
    );
    const clientHeight = window.innerHeight || document.documentElement.clientHeight || 0;
    const totalHeight = scrollHeight - clientHeight;
    const progress = totalHeight > 0 ? (scrollTop / totalHeight) * 100 : 0;
    const clamped = Math.min(100, Math.max(0, Math.round(progress)));
    const widthStr = `${clamped}%`;

    if (progressBar) progressBar.style.width = widthStr;
    if (mobileProgressBar) mobileProgressBar.style.width = widthStr;
    if (desktopReadingLabel) desktopReadingLabel.textContent = `${clamped}%`;
    if (mobileReadingLabel) mobileReadingLabel.textContent = `${clamped}%`;
  };

  window.addEventListener('scroll', updateScrollProgress, { passive: true });
  window.addEventListener('resize', updateScrollProgress, { passive: true });
  window.addEventListener('load', updateScrollProgress, { passive: true });
  updateScrollProgress();

  // Función para activar visualmente el link correspondiente
  const setActiveNav = (targetId) => {
    navLinks.forEach(link => {
      const target = link.getAttribute('data-target') || link.getAttribute('href')?.replace('#', '');
      if (target === targetId) {
        link.classList.add('active');
      } else {
        link.classList.remove('active');
      }
    });
  };

  // IntersectionObserver para detectar sección visible con precisión
  const observerOptions = {
    root: null,
    rootMargin: '-20% 0px -55% 0px',
    threshold: 0
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        setActiveNav(entry.target.id);
      }
    });
  }, observerOptions);

  sections.forEach(sec => observer.observe(sec));
  setActiveNav('hero');

  // Drawer Móvil
  const mobileToggleBtn = document.getElementById('mobile-sidebar-toggle');
  const floatingIndexBtn = document.getElementById('floating-index-btn');
  const closeMobileDrawerBtn = document.getElementById('close-mobile-sidebar');
  const mobileBackdrop = document.getElementById('mobile-sidebar-backdrop');
  const mobileDrawer = document.getElementById('mobile-sidebar-drawer');

  const openMobileDrawer = () => {
    if (mobileBackdrop && mobileDrawer) {
      mobileBackdrop.classList.remove('opacity-0', 'pointer-events-none');
      mobileBackdrop.classList.add('opacity-100', 'pointer-events-auto');
      mobileDrawer.classList.remove('-translate-x-full');
      mobileDrawer.classList.add('translate-x-0');
      document.body.style.overflow = 'hidden';
    }
  };

  const closeMobileDrawer = () => {
    if (mobileBackdrop && mobileDrawer) {
      mobileBackdrop.classList.remove('opacity-100', 'pointer-events-auto');
      mobileBackdrop.classList.add('opacity-0', 'pointer-events-none');
      mobileDrawer.classList.remove('translate-x-0');
      mobileDrawer.classList.add('-translate-x-full');
      document.body.style.overflow = '';
    }
  };

  if (mobileToggleBtn) mobileToggleBtn.addEventListener('click', openMobileDrawer);
  if (floatingIndexBtn) floatingIndexBtn.addEventListener('click', openMobileDrawer);
  if (closeMobileDrawerBtn) closeMobileDrawerBtn.addEventListener('click', closeMobileDrawer);
  if (mobileBackdrop) mobileBackdrop.addEventListener('click', closeMobileDrawer);

  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeMobileDrawer();
  });

  // Manejador de clics en enlaces con smooth scroll
  navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      const targetId = link.getAttribute('data-target') || link.getAttribute('href')?.replace('#', '');
      const targetEl = document.getElementById(targetId);
      if (targetEl) {
        e.preventDefault();
        targetEl.scrollIntoView({ behavior: 'smooth' });
        setActiveNav(targetId);
        closeMobileDrawer();
        if (history.pushState) {
          history.pushState(null, '', `#${targetId}`);
        }
      }
    });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initSidebar();
  loadData();
});
