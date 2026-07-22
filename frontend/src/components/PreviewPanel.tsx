import React, { useState, useEffect } from 'react';
import { Video, User, Plus, Trash2, Milestone } from 'lucide-react';
import { useAppStore } from '../store/appStore';
import { getTranslation } from '../i18n/translations';
import { apiClient } from '../api/client';

export const PreviewPanel: React.FC = () => {
  const {
    metadataState,
    preferences,
    updatePreferences,
    addTask,
    profiles,
    fetchProfiles
  } = useAppStore();

  const data = metadataState.data;
  const currentLang = preferences?.current_lang || 'en';

  // Local state for clips list and current crop window
  const [clipEnabled, setClipEnabled] = useState(false);
  const [clipStart, setClipStart] = useState('00:00');
  const [clipEnd, setClipEnd] = useState('00:00');
  const [selectedProfile, setSelectedProfile] = useState('Default (No Profile)');
  const [addedClips, setAddedClips] = useState<Array<{
    id: string;
    start: number;
    end: number;
    profile: string;
  }>>([]);
  const [sponsorSegments, setSponsorSegments] = useState<Array<{ start: number; end: number; category: string }>>([]);

  // Fetch SponsorBlock segments when a new video is loaded
  useEffect(() => {
    const videoId = data?.raw_info?.id || data?.id;
    if (videoId) {
      const fetchSponsors = async () => {
        try {
          const res = await apiClient.get(`/metadata/sponsorblock/${encodeURIComponent(videoId)}`);
          if (Array.isArray(res.data)) {
            setSponsorSegments(res.data);
          } else {
            setSponsorSegments([]);
          }
        } catch (err) {
          console.error('Failed to fetch SponsorBlock segments:', err);
          setSponsorSegments([]);
        }
      };
      fetchSponsors();
    } else {
      setSponsorSegments([]);
    }
  }, [data]);

  // Fetch profiles on mount
  useEffect(() => {
    fetchProfiles();
  }, [fetchProfiles]);

  // Reset local state when a new video is loaded
  useEffect(() => {
    if (data) {
      setClipEnabled(false);
      setClipStart('00:00');
      const totalSec = Math.floor(data.duration || 0);
      setClipEnd(formatSeconds(totalSec));
      setAddedClips([]);
    }
  }, [data]);

  if (!data) return null;

  const durationSec = Math.floor(data.duration || 0);

  // Time conversion helpers
  function formatSeconds(secs: number): string {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    const pad = (n: number) => n.toString().padStart(2, '0');
    if (m >= 60) {
      const h = Math.floor(m / 60);
      return `${pad(h)}:${pad(m % 60)}:${pad(s)}`;
    }
    return `${pad(m)}:${pad(s)}`;
  }

  // Parse custom format helper
  function parseTimeToSeconds(timeStr: string): number {
    const parts = timeStr.trim().split(':').map(Number);
    if (parts.some(isNaN)) return 0;
    if (parts.length === 3) {
      return parts[0] * 3600 + parts[1] * 60 + parts[2];
    }
    if (parts.length === 2) {
      return parts[0] * 60 + parts[1];
    }
    return parts[0] || 0;
  }

  const handleSetClipStart = (val: string) => {
    setClipStart(val);
    setClipEnabled(true);
  };

  const handleSetClipEnd = (val: string) => {
    setClipEnd(val);
    setClipEnabled(true);
  };

  const handleChapterClick = (start: number, end: number) => {
    setClipStart(formatSeconds(Math.floor(start)));
    setClipEnd(formatSeconds(Math.floor(end)));
    setClipEnabled(true);
  };

  const handleAddClip = () => {
    const startSec = parseTimeToSeconds(clipStart);
    const endSec = parseTimeToSeconds(clipEnd);

    if (startSec >= endSec) {
      alert(getTranslation(currentLang, 'err_clip_start_end'));
      return;
    }

    const newClip = {
      id: Math.random().toString(36).substring(2, 9),
      start: startSec,
      end: endSec,
      profile: selectedProfile
    };

    setAddedClips([...addedClips, newClip]);
  };

  const handleRemoveClip = (id: string) => {
    setAddedClips(addedClips.filter(c => c.id !== id));
  };

  const handleAddToQueue = async () => {
    const settings = {
      video_profile: preferences?.active_profile || 'Custom',
      video_limit: preferences?.custom_settings?.video_limit || '1080',
      ...preferences
    };

    if (addedClips.length > 0) {
      const clipsPayload = addedClips.map(c => ({
        start: c.start,
        end: c.end,
        profile: c.profile,
        output_name: `_clip_${formatSeconds(c.start).replace(/:/g, '-')}_to_${formatSeconds(c.end).replace(/:/g, '-')}`,
        clip_precise: true
      }));
      await addTask(data.url, settings, clipsPayload);
    } else {
      const payload: any = {
        url: data.url,
        settings: {
          ...settings,
          clip_enabled: clipEnabled,
          clip_start: clipEnabled ? clipStart : '00:00',
          clip_end: clipEnabled ? clipEnd : formatSeconds(durationSec)
        }
      };
      await addTask(data.url, payload.settings);
    }
  };

  return (
    <div className="w-full border-b border-[var(--hairline)] p-6 transition-all duration-300">
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
        
        {/* Thumbnail Viewfinder Column */}
        <div className="md:col-span-2 flex flex-col gap-3">
          <div className="viewfinder-frame relative overflow-hidden rounded-[var(--radius)] bg-[var(--bg-recessed)] border border-[var(--hairline-strong)]">
            <div className="viewfinder-corner tl" />
            <div className="viewfinder-corner tr" />
            <div className="viewfinder-corner bl" />
            <div className="viewfinder-corner br" />

            {data.thumbnail_img ? (
              <img
                src={data.thumbnail_img}
                alt={data.title}
                className="aspect-video w-full object-cover opacity-85 transition-transform duration-500 hover:scale-105"
              />
            ) : (
              <div className="flex aspect-video w-full items-center justify-center text-[var(--ink-faint)]">
                <Video className="h-12 w-12 stroke-[1.5]" />
              </div>
            )}
            <div className="timecode font-mono text-xs absolute bottom-2.5 right-2.5 bg-[var(--scrim)] text-white px-2 py-0.5 rounded-[var(--radius)] tracking-widest">
              {formatSeconds(durationSec)}
            </div>
          </div>
          
          <div className="flex flex-col gap-1.5">
            <h3 className="line-clamp-2 text-sm font-semibold font-display text-[var(--ink)] leading-tight">
              {data.title}
            </h3>
            <div className="flex items-center gap-1.5 text-xs text-[var(--ink-dim)]">
              <User className="h-3.5 w-3.5" />
              <span className="font-medium">{data.uploader || data.channel_name || getTranslation(currentLang, 'lbl_unknown_channel')}</span>
            </div>
          </div>
        </div>

        {/* Custom Clipping Actions Column */}
        <div className="md:col-span-3 flex flex-col gap-5 justify-between">
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-2">
              <span className="panel-idx">02</span>
              <h2 className="text-xs font-semibold tracking-widest text-[var(--ink-dim)] uppercase font-mono">
                {getTranslation(currentLang, 'lbl_clip_settings')}
              </h2>
            </div>

            {/* Clipping Toggle & Input Blocks */}
            <div className="flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-[var(--ink)]">
                  {getTranslation(currentLang, 'lbl_clip_range')}
                </span>
                <div 
                  className={`toggle-sw ${clipEnabled ? 'on' : ''}`}
                  onClick={() => setClipEnabled(!clipEnabled)}
                />
              </div>

              {clipEnabled && (
                <div className="flex flex-col gap-3 animate-slide-in">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="flex flex-col gap-1.5">
                      <label className="text-[10px] font-mono tracking-widest text-[var(--ink-faint)] uppercase px-1">
                        {getTranslation(currentLang, 'lbl_start')}
                      </label>
                      <input
                        type="text"
                        value={clipStart}
                        onChange={(e) => handleSetClipStart(e.target.value)}
                        placeholder="00:00"
                        className="rounded-[var(--radius)] border border-[var(--hairline-strong)] bg-[var(--bg-recessed)] px-3 py-2 text-center text-xs font-mono outline-none transition-all focus:border-[var(--accent)] text-[var(--ink)]"
                      />
                    </div>
                    <div className="flex flex-col gap-1.5">
                      <label className="text-[10px] font-mono tracking-widest text-[var(--ink-faint)] uppercase px-1">
                        {getTranslation(currentLang, 'lbl_end')}
                      </label>
                      <input
                        type="text"
                        value={clipEnd}
                        onChange={(e) => handleSetClipEnd(e.target.value)}
                        placeholder="00:00"
                        className="rounded-[var(--radius)] border border-[var(--hairline-strong)] bg-[var(--bg-recessed)] px-3 py-2 text-center text-xs font-mono outline-none transition-all focus:border-[var(--accent)] text-[var(--ink)]"
                      />
                    </div>
                  </div>

                  {/* Interactive Dual Range Slider with Chapters and Sponsors Overlays */}
                  <div className="range-slider-container">
                    <div className="range-slider-track">
                      {/* SponsorBlock segments */}
                      {sponsorSegments.map((seg, idx) => {
                        const left = (seg.start / durationSec) * 100;
                        const width = ((seg.end - seg.start) / durationSec) * 100;
                        return (
                          <div
                            key={idx}
                            style={{ left: `${left}%`, width: `${width}%` }}
                            className="absolute h-full bg-red-500/40 border-l border-r border-red-500/60 pointer-events-none"
                            title={`Sponsor Block: ${seg.category} (${formatSeconds(seg.start)} - ${formatSeconds(seg.end)})`}
                          />
                        );
                      })}
                      {/* Chapter Tick Marks */}
                      {data.chapters && data.chapters.map((ch: any, idx: number) => {
                        const left = (ch.start_time / durationSec) * 100;
                        return (
                          <div
                            key={idx}
                            style={{ left: `${left}%` }}
                            className="absolute w-[1.5px] h-full bg-[var(--ink-dim)] opacity-50 pointer-events-none"
                            title={`Chapter: ${ch.title} (${formatSeconds(ch.start_time)})`}
                          />
                        );
                      })}
                    </div>

                    <div
                      className="range-slider-selected"
                      style={{
                        left: `${(parseTimeToSeconds(clipStart) / durationSec) * 100}%`,
                        width: `${((parseTimeToSeconds(clipEnd) - parseTimeToSeconds(clipStart)) / durationSec) * 100}%`
                      }}
                    />

                    <input
                      type="range"
                      min={0}
                      max={durationSec}
                      step={1}
                      value={parseTimeToSeconds(clipStart)}
                      onChange={(e) => {
                        const val = parseInt(e.target.value);
                        const endSec = parseTimeToSeconds(clipEnd);
                        if (val < endSec) {
                          setClipStart(formatSeconds(val));
                        }
                      }}
                      className="range-slider-input"
                    />

                    <input
                      type="range"
                      min={0}
                      max={durationSec}
                      step={1}
                      value={parseTimeToSeconds(clipEnd)}
                      onChange={(e) => {
                        const val = parseInt(e.target.value);
                        const startSec = parseTimeToSeconds(clipStart);
                        if (val > startSec) {
                          setClipEnd(formatSeconds(val));
                        }
                      }}
                      className="range-slider-input"
                    />
                  </div>

                  <div className="flex justify-between text-[10px] font-mono text-[var(--ink-faint)] px-1">
                    <span>{clipStart}</span>
                    <span>{currentLang === 'tr' ? 'Seçili Süre:' : currentLang === 'es' ? 'Duración:' : 'Selected:'} {formatSeconds(parseTimeToSeconds(clipEnd) - parseTimeToSeconds(clipStart))}</span>
                    <span>{clipEnd}</span>
                  </div>
                </div>
              )}
            </div>

            {/* Profiles Selection & Multi-Clip List Builder */}
            {clipEnabled && (
              <div className="flex flex-col gap-3 border-t border-[var(--hairline)] pt-4 animate-slide-in">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-[var(--ink)]">
                    {getTranslation(currentLang, 'lbl_multi_clip')}
                  </span>
                </div>
                <div className="flex gap-2">
                  <select
                    value={selectedProfile}
                    onChange={(e) => setSelectedProfile(e.target.value)}
                    className="w-full rounded-[var(--radius)] border border-[var(--hairline-strong)] bg-[var(--bg-recessed)] px-3 py-2 text-xs font-semibold outline-none text-[var(--ink)] cursor-pointer"
                  >
                    {profiles.map(p => (
                      <option key={p.name} value={p.name} className="bg-[var(--bg-elevated)]">
                        {p.name} ({p.ext})
                      </option>
                    ))}
                  </select>
                  <button
                    onClick={handleAddClip}
                    className="flex items-center gap-1.5 rounded-[var(--radius)] bg-[var(--bg-recessed)] border border-[var(--hairline-strong)] px-3.5 py-2 text-xs font-semibold text-[var(--ink)] hover:border-[var(--accent)] hover:text-[var(--accent)] active:scale-95 transition-all font-mono"
                  >
                    <Plus className="h-3.5 w-3.5" />
                    <span>{getTranslation(currentLang, 'btn_add')}</span>
                  </button>
                </div>

                {/* Added Clips List */}
                {addedClips.length > 0 && (
                  <div className="max-h-24 overflow-y-auto rounded-[var(--radius)] border border-[var(--hairline-strong)] bg-[var(--bg-recessed)] p-2 flex flex-col gap-1.5 scrollbar-thin">
                    {addedClips.map((c, i) => (
                      <div key={c.id} className="flex items-center justify-between rounded-[var(--radius)] bg-[var(--bg-elevated)] px-2.5 py-1 border border-[var(--hairline)]">
                        <span className="text-[10px] font-mono text-[var(--ink)]">
                          {getTranslation(currentLang, 'lbl_clip_item')} {i + 1}: {formatSeconds(c.start)} - {formatSeconds(c.end)} [{c.profile.split(' ')[0]}]
                        </span>
                        <button
                          onClick={() => handleRemoveClip(c.id)}
                          className="text-[var(--error)] hover:opacity-80 transition-opacity"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Download Mode Selector */}
          <div className="flex flex-col gap-1.5 pt-1">
            <label className="text-[10px] font-mono tracking-widest text-[var(--ink-faint)] uppercase px-1">
              {currentLang === 'tr' ? 'İndirme Modu' : currentLang === 'es' ? 'Modo de Descarga' : 'Download Mode'}
            </label>
            <select
              value={preferences?.mode || 'Video'}
              onChange={async (e) => {
                await updatePreferences({ mode: e.target.value });
              }}
              className="w-full rounded-[var(--radius)] border border-[var(--hairline-strong)] bg-[var(--bg-recessed)] px-3.5 py-2.5 text-xs font-semibold outline-none text-[var(--ink)] cursor-pointer"
            >
              <option value="Video" className="bg-[var(--bg-elevated)]">
                📹 {currentLang === 'tr' ? 'Video + Ses (Görüntü)' : currentLang === 'es' ? 'Video + Audio' : 'Video + Audio'}
              </option>
              <option value="Audio" className="bg-[var(--bg-elevated)]">
                🎵 {currentLang === 'tr' ? 'Sadece Ses (Audio)' : currentLang === 'es' ? 'Solo Audio' : 'Audio Only'}
              </option>
            </select>
          </div>

          {/* Action Trigger Buttons */}
          <div className="flex gap-3">
            <button
              onClick={handleAddToQueue}
              className="flex-1 rounded-[var(--radius)] bg-[var(--accent)] py-3 text-xs font-bold uppercase tracking-widest text-[var(--accent-ink)] hover:bg-[var(--accent-deep)] active:scale-98 transition-all font-mono"
            >
              {addedClips.length > 0
                ? getTranslation(currentLang, 'btn_add_to_queue_clips', { count: addedClips.length })
                : getTranslation(currentLang, 'btn_add_to_queue')}
            </button>
          </div>
        </div>
      </div>

      {/* Chapters bar */}
      {data.chapters && data.chapters.length > 0 && (
        <div className="mt-6 border-t border-[var(--hairline)] pt-5 flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <Milestone className="h-4 w-4 text-[var(--accent)]" />
            <span className="text-xs font-semibold tracking-widest text-[var(--ink-dim)] uppercase font-mono">
              {getTranslation(currentLang, 'lbl_chapters')}
            </span>
          </div>
          <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-thin">
            {data.chapters.map((ch: any, idx: number) => (
              <button
                key={idx}
                onClick={() => handleChapterClick(ch.start_time, ch.end_time)}
                className="flex flex-col gap-0.5 items-start justify-center rounded-[var(--radius)] border border-[var(--hairline-strong)] bg-[var(--bg-recessed)] px-4 py-2 text-left hover:border-[var(--accent)] hover:text-[var(--accent)] active:scale-95 transition-all shrink-0"
              >
                <span className="line-clamp-1 max-w-[160px] text-xs font-semibold text-[var(--ink)]">
                  {ch.title}
                </span>
                <span className="text-[10px] font-mono text-[var(--ink-faint)]">
                  {formatSeconds(Math.floor(ch.start_time))} - {formatSeconds(Math.floor(ch.end_time))}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
