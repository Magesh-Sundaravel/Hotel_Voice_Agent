import React, { useState } from 'react';
import { 
  BellRing, 
  ShieldAlert, 
  CheckCircle2, 
  Car, 
  Clock, 
  Calendar, 
  Check, 
  User, 
  Phone,
  AlertTriangle,
  Filter
} from 'lucide-react';

export default function OperationsAlerts({ notifications, onMarkAsRead, onRefresh }) {
  const [unreadOnly, setUnreadOnly] = useState(false);

  const displayedNotifications = unreadOnly 
    ? notifications.filter(n => !n.is_read)
    : notifications;

  const getAlertIcon = (type) => {
    switch (type) {
      case 'allergy_alert':
        return <ShieldAlert className="w-5 h-5 text-rose-400" />;
      case 'new_booking':
      case 'room_booking_created':
        return <CheckCircle2 className="w-5 h-5 text-emerald-400" />;
      case 'early_departure':
        return <AlertTriangle className="w-5 h-5 text-amber-400" />;
      case 'transfer_request':
        return <Car className="w-5 h-5 text-sky-400" />;
      case 'concierge_request':
        return <Clock className="w-5 h-5 text-purple-400" />;
      default:
        return <BellRing className="w-5 h-5 text-amber-400" />;
    }
  };

  const getAlertBorder = (type, isRead) => {
    if (isRead) return 'border-slate-800/80 bg-slate-900/50 opacity-75';
    switch (type) {
      case 'allergy_alert':
        return 'border-rose-800/50 bg-gradient-to-r from-slate-900 to-rose-950/20';
      case 'early_departure':
        return 'border-amber-800/50 bg-gradient-to-r from-slate-900 to-amber-950/20';
      case 'new_booking':
        return 'border-emerald-800/50 bg-gradient-to-r from-slate-900 to-emerald-950/20';
      default:
        return 'border-slate-800 bg-slate-900/90';
    }
  };

  return (
    <div className="space-y-5">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <BellRing className="w-5 h-5 text-amber-400" />
            Operations & Kitchen Dispatch Alerts
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Registro istantaneo degli eventi operativi generati dall'assistente telefonico (allarmi allergie, partenze anticipate, richieste transfer).
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setUnreadOnly(!unreadOnly)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all cursor-pointer flex items-center gap-1.5 ${
              unreadOnly 
                ? 'bg-amber-500/20 text-amber-300 border-amber-500/40' 
                : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
            }`}
          >
            <Filter className="w-3.5 h-3.5" />
            <span>Solo Non Lette</span>
          </button>
        </div>
      </div>

      {/* ALERTS FEED */}
      <div className="space-y-3">
        {displayedNotifications.length === 0 ? (
          <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-8 text-center text-slate-500 text-xs">
            Nessuna notifica presente.
          </div>
        ) : (
          displayedNotifications.map((notif) => (
            <div
              key={notif.id}
              className={`p-4 rounded-xl border transition-all flex items-start gap-4 ${getAlertBorder(notif.type, notif.is_read)}`}
            >
              <div className="p-2 rounded-lg bg-slate-950/70 border border-slate-800 shrink-0 mt-0.5">
                {getAlertIcon(notif.type)}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <h4 className="text-xs font-bold text-slate-100 flex items-center gap-2">
                    <span>{notif.title}</span>
                    {!notif.is_read && (
                      <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
                    )}
                  </h4>

                  <span className="text-[10px] text-slate-400 font-mono shrink-0">
                    {new Date(notif.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>

                <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                  {notif.message}
                </p>

                {/* CALLER / GUEST CONTEXT */}
                {(notif.customer_name || notif.customer_phone) && (
                  <div className="mt-2 flex items-center gap-3 text-[11px] text-slate-400 pt-2 border-t border-slate-800/60 font-mono">
                    {notif.customer_name && (
                      <span className="flex items-center gap-1 text-slate-300">
                        <User className="w-3 h-3 text-slate-400" />
                        {notif.customer_name}
                      </span>
                    )}
                    {notif.customer_phone && (
                      <span className="flex items-center gap-1 text-slate-400">
                        <Phone className="w-3 h-3 text-slate-400" />
                        {notif.customer_phone}
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* ACTION: MARK AS READ */}
              {!notif.is_read && (
                <button
                  onClick={() => onMarkAsRead(notif.id)}
                  className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/60 text-[11px] font-medium transition-colors cursor-pointer shrink-0 flex items-center gap-1"
                  title="Segna come letto"
                >
                  <Check className="w-3 h-3" /> Letto
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
