'use client';

import { ReactNode, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import I18nProvider from '@/lib/i18n/I18nProvider';
import ToastProvider from '@/components/ToastProvider';

function LangUpdater({ children }: { children: ReactNode }) {
  const { i18n } = useTranslation();

  useEffect(() => {
    const lang = i18n.language?.startsWith('es') ? 'es' : 'en';
    document.documentElement.lang = lang;
  }, [i18n.language]);

  return <>{children}</>;
}

export default function I18nClientLayout({ children }: { children: ReactNode }) {
  return (
    <I18nProvider>
      <LangUpdater>
        <ToastProvider>{children}</ToastProvider>
      </LangUpdater>
    </I18nProvider>
  );
}
