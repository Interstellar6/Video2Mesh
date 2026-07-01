(function () {
  const API_STORAGE_KEY = "v2m-blog-api-v1";
  const DEFAULT_API_URL = "https://api.relumeow.top";

  let apiConfig = loadApiConfig();
  let apiProjects = [];
  let apiTasks = [];
  let apiUser = null;
  let cloudProjects = [];
  let cloudSessions = [];
  let cloudMessages = [];
  let cloudFiles = [];
  let selectedCloudProject = "";
  let selectedCloudSession = "";
  let workspacePath = "";
  let currentCloudSession = null;
  let cloudRunnerPollTimer = 0;
  let cloudSearchQuery = "";
  let isDraftSession = false;

  const $ = (id) => document.getElementById(id);
  const els = {
    identityBadge: $("identityBadge"),
    identityRole: $("identityRole"),
    identityName: $("identityName"),
    apiStatus: $("apiStatus"),
    apiUrlInput: $("apiUrlInput"),
    apiHealthCheck: $("apiHealthCheck"),
    loginForm: $("loginForm"),
    setupForm: $("setupForm"),
    githubLoginButton: $("githubLoginButton"),
    sessionInfo: $("sessionInfo"),
    logoutButton: $("logoutButton"),
    projectList: $("projectList"),
    projectForm: $("projectForm"),
    refreshProjects: $("refreshProjects"),
    taskList: $("taskList"),
    taskForm: $("taskForm"),
    refreshTasks: $("refreshTasks"),
    remoteDocForm: $("remoteDocForm"),
    refreshCloudWorkspace: $("refreshCloudWorkspace"),
    cloudWorkspaceStatus: $("cloudWorkspaceStatus"),
    railNewChat: $("railNewChat"),
    railSearchFocus: $("railSearchFocus"),
    railRunFocus: $("railRunFocus"),
    cloudSearchInput: $("cloudSearchInput"),
    clearCloudSearch: $("clearCloudSearch"),
    cloudProjectForm: $("cloudProjectForm"),
    cloudProjectList: $("cloudProjectList"),
    cloudSessionForm: $("cloudSessionForm"),
    cloudSessionList: $("cloudSessionList"),
    primaryNewSession: $("primaryNewSession"),
    cloudSessionTitle: $("cloudSessionTitle"),
    cloudSessionMeta: $("cloudSessionMeta"),
    cloudWorkspaceChip: $("cloudWorkspaceChip"),
    cloudMessageCount: $("cloudMessageCount"),
    cloudFileCount: $("cloudFileCount"),
    threadNewTask: $("threadNewTask"),
    codexRunStrip: $("codexRunStrip"),
    cloudMessageList: $("cloudMessageList"),
    cloudMessageForm: $("cloudMessageForm"),
    promptSuggestions: $("promptSuggestions"),
    activitySummary: $("activitySummary"),
    activityChangeTitle: $("activityChangeTitle"),
    activityChangeMeta: $("activityChangeMeta"),
    activityOpenWorkspace: $("activityOpenWorkspace"),
    activityReview: $("activityReview"),
    activityToggle: $("activityToggle"),
    composerContext: $("composerContext"),
    composerMode: $("composerMode"),
    attachWorkspaceButton: $("attachWorkspaceButton"),
    clearComposer: $("clearComposer"),
    newSessionShortcut: $("newSessionShortcut"),
    cloudFileList: $("cloudFileList"),
    cloudFileForm: $("cloudFileForm"),
    cloudFilePreview: $("cloudFilePreview"),
    refreshWorkspaceFiles: $("refreshWorkspaceFiles"),
    workspaceUpButton: $("workspaceUpButton"),
    workspacePathLabel: $("workspacePathLabel"),
    workspaceFileList: $("workspaceFileList"),
    workspaceFilePreview: $("workspaceFilePreview"),
    terminalForm: $("terminalForm"),
    terminalCwdLabel: $("terminalCwdLabel"),
    terminalOutput: $("terminalOutput"),
    codexRunnerPill: $("codexRunnerPill"),
    codexRunMeta: $("codexRunMeta"),
    codexRunCard: $("codexRunCard"),
    runCodexNow: $("runCodexNow"),
    inspectorTabs: Array.from(document.querySelectorAll("[data-inspector-tab]")),
    inspectorPanels: Array.from(document.querySelectorAll("[data-inspector-panel]")),
    tabs: Array.from(document.querySelectorAll("[data-admin-tab]")),
    panels: Array.from(document.querySelectorAll("[data-tab-panel]")),
  };

  const escapeHtml = (value) => String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");

  function loadApiConfig() {
    try {
      const raw = window.localStorage.getItem(API_STORAGE_KEY);
      const parsed = raw ? JSON.parse(raw) : {};
      return {
        url: normalizeApiUrl(parsed?.url),
        sessionToken: parsed?.sessionToken || parsed?.token || "",
        expiresAt: parsed?.expiresAt || "",
        username: parsed?.username || "",
        role: parsed?.role || "",
      };
    } catch (_error) {
      return { url: DEFAULT_API_URL, sessionToken: "", expiresAt: "" };
    }
  }

  function normalizeApiUrl(value) {
    const url = String(value || "").trim();
    if (!url) return DEFAULT_API_URL;
    const isLocalHttp = /^http:\/\/(127\.0\.0\.1|localhost)(:\d+)?\/?$/i.test(url);
    const isLocalPage = /^(127\.0\.0\.1|localhost)$/i.test(window.location.hostname);
    if (window.location.protocol === "https:" && isLocalHttp && !isLocalPage) return DEFAULT_API_URL;
    return url;
  }

  function persistApiConfig() {
    apiConfig = {
      url: String(els.apiUrlInput.value || DEFAULT_API_URL).replace(/\/+$/, ""),
      sessionToken: apiConfig.sessionToken || "",
      expiresAt: apiConfig.expiresAt || "",
      username: apiUser?.username || apiUser?.id || "",
      role: apiUser?.role || "",
    };
    try {
      window.localStorage.setItem(API_STORAGE_KEY, JSON.stringify(apiConfig));
    } catch (_error) {
      setApiStatus("浏览器阻止保存 API 设置", "error");
    }
  }

  function setApiStatus(message, state = "idle") {
    els.apiStatus.textContent = message;
    els.apiStatus.dataset.state = state;
  }

  function isFilePreview() {
    return window.location.protocol === "file:";
  }

  function localServerUrl() {
    return "http://127.0.0.1:8000/docs-blog/admin/#auth";
  }

  function friendlyFetchError(error, fallback = "请求失败") {
    const message = error?.message || fallback;
    if (isFilePreview() && /failed to fetch/i.test(message)) {
      return `请用本地 HTTP 服务打开管理员页：${localServerUrl()}`;
    }
    return message;
  }

  function setInspectorTab(tabName) {
    const next = els.inspectorPanels.some((panel) => panel.dataset.inspectorPanel === tabName) ? tabName : "workspace";
    els.inspectorTabs.forEach((tab) => {
      const active = tab.dataset.inspectorTab === next;
      tab.classList.toggle("active", active);
      tab.setAttribute("aria-selected", active ? "true" : "false");
    });
    els.inspectorPanels.forEach((panel) => {
      const active = panel.dataset.inspectorPanel === next;
      panel.hidden = !active;
      panel.classList.toggle("active", active);
    });
  }

  function setActiveTab(tabName) {
    const next = els.panels.some((panel) => panel.dataset.tabPanel === tabName) ? tabName : "auth";
    document.body.dataset.activeAdminTab = next;
    els.tabs.forEach((tab) => {
      const active = tab.dataset.adminTab === next;
      tab.classList.toggle("active", active);
      tab.setAttribute("aria-selected", active ? "true" : "false");
    });
    els.panels.forEach((panel) => {
      panel.hidden = panel.dataset.tabPanel !== next;
    });
    if (!window.location.hash.includes("v2m_session_token") && window.location.hash !== `#${next}`) {
      history.replaceState(null, "", `#${next}`);
    }
  }

  function activeTabFromHash() {
    const tabName = window.location.hash.replace(/^#/, "");
    return els.panels.some((panel) => panel.dataset.tabPanel === tabName) ? tabName : "auth";
  }

  function updateIdentityBadge() {
    if (!apiUser) {
      els.identityBadge.dataset.role = "guest";
      els.identityRole.textContent = "访客";
      els.identityName.textContent = apiConfig.sessionToken ? "恢复中" : "未登录";
      return;
    }
    const role = String(apiUser.role || "admin");
    const name = String(apiUser.username || apiUser.id || "已登录");
    els.identityBadge.dataset.role = role.toLowerCase() === "admin" ? "admin" : "user";
    els.identityRole.textContent = role === "admin" ? "管理员" : role;
    els.identityName.textContent = name;
  }

  function apiBaseUrl() {
    persistApiConfig();
    return apiConfig.url || DEFAULT_API_URL;
  }

  async function apiRequest(path, options = {}) {
    apiBaseUrl();
    const headers = new Headers(options.headers || {});
    const authToken = options.authToken === undefined ? apiConfig.sessionToken : options.authToken;
    if (authToken) headers.set("Authorization", `Bearer ${authToken}`);
    if (options.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
    const response = await fetch(`${apiConfig.url}${path}`, { ...options, headers });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.error || `${response.status} ${response.statusText}`);
    }
    return data;
  }

  async function checkApiHealth() {
    try {
      setApiStatus("连接中...", "busy");
      const data = await apiRequest("/api/health", { authToken: "" });
      const label = data.users_configured ? "API 已连接，请登录" : "API 已连接，请先创建管理员";
      setApiStatus(data.ok ? label : "异常", data.ok ? "ok" : "error");
      if (apiConfig.sessionToken) await restoreSession();
    } catch (error) {
      setApiStatus(friendlyFetchError(error, "连接失败"), "error");
    }
  }

  async function restoreSession() {
    try {
      const data = await apiRequest("/api/auth/me");
      apiUser = data.user || null;
      setApiStatus(apiUser ? "已登录" : "需要登录", apiUser ? "ok" : "warn");
      updateSessionInfo();
      await Promise.all([loadProjects(), loadTasks(), loadCloudProjects(), loadWorkspaceFiles()]);
    } catch (error) {
      apiUser = null;
      apiConfig.sessionToken = "";
      apiConfig.expiresAt = "";
      persistApiConfig();
      updateSessionInfo();
      renderApiLists();
      setApiStatus(friendlyFetchError(error, "登录已失效"), "warn");
    }
  }

  async function setupAdminFromForm(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = Object.fromEntries(new FormData(form).entries());
    const payload = {
      username: String(data.username || ""),
      password: String(data.password || ""),
    };
    try {
      setApiStatus("创建管理员...", "busy");
      const result = await apiRequest("/api/auth/setup", {
        method: "POST",
        authToken: String(data.bootstrap_token || ""),
        body: JSON.stringify(payload),
      });
      applyLoginResult(result);
      form.reset();
      await Promise.all([loadProjects(), loadTasks(), loadCloudProjects(), loadWorkspaceFiles()]);
    } catch (error) {
      setApiStatus(friendlyFetchError(error, "管理员创建失败"), "error");
    }
  }

  async function loginFromForm(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const payload = Object.fromEntries(new FormData(form).entries());
    try {
      setApiStatus("登录中...", "busy");
      const result = await apiRequest("/api/auth/login", {
        method: "POST",
        authToken: "",
        body: JSON.stringify(payload),
      });
      applyLoginResult(result);
      form.reset();
      await Promise.all([loadProjects(), loadTasks(), loadCloudProjects(), loadWorkspaceFiles()]);
    } catch (error) {
      setApiStatus(friendlyFetchError(error, "登录失败"), "error");
    }
  }

  function loginWithGitHub() {
    try {
      persistApiConfig();
      const returnUrl = window.location.href;
      const url = `${apiConfig.url}/api/auth/github/start?return_url=${encodeURIComponent(returnUrl)}`;
      const popup = window.open(url, "v2m-github-login", "width=520,height=720");
      if (!popup) setApiStatus("浏览器拦截了 GitHub 登录窗口", "error");
      else setApiStatus("等待 GitHub 授权...", "busy");
    } catch (error) {
      setApiStatus(error.message || "GitHub 登录失败", "error");
    }
  }

  function handleAuthMessage(event) {
    const expectedOrigin = (() => {
      try { return new URL(apiConfig.url).origin; }
      catch (_error) { return ""; }
    })();
    if (expectedOrigin && event.origin !== expectedOrigin) return;
    const data = event.data || {};
    if (data.type !== "v2m-github-login") return;
    const nextTab = activeTabFromHash();
    applyLoginResult({
      user: data.user,
      session_token: data.sessionToken,
      expires_at: data.expiresAt,
    }, nextTab);
    Promise.all([loadProjects(), loadTasks(), loadCloudProjects(), loadWorkspaceFiles()]).catch(() => {});
  }

  function consumeAuthHash() {
    const hash = window.location.hash.startsWith("#") ? window.location.hash.slice(1) : "";
    const params = new URLSearchParams(hash);
    const sessionToken = params.get("v2m_session_token");
    if (!sessionToken) return false;
    const apiUrl = params.get("v2m_api_url");
    if (apiUrl) {
      apiConfig.url = normalizeApiUrl(apiUrl);
      els.apiUrlInput.value = apiConfig.url;
    }
    const nextTab = params.get("v2m_next_tab") || "projects";
    applyLoginResult({
      user: { username: params.get("v2m_username") || "GitHub", role: "admin" },
      session_token: sessionToken,
      expires_at: params.get("v2m_expires_at") || "",
    }, nextTab);
    history.replaceState(null, "", `${window.location.pathname}${window.location.search}#${nextTab}`);
    Promise.all([loadProjects(), loadTasks(), loadCloudProjects(), loadWorkspaceFiles()]).catch(() => {});
    return true;
  }

  async function logout() {
    try {
      if (apiConfig.sessionToken) {
        await apiRequest("/api/auth/logout", { method: "POST" });
      }
    } catch (_error) {
      // Clear local state even if the API has already stopped.
    }
    apiUser = null;
    apiConfig.sessionToken = "";
    apiConfig.expiresAt = "";
    persistApiConfig();
    apiProjects = [];
    apiTasks = [];
    cloudProjects = [];
    cloudSessions = [];
    cloudMessages = [];
    cloudFiles = [];
    currentCloudSession = null;
    selectedCloudProject = "";
    selectedCloudSession = "";
    workspacePath = "";
    cloudSearchQuery = "";
    isDraftSession = false;
    stopCloudRunnerPolling();
    updateSessionInfo();
    renderApiLists();
    renderCloudWorkspace();
    renderWorkspaceFiles();
    els.workspaceFilePreview.textContent = "选择工作区文件后预览。";
    els.terminalOutput.textContent = "$ ";
    setApiStatus("已退出登录", "warn");
    setActiveTab("auth");
  }

  function applyLoginResult(result, nextTab = "projects") {
    apiUser = result.user || null;
    apiConfig.sessionToken = result.session_token || "";
    apiConfig.expiresAt = result.expires_at || "";
    persistApiConfig();
    updateSessionInfo();
    setApiStatus(apiUser ? "已登录" : "登录成功", "ok");
    setActiveTab(nextTab);
  }

  function updateSessionInfo() {
    updateIdentityBadge();
    if (!apiUser) {
      els.sessionInfo.textContent = apiConfig.sessionToken ? "正在恢复登录态..." : "尚未登录。只有登录后才能访问 Mac 控制接口。";
      return;
    }
    const expiry = apiConfig.expiresAt ? ` · 有效期至 ${apiConfig.expiresAt}` : "";
    els.sessionInfo.textContent = `${apiUser.username || apiUser.id} · ${apiUser.role || "admin"}${expiry}`;
  }

  async function loadProjects() {
    try {
      const data = await apiRequest("/api/projects");
      apiProjects = Array.isArray(data.projects) ? data.projects : [];
      renderApiLists();
    } catch (error) {
      apiProjects = [];
      renderProjectList(error.message);
    }
  }

  async function loadTasks() {
    try {
      const data = await apiRequest("/api/codex-tasks");
      apiTasks = Array.isArray(data.tasks) ? data.tasks : [];
      renderApiLists();
    } catch (error) {
      apiTasks = [];
      renderTaskList(error.message);
    }
  }

  function renderApiLists() {
    renderProjectList();
    renderTaskList();
    renderCloudWorkspace();
  }

  function renderProjectList(error = "") {
    if (error) {
      els.projectList.innerHTML = `<div class="mini-empty">项目读取失败：${escapeHtml(error)}</div>`;
      return;
    }
    if (!apiUser) {
      els.projectList.innerHTML = `<div class="mini-empty">登录后显示项目记录。</div>`;
      return;
    }
    if (!apiProjects.length) {
      els.projectList.innerHTML = `<div class="mini-empty">还没有项目记录。</div>`;
      return;
    }
    els.projectList.innerHTML = apiProjects.slice(0, 8).map((project) => `
      <div class="record-item">
        <strong>${escapeHtml(project.name || project.id || "Untitled")}</strong>
        <span>${escapeHtml(project.status || "active")} · ${escapeHtml(project.updated_at || "")}</span>
        ${project.summary ? `<p>${escapeHtml(project.summary)}</p>` : ""}
        ${project.repo ? `<code>${escapeHtml(project.repo)}</code>` : ""}
      </div>
    `).join("");
  }

  function renderTaskList(error = "") {
    if (error) {
      els.taskList.innerHTML = `<div class="mini-empty">任务读取失败：${escapeHtml(error)}</div>`;
      return;
    }
    if (!apiUser) {
      els.taskList.innerHTML = `<div class="mini-empty">登录后显示 Codex 任务队列。</div>`;
      return;
    }
    if (!apiTasks.length) {
      els.taskList.innerHTML = `<div class="mini-empty">手机或远程页面发送的 Codex 任务会出现在这里。</div>`;
      return;
    }
    els.taskList.innerHTML = apiTasks.slice(0, 10).map((task) => `
      <div class="record-item task-record">
        <div class="record-row">
          <strong>${escapeHtml(task.project || "Video2Mesh")}</strong>
          <select data-task-status="${escapeHtml(task.id || "")}" aria-label="任务状态">
            ${["queued", "running", "done", "blocked"].map((status) => `<option value="${status}" ${task.status === status ? "selected" : ""}>${status}</option>`).join("")}
          </select>
        </div>
        <p>${escapeHtml(task.prompt || "")}</p>
        <span>${escapeHtml(task.created_at || "")}</span>
        ${task.workspace_project && task.workspace_session ? `<code>workspace: ${escapeHtml(task.workspace_project)} / ${escapeHtml(task.workspace_session)}</code>` : ""}
        ${task.result_summary ? `<p>${escapeHtml(task.result_summary)}</p>` : ""}
      </div>
    `).join("");
  }

  function ensureAdmin() {
    return apiUser && String(apiUser.role || "admin").toLowerCase() === "admin";
  }

  async function loadCloudProjects() {
    if (!apiUser) {
      renderCloudWorkspace();
      return;
    }
    try {
      const data = await apiRequest("/api/codex-cloud/projects");
      cloudProjects = Array.isArray(data.projects) ? data.projects : [];
      if (selectedCloudProject && !cloudProjects.some((project) => project.id === selectedCloudProject)) {
        selectedCloudProject = "";
        selectedCloudSession = "";
        currentCloudSession = null;
        isDraftSession = false;
      }
      if (!selectedCloudProject && cloudProjects.length) {
        selectedCloudProject = cloudProjects[0].id || "";
      }
      renderCloudWorkspace();
      if (selectedCloudProject) {
        await Promise.all([
          loadCloudSessions(selectedCloudProject),
          loadWorkspaceFiles(workspacePath || selectedCloudProject),
        ]);
      }
    } catch (error) {
      cloudProjects = [];
      els.cloudProjectList.innerHTML = `<div class="mini-empty">工作区读取失败：${escapeHtml(error.message)}</div>`;
    }
  }

  async function loadCloudSessions(projectId = selectedCloudProject) {
    if (!projectId) {
      cloudSessions = [];
      currentCloudSession = null;
      renderCloudWorkspace();
      return;
    }
    try {
      const data = await apiRequest(`/api/codex-cloud/projects/${encodeURIComponent(projectId)}/sessions`);
      cloudSessions = Array.isArray(data.sessions) ? data.sessions : [];
      if (selectedCloudSession && !cloudSessions.some((session) => session.id === selectedCloudSession)) {
        selectedCloudSession = "";
        currentCloudSession = null;
        isDraftSession = false;
      }
      if (!selectedCloudSession && !isDraftSession && cloudSessions.length) {
        selectedCloudSession = cloudSessions[0].id || "";
      }
      renderCloudWorkspace();
      if (selectedCloudSession) await loadCloudSessionDetail(projectId, selectedCloudSession);
    } catch (error) {
      cloudSessions = [];
      els.cloudSessionList.innerHTML = `<div class="mini-empty">会话读取失败：${escapeHtml(error.message)}</div>`;
    }
  }

  async function loadCloudSessionDetail(projectId = selectedCloudProject, sessionId = selectedCloudSession) {
    if (!projectId || !sessionId) {
      cloudMessages = [];
      cloudFiles = [];
      currentCloudSession = null;
      renderCloudWorkspace();
      return;
    }
    try {
      const data = await apiRequest(`/api/codex-cloud/projects/${encodeURIComponent(projectId)}/sessions/${encodeURIComponent(sessionId)}`);
      cloudMessages = Array.isArray(data.messages) ? data.messages : [];
      cloudFiles = Array.isArray(data.files) ? data.files : [];
      currentCloudSession = data.session || {};
      isDraftSession = false;
      renderCloudWorkspace(currentCloudSession);
      updateCloudRunnerPolling(currentCloudSession);
    } catch (error) {
      cloudMessages = [];
      cloudFiles = [];
      currentCloudSession = null;
      els.cloudMessageList.innerHTML = `<div class="mini-empty">会话读取失败：${escapeHtml(error.message)}</div>`;
    }
  }

  function workspaceDisplayPath(path = workspacePath) {
    return path ? `CodexCloudWorkspace/${path}` : "CodexCloudWorkspace";
  }

  function parentWorkspacePath(path = workspacePath) {
    const parts = String(path || "").split("/").filter(Boolean);
    parts.pop();
    return parts.join("/");
  }

  function workspaceFileKind(entry = {}) {
    if (entry.type === "directory") return "directory";
    const name = String(entry.name || entry.path || "").toLowerCase();
    if (/\.(md|markdown)$/.test(name)) return "markdown";
    if (/\.(json|jsonl)$/.test(name)) return "json";
    if (/\.(log|txt)$/.test(name)) return "log";
    if (/\.(py|js|ts|tsx|jsx|css|html|sh|toml|yml|yaml)$/.test(name)) return "code";
    return "file";
  }

  function setWorkspacePath(path) {
    workspacePath = String(path || "").replace(/^\/+|\/+$/g, "");
    els.workspacePathLabel.textContent = workspaceDisplayPath();
    els.terminalCwdLabel.textContent = workspaceDisplayPath();
    if (els.terminalForm?.elements?.cwd) {
      els.terminalForm.elements.cwd.value = workspacePath;
    }
  }

  async function loadWorkspaceFiles(path = workspacePath) {
    if (!apiUser) {
      renderWorkspaceFiles();
      return;
    }
    if (!ensureAdmin()) {
      renderWorkspaceFiles("仅管理员可用。");
      return;
    }
    try {
      const query = path ? `?path=${encodeURIComponent(path)}` : "";
      const data = await apiRequest(`/api/codex-cloud/fs${query}`);
      setWorkspacePath(data.item?.path || "");
      renderWorkspaceFiles("", data.children || [], data.item || {});
    } catch (error) {
      renderWorkspaceFiles(error.message || "工作区读取失败");
    }
  }

  function renderWorkspaceFiles(error = "", children = [], item = null) {
    if (!els.workspaceFileList) return;
    if (!apiUser) {
      els.workspaceFileList.innerHTML = `<div class="mini-empty">登录后显示工作区文件。</div>`;
      els.workspacePathLabel.textContent = "CodexCloudWorkspace";
      els.terminalCwdLabel.textContent = "CodexCloudWorkspace";
      return;
    }
    if (error) {
      els.workspaceFileList.innerHTML = `<div class="mini-empty">工作区读取失败：${escapeHtml(error)}</div>`;
      return;
    }
    const parentButton = workspacePath ? `
      <button class="record-item workspace-file-item" data-workspace-path="${escapeHtml(parentWorkspacePath())}" data-workspace-type="directory" type="button">
        <strong>..</strong>
        <span>上级目录</span>
      </button>
    ` : "";
    const body = children.length ? children.map((entry) => `
      <button class="record-item workspace-file-item" data-workspace-path="${escapeHtml(entry.path || "")}" data-workspace-type="${escapeHtml(entry.type || "")}" data-file-kind="${escapeHtml(workspaceFileKind(entry))}" type="button">
        <strong>${escapeHtml(entry.name || entry.path || "item")}</strong>
        <span>${escapeHtml(entry.path || ".")} · ${escapeHtml(entry.type || "")}${entry.type === "file" ? ` · ${escapeHtml(entry.size || 0)} bytes` : ""}</span>
      </button>
    `).join("") : `<div class="mini-empty">当前目录为空。</div>`;
    els.workspaceFileList.innerHTML = parentButton + body;
    const nextPath = item?.path || workspacePath || "";
    els.workspacePathLabel.textContent = workspaceDisplayPath(nextPath);
    els.terminalCwdLabel.textContent = workspaceDisplayPath(nextPath);
  }

  function runnerLabel(status) {
    return {
      running: "running",
      done: "done",
      failed: "failed",
      disabled: "disabled",
      already_running: "running",
    }[status] || "idle";
  }

  function formatRelativeTime(value) {
    if (!value) return "";
    const time = Date.parse(String(value));
    if (!Number.isFinite(time)) return String(value);
    const seconds = Math.max(0, Math.round((Date.now() - time) / 1000));
    if (seconds < 60) return "刚刚";
    const minutes = Math.round(seconds / 60);
    if (minutes < 60) return `${minutes} 分钟前`;
    const hours = Math.round(minutes / 60);
    if (hours < 24) return `${hours} 小时前`;
    const days = Math.round(hours / 24);
    if (days < 30) return `${days} 天前`;
    return String(value).slice(0, 10);
  }

  function roleLabel(role) {
    return {
      user: "You",
      assistant: "Codex",
      system: "System",
      tool: "Tool",
    }[String(role || "").toLowerCase()] || String(role || "user");
  }

  function messageStatus(message) {
    return message.run_status || formatRelativeTime(message.created_at) || message.created_at || "";
  }

  function setComposerValue(value) {
    if (!els.cloudMessageForm?.elements?.content) return;
    els.cloudMessageForm.elements.content.value = value;
    els.cloudMessageForm.elements.content.focus();
  }

  function inferTaskTitle(content) {
    const firstLine = String(content || "").split(/\r?\n/).find((line) => line.trim()) || "New task";
    return firstLine.trim().replace(/^#+\s*/, "").slice(0, 56) || "New task";
  }

  function matchesSearch(value, query = cloudSearchQuery) {
    const term = String(query || "").trim().toLowerCase();
    if (!term) return true;
    return String(value || "").toLowerCase().includes(term);
  }

  function sessionLine(session) {
    const parts = [];
    parts.push(session.status || "open");
    parts.push(`${session.message_count || 0} msgs`);
    if (Number(session.file_count || 0) > 0) parts.push(`${session.file_count} files`);
    const rel = formatRelativeTime(session.updated_at || session.created_at || "");
    if (rel) parts.push(rel);
    return parts.join(" · ");
  }

  function runStripCopy(session = currentCloudSession || {}) {
    const runner = session?.codex_runner || {};
    const status = runnerLabel(runner.status || "");
    const waitingForRun = session?.last_role === "user" && status !== "running";
    const map = {
      running: ["running", "Codex 正在处理当前任务。"],
      done: ["done", "最近一次运行已完成。"],
      failed: ["failed", runner.error || "最近一次运行失败。"],
      disabled: ["disabled", "runner 未启用，消息仍会写入会话。"],
      idle: ["idle", waitingForRun ? "有用户消息等待运行，点击 Run 面板里的“运行 Codex”。" : selectedCloudSession ? "等待下一条任务。" : "创建新任务后开始运行。"],
    };
    if (waitingForRun && status === "done") return ["idle", "有新用户消息尚未运行，点击 Run 面板里的“运行 Codex”。"];
    return map[status] || map.idle;
  }

  function renderRunnerState(session = currentCloudSession || {}) {
    const runner = session?.codex_runner || {};
    const status = runnerLabel(runner.status || "");
    if (els.codexRunnerPill) {
      els.codexRunnerPill.textContent = status;
      els.codexRunnerPill.dataset.state = status;
    }
    if (els.codexRunMeta) {
      const duration = runner.duration_ms ? `${Math.round(Number(runner.duration_ms) / 1000)}s` : "";
      els.codexRunMeta.textContent = status === "idle" ? "未运行" : [status, duration].filter(Boolean).join(" · ");
    }
    if (els.codexRunCard) {
      const waitingForRun = session?.last_role === "user" && status !== "running";
      const logLine = runner.log_path ? `<code>${escapeHtml(runner.log_path)}</code>` : "";
      const lastLine = runner.last_message_path ? `<code>${escapeHtml(runner.last_message_path)}</code>` : "";
      const errorLine = runner.error ? `<span>${escapeHtml(runner.error)}</span>` : "";
      els.codexRunCard.innerHTML = `
        <strong>Codex runner</strong>
        <span>状态：${escapeHtml(waitingForRun && status === "done" ? "waiting" : status)}</span>
        ${waitingForRun ? `<span>最后一条用户消息还没有触发 Codex 运行。</span>` : ""}
        ${runner.run_id ? `<code>${escapeHtml(runner.run_id)}</code>` : ""}
        ${runner.codex_session_id ? `<code>session ${escapeHtml(runner.codex_session_id)}</code>` : ""}
        ${logLine}
        ${lastLine}
        ${errorLine}
      `;
    }
    if (els.runCodexNow) {
      els.runCodexNow.disabled = !selectedCloudProject || !selectedCloudSession || status === "running";
    }
    if (els.codexRunStrip) {
      const [label, message] = runStripCopy(session);
      els.codexRunStrip.dataset.state = label;
      els.codexRunStrip.innerHTML = `
        <span class="run-dot" aria-hidden="true"></span>
        <strong>${escapeHtml(label)}</strong>
        <span>${escapeHtml(message)}</span>
      `;
    }
    renderActivityCard(session, status);
  }

  function renderActivityCard(session = currentCloudSession || {}, runnerStatus = "idle") {
    if (!els.activitySummary) return;
    const runner = session?.codex_runner || {};
    const duration = runner.duration_ms ? `${Math.max(1, Math.round(Number(runner.duration_ms) / 1000))}s` : "";
    const updated = formatRelativeTime(runner.finished_at || runner.updated_at || session.updated_at || "");
    const summary = runnerStatus === "running"
      ? "Working..."
      : runnerStatus === "done"
      ? `Worked${duration ? ` for ${duration}` : ""}${updated ? ` · ${updated}` : ""}`
      : selectedCloudSession
      ? "Ready for follow-up"
      : "No active chat";
    els.activitySummary.textContent = summary;
    if (els.activityChangeTitle) {
      els.activityChangeTitle.textContent = cloudFiles.length ? `Edited ${cloudFiles.length} file${cloudFiles.length > 1 ? "s" : ""}` : "Session artifacts";
    }
    if (els.activityChangeMeta) {
      const latest = cloudFiles[0]?.path || runner.log_path || "No files changed yet";
      els.activityChangeMeta.textContent = latest;
    }
  }

  function stopCloudRunnerPolling() {
    if (cloudRunnerPollTimer) {
      window.clearInterval(cloudRunnerPollTimer);
      cloudRunnerPollTimer = 0;
    }
  }

  function updateCloudRunnerPolling(session = currentCloudSession || {}) {
    const runner = session?.codex_runner || {};
    if (runner.status === "running") {
      if (!cloudRunnerPollTimer) {
        cloudRunnerPollTimer = window.setInterval(() => {
          if (selectedCloudProject && selectedCloudSession) {
            loadCloudSessionDetail(selectedCloudProject, selectedCloudSession).catch(() => {});
            loadTasks().catch(() => {});
          }
        }, 3500);
      }
      return;
    }
    stopCloudRunnerPolling();
  }

  function renderCloudWorkspace(sessionDetail = null) {
    if (!els.cloudProjectList) return;
    if (!apiUser) {
      els.cloudProjectList.innerHTML = `<div class="mini-empty">登录后显示 Codex Cloud Workspace。</div>`;
      els.cloudSessionList.innerHTML = `<div class="mini-empty">尚未登录。</div>`;
      els.cloudMessageList.innerHTML = `<div class="mini-empty">管理员登录后可以与 Codex 会话。</div>`;
      els.cloudFileList.innerHTML = `<div class="mini-empty">暂无输出文件。</div>`;
      els.cloudSessionTitle.textContent = "未登录";
      els.cloudSessionMeta.textContent = "需要管理员权限。";
      if (els.cloudWorkspaceStatus) els.cloudWorkspaceStatus.textContent = "offline";
      if (els.cloudMessageCount) els.cloudMessageCount.textContent = "0 messages";
      if (els.cloudFileCount) els.cloudFileCount.textContent = "0 files";
      if (els.composerContext) els.composerContext.textContent = "登录管理员后开始";
      if (els.composerMode) els.composerMode.textContent = "需要登录";
      els.cloudFilePreview.textContent = "选择文件后预览。";
      renderRunnerState({});
      return;
    }
    if (!ensureAdmin()) {
      els.cloudProjectList.innerHTML = `<div class="mini-empty">仅管理员可用。</div>`;
      els.cloudSessionList.innerHTML = `<div class="mini-empty">仅管理员可用。</div>`;
      els.cloudMessageList.innerHTML = `<div class="mini-empty">当前账号没有管理员权限。</div>`;
      els.cloudFileList.innerHTML = `<div class="mini-empty">当前账号没有管理员权限。</div>`;
      if (els.cloudWorkspaceStatus) els.cloudWorkspaceStatus.textContent = "locked";
      if (els.cloudMessageCount) els.cloudMessageCount.textContent = "0 messages";
      if (els.cloudFileCount) els.cloudFileCount.textContent = "0 files";
      if (els.composerContext) els.composerContext.textContent = "需要管理员权限";
      if (els.composerMode) els.composerMode.textContent = "需要管理员权限";
      els.cloudFilePreview.textContent = "选择文件后预览。";
      renderRunnerState({});
      return;
    }
    if (els.cloudWorkspaceStatus) {
      els.cloudWorkspaceStatus.textContent = selectedCloudProject ? "online" : "empty";
    }
    els.cloudProjectList.innerHTML = cloudProjects.length ? cloudProjects.map((project) => `
      <button class="record-item cloud-select ${project.id === selectedCloudProject ? "active" : ""}" data-cloud-project="${escapeHtml(project.id || "")}" type="button">
        <strong>${escapeHtml(project.name || project.id || "Untitled")}</strong>
        <span>${escapeHtml(project.session_count || 0)} sessions · ${escapeHtml(formatRelativeTime(project.updated_at || project.created_at || ""))}</span>
        ${project.summary ? `<p>${escapeHtml(project.summary)}</p>` : ""}
      </button>
    `).join("") : `<div class="mini-empty">还没有云工作台项目。</div>`;

    const filteredSessions = cloudSessions.filter((session) => {
      const haystack = [session.title, session.id, session.status, session.last_message].filter(Boolean).join(" ");
      return matchesSearch(haystack);
    });
    const draftItem = isDraftSession ? `
      <button class="record-item cloud-select active draft-session-item" type="button" data-draft-session="true">
        <strong>New task</strong>
        <span>draft · not saved yet</span>
        <p>输入第一条消息后自动创建会话。</p>
      </button>
    ` : "";
    const sessionListBody = filteredSessions.length ? filteredSessions.map((session) => `
      <button class="record-item cloud-select ${session.id === selectedCloudSession ? "active" : ""}" data-cloud-session="${escapeHtml(session.id || "")}" type="button">
        <strong>${escapeHtml(session.title || session.id || "Untitled")}</strong>
        <span>${escapeHtml(sessionLine(session))}</span>
        ${session.last_message ? `<p>${escapeHtml(session.last_message)}</p>` : ""}
      </button>
    `).join("") : `<div class="mini-empty">${cloudSearchQuery ? "没有匹配的会话。" : "这个项目还没有会话。"}</div>`;
    els.cloudSessionList.innerHTML = draftItem + sessionListBody;

    const activeSession = sessionDetail || currentCloudSession || cloudSessions.find((item) => item.id === selectedCloudSession) || {};
    els.cloudSessionTitle.textContent = isDraftSession ? "New task" : (activeSession.title || selectedCloudSession || "未选择会话");
    els.cloudSessionMeta.textContent = isDraftSession
      ? `${selectedCloudProject || "workspace"} / draft`
      : selectedCloudProject
      ? `${selectedCloudProject}${selectedCloudSession ? ` / ${selectedCloudSession}` : ""}`
      : "选择或新建一个项目。";
    if (els.cloudWorkspaceChip) {
      els.cloudWorkspaceChip.textContent = selectedCloudProject || "workspace";
    }
    if (els.cloudMessageCount) {
      els.cloudMessageCount.textContent = `${cloudMessages.length || Number(activeSession.message_count || 0)} messages`;
    }
    if (els.cloudFileCount) {
      els.cloudFileCount.textContent = `${cloudFiles.length || Number(activeSession.file_count || 0)} files`;
    }
    if (els.composerContext) {
      els.composerContext.textContent = selectedCloudProject
        ? `Codex 将在 ${workspaceDisplayPath(selectedCloudProject)} 运行`
        : "选择 workspace 后开始";
    }
    if (els.composerMode) {
      els.composerMode.textContent = isDraftSession ? "发送后创建会话 · Cmd/Ctrl+Enter" : "Cmd/Ctrl+Enter 发送";
    }
    renderRunnerState(isDraftSession ? {} : activeSession);

    els.cloudMessageList.innerHTML = !isDraftSession && cloudMessages.length ? cloudMessages.map((message) => `
      <div class="cloud-message ${escapeHtml(message.role || "user")}">
        <div class="cloud-message-meta">
          <strong>${escapeHtml(roleLabel(message.role))}</strong>
          <span>${escapeHtml(messageStatus(message))}</span>
        </div>
        <pre>${escapeHtml(message.content || "")}</pre>
        ${message.run_log ? `<code class="message-run-log">${escapeHtml(message.run_log)}</code>` : ""}
      </div>
    `).join("") : `
      <div class="codex-empty-chat">
        <strong>${isDraftSession ? "What should Codex work on?" : selectedCloudSession ? "准备好让 Codex 开工" : "选择或创建一个会话"}</strong>
        <span>${isDraftSession ? "像 Codex Web 一样，直接描述任务。发送后会自动创建 session，并把文件和日志写入当前 workspace。" : selectedCloudSession ? "发送消息后，Codex 会在当前 workspace 里运行并把回复、日志和文件写回这里。" : "左侧选择 workspace，然后点击 New task。每个 session 都有独立消息和输出文件。"}</span>
      </div>
    `;
    els.cloudMessageList.scrollTop = els.cloudMessageList.scrollHeight;

    els.cloudFileList.innerHTML = cloudFiles.length ? cloudFiles.map((file) => `
      <button class="record-item cloud-file-item" data-cloud-file="${escapeHtml(file.path || "")}" type="button">
        <strong>${escapeHtml(file.name || file.path || "file")}</strong>
        <span>${escapeHtml(file.path || "")} · ${escapeHtml(file.size || 0)} bytes</span>
        ${file.summary ? `<p>${escapeHtml(file.summary)}</p>` : ""}
      </button>
    `).join("") : `<div class="mini-empty">Codex 输出文件会显示在这里。</div>`;
  }

  async function createCloudProject(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = Object.fromEntries(new FormData(form).entries());
    try {
      setApiStatus("创建工作台项目...", "busy");
      const result = await apiRequest("/api/codex-cloud/projects", { method: "POST", body: JSON.stringify(data) });
      selectedCloudProject = result.project?.id || "";
      selectedCloudSession = "";
      currentCloudSession = null;
      form.reset();
      setApiStatus("工作台项目已创建", "ok");
      await Promise.all([loadCloudProjects(), loadWorkspaceFiles(selectedCloudProject)]);
    } catch (error) {
      setApiStatus(error.message || "项目创建失败", "error");
    }
  }

  async function createCloudSession(event) {
    event.preventDefault();
    if (!selectedCloudProject) {
      setApiStatus("请先选择项目", "warn");
      return;
    }
    const form = event.currentTarget;
    const data = Object.fromEntries(new FormData(form).entries());
    try {
      setApiStatus("创建 Codex 会话...", "busy");
      const result = await apiRequest(`/api/codex-cloud/projects/${encodeURIComponent(selectedCloudProject)}/sessions`, {
        method: "POST",
        body: JSON.stringify(data),
      });
      selectedCloudSession = result.session?.id || "";
      isDraftSession = false;
      form.reset();
      setApiStatus("Codex 会话已创建", "ok");
      await Promise.all([loadCloudProjects(), loadWorkspaceFiles(workspacePath || selectedCloudProject)]);
    } catch (error) {
      setApiStatus(error.message || "会话创建失败", "error");
    }
  }

  async function sendCloudMessage(event) {
    event.preventDefault();
    if (!selectedCloudProject) {
      setApiStatus("请先选择 workspace", "warn");
      return;
    }
    const form = event.currentTarget;
    const data = Object.fromEntries(new FormData(form).entries());
    const submitButton = form.querySelector("button[type='submit']");
    const content = String(data.content || "").trim();
    if (!content) {
      setApiStatus("请输入消息", "warn");
      return;
    }
    try {
      setApiStatus("Codex 正在运行...", "busy");
      if (submitButton) submitButton.disabled = true;
      if (!selectedCloudSession || isDraftSession) {
        const created = await apiRequest(`/api/codex-cloud/projects/${encodeURIComponent(selectedCloudProject)}/sessions`, {
          method: "POST",
          body: JSON.stringify({ title: inferTaskTitle(content) }),
        });
        selectedCloudSession = created.session?.id || "";
        if (!selectedCloudSession) throw new Error("会话创建失败");
        isDraftSession = false;
      }
      const result = await apiRequest(`/api/codex-cloud/projects/${encodeURIComponent(selectedCloudProject)}/sessions/${encodeURIComponent(selectedCloudSession)}/messages`, {
        method: "POST",
        body: JSON.stringify({ role: "user", content, enqueue_task: true, run_codex: true }),
      });
      form.reset();
      if (result.runner?.status === "running") {
        setApiStatus("消息已发送，Codex 正在生成", "busy");
        currentCloudSession = {
          ...(currentCloudSession || {}),
          last_role: "user",
          codex_runner: result.runner,
        };
        renderRunnerState(currentCloudSession);
        updateCloudRunnerPolling(currentCloudSession);
        setInspectorTab("run");
      } else {
        setApiStatus(result.runner?.status === "disabled" ? "消息已发送，runner 未启用" : "消息已发送", "ok");
      }
      await Promise.all([loadCloudSessions(selectedCloudProject), loadTasks(), loadWorkspaceFiles(workspacePath || selectedCloudProject)]);
    } catch (error) {
      setApiStatus(error.message || "消息发送失败", "error");
    } finally {
      if (submitButton) submitButton.disabled = false;
    }
  }

  async function runCurrentCodexSession() {
    if (!selectedCloudProject || !selectedCloudSession) {
      setApiStatus("请先选择会话", "warn");
      return;
    }
    try {
      setApiStatus("正在启动 Codex...", "busy");
      if (els.runCodexNow) els.runCodexNow.disabled = true;
      const result = await apiRequest(`/api/codex-cloud/projects/${encodeURIComponent(selectedCloudProject)}/sessions/${encodeURIComponent(selectedCloudSession)}/run`, {
        method: "POST",
        body: JSON.stringify({}),
      });
      currentCloudSession = {
        ...(currentCloudSession || {}),
        last_role: "user",
        codex_runner: result.runner || {},
      };
      renderRunnerState(currentCloudSession);
      updateCloudRunnerPolling(currentCloudSession);
      setInspectorTab("run");
      setApiStatus(result.runner?.status === "running" ? "Codex 已启动" : `Codex 状态：${result.runner?.status || "unknown"}`, result.runner?.status === "running" ? "busy" : "warn");
      await Promise.all([loadCloudSessionDetail(selectedCloudProject, selectedCloudSession), loadTasks()]);
    } catch (error) {
      setApiStatus(friendlyFetchError(error, "Codex 启动失败"), "error");
    } finally {
      if (els.runCodexNow) els.runCodexNow.disabled = false;
    }
  }

  async function writeCloudFile(event) {
    event.preventDefault();
    if (!selectedCloudProject || !selectedCloudSession) {
      setApiStatus("请先选择会话", "warn");
      return;
    }
    const form = event.currentTarget;
    const data = Object.fromEntries(new FormData(form).entries());
    try {
      setApiStatus("写入输出文件...", "busy");
      const result = await apiRequest(`/api/codex-cloud/projects/${encodeURIComponent(selectedCloudProject)}/sessions/${encodeURIComponent(selectedCloudSession)}/files`, {
        method: "POST",
        body: JSON.stringify(data),
      });
      form.reset();
      setApiStatus(`文件已写入：${result.file?.path || data.path}`, "ok");
      await Promise.all([loadCloudSessions(selectedCloudProject), loadWorkspaceFiles(workspacePath || selectedCloudProject)]);
    } catch (error) {
      setApiStatus(error.message || "文件写入失败", "error");
    }
  }

  async function selectCloudProject(event) {
    const button = event.target.closest("[data-cloud-project]");
    if (!button) return;
    selectedCloudProject = button.dataset.cloudProject || "";
    selectedCloudSession = "";
    currentCloudSession = null;
    isDraftSession = false;
    cloudMessages = [];
    cloudFiles = [];
    els.cloudFilePreview.textContent = "选择文件后预览。";
    renderCloudWorkspace();
    await Promise.all([loadCloudSessions(selectedCloudProject), loadWorkspaceFiles(selectedCloudProject)]);
  }

  async function selectCloudSession(event) {
    const button = event.target.closest("[data-cloud-session]");
    if (!button) return;
    selectedCloudSession = button.dataset.cloudSession || "";
    currentCloudSession = cloudSessions.find((item) => item.id === selectedCloudSession) || null;
    isDraftSession = false;
    els.cloudFilePreview.textContent = "选择文件后预览。";
    renderCloudWorkspace();
    await loadCloudSessionDetail();
  }

  function focusNewSessionForm() {
    if (!selectedCloudProject) {
      setApiStatus("请先选择 workspace", "warn");
      return;
    }
    const details = els.cloudSessionForm?.closest("details");
    if (details) details.open = true;
    els.cloudSessionForm?.elements?.title?.focus();
  }

  function startNewTask() {
    if (!selectedCloudProject) {
      setApiStatus("请先选择 workspace", "warn");
      return;
    }
    selectedCloudSession = "";
    currentCloudSession = null;
    cloudMessages = [];
    cloudFiles = [];
    isDraftSession = true;
    els.cloudFilePreview.textContent = "选择文件后预览。";
    renderCloudWorkspace();
    setComposerValue("");
    setApiStatus("新任务已准备好", "ok");
  }

  function updateCloudSearch(event) {
    cloudSearchQuery = String(event.target.value || "");
    renderCloudWorkspace(currentCloudSession);
  }

  function clearCloudSearch() {
    cloudSearchQuery = "";
    if (els.cloudSearchInput) els.cloudSearchInput.value = "";
    renderCloudWorkspace(currentCloudSession);
    els.cloudSearchInput?.focus();
  }

  function openCurrentWorkspace() {
    if (!selectedCloudProject) {
      setApiStatus("请先选择 workspace", "warn");
      return;
    }
    setInspectorTab("workspace");
    loadWorkspaceFiles(selectedCloudProject).catch(() => {});
  }

  function focusCloudSearch() {
    els.cloudSearchInput?.focus();
    els.cloudSearchInput?.select?.();
  }

  function showRunPanel() {
    setInspectorTab("run");
  }

  function showArtifactsPanel() {
    setInspectorTab("artifacts");
  }

  function toggleActivityCard() {
    const card = els.activityToggle?.closest(".codex-activity-card");
    if (!card) return;
    card.classList.toggle("collapsed");
  }

  function usePromptSuggestion(event) {
    const button = event.target.closest("[data-prompt]");
    if (!button) return;
    setComposerValue(button.dataset.prompt || "");
  }

  function handleComposerKeydown(event) {
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
      event.preventDefault();
      if (els.cloudMessageForm.requestSubmit) els.cloudMessageForm.requestSubmit();
      else els.cloudMessageForm.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
    }
  }

  async function previewCloudFile(event) {
    const button = event.target.closest("[data-cloud-file]");
    if (!button || !selectedCloudProject || !selectedCloudSession) return;
    const path = button.dataset.cloudFile || "";
    try {
      setApiStatus("读取输出文件...", "busy");
      const baseUrl = apiBaseUrl();
      const encodedPath = path.split("/").map(encodeURIComponent).join("/");
      const response = await fetch(`${baseUrl}/api/codex-cloud/projects/${encodeURIComponent(selectedCloudProject)}/sessions/${encodeURIComponent(selectedCloudSession)}/files/${encodedPath}`, {
        headers: { Authorization: `Bearer ${apiConfig.sessionToken}` },
      });
      const text = await response.text();
      if (!response.ok) {
        let message = text || `${response.status} ${response.statusText}`;
        try {
          message = JSON.parse(text).error || message;
        } catch (_error) {
          // Non-JSON errors can be shown as-is.
        }
        throw new Error(message);
      }
      els.cloudFilePreview.textContent = text || "(empty file)";
      setApiStatus("文件已预览", "ok");
    } catch (error) {
      els.cloudFilePreview.textContent = error.message || "文件读取失败";
      setApiStatus(error.message || "文件读取失败", "error");
    }
  }

  async function selectWorkspaceItem(event) {
    const button = event.target.closest("[data-workspace-path]");
    if (!button) return;
    const path = button.dataset.workspacePath || "";
    const type = button.dataset.workspaceType || "";
    if (type === "directory") {
      els.workspaceFilePreview.textContent = "选择工作区文件后预览。";
      await loadWorkspaceFiles(path);
      return;
    }
    if (type === "file") {
      await previewWorkspaceFile(path);
    }
  }

  async function previewWorkspaceFile(path) {
    try {
      setApiStatus("读取工作区文件...", "busy");
      const data = await apiRequest(`/api/codex-cloud/fs?path=${encodeURIComponent(path)}&preview=1`);
      const label = data.item?.path ? workspaceDisplayPath(data.item.path) : workspaceDisplayPath();
      if (data.preview_error) {
        els.workspaceFilePreview.textContent = `${label}\n\n${data.preview_error}`;
      } else {
        els.workspaceFilePreview.textContent = `${label}\n\n${data.preview || "(empty file)"}`;
      }
      setApiStatus("工作区文件已预览", "ok");
    } catch (error) {
      els.workspaceFilePreview.textContent = error.message || "文件读取失败";
      setApiStatus(error.message || "文件读取失败", "error");
    }
  }

  async function goWorkspaceUp() {
    await loadWorkspaceFiles(parentWorkspacePath());
  }

  async function runTerminalCommand(event) {
    event.preventDefault();
    if (!apiUser || !ensureAdmin()) {
      setApiStatus("仅管理员可用", "warn");
      return;
    }
    const form = event.currentTarget;
    const data = Object.fromEntries(new FormData(form).entries());
    const cwd = String(data.cwd || workspacePath || "");
    const command = String(data.command || "").trim();
    if (!command) {
      setApiStatus("请输入命令", "warn");
      return;
    }
    try {
      setApiStatus("终端命令运行中...", "busy");
      els.terminalOutput.textContent = `$ ${command}\n\nrunning...`;
      const result = await apiRequest("/api/codex-cloud/terminal", {
        method: "POST",
        body: JSON.stringify({ cwd, command, timeout_seconds: 20 }),
      });
      setWorkspacePath(result.cwd || cwd);
      const statusLine = `[exit ${result.returncode}] ${result.duration_ms || 0}ms${result.timed_out ? " · timeout" : ""}${result.truncated ? " · truncated" : ""}`;
      els.terminalOutput.textContent = `${workspaceDisplayPath(result.cwd || cwd)}\n$ ${command}\n${statusLine}\n\n${result.output || ""}`;
      setApiStatus(result.returncode === 0 ? "终端命令完成" : `终端返回 ${result.returncode}`, result.returncode === 0 ? "ok" : "warn");
      await loadWorkspaceFiles(result.cwd || cwd);
    } catch (error) {
      els.terminalOutput.textContent = `$ ${command}\n\n${error.message || "命令运行失败"}`;
      setApiStatus(error.message || "命令运行失败", "error");
    }
  }

  async function createProjectFromForm(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = Object.fromEntries(new FormData(form).entries());
    try {
      setApiStatus("写入项目...", "busy");
      await apiRequest("/api/projects", { method: "POST", body: JSON.stringify(data) });
      form.reset();
      setApiStatus("项目已添加", "ok");
      await loadProjects();
    } catch (error) {
      setApiStatus(error.message || "项目写入失败", "error");
    }
  }

  async function createTaskFromForm(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = Object.fromEntries(new FormData(form).entries());
    try {
      setApiStatus("任务入队...", "busy");
      await apiRequest("/api/codex-tasks", { method: "POST", body: JSON.stringify(data) });
      form.reset();
      form.elements.project.value = data.project || "Video2Mesh";
      form.elements.priority.value = data.priority || "normal";
      setApiStatus("任务已加入队列", "ok");
      await loadTasks();
    } catch (error) {
      setApiStatus(error.message || "任务入队失败", "error");
    }
  }

  async function syncRemoteDocFromForm(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const raw = Object.fromEntries(new FormData(form).entries());
    const data = {
      title: String(raw.title || ""),
      category: String(raw.category || "Remote"),
      summary: String(raw.summary || ""),
      tags: String(raw.tags || "")
        .split(",")
        .map((tag) => tag.trim())
        .filter(Boolean),
      markdown: String(raw.markdown || ""),
    };
    try {
      setApiStatus("同步 Markdown...", "busy");
      const result = await apiRequest("/api/docs", { method: "POST", body: JSON.stringify(data) });
      setApiStatus(`已同步：${result.path || data.title}`, "ok");
      form.reset();
      form.elements.category.value = "Remote";
    } catch (error) {
      setApiStatus(error.message || "Markdown 同步失败", "error");
    }
  }

  async function updateTaskStatus(event) {
    const select = event.target;
    if (!(select instanceof HTMLSelectElement) || !select.matches("[data-task-status]")) return;
    const id = select.dataset.taskStatus;
    if (!id) return;
    try {
      setApiStatus("更新任务状态...", "busy");
      await apiRequest(`/api/codex-tasks/${encodeURIComponent(id)}`, {
        method: "PATCH",
        body: JSON.stringify({ status: select.value }),
      });
      setApiStatus("任务状态已更新", "ok");
      await loadTasks();
    } catch (error) {
      setApiStatus(error.message || "任务更新失败", "error");
    }
  }

  function init() {
    els.apiUrlInput.value = apiConfig.url || DEFAULT_API_URL;
    updateSessionInfo();
    renderApiLists();
    if (isFilePreview()) {
      setApiStatus(`请用本地 HTTP 服务打开：${localServerUrl()}`, "warn");
    } else {
      setApiStatus(apiConfig.sessionToken ? "检查登录态..." : "需要登录", apiConfig.sessionToken ? "busy" : "warn");
    }
    setActiveTab(activeTabFromHash());
    setInspectorTab("workspace");
    const consumedHash = consumeAuthHash();
    if (apiConfig.sessionToken && !consumedHash) restoreSession();
  }

  els.tabs.forEach((tab) => {
    tab.addEventListener("click", () => setActiveTab(tab.dataset.adminTab || "auth"));
  });
  els.apiUrlInput.addEventListener("change", persistApiConfig);
  els.apiHealthCheck.addEventListener("click", checkApiHealth);
  els.setupForm.addEventListener("submit", setupAdminFromForm);
  els.loginForm.addEventListener("submit", loginFromForm);
  els.githubLoginButton.addEventListener("click", loginWithGitHub);
  els.logoutButton.addEventListener("click", logout);
  els.refreshProjects.addEventListener("click", loadProjects);
  els.refreshTasks.addEventListener("click", loadTasks);
  els.projectForm.addEventListener("submit", createProjectFromForm);
  els.taskForm.addEventListener("submit", createTaskFromForm);
  els.remoteDocForm.addEventListener("submit", syncRemoteDocFromForm);
  els.taskList.addEventListener("change", updateTaskStatus);
  els.refreshCloudWorkspace.addEventListener("click", loadCloudProjects);
  els.railNewChat.addEventListener("click", startNewTask);
  els.railSearchFocus.addEventListener("click", focusCloudSearch);
  els.railRunFocus.addEventListener("click", showRunPanel);
  els.cloudSearchInput.addEventListener("input", updateCloudSearch);
  els.clearCloudSearch.addEventListener("click", clearCloudSearch);
  els.primaryNewSession.addEventListener("click", startNewTask);
  els.threadNewTask.addEventListener("click", startNewTask);
  els.newSessionShortcut.addEventListener("click", focusNewSessionForm);
  els.cloudProjectForm.addEventListener("submit", createCloudProject);
  els.cloudSessionForm.addEventListener("submit", createCloudSession);
  els.cloudMessageForm.addEventListener("submit", sendCloudMessage);
  els.cloudMessageForm.elements.content.addEventListener("keydown", handleComposerKeydown);
  els.promptSuggestions.addEventListener("click", usePromptSuggestion);
  els.activityOpenWorkspace.addEventListener("click", openCurrentWorkspace);
  els.activityReview.addEventListener("click", showArtifactsPanel);
  els.activityToggle.addEventListener("click", toggleActivityCard);
  els.clearComposer.addEventListener("click", () => setComposerValue(""));
  els.attachWorkspaceButton.addEventListener("click", openCurrentWorkspace);
  els.cloudFileForm.addEventListener("submit", writeCloudFile);
  els.cloudProjectList.addEventListener("click", selectCloudProject);
  els.cloudSessionList.addEventListener("click", selectCloudSession);
  els.cloudFileList.addEventListener("click", previewCloudFile);
  els.refreshWorkspaceFiles.addEventListener("click", () => loadWorkspaceFiles(workspacePath));
  els.workspaceUpButton.addEventListener("click", goWorkspaceUp);
  els.workspaceFileList.addEventListener("click", selectWorkspaceItem);
  els.terminalForm.addEventListener("submit", runTerminalCommand);
  els.runCodexNow.addEventListener("click", runCurrentCodexSession);
  els.inspectorTabs.forEach((tab) => {
    tab.addEventListener("click", () => setInspectorTab(tab.dataset.inspectorTab || "artifacts"));
  });
  window.addEventListener("message", handleAuthMessage);
  window.addEventListener("hashchange", () => {
    if (window.location.hash.includes("v2m_session_token")) {
      consumeAuthHash();
      return;
    }
    setActiveTab(activeTabFromHash());
  });

  init();
})();
