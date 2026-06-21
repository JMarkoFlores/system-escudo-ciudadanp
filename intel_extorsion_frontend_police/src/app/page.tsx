'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ShieldAlert, Lock, User, Eye, EyeOff, ShieldCheck } from 'lucide-react';

export default function PoliceLoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!username || !password) {
      setError('Por favor, complete todos los campos.');
      return;
    }

    setLoading(true);
    // Simular autenticación para el prototipo
    setTimeout(() => {
      setLoading(false);
      router.push('/dashboard/policial');
    }, 1200);
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center px-4 relative overflow-hidden text-white">
      {/* Background Glows */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-900/10 rounded-full blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-indigo-950/20 rounded-full blur-3xl" />

      {/* Main Container */}
      <div className="w-full max-w-md bg-slate-900/80 border border-slate-800 backdrop-blur-xl rounded-2xl p-8 shadow-2xl z-10 relative">
        
        {/* Header / Brand */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 bg-blue-600/10 border border-blue-500/30 rounded-full flex items-center justify-center mb-4 shadow-[0_0_20px_rgba(59,130,246,0.15)]">
            <ShieldCheck className="text-blue-500" size={36} />
          </div>
          <h1 className="text-2xl font-extrabold tracking-tight">IntelExtorsión</h1>
          <p className="text-xs text-slate-400 mt-1 uppercase tracking-widest font-mono">Consola de Inteligencia DIVINCRI</p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleLogin} className="space-y-6">
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-sm px-4 py-3 rounded-lg flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
              <span>{error}</span>
            </div>
          )}

          {/* User Input */}
          <div className="space-y-2">
            <label className="text-xs text-slate-400 font-semibold uppercase tracking-wider block">Usuario Oficial</label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-500">
                <User size={18} />
              </span>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Código CIP o Usuario"
                className="w-full bg-slate-950 border border-slate-800 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 rounded-lg py-2.5 pl-10 pr-4 text-sm placeholder-slate-600 outline-none transition"
              />
            </div>
          </div>

          {/* Password Input */}
          <div className="space-y-2">
            <label className="text-xs text-slate-400 font-semibold uppercase tracking-wider block">Clave de Seguridad</label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-500">
                <Lock size={18} />
              </span>
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-slate-950 border border-slate-800 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 rounded-lg py-2.5 pl-10 pr-12 text-sm placeholder-slate-600 outline-none transition"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-500 hover:text-slate-300 transition"
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white font-semibold text-sm py-3 rounded-lg transition shadow-lg shadow-blue-600/20 flex items-center justify-center space-x-2 disabled:opacity-50"
          >
            {loading ? (
              <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <span>Autenticar y Acceder</span>
            )}
          </button>
        </form>

        {/* Footer info */}
        <div className="text-center mt-8 text-xs text-slate-500">
          <p>© 2026 Policía Nacional del Perú · DIVINCRI</p>
          <a href="http://localhost:3000" className="text-blue-500 hover:underline mt-2 inline-block">← Volver al Portal Ciudadano</a>
        </div>
      </div>
    </div>
  );
}
