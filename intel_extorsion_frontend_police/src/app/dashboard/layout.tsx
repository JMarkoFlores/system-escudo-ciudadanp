'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useWalletStore } from '@/stores/walletStore';
import { useAppStore } from '@/stores/appStore';
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
} from 'lucide-react';
import { cn } from '@/lib/utils/cn';

const navItems = [
  { label: 'Dashboard', href: '/dashboard/policial', icon: LayoutDashboard },
  { label: 'Analítico', href: '/dashboard/analitico', icon: BarChart3 },
  { label: 'Redes Criminales', href: '/dashboard/grafos', icon: Network },
  { label: 'Alertas', href: '/dashboard/alertas', icon: ShieldAlert },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { sidebarOpen, toggleSidebar } = useAppStore();
  const { account, isConnected, connect, disconnect, did } = useWalletStore();

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
          {navItems.map((item) => {
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
              Web3 Identity
            </div>
          )}

          {isConnected ? (
            <div className={cn('space-y-2', !sidebarOpen && 'flex flex-col items-center')}>
              {sidebarOpen && (
                <div className="text-xs text-slate-300 break-all">
                  <span className="text-slate-500">Cuenta:</span> {account?.slice(0, 10)}...
                </div>
              )}
              {sidebarOpen && did && (
                <div className="text-xs text-slate-300 break-all">
                  <span className="text-slate-500">DID:</span> {did.slice(0, 20)}...
                </div>
              )}
              <button
                onClick={disconnect}
                className="flex items-center text-xs text-red-400 hover:text-red-300 transition"
              >
                <LogOut size={14} className={sidebarOpen ? 'mr-2' : ''} />
                {sidebarOpen && 'Desconectar'}
              </button>
            </div>
          ) : (
            <button
              onClick={connect}
              className={cn(
                'flex items-center text-sm bg-blue-600 hover:bg-blue-500 text-white px-3 py-2 rounded transition',
                !sidebarOpen && 'justify-center px-2'
              )}
            >
              <Wallet size={16} className={sidebarOpen ? 'mr-2' : ''} />
              {sidebarOpen && 'Conectar Pali'}
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
              <Home size={16} className="mr-1" /> Inicio
            </Link>
            <a href="http://localhost:3000/portal" className="text-slate-500 hover:text-slate-800 flex items-center text-sm">
              <MessageSquare size={16} className="mr-1" /> Portal Ciudadano
            </a>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-xs text-slate-400">zkSYS Tanenbaum</span>
            <UserCircle size={24} className="text-slate-400" />
          </div>
        </header>
        <div className="p-6">{children}</div>
      </main>
    </div>
  );
}
