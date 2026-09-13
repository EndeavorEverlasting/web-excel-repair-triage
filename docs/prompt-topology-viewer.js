(() => {
  'use strict';
  const data = window.PROMPT_TOPOLOGY_DATA;
  if (!data || !Array.isArray(data.nodes) || !data.projection || !data.projection.points) throw new Error('Prompt topology viewer data missing');

  const canvas = document.getElementById('universe');
  const ctx = canvas.getContext('2d', {alpha:true});
  const search = document.getElementById('search');
  const detail = document.getElementById('detail');
  const clustersEl = document.getElementById('clusters');
  const hoverEl = document.getElementById('hoverLabel');
  const reset = document.getElementById('resetView');
  const nodeCountEl = document.getElementById('nodeCount');
  const edgeCountEl = document.getElementById('edgeCount');
  const epochEl = document.getElementById('epochId');
  const bindingEl = document.getElementById('bindingHash');

  const nodes = data.nodes;
  const nodesById = new Map(nodes.map(n => [n.prompt_id, n]));
  const edgesByNode = new Map(nodes.map(n => [n.prompt_id, []]));
  for (const edge of data.edges) {
    if (edgesByNode.has(edge.source)) edgesByNode.get(edge.source).push(edge);
    if (edgesByNode.has(edge.target)) edgesByNode.get(edge.target).push(edge);
  }
  const clusterByPrompt = new Map();
  for (const cluster of data.clusters) for (const id of cluster.member_prompt_ids) clusterByPrompt.set(id, cluster.cluster_id);
  const outlierIds = new Set(data.outlier_prompt_ids || []);
  const opportunityByPrompt = new Map(nodes.map(n => [n.prompt_id, []]));
  for (const opp of data.opportunities) for (const id of opp.prompt_ids || []) if (opportunityByPrompt.has(id)) opportunityByPrompt.get(id).push(opp);

  const state = { yaw: -0.28, pitch: 0.17, zoom: 1.0, panX: 0, panY: 0, selectedId: null, hoverId: null, activeCluster: null, query: '', dragging: false, dragStart: null };
  let width = 1, height = 1, dpr = 1, screenPoints = [];

  const hashHue = value => {
    let h = 2166136261;
    for (let i=0;i<value.length;i++) h = Math.imul(h ^ value.charCodeAt(i), 16777619);
    return ((h >>> 0) % 300) + 20;
  };
  const colorFor = node => `hsl(${hashHue(node.family_declared_id || clusterByPrompt.get(node.prompt_id) || node.prompt_id)} 72% 67%)`;
  const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const inActiveGroup = id => !state.activeCluster || (state.activeCluster==='OUTLIER' ? outlierIds.has(id) : clusterByPrompt.get(id)===state.activeCluster);

  function resize() {
    const rect = canvas.getBoundingClientRect();
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    width = Math.max(1, rect.width); height = Math.max(1, rect.height);
    canvas.width = Math.round(width*dpr); canvas.height = Math.round(height*dpr);
    ctx.setTransform(dpr,0,0,dpr,0,0);
  }
  function rotatePoint(p) {
    const cy=Math.cos(state.yaw), sy=Math.sin(state.yaw), cp=Math.cos(state.pitch), sp=Math.sin(state.pitch);
    const x1=p.x*cy-p.z*sy, z1=p.x*sy+p.z*cy;
    return {x:x1, y:p.y*cp-z1*sp, z:p.y*sp+z1*cp};
  }
  function project(id) {
    const p = rotatePoint(data.projection.points[id]);
    const perspective = 1.85 / Math.max(.65, 2.4 - p.z*.55);
    const scale = Math.min(width,height)*0.39*state.zoom*perspective;
    return {id, x:width*.5+state.panX+p.x*scale, y:height*.5+state.panY-p.y*scale, z:p.z, perspective};
  }
  function matches(node) {
    if (!state.query) return true;
    const hay = [node.prompt_id,node.title,node.family_declared,node.prompt_type,node.prompt_class,...(node.keywords||[])].join(' ').toLowerCase();
    return hay.includes(state.query);
  }
  function relationSet(id) {
    if (!id) return new Set();
    const set = new Set([id]);
    for (const e of edgesByNode.get(id) || []) set.add(e.source===id?e.target:e.source);
    return set;
  }
  function draw() {
    ctx.clearRect(0,0,width,height);
    const selectedRelations = relationSet(state.selectedId || state.hoverId);
    screenPoints = nodes.map(n => project(n.prompt_id)).sort((a,b)=>a.z-b.z);
    const byId = new Map(screenPoints.map(p=>[p.id,p]));

    ctx.lineWidth=.7;
    for (const edge of data.edges) {
      const a=byId.get(edge.source), b=byId.get(edge.target); if(!a||!b) continue;
      const related = state.selectedId && (edge.source===state.selectedId || edge.target===state.selectedId);
      if (state.activeCluster && !inActiveGroup(edge.source) && !inActiveGroup(edge.target)) continue;
      ctx.globalAlpha = related ? .42 : .045;
      ctx.strokeStyle = related ? '#8fd1ff' : '#8aa0b7';
      ctx.beginPath(); ctx.moveTo(a.x,a.y); ctx.lineTo(b.x,b.y); ctx.stroke();
    }
    for (const p of screenPoints) {
      const n=nodesById.get(p.id); const queryHit=matches(n);
      const clusterHit=inActiveGroup(p.id);
      const relationHit=!selectedRelations.size || selectedRelations.has(p.id);
      let alpha=.88;
      if(!queryHit) alpha*=.13; if(!clusterHit) alpha*=.16; if(!relationHit) alpha*=.19;
      if(p.id===state.selectedId) alpha=1; else if(p.id===state.hoverId) alpha=1;
      const radius = Math.max(2.2, 4.2*p.perspective) * (p.id===state.selectedId?1.9:p.id===state.hoverId?1.55:1);
      ctx.globalAlpha=alpha; ctx.fillStyle=colorFor(n); ctx.shadowColor=colorFor(n); ctx.shadowBlur=p.id===state.selectedId?18:7;
      ctx.beginPath(); ctx.arc(p.x,p.y,radius,0,Math.PI*2); ctx.fill(); ctx.shadowBlur=0;
    }
    ctx.globalAlpha=1;
    requestAnimationFrame(draw);
  }
  function nearest(clientX,clientY,max=18) {
    const rect=canvas.getBoundingClientRect(), x=clientX-rect.left,y=clientY-rect.top;
    let best=null,bestD=max*max;
    for(const p of screenPoints){const dx=p.x-x,dy=p.y-y,d=dx*dx+dy*dy;if(d<bestD){best=p;bestD=d;}}
    return best;
  }
  function setHover(id,evt) {
    state.hoverId=id;
    if(!id){hoverEl.classList.remove('visible');return;}
    const n=nodesById.get(id); hoverEl.innerHTML=`<strong>${escapeHtml(id)}</strong> · ${escapeHtml(n.title)}`;
    const stage=canvas.parentElement.getBoundingClientRect(); hoverEl.style.left=`${Math.min(stage.width-290,Math.max(8,evt.clientX-stage.left+12))}px`;hoverEl.style.top=`${Math.min(stage.height-54,Math.max(8,evt.clientY-stage.top+12))}px`;hoverEl.classList.add('visible');
  }
  function renderDetail(id) {
    if(!id){detail.innerHTML='<div class="empty">Hover or select a prompt to inspect its topology evidence.</div>';return;}
    const n=nodesById.get(id), cluster=clusterByPrompt.get(id)||'OUTLIER';
    const edges=(edgesByNode.get(id)||[]).slice().sort((a,b)=>b.strength_micros-a.strength_micros).slice(0,8);
    const opps=opportunityByPrompt.get(id)||[];
    detail.innerHTML=`<div class="card"><div class="prompt-id">${escapeHtml(id)}</div><div class="prompt-title">${escapeHtml(n.title)}</div><div class="meta"><span class="tag">${escapeHtml(n.family_declared)}</span><span class="tag">${escapeHtml(n.prompt_type)}</span><span class="tag">${escapeHtml(cluster)}</span></div><div class="edge-list">${edges.length?edges.map(e=>{const other=e.source===id?e.target:e.source;const channels=(e.channels||[]).map(c=>c.type).join(' · ');return `<div class="edge"><strong>${escapeHtml(other)}</strong> ${Math.round(e.strength_micros/1000)/10}%<div class="channels">${escapeHtml(channels)}</div></div>`}).join(''):'<div class="empty">No relationship edges.</div>'}</div><div class="opp-list">${opps.map(o=>`<div class="opp ${escapeHtml(o.state)}"><strong>${escapeHtml(o.state)}</strong> · ${escapeHtml(o.recommended_action)} · score ${escapeHtml(o.score)}</div>`).join('')}</div></div>`;
  }
  function selectPrompt(id,{centerSearch=false}={}) {
    if(id && !nodesById.has(id)) return false;
    state.selectedId=id; if(id) state.activeCluster=null;
    if(centerSearch && id) search.value=id;
    renderDetail(id); renderClusters(); return true;
  }
  function focusCluster(id) {
    if(id && id!=='OUTLIER' && !data.clusters.some(c=>c.cluster_id===id)) return false;
    state.activeCluster = state.activeCluster===id?null:id; state.selectedId=null; renderDetail(null); renderClusters(); return true;
  }
  function renderClusters() {
    clustersEl.innerHTML = data.clusters.map(c=>`<button class="cluster-btn${state.activeCluster===c.cluster_id?' active':''}" type="button" data-cluster="${escapeHtml(c.cluster_id)}">${escapeHtml(c.cluster_id)} · ${c.member_count}</button>`).join('') + `<button class="cluster-btn${state.activeCluster==='OUTLIER'?' active':''}" type="button" data-cluster="OUTLIER">OUTLIERS · ${data.outlier_prompt_ids.length}</button>`;
    clustersEl.querySelectorAll('[data-cluster]').forEach(btn=>btn.addEventListener('click',()=>focusCluster(btn.dataset.cluster)));
  }
  function resetView(){state.yaw=-.28;state.pitch=.17;state.zoom=1;state.panX=0;state.panY=0;state.selectedId=null;state.hoverId=null;state.activeCluster=null;state.query='';search.value='';renderDetail(null);renderClusters();}

  canvas.addEventListener('pointerdown',e=>{state.dragging=true;state.dragStart={x:e.clientX,y:e.clientY,yaw:state.yaw,pitch:state.pitch,panX:state.panX,panY:state.panY,mode:e.shiftKey?'pan':'orbit'};canvas.classList.add('dragging');canvas.setPointerCapture(e.pointerId);});
  canvas.addEventListener('pointermove',e=>{
    if(state.dragging&&state.dragStart){if(state.dragStart.mode==='pan'){state.panX=state.dragStart.panX+(e.clientX-state.dragStart.x);state.panY=state.dragStart.panY+(e.clientY-state.dragStart.y);}else{state.yaw=state.dragStart.yaw+(e.clientX-state.dragStart.x)*.006;state.pitch=Math.max(-1.25,Math.min(1.25,state.dragStart.pitch+(e.clientY-state.dragStart.y)*.006));}setHover(null,e);return;}
    const p=nearest(e.clientX,e.clientY);setHover(p&&p.id,e);if(!state.selectedId)renderDetail(p&&p.id);
  });
  canvas.addEventListener('pointerup',e=>{const moved=state.dragStart?Math.hypot(e.clientX-state.dragStart.x,e.clientY-state.dragStart.y):999;state.dragging=false;canvas.classList.remove('dragging');if(moved<5){const p=nearest(e.clientX,e.clientY);selectPrompt(p&&p.id);}state.dragStart=null;});
  canvas.addEventListener('pointerleave',e=>{if(!state.dragging){setHover(null,e);if(!state.selectedId)renderDetail(null);}});
  canvas.addEventListener('wheel',e=>{e.preventDefault();state.zoom=Math.max(.45,Math.min(2.8,state.zoom*Math.exp(-e.deltaY*.001)));},{passive:false});

  canvas.addEventListener('keydown',e=>{
    const step=e.shiftKey?18:.08; let handled=true;
    if(e.shiftKey&&e.key==='ArrowLeft')state.panX-=step;else if(e.shiftKey&&e.key==='ArrowRight')state.panX+=step;else if(e.shiftKey&&e.key==='ArrowUp')state.panY-=step;else if(e.shiftKey&&e.key==='ArrowDown')state.panY+=step;
    else if(e.key==='ArrowLeft')state.yaw-=step;else if(e.key==='ArrowRight')state.yaw+=step;else if(e.key==='ArrowUp')state.pitch=Math.max(-1.25,state.pitch-step);else if(e.key==='ArrowDown')state.pitch=Math.min(1.25,state.pitch+step);
    else if(e.key==='+'||e.key==='=')state.zoom=Math.min(2.8,state.zoom*1.12);else if(e.key==='-'||e.key==='_')state.zoom=Math.max(.45,state.zoom/1.12);else handled=false;
    if(handled)e.preventDefault();
  });
  search.addEventListener('input',()=>{
    state.query=search.value.trim().toLowerCase(); state.activeCluster=null;
    if(!state.query){state.selectedId=null;renderDetail(null);return;}
    const exact=nodes.find(n=>n.prompt_id.toLowerCase()===state.query);
    const first=exact||nodes.find(matches);
    state.selectedId=first?first.prompt_id:null; renderDetail(state.selectedId); renderClusters();
  });
  search.addEventListener('keydown',e=>{if(e.key==='Escape'){search.value='';state.query='';state.selectedId=null;renderDetail(null);search.blur();}});
  reset.addEventListener('click',resetView);
  window.addEventListener('resize',resize);

  nodeCountEl.textContent=String(nodes.length);edgeCountEl.textContent=String(data.edges.length);epochEl.textContent=data.projection_state.epoch_id;bindingEl.textContent=data.topology_hash;
  renderClusters();renderDetail(null);resize();requestAnimationFrame(draw);

  window.PromptTopologyViewer = Object.freeze({
    snapshot: () => ({yaw:state.yaw,pitch:state.pitch,zoom:state.zoom,panX:state.panX,panY:state.panY,selectedId:state.selectedId,hoverId:state.hoverId,activeCluster:state.activeCluster,query:state.query,nodeCount:nodes.length,edgeCount:data.edges.length,projectionPointCount:Object.keys(data.projection.points).length,outlierCount:outlierIds.size,groupMemberCount:state.activeCluster?nodes.filter(n=>inActiveGroup(n.prompt_id)).length:nodes.length,topologyHash:data.topology_hash,projectionHash:data.projection_hash,epochId:data.projection_state.epoch_id}),
    selectPrompt: id => selectPrompt(id),
    focusCluster: id => focusCluster(id),
    resetView
  });
})();
