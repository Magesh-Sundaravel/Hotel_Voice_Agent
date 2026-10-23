import React, { useEffect } from 'react';
import { 
  X, 
  User, 
  Calendar, 
  BedDouble, 
  Phone, 
  Mail, 
  AlertTriangle,
  LogOut,
  FileText
} from 'lucide-react';

export default function BookingDetailDrawer({ booking, onClose, onOpenEarlyDeparture }) {
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && booking) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [booking, onClose]);

  if (!booking) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-zinc-950/40 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="w-full max-w-md bg-white dark:bg-zinc-900 border-l border-zinc-200 dark:border-zinc-800 h-full flex flex-col justify-between shadow-xl p-5 overflow-y-auto">
        <div>
          {/* HEADER */}
          <div className="flex items-center justify-between pb-3.5 border-b border-zinc-200 dark:border-zinc-800">
            <div>
              <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider font-semibold">
                Folio Prenotazione
              </span>
              <h3 className="text-lg font-bold text-zinc-900 dark:text-zinc-100 tracking-tight mt-0.5">
                {booking.reference_code}
              </h3>
            </div>

            <button
              onClick={onClose}
              className="p-1 rounded-lg text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* GUEST CARD */}
          <div className="mt-4 p-3.5 rounded-lg bg-zinc-50 dark:bg-zinc-800/40 border border-zinc-200/80 dark:border-zinc-800 space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-xs text-zinc-500 dark:text-zinc-400 font-medium">Ospite Registrato</span>
              <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-zinc-200/80 dark:bg-zinc-700/80 text-zinc-800 dark:text-zinc-200">
                {booking.status.replace(/_/g, ' ')}
              </span>
            </div>

            <div className="text-sm font-semibold text-zinc-900 dark:text-zinc-100 flex items-center gap-1.5 pt-0.5">
              <User className="w-3.5 h-3.5 text-zinc-400" />
              {booking.guest_name}
            </div>

            <div className="text-xs text-zinc-500 dark:text-zinc-400 flex items-center gap-2 font-mono">
              <Phone className="w-3 h-3 text-zinc-400" />
              {booking.guest_phone}
            </div>

            {booking.guest_email && (
              <div className="text-xs text-zinc-500 dark:text-zinc-400 flex items-center gap-2">
                <Mail className="w-3 h-3 text-zinc-400" />
                {booking.guest_email}
              </div>
            )}
          </div>

          {/* STAY SPECIFICS */}
          <div className="mt-3.5 p-3.5 rounded-lg bg-zinc-50 dark:bg-zinc-800/40 border border-zinc-200/80 dark:border-zinc-800 space-y-2.5 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-zinc-500 dark:text-zinc-400 flex items-center gap-1.5">
                <BedDouble className="w-3.5 h-3.5 text-zinc-400" />
                Alloggio Assegnato:
              </span>
              <span className="font-semibold text-zinc-900 dark:text-zinc-100">
                Camera {booking.room_number} ({booking.room_category})
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-zinc-500 dark:text-zinc-400 flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-zinc-400" />
                Date Soggiorno:
              </span>
              <span className="font-medium text-zinc-800 dark:text-zinc-200">
                {booking.check_in_date} → {booking.check_out_date}
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-zinc-500 dark:text-zinc-400">Pernottamenti:</span>
              <span className="text-zinc-800 dark:text-zinc-200">
                {booking.nights} {booking.nights === 1 ? 'notte' : 'notti'} • {booking.guests_count} persone
              </span>
            </div>

            {booking.is_early_departure && (
              <div className="p-2.5 rounded bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/60 text-amber-900 dark:text-amber-200">
                <div className="font-semibold text-[11px] flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" /> Partenza Anticipata Registrata
                </div>
                <div className="text-[11px] mt-0.5 text-zinc-700 dark:text-zinc-300">
                  Data effettiva uscita: <strong>{booking.actual_departure_date}</strong>
                </div>
                {booking.early_departure_reason && (
                  <div className="text-[10px] mt-0.5 italic text-zinc-600 dark:text-zinc-400">
                    "{booking.early_departure_reason}"
                  </div>
                )}
              </div>
            )}
          </div>

          {/* SPECIAL REQUESTS */}
          {booking.special_requests && (
            <div className="mt-3.5 p-3 rounded-lg bg-zinc-50 dark:bg-zinc-800/40 border border-zinc-200/80 dark:border-zinc-800 text-xs">
              <span className="font-medium text-zinc-700 dark:text-zinc-300 block mb-0.5">
                Note & Richieste Speciali:
              </span>
              <p className="text-zinc-600 dark:text-zinc-400 italic">
                "{booking.special_requests}"
              </p>
            </div>
          )}

          {/* BILLING LEDGER */}
          <div className="mt-3.5 p-3.5 rounded-lg bg-zinc-50 dark:bg-zinc-800/40 border border-zinc-200/80 dark:border-zinc-800 space-y-2 text-xs">
            <span className="text-[10px] font-semibold text-zinc-400 uppercase tracking-wider block mb-1">
              Riepilogo Conto Folio
            </span>

            <div className="flex justify-between text-zinc-600 dark:text-zinc-400">
              <span>Tariffa concordata per notte:</span>
              <span>€{booking.price_per_night?.toFixed(2)}</span>
            </div>

            <div className="flex justify-between text-zinc-600 dark:text-zinc-400">
              <span>Notti totali computate:</span>
              <span>{booking.nights}</span>
            </div>

            <div className="flex justify-between font-bold text-sm text-zinc-900 dark:text-zinc-100 pt-2 border-t border-zinc-200 dark:border-zinc-700">
              <span>Totale Soggiorno:</span>
              <span className="font-mono text-base">€{booking.total_price?.toFixed(2)}</span>
            </div>
          </div>
        </div>

        {/* BOTTOM ACTION */}
        {booking.status === 'checked_in' && (
          <div className="pt-4 border-t border-zinc-200 dark:border-zinc-800">
            <button
              onClick={() => {
                onClose();
                onOpenEarlyDeparture(booking);
              }}
              className="w-full py-2 rounded-lg bg-amber-600 hover:bg-amber-700 text-white font-medium text-xs transition-colors cursor-pointer flex items-center justify-center gap-1.5 shadow-xs"
            >
              <LogOut className="w-3.5 h-3.5" /> Registra Partenza Anticipata
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
