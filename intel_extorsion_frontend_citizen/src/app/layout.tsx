import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import I18nClientLayout from './I18nClientLayout';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Portal Ciudadano - Escudo Ciudadano contra la Extorsión',
  description:
    'Portal ciudadano para el registro seguro de denuncias de extorsión, preservación de evidencias y consulta de estado.',
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
