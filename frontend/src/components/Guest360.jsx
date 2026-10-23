import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Search, 
  ShieldAlert, 
  Heart, 
  Wine, 
  BedDouble, 
  Phone, 
  Mail, 
  Award,
  Sparkles,
  Plus,
  Check,
  X,
  MessageSquare
} from 'lucide-react';

const API_BASE = '/api';

export default function Guest360() {
  const [guests, setGuests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTag, setSelectedTag] = useState('all');

  // Modal for adding a preference/note to a guest
  const [prefModal, setPrefModal] = useState({ isOpen: false, guest: null });
  const [newPrefType, setNewPrefType] = useState('dietary_restriction');
  const [newPrefValue, setNewPrefValue] = useState('');
  const [isSubmittingPref, setIsSubmittingPref] = useState(false);

  // Fallback initial guests if API fails or is loading
  const fallbackGuests = [
    {
      id: 'guest_rossi_01',
      first_name: 'Marco',
      last_name: 'Rossi',
      phone_number: '+393331112233',
      email: 'marco.rossi@example.com',
      vip_tier: 'gold',
      persona: 'romantic_couple',
      total_stays: 3,
      loyalty_points: 4200,
      preferences: {
        dietary_restrictions: ['Signora Giulia: celiachia rigorosa (100% gluten-free)'],
        room_preferences: ['Piano alto panoramico', 'Cuscini anallergici', 'Ambiente silenzioso'],
        favorite_drinks: ['Franciacorta Brut', 'Tisana ai frutti di bosco'],
        special_notes: 'Festeggiano il 10° anniversario di nozze. Gradito tavolo riservato vista tramonto a The Flair Rooftop.'
      }
    },
    {
      id: 'guest_moretti_02',
      first_name: 'Andrea',
      last_name: 'Moretti',
      phone_number: '+393359988776',
      email: 'andrea.moretti@corporate.it',
      vip_tier: 'sina_privilege_vip',
      persona: 'business_solo',
      total_stays: 14,
      loyalty_points: 21500,
      preferences: {
        dietary_restrictions: ['Nessuna allergia segnalata', 'Colazione proteica'],
        room_preferences: ['Scrivania ergonomica per call', 'Ferro da stiro in camera', 'Wi-Fi premium ultra-veloce'],
        favorite_drinks: ['Caffè espresso doppio ristretto', 'Acqua minerale frizzante'],
        special_notes: 'Ospite frequente di prestigio. Richiede sempre transfer NCC Mercedes Classe E da/per Fiumicino.'
      }
    },
    {
      id: 'guest_bianchi_03',
      first_name: 'Elena',
      last_name: 'Bianchi',
      phone_number: '+393405544332',
      email: 'elena.bianchi@gmail.com',
      vip_tier: 'silver',
      persona: 'family_leisure',
      total_stays: 2,
      loyalty_points: 2400,
      preferences: {
        dietary_restrictions: ['Dieta vegetariana (Elena)', 'Menu bimbi semplice per Leo (8 anni) e Sofia (11 anni)'],
        room_preferences: ['Suite con zona giorno separata', 'Letto supplementare per i figli'],
        favorite_drinks: ['Cappuccino con latte di mandorla', 'Spremuta d\'arancia fresca'],
        special_notes: 'Viaggia con la famiglia. Ha espresso interesse per la proprietà Sina Villa Medici a Firenze.'
      }
    }
  ];

  const fetchGuests = async () => {
    try {
      const res = await fetch(`${API_BASE}/crm/guests`);
      if (res.ok) {
        const data = await res.json();
        if (data && data.length > 0) {
          setGuests(data);
          return;
        }
      }
      setGuests(fallbackGuests);
    } catch (err) {
      console.warn('Using local guests fallback:', err);
      setGuests(fallbackGuests);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGuests();
  }, []);

  const handleAddPreference = async (e) => {
    e.preventDefault();
    if (!newPrefValue.trim() || !prefModal.guest) return;
    setIsSubmittingPref(true);

    try {
      const phone = prefModal.guest.phone_number;
      const payload = {
        [newPrefType]: newPrefValue.trim()
      };

      const res = await fetch(`${API_BASE}/crm/guests/${encodeURIComponent(phone)}/preferences`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        await fetchGuests();
        setPrefModal({ isOpen: false, guest: null });
        setNewPrefValue('');
      }
    } catch (err) {
      console.error('Failed to save preference:', err);
    } finally {
      setIsSubmittingPref(false);
    }
  };

  const getVipBadge = (tier) => {
    switch (tier?.toLowerCase()) {
      case 'sina_privilege_vip':
        return {
          label: 'Sina Privilege VIP',
          class: 'bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 border-purple-200 dark:border-purple-800'
        };
      case 'gold':
        return {
          label: 'Gold Member',
          class: 'bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border-amber-200 dark:border-amber-800'
        };
      case 'silver':
        return {
          label: 'Silver Member',
          class: 'bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border-zinc-200 dark:border-zinc-700'
        };
      default:
        return {
          label: 'Standard Guest',
          class: 'bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 border-zinc-200 dark:border-zinc-700'
        };
    }
  };

  const formatPersona = (persona) => {
    switch (persona) {
      case 'romantic_couple': return 'Coppia Romantica';
      case 'business_solo': return 'Business Solo';
      case 'family_leisure': return 'Famiglia Leisure';
      case 'wellness_seeker': return 'Wellness & Relax';
      case 'culture_explorer': return 'Cultura & Arte';
      default: return persona ? persona.replace(/_/g, ' ') : 'Ospite';
    }
  };

  const filteredGuests = guests.filter(g => {
    const fullName = `${g.first_name || ''} ${g.last_name || ''}`.trim().toLowerCase();
    const phone = (g.phone_number || '').toLowerCase();
    const email = (g.email || '').toLowerCase();
    const q = searchTerm.toLowerCase().trim();

    if (q && !fullName.includes(q) && !phone.includes(q) && !email.includes(q)) {
      return false;
    }

    if (selectedTag === 'allergies') {
      const diets = g.preferences?.dietary_restrictions || [];
      return diets.some(d => d.toLowerCase().includes('celiac') || d.toLowerCase().includes('allerg') || d.toLowerCase().includes('gluten'));
    }

    if (selectedTag === 'vip') {
      return g.vip_tier === 'gold' || g.vip_tier === 'sina_privilege_vip';
    }

    return true;
  });

  return (
    <div className="space-y-4">
      {/* HEADER & SEARCH */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-zinc-200 dark:border-zinc-800">
        <div>
          <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
            <Users className="w-5 h-5 text-zinc-700 dark:text-zinc-300" />
            Guest 360 & Personalizzazione Soggiorno
          </h2>
          <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
            Dossier degli ospiti con note dietetiche per la sala/cucina, preferenze camera e storico fedeltà.
          </p>
        </div>

        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-zinc-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Cerca ospite per nome, tel o email..."
            className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-white dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700/80 text-xs text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-400 dark:focus:ring-zinc-600 transition-all shadow-xs"
          />
        </div>
      </div>

      {/* FILTER PILLS */}
      <div className="flex items-center gap-1.5 text-xs">
        {[
          { id: 'all', label: 'Tutti i Dossier' },
          { id: 'vip', label: 'Ospiti VIP & Gold' },
          { id: 'allergies', label: 'Con Allarmi Alimentari' },
        ].map(tag => (
          <button
            key={tag.id}
            onClick={() => setSelectedTag(tag.id)}
            className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
              selectedTag === tag.id
                ? 'bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900'
                : 'bg-white dark:bg-zinc-900 text-zinc-600 dark:text-zinc-400 border border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800'
            }`}
          >
            {tag.label}
          </button>
        ))}
      </div>

      {/* GUEST DOSSIER CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredGuests.map((guest) => {
          const vip = getVipBadge(guest.vip_tier);
          const fullName = `${guest.first_name || ''} ${guest.last_name || ''}`.trim() || 'Ospite';
          const initials = `${guest.first_name?.[0] || ''}${guest.last_name?.[0] || ''}`.toUpperCase() || 'G';
          const prefs = guest.preferences || {};
          const dietaryAlerts = (prefs.dietary_restrictions || []).filter(
            d => d.toLowerCase().includes('celia') || d.toLowerCase().includes('allerg') || d.toLowerCase().includes('gluten')
          );

          return (
            <div
              key={guest.id}
              className="bg-white dark:bg-zinc-900 border border-zinc-200/90 dark:border-zinc-800 rounded-xl p-4 shadow-xs flex flex-col justify-between hover:border-zinc-300 dark:hover:border-zinc-700 transition-all"
            >
              <div>
                {/* HEADER: AVATAR, NAME & VIP TIER */}
                <div className="flex items-start justify-between pb-3 border-b border-zinc-100 dark:border-zinc-800">
                  <div className="flex items-center gap-2.5">
                    <div className="w-10 h-10 rounded-lg bg-zinc-100 dark:bg-zinc-800 text-zinc-800 dark:text-zinc-200 flex items-center justify-center font-bold text-xs tracking-wider border border-zinc-200 dark:border-zinc-700">
                      {initials}
                    </div>
                    <div>
                      <h3 className="font-semibold text-zinc-900 dark:text-zinc-100 text-sm">
                        {fullName}
                      </h3>
                      <div className="text-[11px] text-zinc-500 dark:text-zinc-400 font-mono flex items-center gap-1 mt-0.5">
                        <Phone className="w-3 h-3 text-zinc-400" />
                        <span>{guest.phone_number}</span>
                      </div>
                    </div>
                  </div>

                  <span className={`text-[10px] font-medium px-2 py-0.5 rounded border ${vip.class}`}>
                    {vip.label}
                  </span>
                </div>

                {/* METRICS & PERSONA */}
                <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                  <div className="p-2 rounded-lg bg-zinc-50 dark:bg-zinc-800/40 border border-zinc-100 dark:border-zinc-800">
                    <span className="text-[10px] text-zinc-400 block">Soggiorni</span>
                    <span className="font-semibold text-zinc-800 dark:text-zinc-200">
                      {guest.total_stays || 0} visite
                    </span>
                  </div>
                  <div className="p-2 rounded-lg bg-zinc-50 dark:bg-zinc-800/40 border border-zinc-100 dark:border-zinc-800">
                    <span className="text-[10px] text-zinc-400 block">Punti Fedeltà</span>
                    <span className="font-semibold text-amber-700 dark:text-amber-300">
                      {guest.loyalty_points || 0} pts
                    </span>
                  </div>
                </div>

                {/* TRAVEL PERSONA BADGE */}
                {guest.persona && (
                  <div className="mt-2.5 flex items-center gap-1.5 text-[11px] text-zinc-600 dark:text-zinc-400">
                    <span className="w-1.5 h-1.5 rounded-full bg-zinc-400"></span>
                    <span>Profilo: <strong>{formatPersona(guest.persona)}</strong></span>
                  </div>
                )}

                {/* CRITICAL DIETARY ALERT FOR KITCHEN & F&B */}
                {dietaryAlerts.length > 0 && (
                  <div className="mt-3 p-2.5 rounded-lg bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/60 text-xs">
                    <div className="font-semibold text-rose-800 dark:text-rose-200 flex items-center gap-1.5 text-[11px]">
                      <ShieldAlert className="w-3.5 h-3.5 text-rose-600 dark:text-rose-400 shrink-0" />
                      Allerta Cucina & Ristorazione
                    </div>
                    <p className="text-[11px] text-rose-700 dark:text-rose-300 mt-1 leading-normal">
                      {dietaryAlerts.join('; ')}
                    </p>
                  </div>
                )}

                {/* PREFERENCES LIST */}
                <div className="mt-3 space-y-1.5 text-xs">
                  {prefs.room_preferences && prefs.room_preferences.length > 0 && (
                    <div className="flex items-start gap-1.5 text-[11px] text-zinc-600 dark:text-zinc-300">
                      <BedDouble className="w-3.5 h-3.5 text-zinc-400 shrink-0 mt-0.5" />
                      <div>
                        <span className="text-zinc-400">Camera: </span>
                        {prefs.room_preferences.join(', ')}
                      </div>
                    </div>
                  )}

                  {prefs.favorite_drinks && prefs.favorite_drinks.length > 0 && (
                    <div className="flex items-start gap-1.5 text-[11px] text-zinc-600 dark:text-zinc-300">
                      <Wine className="w-3.5 h-3.5 text-zinc-400 shrink-0 mt-0.5" />
                      <div>
                        <span className="text-zinc-400">Bevande: </span>
                        {prefs.favorite_drinks.join(', ')}
                      </div>
                    </div>
                  )}
                </div>

                {/* SPECIAL NOTES */}
                {prefs.special_notes && (
                  <div className="mt-3 p-2.5 rounded-lg bg-zinc-50 dark:bg-zinc-800/40 border border-zinc-100 dark:border-zinc-800 text-[11px] text-zinc-600 dark:text-zinc-300">
                    <span className="font-semibold text-zinc-700 dark:text-zinc-200 block mb-0.5">
                      Nota Concierge:
                    </span>
                    <p className="italic">{prefs.special_notes}</p>
                  </div>
                )}
              </div>

              {/* CARD FOOTER ACTION */}
              <div className="mt-4 pt-3 border-t border-zinc-100 dark:border-zinc-800 flex justify-between items-center text-xs">
                <span className="text-[10px] text-zinc-400">
                  {guest.email || 'Nessuna email'}
                </span>
                <button
                  onClick={() => setPrefModal({ isOpen: true, guest })}
                  className="inline-flex items-center gap-1 text-[11px] font-medium text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white cursor-pointer px-2 py-1 rounded bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 transition-colors"
                >
                  <Plus className="w-3 h-3" /> Aggiungi Nota
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* MODAL TO ADD A PREFERENCE OR NOTE */}
      {prefModal.isOpen && prefModal.guest && (
        <div className="fixed inset-0 bg-zinc-950/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl max-w-md w-full p-5 shadow-xl relative animate-in fade-in zoom-in-95 duration-150">
            <button
              onClick={() => setPrefModal({ isOpen: false, guest: null })}
              className="absolute top-4 right-4 p-1 rounded-lg text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200"
            >
              <X className="w-4 h-4" />
            </button>

            <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100 mb-1">
              Nuova Nota per {prefModal.guest.first_name} {prefModal.guest.last_name}
            </h3>
            <p className="text-xs text-zinc-500 dark:text-zinc-400 mb-4">
              La preferenza viene salvata nel CRM e condivisa con la governante e la cucina.
            </p>

            <form onSubmit={handleAddPreference} className="space-y-3">
              <div>
                <label className="text-xs font-medium text-zinc-700 dark:text-zinc-300 block mb-1">
                  Tipologia Nota
                </label>
                <select
                  value={newPrefType}
                  onChange={(e) => setNewPrefType(e.target.value)}
                  className="w-full bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-lg px-3 py-1.5 text-xs text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-zinc-400"
                >
                  <option value="dietary_restriction">Allergia / Restrizione Alimentare (Cucina)</option>
                  <option value="room_preference">Preferenza Camera / Allestimento</option>
                  <option value="favorite_drink">Bevanda Preferita / Minibar</option>
                  <option value="special_note">Nota Generale Concierge</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-medium text-zinc-700 dark:text-zinc-300 block mb-1">
                  Descrizione
                </label>
                <textarea
                  required
                  rows={3}
                  value={newPrefValue}
                  onChange={(e) => setNewPrefValue(e.target.value)}
                  placeholder="Es. Intolleranza al lattosio, cuscino basso in piuma..."
                  className="w-full bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-lg p-2.5 text-xs text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-400"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-zinc-100 dark:border-zinc-800">
                <button
                  type="button"
                  onClick={() => setPrefModal({ isOpen: false, guest: null })}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 cursor-pointer"
                >
                  Annulla
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingPref}
                  className="px-3.5 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-white dark:text-zinc-900 text-xs font-medium transition-colors cursor-pointer disabled:opacity-50"
                >
                  {isSubmittingPref ? 'Salvataggio...' : 'Salva nel CRM'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
