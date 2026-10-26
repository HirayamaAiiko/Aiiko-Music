// Aiiko Music — Sitio web oficial
// Idioma (EN por defecto, detección del sistema, ES / JA / FR) con menú flotante,
// pestañas de capturas, visor ampliado, dock con sección activa y
// datos de la última release leídos desde la API de GitHub.

(() => {
  'use strict';

  // Control estricto de versión, limpieza de caché obsoleta y restauración de scroll
  const SITE_VERSION = '1.17.11';
  try {
    if ('scrollRestoration' in history) {
      history.scrollRestoration = 'manual';
    }
    const storedVer = localStorage.getItem('aiiko_site_version');
    if (storedVer && storedVer !== SITE_VERSION) {
      sessionStorage.clear();
      if ('caches' in window) {
        caches.keys().then((names) => {
          names.forEach((name) => caches.delete(name));
        });
      }
    }
    localStorage.setItem('aiiko_site_version', SITE_VERSION);
  } catch (_) {}

  // En móviles y desktop, al abrir el sitio garantizar que siempre inicie en el encabezado (#inicio)
  if (!window.location.hash || window.location.hash === '#instalacion' || window.location.hash === '#inicio') {
    if (window.location.hash === '#instalacion') {
      history.replaceState(null, '', window.location.pathname + window.location.search);
    }
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
  }

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
      heroExplore: 'Explore features',
      heroSource: 'Source code on GitHub',
      heroMeta: 'Windows 10 & 11 · Open source (GPL-3.0)',
      heroAlt: 'Aiiko Music now playing view with lyrics',
      releaseLabel: 'Latest release: {tag}',
      previewApp: 'Preview app',

      navHome: 'Home',
      navFeatures: 'Features',
      navScreenshots: 'Gallery',
      navFormats: 'Formats',
      navInstall: 'Installation',
      navDownload: 'Download',
      navHomeShort: 'Home',
      navFeaturesShort: 'Features',
      navScreenshotsShort: 'Gallery',
      navFormatsShort: 'Formats',
      navInstallShort: 'Install',
      navDownloadShort: 'Download',

                  featuresEyebrow: 'Features',
      featuresHeadline: 'Everything for your personal library.',
      featuresLead: 'A music player designed for personal music collections.',
      touchSwipeHint: 'Swipe or tap to explore',

            catTab1: 'Audio & Playback',
      catEyebrow1: '01 · Audio Engine & Performance',
      catTitle1: 'Sound Quality Matters',
      catSub1: 'Whether you play your music on an audiophile setup or on a laptop, Aiiko Music is tuned to fulfill all your needs.',

      catTab2: 'Library & Organization',
      catEyebrow2: '02 · Catalog & Discovery',
      catTitle2: 'Manage Your Music Collection',
      catSub2: 'Designed for personal libraries, with hierarchical artist views, zero-latency search, and custom playlists.',

      catTab3: 'Lyrics & Metadata',
      catEyebrow3: '03 · Words & Precision Tags',
      catTitle3: 'Lyrics & Metadata Precision',
      catSub3: 'Synchronized karaoke lyrics, advanced editor tools, and full metadata tagging for pristine collection cataloging.',

      catTab4: 'Experience & Customization',
      catEyebrow4: '04 · Interface & Ecosystem',
      catTitle4: 'Experience & Customization',
      catSub4: 'Tailor your daily listening with floating players, Discord Rich Presence, Last.fm scrobbling, and shortcuts.',

      featCat1: 'Audio & Playback',
      feat_1_1: '10-band equalizer with custom tuning',
      feat_1_2: 'Gapless playback for uninterrupted listening',
      feat_1_3: 'Queue and shuffle playback modes',
      feat_1_4: 'Audio visualizer',

      featCat2: 'Library & Organization',
      feat_2_1: 'Local music library management',
      feat_2_2: 'Album and artist browsing',
      feat_2_3: 'Playlist management',
      feat_2_4: 'Library-wide search to find tracks instantly',

      featCat3: 'Lyrics & Metadata',
      feat_3_1: 'Lyrics support, including local .lrc files and an integrated online finder',
      feat_3_2: 'Advanced lyrics editor with synchronization tools',
      feat_3_3: 'Metadata editor for tagging your collection',
      feat_3_4: 'Album artwork display and handling',

      featCat4: 'Experience & Customization',
      feat_4_1: 'Floating mini player',
      feat_4_2: 'Fullscreen viewer',
      feat_4_3: 'Appearance & accent customization',
      feat_4_4: 'Discord Rich Presence',
      feat_4_5: 'Last.fm scrobbling',
      feat_4_6: 'Keyboard shortcuts',

      featuresMoreBtn: 'View all features',
      featuresModalTitle: 'All Features & Capabilities',
      gaplessBadge: 'GAPLESS · 0.0s SILENCE',
      gaplessNotice: '0.0s SILENCE · CONTINUOUS TRANSITION',
      feat_1_6: 'Floating mini-player & Fullscreen',
      feat_theme_title: 'MAKE IT YOURS',
      feat_desc_1: 'Adjust the sound to your preference, and use the crossfeed functions.',
      feat_desc_2: 'Continuous audio stream transitions with zero silence between consecutive tracks.',
      feat_desc_3: 'Beautiful and dynamic spectrum visualizer that dances to the rhythm of your music.',
      feat_desc_4: 'Browse your music seamlessly in a clean, hassle-free organized library.',
      feat_desc_5: 'Synchronized karaoke-style lyrics with local .lrc support, language translation, and built-in advanced editor.',
      feat_desc_6: 'Always-on-top desktop mini player and immersive fullscreen view for your displays.',
      feat_desc_7: 'Customize your player\'s accent color and visual theme to your liking.',

      shotsTitle: 'Gallery',
      capturasTitle: 'Interactive Gallery',
      capturasLead: 'A dark, distraction-free environment crafted for deep listening sessions.',
      shotsBadge: 'Interactive Gallery',
      shotsSub: 'Scroll to explore every corner of the app in high resolution.',
      shotAltPrefix: 'Aiiko Music screenshot: ',
      zoomBtn: 'Enlarge',
      tabHome: 'Home',
      tabLibrary: 'Library',
      tabNowPlaying: 'Now Playing',
      tabArtists: 'Artists',
      tabArtistDetail: 'Artist detail',
      tabSearch: 'Search',
      tabPlaylists: 'Playlists',
      tabLyricsEditor: 'Lyrics editor',
      shotTagHome: 'Overview',
      shotTagLibrary: 'Local explorer',
      shotTagLyrics: 'Karaoke .LRC',
      shotTagArtists: 'Catalog',
      shotTagDiscography: 'Discography',
      shotTagSearch: 'Instant search',
      shotTagPlaylists: 'Playlist manager',
      shotTagEditor: '.LRC Editor',

            formatsEyebrow: 'Audio Engine & Compatibility',
      formatsTitle: 'Supported Formats',
      formatsSub: 'Aiiko Music plays the most common audio formats, including:',

      experienceCtaLabel: 'Try or install',

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

      taglineHeadline: 'Your music, your way. A local music player, built with care for everyday listening.',

      footerCredit: 'Aiiko Music · Developed by Aiiko Hirayama · © 2026 · GPL-3.0',
      footerLicense: 'License',
      footerPrivacy: 'Privacy'
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
      heroExplore: 'Explorar funciones',
      heroSource: 'Código fuente en GitHub',
      heroMeta: 'Windows 10 y 11 · Código abierto (GPL-3.0)',
      heroAlt: 'Vista de reproducción de Aiiko Music con letras',
      releaseLabel: 'Última versión: {tag}',
      previewApp: 'Ver captura',

      navHome: 'Inicio',
      navFeatures: 'Funciones',
      navScreenshots: 'Galería',
      navFormats: 'Formatos',
      navInstall: 'Instalación',
      navDownload: 'Descargar',
      navHomeShort: 'Inicio',
      navFeaturesShort: 'Funciones',
      navScreenshotsShort: 'Galería',
      navFormatsShort: 'Formatos',
      navInstallShort: 'Instalar',
      navDownloadShort: 'Descarga',

                  featuresEyebrow: 'Características',
      featuresHeadline: 'Todo para tu biblioteca personal.',
      featuresLead: 'Un reproductor de música diseñado para colecciones musicales personales.',
      touchSwipeHint: 'Desliza o toca para explorar',

            catTab1: 'Audio y Reproducción',
      catEyebrow1: '01 · Motor de Audio y Rendimiento',
      catTitle1: 'La Calidad del Sonido Importa',
      catSub1: 'Tanto si escuchas tu música en un equipo audiófilo como en un portátil, Aiiko Music está calibrado para satisfacer todas tus necesidades.',

      catTab2: 'Biblioteca y Organización',
      catEyebrow2: '02 · Catálogo y Descubrimiento',
      catTitle2: 'Gestiona tu Colección Musical',
      catSub2: 'Diseñado para colecciones personales: navegación jerárquica por artistas, búsqueda sin latencia y listas a tu medida.',

      catTab3: 'Letras y Metadatos',
      catEyebrow3: '03 · Letras y Etiquetas de Precisión',
      catTitle3: 'Letras y Metadatos con Precisión',
      catSub3: 'Letras sincronizadas en vivo, herramientas avanzadas de edición y etiquetado exhaustivo de metadatos para tu catálogo.',

      catTab4: 'Experiencia y Personalización',
      catEyebrow4: '04 · Interfaz y Ecosistema',
      catTitle4: 'Experiencia y Personalización',
      catSub4: 'Personaliza tu escucha diaria con mini-reproductor flotante, Discord Rich Presence, scrobbling en Last.fm y atajos de teclado.',

      featCat1: 'Audio y Reproducción',
      feat_1_1: 'Ecualizador de 10 bandas con ajuste personalizado',
      feat_1_2: 'Reproducción sin pausas (gapless) para una escucha continua',
      feat_1_3: 'Modos de reproducción aleatoria y gestión de cola',
      feat_1_4: 'Visualizador de audio en tiempo real',

      featCat2: 'Biblioteca y Organización',
      feat_2_1: 'Gestión de biblioteca musical local',
      feat_2_2: 'Exploración por álbumes y artistas',
      feat_2_3: 'Gestión de listas de reproducción',
      feat_2_4: 'Búsqueda en toda la biblioteca para encontrar canciones al instante',

      featCat3: 'Letras y Metadatos',
      feat_3_1: 'Soporte de letras, incluidos archivos .lrc locales y buscador online integrado',
      feat_3_2: 'Editor avanzado de letras con herramientas de sincronización',
      feat_3_3: 'Editor de metadatos para etiquetar tu colección',
      feat_3_4: 'Visualización y gestión de carátulas de álbum',

      featCat4: 'Experiencia y Personalización',
      feat_4_1: 'Mini-reproductor flotante',
      feat_4_2: 'Visor a pantalla completa',
      feat_4_3: 'Personalización de apariencia y color de acento',
      feat_4_4: 'Discord Rich Presence',
      feat_4_5: 'Registro de reproducciones en Last.fm',
      feat_4_6: 'Atajos de teclado intuitivos',

      featuresMoreBtn: 'Ver todas las características',
      featuresModalTitle: 'Todas las características',
      gaplessBadge: 'GAPLESS · 0.0s SILENCIO',
      gaplessNotice: '0.0s SILENCIO · TRANSICIÓN CONTINUA',
      feat_1_6: 'Mini-reproductor flotante y Fullscreen',
      feat_theme_title: 'HAZLO TUYO',
      feat_desc_1: 'Ajusta el sonido a tu preferencia y utiliza las funciones de crossfeed.',
      feat_desc_2: 'Transición continua de flujo de audio sin pausas entre pistas.',
      feat_desc_3: 'Hermoso y dinámico visualizador de espectro que se mueve al ritmo de tu música.',
      feat_desc_4: 'Navega en tu música en una biblioteca ordenada sin complicaciones.',
      feat_desc_5: 'Letras sincronizadas estilo karaoke con soporte .lrc local, traducción a tu idioma y editor avanzado integrado.',
      feat_desc_6: 'Mini-reproductor flotante siempre visible y vista inmersiva a pantalla completa para tus pantallas.',
      feat_desc_7: 'Personaliza el color de acento y tema visual de tu reproductor a tu gusto.',

      shotsTitle: 'Galería',
      capturasTitle: 'Galería interactiva',
      capturasLead: 'Un entorno oscuro y sin distracciones, diseñado para sesiones de escucha inmersivas.',
      shotsBadge: 'Galería interactiva',
      shotsSub: 'Desliza para explorar cada rincón de la aplicación en alta resolución.',
      shotAltPrefix: 'Captura de Aiiko Music: ',
      zoomBtn: 'Ampliar',
      tabHome: 'Inicio',
      tabLibrary: 'Biblioteca',
      tabNowPlaying: 'Reproducción y letras',
      tabArtists: 'Artistas',
      tabArtistDetail: 'Detalle de artista',
      tabSearch: 'Búsqueda',
      tabPlaylists: 'Listas',
      tabLyricsEditor: 'Editor de letras',
      shotTagHome: 'Vista general',
      shotTagLibrary: 'Explorador local',
      shotTagLyrics: 'Karaoke .LRC',
      shotTagArtists: 'Catálogo',
      shotTagDiscography: 'Discografía',
      shotTagSearch: 'Búsqueda rápida',
      shotTagPlaylists: 'Gestor de listas',
      shotTagEditor: 'Editor .LRC',

            formatsEyebrow: 'Motor de Audio y Compatibilidad',
      formatsTitle: 'Formatos Compatibles',
      formatsSub: 'Aiiko Music reproduce los formatos de audio más comunes, incluyendo:',

      experienceCtaLabel: 'Probar o instalar',

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

      taglineHeadline: 'Tu música, a tu manera. Un reproductor local diseñado con dedicación para tu escucha diaria.',

      footerCredit: 'Aiiko Music · Desarrollado por Aiiko Hirayama · © 2026 · GPL-3.0',
      footerLicense: 'Licencia',
      footerPrivacy: 'Privacidad'
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
      heroExplore: '機能を見る',
      heroSource: 'GitHub でソースコードを見る',
      heroMeta: 'Windows 10 / 11 · オープンソース (GPL-3.0)',
      heroAlt: 'Aiiko Music の再生画面（歌詞表示）',
      releaseLabel: '最新バージョン: {tag}',
      previewApp: '画面を見る',

      navHome: 'ホーム',
      navFeatures: '機能',
      navScreenshots: 'ギャラリー',
      navFormats: '対応形式',
      navInstall: 'インストール',
      navDownload: 'ダウンロード',
      navHomeShort: 'ホーム',
      navFeaturesShort: '機能',
      navScreenshotsShort: 'ギャラリー',
      navFormatsShort: '形式',
      navInstallShort: '導入',
      navDownloadShort: '入手',

                  featuresEyebrow: '機能一覧',
      featuresHeadline: 'パーソナルライブラリのためのすべて。',
      featuresLead: '個人の音楽コレクションのために設計されたミュージックプレーヤー。',
      touchSwipeHint: 'スワイプまたはタップして探索',

            catTab1: 'オーディオ＆再生',
      catEyebrow1: '01 · オーディオエンジン＆性能',
      catTitle1: '音質へのこだわり',
      catSub1: 'オーディオファイル環境でもラップトップでも、Aiiko Music はあらゆるリスニングニーズに応えます。',

      catTab2: 'ライブラリ＆整理',
      catEyebrow2: '02 · カタログ＆ブラウズ',
      catTitle2: '音楽コレクションを自在に管理',
      catSub2: 'パーソナルライブラリのために設計された、アーティスト階層表示、遅延ゼロの検索、カスタムプレイリスト。',

      catTab3: '歌詞＆メタデータ',
      catEyebrow3: '03 · 歌詞＆高精度タグ',
      catTitle3: '高精度な歌詞とメタデータ',
      catSub3: '同期カラオケ歌詞、高度なエディターツール、完璧なコレクション管理のための詳細なメタデータタグ。',

      catTab4: '体験＆カスタマイズ',
      catEyebrow4: '04 · インターフェース＆連携',
      catTitle4: '体験＆カスタマイズ',
      catSub4: 'フローティングミニプレーヤー、Discord Rich Presence 連携、Last.fm スクロブリング、ショートカットで日常のリスニングをカスタマイズ。',

      featCat1: 'オーディオ＆再生',
      feat_1_1: 'カスタム調整が可能な10バンドイコライザー',
      feat_1_2: '途切れのない音楽体験を提供するギャップレス再生',
      feat_1_3: '再生キューとシャッフル再生モード',
      feat_1_4: 'オーディオビジュアライザー',

      featCat2: 'ライブラリ＆整理',
      feat_2_1: 'ローカル音楽ライブラリの管理',
      feat_2_2: 'アルバムとアーティストによるブラウジング',
      feat_2_3: 'プレイリスト管理',
      feat_2_4: '目的の曲を瞬時に探せるライブラリ全体検索',

      featCat3: '歌詞＆メタデータ',
      feat_3_1: 'ローカル.lrcファイル対応およびオンライン歌詞検索',
      feat_3_2: '同期ツールを備えた高度な歌詞エディター',
      feat_3_3: 'コレクションを整理するメタデータタグエディター',
      feat_3_4: 'アルバムアートワークの表示と管理',

      featCat4: '体験＆カスタマイズ',
      feat_4_1: 'フローティングミニプレーヤー',
      feat_4_2: 'フルスクリーンビューア',
      feat_4_3: '外観とアクセントカラーのカスタマイズ',
      feat_4_4: 'Discord Rich Presence 連携',
      feat_4_5: 'Last.fm スクロブリング',
      feat_4_6: 'キーボードショートカット',

      featuresMoreBtn: 'すべての機能を見る',
      featuresModalTitle: 'すべての機能一覧',
      gaplessBadge: 'ギャップレス · 0.0秒無音',
      gaplessNotice: '0.0秒無音 · シームレス再生',
      feat_1_6: 'フローティングミニプレーヤー＆フルスクリーン',
      feat_theme_title: '自分好みにカスタマイズ',
      feat_desc_1: '好みに合わせてサウンドを調整し、クロスフィード機能を使用できます。',
      feat_desc_2: 'トラック間の無音を完全に排除したシームレスな連続再生。',
      feat_desc_3: '音楽のリズムに合わせてダイナミックに躍動する美しいスペクトラムビジュアライザー。',
      feat_desc_4: '整理されたライブラリで手間なく快適に音楽をブラウズ。',
      feat_desc_5: 'ローカル.lrc対応、言語翻訳、統合高度エディターを備えたカラオケ風同期歌詞。',
      feat_desc_6: '常に手前に表示されるミニプレーヤーと没入型フルスクリーンビュー。',
      feat_desc_7: 'アクセントカラーとビジュアルテーマを自分好みにカスタマイズ。',

      shotsTitle: 'ギャラリー',
      capturasTitle: 'インタラクティブギャラリー',
      capturasLead: '音楽に深く浸るために作られた、ダークで洗練されたインターフェース。',
      shotsBadge: 'インタラクティブギャラリー',
      shotsSub: 'スクロールしてアプリの各画面を高解像度で探索。',
      shotAltPrefix: 'Aiiko Music のスクリーンショット: ',
      zoomBtn: '拡大',
      tabHome: 'ホーム',
      tabLibrary: 'ライブラリ',
      tabNowPlaying: '再生と歌詞',
      tabArtists: 'アーティスト',
      tabArtistDetail: 'アーティスト詳細',
      tabSearch: '検索',
      tabPlaylists: 'プレイリスト',
      tabLyricsEditor: '歌詞エディター',
      shotTagHome: '全体表示',
      shotTagLibrary: 'ライブラリ',
      shotTagLyrics: 'カラオケ .LRC',
      shotTagArtists: 'アーティスト一覧',
      shotTagDiscography: 'ディスコグラフィ',
      shotTagSearch: '即時検索',
      shotTagPlaylists: 'プレイリスト',
      shotTagEditor: '歌詞エディター',

            formatsEyebrow: 'オーディオエンジン＆互換性',
      formatsTitle: '対応フォーマット',
      formatsSub: 'Aiiko Musicは一般的な主要オーディオフォーマットに対応しています：',

      experienceCtaLabel: '試す・インストール',

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

      taglineHeadline: 'あなたの音楽を、あなたのスタイルで。日々のリスニングのために丁寧に作られたローカル音楽プレーヤー。',

      footerCredit: 'Aiiko Music · 開発: Aiiko Hirayama · © 2026 · GPL-3.0',
      footerLicense: 'ライセンス',
      footerPrivacy: 'プライバシー'
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
      heroExplore: 'Explorer les fonctionnalités',
      heroSource: 'Code source sur GitHub',
      heroMeta: 'Windows 10 et 11 · Open source (GPL-3.0)',
      heroAlt: 'Vue de lecture d’Aiiko Music avec les paroles',
      releaseLabel: 'Dernière version : {tag}',
      previewApp: 'Voir la capture',

      navHome: 'Accueil',
      navFeatures: 'Fonctionnalités',
      navScreenshots: 'Galerie',
      navFormats: 'Formats',
      navInstall: 'Installation',
      navDownload: 'Télécharger',
      navHomeShort: 'Accueil',
      navFeaturesShort: 'Fonctions',
      navScreenshotsShort: 'Galerie',
      navFormatsShort: 'Formats',
      navInstallShort: 'Installer',
      navDownloadShort: 'Obtenir',

                  featuresEyebrow: 'Fonctionnalités',
      featuresHeadline: 'Tout pour votre bibliothèque personnelle.',
      featuresLead: 'Un lecteur de musique conçu pour les collections musicales personnelles.',
      touchSwipeHint: 'Balayez ou appuyez pour explorer',

            catTab1: 'Audio et Lecture',
      catEyebrow1: '01 · Moteur Audio & Performance',
      catTitle1: 'La Qualité Sonore Avant Tout',
      catSub1: 'Que vous écoutiez votre musique sur une installation audiophile ou sur un ordinateur portable, Aiiko Music est conçu pour combler toutes vos attentes.',

      catTab2: 'Bibliothèque et Organisation',
      catEyebrow2: '02 · Catalogue & Découverte',
      catTitle2: 'Gérez Votre Collection Musicale',
      catSub2: 'Conçu pour les bibliothèques personnelles : affichage hiérarchique des artistes, recherche instantanée et listes personnalisées.',

      catTab3: 'Paroles et Métadonnées',
      catEyebrow3: '03 · Paroles & Balises de Précision',
      catTitle3: 'Précision des Paroles & Métadonnées',
      catSub3: 'Paroles synchronisées en direct, éditeur avancé et étiquetage complet des métadonnées pour organiser votre collection.',

      catTab4: 'Expérience et Personnalisation',
      catEyebrow4: '04 · Interface & Écosystème',
      catTitle4: 'Expérience & Personnalisation',
      catSub4: 'Personnalisez votre écoute quotidienne avec le mini-lecteur flottant, Discord Rich Presence, le scrobbling Last.fm et des raccourcis.',

      featCat1: 'Audio et Lecture',
      feat_1_1: 'Égaliseur 10 bandes avec réglage personnalisé',
      feat_1_2: 'Lecture sans blanc (gapless) pour une écoute ininterrompue',
      feat_1_3: 'Modes de lecture aléatoire et gestion de la file d’attente',
      feat_1_4: 'Visualiseur audio en temps réel',

      featCat2: 'Bibliothèque et Organisation',
      feat_2_1: 'Gestion de la bibliothèque musicale locale',
      feat_2_2: 'Navigation par albums et artistes',
      feat_2_3: 'Gestion des listes de lecture',
      feat_2_4: 'Recherche instantanée dans toute la bibliothèque',

      featCat3: 'Paroles et Métadonnées',
      feat_3_1: 'Prise en charge des paroles, fichiers .lrc locaux et recherche en ligne intégrée',
      feat_3_2: 'Éditeur de paroles avancé avec outils de synchronisation',
      feat_3_3: 'Éditeur de métadonnées pour organiser votre collection',
      feat_3_4: 'Affichage et gestion des pochettes d’albums',

      featCat4: 'Expérience et Personnalisation',
      feat_4_1: 'Mini-lecteur flottant',
      feat_4_2: 'Visualiseur plein écran',
      feat_4_3: 'Personnalisation de l’apparence et des couleurs d’accentuation',
      feat_4_4: 'Intégration Discord Rich Presence',
      feat_4_5: 'Scrobbling Last.fm',
      feat_4_6: 'Raccourcis clavier',

      featuresMoreBtn: 'Voir toutes les fonctionnalités',
      featuresModalTitle: 'Toutes les fonctionnalités',
      gaplessBadge: 'GAPLESS · 0.0s SILENCE',
      gaplessNotice: '0.0s SILENCE · TRANSITION CONTINUE',
      feat_1_6: 'Mini-lecteur flottant et Plein écran',
      feat_theme_title: 'FAITES-LE VÔTRE',
      feat_desc_1: 'Ajustez le son selon vos préférences et utilisez les fonctions de crossfeed.',
      feat_desc_2: 'Transition audio fluide sans aucun silence entre les pistes.',
      feat_desc_3: 'Visualiseur de spectre magnifique et dynamique qui bouge au rythme de votre musique.',
      feat_desc_4: 'Parcourez votre musique dans une bibliothèque ordonnée et sans complications.',
      feat_desc_5: 'Paroles synchronisées style karaoké avec support .lrc local, traduction et éditeur avancé intégré.',
      feat_desc_6: 'Mini-lecteur flottant toujours au premier plan et vue plein écran immersive.',
      feat_desc_7: 'Personnalisez la couleur d\'accentuation et le thème visuel de votre lecteur selon vos envies.',

      shotsTitle: 'Galerie',
      capturasTitle: 'Galerie interactive',
      capturasLead: 'Un environnement sombre et épuré, conçu pour des sessions d’écoute immersives.',
      shotsBadge: 'Galerie interactive',
      shotsSub: 'Faites défiler pour explorer l’application en haute résolution.',
      shotAltPrefix: 'Capture d’Aiiko Music : ',
      zoomBtn: 'Agrandir',
      tabHome: 'Accueil',
      tabLibrary: 'Bibliothèque',
      tabNowPlaying: 'Lecture et paroles',
      tabArtists: 'Artistes',
      tabArtistDetail: 'Détail d’artiste',
      tabSearch: 'Recherche',
      tabPlaylists: 'Playlists',
      tabLyricsEditor: 'Éditeur de paroles',
      shotTagHome: 'Vue générale',
      shotTagLibrary: 'Explorateur local',
      shotTagLyrics: 'Karaoké .LRC',
      shotTagArtists: 'Catalogue',
      shotTagDiscography: 'Discographie',
      shotTagSearch: 'Recherche rapide',
      shotTagPlaylists: 'Gestionnaire de listes',
      shotTagEditor: 'Éditeur .LRC',

            formatsEyebrow: 'Moteur Audio & Compatibilité',
      formatsTitle: 'Formats Pris en Charge',
      formatsSub: 'Aiiko Music prend en charge les formats audio les plus courants, notamment :',

      experienceCtaLabel: 'Essayer ou installer',

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

      taglineHeadline: 'Votre musique, à votre façon. Un lecteur local conçu avec soin pour votre écoute au quotidien.',

      footerCredit: 'Aiiko Music · Développé par Aiiko Hirayama · © 2026 · GPL-3.0',
      footerLicense: 'Licence',
      footerPrivacy: 'Confidentialité'
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

  const dock = $('.dock');
  const dockLinks = $$('.dock-link');
  const indicator = $('.dock-indicator');
  const heroDots = $$('.hero-dot');
  const heroNavLinks = $$('.hero-menu-link, .hero-nav-link');
  const heroNavPill = $('#heroNavPill');
  const heroStage = $('.hero-stage');
  const featuresRows = $('#featuresRows');
  const featuresShowcase = $('#featuresShowcase');
  const heroMockupCard = $('#heroMockupCard');
  const rocketPreviewBtn = $('#heroRocketPreviewBtn');
  const morphBead = $('#morphBead');
  const morphRipple = $('#morphRipple');
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

    renderRelease();
    initTaglineReveal();
  initExperienceReveal();

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

    // Selector de idioma reubicado en la base

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

  /* ---------- Introducción de Marca Cinemática (Logo Centro -> Aiiko Music -> Destino en esquina) ---------- */

  function initBrandIntro() {
    const overlay = $('#introOverlay');
    const actor = $('#introActor');
    const logo = $('#introLogo');
    const text = $('#introText');
    const destBrand = $('#heroBrand');
    const heroStage = $('#inicio');

    if (!overlay || !actor || !logo || !text || !destBrand || !heroStage) return;

    // Si hay hash específico (distinto a #inicio o #instalacion), o movimiento reducido, completar de inmediato
    if (reduceMotion || (window.location.hash && window.location.hash !== '#inicio' && window.location.hash !== '#instalacion')) {
      overlay.remove();
      actor.remove();
      destBrand.classList.add('is-docked');
      heroStage.classList.add('is-revealed');
      return;
    }

    let stageState = 'init'; // 'logo', 'text', 'pause', 'flying', 'done'
    let transitionFired = false;
    let textTimer = null;
    let flightTimer = null;

    const isMobileScreen = window.innerWidth <= 768;

    // En pantallas móviles, el actor está en columna centrado matemáticamente (centerX = 50vw).
    // En escritorio, el actor está en fila horizontal y se calcula el desplazamiento inicial del logo.
    const actorWidth = actor.offsetWidth;
    const logoWidth = logo.offsetWidth;
    const initialLogoShiftX = isMobileScreen ? 0 : (actorWidth - logoWidth) / 2;

    logo.style.transform = isMobileScreen ? 'scale(0.88)' : `translateX(${initialLogoShiftX.toFixed(2)}px) scale(0.88)`;

    // 1. Fase 1: Emergencia suave y majestuosa del logo en el centro de la pantalla (0.0s - 0.9s)
    requestAnimationFrame(() => {
      logo.classList.add('is-emerged');
      logo.style.transform = isMobileScreen ? 'scale(1)' : `translateX(${initialLogoShiftX.toFixed(2)}px) scale(1)`;
      stageState = 'logo';
    });

    // 2. Fase 2: Florecimiento tipográfico (0.9s - 1.7s)
    textTimer = setTimeout(() => {
      revealText();
    }, 900);

    function revealText(instant = false) {
      if (stageState === 'flying' || stageState === 'done') return;
      stageState = 'text';

      if (instant) {
        logo.classList.add('is-aligned');
        text.classList.add('is-visible');
        stageState = 'pause';
        return;
      }

      logo.classList.add('is-aligned');
      text.classList.add('is-visible');

      // 3. Fase 3: Pausa contemplativa de la marca completa (1.7s - 3.0s)
      flightTimer = setTimeout(() => {
        stageState = 'pause';
        flyToCorner();
      }, 1300);
    }

    // 4. Fase 4: Vuelo cinematográfico a la esquina superior izquierda (escritorio) o disolución serena (móvil)
    function flyToCorner() {
      if (transitionFired) return;
      transitionFired = true;
      stageState = 'flying';

      if (isMobileScreen) {
        // En móviles: disolución suave y elegante hacia el hero sin saltos
        actor.style.transition = 'opacity 0.65s cubic-bezier(0.16, 1, 0.3, 1)';
        overlay.style.transition = 'opacity 0.65s cubic-bezier(0.16, 1, 0.3, 1)';
        actor.style.opacity = '0';
        overlay.style.opacity = '0';
        destBrand.classList.add('is-docked');
        heroStage.classList.add('is-revealed');
        setTimeout(() => {
          actor.remove();
          overlay.remove();
          stageState = 'done';
        }, 650);
        return;
      }

      // Asegurar que el lockup esté alineado inmediatamente antes de iniciar el vuelo
      logo.style.transition = 'none';
      logo.style.transform = 'none';
      logo.classList.add('is-aligned');
      text.style.transition = 'none';
      text.classList.add('is-visible');
      void actor.offsetWidth; // Forzar reflow atómico antes de medir

      // Calcular deltas exactos respecto a destBrand
      const destLogo = destBrand.querySelector('.hero-brand-logo') || destBrand;
      const destLogoRect = destLogo.getBoundingClientRect();
      const currentLogoRect = logo.getBoundingClientRect();

      // Factor de escala exacto para igualar dimensiones de logo
      const scaleFactor = destLogoRect.width / logo.offsetWidth;

      // Delta exacto: de la posición actual del logo a la posición final del logo en la barra
      const deltaX = destLogoRect.left - currentLogoRect.left;
      const deltaY = destLogoRect.top - currentLogoRect.top;

      // Fijar origen de transformación en la esquina superior izquierda del logo
      actor.style.transformOrigin = '0 0';
      actor.classList.add('flying-to-corner');
      actor.style.transform = `translate(calc(-50% + ${deltaX.toFixed(2)}px), calc(-50% + ${deltaY.toFixed(2)}px)) scale(${scaleFactor.toFixed(5)})`;

      // Desvanecer el fondo oscuro serenamente mientras se revela el hero
      overlay.style.backgroundColor = 'transparent';
      heroStage.classList.add('is-revealed');

      // 5. Fase 5: Entrega sin parpadeos ni desfase de subpíxeles al aterrizar (1150ms)
      setTimeout(() => {
        destBrand.classList.add('is-docked');
        actor.remove();
        overlay.remove();
        stageState = 'done';
      }, 1150);
    }

    // Interacción del usuario durante la introducción: acelera elegantemente sin saltos
    function onUserInteraction() {
      if (stageState === 'done' || transitionFired) return;
      if (textTimer) clearTimeout(textTimer);
      if (flightTimer) clearTimeout(flightTimer);

      if (stageState === 'logo') {
        revealText(true);
        setTimeout(flyToCorner, 200);
      } else {
        flyToCorner();
      }
    }

    window.addEventListener('wheel', onUserInteraction, { passive: true });
    window.addEventListener('touchmove', onUserInteraction, { passive: true });
    window.addEventListener('scroll', () => {
      // Filtrar el scroll sintético inicial en scrollY = 0
      if (window.scrollY > 20) onUserInteraction();
    }, { passive: true });
    window.addEventListener('keydown', (e) => {
      if (['ArrowDown', 'PageDown', ' ', 'Enter'].includes(e.key)) onUserInteraction();
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

  /* ---------- Funciones: Despliegue interactivo y widgets vivos ---------- */

  /* ---------- Funciones: Ventana Modal de Características ---------- */

  function initFeaturesModal() {
    const modal = $('#featuresModal');
    const openBtn = $('#openFeaturesModalBtn');
    const closeBtn = $('#closeFeaturesModalBtn');
    if (!modal) return;

    let savedScrollY = 0;

    function openModal() {
      savedScrollY = window.scrollY;
      if (typeof modal.showModal === 'function') {
        modal.showModal();
      } else {
        modal.setAttribute('open', '');
      }
      // Solo en escritorio bloqueamos el scroll del body; en móviles evitamos overflow:hidden
      // para que Safari y Chrome no reinicien window.scrollY a 0 al abrir el modal.
      if (window.innerWidth > 768) {
        document.body.style.overflow = 'hidden';
      }
    }

    function closeModal() {
      if (typeof modal.close === 'function') modal.close();
      else modal.removeAttribute('open');
      document.body.style.overflow = '';
      if (savedScrollY > 0) {
        window.scrollTo({ top: savedScrollY, left: 0, behavior: 'instant' });
      }
    }

    if (openBtn) openBtn.addEventListener('click', openModal);
    if (closeBtn) closeBtn.addEventListener('click', closeModal);

    modal.addEventListener('close', () => {
      document.body.style.overflow = '';
      if (savedScrollY > 0) {
        window.scrollTo({ top: savedScrollY, left: 0, behavior: 'instant' });
      }
    });

    modal.addEventListener('cancel', () => {
      document.body.style.overflow = '';
      if (savedScrollY > 0) {
        window.scrollTo({ top: savedScrollY, left: 0, behavior: 'instant' });
      }
    });

    modal.addEventListener('click', (e) => {
      const card = modal.querySelector('.features-modal-card');
      if (card && !card.contains(e.target)) {
        closeModal();
      }
    });

    const card = modal.querySelector('.features-modal-card');
    if (card) {
      card.addEventListener('wheel', (e) => {
        e.stopPropagation();
      }, { passive: false });
    }
  }

  
  /* ---------- Manifiesto: Revelado Palabra por Palabra (ai-design-skills B11) ---------- */

  let taglineObserver = null;

  function initTaglineReveal() {
    const headlineEl = $('#taglineWords');
    if (!headlineEl) return;

    const rawText = t('taglineHeadline') || headlineEl.textContent.trim();
    if (!rawText) return;

    headlineEl.innerHTML = '';
    const isCJK = currentLang === 'ja';
    const tokens = isCJK
      ? rawText.split(/(?<=[、。])|(?=[、。])| /).filter(Boolean)
      : rawText.split(/\s+/).filter(Boolean);

    const spans = tokens.map((token) => {
      const span = document.createElement('span');
      span.className = 'tagline-word';
      span.textContent = token + (isCJK ? '' : ' ');
      headlineEl.appendChild(span);
      return span;
    });

    if (reduceMotion || !('IntersectionObserver' in window)) {
      spans.forEach((s) => s.classList.add('is-active'));
      return;
    }

    if (taglineObserver) {
      taglineObserver.disconnect();
    }

    taglineObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          spans.forEach((word, idx) => {
            setTimeout(() => {
              word.classList.add('is-active');
            }, idx * 45);
          });
          taglineObserver.disconnect();
        }
      });
    }, {
      rootMargin: '0px 0px -12% 0px',
      threshold: 0.15
    });

    const section = $('#manifiesto');
    if (section) taglineObserver.observe(section);
  }

  /* ---------- Experiencia Aiiko Music (Intro ampliada en pantalla completa: logo -> letras -> CTA) ---------- */

  function initExperienceReveal() {
    const section = $('#experiencia');
    const actor = $('#expBrandActor');
    const logo = $('#expLogo');
    const text = $('#expText');
    const cta = $('#expCtaWrap');
    if (!section || !actor || !logo || !text) return;

    let isRevealed = false;
    let animTimer1 = null;
    let animTimer2 = null;

    function resetExperience() {
      if (animTimer1) { clearTimeout(animTimer1); animTimer1 = null; }
      if (animTimer2) { clearTimeout(animTimer2); animTimer2 = null; }
      actor.classList.remove('is-aligned');
      logo.classList.remove('is-emerged');
      text.classList.remove('is-visible');
      if (cta) cta.classList.remove('is-visible');

      if (window.innerWidth >= 680) {
        const actorWidth = actor.offsetWidth;
        const logoWidth = logo.offsetWidth;
        const initialShiftX = (actorWidth - logoWidth) / 2;
        logo.style.transform = `translateX(${initialShiftX.toFixed(2)}px) scale(0.9)`;
      } else {
        logo.style.transform = 'scale(0.9)';
      }
      logo.style.opacity = '0';
      isRevealed = false;
    }

    function playExperience() {
      if (isRevealed) return;
      isRevealed = true;

      if (reduceMotion) {
        logo.classList.add('is-emerged');
        logo.style.transform = 'none';
        actor.classList.add('is-aligned');
        text.classList.add('is-visible');
        if (cta) cta.classList.add('is-visible');
        return;
      }

      // Fase 1: Aparece el logo en el centro
      logo.classList.add('is-emerged');
      if (window.innerWidth >= 680) {
        const actorWidth = actor.offsetWidth;
        const logoWidth = logo.offsetWidth;
        const initialShiftX = (actorWidth - logoWidth) / 2;
        logo.style.transform = `translateX(${initialShiftX.toFixed(2)}px) scale(1)`;
      } else {
        logo.style.transform = 'scale(1)';
      }

      // Fase 2: Aparecen las letras (el logo se desplaza a la izquierda y el texto florece a la derecha)
      animTimer1 = setTimeout(() => {
        actor.classList.add('is-aligned');
        logo.style.transform = 'translateX(0) scale(1)';
        text.classList.add('is-visible');

        // Fase 3: Aparece el botón de Probar o instalar
        animTimer2 = setTimeout(() => {
          if (cta) cta.classList.add('is-visible');
        }, 400);
      }, 750);
    }

    resetExperience();

    window.addEventListener('resize', () => {
      if (!isRevealed) resetExperience();
    });

    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(() => {
        if (!isRevealed) resetExperience();
      });
    }

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting && entry.intersectionRatio >= 0.25) {
          playExperience();
        }
      });
    }, {
      threshold: [0.25]
    });

    observer.observe(section);
  }

  /* ---------- Funciones: Escenario Bloqueado por Rueda/Gestos (Solo FEATURES primero, luego 1 a 1) ---------- */

  function initFeaturesScrollStage() {
    const track = $('#funciones');
    const introView = $('#featuresScreenIntro');
    const cards = $$('.features-focus-card');
    const outroStage = $('#featuresOutroStage');
    const dots = $$('.rail-dot');
    if (!track || cards.length === 0) return;

    let currentStep = 0; // 0 = Solo FEATURES, 1..7 = Cards 1..7, 8 = Outro modal
    const totalSteps = 8;
    let isLocked = false;
    let isTransitioning = false;

    // Ciclo dinámico descendente de temas (06A -> 05A -> 04A -> 03A -> 02A -> 01A -> 00A y se detiene)
    const THEME_SERIES = [
      'images/themes/06A.png',
      'images/themes/05A.png',
      'images/themes/04A.png',
      'images/themes/03A.png',
      'images/themes/02A.png',
      'images/themes/01A.png',
      'images/themes/00A.png'
    ];

    let themeCycleTimer = null;
    let themeTransitionTimer = null;
    let themeIndex = 0;

    function stopThemeCycle() {
      if (themeCycleTimer) { clearTimeout(themeCycleTimer); themeCycleTimer = null; }
      if (themeTransitionTimer) { clearTimeout(themeTransitionTimer); themeTransitionTimer = null; }
      const wipe = $('#themeImgWipe');
      if (wipe) wipe.classList.remove('is-animating');
    }

    function startThemeCycle() {
      stopThemeCycle();
      const base = $('#themeImgBase');
      const wipe = $('#themeImgWipe');
      if (!base || !wipe) return;

      themeIndex = 0;
      base.src = THEME_SERIES[0];
      wipe.src = THEME_SERIES[0];

      // Esperar la transición de entrada inicial de la tarjeta (1.3s) antes del primer cambio
      themeCycleTimer = setTimeout(triggerNextTheme, 1300);

      function triggerNextTheme() {
        const nextIndex = (themeIndex + 1) % THEME_SERIES.length;
        const nextTheme = THEME_SERIES[nextIndex];
        wipe.src = nextTheme;
        wipe.classList.remove('is-animating');
        void wipe.offsetWidth; // Forzar reflujo

        wipe.classList.add('is-animating');

        themeTransitionTimer = setTimeout(() => {
          base.src = nextTheme;
          wipe.classList.remove('is-animating');
          themeIndex = nextIndex;

          themeCycleTimer = setTimeout(triggerNextTheme, 1200);
        }, 750);
      }
    }

    function applyStep(step) {
      if (step < 0) step = 0;
      if (step > totalSteps) step = totalSteps;
      currentStep = step;

      // Paso 0: Solo FEATURES en pantalla completa
      if (introView) {
        if (currentStep === 0) {
          introView.classList.remove('is-passed');
        } else {
          introView.classList.add('is-passed');
        }
      }

      // Pasos 1 a 7: Tarjetas de características en foco central
      cards.forEach((card) => {
        const stepNum = parseInt(card.dataset.step, 10);
        card.classList.remove('is-active', 'is-leaving');

        if (stepNum === currentStep) {
          card.classList.add('is-active');
        } else if (stepNum < currentStep) {
          card.classList.add('is-leaving');
        }
      });

      // Paso 7: Iniciar o detener la secuencia de temas
      if (currentStep === 7) {
        startThemeCycle();
      } else {
        stopThemeCycle();
      }

      // Paso 8: Outro con botón para abrir modal
      if (outroStage) {
        if (currentStep === 8) {
          outroStage.classList.remove('is-leaving');
          outroStage.classList.add('is-active');
        } else {
          outroStage.classList.remove('is-active', 'is-leaving');
        }
      }

      // Actualizar puntos del rail lateral
      dots.forEach((dot) => {
        const dotStep = parseInt(dot.dataset.step, 10);
        dot.classList.toggle('is-active', dotStep === currentStep);
      });

      // Actualizar barra de navegación táctil móvil (flechas y contador de paso)
      const mobileNav = $('#featuresMobileNav');
      const mobileStep = $('#featNavStep');
      if (mobileNav && mobileStep) {
        if (currentStep >= 1 && currentStep <= 7) {
          mobileNav.classList.add('is-visible');
          mobileStep.textContent = currentStep;
        } else {
          mobileNav.classList.remove('is-visible');
        }
      }
    }

    // Permitir clic directo en cualquier punto del rail
    dots.forEach((dot) => {
      dot.addEventListener('click', () => {
        const targetStep = parseInt(dot.dataset.step, 10);
        applyStep(targetStep);
      });
    });

    // Controles táctiles móviles (Flechas Anterior / Siguiente e indicador de toque)
    const featPrevBtn = $('#featPrevBtn');
    const featNextBtn = $('#featNextBtn');
    const touchHintBtn = $('#featuresTouchHint');

    if (featPrevBtn) {
      featPrevBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (currentStep > 1) {
          applyStep(currentStep - 1);
        } else {
          applyStep(0);
        }
      });
    }

    if (featNextBtn) {
      featNextBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (currentStep < 7) {
          applyStep(currentStep + 1);
        } else {
          applyStep(8);
        }
      });
    }

    if (touchHintBtn) {
      touchHintBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        applyStep(1);
      });
    }

    // Control de Rueda en Window: intercepta y bloquea el scroll cuando la sección está en viewport
    function onFeaturesWheel(e) {
      const modal = $('#featuresModal');
      if (modal && modal.open) return;

      const rect = track.getBoundingClientRect();
      const isFeaturesLocked = rect.top <= 80 && rect.bottom >= window.innerHeight - 80;
      if (!isFeaturesLocked) return;

      // Hacia abajo: avanzar pasos
      if (e.deltaY > 10) {
        if (currentStep < totalSteps) {
          e.preventDefault();
          if (Math.abs(rect.top) > 2) {
            window.scrollTo({ top: track.offsetTop, behavior: 'instant' });
          }
          if (!isTransitioning) {
            isTransitioning = true;
            applyStep(currentStep + 1);
            setTimeout(() => { isTransitioning = false; }, 240);
          }
        } else if (currentStep === totalSteps) {
          // Al terminar el full discover scope: salto de scroll de transición hacia #manifiesto
          e.preventDefault();
          if (!isTransitioning) {
            isTransitioning = true;
            transitionLeapTo('manifiesto', () => {
              isTransitioning = false;
            });
          }
        }
      }
      // Hacia arriba: retroceder pasos
      else if (e.deltaY < -10) {
        if (currentStep > 0) {
          e.preventDefault();
          if (Math.abs(rect.top) > 2) {
            window.scrollTo({ top: track.offsetTop, behavior: 'instant' });
          }
          if (!isTransitioning) {
            isTransitioning = true;
            applyStep(currentStep - 1);
            setTimeout(() => { isTransitioning = false; }, 240);
          }
        } else {
          // En el paso 0, subir de regreso al Hero
          e.preventDefault();
          transitionToHero();
        }
      }
    }

    window.addEventListener('wheel', onFeaturesWheel, { passive: false });

    // Navegación por teclado (Flechas abajo/arriba, PageDown/PageUp, Espacio)
    window.addEventListener('keydown', (e) => {
      const rect = track.getBoundingClientRect();
      const isFeaturesLocked = rect.top <= 80 && rect.bottom >= window.innerHeight - 80;
      if (!isFeaturesLocked) return;

      if (['ArrowDown', 'PageDown', ' '].includes(e.key)) {
        if (currentStep < totalSteps) {
          e.preventDefault();
          applyStep(currentStep + 1);
        } else if (currentStep === totalSteps) {
          e.preventDefault();
          transitionLeapTo('manifiesto');
        }
      } else if (['ArrowUp', 'PageUp'].includes(e.key)) {
        if (currentStep > 0) {
          e.preventDefault();
          applyStep(currentStep - 1);
        } else {
          e.preventDefault();
          transitionToHero();
        }
      }
    });

    // Gestos táctiles en pantallas móviles / tablets (Soporte horizontal y vertical)
    let touchStartX = 0;
    let touchStartY = 0;
    let touchLastX = 0;
    let touchLastY = 0;
    let isTouchActive = false;

    track.addEventListener('touchstart', (e) => {
      if (e.touches.length !== 1) return;
      touchStartX = e.touches[0].clientX;
      touchStartY = e.touches[0].clientY;
      touchLastX = touchStartX;
      touchLastY = touchStartY;
      isTouchActive = true;
    }, { passive: true });

    track.addEventListener('touchmove', (e) => {
      if (!isTouchActive) return;
      touchLastX = e.touches[0].clientX;
      touchLastY = e.touches[0].clientY;
      const diffX = touchStartX - touchLastX;
      const diffY = touchStartY - touchLastY;

      // En móvil, la navegación de características es ÚNICAMENTE horizontal.
      // Prevenimos el scroll de página SOLO si el usuario está realizando un swipe horizontal claro.
      if (currentStep >= 1 && currentStep <= 7) {
        if (Math.abs(diffX) > 10 && Math.abs(diffX) > Math.abs(diffY)) {
          if (e.cancelable) e.preventDefault();
        }
      }
    }, { passive: false });

    track.addEventListener('touchend', (e) => {
      if (!isTouchActive) return;
      isTouchActive = false;
      const diffX = touchStartX - touchLastX;
      const diffY = touchStartY - touchLastY;

      if (isTransitioning) return;

      // Navegación móvil ESTRICTAMENTE horizontal (Swipe Izquierda / Derecha).
      // El gesto vertical no altera las características y permite el scroll natural de la página.
      if (Math.abs(diffX) > 35 && Math.abs(diffX) > Math.abs(diffY)) {
        if (diffX > 35) {
          // Deslizar hacia la izquierda -> Avanzar siguiente característica
          if (currentStep < totalSteps) {
            isTransitioning = true;
            applyStep(currentStep + 1);
            setTimeout(() => { isTransitioning = false; }, 360);
          } else if (currentStep === totalSteps) {
            isTransitioning = true;
            transitionLeapTo('manifiesto', () => { isTransitioning = false; });
          }
        } else if (diffX < -35) {
          // Deslizar hacia la derecha -> Retroceder a característica anterior
          if (currentStep > 0) {
            isTransitioning = true;
            applyStep(currentStep - 1);
            setTimeout(() => { isTransitioning = false; }, 360);
          }
        }
      }
    }, { passive: true });

    // Exponer helpers para sincronización de pasos entre saltos de sección
    window.__resetFeaturesStep = () => applyStep(0);
    window.__setFeaturesStep = (s) => applyStep(s);

    // Estado inicial
    applyStep(0);
  }

  /* ---------- Galería de Capturas: Bloqueada por Rueda y Counter-Scroll (Left UP, Right DOWN) ---------- */

  function initDualGalleryParallax() {
    const track = $('#galeria') || $('#capturas');
    const colLeft = $('#galleryColLeft');
    const colRight = $('#galleryColRight');
    if (!track || !colLeft || !colRight) return;

    let galleryStep = 0; // 0, 1, 2, 3 (para 4 pares de imágenes)
    const maxGallerySteps = 3;
    let isGalleryTransitioning = false;

    function applyGalleryStep(step) {
      if (step < 0) step = 0;
      if (step > maxGallerySteps) step = maxGallerySteps;
      galleryStep = step;

      const cardsL = colLeft.children;
      const cardsR = colRight.children;

      const targetCardL = cardsL[galleryStep];
      const targetCardR = cardsR[maxGallerySteps - galleryStep];

      // Counter-Scroll milimétricamente exacto:
      // Columna izquierda sube uno a uno (0 -> 1 -> 2 -> 3)
      // Columna derecha baja uno a uno (3 -> 2 -> 1 -> 0)
      // Ambas columnas L y R alinean la tarjeta activa al mismo nivel horizontal exacto (diferencia 0px)
      const offsetLeft = targetCardL ? -targetCardL.offsetTop : -(galleryStep * 410);
      const offsetRight = targetCardR ? -targetCardR.offsetTop : -((maxGallerySteps - galleryStep) * 410);

      colLeft.style.transform = `translate3d(0, ${offsetLeft}px, 0)`;
      colRight.style.transform = `translate3d(0, ${offsetRight}px, 0)`;
    }

    function onGalleryWheel(e) {
      if (window.innerWidth <= 768) return;

      const rect = track.getBoundingClientRect();
      const isGalleryLocked = rect.top <= 80 && rect.bottom >= window.innerHeight - 80;
      if (!isGalleryLocked) return;

      // Hacia abajo: avanzar capturas
      if (e.deltaY > 10) {
        if (galleryStep < maxGallerySteps) {
          e.preventDefault();
          if (Math.abs(rect.top) > 2) {
            window.scrollTo({ top: track.offsetTop, behavior: 'instant' });
          }
          if (!isGalleryTransitioning) {
            isGalleryTransitioning = true;
            applyGalleryStep(galleryStep + 1);
            setTimeout(() => { isGalleryTransitioning = false; }, 240);
          }
        } else if (galleryStep === maxGallerySteps) {
          // Salto de transición al terminar la galería hacia #formatos
          e.preventDefault();
          if (!isGalleryTransitioning) {
            isGalleryTransitioning = true;
            transitionLeapTo('formatos', () => {
              isGalleryTransitioning = false;
            });
          }
        }
      }
      // Hacia arriba: retroceder capturas
      else if (e.deltaY < -10) {
        if (galleryStep > 0) {
          e.preventDefault();
          if (Math.abs(rect.top) > 2) {
            window.scrollTo({ top: track.offsetTop, behavior: 'instant' });
          }
          if (!isGalleryTransitioning) {
            isGalleryTransitioning = true;
            applyGalleryStep(galleryStep - 1);
            setTimeout(() => { isGalleryTransitioning = false; }, 240);
          }
        } else if (galleryStep === 0) {
          // Salto de transición de regreso hacia #manifiesto
          e.preventDefault();
          if (!isGalleryTransitioning) {
            isGalleryTransitioning = true;
            transitionLeapTo('manifiesto', () => {
              isGalleryTransitioning = false;
            });
          }
        }
      }
    }

    window.addEventListener('wheel', onGalleryWheel, { passive: false });

    // Navegación por teclado en la galería
    window.addEventListener('keydown', (e) => {
      if (window.innerWidth <= 768) return;
      const rect = track.getBoundingClientRect();
      const isGalleryLocked = rect.top <= 80 && rect.bottom >= window.innerHeight - 80;
      if (!isGalleryLocked) return;

      if (['ArrowDown', 'PageDown', ' '].includes(e.key)) {
        if (galleryStep < maxGallerySteps) {
          e.preventDefault();
          applyGalleryStep(galleryStep + 1);
        } else {
          e.preventDefault();
          transitionLeapTo('formatos');
        }
      } else if (['ArrowUp', 'PageUp'].includes(e.key)) {
        if (galleryStep > 0) {
          e.preventDefault();
          applyGalleryStep(galleryStep - 1);
        } else {
          e.preventDefault();
          transitionLeapTo('manifiesto');
        }
      }
    });

    // Gestos táctiles
    let touchStartY = 0;
    track.addEventListener('touchstart', (e) => {
      touchStartY = e.touches[0].clientY;
    }, { passive: true });

    track.addEventListener('touchend', (e) => {
      if (window.innerWidth <= 768) return;
      const touchEndY = e.changedTouches[0].clientY;
      const diffY = touchStartY - touchEndY;
      if (Math.abs(diffY) < 35 || isGalleryTransitioning) return;

      if (diffY > 35) {
        if (galleryStep < maxGallerySteps) {
          isGalleryTransitioning = true;
          applyGalleryStep(galleryStep + 1);
          setTimeout(() => { isGalleryTransitioning = false; }, 380);
        } else {
          isGalleryTransitioning = true;
          transitionLeapTo('formatos', () => { isGalleryTransitioning = false; });
        }
      } else if (diffY < -35) {
        if (galleryStep > 0) {
          isGalleryTransitioning = true;
          applyGalleryStep(galleryStep - 1);
          setTimeout(() => { isGalleryTransitioning = false; }, 380);
        } else {
          isGalleryTransitioning = true;
          transitionLeapTo('manifiesto', () => { isGalleryTransitioning = false; });
        }
      }
    }, { passive: true });

    // Disparador de entrada lateral elegante al llegar por primera vez a la galería
    let galleryHasEntered = false;

    function triggerGalleryEntrance() {
      if (galleryHasEntered) return;
      galleryHasEntered = true;
      track.classList.add('is-entered');
    }

    function resetGalleryEntrance() {
      galleryHasEntered = false;
      track.classList.remove('is-entered');
    }

    if ('IntersectionObserver' in window && !reduceMotion) {
      const galleryObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            triggerGalleryEntrance();
          } else {
            const rect = track.getBoundingClientRect();
            if (rect.bottom < -120 || rect.top > window.innerHeight + 120) {
              resetGalleryEntrance();
            }
          }
        });
      }, { rootMargin: '0px 0px -10% 0px', threshold: 0.1 });

      galleryObserver.observe(track);
    } else {
      track.classList.add('is-entered');
    }

    window.__resetGalleryStep = () => {
      applyGalleryStep(0);
      triggerGalleryEntrance();
    };
    window.__setGalleryStep = (s) => applyGalleryStep(s);
    window.__triggerGalleryEntrance = triggerGalleryEntrance;
    window.__resetGalleryEntrance = resetGalleryEntrance;

    window.addEventListener('resize', () => {
      if (window.innerWidth > 768) {
        applyGalleryStep(galleryStep);
      }
    });

    applyGalleryStep(0);
  }

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

    heroDots.forEach((dot) => {
      if (dot.dataset.target === activeId) dot.classList.add('is-active');
      else dot.classList.remove('is-active');
    });

    heroNavLinks.forEach((link) => {
      if (link.dataset.target === activeId) link.setAttribute('aria-current', 'true');
      else link.removeAttribute('aria-current');
    });

    if (activeId === 'galeria' || activeId === 'capturas') {
      if (typeof window.__triggerGalleryEntrance === 'function') {
        window.__triggerGalleryEntrance();
      }
    }

    placeIndicator();
  }

  /* Transición morfológica líquida orgánica (fusión de palabras en gota y salto al dock) */
  let currentNavState = 'TOP'; // 'TOP' | 'BOTTOM'
  let isAutoScrolling = false;
  let isSectionLeaping = false;
  let currentScrollAnimId = null;
  let morphTimerA = null;
  let morphTimerB = null;
  let morphTimerC = null;

  function cancelSmoothScroll() {
    if (currentScrollAnimId) {
      cancelAnimationFrame(currentScrollAnimId);
      currentScrollAnimId = null;
    }
    isAutoScrolling = false;
    isSectionLeaping = false;
  }

  function smoothScrollToY(targetY, duration = 650, onDone) {
    cancelSmoothScroll();
    isAutoScrolling = true;
    const startY = window.scrollY;
    const distance = targetY - startY;
    let startTime = null;

    function easeInOutCubic(t) {
      return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    }

    function step(now) {
      if (!startTime) startTime = now;
      const progress = Math.min((now - startTime) / duration, 1);
      const ease = easeInOutCubic(progress);
      window.scrollTo(0, startY + distance * ease);

      if (progress < 1) {
        currentScrollAnimId = requestAnimationFrame(step);
      } else {
        currentScrollAnimId = null;
        isAutoScrolling = false;
        if (typeof onDone === 'function') onDone();
      }
    }
    currentScrollAnimId = requestAnimationFrame(step);
  }

  function transitionLeapTo(sectionId, onDone, force = false) {
    const target = document.getElementById(sectionId);
    if (!target) return;
    if (!force && (isSectionLeaping || isAutoScrolling)) return;

    cancelSmoothScroll();
    isSectionLeaping = true;

    const targetY = Math.round(target.getBoundingClientRect().top + window.scrollY);
    smoothScrollToY(targetY, 650, () => {
      isSectionLeaping = false;
      if (typeof onDone === 'function') onDone();
    });
  }

  function transitionToFeatures() {
    const funcionesSec = document.getElementById('funciones');
    if (!funcionesSec) return;

    cancelSmoothScroll();
    isAutoScrolling = true;
    currentNavState = 'BOTTOM';

    const isDesktop = window.innerWidth > 960;
    const targetY = funcionesSec.getBoundingClientRect().top + window.scrollY;

    const heroNav = $('.hero-nav');
    const dropletBead = $('#dropletBead');
    const dockImpactFlare = $('#dockImpactFlare');

    if (heroStage) heroStage.classList.add('is-exiting');

    if (!isDesktop || reduceMotion) {
      if (dock) dock.classList.remove('dock-hidden');
      window.scrollTo({ top: targetY, behavior: 'smooth' });
      setTimeout(() => { isAutoScrolling = false; }, 600);
      return;
    }

    clearTimeout(morphTimerA);
    clearTimeout(morphTimerB);
    clearTimeout(morphTimerC);

    // FASE 1: Las 4 palabras del menú se fusionan orgánicamente hacia el centro (sin líneas artificiales)
    if (heroNav) {
      heroNav.classList.remove('is-condensing');
      heroNav.classList.add('is-morphing-to-drop');
    }

    smoothScrollToY(targetY, 780, () => {
      setTimeout(() => { isAutoScrolling = false; }, 100);
    });

    // FASE 2 (~220ms): Al converger las palabras en el centro, la gota se forma en el encabezado y cae por gravedad
    morphTimerA = setTimeout(() => {
      if (dropletBead) {
        dropletBead.classList.remove('is-shooting-up');
        void dropletBead.offsetWidth;
        dropletBead.classList.add('is-plunging');
      }

      // FASE 3 (~620ms): Al chocar en la base del dock, suave destello y expansión del Dock
      morphTimerB = setTimeout(() => {
        if (dockImpactFlare) {
          dockImpactFlare.classList.remove('is-flaring');
          void dockImpactFlare.offsetWidth;
          dockImpactFlare.classList.add('is-flaring');
        }

        if (dock) {
          dock.classList.remove('dock-hidden');
          dock.classList.add('dock-entering');
        }

        setTimeout(() => {
          if (dropletBead) dropletBead.classList.remove('is-plunging');
          if (dock) dock.classList.remove('dock-entering');
        }, 460);
      }, 400);
    }, 220);
  }

  function transitionToHero() {
    const inicioSec = document.getElementById('inicio');
    if (!inicioSec) return;

    cancelSmoothScroll();
    isAutoScrolling = true;
    currentNavState = 'TOP';

    const isDesktop = window.innerWidth > 960;
    const dropletBead = $('#dropletBead');
    const heroNav = $('.hero-nav');

    if (dock) dock.classList.add('dock-hidden');

    if (!isDesktop || reduceMotion) {
      if (heroNav) {
        heroNav.classList.remove('is-morphing-to-drop', 'is-condensing');
      }
      if (heroStage) heroStage.classList.remove('is-exiting');
      window.scrollTo({ top: 0, behavior: 'smooth' });
      setTimeout(() => { isAutoScrolling = false; }, 600);
      return;
    }

    clearTimeout(morphTimerA);
    clearTimeout(morphTimerB);
    clearTimeout(morphTimerC);

    // Retorno: la gota sale disparada verticalmente hacia arriba hasta la cabecera
    if (dropletBead) {
      dropletBead.classList.remove('is-plunging');
      void dropletBead.offsetWidth;
      dropletBead.classList.add('is-shooting-up');
    }

    smoothScrollToY(0, 720, () => {
      setTimeout(() => {
        isAutoScrolling = false;
        if (heroStage) heroStage.classList.remove('is-exiting');
      }, 100);
    });

    // Al llegar a la cabecera (~400ms), la gota se disuelve y las 4 palabras se expanden a sus posiciones
    morphTimerC = setTimeout(() => {
      if (heroNav) {
        heroNav.classList.remove('is-morphing-to-drop', 'is-condensing');
      }
      setTimeout(() => {
        if (dropletBead) dropletBead.classList.remove('is-shooting-up');
      }, 350);
    }, 400);
  }

  /* Saltos de scroll de transición cinematográficos entre cada sección ("son como nuevas páginas") */
  function initSectionTransitionLeaps() {
    const manifiestoSec = $('#manifiesto');
    const formatosSec = $('#formatos');
    const experienciaSec = $('#experiencia');
    const instalacionSec = $('#instalacion');

    let experienciaLockTime = 0;

    // 1. Manifiesto: salto a Galería (hacia abajo) o a Funciones paso 7 (hacia arriba)
    if (manifiestoSec) {
      window.addEventListener('wheel', (e) => {
        const rect = manifiestoSec.getBoundingClientRect();
        const inView = rect.top <= 80 && rect.bottom >= window.innerHeight - 80;
        if (!inView || isSectionLeaping || isAutoScrolling) return;

        if (e.deltaY > 15) {
          e.preventDefault();
          transitionLeapTo('galeria', () => {
            if (typeof window.__resetGalleryStep === 'function') window.__resetGalleryStep();
          });
        } else if (e.deltaY < -15) {
          e.preventDefault();
          transitionLeapTo('funciones', () => {
            if (typeof window.__setFeaturesStep === 'function') window.__setFeaturesStep(7);
          });
        }
      }, { passive: false });

      // Teclado en Manifiesto
      window.addEventListener('keydown', (e) => {
        const rect = manifiestoSec.getBoundingClientRect();
        const inView = rect.top <= 80 && rect.bottom >= window.innerHeight - 80;
        if (!inView || isSectionLeaping || isAutoScrolling) return;

        if (['ArrowDown', 'PageDown', ' '].includes(e.key)) {
          e.preventDefault();
          transitionLeapTo('galeria', () => {
            if (typeof window.__resetGalleryStep === 'function') window.__resetGalleryStep();
          });
        } else if (['ArrowUp', 'PageUp'].includes(e.key)) {
          e.preventDefault();
          transitionLeapTo('funciones', () => {
            if (typeof window.__setFeaturesStep === 'function') window.__setFeaturesStep(7);
          });
        }
      });
    }

    // 2. Formatos: salto a Experiencia (hacia abajo) o a Galería paso 3 (hacia arriba)
    if (formatosSec) {
      window.addEventListener('wheel', (e) => {
        const rect = formatosSec.getBoundingClientRect();
        const inView = rect.top <= 80 && rect.bottom >= window.innerHeight - 80;
        if (!inView || isSectionLeaping || isAutoScrolling) return;

        if (e.deltaY > 15) {
          e.preventDefault();
          experienciaLockTime = Date.now() + 1100; // Cooldown para asimilar la animación de la vista del logo
          transitionLeapTo('experiencia');
        } else if (e.deltaY < -15) {
          e.preventDefault();
          transitionLeapTo('galeria', () => {
            if (typeof window.__setGalleryStep === 'function') window.__setGalleryStep(3);
          });
        }
      }, { passive: false });

      // Teclado en Formatos
      window.addEventListener('keydown', (e) => {
        const rect = formatosSec.getBoundingClientRect();
        const inView = rect.top <= 80 && rect.bottom >= window.innerHeight - 80;
        if (!inView || isSectionLeaping || isAutoScrolling) return;

        if (['ArrowDown', 'PageDown', ' '].includes(e.key)) {
          e.preventDefault();
          experienciaLockTime = Date.now() + 1100;
          transitionLeapTo('experiencia');
        } else if (['ArrowUp', 'PageUp'].includes(e.key)) {
          e.preventDefault();
          transitionLeapTo('galeria', () => {
            if (typeof window.__setGalleryStep === 'function') window.__setGalleryStep(3);
          });
        }
      });
    }

    // 3. Experiencia: vista del logo animado (salto a Instalación hacia abajo o a Formatos hacia arriba)
    if (experienciaSec) {
      window.addEventListener('wheel', (e) => {
        const rect = experienciaSec.getBoundingClientRect();
        const inView = rect.top <= 80 && rect.bottom >= window.innerHeight - 80;
        if (!inView || isSectionLeaping || isAutoScrolling) return;

        // Bloqueo temporal para evitar que el scroll inercial salte la animación
        if (Date.now() < experienciaLockTime) {
          e.preventDefault();
          return;
        }

        if (e.deltaY > 15) {
          e.preventDefault();
          transitionLeapTo('instalacion');
        } else if (e.deltaY < -15) {
          e.preventDefault();
          transitionLeapTo('formatos');
        }
      }, { passive: false });

      // Teclado en Experiencia
      window.addEventListener('keydown', (e) => {
        const rect = experienciaSec.getBoundingClientRect();
        const inView = rect.top <= 80 && rect.bottom >= window.innerHeight - 80;
        if (!inView || isSectionLeaping || isAutoScrolling) return;

        if (Date.now() < experienciaLockTime) {
          e.preventDefault();
          return;
        }

        if (['ArrowDown', 'PageDown', ' '].includes(e.key)) {
          e.preventDefault();
          transitionLeapTo('instalacion');
        } else if (['ArrowUp', 'PageUp'].includes(e.key)) {
          e.preventDefault();
          transitionLeapTo('formatos');
        }
      });
    }

    // 4. Instalación: salto de regreso a Experiencia (hacia arriba)
    if (instalacionSec) {
      window.addEventListener('wheel', (e) => {
        const rect = instalacionSec.getBoundingClientRect();
        const atTop = rect.top >= -40 && rect.top <= 80;
        if (!atTop || isSectionLeaping || isAutoScrolling) return;

        if (e.deltaY < -15) {
          e.preventDefault();
          experienciaLockTime = Date.now() + 1100;
          transitionLeapTo('experiencia');
        }
      }, { passive: false });

      // Teclado en Instalación
      window.addEventListener('keydown', (e) => {
        const rect = instalacionSec.getBoundingClientRect();
        const atTop = rect.top >= -40 && rect.top <= 80;
        if (!atTop || isSectionLeaping || isAutoScrolling) return;

        if (['ArrowUp', 'PageUp'].includes(e.key)) {
          e.preventDefault();
          experienciaLockTime = Date.now() + 1100;
          transitionLeapTo('experiencia');
        }
      });
    }
  }

  function initDock() {
    let ticking = false;
    const threshold = window.innerHeight * 0.4;

    // Estado inicial al cargar
    if (window.scrollY > threshold) {
      currentNavState = 'BOTTOM';
      if (dock) dock.classList.remove('dock-hidden');
      if (heroNavPill && window.innerWidth > 960) heroNavPill.classList.add('is-hidden');
      if (featuresRows) featuresRows.classList.add('features-active');
      if (featuresShowcase) featuresShowcase.classList.add('features-active');
    } else {
      currentNavState = 'TOP';
      if (dock && window.innerWidth > 960) dock.classList.add('dock-hidden');
      if (heroNavPill) heroNavPill.classList.remove('is-hidden', 'is-collapsing');
      if (heroStage) heroStage.classList.remove('is-exiting');
    }

    // Scroll listener continuo para sincronización de navegación
    window.addEventListener('scroll', () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => {
        const scrollY = window.scrollY;
        updateActive();

        if (!isAutoScrolling) {
          const isDesktop = window.innerWidth > 960;
          if (scrollY > threshold) {
            if (featuresRows && !featuresRows.classList.contains('features-active')) {
              featuresRows.classList.add('features-active');
            }
            if (featuresShowcase && !featuresShowcase.classList.contains('features-active')) {
              featuresShowcase.classList.add('features-active');
            }
            if (isDesktop && currentNavState === 'TOP') {
              currentNavState = 'BOTTOM';
              if (dock) dock.classList.remove('dock-hidden');
              if (heroNavPill) heroNavPill.classList.add('is-hidden');
            }
          } else if (scrollY < threshold) {
            if (isDesktop && currentNavState === 'BOTTOM') {
              currentNavState = 'TOP';
              if (dock) dock.classList.add('dock-hidden');
              if (heroNavPill) heroNavPill.classList.remove('is-hidden', 'is-collapsing');
              if (heroStage) heroStage.classList.remove('is-exiting');
            }
            const heroNav = $('.hero-nav');
            if (heroNav) {
              heroNav.classList.remove('is-morphing-to-drop', 'is-condensing');
            }
            const dropletBead = $('#dropletBead');
            if (dropletBead) {
              dropletBead.classList.remove('is-plunging', 'is-shooting-up');
            }
          }
        }
        ticking = false;
      });
    }, { passive: true });

    // Rueda del ratón: transición fluida automática entre Hero y Características
    window.addEventListener('wheel', (e) => {
      if (isAutoScrolling) return;
      const funcionesSec = document.getElementById('funciones');
      if (!funcionesSec) return;

      const heroH = window.innerHeight * 0.45;

      if (e.deltaY > 18 && window.scrollY < heroH && currentNavState === 'TOP') {
        e.preventDefault();
        transitionToFeatures();
      } else if (e.deltaY < -18 && window.scrollY <= funcionesSec.offsetTop + 40 && currentNavState === 'BOTTOM') {
        e.preventDefault();
        transitionToHero();
      }
    }, { passive: false });

    // Gestos táctiles en pantallas táctiles / móviles
    let touchStartY = 0;
    window.addEventListener('touchstart', (e) => {
      if (e.touches && e.touches.length) {
        touchStartY = e.touches[0].clientY;
      }
    }, { passive: true });

    window.addEventListener('touchend', (e) => {
      if (isAutoScrolling) return;
      if (!e.changedTouches || !e.changedTouches.length) return;
      const touchEndY = e.changedTouches[0].clientY;
      const diffY = touchStartY - touchEndY;
      const funcionesSec = document.getElementById('funciones');
      if (!funcionesSec) return;

      if (diffY > 40 && window.scrollY < window.innerHeight * 0.4 && currentNavState === 'TOP') {
        transitionToFeatures();
      } else if (diffY < -40 && window.scrollY <= funcionesSec.offsetTop + 40 && currentNavState === 'BOTTOM') {
        transitionToHero();
      }
    }, { passive: true });

    // Botón scroll cue en el hero
    const heroScrollCue = $('.hero-scroll-cue');
    if (heroScrollCue) {
      heroScrollCue.addEventListener('click', (e) => {
        e.preventDefault();
        transitionToFeatures();
      });
    }

    // Interceptar enlaces de la cabecera superior (hero-menu-link) para activar la transición física
    heroNavLinks.forEach((link) => {
      link.addEventListener('click', (e) => {
        const target = link.dataset.target;
        if (target === 'funciones' && currentNavState === 'TOP') {
          e.preventDefault();
          transitionToFeatures();
        } else if (currentNavState === 'TOP') {
          e.preventDefault();
          const targetEl = document.getElementById(target);
          transitionToFeatures();
          if (targetEl) {
            setTimeout(() => {
              targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 820);
          }
        }
      });
    });

    // Interceptar enlaces del dock para usar navegación y transiciones controladas
    dockLinks.forEach((link) => {
      link.addEventListener('click', (e) => {
        const target = link.dataset.target;
        if (target === 'inicio') {
          e.preventDefault();
          transitionToHero();
        } else if (target === 'funciones') {
          e.preventDefault();
          if (currentNavState === 'TOP') {
            transitionToFeatures();
          } else {
            transitionLeapTo('funciones', () => {
              if (typeof window.__resetFeaturesStep === 'function') window.__resetFeaturesStep();
            });
          }
        } else if (target === 'galeria' || target === 'capturas') {
          e.preventDefault();
          transitionLeapTo('galeria', () => {
            if (typeof window.__resetGalleryStep === 'function') window.__resetGalleryStep();
          });
        } else if (target === 'formatos') {
          e.preventDefault();
          transitionLeapTo('formatos');
        } else if (target === 'instalacion') {
          e.preventDefault();
          transitionLeapTo('instalacion');
        }
      });
    });

    const expCtaBtn = $('#experienceCtaBtn');
    if (expCtaBtn) {
      expCtaBtn.addEventListener('click', (e) => {
        e.preventDefault();
        transitionLeapTo('instalacion');
      });
    }

    const dockCta = $('.dock-cta');
    if (dockCta) {
      dockCta.addEventListener('click', (e) => {
        e.preventDefault();
        transitionLeapTo('instalacion');
      });
    }

    window.addEventListener('resize', () => {
      placeIndicator();
      if (window.innerWidth <= 960 && dock) {
        dock.classList.remove('dock-hidden');
      }
    });

    if (document.fonts && document.fonts.ready) document.fonts.ready.then(placeIndicator);

    const targetMockup = heroMockupCard || rocketPreviewBtn;
    if (targetMockup && lightbox) {
      const openLightbox = () => {
        if (typeof lightbox.showModal === 'function') {
          lightboxImg.src = 'images/now_playing.png';
          lightboxImg.alt = t('heroAlt');
          lightbox.showModal();
        } else {
          window.open('images/now_playing.png', '_blank', 'noopener');
        }
      };
      targetMockup.addEventListener('click', openLightbox);
      targetMockup.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          openLightbox();
        }
      });
    }

    const heroMockupBack = $('#heroMockupBack');
    if (heroMockupBack && lightbox) {
      const openBackLightbox = () => {
        if (typeof lightbox.showModal === 'function') {
          lightboxImg.src = 'images/home_UI.png';
          lightboxImg.alt = 'Aiiko Music Library & Queue';
          lightbox.showModal();
        } else {
          window.open('images/home_UI.png', '_blank', 'noopener');
        }
      };
      heroMockupBack.addEventListener('click', openBackLightbox);
      heroMockupBack.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          openBackLightbox();
        }
      });
    }
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

  /* ---------- Barras de Scroll Auto-Ocultables Fluent (Windows 11) ---------- */

  function initAutoHideScrollbar() {
    let scrollbarHideTimer = null;
    function notifyScrollActivity() {
      document.body.classList.add('is-scrolling');
      if (scrollbarHideTimer) clearTimeout(scrollbarHideTimer);
      scrollbarHideTimer = setTimeout(() => {
        document.body.classList.remove('is-scrolling');
      }, 900);
    }

    window.addEventListener('scroll', notifyScrollActivity, { passive: true });
    window.addEventListener('wheel', notifyScrollActivity, { passive: true });
    window.addEventListener('touchmove', notifyScrollActivity, { passive: true });
  }

  /* ---------- Superficie reactiva a la luz en características (Specular Light Sheen) ---------- */

  function initSurfaceLightSheen() {
    const sheenCards = $$('.features-focus-card');
    sheenCards.forEach((card) => {
      card.addEventListener('pointermove', (e) => {
        const media = card.querySelector('.focus-media-img');
        if (!media) return;
        const rect = media.getBoundingClientRect();
        const x = Math.max(0, Math.min(100, ((e.clientX - rect.left) / rect.width) * 100));
        const y = Math.max(0, Math.min(100, ((e.clientY - rect.top) / rect.height) * 100));
        media.style.setProperty('--sheen-x', `${x.toFixed(1)}%`);
        media.style.setProperty('--sheen-y', `${y.toFixed(1)}%`);
      }, { passive: true });
    });
  }

  /* ---------- Inicio ---------- */

  initAutoHideScrollbar();
  initSurfaceLightSheen();
  initBrandIntro();
  initReveal();
  initTaglineReveal();
  initExperienceReveal();
  initFeaturesScrollStage();
  initFeaturesModal();
  initDualGalleryParallax();
  initSectionTransitionLeaps();
  initLightbox();
  initLangMenu();
  initDock();

  setLanguage(detectInitialLanguage(), false);
  updateActive();
  loadRelease();
})();
