/**
 * Tecnoemprende & Jota Beta — Universal Headless Spy Telemetry Engine v5
 * (Deep Passive Visitor Intelligence + Anti-Bot + Zero On-Site UI)
 *
 * STRICT PRIVACY & VISIBILITY INVARIANTS:
 *  1. 100% INVISIBLE ON WEBSITES: Never renders any panel, badge, modal, or overlay on any webpage
 *     (not even with ?admin=david, ?view=spy, or Alt+S). All telemetry is visible EXCLUSIVELY inside Jota Beta (/#/espia).
 *  2. ZERO BROWSER ALERTS / ZERO PERMISSION POPUPS: Uses only 100% passive standard APIs
 *     (IntersectionObserver, Scroll, Selection/Copy on page, WebGL renderer, Intl TimeZone, Navigator Languages/Hardware, Passive IP/ISP).
 *  3. Automatic Exclusion of David's IPs (IPv4 & IPv6) and Admin Browser IDs.
 *  4. Mandatory Real Human Proof-of-Interaction + 4-Second Dwell Gate.
 */
(function () {
  const CONFIG = {
    supabaseUrl: 'https://jyrqzjctkmzdvmraqrcv.supabase.co',
    supabaseKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp5cnF6amN0a216ZHZtcmFxcmN2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NjI4MTU3NCwiZXhwIjoyMTAxODU3NTc0fQ.jpzy38i_JqhKiLZwNFXESJo62kk4vWvwCVPLpFIyLjc',
    heartbeatIntervalMs: 15000,
    minHumanDwellMs: 4000,
    excludedIps: [
      '94.59.222.46',
      '92.99.182.224',
      '2001:8f8:2d49:ae62::ba15:f701',
      '74.179.67.173',
      '80.82.77.202',
      '93.174.93.34',
      '45.132.195.24',
      '45.86.18.148'
    ],
    excludedIpPrefixes: [
      '94.59.222.',
      '92.99.182.',
      '2001:8f8:2d49:ae62',
      '66.249.',
      '34.203.',
      '3.239.',
      '52.207.',
      '104.154.',
      '2a03:2880:'
    ],
    excludedVisitorIds: [
      'usr_0ed586a2-f30',
      'usr_7e22d322-49a',
      'usr_a58ff49e-37f'
    ],
    datacenterKeywords: [
      'amazon', 'aws', 'google cloud', 'google llc', 'microsoft', 'azure',
      'digitalocean', 'hetzner', 'ovh', 'choopa', 'vultr', 'linode', 'akamai',
      'censys', 'shodan', 'leaseweb', 'm247', 'datacamp', 'cloudflare', 'fastly',
      'facebook', 'meta platforms', 'quasi networks', 'frantech', 'contabo',
      'tzulo', 'performive', 'multacom', 'scaleway', 'upcloud',
      'alibaba', 'tencent', 'oracle cloud', 'ibm cloud', 'hosting', 'datacenter',
      'server', 'colocation', 'vpn', 'proxy'
    ]
  };

  // Remove any legacy on-page panel immediately and permanently
  function purgeAnyOnSiteUi() {
    const ids = ['tecno-universal-spy-panel', 'spy-floating-panel', 'jota-spy-overlay'];
    ids.forEach((id) => {
      const el = document.getElementById(id);
      if (el) el.remove();
    });
  }

  function isAutomatedBotEnv() {
    const ua = (navigator.userAgent || '').toLowerCase();
    if (!ua) return true;
    if (navigator.webdriver === true) return true;
    if (/bot|crawl|spider|slurp|headless|phantom|puppeteer|playwright|selenium|lighthouse|pagespeed|gtmetrix|pingdom|uptimerobot|whatsapp|telegram|facebookexternalhit|twitterbot|linkedinbot|embedly|quora|pinterest|slackbot|discordbot|vkshare|W3C_Validator|curl|wget|python|axios|node-fetch|go-http-client|java|okhttp/i.test(ua)) {
      return true;
    }
    if (window.outerWidth === 0 && window.outerHeight === 0) return true;
    if (!navigator.languages || navigator.languages.length === 0) return true;
    return false;
  }

  function detectSiteMetadata() {
    if (window.SPY_SITE_ID && window.SPY_SITE_NAME) {
      return {
        siteId: window.SPY_SITE_ID,
        siteName: window.SPY_SITE_NAME,
        category: window.SPY_SITE_CATEGORY || 'dubai'
      };
    }
    const hostPath = (window.location.pathname || '/').replace(/^\/+|\/+$/g, '').split('/')[0];
    const cleanTitle = (document.title || hostPath || 'sitio-web').trim();
    return {
      siteId: hostPath || 'sitio-general',
      siteName: cleanTitle.slice(0, 90),
      category: 'dubai'
    };
  }

  const { siteId, siteName, category } = detectSiteMetadata();
  const urlParams = new URLSearchParams(window.location.search);

  // Silent Admin Exclusion (never shows any UI on the page)
  if (urlParams.get('admin') === 'david' || urlParams.get('view') === 'spy') {
    localStorage.setItem('tecno_spy_admin_excluded', 'true');
  }

  function getOrCreateVisitorId() {
    let vid = localStorage.getItem('tecno_spy_visitor_id');
    if (!vid) {
      vid = 'usr_' + (crypto.randomUUID ? crypto.randomUUID().slice(0, 12) : Math.random().toString(36).substring(2, 12) + Date.now().toString(36));
      localStorage.setItem('tecno_spy_visitor_id', vid);
    }
    return vid;
  }

  const visitorId = getOrCreateVisitorId();
  if (CONFIG.excludedVisitorIds.includes(visitorId)) {
    localStorage.setItem('tecno_spy_admin_excluded', 'true');
  }

  function isIpOrIspExcluded(ipStr, ispStr) {
    if (ipStr) {
      const norm = String(ipStr).trim().toLowerCase();
      if (CONFIG.excludedIps.some(ip => ip.toLowerCase() === norm)) return true;
      if (CONFIG.excludedIpPrefixes.some(prefix => norm.startsWith(prefix.toLowerCase()))) return true;
    }
    if (ispStr) {
      const normIsp = String(ispStr).trim().toLowerCase();
      if (CONFIG.datacenterKeywords.some(kw => normIsp.includes(kw.toLowerCase()))) return true;
    }
    return false;
  }

  function incrementSiteVisitCount(sId) {
    const key = 'tecno_spy_vcount_' + sId;
    const prev = parseInt(localStorage.getItem(key) || '0', 10);
    const next = prev + 1;
    localStorage.setItem(key, String(next));
    return next;
  }

  // Passive Hardware, Screen & GPU Fingerprinting (Zero Permission Prompts)
  function getGpuShortName() {
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      if (!gl) return '';
      const dbg = gl.getExtension('WEBGL_debug_renderer_info');
      if (!dbg) return '';
      const raw = String(gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) || '');
      return raw
        .replace(/ANGLE \((.+)\)/i, '$1')
        .replace(/Direct3D11.*$/i, '')
        .replace(/Mesa /i, '')
        .replace(/\s+/g, ' ')
        .trim()
        .slice(0, 38);
    } catch (e) {
      return '';
    }
  }

  function getDeviceInfo() {
    const ua = navigator.userAgent || '';
    let base = 'Dispositivo Web';
    if (/iPhone/i.test(ua)) base = 'Apple iPhone';
    else if (/iPad/i.test(ua)) base = 'Apple iPad';
    else if (/Android/i.test(ua)) {
      const m = ua.match(/Android\s+[\d.]+;\s*([^;)]+)/i);
      const model = m && m[1] ? m[1].trim() : '';
      base = model && model !== 'K' ? `Android (${model.slice(0, 22)})` : 'Android Smartphone';
    } else if (/Macintosh/i.test(ua)) base = 'Apple Mac';
    else if (/Windows/i.test(ua)) base = 'Windows PC';
    else if (/Linux/i.test(ua)) base = 'Linux PC';

    const dpr = window.devicePixelRatio ? `${Math.round(window.devicePixelRatio * 10) / 10}x` : '';
    const scr = window.screen ? `${window.screen.width}x${window.screen.height}` : '';
    const cores = navigator.hardwareConcurrency ? `${navigator.hardwareConcurrency}c` : '';
    const ram = navigator.deviceMemory ? `${navigator.deviceMemory}GB` : '';
    const hwParts = [scr, dpr, cores, ram].filter(Boolean).join(' • ');
    return hwParts ? `${base} (${hwParts})` : base;
  }

  function getOriginAndProspectAttribution() {
    const ua = navigator.userAgent || '';
    const ref = document.referrer || '';
    const prospectParam =
      urlParams.get('v') ||
      urlParams.get('lead') ||
      urlParams.get('prospect') ||
      urlParams.get('client') ||
      urlParams.get('nombre') ||
      urlParams.get('name') ||
      '';
    const utmSource = urlParams.get('utm_source') || '';
    const utmCampaign = urlParams.get('utm_campaign') || '';

    let channel = 'Directo / Enlace';
    if (utmSource) {
      channel = utmSource + (utmCampaign ? ` (${utmCampaign})` : '');
    } else if (urlParams.get('fbclid') || /FBAN|FBAV/i.test(ua) || /facebook\.com/i.test(ref)) {
      channel = 'Facebook';
    } else if (/Instagram/i.test(ua) || /instagram\.com/i.test(ref)) {
      channel = 'Instagram';
    } else if (/WhatsApp/i.test(ua) || /whatsapp\.com|wa\.me/i.test(ref)) {
      channel = 'WhatsApp';
    } else if (urlParams.get('gclid') || /google\./i.test(ref)) {
      channel = 'Google Search / Maps';
    } else if (/t\.co|twitter\.com|x\.com/i.test(ref)) {
      channel = 'X / Twitter';
    } else if (/linkedin\.com|LinkedInApp/i.test(ua + ' ' + ref)) {
      channel = 'LinkedIn';
    } else if (/tiktok/i.test(ua + ' ' + ref) || urlParams.get('ttclid')) {
      channel = 'TikTok';
    } else if (ref) {
      try {
        channel = 'Ref: ' + new URL(ref).hostname.replace(/^www\./, '');
      } catch (e) {
        channel = ref.slice(0, 60);
      }
    }

    if (prospectParam) {
      return `🎯 Prospecto: ${prospectParam.slice(0, 40)} | ${channel}`;
    }
    return channel;
  }

  const sessionKey = 'tecno_spy_sess_' + siteId;
  const startKey = 'tecno_spy_start_' + siteId;
  const vnumKey = 'tecno_spy_vnum_' + siteId;
  const convKey = 'tecno_spy_conv_' + siteId;
  const convEventsKey = 'tecno_spy_convev_' + siteId;

  let sessionId = sessionStorage.getItem(sessionKey);
  let sessionStartTime = parseInt(sessionStorage.getItem(startKey) || String(Date.now()), 10);
  let visitNumber = parseInt(sessionStorage.getItem(vnumKey) || '0', 10);
  let conversionsCount = parseInt(sessionStorage.getItem(convKey) || '0', 10);
  let conversionEvents = [];
  try {
    conversionEvents = JSON.parse(sessionStorage.getItem(convEventsKey) || '[]');
  } catch (e) {
    conversionEvents = [];
  }

  let clientGeo = { ip: 'direct', city: 'Visitante', country: 'Externo', isp: '' };
  let isTrackingActive = false;
  let hasHumanInteracted = false;
  let hasPassedDwellGate = false;
  let geoReady = false;
  let isBlockedSource = false;

  // Deep Passive Telemetry State
  let maxScrollPct = 0;
  let activeVisibleSec = 0;
  let currentVisibleSections = new Set();
  const sectionDwellSeconds = {};
  let batteryStatusText = '';
  const gpuName = getGpuShortName();
  const systemTimeZone = (() => {
    try {
      return Intl.DateTimeFormat().resolvedOptions().timeZone || '';
    } catch (e) {
      return '';
    }
  })();
  const deviceLanguages = (() => {
    try {
      return (navigator.languages || [navigator.language]).filter(Boolean).slice(0, 3).join(', ');
    } catch (e) {
      return '';
    }
  })();
  const networkConnectionText = (() => {
    try {
      const c = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
      if (!c) return '';
      const parts = [];
      if (c.effectiveType) parts.push(String(c.effectiveType).toUpperCase());
      if (typeof c.downlink === 'number' && c.downlink > 0) parts.push(`${c.downlink} Mbps`);
      return parts.join(' • ');
    } catch (e) {
      return '';
    }
  })();

  if (navigator.getBattery) {
    try {
      navigator.getBattery().then((bat) => {
        if (bat && typeof bat.level === 'number') {
          const pct = Math.round(bat.level * 100);
          batteryStatusText = `${pct}%${bat.charging ? ' ⚡' : ''}`;
        }
      }).catch(() => {});
    } catch (e) {}
  }

  function updateScrollDepth() {
    try {
      const docEl = document.documentElement;
      const body = document.body;
      const scrollTop = window.scrollY || docEl.scrollTop || body.scrollTop || 0;
      const winH = window.innerHeight || docEl.clientHeight || 1;
      const fullH = Math.max(
        body.scrollHeight || 0,
        docEl.scrollHeight || 0,
        body.offsetHeight || 0,
        docEl.offsetHeight || 0,
        1
      );
      if (fullH <= winH) {
        maxScrollPct = Math.max(maxScrollPct, 100);
      } else {
        const pct = Math.min(100, Math.round(((scrollTop + winH) / fullH) * 100));
        if (pct > maxScrollPct) maxScrollPct = pct;
      }
    } catch (e) {}
  }

  function resolveSectionLabel(el, idx) {
    if (!el) return `Sección ${idx + 1}`;
    const dataLabel = el.getAttribute('data-section') || el.getAttribute('aria-label');
    if (dataLabel) return dataLabel.trim().slice(0, 36);
    const heading = el.querySelector('h1, h2, h3');
    if (heading && heading.innerText) {
      const clean = heading.innerText.replace(/\s+/g, ' ').trim();
      if (clean.length > 2) return clean.slice(0, 36);
    }
    if (el.id) {
      return el.id.replace(/[-_]/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()).slice(0, 36);
    }
    if (el.tagName === 'HEADER') return 'Portada / Hero';
    if (el.tagName === 'FOOTER') return 'Pie de Página / Contacto';
    return `Sección ${idx + 1}`;
  }

  function setupSectionAndScrollObservers() {
    updateScrollDepth();
    window.addEventListener('scroll', updateScrollDepth, { passive: true });

    try {
      const candidates = Array.from(
        document.querySelectorAll('header, section, [id*="roi"], [id*="calc"], [id*="map"], [id*="price"], [id*="portfolio"], [id*="service"], [id*="contact"], footer')
      ).slice(0, 20);

      if ('IntersectionObserver' in window && candidates.length > 0) {
        const labelMap = new Map();
        candidates.forEach((el, idx) => {
          labelMap.set(el, resolveSectionLabel(el, idx));
        });

        const obs = new IntersectionObserver(
          (entries) => {
            entries.forEach((entry) => {
              const name = labelMap.get(entry.target);
              if (!name) return;
              if (entry.isIntersecting && entry.intersectionRatio >= 0.25) {
                currentVisibleSections.add(name);
              } else {
                currentVisibleSections.delete(name);
              }
            });
          },
          { threshold: [0.25, 0.6] }
        );

        candidates.forEach((el) => obs.observe(el));
      }
    } catch (e) {}

    // 1-second ticker for active reading time & per-section dwell time
    setInterval(() => {
      if (document.visibilityState === 'visible') {
        activeVisibleSec += 1;
        currentVisibleSections.forEach((secName) => {
          sectionDwellSeconds[secName] = (sectionDwellSeconds[secName] || 0) + 1;
        });
      }
    }, 1000);
  }

  function buildSectionsViewedTelemetryArray() {
    const items = [];
    updateScrollDepth();
    items.push(`📊 Scroll leído: ${maxScrollPct || 15}%`);
    if (activeVisibleSec > 0) {
      items.push(`👁️ Pantalla activa: ${activeVisibleSec}s`);
    }
    if (systemTimeZone) {
      items.push(`🌍 Zona: ${systemTimeZone}`);
    }
    if (deviceLanguages) {
      items.push(`🗣️ Idioma: ${deviceLanguages}`);
    }
    if (clientGeo.isp) {
      items.push(`🏢 ISP/Red: ${clientGeo.isp.slice(0, 42)}`);
    }
    if (networkConnectionText) {
      items.push(`📡 Conexión: ${networkConnectionText}`);
    }
    if (gpuName) {
      items.push(`💎 GPU: ${gpuName}`);
    }
    if (batteryStatusText) {
      items.push(`🔋 Batería: ${batteryStatusText}`);
    }

    const topSections = Object.entries(sectionDwellSeconds)
      .filter(([, sec]) => sec >= 2)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6);

    topSections.forEach(([name, sec]) => {
      items.push(`📌 ${name}: ${sec}s`);
    });

    return items;
  }

  async function ensureSiteRegistered() {
    const cleanUrl = window.location.href.split('?')[0];
    if (cleanUrl.startsWith('file:') || cleanUrl.includes('localhost') || cleanUrl.includes('127.0.0.1')) return;
    try {
      await fetch(`${CONFIG.supabaseUrl}/rest/v1/web_spy_sites`, {
        method: 'POST',
        headers: {
          'apikey': CONFIG.supabaseKey,
          'Authorization': `Bearer ${CONFIG.supabaseKey}`,
          'Content-Type': 'application/json',
          'Prefer': 'resolution=ignore-duplicates'
        },
        body: JSON.stringify({
          site_id: siteId,
          site_name: siteName,
          site_url: cleanUrl,
          category: category,
          platform: 'GitHub Pages / Oficial'
        })
      });
    } catch (e) {}
  }

  async function resolveGeo() {
    try {
      const r1 = await fetch('https://ipwho.is/', { cache: 'no-store' });
      if (r1.ok) {
        const d1 = await r1.json();
        if (d1 && d1.ip) {
          const ispInfo = [
            d1.connection && d1.connection.isp,
            d1.connection && d1.connection.org
          ].filter(Boolean).join(' / ');
          return {
            ip: d1.ip,
            city: d1.city || 'Ciudad',
            country: d1.country || 'País',
            isp: ispInfo
          };
        }
      }
    } catch (e) {}
    try {
      const r2 = await fetch('https://ipapi.co/json/', { cache: 'no-store' });
      if (r2.ok) {
        const d2 = await r2.json();
        if (d2 && d2.ip) {
          return {
            ip: d2.ip,
            city: d2.city || 'Ciudad',
            country: d2.country_name || d2.country || 'País',
            isp: d2.org || ''
          };
        }
      }
    } catch (e2) {}
    return { ip: 'direct_' + visitorId.slice(-6), city: 'Acceso Directo', country: 'Web / Móvil', isp: '' };
  }

  function setupConversionAndIntentListeners() {
    // 1. Click conversions & high-intent buttons
    document.addEventListener('click', (e) => {
      const target = e.target ? e.target.closest('a, button, [role="button"], input[type="submit"]') : null;
      if (!target) return;
      const href = (target.getAttribute('href') || '').toLowerCase();
      const text = (target.innerText || target.value || target.getAttribute('aria-label') || '').trim().replace(/\s+/g, ' ');
      const lowerText = text.toLowerCase();

      let actionLabel = null;
      let isHardConversion = false;

      if (href.includes('wa.me') || href.includes('whatsapp.com')) {
        actionLabel = '💬 Clic Contacto WhatsApp';
        isHardConversion = true;
      } else if (href.startsWith('tel:')) {
        actionLabel = '📞 Llamada Telefónica Directa';
        isHardConversion = true;
      } else if (href.startsWith('mailto:')) {
        actionLabel = '✉️ Clic en Correo Electrónico';
        isHardConversion = true;
      } else if (href.endsWith('.pdf') || lowerText.includes('pdf') || lowerText.includes('brochure') || lowerText.includes('dossier')) {
        actionLabel = '📄 Descarga Brochure / PDF: ' + text.slice(0, 28);
        isHardConversion = true;
      } else if (
        /comprar|reservar|book|appointment|cita|cotizar|ordenar|pedido|checkout|pagar|claim|solicitar|oferta|inquire|buy/i.test(lowerText)
      ) {
        actionLabel = '🛒 Acción: ' + (text || 'Reserva/Compra').slice(0, 32);
        isHardConversion = true;
      }

      if (actionLabel) {
        recordConversion(actionLabel, isHardConversion);
      }
    }, true);

    // 2. Form Submissions
    document.addEventListener('submit', (e) => {
      const form = e.target;
      if (form && form.id !== 'project-form') {
        recordConversion('📝 Formulario Enviado / Solicitud', true);
      }
    }, true);

    // 3. Silent Copy Detection (100% passive via window.getSelection, zero browser alerts)
    document.addEventListener('copy', () => {
      try {
        const selected = (window.getSelection && window.getSelection().toString() || '').trim().replace(/\s+/g, ' ');
        if (selected && selected.length >= 3) {
          recordConversion('📋 Copió texto: "' + selected.slice(0, 36) + '"', false);
        }
      } catch (e) {}
    }, true);

    // 4. Calculator / Simulator / Filter Interaction Detection
    document.addEventListener('change', (e) => {
      try {
        const el = e.target;
        if (!el || !el.tagName) return;
        const type = (el.getAttribute('type') || '').toLowerCase();
        if (el.tagName === 'SELECT' || type === 'range' || type === 'number' || el.classList.contains('simulator-input')) {
          const val = String(el.value || '').trim();
          const name = (el.getAttribute('name') || el.getAttribute('id') || el.getAttribute('aria-label') || 'Filtro/Simulador').slice(0, 22);
          if (val) {
            recordConversion(`🎛️ Simuló ${name}: ${val.slice(0, 24)}`, false);
          }
        }
      } catch (err) {}
    }, true);

    // 5. Video Play Detection
    document.addEventListener('play', (e) => {
      try {
        const el = e.target;
        if (el && el.tagName === 'VIDEO') {
          recordConversion('🎬 Reprodujo Video en Página', false);
        }
      } catch (err) {}
    }, true);
  }

  async function tryActivateHumanSession(forceByConversion = false) {
    if (isTrackingActive || isBlockedSource) return;
    if (!geoReady) return;
    if (!forceByConversion && (!hasHumanInteracted || !hasPassedDwellGate)) return;

    if (!sessionId) {
      sessionId = 'spy_' + siteId.slice(0, 18) + '_' + (crypto.randomUUID ? crypto.randomUUID().slice(0, 10) : Math.random().toString(36).substring(2, 10) + Date.now().toString(36));
      visitNumber = incrementSiteVisitCount(siteId);
      sessionStorage.setItem(sessionKey, sessionId);
      sessionStorage.setItem(startKey, String(sessionStartTime));
      sessionStorage.setItem(vnumKey, String(visitNumber));
    } else if (!visitNumber) {
      visitNumber = parseInt(localStorage.getItem('tecno_spy_vcount_' + siteId) || '1', 10);
    }

    isTrackingActive = true;
    await registerInitialVisit();
    setInterval(() => sendHeartbeat(false), CONFIG.heartbeatIntervalMs);
    window.addEventListener('beforeunload', () => sendHeartbeat(true));
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') sendHeartbeat(true);
    });
  }

  function recordConversion(label, countAsConversion = true) {
    if (isBlockedSource) return;
    if (countAsConversion) {
      conversionsCount += 1;
      sessionStorage.setItem(convKey, String(conversionsCount));
    }
    conversionEvents.push({
      label: label,
      at: new Date().toISOString()
    });
    conversionEvents = conversionEvents.slice(-30);
    sessionStorage.setItem(convEventsKey, JSON.stringify(conversionEvents));
    if (!isTrackingActive) {
      hasHumanInteracted = true;
      hasPassedDwellGate = true;
      tryActivateHumanSession(true);
    } else {
      sendHeartbeat(false);
    }
  }

  window.recordTecnoSpyConversion = (label) => recordConversion(label, true);

  function listenForHumanProof() {
    const onHumanEvent = (e) => {
      if (e && e.isTrusted === false) return;
      hasHumanInteracted = true;
      tryActivateHumanSession(false);
    };
    window.addEventListener('scroll', onHumanEvent, { passive: true, once: true });
    window.addEventListener('touchstart', onHumanEvent, { passive: true, once: true });
    window.addEventListener('pointerdown', onHumanEvent, { passive: true, once: true });
    window.addEventListener('mousemove', onHumanEvent, { passive: true, once: true });
    window.addEventListener('keydown', onHumanEvent, { passive: true, once: true });
  }

  async function initTelemetry() {
    purgeAnyOnSiteUi();
    ensureSiteRegistered();

    if (localStorage.getItem('tecno_spy_admin_excluded') === 'true' || isAutomatedBotEnv()) {
      isBlockedSource = true;
      return;
    }

    sessionStartTime = parseInt(sessionStorage.getItem(startKey) || String(Date.now()), 10);
    sessionStorage.setItem(startKey, String(sessionStartTime));

    setupSectionAndScrollObservers();
    listenForHumanProof();
    setupConversionAndIntentListeners();

    setTimeout(() => {
      if (document.visibilityState !== 'hidden') {
        hasPassedDwellGate = true;
        tryActivateHumanSession(false);
      }
    }, CONFIG.minHumanDwellMs);

    try {
      clientGeo = await resolveGeo();
      if (isIpOrIspExcluded(clientGeo.ip, clientGeo.isp)) {
        isBlockedSource = true;
        return;
      }
      geoReady = true;
      tryActivateHumanSession(false);
    } catch (err) {}
  }

  async function registerInitialVisit() {
    const durationSec = Math.max(4, Math.round((Date.now() - sessionStartTime) / 1000));
    const payload = {
      id: sessionId,
      site_id: siteId,
      site_name: siteName,
      page_path: window.location.pathname || '/',
      page_url: window.location.href.split('?')[0],
      visitor_id: visitorId,
      ip: clientGeo.ip,
      city: clientGeo.city,
      country: clientGeo.country,
      device: getDeviceInfo(),
      user_agent: (navigator.userAgent || '').slice(0, 250),
      referrer: getOriginAndProspectAttribution().slice(0, 200),
      duration_seconds: durationSec,
      sections_viewed: buildSectionsViewedTelemetryArray(),
      conversions_count: conversionsCount,
      conversion_events: conversionEvents,
      is_active: true,
      visit_count: visitNumber || 1,
      last_ping_at: new Date().toISOString()
    };

    try {
      await fetch(`${CONFIG.supabaseUrl}/rest/v1/web_spy_visits`, {
        method: 'POST',
        headers: {
          'apikey': CONFIG.supabaseKey,
          'Authorization': `Bearer ${CONFIG.supabaseKey}`,
          'Content-Type': 'application/json',
          'Prefer': 'resolution=merge-duplicates'
        },
        body: JSON.stringify(payload)
      });
    } catch (e) {}
  }

  async function sendHeartbeat(isClosing = false) {
    if (!isTrackingActive || !sessionId || isBlockedSource) return;
    const durationSec = Math.max(4, Math.round((Date.now() - sessionStartTime) / 1000));
    const payload = {
      duration_seconds: durationSec,
      sections_viewed: buildSectionsViewedTelemetryArray(),
      conversions_count: conversionsCount,
      conversion_events: conversionEvents,
      is_active: !isClosing,
      last_ping_at: new Date().toISOString()
    };

    try {
      await fetch(`${CONFIG.supabaseUrl}/rest/v1/web_spy_visits?id=eq.${encodeURIComponent(sessionId)}`, {
        method: 'PATCH',
        headers: {
          'apikey': CONFIG.supabaseKey,
          'Authorization': `Bearer ${CONFIG.supabaseKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload),
        keepalive: Boolean(isClosing)
      });
    } catch (e) {}
  }

  initTelemetry();
})();
