import React, { useState } from 'react';
import { 
  BedDouble, 
  User, 
  Calendar, 
  AlertTriangle, 
  CheckCircle2, 
  Plus, 
  Layers,
  Sparkles,
  ChevronRight
} from 'lucide-react';

export default function RoomRack({ rooms, bookings, onOpenNewBooking, onOpenEarlyDeparture, onSelectBooking }) {
  const [selectedFloor, setSelectedFloor] = useState('all');
  const [selectedCategory, setSelectedCategory] = useState('all');

  // Group rooms by floor
  const floors = Array.from(new Set(rooms.map(r => r.floor))).sort((a, b) => a - b);

  const filteredRooms = rooms.filter(room => {
    if (selectedFloor !== 'all' && room.floor !== parseInt(selectedFloor)) return false;
    if (selectedCategory !== 'all' && room.category !== selectedCategory) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* HEADER & FILTER TOOLBAR */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <BedDouble className="w-5 h-5 text-amber-400" />
            Room Rack & Occupancy Matrix
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Mappa operativa delle camere dell'hotel con monitoraggio in tempo reale degli ospiti alloggiati e delle partenze anticipate.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Floor filter */}
          <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-1 text-xs">
            <span className="text-slate-400 px-2 py-1 flex items-center gap-1 font-medium text-[11px]">
              <Layers className="w-3.5 h-3.5 text-slate-400" /> Piano:
            </span>
            <button
              onClick={() => setSelectedFloor('all')}
              className={`px-2.5 py-1 rounded-md transition-colors cursor-pointer text-[11px] ${
                selectedFloor === 'all' ? 'bg-amber-500/20 text-amber-300 font-bold' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Tutti
            </button>
            {floors.map(f => (
              <button
                key={f}
                onClick={() => setSelectedFloor(f.toString())}
                className={`px-2.5 py-1 rounded-md transition-colors cursor-pointer text-[11px] ${
                  selectedFloor === f.toString() ? 'bg-amber-500/20 text-amber-300 font-bold' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                P{f}
              </button>
            ))}
          </div>

          {/* New Reservation Action */}
          <button
            onClick={onOpenNewBooking}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs shadow-md shadow-amber-950/40 transition-all cursor-pointer"
          >
            <Plus className="w-4 h-4" /> Nuova Prenotazione
          </button>
        </div>
      </div>

      {/* ROOM CARDS GRID */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredRooms.map(room => {
          // Identify booking status for this room
          const activeBooking = bookings.find(
            b => b.room_number === room.room_number && b.status === 'checked_in'
          );
          const earlyDepBooking = bookings.find(
            b => b.room_number === room.room_number && b.status === 'early_departure'
          );
          const reservedBooking = bookings.find(
            b => b.room_number === room.room_number && b.status === 'confirmed'
          );

          let statusBadge = {
            label: 'Disponibile',
            pill: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
            indicator: 'bg-emerald-400',
            bgGlow: 'border-slate-800 hover:border-slate-700'
          };

          if (activeBooking) {
            statusBadge = {
              label: 'In-House (Occupata)',
              pill: 'bg-sky-500/15 text-sky-300 border-sky-500/30',
              indicator: 'bg-sky-400',
              bgGlow: 'border-sky-900/40 bg-gradient-to-br from-slate-900 via-slate-900 to-sky-950/20'
            };
          } else if (earlyDepBooking) {
            statusBadge = {
              label: 'Early Departure (Libera)',
              pill: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
              indicator: 'bg-amber-400',
              bgGlow: 'border-amber-800/40 bg-gradient-to-br from-slate-900 via-slate-900 to-amber-950/20'
            };
          } else if (reservedBooking) {
            statusBadge = {
              label: 'Prenotata (Arrivo)',
              pill: 'bg-purple-500/15 text-purple-300 border-purple-500/30',
              indicator: 'bg-purple-400',
              bgGlow: 'border-purple-900/40 bg-gradient-to-br from-slate-900 via-slate-900 to-purple-950/20'
            };
          }

          return (
            <div
              key={room.room_number}
              className={`rounded-2xl border p-5 transition-all shadow-md relative overflow-hidden flex flex-col justify-between ${statusBadge.bgGlow}`}
            >
              {/* TOP ROW: ROOM NUMBER & STATUS PILL */}
              <div>
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-serif-luxury text-2xl font-bold text-amber-100">
                        {room.room_number}
                      </span>
                      <span className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 font-mono">
                        Piano {room.floor}
                      </span>
                    </div>
                    <div className="text-xs font-semibold text-amber-300/90 mt-1">
                      {room.name}
                    </div>
                  </div>

                  <span className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full border flex items-center gap-1.5 ${statusBadge.pill}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${statusBadge.indicator}`}></span>
                    {statusBadge.label}
                  </span>
                </div>

                {/* RATE & CAPACITY */}
                <div className="mt-3 flex items-center justify-between text-xs text-slate-400 border-t border-slate-800/60 pt-2.5">
                  <span>Tariffa Giornaliera:</span>
                  <span className="font-bold text-slate-200">€{room.price_per_night} / notte</span>
                </div>

                {/* FEATURES CHIPS */}
                <div className="mt-2 flex flex-wrap gap-1">
                  {room.features.slice(0, 2).map((feat, idx) => (
                    <span key={idx} className="text-[10px] text-slate-400 bg-slate-800/60 px-2 py-0.5 rounded border border-slate-700/50">
                      {feat}
                    </span>
                  ))}
                </div>
              </div>

              {/* OCCUPANT CARD / STATUS */}
              <div className="mt-4 pt-3 border-t border-slate-800">
                {activeBooking && (
                  <div className="p-3 rounded-xl bg-sky-950/40 border border-sky-800/40 space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5 font-semibold text-sky-200 text-xs">
                        <User className="w-3.5 h-3.5 text-sky-400" />
                        <span>{activeBooking.guest_name}</span>
                      </div>
                      <span className="text-[10px] font-mono text-sky-300/80 bg-sky-900/40 px-1.5 py-0.5 rounded">
                        {activeBooking.reference_code}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-slate-400">
                      <span>Fino al {activeBooking.check_out_date}</span>
                      <span>{activeBooking.guests_count} ospiti</span>
                    </div>

                    {activeBooking.special_requests && (
                      <p className="text-[10px] text-amber-200/90 italic line-clamp-1 border-t border-sky-800/30 pt-1">
                        "{activeBooking.special_requests}"
                      </p>
                    )}

                    <div className="pt-1 flex items-center justify-between">
                      <button
                        onClick={() => onSelectBooking(activeBooking)}
                        className="text-[11px] text-sky-300 hover:text-sky-100 flex items-center gap-0.5 cursor-pointer font-medium"
                      >
                        Visualizza Dettagli <ChevronRight className="w-3 h-3" />
                      </button>

                      <button
                        onClick={() => onOpenEarlyDeparture(activeBooking)}
                        className="text-[10px] px-2 py-1 rounded bg-amber-500/20 text-amber-300 hover:bg-amber-500/30 border border-amber-500/40 font-semibold cursor-pointer transition-colors"
                      >
                        Partenza Anticipata
                      </button>
                    </div>
                  </div>
                )}

                {earlyDepBooking && (
                  <div className="p-3 rounded-xl bg-amber-950/30 border border-amber-800/40 space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-amber-200 flex items-center gap-1">
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-400" /> Partito in Anticipo
                      </span>
                      <span className="text-[10px] font-mono text-amber-400">
                        {earlyDepBooking.reference_code}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-300">
                      Ospite: <strong>{earlyDepBooking.guest_name}</strong>
                    </div>
                    {earlyDepBooking.early_departure_reason && (
                      <div className="text-[10px] text-amber-300/80 italic">
                        Motivo: {earlyDepBooking.early_departure_reason}
                      </div>
                    )}
                    <div className="text-[10px] text-slate-400 pt-1 flex justify-between">
                      <span>Camera rilasciata</span>
                      <span className="text-emerald-400 font-semibold">✓ In pulizia per riassegnazione</span>
                    </div>
                  </div>
                )}

                {reservedBooking && !activeBooking && (
                  <div className="p-3 rounded-xl bg-purple-950/30 border border-purple-800/40 space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-purple-200">
                        Arrivo: {reservedBooking.guest_name}
                      </span>
                      <span className="text-[10px] font-mono text-purple-300">
                        {reservedBooking.reference_code}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 flex justify-between">
                      <span>Dal {reservedBooking.check_in_date} ({reservedBooking.nights} notti)</span>
                      <span>{reservedBooking.guests_count} ospiti</span>
                    </div>
                  </div>
                )}

                {!activeBooking && !earlyDepBooking && !reservedBooking && (
                  <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
                    <span className="flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      Pronta per nuovo check-in
                    </span>
                    <span className="text-[10px] text-emerald-400 font-bold bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-500/30">
                      Pulita
                    </span>
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
