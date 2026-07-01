(function () {
  const STORAGE_KEY = "v2m-theme-v1";
  const COOKIE_NAME = "v2m_theme";
  const root = document.documentElement;
  const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)");

  function cookieDomain() {
    const host = window.location.hostname;
    return host === "relumeow.top" || host.endsWith(".relumeow.top") ? "; domain=.relumeow.top; secure" : "";
  }

  function cookieTheme() {
    const match = document.cookie.match(new RegExp(`(?:^|; )${COOKIE_NAME}=([^;]*)`));
    if (!match) return "";
    const value = decodeURIComponent(match[1]);
    return value === "light" || value === "dark" || value === "system" ? value : "";
  }

  function writeCookieTheme(choice) {
    document.cookie = `${COOKIE_NAME}=${encodeURIComponent(choice)}; max-age=31536000; path=/; samesite=lax${cookieDomain()}`;
  }

  function storedTheme() {
    try {
      const value = window.localStorage.getItem(STORAGE_KEY) || cookieTheme();
      return value === "light" || value === "dark" || value === "system" ? value : "system";
    } catch (_error) {
      return cookieTheme() || "system";
    }
  }

  function effectiveTheme(choice) {
    if (choice === "dark" || choice === "light") return choice;
    return prefersDark && prefersDark.matches ? "dark" : "light";
  }

  function labelFor(theme) {
    return theme === "dark" ? "暗夜" : "白天";
  }

  function applyTheme(choice = storedTheme()) {
    const actual = effectiveTheme(choice);
    root.dataset.theme = actual;
    root.dataset.themeChoice = choice;
    document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
      button.dataset.themeState = actual;
      button.setAttribute("aria-label", `切换到${actual === "dark" ? "白天" : "暗夜"}模式`);
      button.setAttribute("title", `当前：${labelFor(actual)}模式`);
      const label = button.querySelector("[data-theme-label]");
      if (label) label.textContent = labelFor(actual);
    });
  }

  function setTheme(choice) {
    try {
      window.localStorage.setItem(STORAGE_KEY, choice);
    } catch (_error) {
      // Theme still applies for the current page even if storage is blocked.
    }
    writeCookieTheme(choice);
    applyTheme(choice);
  }

  function toggleTheme() {
    const current = effectiveTheme(storedTheme());
    setTheme(current === "dark" ? "light" : "dark");
  }

  function bind() {
    document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
      button.addEventListener("click", toggleTheme);
    });
    applyTheme();
  }

  window.V2MTheme = { apply: applyTheme, set: setTheme, toggle: toggleTheme };

  applyTheme();

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bind, { once: true });
  } else {
    bind();
  }

  if (prefersDark) {
    prefersDark.addEventListener("change", () => {
      if (storedTheme() === "system") applyTheme("system");
    });
  }
})();
