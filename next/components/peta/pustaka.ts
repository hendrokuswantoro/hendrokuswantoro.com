const PEKERJA_PETA = "/assets/vendor/maplibre/6.9.0/maplibre-gl-worker.mjs";

export async function pustakaPeta() {
  const maplibregl = await import("maplibre-gl");
  maplibregl.setWorkerUrl(PEKERJA_PETA);
  return maplibregl;
}
