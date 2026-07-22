import React, { useEffect } from 'react';
import { Globe } from 'lucide-react';
import { useAppStore } from './store/appStore';
import { useWebSocket } from './hooks/useWebSocket';
import { UrlPanel } from './components/UrlPanel';
import { PreviewPanel } from './components/PreviewPanel';
import { AdvancedPanel } from './components/AdvancedPanel';
import { QueuePanel } from './components/QueuePanel';
import { ProgressPanel } from './components/ProgressPanel';
import { ToastOverlay } from './components/ToastOverlay';
import { getTranslation } from './i18n/translations';

const App: React.FC = () => {
  const {
    preferences,
    fetchPreferences,
    fetchProfiles,
    fetchQueue,
    fetchHistory,
    fetchSystemStatus,
    updatePreferences,
    handleWsEvent
  } = useAppStore();

  // 1. Establish single global WebSocket connection
  useWebSocket(handleWsEvent);

  // 2. Fetch baseline data on app mount
  useEffect(() => {
    fetchPreferences();
    fetchProfiles();
    fetchQueue();
    fetchHistory();
    fetchSystemStatus();
  }, [fetchPreferences, fetchProfiles, fetchQueue, fetchHistory, fetchSystemStatus]);

  // 3. Keep HTML document theme aligned with preferences state
  useEffect(() => {
    const theme = (preferences?.current_theme || 'makara').toLowerCase();
    
    // Remove all active theme classes
    const themeList = ['theme-makara', 'theme-gece-mavisi', 'theme-orman', 'theme-kagit', 'theme-bulut', 'theme-bahce'];
    themeList.forEach(t => document.documentElement.classList.remove(t));
    
    // Add selected theme class
    document.documentElement.classList.add(`theme-${theme}`);

    // Synchronize Tailwind standard dark class for selector utility
    const isDark = ['makara', 'gece-mavisi', 'orman'].includes(theme);
    if (isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [preferences?.current_theme]);

  // 4. Global keyboard shortcuts hook
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        console.log('[Shortcut] Escape pressed.');
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const currentLang = preferences?.current_lang || 'en';

  const handleLanguageChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    await updatePreferences({ current_lang: e.target.value });
  };

  // Safe fallback if preferences are loading
  if (!preferences) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-[#14110F] text-[#F2ECDF]">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-[#E8A33D] border-t-transparent" />
          <span className="text-sm font-semibold tracking-wider">
            yt-dlp Downloader Pro yükleniyor...
          </span>
        </div>
      </div>
    );
  }

  const appStatusText = getTranslation(currentLang, 'lbl_connected');

  return (
    <div className="min-h-screen w-full bg-[var(--bg)] text-[var(--ink)] relative overflow-x-hidden font-sans">
      {/* Cinematic Film Grain Overlay */}
      <div className="grain" />

      {/* Sprocket Rail Topband */}
      <div className="topband">
        <div className="sprocket-rail">
          {Array.from({ length: 52 }, (_, i) => (
            <span key={i} />
          ))}
        </div>
      </div>

      {/* Main Container */}
      <div className="max-w-[1180px] mx-auto px-6 pb-20 pt-2 flex flex-col gap-6 relative z-10">
        
        {/* Navigation / Header */}
        <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--hairline)] pb-5">
          <div className="flex items-center gap-3.5">
            <div className="brand-mark" />
            <div className="flex flex-col">
              <h1 className="text-2xl font-semibold tracking-widest font-display">
                MAKARA
              </h1>
              <p className="text-[10px] font-mono tracking-widest text-[var(--ink-dim)] uppercase mt-0.5">
                {currentLang === 'tr' ? 'Tarama & Aktarım Odası' : currentLang === 'es' ? 'Sala de Escaneo y Transferencia' : 'Scan & Transfer Room'}
              </p>
            </div>
          </div>

          {/* Localization & Theme Dropdowns */}
          <div className="flex items-center gap-3">
            {/* Connection Indicator */}
            <div className="pill hidden md:flex">
              <span className="dot-live" />
              <span>{appStatusText} · 127.0.0.1:8765</span>
            </div>

            {/* Language Selection */}
            <div className="flex items-center gap-2 rounded-[var(--radius)] border border-[var(--hairline-strong)] bg-[var(--bg-elevated)] px-3 py-1.5">
              <Globe className="h-4 w-4 text-[var(--ink-dim)]" />
              <select
                value={currentLang}
                onChange={handleLanguageChange}
                className="bg-transparent text-xs font-semibold outline-none cursor-pointer text-[var(--ink)]"
              >
                <option value="en" className="bg-[var(--bg-elevated)] text-[var(--ink)]">EN</option>
                <option value="tr" className="bg-[var(--bg-elevated)] text-[var(--ink)]">TR</option>
                <option value="es" className="bg-[var(--bg-elevated)] text-[var(--ink)]">ES</option>
              </select>
            </div>

            {/* Thematic Multi-Theme Selection */}
            <div className="flex items-center gap-2 rounded-[var(--radius)] border border-[var(--hairline-strong)] bg-[var(--bg-elevated)] px-3 py-1.5">
              <span className="text-xs">🎨</span>
              <select
                value={preferences?.current_theme || 'makara'}
                onChange={async (e) => {
                  await updatePreferences({ current_theme: e.target.value });
                }}
                className="bg-transparent text-xs font-semibold outline-none cursor-pointer text-[var(--ink)]"
              >
                <option value="makara" className="bg-[var(--bg-elevated)] text-[var(--ink)]">
                  {getTranslation(currentLang, 'theme_makara')}
                </option>
                <option value="gece-mavisi" className="bg-[var(--bg-elevated)] text-[var(--ink)]">
                  {getTranslation(currentLang, 'theme_gece_mavisi')}
                </option>
                <option value="orman" className="bg-[var(--bg-elevated)] text-[var(--ink)]">
                  {getTranslation(currentLang, 'theme_orman')}
                </option>
                <option value="kagit" className="bg-[var(--bg-elevated)] text-[var(--ink)]">
                  {getTranslation(currentLang, 'theme_kagit')}
                </option>
                <option value="bulut" className="bg-[var(--bg-elevated)] text-[var(--ink)]">
                  {getTranslation(currentLang, 'theme_bulut')}
                </option>
                <option value="bahce" className="bg-[var(--bg-elevated)] text-[var(--ink)]">
                  {getTranslation(currentLang, 'theme_bahce')}
                </option>
              </select>
            </div>
          </div>
        </header>

        {/* Dashboard Panels Layout Grid */}
        <main className="grid grid-cols-1 lg:grid-cols-12 gap-0 border border-[var(--hairline)] rounded-[var(--radius)] overflow-hidden bg-[var(--bg-elevated)] shadow-[var(--shadow)]">
          
          {/* Left Column (Input, Preview, Queue) */}
          <section className="lg:col-span-7 flex flex-col border-r border-[var(--hairline)]">
            <UrlPanel />
            <PreviewPanel />
            <QueuePanel />
          </section>

          {/* Right Column (Advanced configs, Progress) */}
          <section className="lg:col-span-5 flex flex-col">
            <AdvancedPanel />
            <ProgressPanel />
          </section>

        </main>

        {/* Global Toast Overlay */}
        <ToastOverlay />

      </div>
    </div>
  );
};

export default App;
