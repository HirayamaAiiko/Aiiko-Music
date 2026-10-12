// Aiiko Music — Sitio web oficial
// Soporte multilingüe (EN por defecto, detección del sistema, ES, JA, FR),
// botones de descarga interactivos con enlace directo a release,
// pestañas de capturas y dock de navegación con indicador activo.

(() => {
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- Diccionario de idiomas ---------- */

  const I18N = {
    en: {
      pageTitle: 'Aiiko Music — Music player for your personal library',
      heroTitle: 'A music player for your personal library.',
      heroLede: 'Aiiko Music is a local music player for Windows, designed for personal music collections. It brings together playback, albums, artists, playlists, lyrics, and metadata into one cohesive experience.',
      heroDownload: 'Download for Windows',
      heroSource: 'Source code on GitHub',
      heroMeta: 'Windows 10 & 11 · Open Source (GPL-3.0)',
      releaseLabel: 'Latest release: {tag}',

      navHome: 'Home',
      navFeatures: 'Features',
      navScreenshots: 'Screenshots',
      navFormats: 'Formats',
      navInstall: 'Installation',
      navDownload: 'Download',

      featuresTitle: 'Features',
      catLibraryTitle: 'Library',
      fLibrary1: 'Local music library',
      fLibrary2: 'Album and artist browsing',
      fLibrary3: 'Playlist management',
      fLibrary4: 'Full-library search',

      catPlaybackTitle: 'Playback',
      fPlayback1: '10-band equalizer',
      fPlayback2: 'Queue and shuffle playback',
      fPlayback3: 'Gapless playback',
      fPlayback4: 'Audio visualizer',

      catLyricsTitle: 'Lyrics & metadata',
      fLyrics1: 'Synchronized lyrics (.lrc & online search)',
      fLyrics2: 'Built-in lyrics editor',
      fLyrics3: 'Tag and metadata editor',
      fLyrics4: 'Album art support',

      catInterfaceTitle: 'Interface',
      fInterface1: 'Floating mini player',
      fInterface2: 'Fullscreen display mode',
      fInterface3: 'Theme and accent color customization',
      fInterface4: 'Keyboard shortcuts',

      catIntegrationsTitle: 'Integrations',
      fInteg1: 'Discord Rich Presence',
      fInteg2: 'Last.fm scrobbling',

      shotsTitle: 'Screenshots',
      tabHome: 'Home',
      tabLibrary: 'Library',
      tabArtists: 'Artists',
      tabArtistDetail: 'Artist detail',
      tabSearch: 'Search',
      tabPlaylists: 'Playlists',
      tabLyricsEditor: 'Lyrics editor',

      formatsTitle: 'Supported formats',
      formatsSub: 'Aiiko Music plays the most common audio formats, including:',
      formatsNote: 'Format support depends on the underlying audio engine capabilities.',

      installTitle: 'Installation',
      installSub: 'For Windows 10 and 11. Download the latest release package to get started.',
      dlPrimaryTitle: 'Download Latest Release',
      dlPrimaryDesc: '{tag} · Windows 10/11 (64-bit) · Portable ZIP{size}',
      dlSecondaryTitle: 'All Releases',
      dlSecondaryDesc: 'GitHub Releases & Changelog',

      step1: 'Download the ZIP package using the button above.',
      step2: 'Extract the files to your preferred folder.',
      step3: 'Launch <code>Aiiko Music.exe</code> and follow the initial setup prompts.',
      sourceNote: 'If you prefer running or building from source code, instructions are available in the',

      footerCredit: 'Aiiko Music · Developed by Aiiko Hirayama · © 2026 · GPL-3.0 License',
      footerLicense: 'License',
      shotAltPrefix: 'Aiiko Music screenshot: '
    },

    es: {
      pageTitle: 'Aiiko Music — Reproductor de música para tu propia biblioteca',
      heroTitle: 'Un reproductor de música para tu propia biblioteca.',
      heroLede: 'Aiiko Music es un reproductor local para Windows, pensado para colecciones de música personales. Reúne reproducción, álbumes, artistas, listas, letras y metadatos en un solo lugar.',
      heroDownload: 'Descargar para Windows',
      heroSource: 'Código fuente en GitHub',
      heroMeta: 'Windows 10 y 11 · Código abierto (GPL-3.0)',
      releaseLabel: 'Última versión: {tag}',

      navHome: 'Inicio',
      navFeatures: 'Funciones',
      navScreenshots: 'Capturas',
      navFormats: 'Formatos',
      navInstall: 'Instalación',
      navDownload: 'Descargar',

      featuresTitle: 'Funciones',
      catLibraryTitle: 'Biblioteca',
      fLibrary1: 'Biblioteca de música local',
      fLibrary2: 'Navegación por álbumes y artistas',
      fLibrary3: 'Gestión de listas de reproducción',
      fLibrary4: 'Búsqueda en toda la biblioteca',

      catPlaybackTitle: 'Reproducción',
      fPlayback1: 'Ecualizador de 10 bandas',
      fPlayback2: 'Cola y reproducción aleatoria',
      fPlayback3: 'Reproducción sin pausas (gapless)',
      fPlayback4: 'Visualizador de audio',

      catLyricsTitle: 'Letras y metadatos',
      fLyrics1: 'Letras sincronizadas (.lrc y búsqueda en línea)',
      fLyrics2: 'Editor de letras integrado',
      fLyrics3: 'Editor de etiquetas y metadatos',
      fLyrics4: 'Carátulas de álbum',

      catInterfaceTitle: 'Interfaz',
      fInterface1: 'Mini reproductor flotante',
      fInterface2: 'Modo a pantalla completa',
      fInterface3: 'Personalización de temas y acento',
      fInterface4: 'Atajos de teclado',

      catIntegrationsTitle: 'Integraciones',
      fInteg1: 'Discord Rich Presence',
      fInteg2: 'Scrobbling en Last.fm',

      shotsTitle: 'Capturas',
      tabHome: 'Inicio',
      tabLibrary: 'Biblioteca',
      tabArtists: 'Artistas',
      tabArtistDetail: 'Detalle de artista',
      tabSearch: 'Búsqueda',
      tabPlaylists: 'Listas',
      tabLyricsEditor: 'Editor de letras',

      formatsTitle: 'Formatos compatibles',
      formatsSub: 'Aiiko Music reproduce los formatos de audio más comunes, entre ellos:',
      formatsNote: 'La compatibilidad puede depender de las capacidades del motor de reproducción.',

      installTitle: 'Instalación',
      installSub: 'Para Windows 10 y 11. Descarga el paquete de la última versión publicada para comenzar.',
      dlPrimaryTitle: 'Descargar última versión',
      dlPrimaryDesc: '{tag} · Windows 10/11 (64 bits) · ZIP portátil{size}',
      dlSecondaryTitle: 'Todos los lanzamientos',
      dlSecondaryDesc: 'Releases y cambios en GitHub',

      step1: 'Descarga el paquete comprimido (.zip) con el botón superior.',
      step2: 'Extrae los archivos en la carpeta de tu preferencia.',
      step3: 'Abre <code>Aiiko Music.exe</code> y sigue las indicaciones en el primer inicio.',
      sourceNote: 'Si prefieres compilar o ejecutar desde el código fuente, consulta el',

      footerCredit: 'Aiiko Music · Desarrollado por Aiiko Hirayama · © 2026 · Licencia GPL-3.0',
      footerLicense: 'Licencia',
      shotAltPrefix: 'Captura de Aiiko Music: '
    },

    ja: {
      pageTitle: 'Aiiko Music — 個人ライブラリのための音楽プレーヤー',
      heroTitle: 'あなたの個人ライブラリのための音楽プレーヤー。',
      heroLede: 'Aiiko Music は、個人の音楽コレクションのために設計された Windows 向けローカル音楽プレーヤーです。再生、アルバム、アーティスト、プレイリスト、歌詞、メタデータをひとつにまとめます。',
      heroDownload: 'Windows 向けダウンロード',
      heroSource: 'GitHub でソースコードを見る',
      heroMeta: 'Windows 10 / 11 · オープンソース (GPL-3.0)',
      releaseLabel: '最新リリース: {tag}',

      navHome: 'ホーム',
      navFeatures: '機能',
      navScreenshots: 'スクリーンショット',
      navFormats: 'フォーマット',
      navInstall: 'インストール',
      navDownload: 'ダウンロード',

      featuresTitle: '主な機能',
      catLibraryTitle: 'ライブラリ',
      fLibrary1: 'ローカル音楽ライブラリ',
      fLibrary2: 'アルバムおよびアーティストの閲覧',
      fLibrary3: 'プレイリスト管理',
      fLibrary4: 'ライブラリ全体の検索',

      catPlaybackTitle: '再生機能',
      fPlayback1: '10バンドイコライザー',
      fPlayback2: 'キューおよびシャッフル再生',
      fPlayback3: 'ギャップレス再生',
      fPlayback4: 'オーディオビジュアライザー',

      catLyricsTitle: '歌詞・メタデータ',
      fLyrics1: '同期歌詞（.lrc およびオンライン検索）',
      fLyrics2: '歌詞エディター内蔵',
      fLyrics3: 'タグ・メタデータ編集',
      fLyrics4: 'アルバムアート表示',

      catInterfaceTitle: 'インターフェース',
      fInterface1: 'フローティングミニプレーヤー',
      fInterface2: '全画面表示モード',
      fInterface3: 'テーマおよびアクセントカラーのカスタマイズ',
      fInterface4: 'キーボードショートカット',

      catIntegrationsTitle: '外部連携',
      fInteg1: 'Discord Rich Presence',
      fInteg2: 'Last.fm スクロブリング',

      shotsTitle: 'スクリーンショット',
      tabHome: 'ホーム',
      tabLibrary: 'ライブラリ',
      tabArtists: 'アーティスト',
      tabArtistDetail: 'アーティスト詳細',
      tabSearch: '検索',
      tabPlaylists: 'プレイリスト',
      tabLyricsEditor: '歌詞エディター',

      formatsTitle: '対応フォーマット',
      formatsSub: 'Aiiko Music は主要なオーディオ形式に対応しています：',
      formatsNote: '再生エンジンの仕様により互換性が異なる場合があります。',

      installTitle: 'インストール',
      installSub: 'Windows 10 および 11 対応。最新の公開パッケージをダウンロードしてご利用ください。',
      dlPrimaryTitle: '最新版をダウンロード',
      dlPrimaryDesc: '{tag} · Windows 10/11 (64bit) · ポータブル ZIP{size}',
      dlSecondaryTitle: 'すべてのリリース履歴',
      dlSecondaryDesc: 'GitHub Releases & 変更履歴',

      step1: '上のボタンから ZIP パッケージをダウンロードします。',
      step2: '任意のフォルダにファイルを解凍します。',
      step3: '<code>Aiiko Music.exe</code> を起動し、初回設定の案内に従ってください。',
      sourceNote: 'ソースコードからのビルドや実行方法はリポジトリの',

      footerCredit: 'Aiiko Music · 開発者: Aiiko Hirayama · © 2026 · GPL-3.0 ライセンス',
      footerLicense: 'ライセンス',
      shotAltPrefix: 'Aiiko Music スクリーンショット: '
    },

    fr: {
      pageTitle: 'Aiiko Music — Lecteur de musique pour votre bibliothèque',
      heroTitle: 'Un lecteur de musique pour votre bibliothèque personnelle.',
      heroLede: 'Aiiko Music est un lecteur local pour Windows, conçu pour vos collections musicales personnelles. Il réunit lecture, albums, artistes, listes de lecture, paroles et métadonnées en un seul endroit.',
      heroDownload: 'Télécharger pour Windows',
      heroSource: 'Code source sur GitHub',
      heroMeta: 'Windows 10 et 11 · Open source (GPL-3.0)',
      releaseLabel: 'Dernière version : {tag}',

      navHome: 'Accueil',
      navFeatures: 'Fonctionnalités',
      navScreenshots: 'Captures',
      navFormats: 'Formats',
      navInstall: 'Installation',
      navDownload: 'Télécharger',

      featuresTitle: 'Fonctionnalités',
      catLibraryTitle: 'Bibliothèque',
      fLibrary1: 'Bibliothèque musicale locale',
      fLibrary2: 'Navigation par albums et artistes',
      fLibrary3: 'Gestion des listes de lecture',
      fLibrary4: 'Recherche dans toute la bibliothèque',

      catPlaybackTitle: 'Lecture',
      fPlayback1: 'Égaliseur 10 bandes',
      fPlayback2: 'File d\'attente et lecture aléatoire',
      fPlayback3: 'Lecture sans blanc (gapless)',
      fPlayback4: 'Visualiseur audio',

      catLyricsTitle: 'Paroles et métadonnées',
      fLyrics1: 'Paroles synchronisées (.lrc et recherche en ligne)',
      fLyrics2: 'Éditeur de paroles intégré',
      fLyrics3: 'Éditeur de balises et métadonnées',
      fLyrics4: 'Prise en charge des pochettes d\'album',

      catInterfaceTitle: 'Interface',
      fInterface1: 'Mini-lecteur flottant',
      fInterface2: 'Mode plein écran',
      fInterface3: 'Personnalisation du thème et de la couleur',
      fInterface4: 'Raccourcis clavier',

      catIntegrationsTitle: 'Intégrations',
      fInteg1: 'Discord Rich Presence',
      fInteg2: 'Scrobbling Last.fm',

      shotsTitle: 'Captures d\'écran',
      tabHome: 'Accueil',
      tabLibrary: 'Bibliothèque',
      tabArtists: 'Artistes',
      tabArtistDetail: 'Détail d\'artiste',
      tabSearch: 'Recherche',
      tabPlaylists: 'Playlists',
      tabLyricsEditor: 'Éditeur de paroles',

      formatsTitle: 'Formats compatibles',
      formatsSub: 'Aiiko Music prend en charge les formats audio les plus courants, notamment :',
      formatsNote: 'La compatibilité dépend des fonctionnalités du moteur audio.',

      installTitle: 'Installation',
      installSub: 'Pour Windows 10 et 11. Téléchargez la dernière version pour commencer.',
      dlPrimaryTitle: 'Télécharger la dernière version',
      dlPrimaryDesc: '{tag} · Windows 10/11 (64 bits) · ZIP portable{size}',
      dlSecondaryTitle: 'Toutes les versions',
      dlSecondaryDesc: 'Releases et notes sur GitHub',

      step1: 'Téléchargez l\'archive ZIP à l\'aide du bouton ci-dessus.',
      step2: 'Extrayez les fichiers dans le dossier de votre choix.',
      step3: 'Lancez <code>Aiiko Music.exe</code> et suivez les instructions au premier démarrage.',
      sourceNote: 'Pour compiler ou exécuter depuis le code source, consultez le',

      footerCredit: 'Aiiko Music · Développé par Aiiko Hirayama · © 2026 · Licence GPL-3.0',
      footerLicense: 'Licence',
      shotAltPrefix: 'Capture Aiiko Music : '
    }
  };

  const SUPPORTED_LANGS = ['en', 'es', 'ja', 'fr'];
  const DEFAULT_LANG = 'en';

  let currentLang = DEFAULT_LANG;
  let latestTag = '';
  let latestSize = '';
  let directZipUrl = '';

  /* ---------- Detección de idioma del sistema / guardado ---------- */

  function detectInitialLanguage() {
    try {
      const saved = localStorage.getItem('aiiko_lang');
      if (saved && SUPPORTED_LANGS.includes(saved)) {
        return saved;
      }
    } catch (_) { /* ignore */ }

    const browserLangs = navigator.languages || [navigator.language || ''];
    for (const raw of browserLangs) {
      if (!raw) continue;
      const code = raw.toLowerCase().slice(0, 2);
      if (code === 'es') return 'es';
      if (code === 'ja') return 'ja';
      if (code === 'fr') return 'fr';
      if (code === 'en') return 'en';
    }

    return DEFAULT_LANG;
  }

  function formatTemplate(text, data) {
    return text.replace(/\{(\w+)\}/g, (_, key) => data[key] ?? '');
  }

  function setLanguage(lang) {
    if (!SUPPORTED_LANGS.includes(lang)) lang = DEFAULT_LANG;
    currentLang = lang;
    document.documentElement.lang = lang;

    const dict = I18N[lang] || I18N[DEFAULT_LANG];

    // Título de la página
    document.title = dict.pageTitle;

    // Actualizar todos los elementos con data-i18n
    document.querySelectorAll('[data-i18n]').forEach((el) => {
      const key = el.dataset.i18n;
      let text = dict[key];
      if (text === undefined) return;

      if (key === 'dlPrimaryDesc') {
        const tagFormatted = latestTag || 'v1.0.3';
        const sizeFormatted = latestSize ? ` (${latestSize})` : '';
        text = formatTemplate(text, { tag: tagFormatted, size: sizeFormatted });
      }

      el.innerHTML = text;
    });

    // Actualizar badges de versión
    const releaseEl = document.querySelector('[data-release]');
    if (releaseEl && latestTag) {
      releaseEl.textContent = formatTemplate(dict.releaseLabel, { tag: latestTag });
    }

    // Actualizar botones de idioma en ambas barras
    document.querySelectorAll('[data-lang]').forEach((btn) => {
      const active = btn.dataset.lang === lang;
      btn.setAttribute('aria-pressed', String(active));
    });

    const dockLangCurrent = document.getElementById('dockLangCurrent');
    if (dockLangCurrent) {
      dockLangCurrent.textContent = lang.toUpperCase();
    }

    // Guardar preferencia
    try {
      localStorage.setItem('aiiko_lang', lang);
    } catch (_) { /* ignore */ }

    // Reubicar indicador del dock si cambió ancho del texto
    if (typeof placeIndicator === 'function') {
      setTimeout(placeIndicator, 50);
    }
  }

  /* ---------- Aparición al hacer scroll ---------- */

  const revealItems = document.querySelectorAll('[data-reveal]');

  if ('IntersectionObserver' in window && !reduceMotion) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          io.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });

    revealItems.forEach((el) => io.observe(el));
  } else {
    revealItems.forEach((el) => el.classList.add('is-visible'));
  }

  /* ---------- Pestañas de capturas ---------- */

  const tabs = Array.from(document.querySelectorAll('.tab'));
  const stageImage = document.getElementById('stageImage');

  // Precarga de capturas
  tabs.forEach((tab) => {
    const img = new Image();
    img.src = tab.dataset.src;
  });

  function selectTab(tab, focus = false) {
    if (!tab || tab.getAttribute('aria-selected') === 'true') return;

    tabs.forEach((t) => {
      const selected = t === tab;
      t.setAttribute('aria-selected', String(selected));
      t.tabIndex = selected ? 0 : -1;
    });

    if (focus) tab.focus();
    tab.scrollIntoView({ block: 'nearest', inline: 'nearest', behavior: reduceMotion ? 'auto' : 'smooth' });

    const swap = () => {
      const dict = I18N[currentLang] || I18N[DEFAULT_LANG];
      stageImage.src = tab.dataset.src;
      stageImage.width = Number(tab.dataset.w);
      stageImage.height = Number(tab.dataset.h);
      stageImage.alt = `${dict.shotAltPrefix}${tab.textContent.trim()}`;
      stageImage.classList.remove('is-loading');
    };

    if (reduceMotion) {
      swap();
      return;
    }
    stageImage.classList.add('is-loading');
    setTimeout(swap, 180);
  }

  tabs.forEach((tab, i) => {
    tab.tabIndex = tab.getAttribute('aria-selected') === 'true' ? 0 : -1;
    tab.addEventListener('click', () => selectTab(tab));
    tab.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowRight') {
        e.preventDefault();
        selectTab(tabs[(i + 1) % tabs.length], true);
      }
      if (e.key === 'ArrowLeft') {
        e.preventDefault();
        selectTab(tabs[(i - 1 + tabs.length) % tabs.length], true);
      }
    });
  });

  /* ---------- Dock: sección activa ---------- */

  const dockLinks = Array.from(document.querySelectorAll('.dock-link'));
  const indicator = document.querySelector('.dock-indicator');
  const sections = dockLinks
    .map((link) => document.getElementById(link.dataset.target))
    .filter(Boolean);

  let activeId = null;

  function placeIndicator() {
    const link = dockLinks.find((l) => l.dataset.target === activeId);
    if (!link || link.offsetParent === null) {
      indicator.classList.remove('is-ready');
      return;
    }
    const x = link.offsetLeft + link.offsetWidth / 2 - indicator.offsetWidth / 2;
    indicator.style.transform = `translateX(${x}px)`;
    indicator.classList.add('is-ready');
  }

  function updateActive() {
    const probe = window.innerHeight * 0.35;
    let current = sections[0]?.id;

    sections.forEach((section) => {
      if (section.getBoundingClientRect().top <= probe) current = section.id;
    });

    if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2) {
      current = sections[sections.length - 1]?.id;
    }

    if (current === activeId) return;
    activeId = current;

    dockLinks.forEach((link) => {
      if (link.dataset.target === activeId) link.setAttribute('aria-current', 'true');
      else link.removeAttribute('aria-current');
    });
    placeIndicator();
  }

  let ticking = false;
  window.addEventListener('scroll', () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => {
      updateActive();
      ticking = false;
    });
  }, { passive: true });

  window.addEventListener('resize', placeIndicator);

  /* ---------- Listeners de cambio de idioma ---------- */

  document.querySelectorAll('[data-lang]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const targetLang = btn.dataset.lang;
      if (targetLang && targetLang !== currentLang) {
        setLanguage(targetLang);
      }
    });
  });

  const dockLangMobile = document.getElementById('dockLangMobile');
  if (dockLangMobile) {
    dockLangMobile.addEventListener('click', () => {
      const nextIdx = (SUPPORTED_LANGS.indexOf(currentLang) + 1) % SUPPORTED_LANGS.length;
      setLanguage(SUPPORTED_LANGS[nextIdx]);
    });
  }

  /* ---------- Inicialización de idioma ---------- */

  const initialLang = detectInitialLanguage();
  setLanguage(initialLang);
  updateActive();

  /* ---------- Datos de GitHub Releases ---------- */

  const releaseEl = document.querySelector('[data-release]');
  const heroDownloadBtn = document.getElementById('heroDownloadBtn');
  const directDownloadBtn = document.getElementById('directDownloadBtn');

  if ('fetch' in window) {
    fetch('https://api.github.com/repos/HirayamaAiiko/Aiiko-Music/releases/latest', {
      headers: { Accept: 'application/vnd.github+json' }
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (!data || !data.tag_name) return;

        latestTag = data.tag_name;

        // Buscar archivo .zip en los assets
        const zipAsset = Array.isArray(data.assets)
          ? data.assets.find((a) => a.name && a.name.toLowerCase().endsWith('.zip'))
          : null;

        if (zipAsset) {
          directZipUrl = zipAsset.browser_download_url;
          if (zipAsset.size) {
            const mb = (zipAsset.size / (1024 * 1024)).toFixed(0);
            latestSize = `~${mb} MB`;
          }

          if (directDownloadBtn && directZipUrl) {
            directDownloadBtn.href = directZipUrl;
          }
          if (heroDownloadBtn && directZipUrl) {
            heroDownloadBtn.href = directZipUrl;
          }
        }

        // Refrescar strings de versión
        const dict = I18N[currentLang] || I18N[DEFAULT_LANG];
        if (releaseEl) {
          releaseEl.textContent = formatTemplate(dict.releaseLabel, { tag: latestTag });
          releaseEl.hidden = false;
        }

        const dlBadge = document.getElementById('dlBadge');
        if (dlBadge) {
          const sizeFormatted = latestSize ? ` (${latestSize})` : '';
          dlBadge.innerHTML = formatTemplate(dict.dlPrimaryDesc, {
            tag: latestTag,
            size: sizeFormatted
          });
        }
      })
      .catch(() => {
        // Fallback silencioso sin conexión
      });
  }
})();
