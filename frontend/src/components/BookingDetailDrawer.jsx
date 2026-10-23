import React from 'react';
import { 
  X, 
  User, 
  Calendar, 
  BedDouble, 
  Phone, 
  Mail, 
  Receipt, 
  AlertTriangle,
  Clock,
  Sparkles,
  LogOut
} from 'lucide-react';

export default function BookingDetailDrawer({ booking, onClose, onOpenEarlyDeparture }) {
  if (!booking) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/70 backdrop-blur-xs">
      <div className="w-full max-w-md bg-slate-900 border-l border-slate-800 h-full flex flex-col justify-between shadow-2xl p-6 overflow-y-auto">
        <div>
          {/* HEADER */}
          <div className="flex items-center justify-between pb-4 border-b border-slate-800">
            <div>
              <span className="text-[10px] font-mono text-amber-400 font-bold uppercase tracking-wider">
                Folio Prenotazione
              </span>
              <h3 className="text-xl font-bold text-slate-100 font-serif-luxury mt-0.5">
                {booking.reference_code}
              </h3>
            </div>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* GUEST CARD */}
          <div className="mt-5 p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400 font-medium">Ospite Registrato</span>
              <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/30">
                {booking.status.replace(/_/g, ' ')}
              </span>
            </div>

            <div className="text-base font-bold text-slate-100 flex items-center gap-2">
              <User className="w-4 h-4 text-amber-400" />
              {booking.guest_name}
            </div>

            <div className="text-xs text-slate-400 flex items-center gap-2 font-mono">
              <Phone className="w-3.5 h-3.5 text-slate-400" />
              {booking.guest_phone}
            </div>

            {booking.guest_email && (
              <div className="text-xs text-slate-400 flex items-center gap-2">
                <Mail className="w-3.5 h-3.5 text-slate-400" />
                {booking.guest_email}
              </div>
            )}
          </div>

          {/* ROOM & STAY SPECIFICS */}
          <div className="mt-4 p-4 rounded-xl bg-slate-950/50 border border-slate-800 space-y-3 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-slate-400 flex items-center gap-1.5">
                <BedDouble className="w-4 h-4 text-sky-400" />
                Alloggio Assegnato:
              </span>
              <span className="font-bold text-slate-200">
                Camera {booking.room_number} ({booking.room_category})
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-slate-400 flex items-center gap-1.5">
                <Calendar className="w-4 h-4 text-amber-400" />
                Date Soggiorno:
              </span>
              <span className="font-semibold text-slate-200">
                {booking.check_in_date} → {booking.check_out_date}
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-slate-400">Pernottamenti & Ospiti:</span>
              <span className="text-slate-200">
                {booking.nights} {booking.nights === 1 ? 'notte' : 'notti'} • {booking.guests_count} persone
              </span>
            </div>

            {booking.is_early_departure && (
              <div className="p-3 rounded-lg bg-amber-950/40 border border-amber-800/40 text-amber-200">
                <div className="font-bold text-[11px] flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-400" /> Partenza Anticipata Effettuata
                </div>
                <div className="text-[11px] mt-1 text-slate-300">
                  Data effettiva uscita: <strong>{booking.actual_departure_date}</strong>
                </div>
                {booking.early_departure_reason && (
                  <div className="text-[10px] mt-1 italic text-amber-300/80">
                    "{booking.early_departure_reason}"
                  </div>
                )}
              </div>
            )}
          </div>

          {/* SPECIAL REQUESTS & NOTES */}
          {booking.special_requests && (
            <div className="mt-4 p-3.5 rounded-xl bg-slate-950/50 border border-slate-800 text-xs">
              <span className="font-semibold text-slate-300 block mb-1">
                Richieste Speciali / Note Registrate:
              </span>
              <p className="text-slate-300 italic">"{booking.special_requests}"</p>
            </div>
          )}

          {/* BILLING / FOLIO CALCULATION */}
          <div className="mt-4 p-4 rounded-xl bg-gradient-to-br from-slate-950 to-slate-900 border border-slate-800 space-y-2 text-xs">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
              Riepilogo Tariffario
            </span>

            <div className="flex justify-between text-slate-400">
              <span>Tariffa per notte:</span>
              <span>€{booking.price_per_night?.toFixed(2)}</span>
            </div>

            <div className="flex justify-between text-slate-400">
              <span>Notti computate:</span>
              <span>{booking.nights}</span>
            </div>

            <div className="flex justify-between font-bold text-sm text-slate-100 pt-2 border-t border-slate-800">
              <span>Totale Soggiorno:</span>
              <span className="text-amber-300 font-mono text-base">€{booking.total_price?.toFixed(2)}</span>
            </div>
          </div>
        </div>

        {/* BOTTOM ACTION */}
        {booking.status === 'checked_in' && (
          <div className="pt-4 border-t border-slate-800">
            <button
              onClick={() => {
                onClose();
                onOpenEarlyDeparture(booking);
              }}
              className="w-full py-2.5 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 font-semibold text-xs transition-colors cursor-pointer flex items-center justify-center gap-2"
            >
              <LogOut className="w-4 h-4" /> Registra Partenza Anticipata
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
