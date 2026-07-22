import React, { useState, useEffect, useRef } from 'react';
import { Search, Folder, X, Loader2, Link2, CheckCircle2, AlertTriangle } from 'lucide-react';
import { useAppStore } from '../store/appStore';
import { getTranslation } from '../i18n/translations';
import { apiClient } from '../api/client';

export const UrlPanel: React.FC = () => {
  const {
    preferences,
    updatePreferences,
    metadataState,
    fetchMetadata,
    clearMetadata,
    addToast,
    addTask
  } = useAppStore();

  const [url, setUrl] = useState('');
  const [outputDir, setOutputDir] = useState('');
  const debounceTimerRef = useRef<number | null>(null);

  // Spotify integration local states
  const [spotifyTracks, setSpotifyTracks] = useState<Array<{ name: string; artists: string; duration: number; thumbnail: string }>>([]);
  const [spotifyLoading, setSpotifyLoading] = useState(false);
  const [selectedTracks, setSelectedTracks] = useState<Record<number, boolean>>({});

  const currentLang = preferences?.current_lang || 'en';

  // Sync output directory from global preferences state
  useEffect(() => {
    if (preferences) {
      setOutputDir(preferences.output_dir);
    }
  }, [preferences]);

  // Debounced auto-fetch video metadata on URL paste/type
  useEffect(() => {
    if (debounceTimerRef.current) {
      window.clearTimeout(debounceTimerRef.current);
    }

    const trimmedUrl = url.trim();
    if (!trimmedUrl) {
      clearMetadata();
      return;
    }

    // Basic URL validation
    if (!trimmedUrl.startsWith('http://') && !trimmedUrl.startsWith('https://')) {
      return;
    }

    // Ignore Spotify playlist URLs for auto-fetching metadata (we handle them separately)
    if (trimmedUrl.includes('open.spotify.com/playlist/')) {
      return;
    }

    // Don't auto-fetch if we already have this URL's data loaded or loading
    if (metadataState.data?.url === trimmedUrl || metadataState.loading) {
      return;
    }

    debounceTimerRef.current = window.setTimeout(() => {
      fetchMetadata(trimmedUrl, preferences?.browser_cookies || 'disabled');
    }, 1000); // 1 second debounce to prevent spamming yt-dlp queries

    return () => {
      if (debounceTimerRef.current) {
        window.clearTimeout(debounceTimerRef.current);
      }
    };
  }, [url, fetchMetadata, preferences?.browser_cookies, clearMetadata, metadataState.data?.url, metadataState.loading]);

  const handleManualFetch = () => {
    const trimmedUrl = url.trim();
    if (!trimmedUrl.startsWith('http://') && !trimmedUrl.startsWith('https://')) {
      addToast(getTranslation(currentLang, 'err_invalid_url'), 'warning');
      return;
    }
    fetchMetadata(trimmedUrl, preferences?.browser_cookies || 'disabled');
  };

  const handleClearUrl = () => {
    setUrl('');
    clearMetadata();
  };

  const handleBrowseFolder = async () => {
    try {
      const res = await apiClient.post('/config/select-directory');
      if (res.data && res.data.directory) {
        setOutputDir(res.data.directory);
        await updatePreferences({ output_dir: res.data.directory });
      }
    } catch (err) {
      console.error('Folder picker failed:', err);
      addToast(getTranslation(currentLang, 'err_folder_picker_failed'), 'error');
    }
  };

  const handleOutputDirChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const path = e.target.value;
    setOutputDir(path);
  };

  const handleOutputDirBlur = async () => {
    if (preferences && outputDir !== preferences.output_dir) {
      await updatePreferences({ output_dir: outputDir });
    }
  };

  const handleSpotifyFetch = async () => {
    const trimmedUrl = url.trim();
    if (!trimmedUrl.includes('open.spotify.com/playlist/')) {
      addToast('Lütfen geçerli bir Spotify Çalma Listesi URL\'si girin.', 'warning');
      return;
    }
    setSpotifyLoading(true);
    setSpotifyTracks([]);
    try {
      const res = await apiClient.post('/spotify/playlist-tracks', { url: trimmedUrl });
      if (res.data && Array.isArray(res.data.tracks)) {
        setSpotifyTracks(res.data.tracks);
        // select all by default
        const initialSelects: Record<number, boolean> = {};
        res.data.tracks.forEach((_: any, idx: number) => {
          initialSelects[idx] = true;
        });
        setSelectedTracks(initialSelects);
        addToast(`${res.data.tracks.length} şarkı başarıyla yüklendi!`, 'success');
      }
    } catch (err: any) {
      console.error('Spotify fetch failed:', err);
      const detail = err.response?.data?.detail || 'Spotify çalma listesi yüklenemedi. Lütfen Client ID ve Secret ayarlarınızı kontrol edin.';
      addToast(detail, 'error');
    } finally {
      setSpotifyLoading(false);
    }
  };

  const handleAddSelectedToQueue = async () => {
    const selectedList = spotifyTracks.filter((_, idx) => selectedTracks[idx]);
    if (selectedList.length === 0) {
      addToast('Lütfen kuyruğa eklemek için en az bir şarkı seçin.', 'warning');
      return;
    }
    
    // settings for the downloads
    const settings = {
      mode: 'Audio', // default to Audio for Spotify downloads
      active_profile: preferences?.active_profile || 'best'
    };
    
    let addedCount = 0;
    for (const track of selectedList) {
      try {
        const queryUrl = `ytsearch1:${track.artists} - ${track.name}`;
        await addTask(queryUrl, settings);
        addedCount++;
      } catch (err) {
        console.error('Failed to add track to queue:', track.name, err);
      }
    }
    
    addToast(`${addedCount} şarkı indirme kuyruğuna eklendi!`, 'success');
    // Clear list
    setSpotifyTracks([]);
    setUrl('');
  };

  return (
    <div className="w-full border-b border-[var(--hairline)] p-6 transition-all duration-300">
      <div className="flex flex-col gap-5">
        {/* Title */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="panel-idx">01</span>
            <h2 className="text-xs font-semibold tracking-widest text-[var(--ink-dim)] uppercase font-mono">
              {getTranslation(currentLang, 'lbl_media_source')}
            </h2>
          </div>
          <Link2 className="h-4 w-4 text-[var(--accent)]" />
        </div>

        {/* URL Input Row */}
        <div className="flex flex-col gap-1.5">
          <label className="text-[10px] font-mono tracking-widest text-[var(--ink-faint)] uppercase px-1">
            {getTranslation(currentLang, 'url_label')}
          </label>
          <div className="relative flex items-center">
            <div className="pointer-events-none absolute left-4 text-[var(--ink-faint)]">
              <Search className="h-4 w-4" />
            </div>
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder={getTranslation(currentLang, 'lbl_url_placeholder')}
              className="w-full rounded-[var(--radius)] border border-[var(--hairline-strong)] bg-[var(--bg-recessed)] py-3 pl-11 pr-28 text-xs font-mono outline-none transition-all placeholder:text-[var(--ink-faint)] focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)] text-[var(--ink)]"
            />
            <div className="absolute right-2 flex items-center gap-1.5">
              {url && (
                <button
                  onClick={handleClearUrl}
                  className="rounded-md p-1 text-[var(--ink-faint)] hover:bg-[var(--hairline)] hover:text-[var(--ink)]"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              )}
              {url.trim().includes('open.spotify.com/playlist/') ? (
                <button
                  onClick={handleSpotifyFetch}
                  disabled={spotifyLoading || !url.trim()}
                  className="flex items-center justify-center gap-1.5 rounded-[var(--radius)] bg-green-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-green-700 disabled:pointer-events-none disabled:opacity-50 transition-all font-mono"
                >
                  {spotifyLoading ? (
                    <>
                      <Loader2 className="h-3 w-3 animate-spin" />
                      <span>Çözümleniyor...</span>
                    </>
                  ) : (
                    <span>Spotify Çözümle</span>
                  )}
                </button>
              ) : (
                <button
                  onClick={handleManualFetch}
                  disabled={metadataState.loading || !url.trim()}
                  className="flex items-center justify-center gap-1.5 rounded-[var(--radius)] bg-[var(--accent)] px-3 py-1.5 text-xs font-semibold text-[var(--accent-ink)] hover:bg-[var(--accent-deep)] disabled:pointer-events-none disabled:opacity-50 transition-all font-mono"
                >
                  {metadataState.loading ? (
                    <>
                      <Loader2 className="h-3 w-3 animate-spin" />
                      <span>{getTranslation(currentLang, 'lbl_fetching')}</span>
                    </>
                  ) : (
                    <span>{getTranslation(currentLang, 'lbl_query_btn')}</span>
                  )}
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Directory Picker Row */}
        <div className="flex flex-col gap-1.5">
          <label className="text-[10px] font-mono tracking-widest text-[var(--ink-faint)] uppercase px-1">
            {getTranslation(currentLang, 'lbl_save_folder')}
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={outputDir}
              onChange={handleOutputDirChange}
              onBlur={handleOutputDirBlur}
              placeholder={getTranslation(currentLang, 'lbl_folder_placeholder')}
              className="w-full rounded-[var(--radius)] border border-[var(--hairline-strong)] bg-[var(--bg-recessed)] px-4 py-3 text-xs font-mono outline-none transition-all placeholder:text-[var(--ink-faint)] focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)] text-[var(--ink)]"
            />
            <button
              onClick={handleBrowseFolder}
              className="flex items-center gap-2 rounded-[var(--radius)] border border-[var(--hairline-strong)] bg-[var(--bg-recessed)] px-4 py-3 text-xs font-semibold text-[var(--ink)] hover:border-[var(--accent)] hover:text-[var(--accent)] active:scale-95 transition-all font-mono"
            >
              <Folder className="h-3.5 w-3.5" />
              <span>{getTranslation(currentLang, 'btn_browse')}</span>
            </button>
          </div>
        </div>

        {/* Loading / Status Messages */}
        {metadataState.loading && (
          <div className="flex items-center gap-3 rounded-[var(--radius)] bg-[var(--bg-recessed)] p-4 border border-[var(--hairline-strong)]">
            <Loader2 className="h-5 w-5 animate-spin text-[var(--accent)]" />
            <div className="flex flex-col">
              <span className="text-xs font-semibold text-[var(--ink)]">
                {getTranslation(currentLang, 'lbl_analysis_starting')}
              </span>
              <span className="text-[11px] text-[var(--ink-dim)]">
                {getTranslation(currentLang, 'lbl_analysis_detail')}
              </span>
            </div>
          </div>
        )}

        {metadataState.error && (
          <div className="flex items-center gap-3 rounded-[var(--radius)] bg-[var(--bg-recessed)] p-4 border border-[var(--error)]/30">
            <AlertTriangle className="h-5 w-5 text-[var(--error)]" />
            <div className="flex flex-col">
              <span className="text-xs font-semibold text-[var(--error)]">
                {getTranslation(currentLang, 'lbl_query_failed')}
              </span>
              <span className="text-[11px] text-[var(--ink-dim)]">
                {metadataState.error}
              </span>
            </div>
          </div>
        )}

        {!metadataState.loading && metadataState.data && (
          <div className="flex items-center gap-3 rounded-[var(--radius)] bg-[var(--bg-recessed)] p-4 border border-[var(--success)]/30">
            <CheckCircle2 className="h-5 w-5 text-[var(--success)]" />
            <div className="flex flex-col">
              <span className="text-xs font-semibold text-[var(--success)]">
                {getTranslation(currentLang, 'lbl_video_resolved')}
              </span>
              <span className="text-[11px] text-[var(--ink-dim)]">
                {getTranslation(currentLang, 'lbl_video_resolved_detail', { title: metadataState.data.title })}
              </span>
            </div>
          </div>
        )}

        {/* Spotify Playlist tracks selection */}
        {spotifyTracks.length > 0 && (
          <div className="flex flex-col gap-3 border-t border-[var(--hairline)] pt-4 mt-2 animate-slide-in">
            <div className="flex items-center justify-between px-1">
              <span className="text-xs font-bold text-[var(--ink)] font-mono">
                🎵 Çalma Listesi: {spotifyTracks.length} Şarkı Yüklendi
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    const allSelected: Record<number, boolean> = {};
                    spotifyTracks.forEach((_, idx) => {
                      allSelected[idx] = true;
                    });
                    setSelectedTracks(allSelected);
                  }}
                  className="text-[10px] font-mono text-[var(--accent)] hover:underline"
                >
                  Tümünü Seç
                </button>
                <span className="text-[10px] text-[var(--ink-faint)]">|</span>
                <button
                  onClick={() => setSelectedTracks({})}
                  className="text-[10px] font-mono text-[var(--ink-faint)] hover:text-[var(--ink)] hover:underline"
                >
                  Seçimleri Kaldır
                </button>
              </div>
            </div>

            {/* Scrollable Song List */}
            <div className="max-h-60 overflow-y-auto border border-[var(--hairline-strong)] rounded-[var(--radius)] bg-[var(--bg-recessed)] divide-y divide-[var(--hairline)]">
              {spotifyTracks.map((track, idx) => (
                <div key={idx} className="flex items-center gap-3 p-2.5 hover:bg-[var(--bg-elevated)] transition-colors">
                  <input
                    type="checkbox"
                    checked={!!selectedTracks[idx]}
                    onChange={() => {
                      setSelectedTracks(prev => ({
                        ...prev,
                        [idx]: !prev[idx]
                      }));
                    }}
                    className="h-3.5 w-3.5 rounded border-[var(--hairline-strong)] text-[var(--accent)] focus:ring-[var(--accent)] bg-[var(--bg-recessed)] cursor-pointer"
                  />
                  {track.thumbnail ? (
                    <img src={track.thumbnail} alt="" className="w-9 h-9 rounded object-cover flex-none" />
                  ) : (
                    <div className="w-9 h-9 bg-[var(--bg-elevated)] rounded flex items-center justify-center text-[var(--ink-faint)] flex-none">
                      🎵
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold text-[var(--ink)] truncate">{track.name}</p>
                    <p className="text-[10px] text-[var(--ink-faint)] truncate">{track.artists}</p>
                  </div>
                  <div className="text-[10px] font-mono text-[var(--ink-faint)] flex-none px-2">
                    {Math.floor(track.duration / 60)}:{(track.duration % 60).toString().padStart(2, '0')}
                  </div>
                </div>
              ))}
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-2">
              <button
                onClick={handleAddSelectedToQueue}
                className="flex-1 rounded-[var(--radius)] bg-[var(--accent)] py-2.5 text-xs font-bold uppercase tracking-widest text-[var(--accent-ink)] hover:bg-[var(--accent-deep)] active:scale-98 transition-all font-mono"
              >
                Seçilen {Object.values(selectedTracks).filter(Boolean).length} Şarkıyı İndirme Kuyruğuna Ekle
              </button>
              <button
                onClick={() => setSpotifyTracks([])}
                className="rounded-[var(--radius)] border border-[var(--hairline-strong)] px-4 py-2.5 text-xs font-semibold text-[var(--ink)] hover:border-red-500/50 hover:text-red-500 transition-all font-mono"
              >
                İptal Et
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
