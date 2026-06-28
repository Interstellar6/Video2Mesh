const RAW_ORIGIN = "https://raw.githubusercontent.com";
const RAW_REF = "main";
const RAW_PREFIX = `/Interstellar6/Video2Mesh/${RAW_REF}/docs-blog`;

const ROUTES = {
  "/": { path: "/admin/index.html", type: "text/html; charset=utf-8" },
  "/index.html": { path: "/admin/index.html", type: "text/html; charset=utf-8" },
  "/admin.css": { path: "/admin/admin.css", type: "text/css; charset=utf-8" },
  "/admin.js": { path: "/admin/admin.js", type: "application/javascript; charset=utf-8" },
  "/styles.css": { path: "/styles.css", type: "text/css; charset=utf-8" },
};

function upstreamUrl(pathname) {
  const route = ROUTES[pathname];
  if (!route) return null;
  return {
    url: `${RAW_ORIGIN}${RAW_PREFIX}${route.path}`,
    type: route.type,
  };
}

function withAdminHeaders(response, contentType) {
  const headers = new Headers(response.headers);
  headers.set("Content-Type", contentType);
  headers.set("Cache-Control", "no-store");
  headers.set("X-Robots-Tag", "noindex, nofollow");
  headers.set("Access-Control-Allow-Origin", "https://admin.relumeow.top");
  headers.delete("Content-Security-Policy");
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const upstream = upstreamUrl(url.pathname);
    if (!upstream) return new Response("Not found", { status: 404 });

    const upstreamRequest = new Request(upstream.url, request);
    const response = await fetch(upstreamRequest);
    return withAdminHeaders(response, upstream.type);
  },
};
