import React, { useState, useEffect } from 'react';
import { 
  Building2, 
  Calendar, 
  Phone, 
  User, 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  Sparkles, 
  Search, 
  Plus, 
  BedDouble, 
  LogOut, 
  Heart, 
  ShieldAlert, 
  UtensilsCrossed, 
  Car, 
  Wine, 
  Send, 
  RefreshCw,
  Bell,
  Check,
  ChevronRight,
  TrendingUp,
  MapPin
} from 'lucide-react';

const API_BASE = '/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview'); // overview, bookings, crm, voice, alerts
  const [rooms, setRooms] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [stats, setStats] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchFilter, setSearchFilter] = useState('');

  // Voice Simulator state
  const [selectedCallerPhone, setSelectedCallerPhone] = useState('+39 333 1112233');
  const [callerName, setCallerName] = useState('Marco Rossi');
  const [callSessionId, setCallSessionId] = useState(() => 'call_' + Math.random().toString(36).substring(7));
  const [callHistory, setCallHistory] = useState([
    {
      role: 'assistant',
      content: 'Buongiorno, sono l\'assistente AI di Sina Hotels. Come posso aiutarLa?'
    }
  ]);
  const [userSpeechInput, setUserSpeechInput] = useState('');
  const [isCalling, setIsCalling] = useState(false);

  // Early Departure Modal state
  const [earlyDepModal, setEarlyDepModal] = useState({ isOpen: false, booking: null, reason: '' });

  // New Booking Modal state
  const [newBookingModal, setNewBookingModal] = useState({
    isOpen: false,
    guest_name: '',
    guest_phone: '',
    category: 'deluxe',
    check_in_date: '',
    check_out_date: '',
    guests_count: 2,
    special_requests: ''
  });

  const fetchData = async () => {
    try {
      const [roomsRes, bookingsRes, statsRes, notifsRes] = await Promise.all([
        fetch(`${API_BASE}/rooms`),
        fetch(`${API_BASE}/room-bookings`),
        fetch(`${API_BASE}/hotel-stats`),
        fetch(`${API_BASE}/notifications`)
      ]);

      if (roomsRes.ok) setRooms(await roomsRes.json());
      if (bookingsRes.ok) setBookings(await bookingsRes.json());
      if (statsRes.ok) setStats(await statsRes.json());
      if (notifsRes.ok) setNotifications(await notifsRes.json());
    } catch (err) {
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 8000);
    return () => clearInterval(interval);
  }, []);

  // Update caller context when preset selected
  const handleSelectPresetCaller = async (phone, name) => {
    setSelectedCallerPhone(phone);
    setCallerName(name);
    setCallSessionId('call_' + Math.random().toString(36).substring(7));
    try {
      const res = await fetch(`${API_BASE}/crm/caller-context?phone=${encodeURIComponent(phone)}`);
      if (res.ok) {
        const data = await res.json();
        setCallHistory([
          {
            role: 'assistant',
            content: data.suggested_greeting_it || 'Buongiorno, sono l\'assistente AI di Sina Hotels. Come posso aiutarLa?'
          }
        ]);
      }
    } catch {
      setCallHistory([
        {
          role: 'assistant',
          content: 'Buongiorno, sono l\'assistente AI di Sina Hotels. Come posso aiutarLa?'
        }
      ]);
    }
  };

  // Send message to agent
  const handleSendMessage = async (customText = null) => {
    const textToSend = customText || userSpeechInput;
    if (!textToSend.trim()) return;

    const newMessages = [...callHistory, { role: 'user', content: textToSend }];
    setCallHistory(newMessages);
    setUserSpeechInput('');
    setIsCalling(true);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: callSessionId,
          message: textToSend,
          caller_phone: selectedCallerPhone,
          caller_name: callerName,
          hotel_name: 'Sina Bernini Bristol'
        })
      });

      if (res.ok) {
        const data = await res.json();
        setCallHistory([...newMessages, { role: 'assistant', content: data.response }]);
        // Refresh CRM data as booking/early departure may have occurred
        fetchData();
      } else {
        setCallHistory([
          ...newMessages,
          { role: 'assistant', content: 'Mi scusi, si è verificato un errore di connessione con il centralino.' }
        ]);
      }
    } catch {
      setCallHistory([
        ...newMessages,
        { role: 'assistant', content: 'Servizio momentaneamente non raggiungibile.' }
      ]);
    } finally {
      setIsCalling(false);
    }
  };

  // Handle Early Departure submission
  const submitEarlyDeparture = async () => {
    if (!earlyDepModal.booking) return;
    try {
      const res = await fetch(`${API_BASE}/room-bookings/early-departure`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          reference_code: earlyDepModal.booking.reference_code,
          guest_phone: earlyDepModal.booking.guest_phone,
          reason: earlyDepModal.reason || 'Partenza anticipata richiesta dall\'ospite'
        })
      });
      if (res.ok) {
        setEarlyDepModal({ isOpen: false, booking: null, reason: '' });
        fetchData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Handle New Booking creation
  const submitNewBooking = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/room-bookings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newBookingModal)
      });
      if (res.ok) {
        setNewBookingModal({
          isOpen: false,
          guest_name: '',
          guest_phone: '',
          category: 'deluxe',
          check_in_date: '',
          check_out_date: '',
          guests_count: 2,
          special_requests: ''
        });
        fetchData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Filtered bookings
  const filteredBookings = bookings.filter(b => {
    const q = searchFilter.toLowerCase();
    return (
      b.guest_name.toLowerCase().includes(q) ||
      b.reference_code.toLowerCase().includes(q) ||
      b.room_number.toLowerCase().includes(q) ||
      b.status.toLowerCase().includes(q)
    );
  });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* TOP HEADER */}
      <header className="border-b border-amber-900/30 bg-slate-900/80 backdrop-blur-md sticky top-0 z-40 px-6 py-4">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-lg bg-gradient-to-br from-amber-400 to-amber-700 flex items-center justify-center shadow-lg shadow-amber-900/20 border border-amber-300/40">
              <Building2 className="w-6 h-6 text-slate-950 font-bold" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-serif-luxury text-xl font-bold tracking-wider text-amber-200">
                  SINA HOTELS
                </span>
                <span className="text-xs px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/30">
                  5★ Lusso
                </span>
              </div>
              <p className="text-xs text-slate-400 flex items-center gap-1">
                <MapPin className="w-3 h-3 text-amber-400" /> Sina Bernini Bristol — Piazza Barberini, Roma
              </p>
            </div>
          </div>

          {/* AI VOICE STATUS & REFRESH */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 text-xs shadow-inner">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>Voice AI Receptionist Attivo 24/7</span>
            </div>

            <button 
              onClick={fetchData} 
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors border border-slate-700/60"
              title="Aggiorna Dati"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* NAVIGATION TABS */}
        <div className="max-w-7xl mx-auto mt-4 flex items-center gap-2 overflow-x-auto pb-1">
          {[
            { id: 'overview', label: 'Camere & Occupazione', icon: BedDouble },
            { id: 'bookings', label: 'Prenotazioni & Early Departures', icon: Calendar },
            { id: 'crm', label: 'Guest 360 & Preferenze', icon: User },
            { id: 'voice', label: 'Simulatore Chiamata AI', icon: Phone },
            { id: 'alerts', label: 'Alert Staff & Cucina', icon: Bell, count: notifications.filter(n => !n.is_read).length },
          ].map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all cursor-pointer whitespace-nowrap ${
                  isActive 
                    ? 'bg-amber-500/20 text-amber-200 border border-amber-500/50 shadow-md shadow-amber-950/30' 
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-amber-400' : 'text-slate-400'}`} />
                <span>{tab.label}</span>
                {tab.count > 0 && (
                  <span className="ml-1 px-1.5 py-0.2 text-[10px] rounded-full bg-rose-500 text-white font-bold">
                    {tab.count}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </header>

      {/* MAIN CONTAINER */}
      <main className="max-w-7xl mx-auto w-full p-6 flex-1">
        
        {/* KPI OVERVIEW CARDS */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl">
              <span className="text-xs text-slate-400 font-medium">Totale Camere Hotel</span>
              <div className="text-2xl font-bold text-slate-100 mt-1 flex items-baseline justify-between">
                <span>{stats.total_rooms}</span>
                <span className="text-xs text-amber-400 font-normal">Sina Inventory</span>
              </div>
            </div>

            <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl">
              <span className="text-xs text-slate-400 font-medium">Ospiti In-House Attivi</span>
              <div className="text-2xl font-bold text-sky-400 mt-1 flex items-baseline justify-between">
                <span>{stats.in_house_guests_count}</span>
                <span className="text-xs text-slate-400 font-normal">Occupazione {stats.occupancy_rate_percentage}%</span>
              </div>
            </div>

            <div className="bg-slate-900/60 border border-amber-800/40 p-4 rounded-xl bg-gradient-to-br from-slate-900/60 to-amber-950/20">
              <span className="text-xs text-amber-300 font-medium flex items-center gap-1">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400" /> Partenze Anticipate
              </span>
              <div className="text-2xl font-bold text-amber-300 mt-1 flex items-baseline justify-between">
                <span>{stats.early_departures_count}</span>
                <span className="text-[11px] text-amber-400/80 font-normal">Camere Rilasciate</span>
              </div>
            </div>

            <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl">
              <span className="text-xs text-slate-400 font-medium">Arrivi & Partenze Oggi</span>
              <div className="text-2xl font-bold text-emerald-400 mt-1 flex items-baseline justify-between">
                <span>{stats.arrivals_today_count} in / {stats.departures_today_count} out</span>
                <span className="text-xs text-slate-400 font-normal">Oggi</span>
              </div>
            </div>
          </div>
        )}

        {/* TAB 1: ROOMS OCCUPANCY GRID */}
        {activeTab === 'overview' && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                  <BedDouble className="w-5 h-5 text-amber-400" />
                  Stato Camere in Tempo Reale
                </h2>
                <p className="text-xs text-slate-400">
                  Mappa visiva delle 9 camere d'élite con visualizzazione immediata di chi occupa la camera o è partito in anticipo.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setNewBookingModal({ ...newBookingModal, isOpen: true })}
                  className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold text-xs shadow-md shadow-amber-900/30 transition-all cursor-pointer"
                >
                  <Plus className="w-4 h-4" /> Nuova Prenotazione
                </button>
              </div>
            </div>

            {/* ROOMS GRID */}
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {rooms.map(room => {
                // Find if an active booking occupies this room
                const activeBooking = bookings.find(
                  b => b.room_number === room.room_number && b.status === 'checked_in'
                );
                const earlyDepBooking = bookings.find(
                  b => b.room_number === room.room_number && b.status === 'early_departure'
                );
                const upcomingBooking = bookings.find(
                  b => b.room_number === room.room_number && b.status === 'confirmed'
                );

                let statusBadge = { label: 'Disponibile', color: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30' };
                if (activeBooking) {
                  statusBadge = { label: 'In-House (Occupata)', color: 'bg-sky-500/20 text-sky-300 border-sky-500/40' };
                } else if (earlyDepBooking) {
                  statusBadge = { label: 'Early Departure (Libera)', color: 'bg-amber-500/20 text-amber-300 border-amber-500/40' };
                } else if (upcomingBooking) {
                  statusBadge = { label: 'Prenotata (Arrivo)', color: 'bg-purple-500/20 text-purple-300 border-purple-500/40' };
                }

                return (
                  <div
                    key={room.room_number}
                    className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-all shadow-md relative overflow-hidden"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-serif-luxury text-2xl font-bold text-amber-100">
                            Camera {room.room_number}
                          </span>
                          <span className="text-[11px] text-slate-400 font-mono">Piano {room.floor}</span>
                        </div>
                        <p className="text-xs text-amber-300/90 font-medium mt-0.5">{room.name}</p>
                      </div>

                      <span className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full border ${statusBadge.color}`}>
                        {statusBadge.label}
                      </span>
                    </div>

                    <div className="mt-4 pt-3 border-t border-slate-800/80">
                      <div className="flex justify-between items-center text-xs mb-2">
                        <span className="text-slate-400">Tariffa Giornaliera:</span>
                        <span className="font-bold text-slate-200">€{room.price_per_night}/notte</span>
                      </div>

                      {/* OCCUPANT DETAILS */}
                      {activeBooking && (
                        <div className="p-2.5 rounded-lg bg-sky-950/40 border border-sky-800/40 text-xs">
                          <div className="font-semibold text-sky-200 flex items-center justify-between">
                            <span>👤 {activeBooking.guest_name}</span>
                            <span className="text-[10px] text-sky-400 font-mono">{activeBooking.reference_code}</span>
                          </div>
                          <div className="text-[11px] text-slate-400 mt-1 flex justify-between">
                            <span>Fino al {activeBooking.check_out_date}</span>
                            <span>{activeBooking.guests_count} ospiti</span>
                          </div>
                          {activeBooking.special_requests && (
                            <p className="text-[10px] text-amber-300/80 mt-1 italic line-clamp-1">
                              "{activeBooking.special_requests}"
                            </p>
                          )}
                        </div>
                      )}

                      {earlyDepBooking && (
                        <div className="p-2.5 rounded-lg bg-amber-950/40 border border-amber-800/40 text-xs">
                          <div className="font-semibold text-amber-200 flex items-center justify-between">
                            <span>⚠️ Partito in Anticipo</span>
                            <span className="text-[10px] text-amber-400 font-mono">{earlyDepBooking.reference_code}</span>
                          </div>
                          <p className="text-[11px] text-slate-300 mt-1">
                            Ospite: {earlyDepBooking.guest_name}
                          </p>
                          <p className="text-[10px] text-amber-300 mt-0.5 italic">
                            Motivo: {earlyDepBooking.early_departure_reason}
                          </p>
                        </div>
                      )}

                      {!activeBooking && !earlyDepBooking && (
                        <div className="p-2.5 rounded-lg bg-slate-800/40 border border-slate-700/30 text-xs text-slate-400 flex items-center justify-between">
                          <span>Pronta e disponibile per check-in</span>
                          <span className="text-emerald-400 font-bold">✓ Pulita</span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* TAB 2: BOOKINGS & EARLY DEPARTURES */}
        {activeTab === 'bookings' && (
          <div>
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
              <div>
                <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-amber-400" />
                  Registro Prenotazioni & Partenze Anticipate
                </h2>
                <p className="text-xs text-slate-400">
                  Controllo completo su chi ha prenotato, chi è in struttura e chi ha lasciato la camera in anticipo.
                </p>
              </div>

              <div className="flex items-center gap-3">
                <div className="relative">
                  <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                  <input
                    type="text"
                    value={searchFilter}
                    onChange={(e) => setSearchFilter(e.target.value)}
                    placeholder="Cerca ospite, codice o camera..."
                    className="pl-9 pr-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-amber-400 w-64"
                  />
                </div>

                <button
                  onClick={() => setNewBookingModal({ ...newBookingModal, isOpen: true })}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold text-xs shadow-md"
                >
                  <Plus className="w-4 h-4" /> Aggiungi
                </button>
              </div>
            </div>

            {/* TABLE */}
            <div className="bg-slate-900/70 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800/60 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-700/60">
                  <tr>
                    <th className="py-3 px-4">Codice</th>
                    <th className="py-3 px-4">Ospite & Telefono</th>
                    <th className="py-3 px-4">Camera & Tipo</th>
                    <th className="py-3 px-4">Date Soggiorno</th>
                    <th className="py-3 px-4">Totale</th>
                    <th className="py-3 px-4">Stato</th>
                    <th className="py-3 px-4">Azioni</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {filteredBookings.map(b => (
                    <tr key={b.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3 px-4 font-mono font-bold text-amber-300">
                        {b.reference_code}
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-semibold text-slate-100">{b.guest_name}</div>
                        <div className="text-[11px] text-slate-400">{b.guest_phone}</div>
                      </td>
                      <td className="py-3 px-4">
                        <span className="font-bold text-slate-200">Cam. {b.room_number}</span>
                        <div className="text-[11px] text-slate-400 capitalize">{b.room_category.replace('_', ' ')}</div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="text-slate-200">{b.check_in_date} → {b.check_out_date}</div>
                        <div className="text-[11px] text-slate-400">{b.nights} notti • {b.guests_count} ospiti</div>
                      </td>
                      <td className="py-3 px-4 font-bold text-slate-200">
                        €{b.total_price.toFixed(2)}
                      </td>
                      <td className="py-3 px-4">
                        {b.status === 'checked_in' && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-sky-500/20 text-sky-300 border border-sky-500/40">
                            In-House
                          </span>
                        )}
                        {b.status === 'early_departure' && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/40 flex items-center gap-1 w-max">
                            <AlertTriangle className="w-3 h-3" /> Early Departure
                          </span>
                        )}
                        {b.status === 'confirmed' && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/40">
                            Confermata
                          </span>
                        )}
                        {b.status === 'checked_out' && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-700 text-slate-300">
                            Terminata
                          </span>
                        )}
                        {b.status === 'cancelled' && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/40">
                            Cancellata
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        {b.status === 'checked_in' && (
                          <button
                            onClick={() => setEarlyDepModal({ isOpen: true, booking: b, reason: '' })}
                            className="px-2.5 py-1 rounded bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 text-[11px] transition-colors"
                          >
                            Partenza Anticipata
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 3: GUEST 360 CRM */}
        {activeTab === 'crm' && (
          <div>
            <div className="mb-4">
              <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                <User className="w-5 h-5 text-amber-400" />
                Sina Guest 360 & Intelligence CRM
              </h2>
              <p className="text-xs text-slate-400">
                Profili dettagliati degli ospiti con preferenze dietetiche, allergie, abitudini in camera e note comportamentali.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Marco Rossi */}
              <div className="bg-slate-900/80 border border-amber-500/40 rounded-xl p-5 shadow-lg relative">
                <div className="absolute top-4 right-4">
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500 text-slate-950">
                    VIP GOLD
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-amber-500/20 flex items-center justify-center font-bold text-amber-300 border border-amber-500/40">
                    MR
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-100">Marco Rossi</h3>
                    <p className="text-xs text-slate-400">+39 333 1112233</p>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800 space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Stato:</span>
                    <span className="font-semibold text-sky-300">In-House (Camera 402)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Occasione:</span>
                    <span className="font-semibold text-rose-300 flex items-center gap-1">
                      <Heart className="w-3 h-3 text-rose-400 fill-rose-400" /> 10° Anniversario Nozze
                    </span>
                  </div>

                  <div className="p-2.5 rounded-lg bg-rose-950/30 border border-rose-800/40 mt-2">
                    <span className="text-[11px] font-bold text-rose-300 flex items-center gap-1">
                      <ShieldAlert className="w-3.5 h-3.5 text-rose-400" /> Allerta Allergia / Dieta
                    </span>
                    <p className="text-[11px] text-slate-300 mt-1">
                      Signora Giulia: <strong>Celiachia rigorosa</strong> (senza glutine). Avvisare sempre cucina e sala.
                    </p>
                  </div>

                  <div className="p-2.5 rounded-lg bg-slate-800/50 text-[11px] space-y-1 text-slate-300">
                    <div className="flex items-center gap-1.5">
                      <Wine className="w-3.5 h-3.5 text-amber-400" />
                      <span>Preferenza: Franciacorta Brut</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <BedDouble className="w-3.5 h-3.5 text-sky-400" />
                      <span>Camera: Piano alto, cuscini anallergici</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Andrea Moretti */}
              <div className="bg-slate-900/80 border border-purple-500/40 rounded-xl p-5 shadow-lg relative">
                <div className="absolute top-4 right-4">
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-purple-500 text-white">
                    SINA PRIVILEGE
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-purple-500/20 flex items-center justify-center font-bold text-purple-300 border border-purple-500/40">
                    AM
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-100">Andrea Moretti</h3>
                    <p className="text-xs text-slate-400">+39 335 9988776</p>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800 space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Stato:</span>
                    <span className="font-semibold text-purple-300">Pre-Stay (Arrivo Domani)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Persona:</span>
                    <span className="font-semibold text-slate-300">Business Solo (Finanza)</span>
                  </div>

                  <div className="p-2.5 rounded-lg bg-slate-800/50 text-[11px] space-y-1 text-slate-300 mt-2">
                    <div className="flex items-center gap-1.5">
                      <Car className="w-3.5 h-3.5 text-amber-400" />
                      <span>Transfer: Limousine Mercedes NCC Fiumicino</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      <span>Wi-Fi premium e scrivania ergonomica</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Roberto Ferri - Early Departure */}
              <div className="bg-slate-900/80 border border-amber-600/40 rounded-xl p-5 shadow-lg relative">
                <div className="absolute top-4 right-4">
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">
                    EARLY DEPARTURE
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-amber-500/20 flex items-center justify-center font-bold text-amber-300 border border-amber-500/40">
                    RF
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-100">Roberto Ferri</h3>
                    <p className="text-xs text-slate-400">+39 347 1234567</p>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800 space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Camera Assegnata:</span>
                    <span className="font-semibold text-slate-200">Camera 101</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Partito il:</span>
                    <span className="font-semibold text-amber-400">Oggi (Anticipato)</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-amber-950/30 border border-amber-800/40 mt-2 text-[11px] text-amber-200/90">
                    <strong>Motivo registrato:</strong> Imprevisto urgente lavorativo a Milano. Conto ricalcolato e camera inviata a pulizia.
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: LIVE VOICE AI AGENT SIMULATOR */}
        {activeTab === 'voice' && (
          <div className="max-w-3xl mx-auto">
            <div className="bg-slate-900 border border-amber-500/30 rounded-2xl p-6 shadow-2xl relative overflow-hidden">
              <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-amber-500/20 flex items-center justify-center text-amber-400 border border-amber-500/40 animate-pulse">
                    <Phone className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="font-bold text-slate-100">Simulatore Chiamata Centralino Sina Hotels</h2>
                    <p className="text-xs text-slate-400">Testa l'agente vocale formale ("dare del Lei") collegato al CRM</p>
                  </div>
                </div>

                <span className="text-xs px-2.5 py-1 rounded bg-emerald-950 border border-emerald-500/40 text-emerald-300 font-mono">
                  Linea Aperta
                </span>
              </div>

              {/* CALLER SELECTOR PRESETS */}
              <div className="mb-4">
                <span className="text-xs text-slate-400 block mb-2 font-medium">Seleziona Chiamante di Prova:</span>
                <div className="flex flex-wrap gap-2">
                  {[
                    { name: 'Marco Rossi', phone: '+39 333 1112233', desc: 'In-House Cam. 402 (Anniversario)' },
                    { name: 'Andrea Moretti', phone: '+39 335 9988776', desc: 'Pre-Stay VIP Privilege' },
                    { name: 'Roberto Ferri', phone: '+39 347 1234567', desc: 'Early Departure Cam. 101' },
                    { name: 'Nuovo Ospite', phone: '+39 338 9900112', desc: 'Numero non registrato' },
                  ].map(p => (
                    <button
                      key={p.phone}
                      onClick={() => handleSelectPresetCaller(p.phone, p.name)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium border text-left transition-all cursor-pointer ${
                        selectedCallerPhone === p.phone
                          ? 'bg-amber-500/20 text-amber-200 border-amber-500/60 shadow-md'
                          : 'bg-slate-800/60 text-slate-400 border-slate-700/60 hover:bg-slate-800 hover:text-slate-200'
                      }`}
                    >
                      <div className="font-bold">{p.name}</div>
                      <div className="text-[10px] opacity-75">{p.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* DIALOGUE BUBBLES */}
              <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 h-80 overflow-y-auto mb-4 space-y-3">
                {callHistory.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-xs shadow-md ${
                        msg.role === 'user'
                          ? 'bg-amber-500 text-slate-950 font-medium rounded-tr-none'
                          : 'bg-slate-800 text-slate-200 rounded-tl-none border border-slate-700/60'
                      }`}
                    >
                      <div className="text-[10px] opacity-70 mb-0.5 font-bold">
                        {msg.role === 'user' ? `Ospite (${callerName})` : 'AI Receptionist Sina Hotels'}
                      </div>
                      {msg.content}
                    </div>
                  </div>
                ))}

                {isCalling && (
                  <div className="flex justify-start">
                    <div className="bg-slate-800 text-slate-400 text-xs px-4 py-2 rounded-2xl flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping"></span>
                      <span>L'assistente sta rispondendo...</span>
                    </div>
                  </div>
                )}
              </div>

              {/* QUICK UTTERANCES */}
              <div className="mb-3">
                <span className="text-[11px] text-slate-400 block mb-1">Frasi rapide di prova:</span>
                <div className="flex flex-wrap gap-1.5">
                  {[
                    'Vorrei verificare disponibilità per 2 persone dal 2026-10-25 al 2026-10-27 per una camera Deluxe',
                    'Quali sono le camere disponibili e i prezzi per notte?',
                    'Purtroppo devo partire oggi in anticipo per un impegno urgente di lavoro',
                    'Mia moglie è celiaca, potete assicurarci opzioni senza glutine per la colazione?',
                    'Quali sono gli orari della colazione e del Rooftop The Flair?',
                    'No grazie, tutto a posto così. Arrivederci!'
                  ].map((phrase, i) => (
                    <button
                      key={i}
                      onClick={() => handleSendMessage(phrase)}
                      className="text-[10px] bg-slate-800/80 hover:bg-slate-700 text-slate-300 px-2.5 py-1 rounded-md border border-slate-700/60 text-left transition-colors cursor-pointer"
                    >
                      {phrase}
                    </button>
                  ))}
                </div>
              </div>

              {/* INPUT BAR */}
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSendMessage();
                }}
                className="flex items-center gap-2"
              >
                <input
                  type="text"
                  value={userSpeechInput}
                  onChange={(e) => setUserSpeechInput(e.target.value)}
                  placeholder="Scrivi come se stessi parlando al telefono con l'hotel..."
                  className="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-xs text-slate-100 focus:outline-none focus:border-amber-400 shadow-inner"
                />
                <button
                  type="submit"
                  disabled={isCalling}
                  className="px-4 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs flex items-center gap-1.5 shadow-md shadow-amber-900/30 cursor-pointer disabled:opacity-50"
                >
                  <Send className="w-3.5 h-3.5" /> Invia
                </button>
              </form>
            </div>
          </div>
        )}

        {/* TAB 5: STAFF & KITCHEN ALERTS */}
        {activeTab === 'alerts' && (
          <div>
            <div className="mb-4">
              <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                <Bell className="w-5 h-5 text-amber-400" />
                Centro Notifiche CRM per Ricevimento, Governanti e Cucina
              </h2>
              <p className="text-xs text-slate-400">
                Tutti gli eventi generati dalle telefonate dell'Agente Vocale compaiono istantaneamente qui.
              </p>
            </div>

            <div className="space-y-3">
              {notifications.map(notif => (
                <div
                  key={notif.id}
                  className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex items-start gap-3 hover:border-slate-700 transition-colors"
                >
                  <div className="mt-0.5">
                    {notif.type === 'allergy_alert' && <ShieldAlert className="w-5 h-5 text-rose-400" />}
                    {notif.type === 'new_booking' && <CheckCircle2 className="w-5 h-5 text-emerald-400" />}
                    {notif.type === 'transfer_request' && <Car className="w-5 h-5 text-amber-400" />}
                    {notif.type === 'concierge_request' && <Clock className="w-5 h-5 text-purple-400" />}
                    {!['allergy_alert', 'new_booking', 'transfer_request', 'concierge_request'].includes(notif.type) && (
                      <Bell className="w-5 h-5 text-sky-400" />
                    )}
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-bold text-slate-100">{notif.title}</h4>
                      <span className="text-[10px] text-slate-400">
                        {new Date(notif.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 mt-1">{notif.message}</p>
                    {notif.customer_phone && (
                      <div className="text-[10px] text-slate-400 mt-2 font-mono">
                        Contatto: {notif.customer_name} ({notif.customer_phone})
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

      </main>

      {/* EARLY DEPARTURE MODAL */}
      {earlyDepModal.isOpen && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-amber-500/40 rounded-2xl max-w-md w-full p-6 shadow-2xl">
            <h3 className="text-base font-bold text-amber-200 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
              Segnala Partenza Anticipata (Early Departure)
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Camera {earlyDepModal.booking?.room_number} — {earlyDepModal.booking?.guest_name}
            </p>

            <div className="mt-4">
              <label className="text-xs text-slate-300 block mb-1">Motivo della partenza anticipata:</label>
              <textarea
                value={earlyDepModal.reason}
                onChange={(e) => setEarlyDepModal({ ...earlyDepModal, reason: e.target.value })}
                placeholder="Es. Impegno lavorativo urgente a Milano, emergenza personale..."
                className="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-xs text-slate-200 focus:outline-none focus:border-amber-400 h-24"
              />
            </div>

            <div className="mt-5 flex justify-end gap-2">
              <button
                onClick={() => setEarlyDepModal({ isOpen: false, booking: null, reason: '' })}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold hover:bg-slate-700"
              >
                Annulla
              </button>
              <button
                onClick={submitEarlyDeparture}
                className="px-4 py-2 rounded-xl bg-amber-500 text-slate-950 text-xs font-bold hover:bg-amber-400 shadow-lg shadow-amber-900/30"
              >
                Registra Partenza & Libera Camera
              </button>
            </div>
          </div>
        </div>
      )}

      {/* NEW BOOKING MODAL */}
      {newBookingModal.isOpen && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-amber-500/40 rounded-2xl max-w-lg w-full p-6 shadow-2xl">
            <h3 className="text-base font-bold text-amber-200 flex items-center gap-2">
              <Plus className="w-5 h-5 text-amber-400" />
              Nuova Prenotazione Camera — Sina Bernini Bristol
            </h3>
            <form onSubmit={submitNewBooking} className="mt-4 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] text-slate-300 block mb-1">Nome Ospite</label>
                  <input
                    type="text"
                    required
                    value={newBookingModal.guest_name}
                    onChange={(e) => setNewBookingModal({ ...newBookingModal, guest_name: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100"
                    placeholder="Mario Rossi"
                  />
                </div>
                <div>
                  <label className="text-[11px] text-slate-300 block mb-1">Telefono</label>
                  <input
                    type="text"
                    required
                    value={newBookingModal.guest_phone}
                    onChange={(e) => setNewBookingModal({ ...newBookingModal, guest_phone: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100"
                    placeholder="+39 333 1234567"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] text-slate-300 block mb-1">Data Check-in</label>
                  <input
                    type="date"
                    required
                    value={newBookingModal.check_in_date}
                    onChange={(e) => setNewBookingModal({ ...newBookingModal, check_in_date: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100"
                  />
                </div>
                <div>
                  <label className="text-[11px] text-slate-300 block mb-1">Data Check-out</label>
                  <input
                    type="date"
                    required
                    value={newBookingModal.check_out_date}
                    onChange={(e) => setNewBookingModal({ ...newBookingModal, check_out_date: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] text-slate-300 block mb-1">Categoria Camera</label>
                  <select
                    value={newBookingModal.category}
                    onChange={(e) => setNewBookingModal({ ...newBookingModal, category: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100"
                  >
                    <option value="superior">Camera Superior (€250/n)</option>
                    <option value="deluxe">Camera Deluxe Vista Città (€350/n)</option>
                    <option value="junior_suite">Junior Suite con Balcone (€480/n)</option>
                    <option value="panoramic_suite">Suite Panoramica Barberini (€750/n)</option>
                  </select>
                </div>
                <div>
                  <label className="text-[11px] text-slate-300 block mb-1">Numero Ospiti</label>
                  <input
                    type="number"
                    min="1"
                    max="4"
                    value={newBookingModal.guests_count}
                    onChange={(e) => setNewBookingModal({ ...newBookingModal, guests_count: parseInt(e.target.value) })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100"
                  />
                </div>
              </div>

              <div>
                <label className="text-[11px] text-slate-300 block mb-1">Richieste Speciali / Note</label>
                <input
                  type="text"
                  value={newBookingModal.special_requests}
                  onChange={(e) => setNewBookingModal({ ...newBookingModal, special_requests: e.target.value })}
                  placeholder="Es. Letto matrimoniale, culla, allergie..."
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100"
                />
              </div>

              <div className="mt-5 flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setNewBookingModal({ ...newBookingModal, isOpen: false })}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold hover:bg-slate-700"
                >
                  Annulla
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-amber-500 text-slate-950 text-xs font-bold hover:bg-amber-400 shadow-lg shadow-amber-900/30"
                >
                  Conferma Prenotazione
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
