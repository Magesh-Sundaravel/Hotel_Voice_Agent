import React, { useState } from 'react';
import { 
  BedDouble, 
  User, 
  Calendar, 
  AlertTriangle, 
  CheckCircle2, 
  Plus, 
  Layers,
  ChevronRight,
  LogOut,
  Info
} from 'lucide-react';

export default function RoomRack({ rooms, bookings, onOpenNewBooking, onOpenEarlyDeparture, onSelectBooking }) {
  const [selectedFloor, setSelectedFloor] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState('all');

  const floors = Array.from(new Set(rooms.map(r => r.floor))).sort((a, b) => a - b);

  const getRoomBookingInfo = (roomNumber) => {
    const activeBooking = bookings.find(
      b => b.room_number === roomNumber && b.status === 'checked_in'
    );
    const earlyDepBooking = bookings.find(
      b => b.room_number === roomNumber && b.status === 'early_departure'
    );
    const reservedBooking = bookings.find(
      b => b.room_number === roomNumber && b.status === 'confirmed'
    );
    return { activeBooking, earlyDepBooking, reservedBooking };
  };

  const filteredRooms = rooms.filter(room => {
    if (selectedFloor !== 'all' && room.floor !== parseInt(selectedFloor)) return false;
    
    if (selectedStatus !== 'all') {
      const { activeBooking, earlyDepBooking, reservedBooking } = getRoomBookingInfo(room.room_number);
      if (selectedStatus === 'in_house' && !activeBooking) return false;
      if (selectedStatus === 'early_departure' && !earlyDepBooking) return false;
      if (selectedStatus === 'reserved' && !reservedBooking) return false;
      if (selectedStatus === 'available' && (activeBooking || earlyDepBooking || reservedBooking)) return false;
    }
    return true;
  });

  return (
    <div className="space-y-5">
      {/* HEADER & FILTER TOOLBAR */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-zinc-200 dark:border-zinc-800">
        <div>
          <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
            <BedDouble className="w-5 h-5 text-zinc-700 dark:text-zinc-300" />
            Room Rack & Occupazione
          </h2>
          <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
            Stato in tempo reale delle 9 camere e suite del Sina Bernini Bristol.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Floor filter */}
          <div className="flex items-center bg-zinc-100 dark:bg-zinc-800/80 p-0.5 rounded-lg text-xs">
            <button
              onClick={() => setSelectedFloor('all')}
              className={`px-2.5 py-1 rounded-md transition-colors cursor-pointer text-xs font-medium ${
                selectedFloor === 'all'
                  ? 'bg-white dark:bg-zinc-700 text-zinc-900 dark:text-white shadow-xs'
                  : 'text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200'
              }`}
            >
              Tutti i Piani
            </button>
            {floors.map(f => (
              <button
                key={f}
                onClick={() => setSelectedFloor(f.toString())}
                className={`px-2.5 py-1 rounded-md transition-colors cursor-pointer text-xs font-medium ${
                  selectedFloor === f.toString()
                    ? 'bg-white dark:bg-zinc-700 text-zinc-900 dark:text-white shadow-xs'
                    : 'text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200'
                }`}
              >
                Piano {f}
              </button>
            ))}
          </div>

          {/* Quick New Booking Button */}
          <button
            onClick={onOpenNewBooking}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-white dark:text-zinc-900 text-xs font-medium transition-colors cursor-pointer shadow-xs"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Nuova Prenotazione</span>
          </button>
        </div>
      </div>

      {/* STATUS FILTER PILLS */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
        {[
          { id: 'all', label: 'Tutte le Camere' },
          { id: 'available', label: 'Disponibili' },
          { id: 'in_house', label: 'In-House' },
          { id: 'reserved', label: 'In Arrivo' },
          { id: 'early_departure', label: 'Partenze Anticipate' },
        ].map(filter => (
          <button
            key={filter.id}
            onClick={() => setSelectedStatus(filter.id)}
            className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors cursor-pointer whitespace-nowrap ${
              selectedStatus === filter.id
                ? 'bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900'
                : 'bg-white dark:bg-zinc-900 text-zinc-600 dark:text-zinc-400 border border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800'
            }`}
          >
            {filter.label}
          </button>
        ))}
      </div>

      {/* ROOM CARDS GRID */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredRooms.map(room => {
          const { activeBooking, earlyDepBooking, reservedBooking } = getRoomBookingInfo(room.room_number);

          let statusBadge = {
            label: 'Disponibile',
            pill: 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800/60',
            dot: 'bg-emerald-500',
          };

          if (activeBooking) {
            statusBadge = {
              label: 'In-House',
              pill: 'bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800/60',
              dot: 'bg-blue-500',
            };
          } else if (earlyDepBooking) {
            statusBadge = {
              label: 'Early Departure',
              pill: 'bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border-amber-200 dark:border-amber-800/60',
              dot: 'bg-amber-500',
            };
          } else if (reservedBooking) {
            statusBadge = {
              label: 'In Arrivo',
              pill: 'bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 border-indigo-200 dark:border-indigo-800/60',
              dot: 'bg-indigo-500',
            };
          }

          return (
            <div
              key={room.room_number}
              className="bg-white dark:bg-zinc-900 border border-zinc-200/90 dark:border-zinc-800 rounded-xl p-4 transition-all hover:border-zinc-300 dark:hover:border-zinc-700 shadow-[0_1px_2px_rgba(0,0,0,0.03)] flex flex-col justify-between"
            >
              {/* TOP ROW: ROOM NUMBER, CATEGORY & STATUS */}
              <div>
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
                        {room.room_number}
                      </span>
                      <span className="text-[11px] font-medium text-zinc-500 dark:text-zinc-400">
                        Piano {room.floor}
                      </span>
                    </div>
                    <div className="text-xs font-medium text-zinc-700 dark:text-zinc-300 mt-0.5">
                      {room.name}
                    </div>
                  </div>

                  <span className={`inline-flex items-center gap-1.5 text-[11px] font-medium px-2 py-0.5 rounded-md border ${statusBadge.pill}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${statusBadge.dot}`}></span>
                    {statusBadge.label}
                  </span>
                </div>

                {/* RATE & AMENITIES */}
                <div className="mt-2.5 flex items-center justify-between text-xs text-zinc-500 dark:text-zinc-400 pt-2 border-t border-zinc-100 dark:border-zinc-800/60">
                  <span>Tariffa standard:</span>
                  <span className="font-semibold text-zinc-900 dark:text-zinc-200">
                    €{room.price_per_night} / notte
                  </span>
                </div>

                {/* FEATURES TAGS */}
                <div className="mt-2 flex flex-wrap gap-1">
                  {room.features.slice(0, 2).map((feat, idx) => (
                    <span 
                      key={idx} 
                      className="text-[10px] text-zinc-600 dark:text-zinc-400 bg-zinc-100 dark:bg-zinc-800 px-2 py-0.5 rounded font-normal"
                    >
                      {feat}
                    </span>
                  ))}
                </div>
              </div>

              {/* OCCUPANT / BOOKING STATE CONTAINER */}
              <div className="mt-3.5 pt-3 border-t border-zinc-100 dark:border-zinc-800/80">
                {activeBooking && (
                  <div className="p-3 rounded-lg bg-zinc-50 dark:bg-zinc-800/50 border border-zinc-200/80 dark:border-zinc-700/60 space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5 font-medium text-zinc-900 dark:text-zinc-100 text-xs">
                        <User className="w-3.5 h-3.5 text-zinc-500 dark:text-zinc-400" />
                        <span className="truncate max-w-[140px]">{activeBooking.guest_name}</span>
                      </div>
                      <span className="text-[10px] font-mono font-medium text-zinc-500 dark:text-zinc-400 bg-zinc-200/70 dark:bg-zinc-700/60 px-1.5 py-0.5 rounded">
                        {activeBooking.reference_code}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-zinc-500 dark:text-zinc-400">
                      <span>Fino al {activeBooking.check_out_date}</span>
                      <span>{activeBooking.guests_count} {activeBooking.guests_count === 1 ? 'ospite' : 'ospiti'}</span>
                    </div>

                    {activeBooking.special_requests && (
                      <p className="text-[11px] text-zinc-600 dark:text-zinc-300 italic line-clamp-1 border-t border-zinc-200/60 dark:border-zinc-700/40 pt-1">
                        "{activeBooking.special_requests}"
                      </p>
                    )}

                    <div className="pt-1 flex items-center justify-between gap-2">
                      <button
                        onClick={() => onSelectBooking(activeBooking)}
                        className="text-[11px] text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white font-medium flex items-center gap-0.5 cursor-pointer"
                      >
                        Vedi Folio <ChevronRight className="w-3 h-3" />
                      </button>

                      <button
                        onClick={() => onOpenEarlyDeparture(activeBooking)}
                        className="text-[11px] px-2 py-1 rounded bg-amber-50 hover:bg-amber-100 dark:bg-amber-950/40 dark:hover:bg-amber-900/60 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800/60 font-medium cursor-pointer transition-colors"
                      >
                        Partenza Anticipata
                      </button>
                    </div>
                  </div>
                )}

                {earlyDepBooking && (
                  <div className="p-3 rounded-lg bg-amber-50/60 dark:bg-amber-950/20 border border-amber-200/80 dark:border-amber-900/40 space-y-1.5 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-amber-900 dark:text-amber-200 flex items-center gap-1 text-[11px]">
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
                        Partenza Anticipata Registrata
                      </span>
                      <span className="text-[10px] font-mono text-amber-700 dark:text-amber-300">
                        {earlyDepBooking.reference_code}
                      </span>
                    </div>
                    <div className="text-[11px] text-zinc-700 dark:text-zinc-300">
                      Ospite: <strong>{earlyDepBooking.guest_name}</strong>
                    </div>
                    {earlyDepBooking.early_departure_reason && (
                      <div className="text-[11px] text-zinc-600 dark:text-zinc-400 italic">
                        Motivo: {earlyDepBooking.early_departure_reason}
                      </div>
                    )}
                    <div className="text-[10px] text-emerald-700 dark:text-emerald-400 pt-1 font-medium flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> Camera rilasciata per riassegnazione
                    </div>
                  </div>
                )}

                {reservedBooking && !activeBooking && (
                  <div className="p-3 rounded-lg bg-indigo-50/60 dark:bg-indigo-950/20 border border-indigo-200/80 dark:border-indigo-900/40 space-y-1.5 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-indigo-900 dark:text-indigo-200">
                        Arrivo: {reservedBooking.guest_name}
                      </span>
                      <span className="text-[10px] font-mono text-indigo-700 dark:text-indigo-300">
                        {reservedBooking.reference_code}
                      </span>
                    </div>
                    <div className="text-[11px] text-zinc-600 dark:text-zinc-400 flex justify-between">
                      <span>Dal {reservedBooking.check_in_date} ({reservedBooking.nights} {reservedBooking.nights === 1 ? 'notte' : 'notti'})</span>
                      <span>{reservedBooking.guests_count} ospiti</span>
                    </div>
                  </div>
                )}

                {!activeBooking && !earlyDepBooking && !reservedBooking && (
                  <div className="p-2.5 rounded-lg bg-zinc-50 dark:bg-zinc-800/40 border border-zinc-200/60 dark:border-zinc-800 flex items-center justify-between text-xs">
                    <span className="flex items-center gap-1.5 text-zinc-500 dark:text-zinc-400 text-[11px]">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                      Pronta per nuovo arrivo
                    </span>
                    <button
                      onClick={onOpenNewBooking}
                      className="text-[11px] text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white font-medium cursor-pointer"
                    >
                      Assegna
                    </button>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
