import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { PLYLoader } from "three/addons/loaders/PLYLoader.js";

const canvas = document.querySelector("#sceneCanvas");
const fpvCanvas = document.querySelector("#fpvCanvas");
const speedMetric = document.querySelector("#speedMetric");
const heightMetric = document.querySelector("#heightMetric");
const hitMetric = document.querySelector("#hitMetric");
const assetMetric = document.querySelector("#assetMetric");
const modeChip = document.querySelector("#modeChip");
const toast = document.querySelector("#toast");

const REAL_ASSETS = {
  pointCloudUrl: "./assets/3dgs_iter30000_clean_filtered_xyzrgb.ply",
  colliderUrl: "./assets/true_3dgs_cloudcompare_poisson_depth8_trim8_mesh_faces40000.glb",
};

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: "high-performance" });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setClearColor(0x070a0d, 1);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const fpvRenderer = new THREE.WebGLRenderer({ canvas: fpvCanvas, antialias: true, alpha: true });
fpvRenderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
fpvRenderer.outputColorSpace = THREE.SRGBColorSpace;

const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0x070a0d, 14, 44);

const camera = new THREE.PerspectiveCamera(58, window.innerWidth / window.innerHeight, 0.05, 120);
camera.position.set(8.5, 7.2, 9.5);

const fpvCamera = new THREE.PerspectiveCamera(76, 16 / 9, 0.05, 60);

const controls = new OrbitControls(camera, canvas);
controls.target.set(0, 1.3, 0);
controls.enableDamping = true;
controls.maxPolarAngle = Math.PI * 0.49;
controls.minDistance = 4;
controls.maxDistance = 26;

const hemi = new THREE.HemisphereLight(0x9ff3ed, 0x18231f, 1.08);
scene.add(hemi);

const sun = new THREE.DirectionalLight(0xffefd0, 1.92);
sun.position.set(5, 9, 4);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
scene.add(sun);

const fill = new THREE.PointLight(0x58d7c9, 1.1, 18);
fill.position.set(-5, 3, -5);
scene.add(fill);

const visualLayer = new THREE.Group();
visualLayer.name = "visual-splat-layer";
scene.add(visualLayer);

const proceduralLayer = new THREE.Group();
proceduralLayer.name = "procedural-fallback-layer";
visualLayer.add(proceduralLayer);

const realVisualLayer = new THREE.Group();
realVisualLayer.name = "real-3dgs-point-cloud-layer";
visualLayer.add(realVisualLayer);

const colliderLayer = new THREE.Group();
colliderLayer.name = "mesh-collider-proxy-layer";
scene.add(colliderLayer);

const proceduralColliderLayer = new THREE.Group();
proceduralColliderLayer.name = "procedural-collider-layer";
colliderLayer.add(proceduralColliderLayer);

const realColliderLayer = new THREE.Group();
realColliderLayer.name = "real-mesh-collider-layer";
colliderLayer.add(realColliderLayer);

const markerLayer = new THREE.Group();
scene.add(markerLayer);

const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
const keys = new Set();
const heldDrive = new Set();
const clock = new THREE.Clock();

const actor = {
  radius: 0.24,
  height: 0.58,
  position: new THREE.Vector3(-2.8, 0.35, 2.6),
  velocity: new THREE.Vector3(),
  yaw: -0.6,
  speed: 2.55,
};

const state = {
  showVisual: true,
  showCollider: false,
  semanticTint: false,
  useRealAssets: true,
  realVisualReady: false,
  realColliderReady: false,
  realAssetError: "",
  lastHit: "none",
};

const colliderObjects = [];
const realColliderObjects = [];
const proceduralColliderObjects = [];
const obstacles = [];
let floorCollider;
let realColliderRoot = null;
let realPointCount = 0;
let realTriangleCount = 0;
let realBounds = null;
let realTransform = {
  center: new THREE.Vector3(1.6495707035064697, 3.6022610664367676, 6.305891513824463),
  scale: 0.5044801873791451,
};
const baseVisualOpacity = 0.92;

const roomBounds = {
  minX: -5.2,
  maxX: 5.2,
  minZ: -4.5,
  maxZ: 4.5,
};

function makeMat(color, options = {}) {
  return new THREE.MeshStandardMaterial({
    color,
    roughness: 0.84,
    metalness: 0.02,
    ...options,
  });
}

function makeWireMat(color, opacity = 0.34) {
  return new THREE.MeshBasicMaterial({
    color,
    wireframe: true,
    transparent: true,
    opacity,
    depthWrite: false,
  });
}

function formatCount(value) {
  return Intl.NumberFormat("en-US", { notation: value > 999999 ? "compact" : "standard" }).format(value);
}

function setRealAssetError(error) {
  console.warn("Real visual/collider asset failed to load.", error);
  state.realAssetError = error?.message || String(error);
  state.useRealAssets = false;
  setLayerVisibility();
  showToast("真实 PLY/GLB 加载失败，已切回 procedural fallback。");
}

function fitObjectToDemoSpace(object, sourceBox) {
  const box = sourceBox.clone();
  const size = new THREE.Vector3();
  const center = new THREE.Vector3();
  box.getSize(size);
  box.getCenter(center);
  const scale = 8.8 / Math.max(size.x, size.y, size.z);
  object.position.set(-center.x * scale, -center.y * scale, -center.z * scale);
  object.scale.setScalar(scale);
  object.updateMatrixWorld(true);
  realTransform = { center, scale };
  realBounds = new THREE.Box3().setFromObject(object);
}

function applyRealTransform(object) {
  object.position.set(
    -realTransform.center.x * realTransform.scale,
    -realTransform.center.y * realTransform.scale,
    -realTransform.center.z * realTransform.scale
  );
  object.scale.setScalar(realTransform.scale);
  object.updateMatrixWorld(true);
  realBounds = new THREE.Box3().setFromObject(object);
}

function registerCollider(mesh, label, collection = colliderObjects) {
  mesh.userData.colliderLabel = label;
  collection.push(mesh);
  if (!colliderObjects.includes(mesh)) colliderObjects.push(mesh);
}

function activeColliderObjects() {
  return state.useRealAssets && state.realColliderReady ? realColliderObjects : proceduralColliderObjects;
}

function activeModeName() {
  return state.useRealAssets && state.realVisualReady && state.realColliderReady ? "Real PLY + GLB"
    : state.useRealAssets && !state.realAssetError ? "Loading real assets"
    : "Procedural fallback";
}

function updateAssetMetric() {
  if (state.realVisualReady && state.realColliderReady) {
    assetMetric.textContent = `${formatCount(realPointCount)} / ${formatCount(realTriangleCount)}`;
    return;
  }
  assetMetric.textContent = state.realAssetError ? "fallback" : "loading";
}

function updateDebugPanel() {
  updateAssetMetric();
  const mode = activeModeName();
  modeChip.textContent = `${mode} · ${state.showCollider ? "collider visible" : "collider hidden but active"} · raycast ignores visual points`;
}

function realGroundProbe(pos) {
  if (!state.realColliderReady || !realBounds) return null;
  const origin = new THREE.Vector3(pos.x, realBounds.max.y + 2, pos.z);
  raycaster.set(origin, new THREE.Vector3(0, -1, 0));
  raycaster.far = Math.max(16, realBounds.max.y - realBounds.min.y + 4);
  const hits = raycaster.intersectObjects(realColliderObjects, false);
  raycaster.far = Infinity;
  return hits.find((hit) => {
    const normal = hit.face?.normal.clone() || new THREE.Vector3(0, 1, 0);
    normal.transformDirection(hit.object.matrixWorld);
    return normal.y > 0.18;
  }) || null;
}

function realForwardBlock(delta) {
  if (!state.realColliderReady || delta.lengthSq() === 0) return null;
  const dir = delta.clone().setY(0);
  if (dir.lengthSq() === 0) return null;
  dir.normalize();
  const probeDistance = actor.radius + delta.length() + 0.12;
  const heights = [0.38, 0.72, 1.05];
  for (const height of heights) {
    raycaster.set(actor.position.clone().add(new THREE.Vector3(0, height, 0)), dir);
    raycaster.far = probeDistance;
    const hits = raycaster.intersectObjects(realColliderObjects, false);
    for (const hit of hits) {
      const normal = hit.face?.normal.clone() || new THREE.Vector3(0, 1, 0);
      normal.transformDirection(hit.object.matrixWorld);
      if (normal.y < 0.45) {
        raycaster.far = Infinity;
        return hit;
      }
    }
  }
  raycaster.far = Infinity;
  return null;
}

function resetActorOnRealMesh() {
  const candidates = [
    new THREE.Vector3(-2.8, 0, 2.6),
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(-1.8, 0, 1.1),
    new THREE.Vector3(1.4, 0, -0.8),
    new THREE.Vector3(2.6, 0, 1.8),
    new THREE.Vector3(-3.2, 0, -1.6),
  ];
  for (const candidate of candidates) {
    const hit = realGroundProbe(candidate);
    if (hit) {
      actor.position.set(candidate.x, hit.point.y + 0.05, candidate.z);
      actor.velocity.set(0, 0, 0);
      actor.yaw = -0.6;
      return true;
    }
  }
  return false;
}

function placeActorAtCurrentSpawn() {
  if (!(state.useRealAssets && state.realColliderReady && resetActorOnRealMesh())) {
    actor.position.set(-2.8, 0.35, 2.6);
  }
  actor.velocity.set(0, 0, 0);
  actor.yaw = -0.6;
}

const floorShape = [
  new THREE.Vector2(-5.4, -4.7),
  new THREE.Vector2(5.4, -4.7),
  new THREE.Vector2(5.4, 4.7),
  new THREE.Vector2(1.3, 4.7),
  new THREE.Vector2(1.3, 2.3),
  new THREE.Vector2(-1.3, 2.3),
  new THREE.Vector2(-1.3, 4.7),
  new THREE.Vector2(-5.4, 4.7),
];

function buildFloorCollider() {
  const shape = new THREE.Shape(floorShape);
  const geometry = new THREE.ShapeGeometry(shape);
  geometry.rotateX(-Math.PI / 2);
  geometry.computeVertexNormals();
  const material = makeWireMat(0xefb35f, 0.42);
  const mesh = new THREE.Mesh(geometry, material);
  mesh.name = "floor collider mesh";
  mesh.visible = state.showCollider;
  proceduralColliderLayer.add(mesh);
  registerCollider(mesh, "floor", proceduralColliderObjects);
  floorCollider = mesh;

  const visualFloor = new THREE.Mesh(
    geometry.clone(),
    makeMat(0x1a2422, { transparent: true, opacity: 0.28 })
  );
  visualFloor.name = "visual shadow floor";
  visualFloor.position.y = -0.012;
  proceduralLayer.add(visualFloor);
}

function addObstacle({ name, position, size, color, semantic }) {
  const colliderGeo = new THREE.BoxGeometry(size.x, size.y, size.z);
  const colliderMesh = new THREE.Mesh(colliderGeo, makeWireMat(0xefb35f, 0.48));
  colliderMesh.position.copy(position);
  colliderMesh.name = `${name} collider`;
  colliderMesh.userData.semantic = semantic;
  colliderMesh.visible = state.showCollider;
  proceduralColliderLayer.add(colliderMesh);
  registerCollider(colliderMesh, name, proceduralColliderObjects);

  const obstacle = {
    name,
    center: position.clone(),
    half: new THREE.Vector3(size.x / 2, size.y / 2, size.z / 2),
    semantic,
  };
  obstacles.push(obstacle);

  const visualGeo = new THREE.BoxGeometry(size.x * 0.98, size.y * 0.98, size.z * 0.98, 3, 3, 3);
  const visualMat = makeMat(color, { transparent: true, opacity: 0.24 });
  const visualMesh = new THREE.Mesh(visualGeo, visualMat);
  visualMesh.position.copy(position);
  visualMesh.name = `${name} translucent visual proxy`;
  proceduralLayer.add(visualMesh);

  addSplatCluster(position, size, color, semantic);
}

function seededNoise(seed) {
  let t = seed + 0x6d2b79f5;
  return () => {
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function addSplatCluster(center, size, color, semantic) {
  const rand = seededNoise(Math.floor((center.x + 9) * 1000 + (center.z + 7) * 2000));
  const count = Math.max(260, Math.round(size.x * size.y * size.z * 360));
  const positions = new Float32Array(count * 3);
  const colors = new Float32Array(count * 3);
  const base = new THREE.Color(color);
  const semanticColor = semantic === "furniture" ? new THREE.Color(0x58d7c9)
    : semantic === "structure" ? new THREE.Color(0xefb35f)
    : new THREE.Color(0xafb6ff);

  for (let i = 0; i < count; i += 1) {
    const px = (rand() - 0.5) * size.x;
    const py = (rand() - 0.5) * size.y;
    const pz = (rand() - 0.5) * size.z;
    const surfaceBias = rand();
    positions[i * 3] = center.x + px * (surfaceBias > 0.5 ? 1 : 0.9);
    positions[i * 3 + 1] = center.y + py;
    positions[i * 3 + 2] = center.z + pz * (surfaceBias > 0.5 ? 1 : 0.9);
    const c = state.semanticTint ? semanticColor : base.clone().lerp(new THREE.Color(0xffffff), rand() * 0.28);
    colors[i * 3] = c.r;
    colors[i * 3 + 1] = c.g;
    colors[i * 3 + 2] = c.b;
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  const material = new THREE.PointsMaterial({
    size: 0.05,
    vertexColors: true,
    transparent: true,
    opacity: 0.88,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  });
  const points = new THREE.Points(geometry, material);
  points.name = `${semantic} visual gaussian proxies`;
  points.userData.baseColor = color;
  points.userData.semantic = semantic;
  points.raycast = () => {};
  proceduralLayer.add(points);
}

function addWallVisuals() {
  const wallSpecs = [
    { name: "back wall", position: new THREE.Vector3(0, 1.35, -4.72), size: new THREE.Vector3(10.8, 2.7, 0.16) },
    { name: "left wall", position: new THREE.Vector3(-5.48, 1.35, 0), size: new THREE.Vector3(0.16, 2.7, 9.4) },
    { name: "right wall", position: new THREE.Vector3(5.48, 1.35, 0), size: new THREE.Vector3(0.16, 2.7, 9.4) },
  ];
  wallSpecs.forEach((spec) => addObstacle({
    ...spec,
    color: 0x72827e,
    semantic: "structure",
  }));
}

function buildActor() {
  const group = new THREE.Group();
  group.name = "kinematic actor";

  const body = new THREE.Mesh(
    new THREE.CapsuleGeometry(actor.radius, actor.height, 6, 10),
    makeMat(0x58d7c9, { emissive: 0x0d3835, emissiveIntensity: 0.55 })
  );
  body.position.y = actor.radius + actor.height / 2;
  body.castShadow = true;
  group.add(body);

  const sensor = new THREE.Mesh(
    new THREE.BoxGeometry(0.28, 0.16, 0.08),
    makeMat(0xefb35f, { emissive: 0x523000, emissiveIntensity: 0.4 })
  );
  sensor.position.set(0, actor.radius + actor.height + 0.06, -0.22);
  group.add(sensor);

  scene.add(group);
  actor.group = group;
}

function buildScene() {
  buildFloorCollider();
  addWallVisuals();
  addObstacle({
    name: "table",
    position: new THREE.Vector3(-1.35, 0.58, -0.72),
    size: new THREE.Vector3(1.8, 1.05, 1.1),
    color: 0xa98252,
    semantic: "furniture",
  });
  addObstacle({
    name: "chair",
    position: new THREE.Vector3(1.64, 0.46, 0.72),
    size: new THREE.Vector3(0.9, 0.92, 0.86),
    color: 0x688c8a,
    semantic: "furniture",
  });
  addObstacle({
    name: "cabinet",
    position: new THREE.Vector3(3.62, 0.92, -2.6),
    size: new THREE.Vector3(1.18, 1.84, 0.62),
    color: 0x6d7386,
    semantic: "furniture",
  });
  addObstacle({
    name: "sofa",
    position: new THREE.Vector3(-3.55, 0.55, 1.62),
    size: new THREE.Vector3(1.82, 1.1, 0.9),
    color: 0x8a687b,
    semantic: "furniture",
  });

  const grid = new THREE.GridHelper(12, 24, 0x203230, 0x14201d);
  grid.position.y = 0.005;
  scene.add(grid);

  buildActor();
}

async function loadRealPointCloud() {
  const loader = new PLYLoader();
  const geometry = await loader.loadAsync(REAL_ASSETS.pointCloudUrl);
  geometry.computeBoundingBox();
  const sourceBox = geometry.boundingBox.clone();
  realPointCount = geometry.getAttribute("position")?.count || 0;

  if (!geometry.getAttribute("color")) {
    const count = geometry.getAttribute("position").count;
    const colors = new Float32Array(count * 3);
    const color = new THREE.Color(0x58d7c9);
    for (let i = 0; i < count; i += 1) {
      colors[i * 3] = color.r;
      colors[i * 3 + 1] = color.g;
      colors[i * 3 + 2] = color.b;
    }
    geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  }

  const material = new THREE.PointsMaterial({
    size: 0.018,
    vertexColors: true,
    transparent: true,
    opacity: 0.92,
    depthWrite: false,
  });
  const points = new THREE.Points(geometry, material);
  points.name = "real 3dgs centers from PLY";
  points.userData.semantic = "real-ply";
  points.userData.preserveVertexColors = true;
  points.raycast = () => {};
  fitObjectToDemoSpace(points, sourceBox);
  realVisualLayer.add(points);
  state.realVisualReady = true;
  setLayerVisibility();
}

async function loadRealCollider() {
  const loader = new GLTFLoader();
  const gltf = await loader.loadAsync(REAL_ASSETS.colliderUrl);
  const root = gltf.scene;
  root.name = "real 3dgs poisson mesh collider";
  applyRealTransform(root);
  realColliderRoot = root;
  realTriangleCount = 0;

  const shadedMaterial = makeMat(0x31423d, {
    transparent: true,
    opacity: 0.24,
    side: THREE.DoubleSide,
  });
  const wireMaterial = makeWireMat(0xefb35f, 0.5);
  root.traverse((child) => {
    if (!(child instanceof THREE.Mesh)) return;
    const sourceMaterial = child.material;
    if (Array.isArray(sourceMaterial)) sourceMaterial.forEach((material) => material?.dispose?.());
    else sourceMaterial?.dispose?.();
    child.geometry.computeVertexNormals();
    child.material = shadedMaterial;
    child.castShadow = false;
    child.receiveShadow = true;
    child.userData.colliderLabel = "true-3dgs-poisson-mesh";
    child.visible = state.showCollider;
    registerCollider(child, "true-3dgs-poisson-mesh", realColliderObjects);
    const positionCount = child.geometry.getAttribute("position")?.count || 0;
    realTriangleCount += child.geometry.index ? child.geometry.index.count / 3 : positionCount / 3;

    const wire = new THREE.LineSegments(
      new THREE.WireframeGeometry(child.geometry),
      wireMaterial.clone()
    );
    wire.name = `${child.name || "mesh"} collider wire overlay`;
    wire.visible = state.showCollider;
    wire.raycast = () => {};
    child.add(wire);
  });

  realColliderLayer.add(root);
  state.realColliderReady = true;
  resetActorOnRealMesh();
  setLayerVisibility();
}

async function loadRealAssets() {
  updateDebugPanel();
  try {
    await loadRealPointCloud();
    await loadRealCollider();
    setLayerVisibility();
    showToast("Loaded real PLY visual layer + GLB collider mesh.");
  } catch (error) {
    setRealAssetError(error);
  }
}

function updateVisualColors() {
  visualLayer.traverse((child) => {
    if (!(child instanceof THREE.Points)) return;
    if (child.userData.preserveVertexColors) return;
    const colors = child.geometry.getAttribute("color");
    const base = new THREE.Color(child.userData.baseColor || 0xffffff);
    const semantic = child.userData.semantic;
    const semanticColor = semantic === "furniture" ? new THREE.Color(0x58d7c9)
      : semantic === "structure" ? new THREE.Color(0xefb35f)
      : new THREE.Color(0xafb6ff);
    for (let i = 0; i < colors.count; i += 1) {
      const c = state.semanticTint ? semanticColor : base;
      colors.setXYZ(i, c.r, c.g, c.b);
    }
    colors.needsUpdate = true;
  });
}

function isInsideFloor(pos) {
  if (pos.x < roomBounds.minX || pos.x > roomBounds.maxX || pos.z < roomBounds.minZ || pos.z > roomBounds.maxZ) return false;
  const inBackPocket = Math.abs(pos.x) < 1.18 && pos.z > 2.28;
  return !inBackPocket;
}

function intersectsObstacle(pos, radius) {
  for (const obstacle of obstacles) {
    if (obstacle.name.includes("wall")) continue;
    const minX = obstacle.center.x - obstacle.half.x - radius;
    const maxX = obstacle.center.x + obstacle.half.x + radius;
    const minZ = obstacle.center.z - obstacle.half.z - radius;
    const maxZ = obstacle.center.z + obstacle.half.z + radius;
    const verticalClear = actor.position.y <= obstacle.center.y + obstacle.half.y + 0.4;
    if (verticalClear && pos.x > minX && pos.x < maxX && pos.z > minZ && pos.z < maxZ) {
      return obstacle.name;
    }
  }
  return "";
}

function groundHeightAt(pos) {
  if (!isInsideFloor(pos)) return actor.position.y;
  return 0.35 + 0.05 * Math.sin(pos.x * 1.6) * Math.cos(pos.z * 1.4);
}

function tryMove(delta) {
  const next = actor.position.clone().add(delta);
  if (state.useRealAssets && state.realColliderReady) {
    const block = realForwardBlock(delta);
    if (block) {
      showToast("Blocked by real GLB collider mesh.");
      return false;
    }
    const ground = realGroundProbe(next);
    if (!ground) {
      showToast("No walkable face under actor in real collider mesh.");
      return false;
    }
    next.y = ground.point.y + 0.05;
    actor.position.copy(next);
    return true;
  }

  const hit = intersectsObstacle(next, actor.radius);
  if (!isInsideFloor(next) || hit) {
    if (hit) showToast(`Blocked by mesh collider: ${hit}`);
    return false;
  }
  next.y = groundHeightAt(next);
  actor.position.copy(next);
  return true;
}

function updateActor(dt) {
  const forward = new THREE.Vector3(Math.sin(actor.yaw), 0, Math.cos(actor.yaw));
  const right = new THREE.Vector3(forward.z, 0, -forward.x);
  const move = new THREE.Vector3();
  const turn = 1.9 * dt;

  if (keys.has("KeyQ") || keys.has("ArrowLeft") || heldDrive.has("turn-left")) actor.yaw += turn;
  if (keys.has("KeyE") || keys.has("ArrowRight") || heldDrive.has("turn-right")) actor.yaw -= turn;
  if (keys.has("KeyW") || keys.has("ArrowUp") || heldDrive.has("forward")) move.add(forward);
  if (keys.has("KeyS") || keys.has("ArrowDown") || heldDrive.has("backward")) move.sub(forward);
  if (keys.has("KeyA") || heldDrive.has("left")) move.sub(right);
  if (keys.has("KeyD") || heldDrive.has("right")) move.add(right);

  if (move.lengthSq() > 0) {
    move.normalize().multiplyScalar(actor.speed * dt);
    const moved = tryMove(move);
    actor.velocity.copy(moved ? move.clone().divideScalar(Math.max(dt, 0.001)) : new THREE.Vector3());
  } else {
    actor.velocity.multiplyScalar(0.82);
  }

  actor.group.position.copy(actor.position);
  actor.group.rotation.y = actor.yaw;
  speedMetric.textContent = actor.velocity.length().toFixed(1);
  heightMetric.textContent = actor.position.y.toFixed(2);
}

function updateCameras() {
  const actorHead = actor.position.clone().add(new THREE.Vector3(0, 1.08, 0));
  const lookDir = new THREE.Vector3(Math.sin(actor.yaw), -0.08, Math.cos(actor.yaw)).normalize();
  fpvCamera.position.copy(actorHead).addScaledVector(lookDir, 0.22);
  fpvCamera.lookAt(actorHead.clone().add(lookDir.multiplyScalar(4)));
}

function resize() {
  const width = window.innerWidth;
  const height = window.innerHeight;
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();

  const fpvRect = fpvCanvas.getBoundingClientRect();
  const fpvWidth = Math.max(1, Math.floor(fpvRect.width));
  const fpvHeight = Math.max(1, Math.floor(fpvRect.height));
  fpvRenderer.setSize(fpvWidth, fpvHeight, false);
  fpvCamera.aspect = fpvWidth / fpvHeight;
  fpvCamera.updateProjectionMatrix();
}

function setLayerVisibility() {
  visualLayer.visible = state.showVisual;
  realVisualLayer.visible = state.showVisual && state.useRealAssets && state.realVisualReady;
  proceduralLayer.visible = state.showVisual && (!state.useRealAssets || !state.realVisualReady);
  realVisualLayer.traverse((child) => {
    if (child instanceof THREE.Points) child.material.opacity = state.showCollider ? 0.46 : baseVisualOpacity;
  });
  realColliderLayer.traverse((child) => {
    if (child instanceof THREE.Mesh || child instanceof THREE.LineSegments) {
      child.visible = state.showCollider && state.useRealAssets && state.realColliderReady;
    }
  });
  proceduralColliderLayer.traverse((child) => {
    if (child instanceof THREE.Mesh || child instanceof THREE.LineSegments) {
      child.visible = state.showCollider && (!state.useRealAssets || !state.realColliderReady);
    }
  });
  document.querySelector("#toggleAssets").classList.toggle("is-active", state.useRealAssets);
  document.querySelector("#toggleVisual").classList.toggle("is-active", state.showVisual);
  document.querySelector("#toggleCollider").classList.toggle("is-active", state.showCollider);
  document.querySelector("#toggleSemantic").classList.toggle("is-active", state.semanticTint);
  updateDebugPanel();
}

function markHit(point, normal) {
  markerLayer.clear();
  const marker = new THREE.Mesh(
    new THREE.SphereGeometry(0.08, 16, 16),
    makeMat(0xff806d, { emissive: 0x6b1109, emissiveIntensity: 0.8 })
  );
  marker.position.copy(point);
  markerLayer.add(marker);

  const normalLine = new THREE.ArrowHelper(normal, point, 0.48, 0xff806d, 0.14, 0.08);
  markerLayer.add(normalLine);
}

function onPointerDown(event) {
  const rect = canvas.getBoundingClientRect();
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  const hits = raycaster.intersectObjects(activeColliderObjects(), false);
  if (!hits.length) {
    state.lastHit = "none";
    hitMetric.textContent = "none";
    showToast("No collider hit. Visual splats are ignored by raycast.");
    return;
  }
  const hit = hits[0];
  const label = hit.object.userData.colliderLabel || hit.object.name || "collider";
  const normal = hit.face?.normal.clone() || new THREE.Vector3(0, 1, 0);
  normal.transformDirection(hit.object.matrixWorld);
  markHit(hit.point, normal);
  state.lastHit = label;
  hitMetric.textContent = label;
  showToast(`Ray hit mesh collider: ${label}`);
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => toast.classList.remove("show"), 1700);
}

function resetActor() {
  placeActorAtCurrentSpawn();
  markerLayer.clear();
  hitMetric.textContent = "none";
  showToast("Actor reset on the collider mesh floor.");
}

function animate() {
  const dt = Math.min(clock.getDelta(), 0.04);
  updateActor(dt);
  updateCameras();
  controls.update();

  const pulse = 0.78 + Math.sin(clock.elapsedTime * 2.2) * 0.08;
  proceduralLayer.traverse((child) => {
    if (child instanceof THREE.Points) child.material.opacity = pulse;
  });

  renderer.render(scene, camera);
  fpvRenderer.render(scene, fpvCamera);
  requestAnimationFrame(animate);
}

function bindEvents() {
  window.addEventListener("resize", resize);
  window.addEventListener("keydown", (event) => {
    keys.add(event.code);
    if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Space"].includes(event.code)) event.preventDefault();
  });
  window.addEventListener("keyup", (event) => keys.delete(event.code));
  canvas.addEventListener("pointerdown", onPointerDown);

  document.querySelector("#toggleVisual").addEventListener("click", () => {
    state.showVisual = !state.showVisual;
    setLayerVisibility();
  });
  document.querySelector("#toggleAssets").addEventListener("click", () => {
    if (!state.realVisualReady || !state.realColliderReady) {
      showToast("Real PLY/GLB assets are still loading; using fallback until ready.");
      return;
    }
    state.useRealAssets = !state.useRealAssets;
    markerLayer.clear();
    hitMetric.textContent = "none";
    placeActorAtCurrentSpawn();
    setLayerVisibility();
    showToast(state.useRealAssets ? "Using real PLY visual + GLB collider." : "Using procedural fallback scene.");
  });
  document.querySelector("#toggleCollider").addEventListener("click", () => {
    state.showCollider = !state.showCollider;
    setLayerVisibility();
  });
  document.querySelector("#toggleSemantic").addEventListener("click", () => {
    state.semanticTint = !state.semanticTint;
    updateVisualColors();
    setLayerVisibility();
  });
  document.querySelector("#resetActor").addEventListener("click", resetActor);

  document.querySelectorAll("[data-drive]").forEach((button) => {
    const drive = button.dataset.drive;
    button.addEventListener("pointerdown", () => heldDrive.add(drive));
    button.addEventListener("pointerup", () => heldDrive.delete(drive));
    button.addEventListener("pointerleave", () => heldDrive.delete(drive));
    button.addEventListener("pointercancel", () => heldDrive.delete(drive));
  });
}

buildScene();
bindEvents();
resize();
setLayerVisibility();
loadRealAssets();
showToast("Loading real PLY visual layer + GLB collider mesh...");
animate();
