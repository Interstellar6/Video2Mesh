import * as THREE from "three";
import { SplatMesh, SparkRenderer } from "@sparkjsdev/spark";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { DRACOLoader } from "three/addons/loaders/DRACOLoader.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { PLYLoader } from "three/addons/loaders/PLYLoader.js";

const canvas = document.querySelector("#sceneCanvas");
const fpvCanvas = document.querySelector("#fpvCanvas");
const speedMetric = document.querySelector("#speedMetric");
const heightMetric = document.querySelector("#heightMetric");
const hitMetric = document.querySelector("#hitMetric");
const surfaceMetric = document.querySelector("#surfaceMetric");
const assetMetric = document.querySelector("#assetMetric");
const modeChip = document.querySelector("#modeChip");
const toast = document.querySelector("#toast");

const DEMO_ASSET_VERSION = "bedroom4-cli30k-spark-20260703";
const LARGE_ASSET_MANIFEST_URL = `./assets/large-asset-manifest.json?v=${DEMO_ASSET_VERSION}`;
const BEDROOM4_LAYER_ROTATION = { x: 0, y: 0, z: Math.PI };
const BEDROOM4_CLI30K_ROBUST_BOUNDS = {
  min: [-13.553831520080566, -13.723336820602418, -2.7017650175094603],
  max: [18.185760917663574, 7.111933832168579, 24.271147446632385],
};
const PLY_VISUAL_ASSETS = [
  {
    id: "bedroom_4_dense100",
    label: "Bedroom 4 cleaned XYZRGB PLY fallback",
    format: "ply",
    visualUrl: `./assets/bedroom_4_scene_3dgs_repaired_point_cloud_clean.ply?v=${DEMO_ASSET_VERSION}`,
    colliderUrl: `./assets/bedroom_4_colmap_delaunay_collider.glb?v=${DEMO_ASSET_VERSION}`,
    cleanupReportUrl: `./assets/bedroom_4_scene_3dgs_repaired_point_cloud_clean.outlier_clean_report.json?v=${DEMO_ASSET_VERSION}`,
    pointCount: 872374,
    rawPointCount: 874472,
    removedOutliers: 2098,
    pointSize: 0.016,
    colliderLabel: "bedroom-4-colmap-delaunay-collider",
    layerRotation: BEDROOM4_LAYER_ROTATION,
  },
];
const SPARK_VISUAL_ASSETS = [
  {
    id: "bedroom_4_cli30k_graphdeco_clean_ply",
    label: "Bedroom 4 CLI30K GraphDECO clean Gaussian PLY",
    format: "graphdeco-ply",
    visualUrl: `./assets/bedroom_4_cli30k_graphdeco_clean_iteration30000.ply?v=${DEMO_ASSET_VERSION}`,
    colliderUrl: `./assets/bedroom_4_cli30k_colmap_delaunay_dense_collider.glb?v=${DEMO_ASSET_VERSION}`,
    splatCount: 971305,
    rawSplatCount: 1348957,
    removedOutliers: 377652,
    robustBounds: BEDROOM4_CLI30K_ROBUST_BOUNDS,
    lod: false,
    timeoutMs: 180000,
    colliderLabel: "bedroom-4-cli30k-colmap-delaunay-dense-collider",
    layerRotation: BEDROOM4_LAYER_ROTATION,
    primary: true,
  },
  {
    id: "bedroom_4_graphdeco_supersplat_ply",
    label: "Bedroom 4 repaired GraphDECO Gaussian PLY fallback",
    format: "graphdeco-ply",
    visualUrl: `./assets/bedroom_4_scene_3dgs_repaired_supersplat.ply?v=${DEMO_ASSET_VERSION}`,
    colliderUrl: `./assets/bedroom_4_colmap_delaunay_collider.glb?v=${DEMO_ASSET_VERSION}`,
    splatCount: 874472,
    lod: false,
    timeoutMs: 120000,
    colliderLabel: "bedroom-4-colmap-delaunay-collider",
    layerRotation: BEDROOM4_LAYER_ROTATION,
  },
  {
    id: "azureovo_outdoor_splat",
    label: "Spark .splat",
    format: "splat",
    visualUrl: `./assets/azureovo_outdoor.splat?v=${DEMO_ASSET_VERSION}`,
    colliderUrl: `./assets/azureovo_outdoor_collider.glb?v=${DEMO_ASSET_VERSION}`,
    splatCount: 1200000,
    splatRotation: { x: 0, y: 0, z: Math.PI },
    lod: false,
    timeoutMs: 45000,
    colliderLabel: "outdoor-splat-collider-mesh",
  },
  {
    id: "azureovo_sog",
    label: "Spark .sog",
    format: "sog",
    visualUrl: `./assets/azureovo_3dgs.sog?v=${DEMO_ASSET_VERSION}`,
    colliderUrl: `./assets/azureovo_3dgs_collider.glb?v=${DEMO_ASSET_VERSION}`,
    splatCount: 688687,
    splatRotation: { x: -Math.PI / 2, y: 0, z: 0 },
    lod: true,
    timeoutMs: 60000,
    colliderLabel: "sog-3dgs-collider-mesh",
  },
];
const REAL_ASSETS = {
  plyFallbackUrl: "./assets/3dgs_iter30000_clean_filtered_xyzrgb.ply?v=real-assets-20260702",
  poissonFallbackUrl: "./assets/true_3dgs_cloudcompare_poisson_depth8_trim8_mesh_faces40000.glb?v=real-assets-20260702",
};
const COLLIDER_RENDER_MODES = ["wire", "solid", "hidden"];
const COLLIDER_RENDER_MODE_LABELS = {
  wire: "wire + xray",
  solid: "solid",
  hidden: "hidden but active",
};
const SPLAT_QUALITY_ORDER = ["balanced", "crisp", "fast"];
const SPLAT_QUALITY_PRESETS = {
  balanced: {
    label: "Balanced",
    maxStdDev: Math.sqrt(8),
    minAlpha: 0.5 * (1 / 255),
    minPixelRadius: 0,
    maxPixelRadius: 512,
    falloff: 1,
    preBlurAmount: 0,
    blurAmount: 0.3,
    clipXY: 1.4,
    focalAdjustment: 1,
  },
  crisp: {
    label: "Crisp",
    maxStdDev: 2.35,
    minAlpha: 0.75 * (1 / 255),
    minPixelRadius: 0,
    maxPixelRadius: 420,
    falloff: 1,
    preBlurAmount: 0,
    blurAmount: 0.12,
    clipXY: 1.25,
    focalAdjustment: 1,
  },
  fast: {
    label: "Fast",
    maxStdDev: 2.05,
    minAlpha: 1.4 * (1 / 255),
    minPixelRadius: 0.15,
    maxPixelRadius: 220,
    falloff: 0.88,
    preBlurAmount: 0,
    blurAmount: 0.08,
    clipXY: 1.08,
    focalAdjustment: 0.95,
  },
};

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: "high-performance" });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setClearColor(0x070a0d, 1);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const sparkRenderer = new SparkRenderer({
  renderer,
  enableLod: true,
});

const fpvRenderer = new THREE.WebGLRenderer({ canvas: fpvCanvas, antialias: true, alpha: true });
fpvRenderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
fpvRenderer.outputColorSpace = THREE.SRGBColorSpace;

const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0x070a0d, 14, 44);
sparkRenderer.name = "spark-3dgs-renderer";
scene.add(sparkRenderer);

const camera = new THREE.PerspectiveCamera(58, window.innerWidth / window.innerHeight, 0.05, 120);
camera.position.set(8.5, 7.2, 9.5);

const fpvCamera = new THREE.PerspectiveCamera(76, 16 / 9, 0.05, 60);

const controls = new OrbitControls(camera, canvas);
controls.target.set(0, 1.3, 0);
controls.enableDamping = true;
controls.minPolarAngle = 0;
controls.maxPolarAngle = Math.PI;
controls.minDistance = 0.5;
controls.maxDistance = 40;
controls.enablePan = true;

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
const dracoLoader = new DRACOLoader();
dracoLoader.setDecoderPath("https://www.gstatic.com/draco/versioned/decoders/1.5.7/");

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
  colliderRenderMode: "wire",
  semanticTint: false,
  useRealAssets: true,
  cameraMode: "orbit",
  splatQuality: "balanced",
  realVisualReady: false,
  realColliderReady: false,
  realAssetError: "",
  lastHit: "none",
  lastHitInfo: null,
};

const colliderObjects = [];
const realColliderObjects = [];
const proceduralColliderObjects = [];
const obstacles = [];
let floorCollider;
let realColliderRoot = null;
let sparkSplatMesh = null;
let activeVisualAsset = null;
let realVisualSource = "Bedroom 4 3DGS PLY";
let realVisualFormat = "ply";
let realVisualUrl = "";
let realColliderUrl = "";
let realVisualUsesSpark = false;
let realVisualAssetId = "";
let realPointCount = 0;
let realRawPointCount = 0;
let realRemovedOutliers = 0;
let realTriangleCount = 0;
let realBounds = null;
let realFrameBounds = null;
let pointerDown = null;
let largeAssetManifestPromise = null;
const largeAssetBytesCache = new Map();
let realTransform = {
  sourceBox: new THREE.Box3(
    new THREE.Vector3(-8.86639881, -6.50972795, -3.324754),
    new THREE.Vector3(10.8637476, 13.88053226, 17.47151756)
  ),
  scale: 0.5044801873791451,
  rotation: BEDROOM4_LAYER_ROTATION,
  offset: new THREE.Vector3(),
};
const baseVisualOpacity = 0.92;
let hasAutoFramedRealAsset = false;

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

function colliderIsVisible() {
  return state.colliderRenderMode !== "hidden";
}

function nextValue(values, current) {
  const index = Math.max(0, values.indexOf(current));
  return values[(index + 1) % values.length];
}

function formatVec3(vector) {
  if (!vector) return "none";
  return `${vector.x.toFixed(2)}, ${vector.y.toFixed(2)}, ${vector.z.toFixed(2)}`;
}

function surfaceRoleFromUserData(userData = {}) {
  const roles = [];
  if (userData.walkable) roles.push("walkable");
  if (userData.characterCollision) roles.push("character");
  if (userData.cameraCollision) roles.push("camera");
  return roles.join(" / ") || "untagged";
}

function resetRealVisualStats() {
  realPointCount = 0;
  realRawPointCount = 0;
  realRemovedOutliers = 0;
}

function robustPointCloudBounds(geometry, lowerQuantile = 0.001, upperQuantile = 0.999, paddingRatio = 0.02) {
  const position = geometry.getAttribute("position");
  if (!position || position.count === 0) return geometry.boundingBox?.clone() || new THREE.Box3();
  const axes = [[], [], []];
  for (let i = 0; i < position.count; i += 1) {
    axes[0].push(position.getX(i));
    axes[1].push(position.getY(i));
    axes[2].push(position.getZ(i));
  }
  const quantile = (values, q) => {
    values.sort((a, b) => a - b);
    const pos = THREE.MathUtils.clamp(q, 0, 1) * (values.length - 1);
    const lo = Math.floor(pos);
    const hi = Math.min(values.length - 1, lo + 1);
    const frac = pos - lo;
    return values[lo] * (1 - frac) + values[hi] * frac;
  };
  const lower = [];
  const upper = [];
  for (const values of axes) {
    const low = quantile(values, lowerQuantile);
    const high = quantile(values, upperQuantile);
    const extent = Math.max(high - low, 1e-6);
    lower.push(low - extent * paddingRatio);
    upper.push(high + extent * paddingRatio);
  }
  return new THREE.Box3(
    new THREE.Vector3(lower[0], lower[1], lower[2]),
    new THREE.Vector3(upper[0], upper[1], upper[2])
  );
}

function robustSplatBounds(splat, lowerQuantile = 0.001, upperQuantile = 0.999, paddingRatio = 0.02) {
  const axes = [[], [], []];
  splat.forEachSplat((_index, center) => {
    axes[0].push(center.x);
    axes[1].push(center.y);
    axes[2].push(center.z);
  });
  if (!axes[0].length) return splat.getBoundingBox(true);
  const quantile = (values, q) => {
    values.sort((a, b) => a - b);
    const pos = THREE.MathUtils.clamp(q, 0, 1) * (values.length - 1);
    const lo = Math.floor(pos);
    const hi = Math.min(values.length - 1, lo + 1);
    const frac = pos - lo;
    return values[lo] * (1 - frac) + values[hi] * frac;
  };
  const lower = [];
  const upper = [];
  for (const values of axes) {
    const low = quantile(values, lowerQuantile);
    const high = quantile(values, upperQuantile);
    const extent = Math.max(high - low, 1e-6);
    lower.push(low - extent * paddingRatio);
    upper.push(high + extent * paddingRatio);
  }
  return new THREE.Box3(
    new THREE.Vector3(lower[0], lower[1], lower[2]),
    new THREE.Vector3(upper[0], upper[1], upper[2])
  );
}

function boxFromArrayBounds(bounds) {
  if (!bounds?.min || !bounds?.max) return null;
  return new THREE.Box3(
    new THREE.Vector3(bounds.min[0], bounds.min[1], bounds.min[2]),
    new THREE.Vector3(bounds.max[0], bounds.max[1], bounds.max[2])
  );
}

function setRealAssetError(error) {
  console.warn("Real Spark visual/collider assets failed to load.", error);
  state.realAssetError = error?.message || String(error);
  state.useRealAssets = false;
  setLayerVisibility();
  showToast("真实 Spark 3DGS / GLB 全部加载失败，已切回 procedural fallback。");
}

function applyRealLayerTransform() {
  for (const layer of [realVisualLayer, realColliderLayer]) {
    layer.rotation.set(
      realTransform.rotation?.x || 0,
      realTransform.rotation?.y || 0,
      realTransform.rotation?.z || 0
    );
    layer.scale.setScalar(realTransform.scale);
    layer.position.copy(realTransform.offset);
    layer.updateMatrixWorld(true);
  }
}

function fitRealLayersToDemoSpace(sourceBox, asset = activeVisualAsset) {
  const rotation = asset?.layerRotation || { x: 0, y: 0, z: 0 };
  const rotationMatrix = new THREE.Matrix4().makeRotationFromEuler(
    new THREE.Euler(rotation.x || 0, rotation.y || 0, rotation.z || 0)
  );
  const box = transformedBox(sourceBox.clone(), rotationMatrix);
  const size = new THREE.Vector3();
  const center = new THREE.Vector3();
  box.getSize(size);
  box.getCenter(center);
  const scale = 8.8 / Math.max(size.x, size.y, size.z);
  const offset = new THREE.Vector3(
    -center.x * scale,
    -box.min.y * scale,
    -center.z * scale
  );
  realTransform = { sourceBox: sourceBox.clone(), scale, rotation, offset };
  applyRealLayerTransform();
  realBounds = new THREE.Box3().setFromObject(realColliderLayer);
  realFrameBounds = transformedBox(sourceBox.clone(), realVisualLayer.matrixWorld);
  frameCameraToRealBounds(false);
}

function applyRealTransform(object) {
  object.position.set(0, 0, 0);
  object.scale.setScalar(1);
  object.updateMatrixWorld(true);
  applyRealLayerTransform();
  realBounds = new THREE.Box3().setFromObject(realColliderLayer);
  frameCameraToRealBounds(false);
}

function transformedBox(box, matrix) {
  const points = [];
  for (const x of [box.min.x, box.max.x]) {
    for (const y of [box.min.y, box.max.y]) {
      for (const z of [box.min.z, box.max.z]) {
        points.push(new THREE.Vector3(x, y, z).applyMatrix4(matrix));
      }
    }
  }
  return new THREE.Box3().setFromPoints(points);
}

function withTimeout(promise, timeoutMs, label) {
  let timer = null;
  const timeout = new Promise((_, reject) => {
    timer = window.setTimeout(() => reject(new Error(`${label} timed out after ${timeoutMs}ms`)), timeoutMs);
  });
  return Promise.race([promise, timeout]).finally(() => window.clearTimeout(timer));
}

async function getLargeAssetManifest() {
  if (!largeAssetManifestPromise) {
    largeAssetManifestPromise = fetch(LARGE_ASSET_MANIFEST_URL)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Large asset manifest failed: ${response.status} ${response.statusText}`);
        }
        return response.json();
      })
      .catch((error) => {
        largeAssetManifestPromise = null;
        throw error;
      });
  }
  return largeAssetManifestPromise;
}

function cleanAssetPath(url) {
  return url.split("?", 1)[0].replace(/^\.\//, "");
}

async function fetchChunkBytes(part, assetLabel, loadedBytes, totalBytes) {
  const response = await fetch(`${part.url}?v=${DEMO_ASSET_VERSION}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch ${part.url}: ${response.status} ${response.statusText}`);
  }
  const bytes = new Uint8Array(await response.arrayBuffer());
  if (part.size && bytes.length !== part.size) {
    throw new Error(`${part.url} size mismatch: expected ${part.size}, got ${bytes.length}`);
  }
  const nextLoaded = loadedBytes + bytes.length;
  if (totalBytes) {
    const pct = Math.round((nextLoaded / totalBytes) * 100);
    assetMetric.textContent = `${assetLabel} chunks ${pct}%`;
  }
  return bytes;
}

async function getChunkedAssetBytes(asset) {
  let manifest = null;
  try {
    manifest = await getLargeAssetManifest();
  } catch (error) {
    console.warn("Large asset manifest unavailable; falling back to direct asset URL.", error);
    return null;
  }
  const key = cleanAssetPath(asset.visualUrl);
  const entry = manifest.assets?.[key] || manifest.assets?.[asset.id];
  if (!entry?.parts?.length) return null;
  if (largeAssetBytesCache.has(key)) return largeAssetBytesCache.get(key);

  const parts = [];
  let loadedBytes = 0;
  for (const part of entry.parts) {
    const bytes = await fetchChunkBytes(part, asset.format, loadedBytes, entry.size);
    loadedBytes += bytes.length;
    parts.push(bytes);
  }
  const merged = new Uint8Array(entry.size || loadedBytes);
  let offset = 0;
  for (const bytes of parts) {
    merged.set(bytes, offset);
    offset += bytes.length;
  }
  if (entry.size && offset !== entry.size) {
    throw new Error(`${entry.source || key} assembled size mismatch: expected ${entry.size}, got ${offset}`);
  }
  largeAssetBytesCache.set(key, {
    bytes: merged,
    fileName: entry.fileName || key.split("/").pop(),
    fileType: entry.fileType || asset.format,
    source: entry.source || key,
  });
  return largeAssetBytesCache.get(key);
}

function frameCameraToRealBounds(force = false) {
  const frameBox = realFrameBounds || realBounds;
  if (!frameBox || frameBox.isEmpty() || (!force && hasAutoFramedRealAsset)) return;
  const center = new THREE.Vector3();
  const size = new THREE.Vector3();
  frameBox.getCenter(center);
  frameBox.getSize(size);
  const radius = Math.max(size.x, size.y, size.z, 1);
  const distance = radius * 0.86;
  controls.target.copy(center.clone().add(new THREE.Vector3(0, Math.max(size.y * 0.08, 0.38), 0)));
  camera.position.copy(controls.target).add(new THREE.Vector3(distance * 0.78, distance * 0.58, distance * 0.9));
  controls.maxDistance = Math.max(40, radius * 5);
  camera.near = Math.max(0.02, radius / 800);
  camera.far = Math.max(140, radius * 12);
  camera.updateProjectionMatrix();
  controls.update();
  hasAutoFramedRealAsset = true;
}

function registerCollider(mesh, label, collection = colliderObjects) {
  mesh.userData.colliderLabel = label;
  mesh.userData.surfaceType ||= "mesh-collider";
  mesh.userData.walkable ??= true;
  mesh.userData.characterCollision ??= true;
  mesh.userData.cameraCollision ??= true;
  collection.push(mesh);
  if (!colliderObjects.includes(mesh)) colliderObjects.push(mesh);
}

function clearRealAssetLayers({ dispose = false } = {}) {
  if (dispose) {
    realVisualLayer.traverse((child) => {
      if (child !== sparkSplatMesh) {
        child.geometry?.dispose?.();
        if (Array.isArray(child.material)) child.material.forEach((material) => material?.dispose?.());
        else child.material?.dispose?.();
      }
      child.dispose?.();
    });
    realColliderLayer.traverse((child) => {
      child.geometry?.dispose?.();
      if (Array.isArray(child.material)) child.material.forEach((material) => material?.dispose?.());
      else child.material?.dispose?.();
    });
  }
  realVisualLayer.clear();
  realColliderLayer.clear();
  realColliderRoot = null;
  realBounds = null;
  realFrameBounds = null;
  sparkSplatMesh = null;
  activeVisualAsset = null;
  hasAutoFramedRealAsset = false;
  realColliderObjects.length = 0;
  for (let i = colliderObjects.length - 1; i >= 0; i -= 1) {
    if (!proceduralColliderObjects.includes(colliderObjects[i])) colliderObjects.splice(i, 1);
  }
}

function activeColliderObjects() {
  return state.useRealAssets && state.realColliderReady ? realColliderObjects : proceduralColliderObjects;
}

function activeModeName() {
  return state.useRealAssets && state.realVisualReady && state.realColliderReady
    ? `${realVisualSource} + GLB`
    : state.useRealAssets && !state.realAssetError ? "Loading real assets"
    : "Procedural fallback";
}

function syncDemoState() {
  let visibleColliderMeshes = 0;
  let visibleColliderWires = 0;
  realColliderLayer.traverse((child) => {
    if (child instanceof THREE.Mesh && child.visible) visibleColliderMeshes += 1;
    if (child instanceof THREE.LineSegments && child.visible) visibleColliderWires += 1;
  });
  const snapshot = {
    mode: activeModeName(),
    visualSource: realVisualSource,
    visualFormat: realVisualFormat,
    visualUrl: realVisualUrl,
    visualAssetId: realVisualAssetId,
    visualUsesSpark: realVisualUsesSpark,
    visualCount: realPointCount,
    visualRawCount: realRawPointCount,
    visualRemovedOutliers: realRemovedOutliers,
    visualCleanupReportUrl: activeVisualAsset?.cleanupReportUrl || "",
    colliderUrl: realColliderUrl,
    colliderTriangles: Math.round(realTriangleCount),
    realVisualReady: state.realVisualReady,
    realColliderReady: state.realColliderReady,
    showVisual: state.showVisual,
    colliderRenderMode: state.colliderRenderMode,
    colliderVisible: colliderIsVisible(),
    cameraMode: state.cameraMode,
    splatQuality: state.splatQuality,
    sparkRendererVisible: sparkRenderer.visible,
    realVisualLayerVisible: realVisualLayer.visible,
    visibleColliderMeshes,
    visibleColliderWires,
    lastHit: state.lastHit,
    lastHitInfo: state.lastHitInfo,
    realAssetError: state.realAssetError,
  };
  window.__visualPhysicsDemoState = snapshot;
  document.documentElement.dataset.visualPhysicsState = JSON.stringify(snapshot);
  return snapshot;
}

function updateAssetMetric() {
  if (state.realVisualReady && state.realColliderReady) {
    assetMetric.textContent = `${formatCount(realPointCount)} / ${formatCount(realTriangleCount)}`;
    syncDemoState();
    return;
  }
  assetMetric.textContent = state.realAssetError ? "fallback" : "loading";
  syncDemoState();
}

function updateDebugPanel() {
  updateAssetMetric();
  const mode = activeModeName();
  modeChip.textContent = `${mode} · ${COLLIDER_RENDER_MODE_LABELS[state.colliderRenderMode]} collider · ${state.cameraMode} camera · ${SPLAT_QUALITY_PRESETS[state.splatQuality].label} splats · raycast ignores visual points`;
}

function applySplatQuality() {
  const preset = SPLAT_QUALITY_PRESETS[state.splatQuality] || SPLAT_QUALITY_PRESETS.balanced;
  for (const key of [
    "maxStdDev",
    "minAlpha",
    "minPixelRadius",
    "maxPixelRadius",
    "falloff",
    "preBlurAmount",
    "blurAmount",
    "clipXY",
    "focalAdjustment",
  ]) {
    sparkRenderer[key] = preset[key];
  }
  sparkRenderer.sortedCenter?.setScalar?.(Number.NEGATIVE_INFINITY);
  sparkRenderer.sortDirty = true;
  document.querySelector("#cycleSplatQuality").textContent = `Spark ${preset.label}`;
  updateDebugPanel();
}

function realGroundProbe(pos) {
  if (!state.realColliderReady || !realBounds) return null;
  const origin = new THREE.Vector3(pos.x, realBounds.max.y + 2, pos.z);
  raycaster.set(origin, new THREE.Vector3(0, -1, 0));
  raycaster.far = Math.max(16, realBounds.max.y - realBounds.min.y + 4);
  const hits = raycaster.intersectObjects(realColliderObjects, false);
  raycaster.far = Infinity;
  const horizontalHits = hits.filter((hit) => {
    const normal = hit.face?.normal.clone() || new THREE.Vector3(0, 1, 0);
    normal.transformDirection(hit.object.matrixWorld);
    return Math.abs(normal.y) > 0.18;
  });
  horizontalHits.sort((a, b) => a.point.y - b.point.y);
  return horizontalHits[0] || null;
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
  mesh.visible = colliderIsVisible();
  mesh.userData.surfaceType = "procedural-floor";
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
  colliderMesh.userData.surfaceType = `procedural-${semantic}`;
  colliderMesh.visible = colliderIsVisible();
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

async function loadRealPointCloud(asset = {
  id: "legacy_ply_fallback",
  label: "PLY fallback",
  format: "ply",
  visualUrl: REAL_ASSETS.plyFallbackUrl,
  colliderUrl: REAL_ASSETS.poissonFallbackUrl,
  pointSize: 0.018,
}) {
  activeVisualAsset = asset;
  realVisualSource = asset.label;
  realVisualFormat = asset.format;
  realVisualUrl = asset.visualUrl;
  realColliderUrl = asset.colliderUrl || realColliderUrl;
  realVisualAssetId = asset.id || asset.label;
  const loader = new PLYLoader();
  const geometry = await withTimeout(
    loader.loadAsync(asset.visualUrl),
    asset.timeoutMs || 45000,
    `${asset.label} PLY load`
  );
  geometry.computeBoundingBox();
  const sourceBox = robustPointCloudBounds(geometry);
  realPointCount = asset.pointCount || geometry.getAttribute("position")?.count || 0;
  realRawPointCount = asset.rawPointCount || realPointCount;
  realRemovedOutliers = asset.removedOutliers || Math.max(0, realRawPointCount - realPointCount);

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
    size: asset.pointSize || 0.018,
    vertexColors: true,
    transparent: true,
    opacity: 0.92,
    depthWrite: false,
  });
  const points = new THREE.Points(geometry, material);
  points.name = `real ${asset.label} centers from PLY`;
  points.userData.semantic = "real-ply";
  points.userData.preserveVertexColors = true;
  points.raycast = () => {};
  realVisualLayer.add(points);
  realVisualUsesSpark = false;
  fitRealLayersToDemoSpace(sourceBox);
  state.realVisualReady = true;
  setLayerVisibility();
}

async function loadSparkSplat(asset) {
  activeVisualAsset = asset;
  realVisualSource = asset.label;
  realVisualFormat = asset.format;
  realVisualUrl = asset.visualUrl;
  realVisualAssetId = asset.id || asset.label;
  const chunkedAsset = await getChunkedAssetBytes(asset);
  const splatOptions = {
    lod: asset.lod,
    lodAbove: 100000,
    raycastable: false,
    onProgress: (event) => {
      if (!event.total) return;
      const pct = Math.round((event.loaded / event.total) * 100);
      assetMetric.textContent = `${asset.format} ${pct}%`;
    },
  };
  if (chunkedAsset) {
    splatOptions.fileBytes = chunkedAsset.bytes;
    splatOptions.fileName = chunkedAsset.fileName;
    splatOptions.fileType = chunkedAsset.fileType;
  } else {
    splatOptions.url = asset.visualUrl;
  }
  const splat = new SplatMesh(splatOptions);
  splat.name = `real ${asset.label} visual splat`;
  splat.raycast = () => {};
  realVisualLayer.add(splat);
  await withTimeout(splat.initialized, asset.timeoutMs || 60000, `${asset.label} initialization`);
  splat.rotation.set(asset.splatRotation?.x || 0, asset.splatRotation?.y || 0, asset.splatRotation?.z || 0);
  splat.updateMatrixWorld(true);

  const sourceBounds = boxFromArrayBounds(asset.robustBounds) || robustSplatBounds(splat);
  const sourceBox = transformedBox(sourceBounds, splat.matrix);
  if (sourceBox.isEmpty()) {
    throw new Error("Spark splat bounding box is empty.");
  }
  realPointCount = asset.splatCount
    || splat.packedSplats?.numSplats
    || splat.extSplats?.numSplats
    || splat.splats?.numSplats
    || splat.numSplats
    || 0;
  realRawPointCount = asset.rawSplatCount || realPointCount;
  realRemovedOutliers = asset.removedOutliers || Math.max(0, realRawPointCount - realPointCount);
  realVisualUsesSpark = true;
  sparkSplatMesh = splat;
  applySplatQuality();
  fitRealLayersToDemoSpace(sourceBox, asset);
  state.realVisualReady = true;
  setLayerVisibility();
}

async function loadRealCollider(colliderUrl = activeVisualAsset?.colliderUrl || REAL_ASSETS.poissonFallbackUrl, colliderLabel = activeVisualAsset?.colliderLabel || "true-3dgs-poisson-mesh") {
  realColliderUrl = colliderUrl;
  const loader = new GLTFLoader();
  loader.setDRACOLoader(dracoLoader);
  const gltf = await loader.loadAsync(colliderUrl);
  const root = gltf.scene;
  root.name = "real 3dgs mesh collider";
  realColliderRoot = root;
  realTriangleCount = 0;

  const shadedMaterial = makeMat(0x31423d, {
    transparent: true,
    opacity: 0.18,
    side: THREE.DoubleSide,
  });
  const wireMaterial = makeWireMat(0xefb35f, 0.5);
  root.traverse((child) => {
    if (!(child instanceof THREE.Mesh)) return;
    const sourceMaterial = child.material;
    if (Array.isArray(sourceMaterial)) sourceMaterial.forEach((material) => material?.dispose?.());
    else sourceMaterial?.dispose?.();
    child.geometry.computeVertexNormals();
    child.material = shadedMaterial.clone();
    child.castShadow = false;
    child.receiveShadow = true;
    child.userData.colliderLabel = colliderLabel;
    child.userData.surfaceType = "scene-collider";
    child.userData.walkable = true;
    child.userData.characterCollision = true;
    child.userData.cameraCollision = true;
    child.userData.colliderSolid = true;
    child.visible = colliderIsVisible();
    registerCollider(child, child.userData.colliderLabel, realColliderObjects);
    const positionCount = child.geometry.getAttribute("position")?.count || 0;
    realTriangleCount += child.geometry.index ? child.geometry.index.count / 3 : positionCount / 3;

    const wire = new THREE.LineSegments(
      new THREE.WireframeGeometry(child.geometry),
      wireMaterial.clone()
    );
    wire.name = `${child.name || "mesh"} collider wire overlay`;
    wire.visible = colliderIsVisible();
    wire.userData.colliderWire = true;
    wire.raycast = () => {};
    child.add(wire);
  });

  realColliderLayer.add(root);
  applyRealTransform(root);
  state.realColliderReady = true;
  resetActorOnRealMesh();
  setLayerVisibility();
}

async function loadSparkAssetPair(asset) {
  clearRealAssetLayers({ dispose: true });
  state.realVisualReady = false;
  state.realColliderReady = false;
  state.realAssetError = "";
  resetRealVisualStats();
  realTriangleCount = 0;
  realVisualUsesSpark = false;
  realVisualSource = asset.label;
  realVisualFormat = asset.format;
  realVisualUrl = asset.visualUrl;
  realColliderUrl = asset.colliderUrl;
  updateDebugPanel();
  await loadSparkSplat(asset);
  await loadRealCollider(asset.colliderUrl, asset.colliderLabel);
  setLayerVisibility();
}

async function loadPlyAssetPair(asset) {
  clearRealAssetLayers({ dispose: true });
  state.realVisualReady = false;
  state.realColliderReady = false;
  state.realAssetError = "";
  resetRealVisualStats();
  realTriangleCount = 0;
  realVisualUsesSpark = false;
  realVisualSource = asset.label;
  realVisualFormat = asset.format;
  realVisualUrl = asset.visualUrl;
  realColliderUrl = asset.colliderUrl;
  realVisualAssetId = asset.id || asset.label;
  updateDebugPanel();
  await loadRealPointCloud(asset);
  await loadRealCollider(asset.colliderUrl, asset.colliderLabel);
  setLayerVisibility();
}

async function loadRealAssets() {
  updateDebugPanel();
  const assetErrors = [];
  for (const asset of SPARK_VISUAL_ASSETS) {
    try {
      await loadSparkAssetPair(asset);
      showToast(`Loaded ${asset.label} visual + GLB collider mesh.`);
      return;
    } catch (error) {
      console.warn(`${asset.label} visual/collider path failed; trying next asset.`, error);
      assetErrors.push(`${asset.label}: ${error?.message || String(error)}`);
      clearRealAssetLayers({ dispose: true });
      state.realVisualReady = false;
      state.realColliderReady = false;
      resetRealVisualStats();
      realTriangleCount = 0;
      realVisualUsesSpark = false;
    }
  }

  for (const asset of PLY_VISUAL_ASSETS) {
    try {
      await loadPlyAssetPair(asset);
      showToast(`Loaded ${asset.label} visual + GLB collider mesh.`);
      return;
    } catch (error) {
      console.warn(`${asset.label} visual/collider path failed; trying next asset.`, error);
      assetErrors.push(`${asset.label}: ${error?.message || String(error)}`);
      clearRealAssetLayers({ dispose: true });
      state.realVisualReady = false;
      state.realColliderReady = false;
      resetRealVisualStats();
      realTriangleCount = 0;
      realVisualUsesSpark = false;
    }
  }

  try {
    activeVisualAsset = null;
    realVisualSource = "PLY fallback";
    realVisualFormat = "ply";
    realVisualUrl = REAL_ASSETS.plyFallbackUrl;
    realColliderUrl = REAL_ASSETS.poissonFallbackUrl;
    await loadRealPointCloud();
    await loadRealCollider(REAL_ASSETS.poissonFallbackUrl, "true-3dgs-poisson-mesh");
    setLayerVisibility();
    showToast("Spark 资产加载失败，已加载 PLY/Poisson fallback。");
  } catch (fallbackError) {
    const message = [
      ...assetErrors,
      `PLY/Poisson fallback: ${fallbackError?.message || String(fallbackError)}`,
    ].join(" | ");
    setRealAssetError(new Error(message));
  }
}

function updateVisualColors() {
  if (sparkSplatMesh) {
    sparkSplatMesh.recolor.set(state.semanticTint ? 0.58 : 1, state.semanticTint ? 0.95 : 1, state.semanticTint ? 0.9 : 1);
    sparkSplatMesh.opacity = colliderIsVisible() ? 0.58 : 1;
  }
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
  if (state.cameraMode === "fly") {
    actor.velocity.multiplyScalar(0.82);
    actor.group.position.copy(actor.position);
    actor.group.rotation.y = actor.yaw;
    speedMetric.textContent = "0.0";
    heightMetric.textContent = actor.position.y.toFixed(2);
    return;
  }

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

function updateFlyCamera(dt) {
  if (state.cameraMode !== "fly") return;
  const forward = new THREE.Vector3();
  camera.getWorldDirection(forward);
  const flatForward = forward.clone().setY(0);
  if (flatForward.lengthSq() > 0) flatForward.normalize();
  const right = new THREE.Vector3().crossVectors(flatForward, camera.up).normalize();
  const move = new THREE.Vector3();
  if (keys.has("KeyW") || keys.has("ArrowUp")) move.add(flatForward);
  if (keys.has("KeyS") || keys.has("ArrowDown")) move.sub(flatForward);
  if (keys.has("KeyA") || keys.has("ArrowLeft")) move.sub(right);
  if (keys.has("KeyD") || keys.has("ArrowRight")) move.add(right);
  if (keys.has("KeyE") || keys.has("Space")) move.y += 1;
  if (keys.has("KeyQ") || keys.has("ShiftLeft") || keys.has("ShiftRight")) move.y -= 1;
  if (move.lengthSq() === 0) return;
  const speed = (keys.has("AltLeft") || keys.has("AltRight")) ? 8.5 : 4.2;
  camera.position.addScaledVector(move.normalize(), speed * dt);
  controls.target.copy(camera.position).add(forward.multiplyScalar(4));
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

function updateCameraMode() {
  controls.enabled = state.cameraMode === "orbit";
  canvas.classList.toggle("is-fly-mode", state.cameraMode === "fly");
  document.querySelector("#toggleCameraMode").textContent = state.cameraMode === "orbit" ? "Orbit Camera" : "Fly Camera";
  document.querySelector("#toggleCameraMode").classList.toggle("is-active", state.cameraMode === "fly");
  if (state.cameraMode === "fly") {
    const direction = new THREE.Vector3();
    camera.getWorldDirection(direction);
    controls.target.copy(camera.position).add(direction.multiplyScalar(4));
  }
  updateDebugPanel();
}

function setLayerVisibility() {
  visualLayer.visible = state.showVisual;
  realVisualLayer.visible = state.showVisual && state.useRealAssets && state.realVisualReady;
  proceduralLayer.visible = state.showVisual && (!state.useRealAssets || !state.realVisualReady);
  sparkRenderer.visible = state.showVisual && state.useRealAssets && state.realVisualReady && realVisualUsesSpark;
  realVisualLayer.traverse((child) => {
    if (child instanceof THREE.Points) child.material.opacity = colliderIsVisible() ? 0.46 : baseVisualOpacity;
  });
  if (sparkSplatMesh) sparkSplatMesh.opacity = colliderIsVisible() ? 0.58 : 1;
  realColliderLayer.traverse((child) => {
    if (child instanceof THREE.Mesh) {
      child.visible = state.useRealAssets
        && state.realColliderReady
        && state.colliderRenderMode !== "hidden";
      child.material.opacity = state.colliderRenderMode === "solid" ? 0.28 : 0.035;
    } else if (child instanceof THREE.LineSegments) {
      child.visible = state.useRealAssets && state.realColliderReady && state.colliderRenderMode === "wire";
    }
  });
  proceduralColliderLayer.traverse((child) => {
    if (child instanceof THREE.Mesh || child instanceof THREE.LineSegments) {
      child.visible = colliderIsVisible() && (!state.useRealAssets || !state.realColliderReady);
    }
  });
  document.querySelector("#toggleAssets").classList.toggle("is-active", state.useRealAssets);
  document.querySelector("#toggleVisual").classList.toggle("is-active", state.showVisual);
  document.querySelector("#toggleCollider").classList.toggle("is-active", colliderIsVisible());
  document.querySelector("#toggleCollider").textContent = `Collider ${state.colliderRenderMode}`;
  document.querySelector("#toggleSemantic").classList.toggle("is-active", state.semanticTint);
  document.querySelector("#cycleSplatQuality").classList.toggle("is-active", state.splatQuality !== "balanced");
  updateCameraMode();
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

function focusCameraOnPoint(point) {
  if (state.cameraMode !== "orbit") return;
  const offset = camera.position.clone().sub(controls.target);
  controls.target.copy(point);
  camera.position.copy(point).add(offset);
  controls.update();
}

function describeHit(hit, normal) {
  const label = hit.object.userData.colliderLabel || hit.object.name || "collider";
  const role = surfaceRoleFromUserData(hit.object.userData);
  const surfaceType = hit.object.userData.surfaceType || "mesh-collider";
  const faceIndex = Number.isFinite(hit.faceIndex) ? hit.faceIndex : -1;
  return {
    label,
    surfaceType,
    role,
    faceIndex,
    point: {
      x: Number(hit.point.x.toFixed(4)),
      y: Number(hit.point.y.toFixed(4)),
      z: Number(hit.point.z.toFixed(4)),
    },
    normal: {
      x: Number(normal.x.toFixed(4)),
      y: Number(normal.y.toFixed(4)),
      z: Number(normal.z.toFixed(4)),
    },
    distance: Number(hit.distance.toFixed(4)),
  };
}

function inspectColliderAt(clientX, clientY, { focus = true } = {}) {
  const rect = canvas.getBoundingClientRect();
  pointer.x = ((clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  const hits = raycaster.intersectObjects(activeColliderObjects(), false);
  if (!hits.length) {
    state.lastHit = "none";
    state.lastHitInfo = null;
    hitMetric.textContent = "none";
    surfaceMetric.textContent = "none";
    syncDemoState();
    showToast("No collider hit. Visual splats are ignored by raycast.");
    return;
  }
  const hit = hits[0];
  const label = hit.object.userData.colliderLabel || hit.object.name || "collider";
  const normal = hit.face?.normal.clone() || new THREE.Vector3(0, 1, 0);
  normal.transformDirection(hit.object.matrixWorld);
  markHit(hit.point, normal);
  state.lastHit = label;
  state.lastHitInfo = describeHit(hit, normal);
  hitMetric.textContent = `face ${state.lastHitInfo.faceIndex >= 0 ? state.lastHitInfo.faceIndex : "n/a"}`;
  surfaceMetric.textContent = state.lastHitInfo.role;
  if (focus) focusCameraOnPoint(hit.point);
  syncDemoState();
  showToast(`Ray hit ${label}: ${state.lastHitInfo.surfaceType}, normal ${formatVec3(normal)}.`);
}

function onPointerDown(event) {
  if (event.button !== 0) return;
  pointerDown = { x: event.clientX, y: event.clientY, time: performance.now() };
}

function onPointerMove(event) {
  if (state.cameraMode !== "fly" || event.buttons !== 1) return;
  const direction = new THREE.Vector3();
  camera.getWorldDirection(direction);
  const spherical = new THREE.Spherical().setFromVector3(direction);
  spherical.theta -= event.movementX * 0.0032;
  spherical.phi = THREE.MathUtils.clamp(spherical.phi - event.movementY * 0.0032, 0.04, Math.PI - 0.04);
  direction.setFromSpherical(spherical).normalize();
  controls.target.copy(camera.position).add(direction.multiplyScalar(4));
  camera.lookAt(controls.target);
}

function onPointerUp(event) {
  if (event.button !== 0 || !pointerDown) return;
  const dx = event.clientX - pointerDown.x;
  const dy = event.clientY - pointerDown.y;
  const elapsed = performance.now() - pointerDown.time;
  pointerDown = null;
  if (Math.hypot(dx, dy) > 5 || elapsed > 450) return;
  inspectColliderAt(event.clientX, event.clientY);
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
  state.lastHit = "none";
  state.lastHitInfo = null;
  hitMetric.textContent = "none";
  surfaceMetric.textContent = "none";
  syncDemoState();
  showToast("Actor reset on the collider mesh floor.");
}

function resetCamera() {
  frameCameraToRealBounds(true);
  showToast("View reset to the loaded 3DGS / collider bounds.");
}

function animate() {
  const dt = Math.min(clock.getDelta(), 0.04);
  updateActor(dt);
  updateFlyCamera(dt);
  updateCameras();
  if (state.cameraMode === "orbit") controls.update();

  const pulse = 0.78 + Math.sin(clock.elapsedTime * 2.2) * 0.08;
  proceduralLayer.traverse((child) => {
    if (child instanceof THREE.Points) child.material.opacity = pulse;
  });

  sparkRenderer.render(scene, camera);
  const mainSparkVisible = sparkRenderer.visible;
  sparkRenderer.visible = false;
  fpvRenderer.render(scene, fpvCamera);
  sparkRenderer.visible = mainSparkVisible;
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
  canvas.addEventListener("pointermove", onPointerMove);
  canvas.addEventListener("pointerup", onPointerUp);

  document.querySelector("#toggleVisual").addEventListener("click", () => {
    state.showVisual = !state.showVisual;
    setLayerVisibility();
  });
  document.querySelector("#toggleAssets").addEventListener("click", () => {
    if (!state.realVisualReady || !state.realColliderReady) {
      showToast("Real Spark 3DGS / GLB assets are still loading; using fallback until ready.");
      return;
    }
    state.useRealAssets = !state.useRealAssets;
    markerLayer.clear();
    state.lastHit = "none";
    state.lastHitInfo = null;
    hitMetric.textContent = "none";
    surfaceMetric.textContent = "none";
    placeActorAtCurrentSpawn();
    setLayerVisibility();
    showToast(state.useRealAssets ? `Using ${realVisualSource} visual + GLB collider.` : "Using procedural fallback scene.");
  });
  document.querySelector("#toggleCollider").addEventListener("click", () => {
    state.colliderRenderMode = nextValue(COLLIDER_RENDER_MODES, state.colliderRenderMode);
    setLayerVisibility();
    showToast(`Collider render mode: ${COLLIDER_RENDER_MODE_LABELS[state.colliderRenderMode]}. Collision stays active.`);
  });
  document.querySelector("#toggleCameraMode").addEventListener("click", () => {
    state.cameraMode = state.cameraMode === "orbit" ? "fly" : "orbit";
    keys.clear();
    updateCameraMode();
    showToast(state.cameraMode === "fly" ? "Fly camera: drag to look, WASD move, Q/E down/up." : "Orbit camera: drag orbit, click collider to focus.");
  });
  document.querySelector("#cycleSplatQuality").addEventListener("click", () => {
    state.splatQuality = nextValue(SPLAT_QUALITY_ORDER, state.splatQuality);
    applySplatQuality();
    showToast(`Spark render quality: ${SPLAT_QUALITY_PRESETS[state.splatQuality].label}.`);
  });
  document.querySelector("#toggleSemantic").addEventListener("click", () => {
    state.semanticTint = !state.semanticTint;
    updateVisualColors();
    setLayerVisibility();
  });
  document.querySelector("#resetCamera").addEventListener("click", resetCamera);
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
showToast("Loading real Spark 3DGS visual layer + GLB collider mesh...");
animate();
