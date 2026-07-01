'use client';

import { ReactNode, useEffect, useState } from 'react';
import i18n from './i18n';

export default function I18nProvider({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const handleLoaded = () => setReady(true);
    if (i18n.isInitialized) {
      setReady(true);
    } else {
      i18n.on('initialized', handleLoaded);
    }
    return () => {
      i18n.off('initialized', handleLoaded);
    };
  }, []);

  if (!ready) return null;

  return <>{children}</>;
}
