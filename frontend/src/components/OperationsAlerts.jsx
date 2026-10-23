import React, { useState } from 'react';
import { 
  BellRing, 
  ShieldAlert, 
  CheckCircle2, 
  Car, 
  Clock, 
  Check, 
  User, 
  Phone,
  AlertTriangle,
  Filter,
  CheckCheck
} from 'lucide-react';

export default function OperationsAlerts({ notifications, onMarkAsRead, onRefresh }) {
  const [unreadOnly, setUnreadOnly] = useState(false);

  const displayedNotifications = unreadOnly 
    ? notifications.filter(n => !n.is_read)
    : notifications;

  const unreadCount = notifications.filter(n => !n.is_read).length;

  const getAlertIcon = (type) => {
    switch (type) {
      case 'allergy_alert':
        return <ShieldAlert className="w-4 h-4 text-rose-600 dark:text-rose-400" />;
      case 'new_booking':
      case 'room_booking_created':
        return <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />;
      case 'early_departure':
        return <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400" />;
      case 'transfer_request':
        return <Car className="w-4 h-4 text-blue-600 dark:text-blue-400" />;
      case 'concierge_request':
        return <Clock className="w-4 h-4 text-zinc-600 dark:text-zinc-400" />;
      default:
        return <BellRing className="w-4 h-4 text-zinc-600 dark:text-zinc-400" />;
    }
  };

  const getAlertIconBg = (type) => {
    switch (type) {
      case 'allergy_alert':
        return 'bg-rose-50 dark:bg-rose-950/40 border-rose-200 dark:border-rose-900/60';
      case 'early_departure':
        return 'bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-900/60';
      case 'new_booking':
      case 'room_booking_created':
        return 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-900/60';
      case 'transfer_request':
        return 'bg-blue-50 dark:bg-blue-950/40 border-blue-200 dark:border-blue-900/60';
      default:
        return 'bg-zinc-100 dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700';
    }
  };

  return (
    <div className="space-y-4">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-zinc-200 dark:border-zinc-800">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
              <BellRing className="w-5 h-5 text-zinc-700 dark:text-zinc-300" />
              Allarmi & Centralino Voice
            </h2>
            {unreadCount > 0 && (
              <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-rose-500 text-white">
                {unreadCount} nuove
              </span>
            )}
          </div>
          <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
            Registro istantaneo degli eventi operativi generati dall'assistente telefonico (allarmi diete, partenze anticipate, NCC).
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setUnreadOnly(!unreadOnly)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors cursor-pointer flex items-center gap-1.5 ${
              unreadOnly 
                ? 'bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900 border-zinc-900 dark:border-zinc-100' 
                : 'bg-white dark:bg-zinc-900 text-zinc-600 dark:text-zinc-400 border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800'
            }`}
          >
            <Filter className="w-3.5 h-3.5" />
            <span>{unreadOnly ? 'Tutte le Notifiche' : 'Solo Non Lette'}</span>
          </button>
        </div>
      </div>

      {/* ALERTS FEED */}
      <div className="space-y-2.5">
        {displayedNotifications.length === 0 ? (
          <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-8 text-center text-zinc-500 dark:text-zinc-400 text-xs shadow-xs">
            {unreadOnly ? 'Tutti gli allarmi sono stati letti.' : 'Nessuna notifica presente.'}
          </div>
        ) : (
          displayedNotifications.map((notif) => (
            <div
              key={notif.id}
              className={`p-3.5 rounded-xl border transition-all flex items-start gap-3.5 ${
                notif.is_read
                  ? 'bg-white/70 dark:bg-zinc-900/60 border-zinc-200/80 dark:border-zinc-800 opacity-75'
                  : 'bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-700/80 shadow-xs'
              }`}
            >
              {/* ICON BADGE */}
              <div className={`p-2 rounded-lg border shrink-0 mt-0.5 ${getAlertIconBg(notif.type)}`}>
                {getAlertIcon(notif.type)}
              </div>

              {/* DETAILS */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <h4 className="text-xs font-semibold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
                    <span>{notif.title}</span>
                    {!notif.is_read && (
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
                    )}
                  </h4>

                  <span className="text-[11px] text-zinc-400 dark:text-zinc-500 font-mono shrink-0">
                    {new Date(notif.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>

                <p className="text-xs text-zinc-600 dark:text-zinc-300 mt-1 leading-relaxed">
                  {notif.message}
                </p>

                {/* CALLER / GUEST CONTEXT */}
                {(notif.customer_name || notif.customer_phone) && (
                  <div className="mt-2 flex items-center gap-3 text-[11px] text-zinc-500 dark:text-zinc-400 pt-2 border-t border-zinc-100 dark:border-zinc-800">
                    {notif.customer_name && (
                      <span className="flex items-center gap-1 font-medium text-zinc-700 dark:text-zinc-300">
                        <User className="w-3 h-3 text-zinc-400" />
                        {notif.customer_name}
                      </span>
                    )}
                    {notif.customer_phone && (
                      <span className="flex items-center gap-1 font-mono text-zinc-500">
                        <Phone className="w-3 h-3 text-zinc-400" />
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
                  className="px-2.5 py-1 rounded-lg text-xs font-medium text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 transition-colors cursor-pointer shrink-0 flex items-center gap-1"
                  title="Segna come letto"
                >
                  <Check className="w-3 h-3" />
                  <span>Letto</span>
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
