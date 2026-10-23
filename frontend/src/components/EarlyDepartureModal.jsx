import React, { useState, useEffect } from 'react';
import { AlertTriangle, X, Check, BedDouble, User } from 'lucide-react';

export default function EarlyDepartureModal({ isOpen, booking, onClose, onSubmit }) {
  const [reason, setReason] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

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
    <div className="fixed inset-0 bg-zinc-950/50 backdrop-blur-xs z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl max-w-lg w-full p-5 shadow-xl relative animate-in fade-in zoom-in-95 duration-150">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1 rounded-lg text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200"
        >
          <X className="w-4 h-4" />
        </button>

        <div className="flex items-center gap-2.5 mb-3">
          <div className="w-9 h-9 rounded-lg bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800/60 flex items-center justify-center shrink-0">
            <AlertTriangle className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
              Registra Partenza Anticipata
            </h3>
            <p className="text-xs text-zinc-500 dark:text-zinc-400">
              Ricalcolo del soggiorno e rilascio immediato della camera per il servizio ai piani.
            </p>
          </div>
        </div>

        {/* BOOKING RECAP CARD */}
        <div className="p-3 rounded-lg bg-zinc-50 dark:bg-zinc-800/40 border border-zinc-200/80 dark:border-zinc-800 text-xs space-y-1.5 mb-3.5">
          <div className="flex justify-between items-center">
            <span className="font-medium text-zinc-800 dark:text-zinc-200 flex items-center gap-1.5">
              <User className="w-3.5 h-3.5 text-zinc-400" />
              {booking.guest_name}
            </span>
            <span className="font-mono text-zinc-700 dark:text-zinc-300 font-semibold bg-zinc-200/70 dark:bg-zinc-700/60 px-2 py-0.5 rounded text-[11px]">
              {booking.reference_code}
            </span>
          </div>

          <div className="flex justify-between text-zinc-500 dark:text-zinc-400 text-[11px] pt-1 border-t border-zinc-200/60 dark:border-zinc-700/40">
            <span>Camera: <strong>{booking.room_number}</strong> ({booking.room_category})</span>
            <span>Check-out programmato: <strong>{booking.check_out_date}</strong></span>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3.5">
          <div>
            <label className="text-xs font-medium text-zinc-700 dark:text-zinc-300 block mb-1">
              Motivo della partenza anticipata:
            </label>
            <textarea
              required
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Es. Rientro anticipato urgente per impegni di lavoro, cambio volo..."
              className="w-full bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-lg p-2.5 text-xs text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-400 dark:focus:ring-zinc-600"
            />
          </div>

          <div className="p-2.5 rounded-lg bg-amber-50/70 dark:bg-amber-950/20 border border-amber-200/80 dark:border-amber-900/40 text-[11px] text-amber-900 dark:text-amber-200 leading-normal">
            <strong>Nota Operativa:</strong> Registrando l'uscita anticipata, il PMS sblocca la camera per la pulizia, adegua le notti computate e aggiorna la disponibilità.
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-zinc-100 dark:border-zinc-800">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-3.5 py-1.5 rounded-lg text-xs font-medium text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 cursor-pointer"
            >
              Annulla
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-3.5 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-700 text-white text-xs font-medium transition-colors cursor-pointer disabled:opacity-50 shadow-xs"
            >
              {isSubmitting ? 'Registrazione...' : 'Conferma Uscita & Libera Camera'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
