import { create } from 'zustand';
import { apiClient } from '../api/client';
import type { WsEvent } from '../hooks/useWebSocket';

export interface DownloadTask {
  id: string;
  url: string;
  title: string;
  duration: string;
  preset: string;
  status: string;
  status_code: string;
  mode: string;
  video_profile: string;
  audio_quality: string;
  clip_enabled: boolean;
  clip_start: string;
  clip_end: string;
  percent: number;
  speed: string;
  eta: string;
  size: string;
  file_path: string;
}

export interface AppPreferences {
  output_dir: string;
  current_lang: string;
  current_theme: string;
  active_profile: string;
  mode: string;
  custom_settings: Record<string, any>;
  spotify_client_id: string;
  spotify_client_secret: string;
  sponsorblock_enabled: boolean;
  browser_cookies: string;
  speed_limit: string | null;
  metadata_flag: boolean;
  thumbnail_flag: boolean;
  subtitle_flag: boolean;
  auto_subtitle_flag: boolean;
  restrict_filenames: boolean;
  keep_video_flag: boolean;
  embed_chapters: boolean;
  concurrent_fragments: string;
  output_template: string;
  extra_args: string;
  folder_org: string;
  compact_mode: boolean;
  max_workers: number;
}

export interface ExportProfile {
  name: string;
  ext: string;
  max_duration: number | null;
}

export interface SystemStatus {
  app_version: string;
  yt_dlp_version: string;
  ffmpeg_path: string;
  os_platform: string;
  os_release: string;
  disk_free_bytes: number;
  disk_total_bytes: number;
}

export interface MetadataState {
  loading: boolean;
  data: any | null;
  error: string | null;
}

export interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  text: string;
}

interface AppState {
  preferences: AppPreferences | null;
  profiles: ExportProfile[];
  presets: Record<string, any>;
  queue: DownloadTask[];
  history: any[];
  systemStatus: SystemStatus | null;
  metadataState: MetadataState;
  toasts: ToastMessage[];
  logs: string[];

  // Toast actions
  addToast: (text: string, type?: ToastMessage['type']) => void;
  removeToast: (id: string) => void;
  clearLogs: () => void;

  // Preferences
  fetchPreferences: () => Promise<void>;
  updatePreferences: (patch: Partial<AppPreferences>) => Promise<void>;

  // Profiles & Presets
  fetchProfiles: () => Promise<void>;
  fetchPresets: () => Promise<void>;
  savePreset: (name: string, settings: Record<string, any>) => Promise<void>;
  deletePreset: (name: string) => Promise<void>;

  // Queue
  fetchQueue: () => Promise<void>;
  addTask: (url: string, settings?: Record<string, any>, clips?: any[]) => Promise<any>;
  removeTask: (taskId: string) => Promise<void>;
  pauseTask: (taskId: string) => Promise<void>;
  resumeTask: (taskId: string) => Promise<void>;

  // Downloads Control
  startDownloads: () => Promise<void>;
  cancelDownloads: () => Promise<void>;

  // History
  fetchHistory: () => Promise<void>;
  deleteHistoryItem: (recordId: string) => Promise<void>;
  clearHistory: () => Promise<void>;

  // Metadata
  fetchMetadata: (url: string, browserCookies?: string) => Promise<void>;
  clearMetadata: () => void;

  // System Status
  fetchSystemStatus: () => Promise<void>;

  // WebSocket event handler
  handleWsEvent: (event: WsEvent) => void;
}

export const useAppStore = create<AppState>((set, get) => ({
  preferences: null,
  profiles: [],
  presets: {},
  queue: [],
  history: [],
  systemStatus: null,
  metadataState: { loading: false, data: null, error: null },
  toasts: [],
  logs: [],

  clearLogs: () => set({ logs: [] }),

  addToast: (text, type = 'info') => {
    const id = Math.random().toString(36).substring(2, 9);
    set((state) => ({
      toasts: [...state.toasts, { id, type, text }],
    }));
    setTimeout(() => get().removeToast(id), 4000);
  },

  removeToast: (id) => {
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    }));
  },

  fetchPreferences: async () => {
    try {
      const res = await apiClient.get('/config/preferences');
      set({ preferences: res.data });
    } catch (err) {
      get().addToast('Ayarlar yüklenemedi.', 'error');
    }
  },

  updatePreferences: async (patch) => {
    try {
      const res = await apiClient.patch('/config/preferences', patch);
      set({ preferences: res.data.preferences });
      get().addToast('Ayarlar kaydedildi.', 'success');
    } catch (err) {
      get().addToast('Ayarlar güncellenemedi.', 'error');
    }
  },

  fetchProfiles: async () => {
    try {
      const res = await apiClient.get('/config/profiles');
      set({ profiles: res.data });
    } catch (err) {
      console.error('Profiller yüklenemedi:', err);
    }
  },

  fetchPresets: async () => {
    try {
      const res = await apiClient.get('/config/presets');
      set({ presets: res.data });
    } catch (err) {
      console.error('Şablonlar yüklenemedi:', err);
    }
  },

  savePreset: async (name, settings) => {
    try {
      await apiClient.post(`/config/presets/${encodeURIComponent(name)}`, settings);
      get().addToast(`'${name}' şablonu kaydedildi.`, 'success');
      await get().fetchPresets();
    } catch (err) {
      get().addToast('Şablon kaydedilemedi.', 'error');
    }
  },

  deletePreset: async (name) => {
    try {
      await apiClient.delete(`/config/presets/${encodeURIComponent(name)}`);
      get().addToast(`'${name}' şablonu silindi.`, 'success');
      await get().fetchPresets();
    } catch (err) {
      get().addToast('Şablon silinemedi.', 'error');
    }
  },

  fetchQueue: async () => {
    try {
      const res = await apiClient.get('/queue');
      // map backend payload to frontend types
      const mapped: DownloadTask[] = res.data.map((t: any) => ({
        id: t.task_id,
        url: t.url,
        title: t.title,
        duration: t.duration,
        preset: t.preset,
        status: t.status,
        status_code: t.status_code,
        mode: t.mode,
        video_profile: t.video_profile || '',
        audio_quality: t.audio_quality || '',
        clip_enabled: t.clip_enabled,
        clip_start: t.clip_start,
        clip_end: t.clip_end,
        percent: t.percent,
        speed: t.speed,
        eta: t.eta,
        size: t.size,
        file_path: t.file_path,
      }));
      set({ queue: mapped });
    } catch (err) {
      console.error('İndirme kuyruğu alınamadı:', err);
    }
  },

  addTask: async (url, settings, clips) => {
    try {
      const res = await apiClient.post('/queue', {
        url,
        settings,
        clips,
      });
      if (res.data.success) {
        get().addToast(res.data.detail, 'success');
        await get().fetchQueue();
      } else {
        get().addToast(res.data.detail, 'warning');
      }
      return res.data;
    } catch (err: any) {
      const detail = err.response?.data?.detail || 'Görev kuyruğa eklenemedi.';
      get().addToast(detail, 'error');
      throw err;
    }
  },

  removeTask: async (taskId) => {
    try {
      await apiClient.delete(`/queue/${taskId}`);
      get().addToast('Görev kuyruktan silindi.', 'success');
      await get().fetchQueue();
    } catch (err) {
      get().addToast('Görev silinemedi.', 'error');
    }
  },

  pauseTask: async (taskId) => {
    try {
      await apiClient.post(`/queue/${taskId}/pause`);
      get().addToast('İndirme duraklatıldı.', 'info');
      await get().fetchQueue();
    } catch (err) {
      get().addToast('İndirme duraklatılamadı.', 'error');
    }
  },

  resumeTask: async (taskId) => {
    try {
      await apiClient.post(`/queue/${taskId}/resume`);
      get().addToast('İndirme devam ettiriliyor.', 'info');
      await get().fetchQueue();
    } catch (err) {
      get().addToast('İndirme devam ettirilemedi.', 'error');
    }
  },

  startDownloads: async () => {
    try {
      const res = await apiClient.post('/download/start');
      get().addToast(res.data.detail, 'success');
      await get().fetchQueue();
    } catch (err: any) {
      const detail = err.response?.data?.detail || 'İndirme işlemi başlatılamadı.';
      get().addToast(detail, 'error');
    }
  },

  cancelDownloads: async () => {
    try {
      const res = await apiClient.post('/download/cancel');
      get().addToast(res.data.detail, 'info');
      await get().fetchQueue();
    } catch (err) {
      get().addToast('İptal işlemi başarısız oldu.', 'error');
    }
  },

  fetchHistory: async () => {
    try {
      const res = await apiClient.get('/history');
      set({ history: res.data });
    } catch (err) {
      console.error('İndirme geçmişi yüklenemedi:', err);
    }
  },

  deleteHistoryItem: async (recordId) => {
    try {
      await apiClient.delete(`/history/${recordId}`);
      get().addToast('Geçmiş kaydı silindi.', 'success');
      await get().fetchHistory();
    } catch (err) {
      get().addToast('Kayıt silinemedi.', 'error');
    }
  },

  clearHistory: async () => {
    try {
      await apiClient.post('/history/clear');
      get().addToast('Tüm geçmiş temizlendi.', 'success');
      await get().fetchHistory();
    } catch (err) {
      get().addToast('Geçmiş temizlenemedi.', 'error');
    }
  },

  fetchMetadata: async (url, browserCookies = 'disabled') => {
    set({ metadataState: { loading: true, data: null, error: null } });
    try {
      const res = await apiClient.post('/metadata', {
        url,
        browser_cookies: browserCookies,
      });
      set({ metadataState: { loading: false, data: res.data, error: null } });
    } catch (err: any) {
      const detail = err.response?.data?.detail || 'Video bilgileri çekilemedi.';
      set({ metadataState: { loading: false, data: null, error: detail } });
      get().addToast(detail, 'error');
    }
  },

  clearMetadata: () => {
    set({ metadataState: { loading: false, data: null, error: null } });
  },

  fetchSystemStatus: async () => {
    try {
      const res = await apiClient.get('/config/system/status');
      set({ systemStatus: res.data });
    } catch (err) {
      console.error('Sistem durumu alınamadı:', err);
    }
  },

  handleWsEvent: (event) => {
    const { type, task_id, payload } = event;
    
    // 1. Core global event categories
    if (type === 'task_added') {
      const t = payload || event.task;
      if (t) {
        set((state) => {
          const exists = state.queue.some((item) => item.id === t.task_id);
          if (exists) return state;
          return {
            queue: [
              ...state.queue,
              {
                id: t.task_id,
                url: t.url,
                title: t.title,
                duration: t.duration,
                preset: t.preset,
                status: t.status,
                status_code: t.status_code,
                mode: t.mode,
                video_profile: t.video_profile || '',
                audio_quality: t.audio_quality || '',
                clip_enabled: t.clip_enabled,
                clip_start: t.clip_start,
                clip_end: t.clip_end,
                percent: t.percent || 0,
                speed: t.speed || '',
                eta: t.eta || '',
                size: t.size || '',
                file_path: t.file_path || '',
              },
            ],
          };
        });
      }
      return;
    }

    if (type === 'task_removed') {
      const id = task_id || payload;
      if (id) {
        set((state) => ({
          queue: state.queue.filter((t) => t.id !== id),
        }));
      }
      return;
    }

    if (type === 'queue_done') {
      get().addToast('Tüm indirmeler tamamlandı!', 'success');
      get().fetchHistory();
      get().fetchQueue();
      return;
    }

    if (type === 'toast_success') {
      let msg = 'Başarılı!';
      if (typeof payload === 'string') {
        msg = payload;
      } else if (payload && typeof payload === 'object') {
        if (payload.title) {
          msg = `Başarıyla indirildi: ${payload.title}`;
        } else if (payload.detail) {
          msg = payload.detail;
        } else {
          msg = JSON.stringify(payload);
        }
      }
      get().addToast(msg, 'success');
      return;
    }
    if (type === 'toast_error') {
      let msg = 'Bir hata oluştu.';
      if (typeof payload === 'string') {
        msg = payload;
      } else if (payload && typeof payload === 'object') {
        if (payload.title && payload.code !== undefined) {
          msg = `İndirme Hatası (Kod: ${payload.code}) - ${payload.title}`;
        } else if (payload.detail) {
          msg = payload.detail;
        } else {
          msg = JSON.stringify(payload);
        }
      }
      get().addToast(msg, 'error');
      return;
    }
    if (type === 'toast_cancel') {
      let msg = 'İndirme iptal edildi.';
      if (typeof payload === 'string') {
        msg = payload;
      } else if (payload && typeof payload === 'object') {
        if (payload.title) {
          msg = `İndirme iptal edildi: ${payload.title}`;
        } else {
          msg = JSON.stringify(payload);
        }
      }
      get().addToast(msg, 'info');
      return;
    }

    if (type === 'log') {
      const logStr = typeof payload === 'string' ? payload : (payload ? JSON.stringify(payload) : '');
      set((state) => {
        const newLogs = [...state.logs, logStr];
        if (newLogs.length > 100) {
          newLogs.shift();
        }
        return { logs: newLogs };
      });
      return;
    }

    // 2. Task-specific progress/state feeds
    if (task_id) {
      set((state) => ({
        queue: state.queue.map((task) => {
          if (task.id !== task_id) return task;

          switch (type) {
            case 'percent_complete':
              return { ...task, percent: typeof payload === 'number' ? payload : parseFloat(payload) };
            case 'stats':
              return {
                ...task,
                speed: payload?.speed || task.speed,
                eta: payload?.eta || task.eta,
                size: payload?.size || task.size,
              };
            case 'status':
              return { ...task, status: payload || '', status_code: payload || '' };
            default:
              return task;
          }
        }),
      }));
    }
  },
}));
