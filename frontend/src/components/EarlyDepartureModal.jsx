import React, { useState } from 'react';
import { AlertTriangle, X, Check, Calendar, BedDouble, User } from 'lucide-react';

export default function EarlyDepartureModal({ isOpen, booking, onClose, onSubmit }) {
  const [reason, setReason] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen || !booking) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    await onSubmit({
      reference_code: booking.reference_code,
      guest_phone: booking.guest_phone,
      reason: reason.trim() || 'Partenza anticipata richiesta dall\'ospite'
    });
    setIsSubmitting(false);
  };

  return (
    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-amber-500/40 rounded-2xl max-w-lg w-full p-6 shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center justify-center">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-100">
              Registra Partenza Anticipata (Early Departure)
            </h3>
            <p className="text-xs text-slate-400">
              Ricalcolo automatico del conto e sblocco immediato della camera per il servizio ai piani.
            </p>
          </div>
        </div>

        {/* BOOKING RECAP CARD */}
        <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 text-xs space-y-2 mb-4">
          <div className="flex justify-between items-center">
            <span className="font-semibold text-slate-200 flex items-center gap-1.5">
              <User className="w-3.5 h-3.5 text-amber-400" />
              {booking.guest_name}
            </span>
            <span className="font-mono text-amber-300 font-bold bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
              {booking.reference_code}
            </span>
          </div>

          <div className="flex justify-between text-slate-400 text-[11px] pt-1 border-t border-slate-800/60">
            <span>Camera: <strong>{booking.room_number}</strong> ({booking.room_category})</span>
            <span>Check-out programmato: <strong>{booking.check_out_date}</strong></span>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1.5">
              Motivo della partenza anticipata:
            </label>
            <textarea
              required
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Es. Rientro anticipato urgente per impegni di lavoro, cambio itinerario di volo..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-100 focus:outline-none focus:border-amber-400 h-24 placeholder:text-slate-600"
            />
          </div>

          <div className="p-3 rounded-lg bg-amber-950/30 border border-amber-800/40 text-[11px] text-amber-300/90 leading-relaxed">
            <strong>Nota Operativa:</strong> Registrando l'uscita anticipata, il sistema imposta lo stato della prenotazione su <em>Early Departure</em>, notifica la governante per le pulizie e adegua il totale dei pernottamenti.
          </div>

          <div className="flex justify-end gap-2.5 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-colors cursor-pointer"
            >
              Annulla
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs shadow-md shadow-amber-950/40 transition-all cursor-pointer disabled:opacity-50"
            >
              {isSubmitting ? 'Registrazione in corso...' : 'Registra Partenza & Libera Camera'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
