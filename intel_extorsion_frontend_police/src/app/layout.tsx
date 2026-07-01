import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import I18nClientLayout from './I18nClientLayout';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Consola de Inteligencia DIVINCRI - Escudo Ciudadano',
  description:
    'Sistema policial de inteligencia para el análisis, correlación, clustering y sellado de evidencias contra la extorsión.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body className={inter.className}>
        <I18nClientLayout>{children}</I18nClientLayout>
      </body>
    </html>
  );
}
