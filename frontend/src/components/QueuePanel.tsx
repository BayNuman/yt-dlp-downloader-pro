import React, { useState, useEffect } from 'react';
import { List, History, Play, Pause, Trash2, ExternalLink, FolderOpen, Calendar, HardDrive } from 'lucide-react';
import { useAppStore } from '../store/appStore';
import { getTranslation } from '../i18n/translations';

export const QueuePanel: React.FC = () => {
  const {
    queue,
    fetchQueue,
    removeTask,
    pauseTask,
    resumeTask,
    history,
    fetchHistory,
    deleteHistoryItem,
    clearHistory,
    preferences,
    addToast
  } = useAppStore();

  const [activeTab, setActiveTab] = useState<'queue' | 'history'>('queue');
  const currentLang = preferences?.current_lang || 'en';

  // Load queue and history on mount and keep synced
  useEffect(() => {
    fetchQueue();
    fetchHistory();
    const interval = setInterval(() => {
      if (activeTab === 'queue') {
        fetchQueue();
      }
    }, 4000); // Polling fallback in case WS disconnects
    return () => clearInterval(interval);
  }, [fetchQueue, fetchHistory, activeTab]);

  const handleOpenFolder = async (filePath: string) => {
    const tauri = (window as any).__TAURI__;
    if (tauri && tauri.shell) {
      try {
        const { open } = (window as any).__TAURI__.shell || {};
        if (open) {
          const dirPath = filePath.substring(0, filePath.lastIndexOf('\\')) || filePath.substring(0, filePath.lastIndexOf('/'));
          await open(dirPath);
        }
      } catch (err) {
        addToast(getTranslation(currentLang, 'err_open_folder'), 'error');
      }
    } else {
      addToast(getTranslation(currentLang, 'msg_file_location') + filePath, 'info');
    }
  };

  const formatBytes = (bytes: number): string => {
    if (!bytes || bytes <= 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (timestamp: number): string => {
    if (!timestamp) return '';
    const date = new Date(timestamp * 1000);
    return date.toLocaleDateString(currentLang === 'tr' ? 'tr-TR' : currentLang === 'es' ? 'es-ES' : 'en-US', {
      hour: '2-digit',
      minute: '2-digit',
      day: 'numeric',
      month: 'short'
    });
  };

  return (
    <div className="w-full border-b border-[var(--hairline)] p-6 transition-all duration-300">
      <div className="flex flex-col gap-6">
        
        {/* Navigation & Controls */}
        <div className="flex items-center justify-between border-b border-[var(--hairline)] pb-3">
          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab('queue')}
              className={`flex items-center gap-1.5 border-b-2 px-4 py-2.5 text-xs font-semibold transition-all font-mono uppercase tracking-wider ${
                activeTab === 'queue'
                  ? 'border-[var(--accent)] text-[var(--accent)]'
                  : 'border-transparent text-[var(--ink-faint)] hover:text-[var(--ink)]'
              }`}
            >
              <List className="h-3.5 w-3.5" />
              <span>{getTranslation(currentLang, 'lbl_download_list')} ({queue.length})</span>
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`flex items-center gap-1.5 border-b-2 px-4 py-2.5 text-xs font-semibold transition-all font-mono uppercase tracking-wider ${
                activeTab === 'history'
                  ? 'border-[var(--accent)] text-[var(--accent)]'
                  : 'border-transparent text-[var(--ink-faint)] hover:text-[var(--ink)]'
              }`}
            >
              <History className="h-3.5 w-3.5" />
              <span>{getTranslation(currentLang, 'lbl_history')} ({history.length})</span>
            </button>
          </div>

          {/* Clear history button */}
          {activeTab === 'history' && history.length > 0 && (
            <button
              onClick={clearHistory}
              className="flex items-center gap-1 text-[11px] font-semibold text-[var(--error)] hover:opacity-80 transition-colors font-mono"
            >
              <Trash2 className="h-3.5 w-3.5" />
              <span>{getTranslation(currentLang, 'btn_clear_all')}</span>
            </button>
          )}
        </div>

        {/* Tab content container */}
        <div className="min-h-[220px] max-h-[360px] overflow-y-auto pr-1 scrollbar-thin">
          
          {/* Active Queue List */}
          {activeTab === 'queue' && (
            <div className="flex flex-col gap-3">
              {queue.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-[var(--ink-faint)]">
                  <List className="h-12 w-12 stroke-[1.2] mb-2" />
                  <span className="text-xs font-semibold">{getTranslation(currentLang, 'lbl_queue_empty')}</span>
                </div>
              ) : (
                queue.map((task) => (
                  <div
                    key={task.id}
                    className="group relative flex flex-col gap-3.5 rounded-[var(--radius)] border border-[var(--hairline-strong)] bg-[var(--bg-recessed)] p-4 transition-all duration-300"
                  >
                    {/* Task Title & Status Row */}
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex flex-col gap-0.5">
                        <span className="line-clamp-1 text-xs font-semibold text-[var(--ink)]">
                          {task.title}
                        </span>
                        <a
                          href={task.url}
                          target="_blank"
                          rel="noreferrer"
                          className="flex items-center gap-1 text-[10px] font-mono text-[var(--ink-faint)] hover:text-[var(--accent)]"
                        >
                          <span className="truncate max-w-[240px]">{task.url}</span>
                          <ExternalLink className="h-2.5 w-2.5" />
                        </a>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`status-chip ${(task.status_code || '').toLowerCase()}`}>
                          {task.status}
                        </span>
                      </div>
                    </div>

                    {/* exposed film frames progress bar */}
                    {task.percent > 0 && (
                      <div className="flex flex-col gap-1.5 animate-slide-in">
                        <div className="reel-progress">
                          {Array.from({ length: 40 }, (_, i) => (
                            <i key={i} className={i < Math.round(task.percent / 2.5) ? 'on' : ''} />
                          ))}
                        </div>
                        <div className="flex items-center justify-between text-[10px] font-bold text-[var(--ink-dim)]">
                          <span>{getTranslation(currentLang, 'lbl_percent_done', { percent: task.percent })}</span>
                          {task.speed && (
                            <span className="font-mono">
                              {getTranslation(currentLang, 'lbl_speed_eta', { speed: task.speed, eta: task.eta })}
                            </span>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Inline Task Control Actions */}
                    <div className="flex items-center justify-between border-t border-[var(--hairline)] pt-2 text-[10px] font-semibold text-[var(--ink-faint)]">
                      <span className="font-mono">Format: {task.preset}</span>
                      <div className="flex items-center gap-2.5">
                        {(task.status_code || '').toLowerCase() === 'downloading' && (
                          <button
                            onClick={() => pauseTask(task.id)}
                            className="text-[var(--warning)] hover:opacity-85 transition-opacity"
                            title={getTranslation(currentLang, 'btn_pause')}
                          >
                            <Pause className="h-4 w-4" />
                          </button>
                        )}
                        {(task.status_code || '').toLowerCase() === 'paused' && (
                          <button
                            onClick={() => resumeTask(task.id)}
                            className="text-[var(--accent)] hover:opacity-85 transition-opacity"
                            title={getTranslation(currentLang, 'btn_resume')}
                          >
                            <Play className="h-4 w-4" />
                          </button>
                        )}
                        <button
                          onClick={() => removeTask(task.id)}
                          className="text-[var(--error)] hover:opacity-85 transition-opacity"
                          title={getTranslation(currentLang, 'btn_remove')}
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Download History list */}
          {activeTab === 'history' && (
            <div className="flex flex-col gap-2">
              {history.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-[var(--ink-faint)]">
                  <History className="h-12 w-12 stroke-[1.2] mb-2" />
                  <span className="text-xs font-semibold">{getTranslation(currentLang, 'lbl_history_empty')}</span>
                </div>
              ) : (
                history.map((record) => (
                  <div
                    key={record.id}
                    className="flex items-center justify-between gap-4 rounded-[var(--radius)] border border-[var(--hairline-strong)] bg-[var(--bg-recessed)] px-4 py-3 transition-all duration-200"
                  >
                    <div className="flex flex-col gap-0.5">
                      <span className="line-clamp-1 text-xs font-semibold text-[var(--ink)]">
                        {record.title}
                      </span>
                      <div className="flex items-center gap-3 text-[10px] font-mono text-[var(--ink-faint)]">
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {formatDate(record.downloaded_at)}
                        </span>
                        <span className="flex items-center gap-1">
                          <HardDrive className="h-3 w-3" />
                          {formatBytes(record.file_size_bytes)}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      {record.file_path && (
                        <button
                          onClick={() => handleOpenFolder(record.file_path)}
                          className="rounded-md p-1.5 text-[var(--ink-faint)] hover:bg-[var(--bg-elevated)] hover:text-[var(--ink)] transition-colors"
                          title={getTranslation(currentLang, 'btn_show_folder')}
                        >
                          <FolderOpen className="h-4 w-4" />
                        </button>
                      )}
                      <button
                        onClick={() => deleteHistoryItem(record.id)}
                        className="rounded-md p-1.5 text-[var(--error)] hover:bg-[var(--bg-elevated)] transition-colors"
                        title={getTranslation(currentLang, 'btn_delete_history')}
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

        </div>

      </div>
    </div>
  );
};
