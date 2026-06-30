import React from 'react';

const channels = [
  {
    name: 'WhatsApp',
    icon: '💬',
    color: 'bg-green-50 border-green-200',
    textColor: 'text-green-700',
    btnColor: 'bg-green-600 hover:bg-green-700',
    description: 'Envía evidencias y mensajes de voz desde tu celular. El bot transcribe audios con Whisper IA y sella todo en blockchain.',
    action: 'Escribir al bot',
    link: 'https://wa.me/51999999999',
    note: 'Disponible 24/7. Tus audios se procesan con reconocimiento de voz de Groq Whisper.',
  },
  {
    name: 'Telegram',
    icon: '✈️',
    color: 'bg-sky-50 border-sky-200',
    textColor: 'text-sky-700',
    btnColor: 'bg-sky-600 hover:bg-sky-700',
    description: 'Chatea con el bot de Telegram para reportar extorsión y adjuntar evidencias con trazabilidad forense.',
    action: 'Abrir en Telegram',
    link: 'https://t.me/IntelExtorsionBot',
    note: 'Compatible con imágenes, documentos y mensajes de texto. Sin límite de tamaño.',
  },
  {
    name: 'Discord',
    icon: '🎮',
    color: 'bg-indigo-50 border-indigo-200',
    textColor: 'text-indigo-700',
    btnColor: 'bg-indigo-600 hover:bg-indigo-700',
    description: 'Únete al servidor de Discord para reportar evidencia en canales dedicados con custodia automatizada.',
    action: 'Unirse al servidor',
    link: 'https://discord.gg/intel-extorsion',
    note: 'Canales separados por tipo de evidencia. Moderación y custodia automática.',
  },
];

const ChannelConnect = () => {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
      <h2 className="text-lg font-bold mb-2 text-gray-800 flex items-center gap-2">
        <span className="w-8 h-8 bg-amber-100 rounded-lg flex items-center justify-center text-amber-600 text-sm">📡</span>
        Canales de Aportación de Evidencia
      </h2>
      <p className="text-sm text-gray-500 mb-4">
        ¿Prefieres usar mensajería instantánea? También puedes aportar evidencias con custodia forense a través de nuestros bots. El sellado en blockchain y la captura forense aplican exactamente igual que en la DApp.
      </p>

      <div className="grid md:grid-cols-3 gap-4">
        {channels.map((ch) => (
          <div key={ch.name} className={`rounded-xl border p-4 ${ch.color} space-y-2`}>
            <div className="flex items-center gap-2">
              <span className="text-2xl">{ch.icon}</span>
              <h3 className={`font-bold text-sm ${ch.textColor}`}>{ch.name}</h3>
            </div>
            <p className="text-xs text-gray-600 leading-relaxed">{ch.description}</p>
            <a
              href={ch.link}
              target="_blank"
              rel="noreferrer"
              className={`block text-center text-white text-xs font-semibold py-2 px-3 rounded-lg transition ${ch.btnColor}`}
            >
              {ch.action}
            </a>
            <p className="text-xs text-gray-400 italic">{ch.note}</p>
          </div>
        ))}
      </div>

      <div className="mt-4 bg-gray-50 rounded-lg p-3 text-xs text-gray-500 leading-relaxed border border-gray-100">
        <p className="font-semibold text-gray-700 mb-1">🔒 Privacidad y trazabilidad</p>
        <p>Independientemente del canal que uses, toda evidencia se procesa con los mismos estándares forenses: hash SHA-256 del archivo original, timestamp UTC, eliminación de EXIF/GPS, y sellado en zkSYS Tanenbaum Testnet. Tu identidad se protege mediante DID (Identidad Descentralizada) — eres seudónimo, no anónimo. Solo la DIVINCRI La Libertad puede vincular tu DID con tu identidad civil, y solo si tú lo autorizas explícitamente.</p>
      </div>
    </div>
  );
};

export default ChannelConnect;
