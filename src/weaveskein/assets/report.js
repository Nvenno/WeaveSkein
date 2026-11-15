(() => {
  "use strict";
  const $ = id => document.getElementById(id);
  const data = JSON.parse($("report-data").textContent);
  const modules = new Map(data.modules.map(module => [module.name, module]));
  const names = [...modules.keys()].sort();
  const incoming = new Map(), outgoing = new Map(), categories = new Map();
  const testDirs = new Set(["tests", "test", "__tests__"]);
  const exampleDirs = new Set(["example", "examples", "samples"]);
  const byLeaf = new Map();
  for (const name of names) {
    const dirs = modules.get(name).path.split(/[\\/]/).slice(0, -1);
    categories.set(name, {test: dirs.some(d => testDirs.has(d)), example: dirs.some(d => exampleDirs.has(d))});
    incoming.set(name, []); outgoing.set(name, []);
    const leaf = name.split(".").at(-1);
    byLeaf.set(leaf, (byLeaf.get(leaf) || 0) + 1);
  }
  const elements = names.map(name => {
    const parts = name.split(".");
    const short = byLeaf.get(parts.at(-1)) === 1 ? parts.at(-1) : parts.slice(-2).join(".");
    const label = short.length > 26 ? short.slice(0, 10) + "…" + short.slice(-13) : short;
    return {data: {id: name, label}, classes: modules.get(name).cycle === null ? "" : "cyclic"};
  });
  data.edges.forEach(([source, target], i) => {
    outgoing.get(source).push(target); incoming.get(target).push(source);
    const group = modules.get(source).cycle;
    elements.push({data: {id: ":" + i, source, target},
      classes: group !== null && group === modules.get(target).cycle ? "cyclic" : ""});
  });

  function append(parent, tag, text, cls) {
    const el = document.createElement(tag);
    el.textContent = text;
    if (cls) el.className = cls;
    parent.append(el);
    return el;
  }
  const icons = {
    graph: "M5 6l7 5m1 2 5 5M5 7l1 10m2 1 9 1 M5 3a2 2 0 1 0 0 4 2 2 0 0 0 0-4 M13 9a2 2 0 1 0 0 4 2 2 0 0 0 0-4 M19 17a2 2 0 1 0 0 4 2 2 0 0 0 0-4",
    search: "M15 15l5 5 M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0",
    filter: "M3 7h10m4 0h4M3 17h4m4 0h10M13 4v6M8 14v6",
    cycle: "M4 11a8 8 0 0 1 14-5l2 2m0-5v5h-5 M20 13a8 8 0 0 1-14 5l-2-2m0 5v-5h5",
    fit: "M8 3H3v5m13-5h5v5M3 16v5h5m13-5v5h-5",
    inspect: "M3 4h18v16H3z M13 4v16"
  };
  for (const slot of document.querySelectorAll("[data-icon]")) {
    const ns = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(ns, "svg"), path = document.createElementNS(ns, "path");
    for (const [key, value] of Object.entries({viewBox:"0 0 24 24",fill:"none",stroke:"currentColor",
      "stroke-width":"1.6","stroke-linejoin":"round","stroke-linecap":"round","aria-hidden":"true"})) svg.setAttribute(key,value);
    path.setAttribute("d", icons[slot.dataset.icon]); svg.append(path); slot.append(svg);
  }
  const degree = name => incoming.get(name).length + outgoing.get(name).length;
  const ranked = names.slice().sort((a,b) => degree(b) - degree(a));
  $("project").textContent = data.project;
  $("total-modules").textContent = names.length;
  $("total-edges").textContent = data.edges.length;
  $("total-isolated").textContent = names.filter(n => !degree(n)).length;
  $("total-cycles").textContent = data.cycles;
  $("cycles").disabled = !data.cycles;

  const theme = getComputedStyle(document.documentElement);
  const color = name => theme.getPropertyValue(name).trim();
  const outgoingColor = color("--accent"), incomingColor = color("--importer"), cycleColor = color("--cycle");
  const edgeColor = color => ({"line-color":color, "target-arrow-color":color, width:2.6});
  const cy = cytoscape({
    container:$("graph"), elements, layout:{name:"preset"}, minZoom:0.025, maxZoom:4,
    boxSelectionEnabled:false, autounselectify:true,
    style:[
      {selector:"node",style:{
        width:22,height:22,"background-color":"#bf784d","border-width":2,"border-color":"#dc9c70",
        label:"data(label)",color:color("--ink"),"font-family":"Consolas, monospace","font-size":16,
        "min-zoomed-font-size":8,"text-valign":"bottom","text-margin-y":6,
        "text-background-color":color("--canvas"),"text-background-opacity":0.94,"text-background-padding":2
      }},
      {selector:"edge",style:{width:1.7,"line-color":"#78716c","target-arrow-color":"#aba198",
        "target-arrow-shape":"triangle","arrow-scale":1.05,"curve-style":"bezier"}},
      {selector:"node.cyclic",style:{"border-width":3,"border-color":cycleColor}},
      {selector:"edge.cycle-lit",style:edgeColor(cycleColor)},
      {selector:"node.cycle-lit",style:{"background-color":cycleColor}},
      {selector:"node.outgoing",style:{"background-color":outgoingColor}},
      {selector:"node.incoming",style:{"background-color":incomingColor}},
      {selector:"node.incoming.outgoing",style:{"pie-size":"100%","pie-1-background-color":outgoingColor,"pie-1-background-size":50}},
      {selector:"edge.outgoing",style:edgeColor(outgoingColor)},
      {selector:"edge.incoming",style:{...edgeColor(incomingColor),"line-style":"dashed"}},
      {selector:"node.picked",style:{"background-color":"#fff1dd","border-width":4,"border-color":outgoingColor,
        width:29,height:29,"font-weight":"bold","min-zoomed-font-size":0}},
      {selector:".muted",style:{opacity:0.31}},
      {selector:"edge.muted",style:{opacity:0.16}},
      {selector:"node.found, node.hovered",style:{"underlay-color":outgoingColor,"underlay-opacity":0.28,
        "underlay-padding":6,"min-zoomed-font-size":0,opacity:1}},
      {selector:".hidden",style:{display:"none"}}
    ]
  });
  const nodes = cy.nodes(), edges = cy.edges();
  const query = $("query"), mode = $("focus-mode"), tests = $("hide-tests"), examples = $("hide-examples");
  let selected = null, visible = new Set(names), cycleLit = false;
  let fitted = true;
  function layout() {
    if (!nodes.length) return;
    const cols = Math.max(1, Math.ceil(Math.sqrt(nodes.length * cy.width() / Math.max(1,cy.height()))));
    // Stable starting coordinates avoid a random force-layout seed. Dense graphs use only the grid.
    nodes.layout({name:"grid",cols,fit:false,avoidOverlap:true,nodeDimensionsIncludeLabels:true,
      boundingBox:{x1:0,y1:0,w:cols*130,h:Math.ceil(nodes.length/cols)*90}}).run();
    if (nodes.length > 2 && nodes.length <= 120 && edges.length <= 600) {
      cy.layout({name:"cose",animate:false,fit:false,randomize:false,numIter:420,
        idealEdgeLength:100,nodeRepulsion:9000,nodeDimensionsIncludeLabels:true,componentSpacing:75}).run();
    }
  }
  function fit() {
    const shown = cy.elements().not(".hidden");
    if (shown.length) {
      cy.fit(shown, Math.min(55, Math.max(32, cy.width()*0.045)));
      if (cy.zoom() > 1.6) { cy.zoom(1.6); cy.center(shown); }
    }
    fitted = true;
  }
  function zoomLevel() { $("zoom-level").textContent = Math.round(cy.zoom()*100) + "%"; }
  cy.on("zoom pan drag", () => { fitted = false; zoomLevel(); hideTip(); });
  layout(); fit(); zoomLevel();
  new ResizeObserver(() => {
    const preserveFit = fitted;
    cy.resize();
    if (preserveFit) fit();
  }).observe($("graph"));

  function allowed(name) {
    const cat = categories.get(name);
    return !(tests.checked && cat.test || examples.checked && cat.example);
  }
  function impact(name) {
    const seen = new Set([name]), queue = [name];
    while (queue.length) {
      for (const next of incoming.get(queue.pop())) {
        if (!seen.has(next)) { seen.add(next); queue.push(next); }
      }
    }
    seen.delete(name);
    return [...seen].sort();
  }
  function link(parent, name) {
    const el = append(parent,"button",name,"module-link");
    el.disabled = !allowed(name);
    el.title = el.disabled ? "Hidden by path filters" : modules.get(name).path;
    el.onclick = () => select(name,true);
    return el;
  }
  function list(parent, items) {
    let offset = 0;
    function page() {
      for (const name of items.slice(offset,offset+40)) link(parent,name);
      offset += 40;
      if (offset < items.length) {
        const more = append(parent,"button","Show more (" + (items.length-offset) + ")","more");
        more.onclick = () => { more.remove(); page(); };
      }
    }
    page();
  }
  function inspect() {
    const panel = $("details");
    panel.replaceChildren();
    $("clear").hidden = !selected;
    if (!selected) {
      append(panel,"p",names.length ? "Select a module to inspect its imports and change impact." : "No modules to inspect.","hint");
      const hubs = ranked.filter(n => visible.has(n) && degree(n)).slice(0,5);
      if (hubs.length) {
        append(panel,"h4","Most connected modules");
        hubs.forEach(n => link(panel,n));
      }
      return;
    }
    const item = modules.get(selected), affected = impact(selected);
    append(panel,"h3",selected);
    append(panel,"p",item.path,"path");
    append(panel,"span",item.cycle === null ? "Outside dependency cycles" : "Circular group " + (item.cycle+1),
      item.cycle === null ? "status" : "status cyclic");
    const metrics = append(panel,"dl","","metrics");
    function metric(label, count) {
      const cell = append(metrics,"div","");
      append(cell,"dt",label); append(cell,"dd",count);
    }
    metric("Dependencies",outgoing.get(selected).length); metric("Importers",incoming.get(selected).length);
    metric("Potential impact",affected.length);
    function section(title, items, open, empty, help) {
      const block = append(panel,"details","");
      const summary = append(block,"summary",title);
      append(summary,"span",items.length,"count");
      block.open = open;
      function fill() {
        if (block.children.length > 1 || !block.open) return;
        if (help) append(block,"p",help,"hint");
        const body = append(block,"div","","links");
        if (items.length) list(body,items); else append(body,"p",empty,"hint");
      }
      fill(); block.ontoggle = fill;
    }
    section("Direct dependencies",outgoing.get(selected),true,"No outgoing imports.");
    section("Direct importers",incoming.get(selected),true,"No incoming imports.");
    section("Potential change impact",affected,false,"No reachable importers.",
      "Direct and indirect importers that may be affected by a change.");
  }
  function updateIndex() {
    const container = $("module-list");
    container.replaceChildren();
    if (!$("index").open) return;
    list(container,[...visible]);
    if (!visible.size) append(container,"p","No visible modules.","hint");
  }
  function updateView(reframe = false) {
    if (selected && !allowed(selected)) selected = null;
    if (!selected) mode.value = "all";
    mode.disabled = !selected;
    $("focus-help").hidden = !!selected;
    const focus = mode.value;
    const out = new Set(selected ? outgoing.get(selected) : []);
    const ins = new Set(selected ? incoming.get(selected) : []);
    visible = new Set(names.filter(n => allowed(n) && (focus === "all" || n === selected ||
      (focus !== "in" && out.has(n)) || (focus !== "out" && ins.has(n)))));
    cy.batch(() => {
      for (const node of nodes) {
        const id = node.id();
        node.toggleClass("hidden",!visible.has(id));
        node.toggleClass("picked",id === selected);
        node.toggleClass("outgoing",id !== selected && out.has(id));
        node.toggleClass("incoming",id !== selected && ins.has(id));
        node.toggleClass("muted",!!selected && id !== selected && !out.has(id) && !ins.has(id) && !(cycleLit && node.hasClass("cyclic")));
      }
      for (const edge of edges) {
        const {source,target} = edge.data();
        const isOut = source === selected, isIn = target === selected;
        const focused = focus === "all" || (focus !== "in" && isOut) || (focus !== "out" && isIn);
        edge.toggleClass("hidden",!focused || !visible.has(source) || !visible.has(target));
        edge.toggleClass("incoming",isIn); edge.toggleClass("outgoing",isOut);
        edge.toggleClass("muted",!!selected && !isIn && !isOut && !(cycleLit && edge.hasClass("cyclic")));
      }
      cy.elements(".cyclic").toggleClass("cycle-lit",cycleLit);
    });
    const count = Number(tests.checked) + Number(examples.checked) + Number(focus !== "all");
    $("filters").classList.toggle("active",!!count);
    $("filter-count").textContent = count; $("filter-count").hidden = !count;
    $("visible-count").textContent = visible.size + " / " + names.length + " visible";
    $("empty").hidden = visible.size > 0;
    $("empty-title").textContent = names.length ? "No visible modules" : "No Python modules found";
    $("empty-help").textContent = names.length ? "Reset the filters to see the graph." : "Scan a directory containing Python source files.";
    $("empty-reset").hidden = !names.length;
    for (const id of ["fit","zoom-in","zoom-out"]) $(id).disabled = !visible.size;
    hideTip(); search(); inspect(); updateIndex();
    if (reframe) fit();
  }
  function select(name, center) {
    const wasFocused = mode.value !== "all";
    selected = name;
    query.value = "";
    updateView(wasFocused);
    if (center && name && mode.value === "all") {
      const node = cy.getElementById(name);
      cy.zoom(Math.max(0.9,cy.zoom())); cy.center(node);
    }
  }
  function search() {
    const term = query.value.trim().toLowerCase(), results = $("results");
    results.hidden = !term; results.replaceChildren();
    cy.batch(() => {
      nodes.filter(".found").removeClass("found");
      if (!term) return;
      const matches = [...visible].filter(n => n.toLowerCase().includes(term));
      for (const name of matches) cy.getElementById(name).addClass("found");
      for (const name of matches.slice(0,40)) link(results,name);
      if (!matches.length) append(results,"p","No visible modules match.","hint");
      if (matches.length > 40) append(results,"p","Showing 40 of " + matches.length + " matches.","hint");
    });
  }
  function reset() {
    tests.checked = examples.checked = false; mode.value = "all"; query.value = "";
    updateView(true);
  }
  function filters(open) {
    $("filter-panel").hidden = !open; $("filters").setAttribute("aria-expanded",String(open));
  }
  $("filters").onclick = () => filters($("filter-panel").hidden);
  $("reset").onclick = $("empty-reset").onclick = reset;
  for (const control of [mode,tests,examples]) control.onchange = () => updateView(true);
  $("clear").onclick = () => { select(null,false); query.focus(); };
  $("cycles").onclick = () => {
    cycleLit = !cycleLit; $("cycles").setAttribute("aria-pressed",String(cycleLit)); updateView();
  };
  $("fit").onclick = fit;
  function zoom(factor) {
    cy.zoom({level:cy.zoom()*factor,renderedPosition:{x:cy.width()/2,y:cy.height()/2}});
  }
  $("zoom-in").onclick = () => zoom(1.25);
  $("zoom-out").onclick = () => zoom(0.8);
  $("index").ontoggle = updateIndex;
  query.oninput = search;
  query.onfocus = search;
  function dismissSearch() { $("results").hidden = true; }
  document.addEventListener("pointerdown",event => {
    if (!event.target.closest(".filter-wrap")) filters(false);
    if (!event.target.closest(".search")) dismissSearch();
  });
  document.addEventListener("keydown",event => {
    if (event.key === "/" && !event.ctrlKey && !event.altKey && !event.metaKey &&
        !event.target.closest("input,select,textarea")) { event.preventDefault(); query.focus(); query.select(); }
    if (event.key === "Escape") {
      if (!$("filter-panel").hidden) { filters(false); $("filters").focus(); }
      else if (event.target.closest(".search")) { query.value = ""; query.focus(); search(); }
    }
    const first = $("results").querySelector("button");
    if (event.target === query && first && !$("results").hidden) {
      if (event.key === "Enter") { first.click(); query.focus(); }
      if (event.key === "ArrowDown") { event.preventDefault(); first.focus(); }
    }
  });
  function hideTip() { $("tooltip").hidden = true; }
  cy.on("mouseover","node",event => {
    const node = event.target, tip = $("tooltip");
    node.addClass("hovered"); tip.textContent = node.id(); tip.hidden = false;
    const point = node.renderedPosition();
    tip.style.left = Math.max(4,Math.min(point.x+12,cy.width()-tip.offsetWidth-4)) + "px";
    tip.style.top = Math.max(4,Math.min(point.y-tip.offsetHeight-8,cy.height()-tip.offsetHeight-4)) + "px";
  });
  cy.on("mouseout","node",event => { event.target.removeClass("hovered"); hideTip(); });
  cy.on("tap","node",event => select(event.target.id(),false));
  cy.on("tap",event => { if (event.target === cy) select(null,false); });
  if (data.warnings.length) {
    $("diagnostics").hidden = false;
    $("warning-count").textContent = "Analysis warnings (" + data.warnings.length + ")";
    for (const warning of data.warnings) append($("warnings"),"li",warning);
  }
  updateView();
})();
