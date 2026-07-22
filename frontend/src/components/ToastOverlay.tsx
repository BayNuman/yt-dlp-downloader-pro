import React from 'react';
import { X, CheckCircle, AlertTriangle, AlertCircle, Info } from 'lucide-react';
import { useAppStore } from '../store/appStore';
import type { ToastMessage } from '../store/appStore';

export const ToastOverlay: React.FC = () => {
  const { toasts, removeToast } = useAppStore();

  if (toasts.length === 0) return null;

  const getIcon = (type: ToastMessage['type']) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="h-4.5 w-4.5 text-[var(--success)]" />;
      case 'error':
        return <AlertCircle className="h-4.5 w-4.5 text-[var(--error)]" />;
      case 'warning':
        return <AlertTriangle className="h-4.5 w-4.5 text-[var(--warning)]" />;
      case 'info':
      default:
        return <Info className="h-4.5 w-4.5 text-[var(--accent)]" />;
    }
  };

  const getToastStyle = (type: ToastMessage['type']): React.CSSProperties => {
    const baseStyle: React.CSSProperties = {
      borderLeftWidth: '3px',
      pointerEvents: 'auto'
    };
    switch (type) {
      case 'success':
        return { ...baseStyle, borderLeftColor: 'var(--success)' };
      case 'error':
        return { ...baseStyle, borderLeftColor: 'var(--error)' };
      case 'warning':
        return { ...baseStyle, borderLeftColor: 'var(--warning)' };
      case 'info':
      default:
        return { ...baseStyle, borderLeftColor: 'var(--accent)' };
    }
  };

  return (
    <div className="fixed top-6 right-6 z-[9999] flex flex-col gap-3 pointer-events-none">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className="flex items-start gap-3 w-80 rounded-[var(--radius)] border border-[var(--hairline-strong)] bg-[var(--bg-elevated)] p-4 shadow-[var(--shadow)] animate-slide-in transition-all duration-300 text-[var(--ink)]"
          style={getToastStyle(toast.type)}
        >
          {/* Icon */}
          <div className="shrink-0 mt-0.5">{getIcon(toast.type)}</div>
          
          {/* Message */}
          <div className="flex-1 text-xs font-semibold leading-relaxed">
            {toast.text}
          </div>
          
          {/* Dismiss button */}
          <button
            onClick={() => removeToast(toast.id)}
            className="shrink-0 rounded-[var(--radius)] p-0.5 text-[var(--ink-faint)] hover:bg-[var(--hairline)] hover:text-[var(--ink)] transition-colors"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      ))}
    </div>
  );
};
