import React, { useEffect, useState, useRef } from 'react';
import { Terminal, Play, Square, RefreshCcw } from 'lucide-react';
import { useAppStore } from '../store/appStore';
import { getTranslation } from '../i18n/translations';

export const ProgressPanel: React.FC = () => {
  const {
    queue,
    logs,
    clearLogs,
    startDownloads,
    cancelDownloads,
    preferences
  } = useAppStore();

  const terminalEndRef = useRef<HTMLDivElement | null>(null);

  // Speed history local state for the live sparkline graph
  const [speedHistory, setSpeedHistory] = useState<number[]>(Array(60).fill(0));

  const currentLang = preferences?.current_lang || 'en';

  // Determine active downloading tasks and calculate aggregate download speed
  const activeTasks = queue.filter(
    (t) => (t.status_code || '').toLowerCase() === 'downloading'
  );
  
  const isDownloading = activeTasks.length > 0;

  // Aggregate speed string
  const currentSpeedText = isDownloading ? activeTasks[0].speed : '';
  const currentEtaText = isDownloading ? activeTasks[0].eta : '';

  // Parser helper to convert raw speed string to MB/s numeric values
  function parseSpeedToMbps(s: string): number {
    if (!s) return 0;
    const cleaned = s.trim().toLowerCase();
    const match = /([0-9.]+)\s*(gib|mib|kib|gb|mb|kb|b)\/s/.exec(cleaned);
    if (!match) return 0;
    const val = parseFloat(match[1]);
    const unit = match[2];
    if (unit === 'gib' || unit === 'gb') return val * 1024;
    if (unit === 'mib' || unit === 'mb') return val;
    if (unit === 'kib' || unit === 'kb') return val / 1024;
    return val / (1024 * 1024);
  }

  // Poll current speed every second to record history
  useEffect(() => {
    const timer = setInterval(() => {
      let speedValue = 0;
      if (isDownloading && activeTasks[0]?.speed) {
        speedValue = parseSpeedToMbps(activeTasks[0].speed);
      }
      
      setSpeedHistory((prev) => {
        const next = [...prev.slice(1), speedValue];
        return next;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [isDownloading, activeTasks]);

  // Auto-scroll terminal console to bottom on new log arrival
  useEffect(() => {
    if (terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  // Render SVG points for sparkline
  const maxSpeed = Math.max(...speedHistory, 5); // Minimum y-scale boundary
  const svgWidth = 500;
  const svgHeight = 50;
  
  const points = speedHistory
    .map((val, idx) => {
      const x = (idx / (speedHistory.length - 1)) * svgWidth;
      const safeMaxSpeed = isNaN(maxSpeed) || maxSpeed <= 0 ? 5 : maxSpeed;
      const safeVal = isNaN(val) ? 0 : val;
      const y = svgHeight - (safeVal / safeMaxSpeed) * (svgHeight - 6);
      return `${x},${isNaN(y) ? svgHeight : y}`;
    })
    .join(' ');

  // Gradient area points
  const areaPoints = `0,${svgHeight} ${points} ${svgWidth},${svgHeight}`;

  return (
    <div className="w-full border-b border-[var(--hairline)] p-6 transition-all duration-300">
      <div className="flex flex-col gap-5">
        
        {/* Header Actions */}
        <div className="flex items-center justify-between border-b border-[var(--hairline)] pb-3">
          <div className="flex items-center gap-2">
            <span className="panel-idx">04</span>
            <h2 className="text-xs font-semibold tracking-widest text-[var(--ink-dim)] uppercase font-mono">
              {getTranslation(currentLang, 'lbl_progress_title')}
            </h2>
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={startDownloads}
              className="flex items-center gap-1.5 rounded-[var(--radius)] bg-[var(--accent)] px-3.5 py-1.5 text-xs font-semibold text-[var(--accent-ink)] hover:bg-[var(--accent-deep)] active:scale-95 transition-all font-mono"
            >
              <Play className="h-3 w-3" />
              <span>{getTranslation(currentLang, 'btn_start_dl')}</span>
            </button>
            <button
              onClick={cancelDownloads}
              className="flex items-center gap-1.5 rounded-[var(--radius)] border border-[var(--hairline-strong)] bg-[var(--bg-recessed)] px-3.5 py-1.5 text-xs font-semibold text-[var(--ink)] hover:border-[var(--accent)] hover:text-[var(--accent)] active:scale-95 transition-all font-mono"
            >
              <Square className="h-3 w-3" />
              <span>{getTranslation(currentLang, 'btn_stop_dl')}</span>
            </button>
          </div>
        </div>

        {/* Speed Stats & Sparkline Graph */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 items-center">
          
          {/* Numbers */}
          <div className="flex flex-col gap-1">
            <span className="text-[9px] font-mono tracking-widest text-[var(--ink-faint)] uppercase">
              {getTranslation(currentLang, 'lbl_total_speed')}
            </span>
            <div className="flex items-baseline gap-1.5 text-[var(--ink)] font-mono font-semibold">
              <span className="text-xl">
                {currentSpeedText || '0.00 MB/s'}
              </span>
            </div>
            {currentEtaText && (
              <span className="text-[10px] font-mono text-[var(--ink-dim)]">
                {getTranslation(currentLang, 'lbl_eta_remaining', { eta: currentEtaText })}
              </span>
            )}
          </div>

          {/* Sparkline Graphic Column */}
          <div className="sm:col-span-2 scope-box p-2">
            <div className="flex justify-between items-baseline mb-1">
              <span className="text-[9px] font-mono text-[var(--ink-faint)] uppercase">
                {getTranslation(currentLang, 'lbl_parallel_threads', { count: activeTasks.length || 1 })}
              </span>
              <span className="text-[9px] font-mono text-[var(--ink-faint)] uppercase">
                {getTranslation(currentLang, 'lbl_speed_history')}
              </span>
            </div>
            <svg
              viewBox={`0 0 ${svgWidth} ${svgHeight}`}
              className="w-full h-11 overflow-visible"
              preserveAspectRatio="none"
            >
              <defs>
                <linearGradient id="sparklineAreaGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.25" />
                  <stop offset="100%" stopColor="var(--accent)" stopOpacity="0.0" />
                </linearGradient>
              </defs>
              
              {/* Speed history area */}
              <polygon
                points={areaPoints}
                fill="url(#sparklineAreaGrad)"
                className="transition-all duration-1000"
              />
              
              {/* Speed history stroke line */}
              <polyline
                fill="none"
                stroke="var(--accent)"
                strokeWidth="1.8"
                points={points}
                className="transition-all duration-1000"
              />
            </svg>
          </div>

        </div>

        {/* Terminal Logs console */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between text-xs font-semibold text-[var(--ink-dim)]">
            <div className="flex items-center gap-1.5">
              <Terminal className="h-4 w-4 text-[var(--accent)]" />
              <span>{getTranslation(currentLang, 'lbl_system_logs')}</span>
            </div>
            {logs.length > 0 && (
              <button
                onClick={clearLogs}
                className="flex items-center gap-1 hover:text-[var(--ink)] font-mono text-[10px]"
              >
                <RefreshCcw className="h-3 w-3" />
                <span>{getTranslation(currentLang, 'btn_clear_console')}</span>
              </button>
            )}
          </div>
          
          <div className="console scrollbar-thin">
            {logs.length === 0 ? (
              <span className="text-[var(--ink-faint)] select-none">
                {getTranslation(currentLang, 'lbl_logs_waiting')}
              </span>
            ) : (
              logs.map((log, idx) => {
                const logStr = typeof log === 'string' ? log : (log ? String(log) : '');
                const isOk = logStr.toLowerCase().includes('merger') || logStr.toLowerCase().includes('birleştiriliyor') || logStr.toLowerCase().includes('deleting') || logStr.toLowerCase().includes('success');
                const isWarn = logStr.toLowerCase().includes('warn') || logStr.toLowerCase().includes('warning') || logStr.toLowerCase().includes('hata') || logStr.toLowerCase().includes('error');
                
                return (
                  <div key={idx} className={`ln ${isOk ? 'ok' : isWarn ? 'warn' : ''}`}>
                    <span className="msg">{logStr}</span>
                  </div>
                );
              })
            )}
            <div ref={terminalEndRef} />
          </div>
        </div>

      </div>
    </div>
  );
};
