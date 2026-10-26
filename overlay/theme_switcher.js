/**
 * Jenna Theme Switcher — Client-side theme management
 * Loads Omarchy themes, applies CSS variables, syncs with system theme
 */
class JennaThemeSwitcher {
  constructor(options = {}) {
    this.apiBase = options.apiBase || "/api";
    this.onChange = options.onChange || (() => {});
    this.currentTheme = null;
    this.syncWithSystem = false;
    this.panel = null;
    this.triggerBtn = null;
    this.themes = [];
    this.mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
  }

  async init() {
    await this.loadThemes();
    this.currentTheme = this.getStoredTheme() || this.detectSystemTheme();
    this.applyTheme(this.currentTheme);
    this.buildPanel();
    this.bindEvents();
    this.startSystemSync();
  }

  async loadThemes() {
    try {
      const res = await fetch(`${this.apiBase}/themes`);
      this.themes = await res.json();
    } catch {
      // Fallback: hardcoded list from registry
      this.themes = [
        { name: "catppuccin", mode: "dark", accent: "#89b4fa", background: "#1e1e2e" },
        { name: "tokyo-night", mode: "dark", accent: "#7aa2f7", background: "#1a1b26" },
        { name: "gruvbox", mode: "dark", accent: "#7daea3", background: "#282828" },
        { name: "nord", mode: "dark", accent: "#81a1c1", background: "#2e3440" },
        { name: "rose-pine", mode: "light", accent: "#56949f", background: "#faf4ed" },
        { name: "ethereal", mode: "dark", accent: "#7d82d9", background: "#060B1E" },
        { name: "quattro", mode: "dark", accent: "#7aa2f7", background: "#1a1b26" },
      ];
    }
  }

  detectSystemTheme() {
    // Check if Omarchy theme is detectable via CSS custom property
    const root = getComputedStyle(document.documentElement);
    const omarchyAccent = root.getPropertyValue("--omarchy-accent").trim();
    if (omarchyAccent) {
      const match = this.themes.find(t => t.accent === omarchyAccent);
      if (match) return match.name;
    }
    // Fallback to OS preference
    return this.mediaQuery.matches ? "catppuccin" : "rose-pine";
  }

  getStoredTheme() {
    try {
      return localStorage.getItem("jenna-theme");
    } catch {
      return null;
    }
  }

  setStoredTheme(name) {
    try {
      localStorage.setItem("jenna-theme", name);
    } catch {}
  }

  applyTheme(themeName) {
    const theme = this.themes.find(t => t.name === themeName);
    if (!theme) return false;

    this.currentTheme = themeName;
    this.setStoredTheme(themeName);

    // Fetch CSS variables from server (or compute client-side)
    this.fetchThemeCSS(themeName).then(css => {
      this.injectCSS(css);
      this.updatePanelUI();
      this.onChange(themeName, theme);
    });

    return true;
  }

  async fetchThemeCSS(themeName) {
    try {
      const res = await fetch(`${this.apiBase}/themes/${themeName}/css`);
      return await res.text();
    } catch {
      // Client-side fallback: generate minimal CSS vars
      const theme = this.themes.find(t => t.name === themeName);
      return this.generateCSSVars(theme);
    }
  }

  generateCSSVars(theme) {
    if (!theme) return "";
    const isDark = theme.mode === "dark";
    // Minimal mapping - server should provide full mapping
    const vars = {
      "--jenna-bg-base": isDark ? "#0A0B0D" : "#FAF4ED",
      "--jenna-bg-surface": isDark ? "#101215" : "#F2E9E1",
      "--jenna-bg-raised": isDark ? "#15181C" : "#E1DBD5",
      "--jenna-hairline": isDark ? "rgba(255,255,255,0.07)" : "rgba(0,0,0,0.08)",
      "--jenna-hairline-strong": isDark ? "rgba(255,255,255,0.13)" : "rgba(0,0,0,0.14)",
      "--jenna-ink-1": isDark ? "#F2F4F7" : "#575279",
      "--jenna-ink-2": isDark ? "#9AA3AE" : "#9893A5",
      "--jenna-ink-3": isDark ? "#5C6570" : "#CECACD",
      "--jenna-accent": theme.accent,
      "--jenna-state-listening": theme.cyan || "#22D3EE",
      "--jenna-state-thinking": theme.yellow || "#F59E0B",
      "--jenna-state-ready": theme.green || "#10B981",
      "--jenna-state-fault": theme.red || "#DC143C",
      "--jenna-mode": theme.mode,
    };
    return Object.entries(vars).map(([k, v]) => `${k}: ${v};`).join("\n");
  }

  injectCSS(cssText) {
    let styleEl = document.getElementById("jenna-theme-vars");
    if (!styleEl) {
      styleEl = document.createElement("style");
      styleEl.id = "jenna-theme-vars";
      document.head.appendChild(styleEl);
    }
    styleEl.textContent = `:root { ${cssText} }`;
  }

  buildPanel() {
    this.panel = document.createElement("div");
    this.panel.className = "jenna-theme-switcher";
    this.panel.innerHTML = this.panelHTML();
    document.body.appendChild(this.panel);

    // Find or create trigger button
    this.triggerBtn = document.querySelector("[data-jenna-theme-trigger]");
    if (!this.triggerBtn) {
      this.triggerBtn = document.createElement("button");
      this.triggerBtn.setAttribute("data-jenna-theme-trigger", "");
      this.triggerBtn.className = "jenna-theme-trigger";
      this.triggerBtn.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="5"/>
          <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
        </svg>
        <span class="jenna-theme-trigger__label">Theme</span>
      `;
      // Insert into telemetry bar or header
      const bar = document.querySelector(".jenna-telemetry-bar, header, nav");
      if (bar) bar.appendChild(this.triggerBtn);
      else document.body.appendChild(this.triggerBtn);
    }
  }

  panelHTML() {
    const current = this.themes.find(t => t.name === this.currentTheme) || this.themes[0];
    return `
      <div class="jenna-theme-switcher__header">
        <span class="jenna-theme-switcher__title">Theme</span>
        <button class="jenna-theme-switcher__close" data-close>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
      <div class="jenna-theme-switcher__current">
        <div class="jenna-theme-switcher__current-swatch" style="background:${current.accent}"></div>
        <span class="jenna-theme-switcher__current-name">${current.name}</span>
        <span class="jenna-theme-switcher__mode" style="text-transform:uppercase;font-size:9px;color:var(--jenna-ink-3)">${current.mode}</span>
      </div>
      <div class="jenna-theme-switcher__list" data-list>
        ${this.themes.map(t => `
          <button class="jenna-theme-option ${t.name === this.currentTheme ? 'active' : ''}" data-theme="${t.name}">
            <div class="jenna-theme-option__swatch" style="background:${t.accent}"></div>
            <div class="jenna-theme-option__info">
              <div class="jenna-theme-option__name">${t.name}</div>
              <div class="jenna-theme-option__meta">
                <span class="jenna-theme-option__mode">${t.mode}</span>
                <span>●</span>
                <span style="color:${t.accent}">accent</span>
              </div>
            </div>
          </button>
        `).join("")}
      </div>
      <div class="jenna-theme-switcher__sync">
        <span class="jenna-theme-switcher__sync-label">Sync with Omarchy</span>
        <button class="jenna-theme-switcher__sync-toggle ${this.syncWithSystem ? 'active' : ''}" data-sync-toggle></button>
      </div>
    `;
  }

  bindEvents() {
    // Trigger button
    this.triggerBtn.addEventListener("click", () => this.togglePanel());

    // Panel events
    this.panel.querySelector("[data-close]").addEventListener("click", () => this.closePanel());
    this.panel.querySelector("[data-list]").addEventListener("click", e => {
      const btn = e.target.closest("[data-theme]");
      if (btn) this.applyTheme(btn.dataset.theme);
    });
    this.panel.querySelector("[data-sync-toggle]").addEventListener("click", e => {
      this.syncWithSystem = !this.syncWithSystem;
      e.currentTarget.classList.toggle("active", this.syncWithSystem);
      if (this.syncWithSystem) this.syncToSystemTheme();
    });

    // Click outside to close
    document.addEventListener("click", e => {
      if (!this.panel.contains(e.target) && !this.triggerBtn.contains(e.target)) {
        this.closePanel();
      }
    });

    // ESC to close
    document.addEventListener("keydown", e => {
      if (e.key === "Escape") this.closePanel();
    });
  }

  togglePanel() {
    this.panel.classList.toggle("open");
  }

  closePanel() {
    this.panel.classList.remove("open");
  }

  updatePanelUI() {
    const current = this.themes.find(t => t.name === this.currentTheme);
    if (!current) return;

    this.panel.querySelector(".jenna-theme-switcher__current-swatch").style.background = current.accent;
    this.panel.querySelector(".jenna-theme-switcher__current-name").textContent = current.name;
    this.panel.querySelector(".jenna-theme-switcher__mode").textContent = current.mode;

    this.panel.querySelectorAll(".jenna-theme-option").forEach(btn => {
      btn.classList.toggle("active", btn.dataset.theme === this.currentTheme);
    });
  }

  startSystemSync() {
    this.mediaQuery.addEventListener("change", () => {
      if (this.syncWithSystem) this.syncToSystemTheme();
    });
  }

  async syncToSystemTheme() {
    try {
      const res = await fetch(`${this.apiBase}/themes/current`);
      const data = await res.json();
      if (data.theme && data.theme !== this.currentTheme) {
        this.applyTheme(data.theme);
      }
    } catch {
      // Fallback to OS preference
      const fallback = this.mediaQuery.matches ? "catppuccin" : "rose-pine";
      if (fallback !== this.currentTheme) this.applyTheme(fallback);
    }
  }
}

// Auto-init if not in a module context
if (typeof window !== "undefined" && !window.JennaThemeSwitcher) {
  window.JennaThemeSwitcher = JennaThemeSwitcher;
  document.addEventListener("DOMContentLoaded", () => {
    window.jennaThemeSwitcher = new JennaThemeSwitcher();
    window.jennaThemeSwitcher.init();
  });
}

export { JennaThemeSwitcher };