import React from 'react';
import { 
  Building2, 
  BedDouble, 
  CalendarCheck, 
  Users, 
  BellRing, 
  MapPin, 
  Sparkles,
  PhoneCall
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab, unreadAlertsCount = 0 }) {
  const menuItems = [
    { 
      id: 'room_rack', 
      label: 'Room Rack & Status', 
      subtitle: 'Occupazione e stato piani',
      icon: BedDouble 
    },
    { 
      id: 'reservations', 
      label: 'Reservations & Stays', 
      subtitle: 'Registro soggiorni e partenze',
      icon: CalendarCheck 
    },
    { 
      id: 'guest_crm', 
      label: 'Guest 360 Intelligence', 
      subtitle: 'Profili VIP, diete e preferenze',
      icon: Users 
    },
    { 
      id: 'operations_alerts', 
      label: 'Operations & Kitchen Alerts', 
      subtitle: 'Notifiche in tempo reale da centralino',
      icon: BellRing, 
      badge: unreadAlertsCount 
    },
  ];

  return (
    <aside className="w-72 bg-slate-900/95 border-r border-slate-800 flex flex-col justify-between shrink-0 select-none">
      <div>
        {/* HOTEL LOGO & IDENTITY */}
        <div className="p-6 border-b border-slate-800/80">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-amber-400 via-amber-500 to-amber-700 flex items-center justify-center shadow-lg shadow-amber-950/40 border border-amber-300/30">
              <Building2 className="w-6 h-6 text-slate-950" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-serif-luxury text-lg font-bold tracking-wider text-amber-200">
                  SINA HOTELS
                </span>
              </div>
              <p className="text-[11px] text-amber-400/90 font-medium">Bernini Bristol • 5★ Lusso</p>
            </div>
          </div>

          <div className="mt-4 flex items-center gap-1.5 text-[11px] text-slate-400">
            <MapPin className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            <span className="truncate">Piazza Barberini 23, Roma</span>
          </div>
        </div>

        {/* PMS SYSTEM LABEL */}
        <div className="px-6 pt-5 pb-2">
          <span className="text-[10px] uppercase font-bold tracking-widest text-slate-400">
            Front Desk & Property Management
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
                className={`w-full flex items-center justify-between px-3.5 py-3 rounded-xl text-left transition-all cursor-pointer ${
                  isActive
                    ? 'bg-amber-500/15 text-amber-200 border border-amber-500/40 shadow-sm shadow-amber-950/20'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`p-1.5 rounded-lg ${isActive ? 'bg-amber-400/20 text-amber-300' : 'text-slate-400'}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-slate-200">{item.label}</div>
                    <div className="text-[10px] text-slate-400 font-normal">{item.subtitle}</div>
                  </div>
                </div>

                {item.badge > 0 && (
                  <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-rose-500 text-white shadow-sm">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* FOOTER SYSTEM STATUS */}
      <div className="p-4 m-3 rounded-xl bg-slate-950/70 border border-slate-800/80 text-xs">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-1.5 text-slate-300 font-medium text-[11px]">
            <PhoneCall className="w-3.5 h-3.5 text-emerald-400" />
            <span>Voice Receptionist</span>
          </div>
          <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            Online
          </span>
        </div>
        <p className="text-[10px] text-slate-400 leading-relaxed">
          I clienti telefonano al centralino esterno. Prenotazioni e richieste compaiono qui automaticamente.
        </p>
      </div>
    </aside>
  );
}
