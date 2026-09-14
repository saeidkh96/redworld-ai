const canvas = document.getElementById("worldCanvas");
let ctx = canvas.getContext("2d", { alpha: false });
const screenCtx = ctx;
const staticCanvas = document.createElement("canvas");
const staticCtx = staticCanvas.getContext("2d", { alpha: false });
let pixelRatio = 1;
let staticDirty = true;
let lastFrame = 0;
const TARGET_FRAME_MS = 1000 / 24;
const INTERACTION_DPR_CAP = 1.0;
const IDLE_FRAME_MS = 1000 / 12;
let panTransformRaf = 0;
let hoverRaf = 0;

let snapshot = null;
let selected = null;
let selectedCitizen = null;
let socket = null;
let live = false;
let citizens = [];
let animationTime = 0;
let hoverAgent = null;
let panPreviewX = 0;
let panPreviewY = 0;
let panStartX = 0;
let panStartY = 0;
let panBaseCameraX = 0;
let panBaseCameraY = 0;
const cityEngine = new window.RedWorldCityEngine();
let cityScene = null;

// v0.1.13: the visible city is the simulation map itself.
// The cinematic image is no longer used as terrain because its streets and
// buildings do not share coordinates with the simulation geography.
const USE_CINEMATIC_MAP = false;
const cinematicMap = new Image();
let cinematicReady = false;
if (USE_CINEMATIC_MAP) {
  cinematicMap.decoding = "async";
  cinematicMap.src = "/static/assets/genesis-city-cinematic.webp";
  cinematicMap.onload = () => {
    cinematicReady = true;
    staticDirty = true;
    document.getElementById("worldStage").classList.add("cinematic-ready");
  };
}

const camera = { zoom: 1.08, x: 0, y: 8, dragging: false, lastX: 0, lastY: 0 };
const layers = {
  buildings: true,
  labels: true,
  people: true,
  traffic: true,
  economy: false,
  services: false,
};

let fpsFrames = 0;
let fpsWindowStart = performance.now();
let renderAverage = 0;
let lastSocketMessage = 0;

const districtPalette = {
  residential: [49, 87, 78], education: [58, 73, 108], mixed: [47, 85, 91], central: [53, 76, 89],
  commercial: [91, 55, 78], industrial: [92, 79, 51], civic: [55, 83, 74],
};

const buildingPalette = {
  home: [86, 117, 119], workplace: [70, 92, 115], park: [57, 103, 70], shop: [132, 82, 73], station: [72, 113, 123],
  government: [105, 95, 113], bank: [121, 98, 67], university: [76, 82, 128], hospital: [137, 77, 77],
};

function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
function rgba(rgb, a = 1) { return `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${a})`; }
function shade(rgb, factor) { return rgb.map((v) => clamp(Math.round(v * factor), 0, 255)); }
function hashCode(text) { let hash = 0; for (let i = 0; i < text.length; i += 1) hash = (hash * 31 + text.charCodeAt(i)) | 0; return Math.abs(hash); }
function randFrom(text, min = 0, max = 1) { return min + (hashCode(text) % 10000) / 10000 * (max - min); }

function resize() {
  const rect = canvas.getBoundingClientRect();
  pixelRatio = Math.min(window.devicePixelRatio || 1, INTERACTION_DPR_CAP);
  canvas.width = Math.floor(rect.width * pixelRatio);
  canvas.height = Math.floor(rect.height * pixelRatio);
  staticCanvas.width = canvas.width;
  staticCanvas.height = canvas.height;
  screenCtx.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
  staticCtx.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
  staticDirty = true;
}
window.addEventListener("resize", resize);

function isoPoint(x, y, z = 0) {
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  const scale = Math.min(width / 132, height / 87) * camera.zoom;
  const dx = x - 50;
  const dy = y - 48;
  return {
    x: width * 0.5 + (dx - dy) * scale * 0.9 + camera.x,
    y: height * 0.43 + (dx + dy) * scale * 0.45 + camera.y - z * scale * 0.72,
    scale,
  };
}

function polygon(points, fill, stroke = null, lineWidth = 1) {
  if (!points.length) return;
  ctx.beginPath(); ctx.moveTo(points[0].x, points[0].y); points.slice(1).forEach((p) => ctx.lineTo(p.x, p.y)); ctx.closePath();
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lineWidth; ctx.stroke(); }
}
function isoRect(cx, cy, width, depth, z = 0) {
  return [isoPoint(cx - width/2, cy - depth/2, z), isoPoint(cx + width/2, cy - depth/2, z), isoPoint(cx + width/2, cy + depth/2, z), isoPoint(cx - width/2, cy + depth/2, z)];
}
function line(a, b, color, width, dash = []) {
  ctx.save(); ctx.strokeStyle = color; ctx.lineWidth = width; ctx.setLineDash(dash); ctx.lineCap = "round"; ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke(); ctx.restore();
}

function worldLight() {
  const minute = snapshot?.summary?.minute_of_day ?? 360;
  const h = minute / 60;
  const daylight = clamp(1 - Math.abs(h - 13) / 9, 0.12, 1);
  return { h, daylight, night: daylight < 0.42 };
}

function cinematicLayout() {
  const w = canvas.clientWidth;
  const h = canvas.clientHeight;
  const imageAspect = cinematicMap.naturalWidth / cinematicMap.naturalHeight;
  const stageAspect = w / h;
  let baseW;
  let baseH;
  if (stageAspect > imageAspect) {
    baseW = w;
    baseH = w / imageAspect;
  } else {
    baseH = h;
    baseW = h * imageAspect;
  }
  const drawW = baseW * camera.zoom;
  const drawH = baseH * camera.zoom;
  return {
    drawW,
    drawH,
    dx: (w - drawW) / 2 + camera.x,
    dy: (h - drawH) / 2 + camera.y,
  };
}

function imagePoint(nx, ny) {
  const layout = cinematicLayout();
  return {
    x: layout.dx + nx * layout.drawW,
    y: layout.dy + ny * layout.drawH,
  };
}

function drawCinematicBackground() {
  const w = canvas.clientWidth;
  const h = canvas.clientHeight;
  ctx.fillStyle = "#050b10";
  ctx.fillRect(0, 0, w, h);
  if (!cinematicReady) return false;

  const { drawW, drawH, dx, dy } = cinematicLayout();
  ctx.save();
  if (!layers.buildings) {
    ctx.globalAlpha = .34;
    ctx.filter = "grayscale(.8) brightness(.72)";
  }
  ctx.drawImage(cinematicMap, dx, dy, drawW, drawH);
  ctx.restore();

  const night = worldLight().night;
  ctx.save();
  const tint = ctx.createLinearGradient(0, 0, 0, h);
  tint.addColorStop(0, night ? "rgba(1,7,14,.04)" : "rgba(17,31,28,.04)");
  tint.addColorStop(1, "rgba(1,5,9,.12)");
  ctx.fillStyle = tint;
  ctx.fillRect(0, 0, w, h);
  ctx.restore();
  return true;
}

function drawBackground() {
  const w = canvas.clientWidth, h = canvas.clientHeight;
  const { daylight } = worldLight();
  const g = ctx.createLinearGradient(0, 0, 0, h);
  g.addColorStop(0, daylight > .45 ? "#10252b" : "#07131d");
  g.addColorStop(.5, "#0b1d22");
  g.addColorStop(1, "#061015");
  ctx.fillStyle = g; ctx.fillRect(0, 0, w, h);

  // Soft world glow.
  const rg = ctx.createRadialGradient(w*.45,h*.32,10,w*.45,h*.42,w*.62);
  rg.addColorStop(0, `rgba(71,111,108,${0.12*daylight})`); rg.addColorStop(1,"rgba(0,0,0,0)");
  ctx.fillStyle = rg; ctx.fillRect(0,0,w,h);

  // Terrain grid, deliberately faint.
  ctx.save(); ctx.globalAlpha = .055; ctx.strokeStyle = "#8fb1b2"; ctx.lineWidth = 1;
  for (let x=-25;x<=130;x+=5){ const a=isoPoint(x,-15), b=isoPoint(x,120); line(a,b,"#89a8ac",1); }
  for (let y=-25;y<=130;y+=5){ const a=isoPoint(-15,y), b=isoPoint(120,y); line(a,b,"#89a8ac",1); }
  ctx.restore();

  drawCityGround();
  drawRiver();
}

function drawCityGround() {
  const city = isoRect(49, 49, 94, 88, -0.12);
  polygon(city, "rgba(18,42,42,.83)", "rgba(113,151,145,.13)", 1);

  // Forested outer belt gives the map a finished city boundary.
  for (let i = 0; i < 72; i += 1) {
    const side = i % 4;
    const t = ((hashCode(`forest-${i}`) % 10000) / 10000);
    let x;
    let y;
    if (side === 0) { x = 3 + t * 92; y = 4 + randFrom(`fy-${i}`, 0, 5); }
    else if (side === 1) { x = 3 + t * 92; y = 91 + randFrom(`fy-${i}`, 0, 5); }
    else if (side === 2) { x = 3 + randFrom(`fx-${i}`, 0, 5); y = 5 + t * 86; }
    else { x = 93 + randFrom(`fx-${i}`, 0, 4); y = 5 + t * 86; }
    drawTree(x, y, .34 + (i % 4) * .05, i);
  }

  // Green medians/open space between districts.
  const greens = [
    [33, 31, 9, 7], [64, 31, 10, 7], [34, 60, 10, 8], [64, 62, 9, 7],
  ];
  greens.forEach(([x, y, w, d]) => {
    const patch = isoRect(x, y, w, d, .01);
    polygon(patch, "rgba(34,75,55,.38)", "rgba(88,127,94,.08)", .5);
  });
}

function riverPathPoints() {
  return [[95,-6],[101,7],[97,18],[104,31],[98,44],[105,59],[98,73],[105,88],[99,108]];
}
function drawRiver() {
  const pts = riverPathPoints().map(([x,y]) => isoPoint(x,y,.02));
  const s = isoPoint(0,0).scale;
  ctx.save(); ctx.lineCap="round";ctx.lineJoin="round";
  ctx.strokeStyle="#0a2935";ctx.lineWidth=Math.max(30,s*5.8);ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);pts.slice(1).forEach(p=>ctx.lineTo(p.x,p.y));ctx.stroke();
  ctx.strokeStyle="rgba(66,132,151,.34)";ctx.lineWidth=Math.max(22,s*4.2);ctx.stroke();
  ctx.strokeStyle="rgba(141,203,211,.12)";ctx.lineWidth=Math.max(1.5,s*.28);ctx.setLineDash([s*1.5,s*2.2]);ctx.stroke();
  ctx.restore();
  // River banks.
  pts.slice(1).forEach((p,i)=>{ if(i%2!==0)return; ctx.fillStyle="rgba(74,111,89,.22)"; ctx.beginPath();ctx.arc(p.x-12,p.y-2,7,0,Math.PI*2);ctx.fill(); });
}

function drawDistricts() {
  snapshot.districts.forEach((d) => {
    const rgb = districtPalette[d.kind] || [50,78,89];
    const tile = isoRect(d.x,d.y,d.width,d.height,.01);
    polygon(tile, rgba(rgb,.17), rgba(shade(rgb,1.45),.13), 1);

    // Blocks and sidewalks inside each district.
    for(let gx=-1;gx<=1;gx+=1){
      for(let gy=-1;gy<=1;gy+=1){
        const bx=d.x+gx*d.width*.27, by=d.y+gy*d.height*.27;
        const block=isoRect(bx,by,d.width*.22,d.height*.22,.025);
        polygon(block,"rgba(66,88,83,.12)","rgba(141,172,161,.07)",.6);
      }
    }

    if(layers.labels){
      const p=isoPoint(d.x,d.y-d.height/2-1.2,.1); ctx.save(); ctx.textAlign="center"; ctx.font="800 7px Segoe UI";ctx.fillStyle="rgba(184,209,214,.54)";ctx.fillText(d.name.toUpperCase(),p.x,p.y);ctx.restore();
    }
  });
}

function roadWidth(road) {
  const s = isoPoint(0, 0).scale;
  if (road.kind === "arterial") return Math.max(8, s * 1.02);
  if (road.kind === "street") return Math.max(5.4, s * 0.68);
  return Math.max(2.8, s * 0.34);
}

function drawRoadSegment(road) {
  const a = isoPoint(road.x1, road.y1, .09);
  const b = isoPoint(road.x2, road.y2, .09);
  const s = isoPoint(0, 0).scale;
  const width = roadWidth(road);
  const arterial = road.kind === "arterial";
  const access = road.kind === "access";

  // Pavement/sidewalk shoulders first, then asphalt.
  line(a, b, "rgba(135,151,145,.20)", width + (access ? 3 : 8));
  line(a, b, "rgba(16,24,26,.98)", width + (access ? 1.8 : 5));
  line(a, b, arterial ? "rgba(62,72,75,.99)" : access ? "rgba(54,66,66,.92)" : "rgba(57,70,72,.98)", width);

  // Lane markings are only for streets that vehicles should use.
  if (!access) {
    line(a, b, arterial ? "rgba(237,211,142,.42)" : "rgba(221,226,215,.25)", .85, [s * .75, s * 1.2]);
    if (arterial) {
      // Dual carriageway hint.
      const dx = b.x - a.x;
      const dy = b.y - a.y;
      const length = Math.hypot(dx, dy) || 1;
      const ox = (-dy / length) * Math.max(1.3, s * .13);
      const oy = (dx / length) * Math.max(1.3, s * .13);
      line({ x: a.x + ox, y: a.y + oy }, { x: b.x + ox, y: b.y + oy }, "rgba(211,220,211,.17)", .65);
      line({ x: a.x - ox, y: a.y - oy }, { x: b.x - ox, y: b.y - oy }, "rgba(211,220,211,.17)", .65);
    }
  }
}

function drawIntersection(location) {
  const p = isoPoint(location.x, location.y, .105);
  const s = isoPoint(0, 0).scale;
  const arterial = String(location.id).startsWith("hub-");
  const radius = arterial ? Math.max(4.8, s * .55) : Math.max(3.3, s * .38);
  ctx.save();
  ctx.fillStyle = arterial ? "rgba(65,77,79,.98)" : "rgba(58,70,72,.97)";
  ctx.beginPath();
  ctx.arc(p.x, p.y, radius, 0, Math.PI * 2);
  ctx.fill();
  if (arterial) {
    ctx.strokeStyle = "rgba(235,226,191,.25)";
    ctx.lineWidth = .75;
    ctx.setLineDash([2, 3]);
    ctx.beginPath();
    ctx.arc(p.x, p.y, radius * .62, 0, Math.PI * 2);
    ctx.stroke();
  }
  ctx.restore();
}

function drawRoads() {
  const accessRoads = snapshot.roads.filter((r) => r.kind === "access");
  const streets = snapshot.roads.filter((r) => r.kind === "street");
  const arterials = snapshot.roads.filter((r) => r.kind === "arterial");
  // Draw wide roads below local driveways so entrances read correctly.
  arterials.forEach(drawRoadSegment);
  streets.forEach(drawRoadSegment);
  accessRoads.forEach(drawRoadSegment);

  snapshot.locations
    .filter((l) => String(l.id).startsWith("street-") || String(l.id).startsWith("hub-"))
    .forEach(drawIntersection);

  drawBridges();
}

function drawBridges() {
  // Bridges are decorative infrastructure aligned with the right-side river.
  // They are not navigation shortcuts unless geography contains a road there.
  const bridges = [[87, 22, 100, 22], [88, 49, 101, 49], [88, 75, 101, 75]];
  bridges.forEach(([x1, y1, x2, y2]) => {
    const a = isoPoint(x1, y1, .32);
    const b = isoPoint(x2, y2, .32);
    const s = isoPoint(0, 0).scale;
    line(a, b, "rgba(10,13,15,.98)", s * 1.1 + 8);
    line(a, b, "rgba(87,97,98,.98)", s * 1.1 + 4);
    line(a, b, "rgba(222,214,176,.22)", .9, [s * .85, s * 1.1]);
    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const length = Math.hypot(dx, dy) || 1;
    const nx = -dy / length;
    const ny = dx / length;
    for (let i = 1; i <= 3; i += 1) {
      const t = i / 4;
      const x = a.x + dx * t;
      const y = a.y + dy * t;
      ctx.strokeStyle = "rgba(157,180,182,.42)";
      ctx.lineWidth = .8;
      ctx.beginPath();
      ctx.moveTo(x + nx * 5, y + ny * 5);
      ctx.lineTo(x - nx * 5, y - ny * 5);
      ctx.stroke();
    }
  });
}

function drawTree(x,y,size=.5,variant=0){
  const base=isoPoint(x,y,.08), mid=isoPoint(x,y,.72*size), top=isoPoint(x,y,1.35*size); const s=base.scale;
  const crown=Math.max(2.5,s*size*.52);
  const palettes=[
    ["rgba(37,88,58,.98)","rgba(61,126,74,.98)","rgba(83,145,86,.96)"],
    ["rgba(42,96,62,.98)","rgba(72,137,80,.98)","rgba(101,154,88,.96)"],
    ["rgba(31,78,55,.98)","rgba(54,116,71,.98)","rgba(74,137,77,.96)"],
  ];
  const colors=palettes[variant%palettes.length];
  ctx.save();
  ctx.fillStyle="rgba(2,10,10,.18)";ctx.beginPath();ctx.ellipse(base.x+2,base.y+2,crown*.85,crown*.35,-.15,0,Math.PI*2);ctx.fill();
  ctx.strokeStyle="rgba(77,57,35,.96)";ctx.lineWidth=Math.max(1,s*.09);ctx.beginPath();ctx.moveTo(base.x,base.y);ctx.lineTo(mid.x,mid.y+1);ctx.stroke();
  ctx.shadowColor="rgba(38,104,62,.30)";ctx.shadowBlur=5;
  [[-.48,.15,.68],[.48,.18,.66],[0,-.36,.78],[0,.20,.82]].forEach((part,i)=>{
    ctx.fillStyle=colors[i%colors.length];ctx.beginPath();ctx.arc(top.x+part[0]*crown,top.y+part[1]*crown,crown*part[2],0,Math.PI*2);ctx.fill();
  });
  ctx.shadowBlur=0;
  ctx.fillStyle="rgba(130,180,103,.34)";ctx.beginPath();ctx.arc(top.x-crown*.18,top.y-crown*.42,crown*.25,0,Math.PI*2);ctx.fill();
  ctx.restore();
}

function drawLamp(x, y) {
  const base = isoPoint(x, y, .08);
  const top = isoPoint(x, y, .72);
  ctx.save();
  ctx.strokeStyle = "rgba(73,84,82,.9)";
  ctx.lineWidth = .8;
  ctx.beginPath();
  ctx.moveTo(base.x, base.y);
  ctx.lineTo(top.x, top.y);
  ctx.stroke();
  ctx.fillStyle = worldLight().night ? "rgba(255,220,137,.78)" : "rgba(224,232,215,.34)";
  ctx.shadowColor = "rgba(255,205,107,.48)";
  ctx.shadowBlur = worldLight().night ? 7 : 2;
  ctx.beginPath();
  ctx.arc(top.x, top.y, 1.15, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

function drawStreetFurniture() {
  snapshot.districts.forEach((d) => {
    const residential = d.kind === "residential" || d.kind === "mixed";
    const treeCount = residential ? 30 : (d.kind === "civic" || d.kind === "education" ? 20 : 12);
    for (let i = 0; i < treeCount; i += 1) {
      const ring = i % 2 === 0 ? .43 : .31;
      const angle = (i / treeCount) * Math.PI * 2 + (hashCode(d.id) % 9) * .08;
      const x = d.x + Math.cos(angle) * d.width * ring;
      const y = d.y + Math.sin(angle) * d.height * ring;
      drawTree(x, y, .38 + (i % 4) * .055, i + hashCode(d.id));
    }
    // Lamps around the inner street loop.
    for (let i = 0; i < 8; i += 1) {
      const angle = (i / 8) * Math.PI * 2;
      drawLamp(
        d.x + Math.cos(angle) * d.width * .29,
        d.y + Math.sin(angle) * d.height * .29,
      );
    }
  });
}

function buildingDimensions(l) {
  const h = hashCode(l.id);
  if (l.type === "home") return [1.65, 1.25, 1.18 + (h % 4) * .14];
  if (l.type === "workplace") return [2.25, 1.7, 2.8 + (h % 8) * .44];
  if (l.type === "park") return [5.4, 4.2, .08];
  if (l.type === "station") return [2.0, 1.45, .62];
  if (l.type === "government") return [4.2, 3.0, 3.5];
  if (l.type === "bank") return [3.3, 2.45, 4.6];
  if (l.type === "university") return [5.0, 3.4, 3.25];
  if (l.type === "hospital") return [4.2, 3.2, 3.1];
  if (l.type === "shop") return [3.2, 2.4, 1.5];
  return [1.8, 1.4, 2.0];
}

function drawLot(l, w, d, kind = "urban") {
  const lot = isoRect(l.x, l.y, w * 1.6, d * 1.58, .04);
  const fill = kind === "residential"
    ? "rgba(49,77,62,.48)"
    : kind === "industrial"
      ? "rgba(76,72,60,.36)"
      : "rgba(78,88,84,.27)";
  polygon(lot, fill, "rgba(154,170,159,.13)", .55);
}

function drawBoxBuilding(l, w, d, h, rgb) {
  const base = isoRect(l.x, l.y, w, d, .08);
  const top = isoRect(l.x, l.y, w, d, h);
  const left = [base[3], base[2], top[2], top[3]];
  const right = [base[1], base[2], top[2], top[1]];
  ctx.save();
  ctx.shadowColor = "rgba(0,0,0,.42)";
  ctx.shadowBlur = 9;
  ctx.shadowOffsetY = 5;
  polygon(left, rgba(shade(rgb, .52), .99));
  polygon(right, rgba(shade(rgb, .72), .99));
  polygon(top, rgba(shade(rgb, 1.16), .99), "rgba(225,240,240,.11)", .6);
  ctx.restore();
  return { base, top };
}

function drawWindows(l, w, d, h) {
  if (h < 1.6) return;
  const rows = Math.min(7, Math.max(2, Math.floor(h / .62)));
  const cols = Math.min(5, Math.max(2, Math.floor(w / .48)));
  const night = worldLight().night;
  const seed = hashCode(l.id);
  for (let r = 1; r <= rows; r += 1) {
    for (let c = 1; c <= cols; c += 1) {
      if ((seed + r * 11 + c * 7) % 5 === 0) continue;
      const z = h * r / (rows + 1);
      const oy = (-d * .34) + (c - 1) * (d * .68 / Math.max(1, cols - 1));
      const p = isoPoint(l.x + w / 2 + .02, l.y + oy, z);
      ctx.fillStyle = night ? "rgba(247,207,120,.64)" : "rgba(169,215,224,.31)";
      ctx.fillRect(p.x - 1.25, p.y - .7, 2.5, 1.35);
    }
  }
}

function drawHome(l, w, d, h) {
  drawLot(l, w, d, "residential");
  const rgb = [100, 111, 108];
  drawBoxBuilding(l, w, d, h, rgb);
  const roofH = .72;
  const a = isoPoint(l.x - w / 2, l.y - d / 2, h);
  const b = isoPoint(l.x + w / 2, l.y - d / 2, h);
  const c = isoPoint(l.x + w / 2, l.y + d / 2, h);
  const d1 = isoPoint(l.x - w / 2, l.y + d / 2, h);
  const ridge1 = isoPoint(l.x, l.y - d / 2, h + roofH);
  const ridge2 = isoPoint(l.x, l.y + d / 2, h + roofH);
  const roof = hashCode(l.id) % 3;
  const roofColors = [
    [117, 68, 56], [77, 78, 78], [92, 77, 62],
  ];
  const rc = roofColors[roof];
  polygon([a, b, ridge1], rgba(shade(rc, .92), .99));
  polygon([d1, c, ridge2], rgba(shade(rc, .8), .99));
  polygon([a, ridge1, ridge2, d1], rgba(shade(rc, 1.08), .99));
  polygon([b, c, ridge2, ridge1], rgba(shade(rc, .9), .99));
  const door = isoPoint(l.x + w / 2 + .03, l.y, h * .34);
  ctx.fillStyle = "rgba(37,46,45,.88)";
  ctx.fillRect(door.x - 1.1, door.y - 2.2, 2.2, 4.4);
  // Tiny garden trees, kept off the access edge.
  drawTree(l.x - w * .72, l.y + d * .72, .3, hashCode(l.id));
}

function drawPark(l, w, d) {
  const ground = isoRect(l.x, l.y, w, d, .07);
  polygon(ground, "rgba(42,100,65,.88)", "rgba(107,165,108,.26)", .8);
  const p1 = isoPoint(l.x - w * .43, l.y, .09);
  const p2 = isoPoint(l.x + w * .43, l.y, .09);
  const p3 = isoPoint(l.x, l.y - d * .41, .09);
  const p4 = isoPoint(l.x, l.y + d * .41, .09);
  line(p1, p2, "rgba(190,174,136,.39)", 2.6);
  line(p3, p4, "rgba(190,174,136,.34)", 2.4);
  const center = isoPoint(l.x, l.y, .12);
  ctx.fillStyle = "rgba(84,132,145,.55)";
  ctx.beginPath();
  ctx.arc(center.x, center.y, Math.max(2.5, center.scale * .35), 0, Math.PI * 2);
  ctx.fill();
  for (let i = 0; i < 13; i += 1) {
    const ox = randFrom(l.id + `x${i}`, -w * .42, w * .42);
    const oy = randFrom(l.id + `y${i}`, -d * .38, d * .38);
    if (Math.abs(ox) < .55 || Math.abs(oy) < .55) continue;
    drawTree(l.x + ox, l.y + oy, .38 + (i % 4) * .055, i);
  }
}

function drawWorkplace(l, w, d, h) {
  const district = snapshot.districts.find((item) => item.id === l.district_id);
  const industrial = district?.kind === "industrial";
  drawLot(l, w, d, industrial ? "industrial" : "urban");
  if (industrial) {
    const lowH = Math.min(2.1, h * .55);
    drawBoxBuilding(l, w * 1.35, d * 1.15, lowH, [92, 91, 82]);
    const roof = isoRect(l.x, l.y, w * 1.15, d * .92, lowH + .08);
    polygon(roof, "rgba(111,108,92,.98)");
    const stack = isoPoint(l.x + w * .35, l.y - d * .18, lowH + .9);
    ctx.fillStyle = "rgba(82,78,70,.95)";
    ctx.fillRect(stack.x - 1.2, stack.y, 2.4, 8);
  } else {
    const palette = [[62,88,109], [67,93,105], [73,84,103], [65,96,91]];
    const rgb = palette[hashCode(l.id) % palette.length];
    drawBoxBuilding(l, w, d, h, rgb);
    drawWindows(l, w, d, h);
    if (h > 4.2) {
      const crown = isoRect(l.x, l.y, w * .7, d * .68, h + .28);
      polygon(crown, rgba(shade(rgb, 1.2), .95), "rgba(204,228,232,.12)", .5);
    }
  }
}

function drawShop(l, w, d, h) {
  drawLot(l, w, d, "urban");
  drawBoxBuilding(l, w, d, h, [112, 79, 68]);
  const front = isoPoint(l.x + w / 2 + .04, l.y, h * .42);
  ctx.fillStyle = "rgba(238,176,112,.78)";
  ctx.fillRect(front.x - 5, front.y - 1.2, 10, 2.4);
}

function drawLandmark(l, w, d, h) {
  drawLot(l, w, d, "urban");
  const rgb = buildingPalette[l.type] || [100, 100, 110];
  if (l.type === "hospital") {
    // Main block + two wings.
    drawBoxBuilding(l, w * .58, d, h, rgb);
    const left = { ...l, x: l.x - w * .36 };
    const right = { ...l, x: l.x + w * .36 };
    drawBoxBuilding(left, w * .48, d * .58, h * .72, shade(rgb, .92));
    drawBoxBuilding(right, w * .48, d * .58, h * .72, shade(rgb, .92));
  } else if (l.type === "university") {
    drawBoxBuilding(l, w, d * .64, h, rgb);
    const annex = { ...l, y: l.y + d * .36 };
    drawBoxBuilding(annex, w * .72, d * .3, h * .62, shade(rgb, .92));
  } else if (l.type === "government") {
    drawBoxBuilding(l, w, d, h * .75, rgb);
    const dome = isoPoint(l.x, l.y, h * .75 + .45);
    ctx.fillStyle = "rgba(199,188,154,.74)";
    ctx.beginPath();
    ctx.arc(dome.x, dome.y, Math.max(3.4, dome.scale * .42), Math.PI, 0);
    ctx.fill();
  } else {
    drawBoxBuilding(l, w, d, h, rgb);
  }
  drawWindows(l, w, d, h);
  if (l.type === "hospital") {
    const p = isoPoint(l.x, l.y, h + .13);
    ctx.strokeStyle = "#f6e2e2";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(p.x - 4, p.y);
    ctx.lineTo(p.x + 4, p.y);
    ctx.moveTo(p.x, p.y - 4);
    ctx.lineTo(p.x, p.y + 4);
    ctx.stroke();
  }
  if (l.type === "bank") {
    const p = isoPoint(l.x, l.y, h + .28);
    ctx.fillStyle = "rgba(218,188,111,.72)";
    ctx.beginPath();
    ctx.arc(p.x, p.y, 3.7, 0, Math.PI * 2);
    ctx.fill();
  }
}

function drawStation(l, w, d, h) {
  // Street nodes are navigation-only and should not appear as buildings.
  if (String(l.id).startsWith("street-")) return;
  const pad = isoRect(l.x, l.y, w * 1.7, d * 1.8, .055);
  polygon(pad, "rgba(48,69,72,.76)", "rgba(124,158,158,.15)", .7);
  drawBoxBuilding(l, w, d, h, buildingPalette.station);
  const p = isoPoint(l.x, l.y, h + .2);
  ctx.fillStyle = "rgba(118,225,230,.55)";
  ctx.fillRect(p.x - 4, p.y - 1, 8, 2);
}

function drawBuilding(l) {
  const [w, d, h] = buildingDimensions(l);
  if (l.type === "park") return drawPark(l, w, d);
  if (l.type === "home") return drawHome(l, w, d, h);
  if (l.type === "station") return drawStation(l, w, d, h);
  if (l.type === "workplace") return drawWorkplace(l, w, d, h);
  if (l.type === "shop") return drawShop(l, w, d, h);
  if (["government", "bank", "university", "hospital"].includes(l.type)) {
    return drawLandmark(l, w, d, h);
  }
  drawLot(l, w, d);
  drawBoxBuilding(l, w, d, h, buildingPalette[l.type] || [77, 98, 108]);
  drawWindows(l, w, d, h);
}

// v0.1.16 dense cityscape. Visual infill is decorative only: simulation roads remain
// the navigation source of truth, and every parcel keeps a safety buffer from them.
function pointSegmentDistance(px, py, x1, y1, x2, y2) {
  const vx = x2 - x1;
  const vy = y2 - y1;
  const wx = px - x1;
  const wy = py - y1;
  const len2 = vx * vx + vy * vy;
  if (!len2) return Math.hypot(px - x1, py - y1);
  const t = clamp((wx * vx + wy * vy) / len2, 0, 1);
  return Math.hypot(px - (x1 + t * vx), py - (y1 + t * vy));
}

function visualClearance(x, y, district, clearance = 1.05) {
  if (
    Math.abs(x - district.x) > district.width * .46
    || Math.abs(y - district.y) > district.height * .46
  ) return false;
  for (const road of snapshot.roads || []) {
    if (pointSegmentDistance(x, y, road.x1, road.y1, road.x2, road.y2) < clearance) {
      return false;
    }
  }
  for (const location of snapshot.locations || []) {
    if (Math.hypot(x - location.x, y - location.y) < clearance * .72) return false;
  }
  return true;
}

function decorativeBuilding(id, x, y, district, slot) {
  const location = { id, x, y, district_id: district.id, type: "decorative" };
  if (district.kind === "residential" || district.kind === "mixed") {
    const w = .78 + randFrom(`${id}-w`, 0, .55);
    const depth = .66 + randFrom(`${id}-d`, 0, .42);
    const h = .62 + randFrom(`${id}-h`, 0, .78);
    drawLot(location, w * 1.32, depth * 1.35, "residential");
    drawBoxBuilding(location, w, depth, h, slot % 4 === 0 ? [96, 91, 82] : [79, 91, 87]);
    const roof = isoRect(x, y, w * 1.06, depth * 1.08, h + .18);
    polygon(roof, slot % 3 === 0 ? "rgba(132,72,57,.98)" : "rgba(91,77,67,.98)");
    if (slot % 2 === 0) drawTree(x - .72, y + .62, .22 + (slot % 3) * .025, slot);
    return;
  }

  if (district.kind === "industrial") {
    const w = 1.25 + randFrom(`${id}-w`, 0, 1.15);
    const depth = .9 + randFrom(`${id}-d`, 0, .75);
    const h = .55 + randFrom(`${id}-h`, 0, .9);
    drawLot(location, w * 1.18, depth * 1.25, "industrial");
    drawBoxBuilding(location, w, depth, h, slot % 4 === 0 ? [101, 91, 74] : [79, 84, 82]);
    if (slot % 5 === 0) {
      const chimney = { ...location, x: x + w * .28, y: y - depth * .18 };
      drawBoxBuilding(chimney, .22, .22, h + 1.15, [72, 75, 73]);
    }
    return;
  }

  const downtown = district.kind === "central" || district.kind === "commercial";
  const w = .88 + randFrom(`${id}-w`, 0, downtown ? .75 : .58);
  const depth = .72 + randFrom(`${id}-d`, 0, downtown ? .62 : .5);
  const baseHeight = downtown ? 1.7 : 1.05;
  const h = baseHeight + randFrom(`${id}-h`, 0, downtown ? 4.8 : 2.5);
  const palettes = downtown
    ? [[66, 84, 104], [78, 91, 105], [72, 79, 94], [83, 94, 101]]
    : [[78, 89, 96], [86, 91, 101], [74, 94, 92]];
  const rgb = palettes[slot % palettes.length];
  drawLot(location, w * 1.18, depth * 1.2, "urban");
  drawBoxBuilding(location, w, depth, h, rgb);
  drawWindows(location, w, depth, h);
  if (downtown && slot % 7 === 0) {
    const crown = { ...location, x: x - .05, y: y - .04 };
    drawBoxBuilding(crown, w * .68, depth * .66, .42, shade(rgb, 1.12));
  }
}

function districtTarget(district) {
  if (district.kind === "central") return 105;
  if (district.kind === "commercial") return 92;
  if (district.kind === "residential" || district.kind === "mixed") return 82;
  if (district.kind === "industrial") return 64;
  if (district.kind === "education") return 66;
  if (district.kind === "civic") return 60;
  return 58;
}

function drawUrbanInfill() {
  if (!layers.buildings) return;
  const parcels = [];
  snapshot.districts.forEach((district) => {
    const target = districtTarget(district);
    let accepted = 0;
    for (let attempt = 0; attempt < target * 45 && accepted < target; attempt += 1) {
      const id = `city-${district.id}-${attempt}`;
      const x = district.x + randFrom(`${id}-x`, -district.width * .455, district.width * .455);
      const y = district.y + randFrom(`${id}-y`, -district.height * .455, district.height * .455);
      const roadBuffer = district.kind === "industrial" ? 1.15 : 1.0;
      if (!visualClearance(x, y, district, roadBuffer)) continue;
      const spacing = district.kind === "central" || district.kind === "commercial" ? .86 : .96;
      if (parcels.some((parcel) => Math.hypot(x - parcel.x, y - parcel.y) < spacing)) continue;
      parcels.push({ id: `${district.id}-${accepted}`, x, y, district, slot: accepted });
      accepted += 1;
    }
  });
  parcels.sort((a, b) => (a.x + a.y) - (b.x + b.y));
  parcels.forEach((parcel) => decorativeBuilding(
    parcel.id,
    parcel.x,
    parcel.y,
    parcel.district,
    parcel.slot,
  ));
}

function drawNeighborhoodDetails() {
  snapshot.districts.forEach((district) => {
    const q = .455;
    const corners = [
      [district.x - district.width * q, district.y - district.height * q],
      [district.x + district.width * q, district.y - district.height * q],
      [district.x + district.width * q, district.y + district.height * q],
      [district.x - district.width * q, district.y + district.height * q],
    ].map(([x, y]) => isoPoint(x, y, .025));
    ctx.save();
    ctx.strokeStyle = "rgba(145,158,145,.13)";
    ctx.lineWidth = Math.max(1, isoPoint(0, 0).scale * .16);
    ctx.beginPath();
    ctx.moveTo(corners[0].x, corners[0].y);
    corners.slice(1).forEach((point) => ctx.lineTo(point.x, point.y));
    ctx.closePath();
    ctx.stroke();
    ctx.restore();

    // Dense street greenery and lighting, with a smaller road buffer than buildings.
    for (let i = 0; i < 72; i += 1) {
      const x = district.x + randFrom(
        `green-${district.id}-${i}-x`,
        -district.width * .46,
        district.width * .46,
      );
      const y = district.y + randFrom(
        `green-${district.id}-${i}-y`,
        -district.height * .46,
        district.height * .46,
      );
      if (!visualClearance(x, y, district, .48)) continue;
      if (i % 8 === 0) drawLamp(x, y);
      else drawTree(x, y, .2 + (i % 5) * .035, hashCode(district.id) + i);
    }
  });

  // Tree-lined arterial corridors visually connect the districts without changing navigation.
  (snapshot.roads || [])
    .filter((road) => road.kind === "arterial")
    .forEach((road, roadIndex) => {
      const dx = road.x2 - road.x1;
      const dy = road.y2 - road.y1;
      const length = Math.hypot(dx, dy) || 1;
      const nx = -dy / length;
      const ny = dx / length;
      for (let i = 2; i < 10; i += 1) {
        const t = i / 11;
        const side = i % 2 === 0 ? 1 : -1;
        const x = road.x1 + dx * t + nx * 1.55 * side;
        const y = road.y1 + dy * t + ny * 1.55 * side;
        drawTree(x, y, .23 + (i % 3) * .035, roadIndex * 17 + i);
      }
    });
}


function drawGreenZone(zone) {
  const patch = isoRect(zone.x, zone.y, zone.width, zone.depth, .035);
  const fill = zone.kind === "garden" ? "rgba(38,91,55,.88)" : "rgba(48,108,64,.82)";
  polygon(patch, fill, "rgba(118,176,111,.2)", .55);
  const pathA = isoPoint(zone.x - zone.width * .38, zone.y, .055);
  const pathB = isoPoint(zone.x + zone.width * .38, zone.y, .055);
  line(pathA, pathB, "rgba(190,181,151,.32)", Math.max(1, pathA.scale * .16));
  if (zone.kind === "garden") {
    const pathC = isoPoint(zone.x, zone.y - zone.depth * .35, .057);
    const pathD = isoPoint(zone.x, zone.y + zone.depth * .35, .057);
    line(pathC, pathD, "rgba(190,181,151,.28)", Math.max(1, pathC.scale * .14));
  }
}

function drawShrub(shrub) {
  const p = isoPoint(shrub.x, shrub.y, .13);
  const radius = Math.max(1.2, p.scale * shrub.size * .55);
  const greens = ["rgba(47,111,65,.96)", "rgba(56,124,70,.96)", "rgba(41,98,61,.96)"];
  ctx.fillStyle = greens[shrub.variant % greens.length];
  ctx.beginPath();
  ctx.arc(p.x, p.y, radius, 0, Math.PI * 2);
  ctx.fill();
}

function drawFlowerBed(bed) {
  const p = isoPoint(bed.x, bed.y, .075);
  const colors = ["#d9787d", "#e1b46c", "#9f8bd8", "#d78fb0"];
  ctx.save();
  for (let i = 0; i < 7; i += 1) {
    const a = (i / 7) * Math.PI * 2;
    ctx.fillStyle = colors[(bed.variant + i) % colors.length];
    ctx.beginPath();
    ctx.arc(p.x + Math.cos(a) * 3.2, p.y + Math.sin(a) * 1.8, 1, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.restore();
}

function drawEngineGreenGround() {
  if (!snapshot) return;
  cityScene = cityEngine.build(snapshot);
  (cityScene.greenZones || []).forEach(drawGreenZone);
}

function drawEngineParcel(parcel) {
  if (parcel.type === "pocket-park") {
    const patch = isoRect(parcel.x, parcel.y, 1.45, 1.15, .045);
    polygon(patch, "rgba(40,94,61,.78)", "rgba(104,157,105,.18)", .5);
    drawTree(parcel.x - .32, parcel.y + .18, .22, 1);
    drawTree(parcel.x + .28, parcel.y - .17, .19, 3);
    return;
  }
  if (parcel.type === "plaza") {
    const patch = isoRect(parcel.x, parcel.y, 1.7, 1.45, .048);
    polygon(patch, "rgba(112,111,101,.36)", "rgba(182,178,154,.13)", .55);
    const center = isoPoint(parcel.x, parcel.y, .12);
    ctx.fillStyle = "rgba(94,145,160,.55)";
    ctx.beginPath();
    ctx.arc(center.x, center.y, Math.max(2, center.scale * .22), 0, Math.PI * 2);
    ctx.fill();
    return;
  }

  const l = { id: parcel.id, x: parcel.x, y: parcel.y, type: parcel.type };
  const w = parcel.width;
  const d = parcel.depth;
  const h = parcel.height;
  if (parcel.type === "house") {
    drawLot(l, w, d, "residential");
    drawBoxBuilding(l, w, d, h, parcel.variant % 2 ? [82, 96, 91] : [93, 98, 89]);
    const roof = isoRect(l.x, l.y, w * 1.06, d * 1.08, h + .18);
    polygon(roof, parcel.variant % 3 === 0 ? "rgba(132,71,55,.98)" : "rgba(92,79,67,.98)");
    return;
  }
  if (parcel.type === "apartment") {
    drawLot(l, w, d, "residential");
    drawBoxBuilding(l, w, d, h, [72, 88, 96]);
    drawWindows(l, w, d, h);
    return;
  }
  if (parcel.type === "warehouse" || parcel.type === "factory") {
    drawLot(l, w, d, "industrial");
    drawBoxBuilding(l, w, d, h, parcel.variant % 2 ? [88, 87, 78] : [76, 83, 80]);
    if (parcel.type === "factory") {
      const chimney = { ...l, x: l.x + w * .28, y: l.y - d * .15 };
      drawBoxBuilding(chimney, .18, .18, h + .8, [66, 70, 68]);
    }
    return;
  }
  if (parcel.type === "shop") {
    drawLot(l, w, d, "urban");
    drawBoxBuilding(l, w, d, h, [105, 76, 69]);
    const front = isoPoint(l.x + w / 2, l.y, h * .45);
    ctx.fillStyle = "rgba(241,181,106,.74)";
    ctx.fillRect(front.x - 3, front.y - .8, 6, 1.6);
    return;
  }

  const palettes = parcel.type === "tower"
    ? [[61,82,104],[71,88,105],[68,79,97],[74,91,99]]
    : parcel.type === "campus" || parcel.type === "academic"
      ? [[81,86,113],[75,91,108],[89,91,105]]
      : [[74,88,98],[82,91,100],[72,92,92]];
  const rgb = palettes[parcel.variant % palettes.length];
  drawLot(l, w, d, "urban");
  drawBoxBuilding(l, w, d, h, rgb);
  drawWindows(l, w, d, h);
  if (parcel.type === "tower" && h > 4.5) {
    const crown = isoRect(l.x, l.y, w * .7, d * .68, h + .22);
    polygon(crown, rgba(shade(rgb, 1.18), .96), "rgba(218,235,236,.12)", .5);
  }
}

function drawEngineCity() {
  if (!layers.buildings || !snapshot) return;
  cityScene = cityEngine.build(snapshot);
  cityScene.parcels.forEach(drawEngineParcel);
}

function drawEngineVegetation() {
  if (!snapshot) return;
  cityScene = cityEngine.build(snapshot);
  cityScene.trees.forEach((tree) => drawTree(tree.x, tree.y, tree.size, tree.variant));
  (cityScene.shrubs || []).forEach(drawShrub);
  (cityScene.flowers || []).forEach(drawFlowerBed);
  cityScene.lamps.forEach((lamp) => drawLamp(lamp.x, lamp.y));
}

function drawBuildings() {
  [...snapshot.locations]
    .filter((l) => !String(l.id).startsWith("street-"))
    .sort((a, b) => (a.x + a.y) - (b.x + b.y))
    .forEach(drawBuilding);
}

// Real-world visual navigation. Citizens use the same geography as roads/buildings.
const worldAgentMotion = new Map();

function connectedLocations(locationId) {
  if (!snapshot?.roads) return [];
  const connected = [];
  snapshot.roads.forEach((road) => {
    if (road.source === locationId) connected.push(locationForId(road.target));
    else if (road.target === locationId) connected.push(locationForId(road.source));
  });
  return connected.filter(Boolean);
}

function entranceDistance(location) {
  if (!location) return 1.2;
  if (["government", "bank", "university", "hospital"].includes(location.type)) return 2.8;
  if (location.type === "workplace") return 2.15;
  if (location.type === "home") return 1.45;
  if (location.type === "station") return 1.65;
  return 1.35;
}

function worldEntrance(locationId, agentId = "") {
  const location = locationForId(locationId);
  if (!location) return { x: 50, y: 50 };
  const neighbors = connectedLocations(locationId);
  if (!neighbors.length || location.type === "park") return { x: location.x, y: location.y };
  const neighbor = neighbors[hashCode(`${locationId}:${agentId}`) % neighbors.length];
  const dx = neighbor.x - location.x;
  const dy = neighbor.y - location.y;
  const length = Math.hypot(dx, dy) || 1;
  const distance = entranceDistance(location);
  return {
    x: location.x + (dx / length) * distance,
    y: location.y + (dy / length) * distance,
  };
}

function worldAgentPoint(agent) {
  const target = worldEntrance(agent.location_id, agent.id);
  let state = worldAgentMotion.get(agent.id);
  if (!state) {
    state = {
      locationId: agent.location_id,
      from: target,
      to: target,
      startedAt: animationTime,
      duration: 1,
    };
    worldAgentMotion.set(agent.id, state);
  } else if (state.locationId !== agent.location_id) {
    const previous = worldEntrance(state.locationId, agent.id);
    state = {
      locationId: agent.location_id,
      from: previous,
      to: target,
      startedAt: animationTime,
      duration: 900,
    };
    worldAgentMotion.set(agent.id, state);
  }
  const t = clamp((animationTime - state.startedAt) / state.duration, 0, 1);
  const eased = t * t * (3 - 2 * t);
  return {
    x: state.from.x + (state.to.x - state.from.x) * eased,
    y: state.from.y + (state.to.y - state.from.y) * eased,
  };
}

const visualNavNodes = {
  northA: [.19, .20], northB: [.29, .27], northC: [.37, .31],
  westA: [.17, .43], westB: [.29, .48], westC: [.37, .47],
  centralA: [.39, .34], centralB: [.46, .40], centralC: [.52, .46],
  universityA: [.53, .18], universityB: [.59, .25], universityC: [.61, .32],
  riversideA: [.67, .33], riversideB: [.70, .41], riversideC: [.69, .49],
  commercialA: [.57, .49], commercialB: [.62, .55], commercialC: [.66, .61],
  industrialA: [.35, .58], industrialB: [.42, .63], industrialC: [.49, .68],
  civicA: [.52, .62], civicB: [.58, .68], civicC: [.64, .72],
};

const visualNavEdges = [
  ["northA", "northB"], ["northB", "northC"], ["northC", "centralA"],
  ["westA", "westB"], ["westB", "westC"], ["westC", "centralA"],
  ["centralA", "centralB"], ["centralB", "centralC"],
  ["centralB", "universityB"], ["universityA", "universityB"],
  ["universityB", "universityC"], ["universityC", "riversideA"],
  ["riversideA", "riversideB"], ["riversideB", "riversideC"],
  ["centralC", "commercialA"], ["commercialA", "commercialB"],
  ["commercialB", "commercialC"], ["commercialC", "civicC"],
  ["westC", "industrialA"], ["industrialA", "industrialB"],
  ["industrialB", "industrialC"], ["industrialC", "civicA"],
  ["civicA", "civicB"], ["civicB", "civicC"],
  ["centralC", "civicA"], ["commercialB", "civicB"],
];

const districtVisualNodes = {
  "res-north": ["northA", "northB", "northC"],
  "res-south": ["westA", "westB", "westC"],
  central: ["centralA", "centralB", "centralC"],
  university: ["universityA", "universityB", "universityC"],
  riverside: ["riversideA", "riversideB", "riversideC"],
  commercial: ["commercialA", "commercialB", "commercialC"],
  industrial: ["industrialA", "industrialB", "industrialC"],
  civic: ["civicA", "civicB", "civicC"],
};

const landmarkVisualNodes = {
  "city-hall": "civicA",
  "central-bank": "centralC",
  "university-main": "universityA",
  "city-hospital": "civicB",
  "market-square": "commercialB",
  "central-park": "centralB",
};

const agentMotion = new Map();

function navAdjacency() {
  const graph = new Map(Object.keys(visualNavNodes).map((key) => [key, []]));
  visualNavEdges.forEach(([a, b]) => {
    graph.get(a).push(b);
    graph.get(b).push(a);
  });
  return graph;
}
const visualGraph = navAdjacency();

function locationForId(locationId) {
  return snapshot?.locations?.find((location) => location.id === locationId) || null;
}

function visualNodeForLocation(locationId) {
  if (landmarkVisualNodes[locationId]) return landmarkVisualNodes[locationId];
  const location = locationForId(locationId);
  if (!location) return "centralB";
  const choices = districtVisualNodes[location.district_id] || ["centralB"];
  return choices[hashCode(location.id) % choices.length];
}

function safeVisualAnchor(locationId, agentId = "") {
  const nodeId = visualNodeForLocation(locationId);
  const base = visualNavNodes[nodeId] || visualNavNodes.centralB;
  const hash = hashCode(`${locationId}:${agentId}`);
  const offset = ((hash % 7) - 3) * .0016;
  const vertical = (((Math.floor(hash / 7)) % 5) - 2) * .0012;
  return { nodeId, x: base[0] + offset, y: base[1] + vertical };
}

function shortestVisualNodes(source, target) {
  if (source === target) return [source];
  const queue = [source];
  const previous = new Map([[source, null]]);
  while (queue.length) {
    const current = queue.shift();
    for (const next of visualGraph.get(current) || []) {
      if (previous.has(next)) continue;
      previous.set(next, current);
      if (next === target) {
        const path = [target];
        let cursor = current;
        while (cursor) {
          path.push(cursor);
          cursor = previous.get(cursor);
        }
        return path.reverse();
      }
      queue.push(next);
    }
  }
  return [source, target];
}

function routeForLocations(fromLocationId, toLocationId, agentId) {
  const from = safeVisualAnchor(fromLocationId, agentId);
  const to = safeVisualAnchor(toLocationId, agentId);
  const nodePath = shortestVisualNodes(from.nodeId, to.nodeId);
  const points = [{ x: from.x, y: from.y }];
  nodePath.slice(1, -1).forEach((nodeId) => {
    const [x, y] = visualNavNodes[nodeId];
    points.push({ x, y });
  });
  points.push({ x: to.x, y: to.y });
  return points;
}

function pointAlongRoute(points, progress) {
  if (points.length === 1) return points[0];
  const segments = [];
  let total = 0;
  for (let i = 0; i < points.length - 1; i += 1) {
    const a = points[i];
    const b = points[i + 1];
    const length = Math.hypot(b.x - a.x, b.y - a.y);
    segments.push({ a, b, length });
    total += length;
  }
  let remaining = clamp(progress, 0, 1) * total;
  for (const segment of segments) {
    if (remaining <= segment.length || segment === segments[segments.length - 1]) {
      const t = segment.length ? remaining / segment.length : 1;
      return {
        x: segment.a.x + (segment.b.x - segment.a.x) * clamp(t, 0, 1),
        y: segment.a.y + (segment.b.y - segment.a.y) * clamp(t, 0, 1),
      };
    }
    remaining -= segment.length;
  }
  return points[points.length - 1];
}

function normalizedAgentPoint(agent) {
  const target = safeVisualAnchor(agent.location_id, agent.id);
  let state = agentMotion.get(agent.id);
  if (!state) {
    state = {
      locationId: agent.location_id,
      route: [{ x: target.x, y: target.y }],
      startedAt: animationTime,
      duration: 1,
    };
    agentMotion.set(agent.id, state);
  } else if (state.locationId !== agent.location_id) {
    const current = pointAlongRoute(
      state.route,
      clamp((animationTime - state.startedAt) / state.duration, 0, 1),
    );
    const fromNode = visualNodeForLocation(state.locationId);
    const toNode = visualNodeForLocation(agent.location_id);
    const nodePath = shortestVisualNodes(fromNode, toNode);
    const route = [{ x: current.x, y: current.y }];
    nodePath.slice(1, -1).forEach((nodeId) => {
      const [x, y] = visualNavNodes[nodeId];
      route.push({ x, y });
    });
    route.push({ x: target.x, y: target.y });
    state = {
      locationId: agent.location_id,
      route,
      startedAt: animationTime,
      duration: Math.max(650, Math.min(1200, 520 + route.length * 145)),
    };
    agentMotion.set(agent.id, state);
  }
  const progress = clamp((animationTime - state.startedAt) / state.duration, 0, 1);
  return pointAlongRoute(state.route, progress);
}

function drawDensity(){
  if(!layers.density||!snapshot.density)return;
  ctx.save();ctx.globalCompositeOperation="screen";
  snapshot.density.forEach((entry)=>{
    if(entry.count<4)return;
    const anchor=safeVisualAnchor(entry.location_id,"density");
    const p=(USE_CINEMATIC_MAP && cinematicReady)?imagePoint(anchor.x,anchor.y):(()=>{const l=locationForId(entry.location_id);return l?isoPoint(l.x,l.y,.25):null;})();
    if(!p)return;
    const r=Math.min(42,6+Math.sqrt(entry.count)*2.25)*camera.zoom;
    const g=ctx.createRadialGradient(p.x,p.y,0,p.x,p.y,r);
    g.addColorStop(0,"rgba(255,122,81,.22)");g.addColorStop(.5,"rgba(236,73,77,.08)");g.addColorStop(1,"rgba(236,73,77,0)");
    ctx.fillStyle=g;ctx.beginPath();ctx.arc(p.x,p.y,r,0,Math.PI*2);ctx.fill();
  });ctx.restore();
}

function agentScreen(agent,index){
  if(USE_CINEMATIC_MAP && cinematicReady){
    const normalized=normalizedAgentPoint(agent);
    return imagePoint(normalized.x,normalized.y);
  }
  const world=worldAgentPoint(agent);
  const p=isoPoint(world.x,world.y,.32);
  const crowdX=((hashCode(agent.id)%7)-3)*.32;
  const crowdY=(((hashCode(agent.id+"y")%5)-2)*.22);
  return {
    x:p.x+crowdX,
    y:p.y+crowdY+Math.sin(animationTime*.004+index*.71)*.35,
  };
}
function drawPerson(agent,index){
  const p=agentScreen(agent,index); const sc=clamp(camera.zoom,.78,1.35);ctx.save();ctx.translate(p.x,p.y);ctx.globalAlpha=.94;
  ctx.fillStyle=agent.moving?"#f2c56d":"#94e0e2";ctx.beginPath();ctx.arc(0,-3.2*sc,1.15*sc,0,Math.PI*2);ctx.fill();ctx.strokeStyle=agent.moving?"#e7b75f":"#69bcc5";ctx.lineWidth=1.1*sc;ctx.lineCap="round";
  ctx.beginPath();ctx.moveTo(0,-1.9*sc);ctx.lineTo(0,2.1*sc);ctx.moveTo(0,-.8*sc);ctx.lineTo(-1.5*sc,.5*sc);ctx.moveTo(0,-.8*sc);ctx.lineTo(1.5*sc,.5*sc);ctx.moveTo(0,2*sc);ctx.lineTo(-1.2*sc,3.9*sc);ctx.moveTo(0,2*sc);ctx.lineTo(1.2*sc,3.9*sc);ctx.stroke();ctx.restore();
  if(selected===agent.id||hoverAgent===agent.id){ctx.save();ctx.strokeStyle=selected===agent.id?"#ff5965":"#7ce2e7";ctx.lineWidth=1.5;ctx.shadowColor=ctx.strokeStyle;ctx.shadowBlur=9;ctx.beginPath();ctx.arc(p.x,p.y-1,8+Math.sin(animationTime*.006)*1.1,0,Math.PI*2);ctx.stroke();ctx.shadowBlur=0;ctx.font="700 8px Segoe UI";ctx.textAlign="center";ctx.fillStyle="#eaf7f7";ctx.fillText(agent.name,p.x,p.y-13);ctx.restore();}
}
function selectedAgentForMap() {
  if (!selected || !selectedCitizen || !snapshot) return null;

  // If the selected citizen is already inside the regular rendered sample,
  // use that live agent directly.
  const sampledAgent = snapshot.agents.find(
    (agent) => agent.id === selected
  );

  if (sampledAgent) return sampledAgent;

  // The map intentionally renders only a small citizen sample for performance.
  // Build a temporary visual agent for a selected citizen that is outside
  // that sample so the user can still locate them on the map.
  const locationId = selectedCitizen.current_location_id;

  if (!locationId) return null;

  return {
    id: selectedCitizen.id,
    name: selectedCitizen.name,
    location_id: locationId,
    moving: Boolean(selectedCitizen.moving),
    action: selectedCitizen.action || "idle",
  };
}

function drawPeople() {
  if (!layers.people) return;

  snapshot.agents.forEach(drawPerson);

  const selectedAgent = selectedAgentForMap();

  if (
    selectedAgent &&
    !snapshot.agents.some((agent) => agent.id === selectedAgent.id)
  ) {
    drawPerson(selectedAgent, snapshot.agents.length);
  }
}

function drawTraffic(){
  if(!layers.traffic)return;
  if(USE_CINEMATIC_MAP && cinematicReady){
    const routes=[
      [[.06,.56],[.28,.46],[.51,.49],[.78,.38],[.96,.49]],
      [[.15,.78],[.36,.63],[.55,.66],[.77,.56],[.92,.72]],
      [[.22,.28],[.42,.38],[.63,.30],[.86,.22]],
      [[.38,.89],[.50,.74],[.67,.73],[.85,.84]],
    ];
    const count=26;
    for(let i=0;i<count;i+=1){
      const route=routes[i%routes.length];
      const phase=(animationTime*.000025*(1+(i%3)*.11)+i*.071)%1;
      const segFloat=phase*(route.length-1);
      const seg=Math.min(route.length-2,Math.floor(segFloat));
      const lt=segFloat-seg;
      const a=route[seg],b=route[seg+1];
      const normalizedX=a[0]+(b[0]-a[0])*lt;
      const normalizedY=a[1]+(b[1]-a[1])*lt;
      const p=imagePoint(normalizedX,normalizedY);
      const pa=imagePoint(a[0],a[1]);
      const pb=imagePoint(b[0],b[1]);
      const angle=Math.atan2(pb.y-pa.y,pb.x-pa.x);
      ctx.save();
      ctx.translate(p.x,p.y);
      ctx.rotate(angle);
      ctx.shadowBlur=5;
      ctx.shadowColor=i%4===0?"rgba(237,79,85,.55)":"rgba(229,206,137,.38)";
      ctx.fillStyle=i%4===0?"rgba(231,74,82,.92)":i%3===0?"rgba(223,191,111,.88)":"rgba(178,204,213,.82)";
      ctx.fillRect(-2.8,-1.2,5.6,2.4);
      ctx.fillStyle="rgba(242,249,248,.55)";
      ctx.fillRect(.8,-.8,1.3,1.6);
      ctx.restore();
    }
    return;
  }
  const roads=snapshot.roads;if(!roads.length)return;const count=Math.min(24,Math.max(12,roads.length));
  for(let i=0;i<count;i+=1){const r=roads[(i*7)%roads.length];let t=(animationTime*.000028*(1+(i%4)*.09)+i*.091)%1;if(i%2)t=1-t;const x=r.x1+(r.x2-r.x1)*t,y=r.y1+(r.y2-r.y1)*t,p=isoPoint(x,y,.16);const angle=Math.atan2((isoPoint(r.x2,r.y2).y-isoPoint(r.x1,r.y1).y),(isoPoint(r.x2,r.y2).x-isoPoint(r.x1,r.y1).x));ctx.save();ctx.translate(p.x,p.y);ctx.rotate(angle);ctx.fillStyle=i%5===0?"rgba(226,76,81,.9)":i%3===0?"rgba(213,183,102,.75)":"rgba(170,202,207,.68)";ctx.fillRect(-2.3,-1.1,4.6,2.2);ctx.fillStyle="rgba(221,241,243,.32)";ctx.fillRect(.5,-.8,1.2,1.6);ctx.restore();}
}

function drawAmbient(){
  if(USE_CINEMATIC_MAP && cinematicReady){
    const route=[[.18,.74],[.33,.63],[.48,.65],[.62,.57],[.70,.48]];
    const t=(animationTime*.000018)%1;
    const seg=(route.length-1)*t;
    const i=Math.min(route.length-2,Math.floor(seg));
    const local=seg-i;
    const a=route[i],b=route[i+1];
    const p=imagePoint(a[0]+(b[0]-a[0])*local,a[1]+(b[1]-a[1])*local);
    const pa=imagePoint(a[0],a[1]),pb=imagePoint(b[0],b[1]);
    const angle=Math.atan2(pb.y-pa.y,pb.x-pa.x);
    ctx.save();ctx.translate(p.x,p.y);ctx.rotate(angle);
    ctx.fillStyle="rgba(102,177,184,.82)";ctx.fillRect(-5,-1.5,10,3);
    ctx.fillStyle="rgba(225,240,240,.35)";ctx.fillRect(-3,-1,5,2);ctx.restore();
    return;
  }
  const route=[[18,72],[50,75],[79,75],[78,48],[49,46]];
  const t=(animationTime*.000018)%1;const seg=(route.length-1)*t;
  const i=Math.min(route.length-2,Math.floor(seg));const local=seg-i;
  const x=route[i][0]+(route[i+1][0]-route[i][0])*local;
  const y=route[i][1]+(route[i+1][1]-route[i][1])*local;
  const p=isoPoint(x,y,.2);ctx.save();ctx.translate(p.x,p.y);
  ctx.fillStyle="rgba(102,177,184,.82)";ctx.fillRect(-5,-1.5,10,3);
  ctx.fillStyle="rgba(225,240,240,.35)";ctx.fillRect(-3,-1,5,2);ctx.restore();
}


function drawLivingAtmosphere(){
  if(!snapshot)return;
  const light=worldLight();
  const river=riverPathPoints();
  // Animated water glints: purely visual and clipped conceptually to the river corridor.
  ctx.save();
  ctx.lineCap="round";
  for(let i=0;i<24;i+=1){
    const seg=i%(river.length-1);const a=river[seg],b=river[seg+1];
    const phase=(animationTime*.000035+i*.137)%1;
    const x=a[0]+(b[0]-a[0])*phase;const y=a[1]+(b[1]-a[1])*phase;
    const p=isoPoint(x,y,.04);const shimmer=3+(i%4)*1.2;
    ctx.strokeStyle=`rgba(128,207,218,${.08+.08*Math.sin(animationTime*.002+i)})`;
    ctx.lineWidth=.8;ctx.beginPath();ctx.moveTo(p.x-shimmer,p.y);ctx.lineTo(p.x+shimmer,p.y-1);ctx.stroke();
  }
  ctx.restore();

  // Warm window/lamp bloom at dawn and night gives the city depth in video.
  if(light.h<8 || light.h>17){
    ctx.save();ctx.globalCompositeOperation="screen";
    (cityScene?.lamps||[]).filter((_,i)=>i%3===0).forEach((lamp,i)=>{
      const p=isoPoint(lamp.x,lamp.y,.72);const r=5+(i%3)*1.5;
      const g=ctx.createRadialGradient(p.x,p.y,0,p.x,p.y,r);
      g.addColorStop(0,"rgba(255,213,123,.18)");g.addColorStop(1,"rgba(255,190,90,0)");
      ctx.fillStyle=g;ctx.beginPath();ctx.arc(p.x,p.y,r,0,Math.PI*2);ctx.fill();
    });
    ctx.restore();
  }

  // Subtle animated canopy highlights keep green areas from looking flat.
  if(camera.zoom>.68){
    ctx.save();ctx.globalAlpha=.12;
    (cityScene?.trees||[]).filter((_,i)=>i%9===0).forEach((tree,i)=>{
      const p=isoPoint(tree.x,tree.y,1.1*tree.size);const sway=Math.sin(animationTime*.0012+i*.8)*1.2;
      ctx.fillStyle="rgba(132,194,112,.55)";ctx.beginPath();ctx.arc(p.x+sway,p.y-1,1.2,0,Math.PI*2);ctx.fill();
    });ctx.restore();
  }
}

function drawCityDetails() {
  if (!snapshot || camera.zoom < .58) return;
  snapshot.districts.forEach((d) => {
    // Civic/commercial hardscape.
    if (["central", "commercial", "civic", "education"].includes(d.kind)) {
      const plaza = isoRect(d.x + d.width * .18, d.y - d.height * .18, d.width * .16, d.height * .12, .055);
      polygon(plaza, "rgba(132,139,128,.14)", "rgba(186,194,177,.09)", .5);
      for (let i = 0; i < 4; i += 1) {
        const p = isoPoint(d.x + d.width * (.08 + i * .055), d.y - d.height * .23, .09);
        ctx.fillStyle = i % 2 ? "rgba(204,111,80,.58)" : "rgba(112,153,164,.52)";
        ctx.fillRect(p.x - 2.2, p.y - 1.1, 4.4, 2.2);
      }
    }

    // Parking lots for commercial, industrial and university districts.
    if (["commercial", "industrial", "education"].includes(d.kind)) {
      const lot = isoRect(d.x - d.width * .28, d.y + d.height * .27, d.width * .18, d.height * .16, .05);
      polygon(lot, "rgba(52,59,58,.54)", "rgba(144,153,144,.10)", .5);
      for (let i = 0; i < 6; i += 1) {
        const p = isoPoint(
          d.x - d.width * .34 + (i % 3) * d.width * .055,
          d.y + d.height * .24 + Math.floor(i / 3) * d.height * .055,
          .08,
        );
        ctx.fillStyle = i % 3 === 0 ? "rgba(198,76,79,.72)" : "rgba(157,181,187,.58)";
        ctx.fillRect(p.x - 2.1, p.y - .9, 4.2, 1.8);
      }
    }
  });
}

function drawCinematicOverlayCards() {
  if (!USE_CINEMATIC_MAP || !cinematicReady) return;
  const w = canvas.clientWidth;
  const h = canvas.clientHeight;

  if (layers.economy) {
    const cards = [
      { x: .61, y: .33, title: "Genesis Bank", sub: "Finance & Economy" },
      { x: .48, y: .58, title: "Central Business District", sub: "40 active businesses" },
    ];
    cards.forEach((card) => {
      const x = card.x * w;
      const y = card.y * h;
      ctx.save();
      ctx.fillStyle = "rgba(6,17,25,.88)";
      ctx.strokeStyle = "rgba(60,104,121,.55)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.roundRect(x - 68, y - 20, 136, 40, 7);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = "#e8f3f6";
      ctx.font = "700 9px Segoe UI";
      ctx.textAlign = "center";
      ctx.fillText(card.title, x, y - 2);
      ctx.fillStyle = "#6f8b97";
      ctx.font = "7px Segoe UI";
      ctx.fillText(card.sub, x, y + 11);
      ctx.restore();
    });
  }

  if (layers.services) {
    const services = [
      { x: .22, y: .61, label: "Hospital", color: "#ef5963" },
      { x: .53, y: .17, label: "University", color: "#9b91ff" },
      { x: .39, y: .34, label: "City Hall", color: "#e6d5a4" },
      { x: .75, y: .68, label: "Riverside Park", color: "#70d499" },
    ];
    services.forEach((item) => {
      const x = item.x * w;
      const y = item.y * h;
      ctx.save();
      ctx.shadowColor = item.color;
      ctx.shadowBlur = 10;
      ctx.fillStyle = item.color;
      ctx.beginPath();
      ctx.arc(x, y, 4, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;
      ctx.fillStyle = "rgba(5,14,21,.9)";
      ctx.fillRect(x + 7, y - 9, 72, 18);
      ctx.fillStyle = "#e9f4f6";
      ctx.font = "700 7px Segoe UI";
      ctx.textAlign = "left";
      ctx.fillText(item.label, x + 12, y + 2);
      ctx.restore();
    });
  }
}

function rebuildStatic(){
  if(!snapshot)return;
  ctx=staticCtx;
  ctx.clearRect(0,0,canvas.clientWidth,canvas.clientHeight);
  const cinematic = USE_CINEMATIC_MAP && drawCinematicBackground();
  if (!cinematic) {
    drawBackground();
    drawDistricts();
    drawRoads();
    drawEngineGreenGround();
    drawEngineCity();
    drawEngineVegetation();
    drawStreetFurniture();
    drawBuildings();
    drawCityDetails();
  }
  drawCinematicOverlayCards();
  ctx=screenCtx;
  staticDirty=false;
}
function draw(){
  if(!snapshot)return;
  // During camera drag we reuse the already rendered city bitmap and translate it.
  // Rebuilding hundreds of buildings/trees on every pointermove was the main source
  // of panning stalls. The authoritative camera is committed once on pointerup.
  if(!camera.dragging && staticDirty)rebuildStatic();
  screenCtx.save();
  screenCtx.setTransform(1,0,0,1,0,0);
  screenCtx.fillStyle = "#050b10";
  screenCtx.fillRect(0,0,canvas.width,canvas.height);
  screenCtx.drawImage(staticCanvas,0,0);
  screenCtx.restore();
  screenCtx.setTransform(pixelRatio,0,0,pixelRatio,0,0);
  ctx=screenCtx;
  // Dynamic atmosphere/agents are intentionally frozen while dragging. This keeps
  // interaction responsive and resumes the live scene immediately after release.
  if(camera.dragging)return;
  drawLivingAtmosphere();drawDensity();drawTraffic();drawAmbient();drawPeople();
}
function animate(time){
  if(document.hidden){requestAnimationFrame(animate);return;}
  // While panning, the browser compositor moves the existing canvas texture.
  // We deliberately do zero canvas drawing here; this is much cheaper than
  // copying a full-screen bitmap on every drag frame.
  if(camera.dragging){requestAnimationFrame(animate);return;}
  const frameBudget = live || selected ? TARGET_FRAME_MS : IDLE_FRAME_MS;
  if(time-lastFrame>=frameBudget){
    const renderStart = performance.now();
    animationTime=time;
    draw();
    const renderMs = performance.now() - renderStart;
    renderAverage = renderAverage ? renderAverage * .9 + renderMs * .1 : renderMs;
    fpsFrames += 1;
    if (time - fpsWindowStart >= 1000) {
      const fps = Math.round((fpsFrames * 1000) / (time - fpsWindowStart));
      const fpsEl = document.getElementById("perfFps");
      const renderEl = document.getElementById("perfRender");
      const wsEl = document.getElementById("perfWs");
      if (fpsEl) fpsEl.textContent = String(fps);
      if (renderEl) renderEl.textContent = `${renderAverage.toFixed(1)} ms`;
      if (wsEl) {
        wsEl.textContent = lastSocketMessage ? `${Math.max(0, Math.round(performance.now() - lastSocketMessage))} ms` : "—";
      }
      fpsFrames = 0;
      fpsWindowStart = time;
    }
    lastFrame=time;
  }
  requestAnimationFrame(animate);
}

function formatNumber(v){return Number(v||0).toLocaleString();}
function renderMetrics(){
  const s=snapshot.summary;const unemployment=Number(s.unemployment_rate||0)*100;const civ=s.living_civilization||{};const autonomous=s.autonomous_world||{};const items=[["Population",formatNumber(s.population)],["Agents",formatNumber(autonomous.agents||0)],["Businesses",formatNumber(s.businesses)],["Unemployment",`${unemployment.toFixed(1)}%`],["Development",`${Math.round(Number(civ.development_level||0)*100)}%`],["Emergence",`${Math.round(Number(autonomous.emergence_index||0)*100)}%`],["HITL Pending",formatNumber(autonomous.pending_human_reviews||0)],["World tick",formatNumber(s.tick)]];
  document.getElementById("metrics").innerHTML=items.map(([l,v])=>`<div class="metric"><b>${v}</b><span>${l}</span></div>`).join("");
  document.getElementById("worldTime").textContent=`${s.time.toUpperCase()} • TICK ${s.tick}`;document.getElementById("overlayPopulation").textContent=formatNumber(s.population);document.getElementById("cinemaTime").textContent=s.time.toUpperCase();document.title=`RedWorld AI — ${s.time}`;
}
async function loadCitizens() {
  const response = await fetch("/api/v1/world/citizens?limit=2000");
  const data = await response.json();
  citizens = data.items;
  renderCitizenOptions(citizens);
}
function renderCitizenOptions(list){const el=document.getElementById("citizenSelect");el.innerHTML='<option value="">Select a citizen...</option>'+list.map(c=>`<option value="${c.id}">${c.name} — ${c.occupation}</option>`).join("");}
function focusCitizenOnMap(agent) {
  if (!agent || !snapshot) return;

  // Give the selected citizen enough visual space without zooming in too far.
  if (camera.zoom < 1.28) {
    camera.zoom = 1.28;
  }

  // Calculate the citizen position using the same renderer used by the map.
  const point = agentScreen(agent, snapshot.agents.length);

  // Move the citizen close to the center of the visible map.
  camera.x += canvas.clientWidth * 0.5 - point.x;
  camera.y += canvas.clientHeight * 0.48 - point.y;

  staticDirty = true;
}

async function showCitizen(id) {
  selected = id || null;
  selectedCitizen = null;

  document.getElementById("citizenSelect").value = id || "";

  const detail = document.getElementById("citizenDetail");

  if (!id) {
    detail.className = "citizen empty-state";
    detail.innerHTML =
      "Select a citizen to follow their life in the city.";
    return;
  }

  const response = await fetch(`/api/v1/world/citizens/${id}`);

  if (!response.ok) {
    selected = null;
    selectedCitizen = null;

    detail.className = "citizen empty-state";
    detail.innerHTML =
      "Citizen data is no longer available. Refresh the viewer and try again.";

    await loadCitizens();
    return;
  }

  const c = await response.json();

  selectedCitizen = c;

  detail.className = "citizen";

  detail.innerHTML = `
    <span class="agent-tag">AUTONOMOUS CITIZEN</span>
    <strong>${c.name}</strong><br>
    ${c.occupation}

    <div class="citizen-grid">
      <div class="citizen-stat">
        <small>Age</small>
        <b>${c.age}</b>
      </div>

      <div class="citizen-stat">
        <small>Cash</small>
        <b>${c.cash} RWC</b>
      </div>

      <div class="citizen-stat">
        <small>Action</small>
        <b>${c.action || "idle"}</b>
      </div>

      <div class="citizen-stat">
        <small>Location</small>
        <b>${c.current_location || "—"}</b>
      </div>

      <div class="citizen-stat">
        <small>Hunger</small>
        <b>${Math.round((c.needs?.hunger || 0) * 100)}%</b>
      </div>

      <div class="citizen-stat">
        <small>Energy Need</small>
        <b>${Math.round((c.needs?.energy || 0) * 100)}%</b>
      </div>

      <div class="citizen-stat">
        <small>Social Need</small>
        <b>${Math.round((c.needs?.social || 0) * 100)}%</b>
      </div>

      <div class="citizen-stat">
        <small>Relations</small>
        <b>${c.relationships || 0}</b>
      </div>
    </div>

    <div class="citizen-life">
      <small>HUMAN DEVELOPMENT</small>
      <div>
        Stage: ${c.life?.life_stage?.replaceAll("_", " ") || "—"} ·
        Education ${Math.round((c.life?.education || 0) * 100)}% ·
        Skill ${Math.round((c.life?.skill || 0) * 100)}% ·
        Career ${Math.round((c.life?.career_progress || 0) * 100)}%
      </div>
      <div>
        Happiness ${Math.round((c.life?.happiness || 0) * 100)}% ·
        Health ${Math.round((c.life?.physical_health || 0) * 100)}% ·
        Mental ${Math.round((c.life?.mental_health || 0) * 100)}% ·
        Burnout risk ${Math.round((c.life?.burnout_risk || 0) * 100)}%
      </div>
      <div>
        Belonging ${Math.round((c.life?.belonging || 0) * 100)}% ·
        Civic ${Math.round((c.life?.civic_engagement || 0) * 100)}% ·
        Influence ${Math.round((c.life?.community_influence || 0) * 100)}%
      </div>

      <small>AUTONOMOUS AGENT</small>
      <div>
        Autonomy ${Math.round((c.autonomous_agent?.autonomy || 0) * 100)}% ·
        Decisions ${c.autonomous_agent?.decisions || 0} ·
        Plan ${c.autonomous_agent?.plan?.goal_key?.replaceAll("_", " ") || "forming"}
      </div>

      <small>GOALS</small>
      <div>
        ${
          (c.goals || [])
            .map(
              (goal) =>
                `${goal.type.replaceAll("_", " ")} ${Math.round(
                  goal.progress * 100
                )}%`
            )
            .join(" · ") || "—"
        }
      </div>

      <small>LIFE HISTORY</small>
      <div>
        ${
          (c.life?.history || [])
            .slice(-3)
            .map((event) => `${event.year}: ${event.summary}`)
            .join(" · ") || "Life history is still unfolding"
        }
      </div>

      <small>RECENT MEMORY</small>
      <div>
        ${
          (c.memories || [])
            .slice(-2)
            .map((memory) => memory.summary)
            .join(" · ") || "No significant memory yet"
        }
      </div>
    </div>
  `;

  const selectedAgent = selectedAgentForMap();

  if (selectedAgent) {
    focusCitizenOnMap(selectedAgent);
  }
}

async function loadEvents(){const response=await fetch("/api/v1/world/events?limit=14");const data=await response.json();renderEvents(data.items);}
async function loadAutonomy(){
  const response=await fetch("/api/v1/world/autonomy");
  const data=await response.json();
  document.getElementById("reviewCount").textContent=String(data.pending_human_reviews||0);
  document.getElementById("autonomyStatus").innerHTML=`<div><small>Agents</small><b>${formatNumber(data.agents)}</b></div><div><small>Emergence</small><b>${Math.round((data.emergence_index||0)*100)}%</b></div><div><small>Learning</small><b>${Math.round((data.learning_index||0)*100)}%</b></div>`;
  const queue=document.getElementById("reviewQueue");
  const items=data.pending_reviews||[];
  queue.innerHTML=items.length?items.map(r=>`<div class="review-card"><span class="risk">${r.risk_level.toUpperCase()} · ${(r.risk_score*100).toFixed(0)}%</span><b>${r.agent_name} → ${r.intent.replaceAll("_"," ")}</b><p>${r.expected_impact}</p><div class="review-actions"><button class="approve" data-review="${r.id}" data-decision="approved">APPROVE</button><button class="modify" data-review="${r.id}" data-decision="modified">MODIFY</button><button class="reject" data-review="${r.id}" data-decision="rejected">REJECT</button></div></div>`).join(""):'<div class="empty-state">No high-risk actions waiting for review.</div>';
  queue.querySelectorAll("button[data-review]").forEach(button=>{button.onclick=async()=>{const id=button.dataset.review;const decision=button.dataset.decision;await fetch(`/api/v1/world/autonomy/reviews/${id}?decision=${decision}`,{method:"POST"});await loadAutonomy();await refresh();};});
}
async function refresh(){const response=await fetch("/api/v1/world/map?render_sample=120");snapshot=await response.json();cityEngine.invalidate();cityScene=null;staticDirty=true;renderMetrics();loadEvents();loadAutonomy();}
async function stepWorld(){await fetch("/api/v1/world/step?steps=1",{method:"POST"});await refresh();}

document.getElementById("stepBtn").onclick=stepWorld;document.getElementById("citizenSelect").onchange=(e)=>showCitizen(e.target.value);document.getElementById("search").oninput=(e)=>{const q=e.target.value.toLowerCase();renderCitizenOptions(citizens.filter(c=>`${c.name} ${c.occupation}`.toLowerCase().includes(q)));};
function renderEvents(items){document.getElementById("eventCount").textContent=items.length;const events=[...items].reverse();document.getElementById("events").innerHTML=events.length?events.map(e=>`<div class="event"><span class="tick">T${e.tick}</span><b>${e.name}</b><small>World event recorded</small></div>`).join(""):'<div class="empty-state">No events yet.</div>';}
document.getElementById("liveBtn").onclick=()=>{live=!live;const button=document.getElementById("liveBtn");button.classList.toggle("live",live);button.textContent=live?"■ PAUSE":"▶ LIVE";if(live){socket=new WebSocket(`${location.protocol==="https:"?"wss":"ws"}://${location.host}/api/v1/world/live`);socket.onmessage=(event)=>{lastSocketMessage=performance.now();const update=JSON.parse(event.data);const oldMinute=snapshot?.summary?.minute_of_day;snapshot={...snapshot,...update,districts:snapshot.districts,locations:snapshot.locations,roads:snapshot.roads};if(oldMinute!==snapshot.summary.minute_of_day)staticDirty=true;renderMetrics();if(update.events)renderEvents(update.events);};socket.onclose=()=>{socket=null;if(live){live=false;button.classList.remove("live");button.textContent="▶ LIVE";}};}else if(socket){socket.close();socket=null;}};
document.getElementById("cinemaBtn").onclick=()=>{document.body.classList.toggle("cinema");const b=document.getElementById("cinemaBtn");b.textContent=document.body.classList.contains("cinema")?"▣ EXIT CINEMA":"▣ CINEMA";setTimeout(resize,180);};
document.querySelectorAll(".layer").forEach((button) => {
  button.onclick = () => {
    const layer = button.dataset.layer;
    layers[layer] = !layers[layer];
    button.classList.toggle("active", layers[layer]);
    if (["buildings", "economy", "services"].includes(layer)) staticDirty = true;
  };
});
function setZoom(next,ax=canvas.clientWidth/2,ay=canvas.clientHeight/2){const old=camera.zoom;camera.zoom=clamp(next,.55,1.9);const ratio=camera.zoom/old;camera.x=ax-(ax-camera.x)*ratio;camera.y=ay-(ay-camera.y)*ratio;staticDirty=true;}
document.getElementById("zoomIn").onclick=()=>setZoom(camera.zoom*1.12);document.getElementById("zoomOut").onclick=()=>setZoom(camera.zoom/1.12);document.getElementById("resetView").onclick=()=>{Object.assign(camera,{zoom:1,x:0,y:0});staticDirty=true;};
canvas.addEventListener("wheel",(e)=>{e.preventDefault();const r=canvas.getBoundingClientRect();setZoom(camera.zoom*(e.deltaY<0?1.08:1/1.08),e.clientX-r.left,e.clientY-r.top);},{passive:false});
canvas.addEventListener("pointerdown",(e)=>{
  camera.dragging=true;
  panStartX=e.clientX;panStartY=e.clientY;
  panBaseCameraX=camera.x;panBaseCameraY=camera.y;
  panPreviewX=0;panPreviewY=0;
  canvas.classList.add("dragging");
  canvas.setPointerCapture(e.pointerId);
});
canvas.addEventListener("pointermove",(e)=>{
  if(camera.dragging){
    panPreviewX=e.clientX-panStartX;
    panPreviewY=e.clientY-panStartY;
    if(!panTransformRaf){
      panTransformRaf=requestAnimationFrame(()=>{
        canvas.style.transform=`translate3d(${panPreviewX}px, ${panPreviewY}px, 0)`;
        panTransformRaf=0;
      });
    }
    return;
  }
  if(!snapshot||hoverRaf)return;
  const clientX=e.clientX,clientY=e.clientY;
  hoverRaf=requestAnimationFrame(()=>{
    hoverRaf=0;
    const rect=canvas.getBoundingClientRect(),mx=clientX-rect.left,my=clientY-rect.top;
    let best=null,bestD=14;
    snapshot.agents.forEach((a,i)=>{const p=agentScreen(a,i);const d=Math.hypot(p.x-mx,p.y-my);if(d<bestD){bestD=d;best=a;}});
    hoverAgent=best?.id||null;canvas.style.cursor=best?"pointer":"grab";
  });
});
function commitPan(){
  if(!camera.dragging)return;
  camera.x=panBaseCameraX+panPreviewX;
  camera.y=panBaseCameraY+panPreviewY;
  panPreviewX=0;panPreviewY=0;
  camera.dragging=false;
  canvas.style.transform="translate3d(0,0,0)";
  staticDirty=true;
  canvas.classList.remove("dragging");
}
canvas.addEventListener("pointerup",(e)=>{commitPan();try{canvas.releasePointerCapture(e.pointerId);}catch(_){/*noop*/}});
canvas.addEventListener("pointercancel",()=>{commitPan();});
canvas.addEventListener("pointerleave",()=>{if(camera.dragging)commitPan();hoverAgent=null;canvas.classList.remove("dragging");});
canvas.addEventListener("click",(e)=>{if(!snapshot)return;const rect=canvas.getBoundingClientRect(),mx=e.clientX-rect.left,my=e.clientY-rect.top;let best=null,bestD=13;snapshot.agents.forEach((a,i)=>{const p=agentScreen(a,i);const d=Math.hypot(p.x-mx,p.y-my);if(d<bestD){bestD=d;best=a;}});if(best)showCitizen(best.id);});

(async function init(){resize();await Promise.all([refresh(),loadCitizens()]);requestAnimationFrame(animate);})();
