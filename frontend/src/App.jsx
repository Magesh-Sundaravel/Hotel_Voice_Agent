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
  Sun,
  Moon,
  TrendingUp,
  ArrowUpRight,
  ArrowDownRight
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
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [searchFilter, setSearchFilter] = useState('');
  const [lastRefreshed, setLastRefreshed] = useState(new Date());

  // Theme Management (Light by default for clean modern feel)
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('sina_pms_theme') || 'light';
  });

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('sina_pms_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => (prev === 'light' ? 'dark' : 'light'));
  };

  // Modal & Drawer states
  const [earlyDepModal, setEarlyDepModal] = useState({ isOpen: false, booking: null });
  const [newBookingModalOpen, setNewBookingModalOpen] = useState(false);
  const [selectedBookingForDrawer, setSelectedBookingForDrawer] = useState(null);

  const fetchData = async () => {
    setIsRefreshing(true);
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
      setIsRefreshing(false);
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
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 flex font-sans antialiased selection:bg-amber-100 dark:selection:bg-amber-900/50 selection:text-amber-900 dark:selection:text-amber-100 transition-colors">
      {/* SIDEBAR NAVIGATION */}
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        unreadAlertsCount={unreadAlertsCount} 
      />

      {/* MAIN DESK AREA */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        {/* TOP STATUS BAR */}
        <header className="h-16 border-b border-zinc-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-md sticky top-0 z-30 px-6 flex items-center justify-between gap-4 transition-colors">
          <div className="flex items-center gap-3 min-w-0">
            <h1 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100 tracking-tight hidden sm:block">
              Sina Bernini Bristol — Front Desk & Operations
            </h1>
            <span className="text-[11px] font-medium px-2 py-0.5 rounded-md bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-700">
              Reception Desk
            </span>
          </div>

          <div className="flex items-center gap-2.5">
            {/* Live Sync Timestamp */}
            <div className="hidden md:flex items-center gap-1.5 text-xs text-zinc-500 dark:text-zinc-400 font-mono">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
              <span>Sync: {lastRefreshed.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
            </div>

            {/* Manual Refresh */}
            <button
              onClick={fetchData}
              disabled={isRefreshing}
              className="p-2 rounded-lg text-zinc-600 hover:text-zinc-900 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:text-zinc-100 dark:hover:bg-zinc-800 border border-zinc-200 dark:border-zinc-800 transition-colors cursor-pointer"
              title="Aggiorna Dati PMS"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-zinc-800 dark:text-zinc-200' : ''}`} />
            </button>

            {/* Theme Toggle (Light / Dark) */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg text-zinc-600 hover:text-zinc-900 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:text-zinc-100 dark:hover:bg-zinc-800 border border-zinc-200 dark:border-zinc-800 transition-colors cursor-pointer"
              title={theme === 'light' ? 'Passa alla modalità scura' : 'Passa alla modalità chiara'}
            >
              {theme === 'light' ? (
                <Moon className="w-3.5 h-3.5" />
              ) : (
                <Sun className="w-3.5 h-3.5" />
              )}
            </button>

            {/* Quick New Booking Button */}
            <button
              onClick={() => setNewBookingModalOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-white dark:text-zinc-900 font-medium text-xs shadow-xs transition-colors cursor-pointer ml-1"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Nuova Prenotazione</span>
            </button>
          </div>
        </header>

        {/* PMS DASHBOARD CONTENT */}
        <main className="p-6 max-w-7xl w-full mx-auto space-y-5 flex-1">
          {/* HIGH-LEVEL KPI EXECUTIVE METRICS */}
          {stats && (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
              {/* TOTAL ROOMS */}
              <div className="bg-white dark:bg-zinc-900 border border-zinc-200/90 dark:border-zinc-800 p-4 rounded-xl shadow-xs">
                <span className="text-[11px] font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wider block">
                  Totale Camere
                </span>
                <div className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100 mt-1 flex items-baseline justify-between">
                  <span>{stats.total_rooms}</span>
                  <span className="text-xs font-normal text-zinc-500 dark:text-zinc-400">9 Suite & Camere</span>
                </div>
              </div>

              {/* OCCUPANCY */}
              <div className="bg-white dark:bg-zinc-900 border border-zinc-200/90 dark:border-zinc-800 p-4 rounded-xl shadow-xs">
                <span className="text-[11px] font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wider block">
                  Ospiti In-House
                </span>
                <div className="text-2xl font-bold tracking-tight text-blue-600 dark:text-blue-400 mt-1 flex items-baseline justify-between">
                  <span>{stats.in_house_guests_count}</span>
                  <span className="text-xs font-medium text-blue-700 dark:text-blue-300">
                    {stats.occupancy_rate_percentage}% Occupazione
                  </span>
                </div>
              </div>

              {/* EARLY DEPARTURES */}
              <div className="bg-white dark:bg-zinc-900 border border-zinc-200/90 dark:border-zinc-800 p-4 rounded-xl shadow-xs">
                <span className="text-[11px] font-medium text-amber-800 dark:text-amber-400 uppercase tracking-wider flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3 text-amber-600 dark:text-amber-400" /> Partenze Anticipate
                </span>
                <div className="text-2xl font-bold tracking-tight text-amber-700 dark:text-amber-300 mt-1 flex items-baseline justify-between">
                  <span>{stats.early_departures_count}</span>
                  <span className="text-xs font-normal text-amber-700/80 dark:text-amber-400/80">
                    Camere Rilasciate
                  </span>
                </div>
              </div>

              {/* TODAY'S FLOW */}
              <div className="bg-white dark:bg-zinc-900 border border-zinc-200/90 dark:border-zinc-800 p-4 rounded-xl shadow-xs">
                <span className="text-[11px] font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wider block">
                  Movimenti Oggi
                </span>
                <div className="text-2xl font-bold tracking-tight text-emerald-600 dark:text-emerald-400 mt-1 flex items-baseline justify-between">
                  <span>{stats.arrivals_today_count} in / {stats.departures_today_count} out</span>
                  <span className="text-xs font-normal text-zinc-500 dark:text-zinc-400">Oggi</span>
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
