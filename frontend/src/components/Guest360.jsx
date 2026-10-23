import React, { useState } from 'react';
import { 
  Users, 
  Search, 
  ShieldAlert, 
  Heart, 
  Wine, 
  BedDouble, 
  Car, 
  Sparkles, 
  Phone, 
  Mail, 
  Award,
  Calendar,
  CheckCircle2,
  UtensilsCrossed
} from 'lucide-react';

export default function Guest360() {
  const [searchTerm, setSearchTerm] = useState('');

  // Sample luxury guest profiles from CRM
  const guests = [
    {
      id: 'guest_rossi_01',
      name: 'Marco Rossi',
      phone: '+39 333 1112233',
      email: 'marco.rossi@example.com',
      vipTier: 'GOLD',
      vipColor: 'bg-amber-500 text-slate-950 border-amber-300',
      persona: 'Coppia Romantica',
      totalStays: 3,
      loyaltyPoints: 4200,
      currentStay: {
        status: 'In-House',
        room: 'Camera 402 (Suite Panoramica)',
        dates: 'Attivo — Check-out tra 2 giorni',
        occasion: '10° Anniversario di Nozze'
      },
      allergenAlert: 'Signora Giulia è affetta da celiachia rigorosa (100% gluten-free). Allertare sempre maitre e cucina per colazione e cena.',
      roomPreferences: ['Piano alto panoramico', 'Cuscini anallergici', 'Ambiente silenzioso'],
      favoriteBeverages: ['Franciacorta Brut', 'Tisana ai frutti di bosco biologica'],
      specialNotes: 'Festeggiano il decimo anniversario di matrimonio. Gradito tavolo appartato vista tramonto a The Flair Rooftop.'
    },
    {
      id: 'guest_moretti_02',
      name: 'Andrea Moretti',
      phone: '+39 335 9988776',
      email: 'andrea.moretti@corporate.it',
      vipTier: 'SINA PRIVILEGE VIP',
      vipColor: 'bg-purple-500 text-white border-purple-300',
      persona: 'Business Solo Traveler',
      totalStays: 14,
      loyaltyPoints: 21500,
      currentStay: {
        status: 'Pre-Stay (Arrivo Domani)',
        room: 'Camera 201 (Deluxe King)',
        dates: 'Domani alle 14:00',
        occasion: 'Conferenza Finanziaria Internazionale'
      },
      allergenAlert: null,
      roomPreferences: ['Scrivania ergonomica per call', 'Ferro da stiro in camera', 'Wi-Fi premium ultra-veloce'],
      favoriteBeverages: ['Caffè espresso doppio ristretto Illy', 'Acqua minerale frizzante'],
      specialNotes: 'Ospite frequente di prestigio. Richiede sempre transfer NCC Mercedes Classe S da/per Aeroporto Fiumicino.'
    },
    {
      id: 'guest_bianchi_03',
      name: 'Elena Bianchi',
      phone: '+39 340 5544332',
      email: 'elena.bianchi@gmail.com',
      vipTier: 'SILVER',
      vipColor: 'bg-slate-300 text-slate-950 border-slate-200',
      persona: 'Family Leisure',
      totalStays: 2,
      loyaltyPoints: 2400,
      currentStay: {
        status: 'Post-Stay (Check-out completato)',
        room: 'Camera 301 (Junior Suite)',
        dates: 'Partita ieri',
        occasion: 'Vacanza in Famiglia a Roma'
      },
      allergenAlert: 'Dieta vegetariana per la Sig.ra Elena; menu bambini semplice per Leo (8 anni) e Sofia (11 anni).',
      roomPreferences: ['Suite con zona giorno separata', 'Letto supplementare per i figli'],
      favoriteBeverages: ['Cappuccino con latte di mandorla', 'Spremuta d\'arancia fresca'],
      specialNotes: 'Interessata a future vacanze estive presso la proprietà Sina Villa Medici a Firenze.'
    }
  ];

  const filteredGuests = guests.filter(g => {
    const q = searchTerm.toLowerCase().trim();
    if (!q) return true;
    return (
      g.name.toLowerCase().includes(q) ||
      g.phone.includes(q) ||
      g.email.toLowerCase().includes(q) ||
      g.persona.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      {/* HEADER & SEARCH */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Users className="w-5 h-5 text-amber-400" />
            Sina Guest 360 & Personalization Intelligence
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Dossier degli ospiti con profilazione VIP, restrizioni alimentari per la ristorazione, preferenze in camera e note concierge.
          </p>
        </div>

        <div className="relative w-full md:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Cerca ospite per nome, tel o persona..."
            className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-100 focus:outline-none focus:border-amber-400"
          />
        </div>
      </div>

      {/* GUEST DOSSIER CARDS */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {filteredGuests.map((guest) => (
          <div
            key={guest.id}
            className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col justify-between hover:border-slate-700 transition-all relative overflow-hidden"
          >
            {/* TOP HEADER: AVATAR & VIP TIER */}
            <div>
              <div className="flex items-start justify-between pb-3 border-b border-slate-800/80">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-500/20 to-slate-800 border border-amber-500/30 flex items-center justify-center font-bold text-amber-300 font-serif-luxury text-lg shadow-inner">
                    {guest.name.split(' ').map(n => n[0]).join('')}
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-100 text-sm">{guest.name}</h3>
                    <div className="text-[11px] text-slate-400 flex items-center gap-1 font-mono">
                      <Phone className="w-3 h-3 text-slate-400" /> {guest.phone}
                    </div>
                  </div>
                </div>

                <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full border shadow-sm ${guest.vipColor}`}>
                  {guest.vipTier}
                </span>
              </div>

              {/* STAY STATUS & STATS */}
              <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800/60">
                  <span className="text-[10px] text-slate-400 block">Soggiorni Storici</span>
                  <span className="font-bold text-slate-200">{guest.totalStays} soggiorni</span>
                </div>
                <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800/60">
                  <span className="text-[10px] text-slate-400 block">Punti Fedeltà Sina</span>
                  <span className="font-bold text-amber-300">{guest.loyaltyPoints} pts</span>
                </div>
              </div>

              {/* CURRENT STAY SUMMARY */}
              <div className="mt-3 p-2.5 rounded-xl bg-slate-800/40 border border-slate-700/40 text-xs space-y-1">
                <div className="flex justify-between items-center">
                  <span className="text-slate-400 font-medium">Stato Soggiorno:</span>
                  <span className="font-bold text-sky-300">{guest.currentStay.status}</span>
                </div>
                <div className="text-slate-300 text-[11px]">
                  {guest.currentStay.room}
                </div>
                {guest.currentStay.occasion && (
                  <div className="text-[11px] text-rose-300 flex items-center gap-1 pt-1 font-medium">
                    <Heart className="w-3 h-3 text-rose-400 fill-rose-400" />
                    {guest.currentStay.occasion}
                  </div>
                )}
              </div>

              {/* CRITICAL ALLERGY ALERT FOR KITCHEN/F&B */}
              {guest.allergenAlert && (
                <div className="mt-3 p-3 rounded-xl bg-rose-950/40 border border-rose-800/60 text-xs">
                  <div className="font-bold text-rose-300 flex items-center gap-1.5 text-[11px] uppercase tracking-wide">
                    <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0" />
                    Allerta Cucina / Ristorazione
                  </div>
                  <p className="text-[11px] text-rose-100/90 mt-1 leading-relaxed">
                    {guest.allergenAlert}
                  </p>
                </div>
              )}

              {/* PREFERENCES LIST */}
              <div className="mt-3 space-y-2 text-xs">
                <div className="flex items-start gap-2 text-[11px] text-slate-300">
                  <BedDouble className="w-3.5 h-3.5 text-sky-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="text-slate-400">Preferenze camera: </span>
                    {guest.roomPreferences.join(', ')}
                  </div>
                </div>

                <div className="flex items-start gap-2 text-[11px] text-slate-300">
                  <Wine className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="text-slate-400">Bevande preferite: </span>
                    {guest.favoriteBeverages.join(', ')}
                  </div>
                </div>
              </div>
            </div>

            {/* SPECIAL NOTES FOOTER */}
            <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-400">
              <span className="font-semibold text-slate-300 block mb-0.5">Nota Concierge & Staff:</span>
              <p className="italic text-slate-300/90">{guest.specialNotes}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
