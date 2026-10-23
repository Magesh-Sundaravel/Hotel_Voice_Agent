import React, { useState } from 'react';
import { 
  CalendarCheck, 
  Search, 
  Plus, 
  AlertTriangle, 
  Filter, 
  User, 
  Eye, 
  LogOut,
  BedDouble,
  Receipt
} from 'lucide-react';

export default function ReservationsTable({ 
  bookings, 
  searchFilter, 
  setSearchFilter, 
  onOpenNewBooking, 
  onOpenEarlyDeparture, 
  onSelectBooking 
}) {
  const [statusFilter, setStatusFilter] = useState('all');

  const filteredBookings = bookings.filter(b => {
    // Status filter
    if (statusFilter !== 'all' && b.status !== statusFilter) return false;

    // Search query
    const q = searchFilter.toLowerCase().trim();
    if (!q) return true;
    return (
      b.guest_name.toLowerCase().includes(q) ||
      b.reference_code.toLowerCase().includes(q) ||
      b.room_number.toLowerCase().includes(q) ||
      b.guest_phone.toLowerCase().includes(q)
    );
  });

  const getStatusBadge = (status) => {
    switch (status) {
      case 'checked_in':
        return {
          label: 'In-House',
          class: 'bg-sky-500/20 text-sky-300 border-sky-500/40'
        };
      case 'early_departure':
        return {
          label: 'Early Departure',
          class: 'bg-amber-500/20 text-amber-300 border-amber-500/40'
        };
      case 'confirmed':
        return {
          label: 'Confermata',
          class: 'bg-purple-500/20 text-purple-300 border-purple-500/40'
        };
      case 'checked_out':
        return {
          label: 'Check-out Eseguito',
          class: 'bg-slate-700/60 text-slate-300 border-slate-600/40'
        };
      case 'cancelled':
        return {
          label: 'Cancellata',
          class: 'bg-rose-500/20 text-rose-300 border-rose-500/40'
        };
      default:
        return {
          label: status,
          class: 'bg-slate-800 text-slate-300 border-slate-700'
        };
    }
  };

  return (
    <div className="space-y-5">
      {/* HEADER & CONTROLS */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <CalendarCheck className="w-5 h-5 text-amber-400" />
            Registro Soggiorni & Prenotazioni
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Registro centrale delle prenotazioni con tracciamento dello storico arrivi, partenze anticipate e tariffe.
          </p>
        </div>

        <button
          onClick={onOpenNewBooking}
          className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs shadow-md shadow-amber-950/40 cursor-pointer self-start md:self-auto"
        >
          <Plus className="w-4 h-4" /> Nuova Prenotazione
        </button>
      </div>

      {/* SEARCH & STATUS FILTER PILLS */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-900/60 p-3 rounded-xl border border-slate-800">
        <div className="relative flex-1 max-w-sm">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            placeholder="Cerca per ospite, codice (es. SINA-4020) o camera..."
            className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-100 focus:outline-none focus:border-amber-400"
          />
        </div>

        {/* STATUS FILTER PILLS */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0 text-xs">
          {[
            { id: 'all', label: 'Tutti' },
            { id: 'checked_in', label: 'In-House' },
            { id: 'confirmed', label: 'Confermate' },
            { id: 'early_departure', label: 'Early Departure' },
            { id: 'checked_out', label: 'Terminate' },
          ].map(f => (
            <button
              key={f.id}
              onClick={() => setStatusFilter(f.id)}
              className={`px-3 py-1 rounded-lg transition-all cursor-pointer text-xs whitespace-nowrap ${
                statusFilter === f.id
                  ? 'bg-amber-500/20 text-amber-200 border border-amber-500/40 font-bold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* TABLE */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-800/70 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-700/60">
              <tr>
                <th className="py-3.5 px-4">Codice Rif.</th>
                <th className="py-3.5 px-4">Ospite & Contatto</th>
                <th className="py-3.5 px-4">Camera</th>
                <th className="py-3.5 px-4">Date Soggiorno</th>
                <th className="py-3.5 px-4">Totale Stay</th>
                <th className="py-3.5 px-4">Stato Operativo</th>
                <th className="py-3.5 px-4 text-right">Azioni Front Desk</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredBookings.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    Nessuna prenotazione trovata per i criteri selezionati.
                  </td>
                </tr>
              ) : (
                filteredBookings.map((b) => {
                  const statusInfo = getStatusBadge(b.status);
                  return (
                    <tr key={b.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3.5 px-4">
                        <span className="font-mono font-bold text-amber-300 text-xs px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/20">
                          {b.reference_code}
                        </span>
                      </td>

                      <td className="py-3.5 px-4">
                        <div className="font-semibold text-slate-100 flex items-center gap-1.5">
                          <User className="w-3.5 h-3.5 text-slate-400" />
                          <span>{b.guest_name}</span>
                        </div>
                        <div className="text-[11px] text-slate-400 pl-5 font-mono">{b.guest_phone}</div>
                      </td>

                      <td className="py-3.5 px-4">
                        <div className="font-bold text-slate-200">Camera {b.room_number}</div>
                        <div className="text-[11px] text-slate-400 capitalize">
                          {b.room_category.replace(/_/g, ' ')}
                        </div>
                      </td>

                      <td className="py-3.5 px-4">
                        <div className="text-slate-200 font-medium">
                          {b.check_in_date} → {b.check_out_date}
                        </div>
                        <div className="text-[11px] text-slate-400">
                          {b.nights} {b.nights === 1 ? 'notte' : 'notti'} • {b.guests_count} ospiti
                        </div>
                      </td>

                      <td className="py-3.5 px-4">
                        <div className="font-bold text-slate-100">€{b.total_price.toFixed(2)}</div>
                        <div className="text-[10px] text-slate-400">€{b.price_per_night}/n</div>
                      </td>

                      <td className="py-3.5 px-4">
                        <span className={`inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-0.5 rounded-full border ${statusInfo.class}`}>
                          {b.status === 'early_departure' && <AlertTriangle className="w-3 h-3 text-amber-400" />}
                          {statusInfo.label}
                        </span>
                        {b.early_departure_reason && (
                          <div className="text-[10px] text-amber-300/80 mt-1 max-w-xs truncate" title={b.early_departure_reason}>
                            {b.early_departure_reason}
                          </div>
                        )}
                      </td>

                      <td className="py-3.5 px-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => onSelectBooking(b)}
                            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors cursor-pointer"
                            title="Vedi Folio Prenotazione"
                          >
                            <Eye className="w-3.5 h-3.5" />
                          </button>

                          {b.status === 'checked_in' && (
                            <button
                              onClick={() => onOpenEarlyDeparture(b)}
                              className="px-2.5 py-1 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 text-[11px] font-medium transition-colors cursor-pointer flex items-center gap-1"
                            >
                              <LogOut className="w-3 h-3" /> Partenza Anticipata
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
