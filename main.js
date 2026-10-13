// Aiiko Music — Sitio web oficial
// Idioma (EN por defecto, detección del sistema, ES / JA / FR) con menú flotante,
// pestañas de capturas, visor ampliado, dock con sección activa y
// datos de la última release leídos desde la API de GitHub.

(() => {
  'use strict';

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- Textos ---------- */

  const I18N = {
    en: {
      pageTitle: 'Aiiko Music — Music player for your personal library',
      langLabel: 'Language',
      dockLabel: 'Sections',
      footerNav: 'Project links',
      zoomLabel: 'Enlarge screenshot',
      closeLabel: 'Close',

      heroTitle: 'A music player for your personal library.',
      heroLede: 'Aiiko Music is a local music player for Windows, designed for personal music collections. It brings together playback, albums, artists, playlists, lyrics and metadata in one place.',
      heroDownload: 'Download for Windows',
      heroSource: 'Source code on GitHub',
      heroMeta: 'Windows 10 & 11 · Open source (GPL-3.0)',
      heroAlt: 'Aiiko Music now playing view with lyrics',
      releaseLabel: 'Latest release: {tag}',

      navHome: 'Home',
      navFeatures: 'Features',
      navScreenshots: 'Screenshots',
      navFormats: 'Formats',
      navInstall: 'Installation',
      navDownload: 'Download',
      navHomeShort: 'Home',
      navFeaturesShort: 'Features',
      navScreenshotsShort: 'Screens',
      navFormatsShort: 'Formats',
      navInstallShort: 'Install',
      navDownloadShort: 'Download',

      featuresTitle: 'Features',
      catLibraryTitle: 'Library',
      fLibrary1: 'Local music library',
      fLibrary2: 'Album and artist browsing',
      fLibrary3: 'Playlist management',
      fLibrary4: 'Search across the whole library',
      catPlaybackTitle: 'Playback',
      fPlayback1: '10-band equalizer',
      fPlayback2: 'Queue and shuffle',
      fPlayback3: 'Gapless playback',
      fPlayback4: 'Audio visualizer',
      catLyricsTitle: 'Lyrics & metadata',
      fLyrics1: 'Lyrics, including .lrc files and online search',
      fLyrics2: 'Lyrics editor',
      fLyrics3: 'Metadata editor',
      fLyrics4: 'Album art',
      catInterfaceTitle: 'Interface',
      fInterface1: 'Floating mini player',
      fInterface2: 'Fullscreen view',
      fInterface3: 'Appearance and accent customization',
      fInterface4: 'Keyboard shortcuts',
      catIntegrationsTitle: 'Integrations',
      fInteg1: 'Discord Rich Presence',
      fInteg2: 'Last.fm scrobbling',

      shotsTitle: 'Screenshots',
      shotAltPrefix: 'Aiiko Music screenshot: ',
      tabHome: 'Home',
      tabLibrary: 'Library',
      tabArtists: 'Artists',
      tabArtistDetail: 'Artist detail',
      tabSearch: 'Search',
      tabPlaylists: 'Playlists',
      tabLyricsEditor: 'Lyrics editor',

      formatsTitle: 'Supported formats',
      formatsSub: 'Aiiko Music plays the most common audio formats, including:',
      formatsNote: 'Format support depends on the capabilities of the playback engine.',

      installTitle: 'Installation',
      installSub: 'For Windows 10 and 11. The easiest way is to download the latest release.',
      dlPrimaryTitle: 'Download latest release',
      dlSecondaryTitle: 'All releases',
      dlSecondaryDesc: 'Previous versions and release notes',
      step1: 'Download the ZIP file with the button above.',
      step2: 'Extract it to a folder of your choice.',
      step3: 'Open <code>Aiiko Music.exe</code> and follow the prompts shown on first launch.',
      sourceNote: 'If you prefer to run it from source, the instructions are in the',
      sourceNoteAfter: '.',

      footerCredit: 'Aiiko Music · Developed by Aiiko Hirayama · © 2026 · GPL-3.0',
      footerLicense: 'License'
    },

    es: {
      pageTitle: 'Aiiko Music — Reproductor de música para tu propia biblioteca',
      langLabel: 'Idioma',
      dockLabel: 'Secciones',
      footerNav: 'Enlaces del proyecto',
      zoomLabel: 'Ampliar captura',
      closeLabel: 'Cerrar',

      heroTitle: 'Un reproductor de música para tu propia biblioteca.',
      heroLede: 'Aiiko Music es un reproductor local para Windows, pensado para colecciones de música personales. Reúne reproducción, álbumes, artistas, listas, letras y metadatos en un solo lugar.',
      heroDownload: 'Descargar para Windows',
      heroSource: 'Código fuente en GitHub',
      heroMeta: 'Windows 10 y 11 · Código abierto (GPL-3.0)',
      heroAlt: 'Vista de reproducción de Aiiko Music con letras',
      releaseLabel: 'Última versión: {tag}',

      navHome: 'Inicio',
      navFeatures: 'Funciones',
      navScreenshots: 'Capturas',
      navFormats: 'Formatos',
      navInstall: 'Instalación',
      navDownload: 'Descargar',
      navHomeShort: 'Inicio',
      navFeaturesShort: 'Funciones',
      navScreenshotsShort: 'Capturas',
      navFormatsShort: 'Formatos',
      navInstallShort: 'Instalar',
      navDownloadShort: 'Descarga',

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
      fLyrics1: 'Letras, incluidos archivos .lrc y búsqueda en línea',
      fLyrics2: 'Editor de letras',
      fLyrics3: 'Editor de metadatos',
      fLyrics4: 'Carátulas de álbum',
      catInterfaceTitle: 'Interfaz',
      fInterface1: 'Mini reproductor flotante',
      fInterface2: 'Vista a pantalla completa',
      fInterface3: 'Personalización de apariencia y acento',
      fInterface4: 'Atajos de teclado',
      catIntegrationsTitle: 'Integraciones',
      fInteg1: 'Discord Rich Presence',
      fInteg2: 'Scrobbling en Last.fm',

      shotsTitle: 'Capturas',
      shotAltPrefix: 'Captura de Aiiko Music: ',
      tabHome: 'Inicio',
      tabLibrary: 'Biblioteca',
      tabArtists: 'Artistas',
      tabArtistDetail: 'Detalle de artista',
      tabSearch: 'Búsqueda',
      tabPlaylists: 'Listas',
      tabLyricsEditor: 'Editor de letras',

      formatsTitle: 'Formatos compatibles',
      formatsSub: 'Aiiko Music reproduce los formatos de audio más comunes, entre ellos:',
      formatsNote: 'La compatibilidad depende de las capacidades del motor de reproducción.',

      installTitle: 'Instalación',
      installSub: 'Para Windows 10 y 11. La forma más sencilla es descargar la última versión publicada.',
      dlPrimaryTitle: 'Descargar última versión',
      dlSecondaryTitle: 'Todas las versiones',
      dlSecondaryDesc: 'Versiones anteriores y notas de cada versión',
      step1: 'Descarga el archivo ZIP con el botón de arriba.',
      step2: 'Extráelo en la carpeta que prefieras.',
      step3: 'Abre <code>Aiiko Music.exe</code> y sigue las indicaciones del primer inicio.',
      sourceNote: 'Si prefieres ejecutarlo desde el código fuente, las instrucciones están en el',
      sourceNoteAfter: '.',

      footerCredit: 'Aiiko Music · Desarrollado por Aiiko Hirayama · © 2026 · GPL-3.0',
      footerLicense: 'Licencia'
    },

    ja: {
      pageTitle: 'Aiiko Music — あなたの音楽ライブラリのためのプレーヤー',
      langLabel: '言語',
      dockLabel: 'セクション',
      footerNav: 'プロジェクトのリンク',
      zoomLabel: 'スクリーンショットを拡大',
      closeLabel: '閉じる',

      heroTitle: 'あなたの音楽ライブラリのための音楽プレーヤー。',
      heroLede: 'Aiiko Music は、個人の音楽コレクションのために作られた Windows 向けのローカル音楽プレーヤーです。再生、アルバム、アーティスト、プレイリスト、歌詞、メタデータをひとつにまとめます。',
      heroDownload: 'Windows 版をダウンロード',
      heroSource: 'GitHub でソースコードを見る',
      heroMeta: 'Windows 10 / 11 · オープンソース (GPL-3.0)',
      heroAlt: 'Aiiko Music の再生画面（歌詞表示）',
      releaseLabel: '最新バージョン: {tag}',

      navHome: 'ホーム',
      navFeatures: '機能',
      navScreenshots: 'スクリーンショット',
      navFormats: '対応形式',
      navInstall: 'インストール',
      navDownload: 'ダウンロード',
      navHomeShort: 'ホーム',
      navFeaturesShort: '機能',
      navScreenshotsShort: '画面',
      navFormatsShort: '形式',
      navInstallShort: '導入',
      navDownloadShort: '入手',

      featuresTitle: '機能',
      catLibraryTitle: 'ライブラリ',
      fLibrary1: 'ローカル音楽ライブラリ',
      fLibrary2: 'アルバム・アーティスト別の閲覧',
      fLibrary3: 'プレイリスト管理',
      fLibrary4: 'ライブラリ全体の検索',
      catPlaybackTitle: '再生',
      fPlayback1: '10バンドイコライザー',
      fPlayback2: 'キューとシャッフル再生',
      fPlayback3: 'ギャップレス再生',
      fPlayback4: 'オーディオビジュアライザー',
      catLyricsTitle: '歌詞とメタデータ',
      fLyrics1: '歌詞（.lrc ファイルとオンライン検索に対応）',
      fLyrics2: '歌詞エディター',
      fLyrics3: 'メタデータエディター',
      fLyrics4: 'アルバムアート',
      catInterfaceTitle: 'インターフェース',
      fInterface1: 'フローティングミニプレーヤー',
      fInterface2: '全画面表示',
      fInterface3: '外観とアクセントカラーのカスタマイズ',
      fInterface4: 'キーボードショートカット',
      catIntegrationsTitle: '連携',
      fInteg1: 'Discord Rich Presence',
      fInteg2: 'Last.fm へのスクロブル',

      shotsTitle: 'スクリーンショット',
      shotAltPrefix: 'Aiiko Music のスクリーンショット: ',
      tabHome: 'ホーム',
      tabLibrary: 'ライブラリ',
      tabArtists: 'アーティスト',
      tabArtistDetail: 'アーティスト詳細',
      tabSearch: '検索',
      tabPlaylists: 'プレイリスト',
      tabLyricsEditor: '歌詞エディター',

      formatsTitle: '対応フォーマット',
      formatsSub: 'Aiiko Music は一般的なオーディオ形式を再生できます。主な形式：',
      formatsNote: '対応状況は再生エンジンの機能によって異なります。',

      installTitle: 'インストール',
      installSub: 'Windows 10 / 11 対応。最新バージョンをダウンロードするのが最も簡単です。',
      dlPrimaryTitle: '最新バージョンをダウンロード',
      dlSecondaryTitle: 'すべてのバージョン',
      dlSecondaryDesc: '過去のバージョンとリリースノート',
      step1: '上のボタンから ZIP ファイルをダウンロードします。',
      step2: '任意のフォルダーに展開します。',
      step3: '<code>Aiiko Music.exe</code> を開き、初回起動時の案内に従ってください。',
      sourceNote: 'ソースコードから実行する場合の手順は',
      sourceNoteAfter: ' に記載しています。',

      footerCredit: 'Aiiko Music · 開発: Aiiko Hirayama · © 2026 · GPL-3.0',
      footerLicense: 'ライセンス'
    },

    fr: {
      pageTitle: 'Aiiko Music — Lecteur de musique pour votre bibliothèque',
      langLabel: 'Langue',
      dockLabel: 'Sections',
      footerNav: 'Liens du projet',
      zoomLabel: 'Agrandir la capture',
      closeLabel: 'Fermer',

      heroTitle: 'Un lecteur de musique pour votre propre bibliothèque.',
      heroLede: 'Aiiko Music est un lecteur local pour Windows, pensé pour les collections musicales personnelles. Il réunit lecture, albums, artistes, playlists, paroles et métadonnées au même endroit.',
      heroDownload: 'Télécharger pour Windows',
      heroSource: 'Code source sur GitHub',
      heroMeta: 'Windows 10 et 11 · Open source (GPL-3.0)',
      heroAlt: 'Vue de lecture d’Aiiko Music avec les paroles',
      releaseLabel: 'Dernière version : {tag}',

      navHome: 'Accueil',
      navFeatures: 'Fonctionnalités',
      navScreenshots: 'Captures',
      navFormats: 'Formats',
      navInstall: 'Installation',
      navDownload: 'Télécharger',
      navHomeShort: 'Accueil',
      navFeaturesShort: 'Fonctions',
      navScreenshotsShort: 'Captures',
      navFormatsShort: 'Formats',
      navInstallShort: 'Installer',
      navDownloadShort: 'Obtenir',

      featuresTitle: 'Fonctionnalités',
      catLibraryTitle: 'Bibliothèque',
      fLibrary1: 'Bibliothèque musicale locale',
      fLibrary2: 'Navigation par albums et artistes',
      fLibrary3: 'Gestion des playlists',
      fLibrary4: 'Recherche dans toute la bibliothèque',
      catPlaybackTitle: 'Lecture',
      fPlayback1: 'Égaliseur 10 bandes',
      fPlayback2: 'File d’attente et lecture aléatoire',
      fPlayback3: 'Lecture sans blanc (gapless)',
      fPlayback4: 'Visualiseur audio',
      catLyricsTitle: 'Paroles et métadonnées',
      fLyrics1: 'Paroles, y compris les fichiers .lrc et la recherche en ligne',
      fLyrics2: 'Éditeur de paroles',
      fLyrics3: 'Éditeur de métadonnées',
      fLyrics4: 'Pochettes d’album',
      catInterfaceTitle: 'Interface',
      fInterface1: 'Mini-lecteur flottant',
      fInterface2: 'Vue plein écran',
      fInterface3: 'Personnalisation de l’apparence et de l’accent',
      fInterface4: 'Raccourcis clavier',
      catIntegrationsTitle: 'Intégrations',
      fInteg1: 'Discord Rich Presence',
      fInteg2: 'Scrobbling Last.fm',

      shotsTitle: 'Captures d’écran',
      shotAltPrefix: 'Capture d’Aiiko Music : ',
      tabHome: 'Accueil',
      tabLibrary: 'Bibliothèque',
      tabArtists: 'Artistes',
      tabArtistDetail: 'Détail d’artiste',
      tabSearch: 'Recherche',
      tabPlaylists: 'Playlists',
      tabLyricsEditor: 'Éditeur de paroles',

      formatsTitle: 'Formats pris en charge',
      formatsSub: 'Aiiko Music lit les formats audio les plus courants, notamment :',
      formatsNote: 'La compatibilité dépend des capacités du moteur de lecture.',

      installTitle: 'Installation',
      installSub: 'Pour Windows 10 et 11. Le plus simple est de télécharger la dernière version publiée.',
      dlPrimaryTitle: 'Télécharger la dernière version',
      dlSecondaryTitle: 'Toutes les versions',
      dlSecondaryDesc: 'Versions précédentes et notes de version',
      step1: 'Téléchargez le fichier ZIP avec le bouton ci-dessus.',
      step2: 'Extrayez-le dans le dossier de votre choix.',
      step3: 'Ouvrez <code>Aiiko Music.exe</code> et suivez les indications du premier démarrage.',
      sourceNote: 'Pour l’exécuter depuis le code source, les instructions se trouvent dans le',
      sourceNoteAfter: '.',

      footerCredit: 'Aiiko Music · Développé par Aiiko Hirayama · © 2026 · GPL-3.0',
      footerLicense: 'Licence'
    }
  };

  const LANGS = ['en', 'es', 'ja', 'fr'];
  const DEFAULT_LANG = 'en';
  const LANG_KEY = 'aiiko_lang';

  const REPO_API = 'https://api.github.com/repos/HirayamaAiiko/Aiiko-Music/releases/latest';
  const RELEASE_KEY = 'aiiko_release_v1';
  const RELEASE_TTL = 30 * 60 * 1000; // 30 min: evita agotar el límite de la API

  const BASE_RATIO = 1366 / 742;

  let currentLang = DEFAULT_LANG;
  const release = { tag: '', size: '', url: '' };

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  /* ---------- Elementos ---------- */

  const tabs = $$('.tab');
  const stagePanel = $('#stagePanel');
  const stageZoom = $('#stageZoom');
  const stageImage = $('#stageImage');

  const dockLinks = $$('.dock-link');
  const indicator = $('.dock-indicator');
  const sections = dockLinks
    .map((link) => document.getElementById(link.dataset.target))
    .filter(Boolean);

  const langFloat = $('#langFloat');
  const langToggle = $('#langToggle');
  const langCode = $('#langCode');
  const langOptions = $$('.lang-option');

  const lightbox = $('#lightbox');
  const lightboxImg = $('#lightboxImg');

  const releaseEl = $('[data-release]');
  const dlBadge = $('#dlBadge');
  const downloadLinks = [$('#heroDownloadBtn'), $('#directDownloadBtn')].filter(Boolean);

  /* ---------- Utilidades ---------- */

  function t(key) {
    const dict = I18N[currentLang] || I18N[DEFAULT_LANG];
    return dict[key] ?? I18N[DEFAULT_LANG][key] ?? '';
  }

  function format(text, data) {
    return text.replace(/\{(\w+)\}/g, (_, key) => data[key] ?? '');
  }

  function storageGet(store, key) {
    try { return store.getItem(key); } catch (_) { return null; }
  }

  function storageSet(store, key, value) {
    try { store.setItem(key, value); } catch (_) { /* modo privado / bloqueado */ }
  }

  /* ---------- Idioma ---------- */

  // Prioridad: elección guardada del usuario > idioma del sistema > inglés
  function detectInitialLanguage() {
    const saved = storageGet(localStorage, LANG_KEY);
    if (saved && LANGS.includes(saved)) return saved;

    const prefs = navigator.languages && navigator.languages.length
      ? navigator.languages
      : [navigator.language || ''];

    for (const raw of prefs) {
      const code = String(raw).toLowerCase().slice(0, 2);
      if (LANGS.includes(code)) return code;
    }
    return DEFAULT_LANG;
  }

  function setLanguage(lang, persist = false) {
    if (!LANGS.includes(lang)) lang = DEFAULT_LANG;
    currentLang = lang;
    document.documentElement.lang = lang;
    document.title = t('pageTitle');

    $$('[data-i18n]').forEach((el) => {
      const value = t(el.dataset.i18n);
      if (!value) return;
      if (value.includes('<')) el.innerHTML = value;
      else el.textContent = value;
    });

    $$('[data-i18n-label]').forEach((el) => {
      el.setAttribute('aria-label', t(el.dataset.i18nLabel));
    });

    $$('[data-i18n-alt]').forEach((el) => {
      el.alt = t(el.dataset.i18nAlt);
    });

    langOptions.forEach((opt) => {
      opt.setAttribute('aria-checked', String(opt.dataset.lang === lang));
    });
    if (langCode) langCode.textContent = lang.toUpperCase();

    updateStageAlt();
    renderRelease();

    // Solo se guarda cuando el usuario elige; así la detección del sistema sigue funcionando
    if (persist) storageSet(localStorage, LANG_KEY, lang);

    requestAnimationFrame(placeIndicator);
  }

  /* ---------- Menú de idioma flotante ---------- */

  function isLangMenuOpen() {
    return langFloat.classList.contains('is-open');
  }

  function openLangMenu(focusItem) {
    langFloat.classList.add('is-open');
    langToggle.setAttribute('aria-expanded', 'true');
    if (focusItem) {
      const current = langOptions.find((o) => o.getAttribute('aria-checked') === 'true') || langOptions[0];
      requestAnimationFrame(() => current.focus());
    }
  }

  function closeLangMenu(returnFocus) {
    langFloat.classList.remove('is-open');
    langToggle.setAttribute('aria-expanded', 'false');
    if (returnFocus) langToggle.focus();
  }

  function initLangMenu() {
    if (!langFloat || !langToggle) return;

    langToggle.addEventListener('click', () => {
      if (isLangMenuOpen()) closeLangMenu(false);
      else openLangMenu(false);
    });

    langToggle.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault();
        openLangMenu(true);
      }
    });

    langOptions.forEach((opt, i) => {
      opt.addEventListener('click', () => {
        setLanguage(opt.dataset.lang, true);
        closeLangMenu(true);
      });

      opt.addEventListener('keydown', (e) => {
        const last = langOptions.length - 1;
        let next = null;
        if (e.key === 'ArrowDown') next = i === last ? 0 : i + 1;
        if (e.key === 'ArrowUp') next = i === 0 ? last : i - 1;
        if (e.key === 'Home') next = 0;
        if (e.key === 'End') next = last;
        if (next !== null) {
          e.preventDefault();
          langOptions[next].focus();
        }
        if (e.key === 'Escape') {
          e.preventDefault();
          closeLangMenu(true);
        }
        if (e.key === 'Tab') closeLangMenu(false);
      });
    });

    document.addEventListener('click', (e) => {
      if (isLangMenuOpen() && !langFloat.contains(e.target)) closeLangMenu(false);
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && isLangMenuOpen()) closeLangMenu(true);
    });
  }

  /* ---------- Aparición al hacer scroll ---------- */

  function initReveal() {
    const items = $$('[data-reveal]');

    if (!('IntersectionObserver' in window) || reduceMotion) {
      items.forEach((el) => el.classList.add('is-visible'));
      return;
    }

    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-visible');
        io.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });

    items.forEach((el) => io.observe(el));
  }

  /* ---------- Pestañas de capturas ---------- */

  function selectedTab() {
    return tabs.find((tab) => tab.getAttribute('aria-selected') === 'true') || tabs[0];
  }

  function updateStageAlt() {
    const tab = selectedTab();
    if (tab && stageImage) stageImage.alt = t('shotAltPrefix') + tab.textContent.trim();
  }

  // Las capturas con otra proporción se estrechan para conservar la misma altura
  function fitStage(w, h) {
    if (!stageZoom) return;
    const ratio = w / h;
    stageZoom.style.width = ratio < BASE_RATIO ? `${((ratio / BASE_RATIO) * 100).toFixed(2)}%` : '100%';
  }

  function selectTab(tab, focus = false) {
    if (!tab || tab.getAttribute('aria-selected') === 'true') return;

    tabs.forEach((t2) => {
      const selected = t2 === tab;
      t2.setAttribute('aria-selected', String(selected));
      t2.tabIndex = selected ? 0 : -1;
    });

    if (focus) tab.focus();
    tab.scrollIntoView({ block: 'nearest', inline: 'nearest', behavior: reduceMotion ? 'auto' : 'smooth' });
    stagePanel?.setAttribute('aria-labelledby', tab.id);

    const swap = () => {
      const w = Number(tab.dataset.w);
      const h = Number(tab.dataset.h);
      stageImage.src = tab.dataset.src;
      stageImage.width = w;
      stageImage.height = h;
      fitStage(w, h);
      updateStageAlt();
      stageImage.classList.remove('is-loading');
    };

    if (reduceMotion) {
      swap();
      return;
    }
    stageImage.classList.add('is-loading');
    setTimeout(swap, 180);
  }

  function initTabs() {
    if (!tabs.length || !stageImage) return;

    // Precarga para que el cambio entre capturas sea inmediato
    tabs.forEach((tab) => { const img = new Image(); img.src = tab.dataset.src; });

    tabs.forEach((tab, i) => {
      tab.tabIndex = tab.getAttribute('aria-selected') === 'true' ? 0 : -1;
      tab.addEventListener('click', () => selectTab(tab));
      tab.addEventListener('keydown', (e) => {
        let next = null;
        if (e.key === 'ArrowRight') next = (i + 1) % tabs.length;
        if (e.key === 'ArrowLeft') next = (i - 1 + tabs.length) % tabs.length;
        if (e.key === 'Home') next = 0;
        if (e.key === 'End') next = tabs.length - 1;
        if (next !== null) {
          e.preventDefault();
          selectTab(tabs[next], true);
        }
      });
    });
  }

  /* ---------- Visor ampliado ---------- */

  function initLightbox() {
    const zooms = $$('.zoom');
    const supported = lightbox && typeof lightbox.showModal === 'function';

    zooms.forEach((btn) => {
      btn.addEventListener('click', () => {
        const img = btn.querySelector('img');
        if (!img) return;
        const src = img.currentSrc || img.src;

        if (!supported) {
          window.open(src, '_blank', 'noopener');
          return;
        }
        lightboxImg.src = src;
        lightboxImg.alt = img.alt;
        lightbox.showModal();
        const scroller = lightbox.querySelector('.lightbox-scroll');
        if (scroller) scroller.scrollLeft = 0;
      });
    });

    if (!supported) return;

    // Cualquier clic fuera de la imagen (fondo o botón de cerrar) cierra el visor
    lightbox.addEventListener('click', (e) => {
      if (e.target !== lightboxImg) lightbox.close();
    });
  }

  /* ---------- Dock: sección activa ---------- */

  let activeId = null;

  function placeIndicator() {
    if (!indicator) return;
    const link = dockLinks.find((l) => l.dataset.target === activeId);

    // En móvil el indicador está oculto (el estado activo se marca con color)
    if (!link || link.offsetParent === null || indicator.offsetParent === null) {
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

    // Al llegar al final de la página se marca la última sección
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

  function initDock() {
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
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(placeIndicator);
  }

  /* ---------- Última versión publicada ---------- */

  function renderRelease() {
    if (releaseEl && release.tag) {
      releaseEl.textContent = format(t('releaseLabel'), { tag: release.tag });
      releaseEl.hidden = false;
    }

    if (dlBadge) {
      dlBadge.textContent = [
        release.tag,
        'Windows 10/11',
        release.size ? `ZIP (${release.size})` : 'ZIP'
      ].filter(Boolean).join(' · ');
    }
  }

  function applyRelease(info) {
    release.tag = info.tag || '';
    release.size = info.size || '';
    release.url = info.url || '';
    if (release.url) downloadLinks.forEach((a) => { a.href = release.url; });
    renderRelease();
  }

  function loadRelease() {
    const cached = storageGet(sessionStorage, RELEASE_KEY);
    if (cached) {
      try {
        const info = JSON.parse(cached);
        if (info && Date.now() - info.t < RELEASE_TTL) {
          applyRelease(info);
          return;
        }
      } catch (_) { /* caché corrupta: se vuelve a pedir */ }
    }

    if (!('fetch' in window)) return;

    fetch(REPO_API, { headers: { Accept: 'application/vnd.github+json' } })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (!data || !data.tag_name) return;

        const zip = Array.isArray(data.assets)
          ? data.assets.find((a) => a.name && a.name.toLowerCase().endsWith('.zip'))
          : null;

        const info = {
          tag: data.tag_name,
          url: zip ? zip.browser_download_url : '',
          size: zip && zip.size ? `~${Math.round(zip.size / (1024 * 1024))} MB` : '',
          t: Date.now()
        };

        applyRelease(info);
        storageSet(sessionStorage, RELEASE_KEY, JSON.stringify(info));
      })
      .catch(() => { /* sin conexión o límite de la API: se mantiene el enlace a /releases/latest */ });
  }

  /* ---------- Inicio ---------- */

  initReveal();
  initTabs();
  initLightbox();
  initLangMenu();
  initDock();

  setLanguage(detectInitialLanguage(), false);
  updateActive();
  loadRelease();
})();
