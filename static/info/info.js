const set = (selector, value) => {
  const node = document.querySelector(selector);
  if (node) node.textContent = value ?? "—";
};

set("[data-info-url]", location.href);
set("[data-info-online]", navigator.onLine ? "oui" : "non");
set("[data-info-ua]", navigator.userAgent);

try {
  const response = await fetch("../provenance.json", { cache: "no-store" });
  if (!response.ok) throw new Error(`provenance.json HTTP ${response.status}`);
  const provenance = await response.json();
  set("[data-info-content-sha]", provenance.content_sha);
  set("[data-info-core-sha]", provenance.core_sha);
  set("[data-info-built-at]", provenance.built_at);
} catch (error) {
  const node = document.querySelector("[data-info-error]");
  if (node) {
    node.hidden = false;
    node.textContent = `Provenance indisponible : ${error.message}`;
  }
}

if ("serviceWorker" in navigator) {
  const registration = await navigator.serviceWorker.getRegistration();
  set("[data-info-sw]", registration ? "enregistré" : "non enregistré");
  set("[data-info-sw-controller]", navigator.serviceWorker.controller?.scriptURL || "aucun");
} else {
  set("[data-info-sw]", "non supporté");
  set("[data-info-sw-controller]", "aucun");
}

if ("caches" in globalThis) {
  try {
    const names = await caches.keys();
    set("[data-info-caches]", names.length ? names.join(", ") : "aucun");
  } catch {
    set("[data-info-caches]", "indisponible");
  }
} else {
  set("[data-info-caches]", "non supporté");
}
