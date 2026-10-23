import React, { useState, useEffect } from 'react';
import { 
  Building2, 
  Calendar, 
  BedDouble, 
  AlertTriangle, 
  Users, 
  BellRing, 
  RefreshCw, 
  Plus, 
  Search,
  Clock,
  Sparkles,
  TrendingUp,
  ShieldAlert
} from 'lucide-react';

import Sidebar from './components/Sidebar';
import RoomRack from './components/RoomRack';
import ReservationsTable from './components/ReservationsTable';
import Guest360 from './components/Guest360';
import OperationsAlerts from './components/OperationsAlerts';
import EarlyDepartureModal from './components/EarlyDepartureModal';
import NewBookingModal from './components/NewBookingModal';
import BookingDetailDrawer from './components/BookingDetailDrawer';

const API_BASE = '/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('room_rack');
  const [rooms, setRooms] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [stats, setStats] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchFilter, setSearchFilter] = useState('');
  const [lastRefreshed, setLastRefreshed] = useState(new Date());

  // Modal & Drawer states
  const [earlyDepModal, setEarlyDepModal] = useState({ isOpen: false, booking: null });
  const [newBookingModalOpen, setNewBookingModalOpen] = useState(false);
  const [selectedBookingForDrawer, setSelectedBookingForDrawer] = useState(null);

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
      setLastRefreshed(new Date());
    } catch (err) {
      console.error('Error fetching PMS data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Real-time synchronization interval
    const interval = setInterval(fetchData, 6000);
    return () => clearInterval(interval);
  }, []);

  // Handle Early Departure submission
  const handleEarlyDepartureSubmit = async ({ reference_code, guest_phone, reason }) => {
    try {
      const res = await fetch(`${API_BASE}/room-bookings/early-departure`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reference_code, guest_phone, reason })
      });
      if (res.ok) {
        setEarlyDepModal({ isOpen: false, booking: null });
        fetchData();
      }
    } catch (err) {
      console.error('Failed to submit early departure:', err);
    }
  };

  // Handle New Booking creation
  const handleNewBookingSubmit = async (formData) => {
    try {
      const res = await fetch(`${API_BASE}/room-bookings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      if (res.ok) {
        setNewBookingModalOpen(false);
        fetchData();
      }
    } catch (err) {
      console.error('Failed to create new booking:', err);
    }
  };

  // Mark notification as read
  const handleMarkAsRead = async (notificationId) => {
    try {
      const res = await fetch(`${API_BASE}/notifications/${notificationId}/read`, {
        method: 'POST'
      });
      if (res.ok) {
        setNotifications(prev =>
          prev.map(n => n.id === notificationId ? { ...n, is_read: true } : n)
        );
      }
    } catch (err) {
      console.error('Failed to mark notification as read:', err);
    }
  };

  const unreadAlertsCount = notifications.filter(n => !n.is_read).length;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex font-sans antialiased selection:bg-amber-500/30 selection:text-amber-200">
      {/* SIDEBAR NAVIGATION */}
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        unreadAlertsCount={unreadAlertsCount} 
      />

      {/* MAIN PMS DESK AREA */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        {/* TOP STATUS BAR */}
        <header className="h-16 border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-30 px-6 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <h1 className="text-sm font-bold text-slate-200 tracking-wide font-serif-luxury hidden sm:block">
              SINA BERNINI BRISTOL — FRONT DESK PMS
            </h1>
            <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/30">
              Reception Console
            </span>
          </div>

          <div className="flex items-center gap-3">
            {/* Live Sync Timestamp */}
            <div className="hidden md:flex items-center gap-1.5 text-[11px] text-slate-400 font-mono">
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
              <span>Sync: {lastRefreshed.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
            </div>

            {/* Manual Refresh */}
            <button
              onClick={fetchData}
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors border border-slate-700/60 cursor-pointer"
              title="Aggiorna Dati PMS"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>

            {/* Quick New Booking Button */}
            <button
              onClick={() => setNewBookingModalOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs shadow-md shadow-amber-950/40 transition-all cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Nuova Prenotazione</span>
            </button>
          </div>
        </header>

        {/* PMS DASHBOARD CONTENT */}
        <main className="p-6 max-w-7xl w-full mx-auto space-y-6 flex-1">
          {/* HIGH-LEVEL KPI EXECUTIVE METRICS */}
          {stats && (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {/* TOTAL ROOMS */}
              <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-2xl shadow-sm">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                  Totale Camere Hotel
                </span>
                <div className="text-2xl font-bold text-slate-100 font-serif-luxury mt-1 flex items-baseline justify-between">
                  <span>{stats.total_rooms}</span>
                  <span className="text-[11px] text-amber-400 font-normal font-sans">9 Suite & Camere</span>
                </div>
              </div>

              {/* OCCUPANCY */}
              <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-2xl shadow-sm">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                  Ospiti In-House
                </span>
                <div className="text-2xl font-bold text-sky-400 font-serif-luxury mt-1 flex items-baseline justify-between">
                  <span>{stats.in_house_guests_count}</span>
                  <span className="text-[11px] text-sky-300 font-normal font-sans">
                    Occupazione {stats.occupancy_rate_percentage}%
                  </span>
                </div>
              </div>

              {/* EARLY DEPARTURES */}
              <div className="bg-slate-900/80 border border-amber-800/40 p-4 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900 to-amber-950/20 shadow-sm">
                <span className="text-[11px] font-semibold text-amber-300 uppercase tracking-wider flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3 text-amber-400" /> Partenze Anticipate
                </span>
                <div className="text-2xl font-bold text-amber-300 font-serif-luxury mt-1 flex items-baseline justify-between">
                  <span>{stats.early_departures_count}</span>
                  <span className="text-[11px] text-amber-400/90 font-normal font-sans">
                    Camere Rilasciate
                  </span>
                </div>
              </div>

              {/* TODAY'S FLOW */}
              <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-2xl shadow-sm">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                  Movimenti Oggi
                </span>
                <div className="text-2xl font-bold text-emerald-400 font-serif-luxury mt-1 flex items-baseline justify-between">
                  <span>{stats.arrivals_today_count} in / {stats.departures_today_count} out</span>
                  <span className="text-[11px] text-slate-400 font-normal font-sans">Oggi</span>
                </div>
              </div>
            </div>
          )}

          {/* ACTIVE TAB CONTENT */}
          {activeTab === 'room_rack' && (
            <RoomRack
              rooms={rooms}
              bookings={bookings}
              onOpenNewBooking={() => setNewBookingModalOpen(true)}
              onOpenEarlyDeparture={(b) => setEarlyDepModal({ isOpen: true, booking: b })}
              onSelectBooking={(b) => setSelectedBookingForDrawer(b)}
            />
          )}

          {activeTab === 'reservations' && (
            <ReservationsTable
              bookings={bookings}
              searchFilter={searchFilter}
              setSearchFilter={setSearchFilter}
              onOpenNewBooking={() => setNewBookingModalOpen(true)}
              onOpenEarlyDeparture={(b) => setEarlyDepModal({ isOpen: true, booking: b })}
              onSelectBooking={(b) => setSelectedBookingForDrawer(b)}
            />
          )}

          {activeTab === 'guest_crm' && (
            <Guest360 />
          )}

          {activeTab === 'operations_alerts' && (
            <OperationsAlerts
              notifications={notifications}
              onMarkAsRead={handleMarkAsRead}
              onRefresh={fetchData}
            />
          )}
        </main>
      </div>

      {/* MODALS & DRAWERS */}
      <EarlyDepartureModal
        isOpen={earlyDepModal.isOpen}
        booking={earlyDepModal.booking}
        onClose={() => setEarlyDepModal({ isOpen: false, booking: null })}
        onSubmit={handleEarlyDepartureSubmit}
      />

      <NewBookingModal
        isOpen={newBookingModalOpen}
        onClose={() => setNewBookingModalOpen(false)}
        onSubmit={handleNewBookingSubmit}
      />

      <BookingDetailDrawer
        booking={selectedBookingForDrawer}
        onClose={() => setSelectedBookingForDrawer(null)}
        onOpenEarlyDeparture={(b) => setEarlyDepModal({ isOpen: true, booking: b })}
      />
    </div>
  );
}
