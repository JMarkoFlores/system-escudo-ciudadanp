'use client';

import { useTranslation } from 'react-i18next';
import { Languages } from 'lucide-react';

export default function LanguageSwitcher({ compact = false }: { compact?: boolean }) {
  const { i18n } = useTranslation();
  const current = i18n.language?.startsWith('es') ? 'es' : 'en';

  const toggle = () => {
    const next = current === 'es' ? 'en' : 'es';
    i18n.changeLanguage(next);
    if (typeof document !== 'undefined') {
      document.documentElement.lang = next;
    }
  };

  if (compact) {
    return (
      <button
        onClick={toggle}
        className="flex items-center space-x-1 text-xs font-bold px-2.5 py-1.5 rounded-lg border border-slate-700/50 text-slate-400 hover:text-white hover:border-slate-500 transition bg-slate-800/30"
        title={current === 'es' ? 'Switch to English' : 'Cambiar a Español'}
      >
        <Languages size={14} />
        <span>{current === 'es' ? 'EN' : 'ES'}</span>
      </button>
    );
  }

  return (
    <button
      onClick={toggle}
      className="flex items-center space-x-1.5 text-xs font-bold px-3 py-1.5 rounded-lg border border-slate-700 text-slate-300 hover:text-white hover:border-slate-500 transition"
    >
      <Languages size={14} />
      <span>{current === 'es' ? 'English' : 'Español'}</span>
    </button>
  );
}
