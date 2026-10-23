import React from 'react';
import { 
  Building2, 
  BedDouble, 
  CalendarCheck, 
  Users, 
  BellRing, 
  MapPin, 
  PhoneCall,
  Sparkles,
  ExternalLink
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab, unreadAlertsCount = 0 }) {
  const menuItems = [
    { 
      id: 'room_rack', 
      label: 'Room Rack', 
      subtitle: 'Occupazione e stato piani',
      icon: BedDouble 
    },
    { 
      id: 'reservations', 
      label: 'Prenotazioni', 
      subtitle: 'Registro soggiorni e folios',
      icon: CalendarCheck 
    },
    { 
      id: 'guest_crm', 
      label: 'Guest 360 CRM', 
      subtitle: 'Dossier VIP e diete',
      icon: Users 
    },
    { 
      id: 'operations_alerts', 
      label: 'Allarmi & Centralino', 
      subtitle: 'Notifiche in tempo reale',
      icon: BellRing, 
      badge: unreadAlertsCount 
    },
  ];

  return (
    <aside className="w-64 bg-white dark:bg-zinc-900 border-r border-zinc-200 dark:border-zinc-800 flex flex-col justify-between shrink-0 select-none transition-colors">
      <div>
        {/* BRAND IDENTITY */}
        <div className="p-5 border-b border-zinc-200 dark:border-zinc-800">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-950 flex items-center justify-center font-bold text-sm tracking-wider shadow-sm">
              SB
            </div>
            <div className="min-w-0">
              <div className="font-semibold text-sm text-zinc-900 dark:text-zinc-100 tracking-tight truncate">
                Sina Bernini Bristol
              </div>
              <p className="text-[11px] text-zinc-500 dark:text-zinc-400 font-normal">
                5★ Lusso • Roma
              </p>
            </div>
          </div>

          <div className="mt-3 flex items-center gap-1.5 text-[11px] text-zinc-500 dark:text-zinc-400">
            <MapPin className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
            <span className="truncate">Piazza Barberini 23</span>
          </div>
        </div>

        {/* SECTION TITLE */}
        <div className="px-5 pt-4 pb-2">
          <span className="text-[11px] font-medium uppercase tracking-wider text-zinc-400 dark:text-zinc-500">
            Gestione Reception
          </span>
        </div>

        {/* NAVIGATION LINKS */}
        <nav className="px-3 space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-left transition-colors cursor-pointer text-xs font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-400 ${
                  isActive
                    ? 'bg-zinc-100 text-zinc-900 dark:bg-zinc-800 dark:text-white font-semibold shadow-xs'
                    : 'text-zinc-600 hover:text-zinc-900 hover:bg-zinc-50 dark:text-zinc-400 dark:hover:text-zinc-200 dark:hover:bg-zinc-800/60'
                }`}
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-zinc-900 dark:text-white' : 'text-zinc-500 dark:text-zinc-400'}`} />
                  <div className="truncate">
                    <div>{item.label}</div>
                    <div className="text-[10px] text-zinc-400 dark:text-zinc-500 font-normal">{item.subtitle}</div>
                  </div>
                </div>

                {item.badge > 0 && (
                  <span className="px-1.5 py-0.5 text-[10px] font-semibold rounded-full bg-rose-500 text-white leading-none ml-2 shrink-0">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* FOOTER SYSTEM STATUS */}
      <div className="p-4 border-t border-zinc-200 dark:border-zinc-800">
        <div className="p-3 rounded-lg bg-zinc-50 dark:bg-zinc-950/70 border border-zinc-200/80 dark:border-zinc-800/80 text-xs">
          <div className="flex items-center justify-between mb-1.5">
            <div className="flex items-center gap-1.5 font-medium text-[11px] text-zinc-800 dark:text-zinc-200">
              <PhoneCall className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
              <span>Voice Receptionist</span>
            </div>
            <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-600 dark:text-emerald-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              Attivo
            </span>
          </div>
          <p className="text-[11px] text-zinc-500 dark:text-zinc-400 leading-normal">
            L'assistente telefonico risponde ai clienti in lingua italiana e aggiorna il PMS.
          </p>
        </div>
      </div>
    </aside>
  );
}
