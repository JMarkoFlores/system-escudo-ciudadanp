'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useTranslation } from 'react-i18next';
import { useWalletStore } from '@/stores/walletStore';
import { useAppStore } from '@/stores/appStore';
import LanguageSwitcher from '@/components/LanguageSwitcher';
import {
  LayoutDashboard,
  ShieldAlert,
  Network,
  BarChart3,
  Menu,
  X,
  Wallet,
  LogOut,
  UserCircle,
  ChevronRight,
  Home,
  MessageSquare,
  Users,
} from 'lucide-react';
import { cn } from '@/lib/utils/cn';

const getNavItems = (t: any) => [
  { label: t('dashboard.navDashboard'), href: '/dashboard/policial', icon: LayoutDashboard },
  { label: t('dashboard.navAnalytics'), href: '/dashboard/analitico', icon: BarChart3 },
  { label: t('dashboard.navCriminalNetworks'), href: '/dashboard/grafos', icon: Network },
  { label: t('dashboard.navAlerts'), href: '/dashboard/alertas', icon: ShieldAlert },
  { label: t('dashboard.navRevelations'), href: '/dashboard/revelaciones', icon: Users },
  { label: t('dashboard.navUsers'), href: '/dashboard/usuarios', icon: Users, adminOnly: true },
];

interface PoliceUser {
  username: string;
  rol: string;
  nombre_completo: string;
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { t } = useTranslation();
  const pathname = usePathname();
  const router = useRouter();
  const { sidebarOpen, toggleSidebar } = useAppStore();
  const { account, isConnected, connect, disconnect, did, init, error, switchToZkSYS, chainId } = useWalletStore();
  const [user, setUser] = useState<PoliceUser | null>(null);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const raw = localStorage.getItem('police_user');
      if (!raw) {
        router.replace('/');
        return;
      }
      try {
        setUser(JSON.parse(raw));
      } catch {
        router.replace('/');
      }
    }
  }, [router]);

  useEffect(() => {
    init();
  }, [init]);

  const handleLogout = () => {
    localStorage.removeItem('police_token');
    localStorage.removeItem('police_user');
    router.replace('/');
  };

  if (!user) return null;

  const navItems = getNavItems(t);

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 bg-slate-900 text-white transition-all duration-300 flex flex-col',
          sidebarOpen ? 'w-64' : 'w-16'
        )}
      >
        <div className="h-16 flex items-center justify-between px-4 border-b border-slate-700">
          {sidebarOpen && (
            <Link href="/" className="font-bold text-lg tracking-tight">
              IntelExtorsión
            </Link>
          )}
          <button onClick={toggleSidebar} className="p-1 hover:bg-slate-800 rounded">
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        <nav className="flex-1 py-4 space-y-1">
          {navItems
            .filter((item) => !item.adminOnly || user.rol === 'admin')
            .map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center px-4 py-3 text-sm font-medium transition-colors',
                  active ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white',
                  !sidebarOpen && 'justify-center'
                )}
                title={item.label}
              >
                <Icon size={20} className={sidebarOpen ? 'mr-3' : ''} />
                {sidebarOpen && <span>{item.label}</span>}
                {sidebarOpen && active && <ChevronRight size={16} className="ml-auto" />}
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-slate-700 p-4 space-y-3">
          {sidebarOpen && (
            <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
              {t('dashboard.web3Identity')}
            </div>
          )}

          {error && (
            <div className="bg-red-900/30 border border-red-500/30 rounded-lg p-2 text-[10px] text-red-300">
              {error}
              {error.includes('zkSYS') && (
                <button
                  onClick={switchToZkSYS}
                  className="mt-1 w-full bg-red-600 hover:bg-red-500 text-white text-[10px] font-medium py-1 px-2 rounded transition"
                >
                  {t('dashboard.switchToZkSYS')}
                </button>
              )}
            </div>
          )}

          {isConnected ? (
            <div className={cn('space-y-2', !sidebarOpen && 'flex flex-col items-center')}>
              {sidebarOpen && (
                <>
                  <div className="flex items-center gap-1.5">
                    <span className="inline-block w-2 h-2 bg-green-500 rounded-full" />
                    <span className="text-[10px] text-green-400 font-medium">{t('dashboard.connected')}</span>
                    {chainId === 57057 && (
                      <span className="bg-green-900/30 text-green-300 text-[9px] px-1.5 py-0.5 rounded-full">zkSYS</span>
                    )}
                  </div>
                  <div className="text-[10px] text-slate-400 break-all">
                    <span className="text-slate-500">{t('dashboard.account')}</span> {account?.slice(0, 10)}...
                  </div>
                  {did && (
                    <div className="text-[10px] text-slate-400 break-all">
                      <span className="text-slate-500">DID:</span> {did.slice(0, 24)}...
                    </div>
                  )}
                </>
              )}
              <button
                onClick={disconnect}
                className="flex items-center text-[10px] text-red-400 hover:text-red-300 transition"
              >
                <LogOut size={12} className={sidebarOpen ? 'mr-1.5' : ''} />
                {sidebarOpen && t('dashboard.disconnect')}
              </button>
            </div>
          ) : (
            <button
              onClick={connect}
              className={cn(
                'flex items-center text-sm bg-blue-600 hover:bg-blue-500 text-white px-3 py-2 rounded-lg transition w-full',
                !sidebarOpen && 'justify-center px-2'
              )}
            >
              <Wallet size={16} className={sidebarOpen ? 'mr-2' : ''} />
              {sidebarOpen && t('dashboard.connectPali')}
            </button>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <main
        className={cn(
          'flex-1 transition-all duration-300',
          sidebarOpen ? 'ml-64' : 'ml-16'
        )}
      >
        <header className="h-16 bg-white border-b flex items-center justify-between px-6 sticky top-0 z-40">
          <div className="flex items-center space-x-4">
            <Link href="/" className="text-slate-500 hover:text-slate-800 flex items-center text-sm">
              <Home size={16} className="mr-1" /> {t('dashboard.home')}
            </Link>
            <a href="http://localhost:3000/portal" className="text-slate-500 hover:text-slate-800 flex items-center text-sm">
              <MessageSquare size={16} className="mr-1" /> {t('dashboard.citizenPortal')}
            </a>
            <LanguageSwitcher compact />
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-xs text-slate-400">{t('common.network')} zkSYS Tanenbaum</span>
            <div className="flex items-center space-x-2">
              <div className="text-right hidden sm:block">
                <div className="text-xs font-medium text-slate-700">{user.nombre_completo}</div>
                <div className="text-[10px] uppercase tracking-wider text-blue-600">{user.rol}</div>
              </div>
              <UserCircle size={24} className="text-slate-400" />
              <button
                onClick={handleLogout}
                className="text-slate-400 hover:text-red-500 transition"
                title={t('common.logout')}
              >
                <LogOut size={20} />
              </button>
            </div>
          </div>
        </header>
        <div className="p-6">{children}</div>
      </main>
    </div>
  );
}
