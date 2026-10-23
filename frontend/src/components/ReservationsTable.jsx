import React, { useState } from 'react';
import { 
  CalendarCheck, 
  Search, 
  Plus, 
  AlertTriangle, 
  User, 
  Eye, 
  LogOut,
  X,
  Phone
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
          class: 'bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800/60'
        };
      case 'early_departure':
        return {
          label: 'Early Departure',
          class: 'bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border-amber-200 dark:border-amber-800/60'
        };
      case 'confirmed':
        return {
          label: 'In Arrivo',
          class: 'bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 border-indigo-200 dark:border-indigo-800/60'
        };
      case 'checked_out':
        return {
          label: 'Terminato',
          class: 'bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 border-zinc-200 dark:border-zinc-700'
        };
      case 'cancelled':
        return {
          label: 'Cancellata',
          class: 'bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border-rose-200 dark:border-rose-800/60'
        };
      default:
        return {
          label: status,
          class: 'bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border-zinc-200 dark:border-zinc-700'
        };
    }
  };

  const statusOptions = [
    { id: 'all', label: 'Tutti' },
    { id: 'checked_in', label: 'In-House' },
    { id: 'confirmed', label: 'In Arrivo' },
    { id: 'early_departure', label: 'Partenze Anticipate' },
    { id: 'checked_out', label: 'Terminati' },
  ];

  return (
    <div className="space-y-4">
      {/* HEADER & CONTROLS */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-zinc-200 dark:border-zinc-800">
        <div>
          <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
            <CalendarCheck className="w-5 h-5 text-zinc-700 dark:text-zinc-300" />
            Registro Soggiorni & Prenotazioni
          </h2>
          <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
            Archivio cronologico e gestione operativa dei folios e dei check-in/out.
          </p>
        </div>

        <button
          onClick={onOpenNewBooking}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-white dark:text-zinc-900 text-xs font-medium transition-colors cursor-pointer shadow-xs self-start sm:self-auto"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Nuova Prenotazione</span>
        </button>
      </div>

      {/* SEARCH & STATUS FILTER ROW */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white dark:bg-zinc-900 p-3 rounded-xl border border-zinc-200 dark:border-zinc-800 shadow-xs">
        <div className="relative flex-1 max-w-sm">
          <Search className="w-4 h-4 text-zinc-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            placeholder="Cerca per ospite, codice (es. SINA-4020) o camera..."
            className="w-full pl-9 pr-8 py-1.5 rounded-lg bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700/80 text-xs text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-400 dark:focus:ring-zinc-600 transition-all"
          />
          {searchFilter && (
            <button
              onClick={() => setSearchFilter('')}
              className="absolute right-2.5 top-2.5 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 cursor-pointer"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* STATUS FILTER BUTTONS */}
        <div className="flex items-center gap-1 overflow-x-auto pb-1 sm:pb-0 text-xs">
          {statusOptions.map(f => (
            <button
              key={f.id}
              onClick={() => setStatusFilter(f.id)}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors cursor-pointer whitespace-nowrap ${
                statusFilter === f.id
                  ? 'bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900'
                  : 'text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* TABLE */}
      <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-zinc-50 dark:bg-zinc-800/60 text-zinc-500 dark:text-zinc-400 uppercase text-[10px] font-medium tracking-wider border-b border-zinc-200 dark:border-zinc-800">
              <tr>
                <th className="py-3 px-4">Codice Rif.</th>
                <th className="py-3 px-4">Ospite & Contatto</th>
                <th className="py-3 px-4">Camera</th>
                <th className="py-3 px-4">Soggiorno</th>
                <th className="py-3 px-4">Tariffa Totale</th>
                <th className="py-3 px-4">Stato</th>
                <th className="py-3 px-4 text-right">Azioni</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
              {filteredBookings.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-10 text-center text-zinc-400 text-xs">
                    Nessuna prenotazione corrisponde ai filtri di ricerca.
                  </td>
                </tr>
              ) : (
                filteredBookings.map((b) => {
                  const statusInfo = getStatusBadge(b.status);
                  return (
                    <tr 
                      key={b.id} 
                      className="hover:bg-zinc-50/80 dark:hover:bg-zinc-800/40 transition-colors"
                    >
                      <td className="py-3 px-4">
                        <span className="font-mono text-xs font-semibold text-zinc-800 dark:text-zinc-200 bg-zinc-100 dark:bg-zinc-800 px-2 py-0.5 rounded border border-zinc-200 dark:border-zinc-700">
                          {b.reference_code}
                        </span>
                      </td>

                      <td className="py-3 px-4">
                        <div className="font-medium text-zinc-900 dark:text-zinc-100 flex items-center gap-1.5">
                          <User className="w-3.5 h-3.5 text-zinc-400" />
                          <span>{b.guest_name}</span>
                        </div>
                        <div className="text-[11px] text-zinc-500 dark:text-zinc-400 pl-5 font-mono">
                          {b.guest_phone}
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        <div className="font-semibold text-zinc-800 dark:text-zinc-200">
                          Camera {b.room_number}
                        </div>
                        <div className="text-[11px] text-zinc-500 dark:text-zinc-400 capitalize">
                          {b.room_category.replace(/_/g, ' ')}
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        <div className="text-zinc-800 dark:text-zinc-200 font-medium">
                          {b.check_in_date} → {b.check_out_date}
                        </div>
                        <div className="text-[11px] text-zinc-500 dark:text-zinc-400">
                          {b.nights} {b.nights === 1 ? 'notte' : 'notti'} • {b.guests_count} ospiti
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        <div className="font-semibold text-zinc-900 dark:text-zinc-100">
                          €{b.total_price.toFixed(2)}
                        </div>
                        <div className="text-[10px] text-zinc-400">
                          €{b.price_per_night}/notte
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        <span className={`inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded border ${statusInfo.class}`}>
                          {b.status === 'early_departure' && <AlertTriangle className="w-3 h-3 text-amber-500" />}
                          {statusInfo.label}
                        </span>
                        {b.early_departure_reason && (
                          <div className="text-[10px] text-amber-700 dark:text-amber-300 mt-1 max-w-xs truncate" title={b.early_departure_reason}>
                            {b.early_departure_reason}
                          </div>
                        )}
                      </td>

                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => onSelectBooking(b)}
                            className="p-1.5 rounded-lg text-zinc-600 hover:text-zinc-900 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:text-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
                            title="Visualizza Folio Completo"
                          >
                            <Eye className="w-4 h-4" />
                          </button>

                          {b.status === 'checked_in' && (
                            <button
                              onClick={() => onOpenEarlyDeparture(b)}
                              className="px-2 py-1 rounded bg-amber-50 hover:bg-amber-100 dark:bg-amber-950/40 dark:hover:bg-amber-900/60 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800/60 text-[11px] font-medium transition-colors cursor-pointer flex items-center gap-1"
                              title="Registra Partenza Anticipata"
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
