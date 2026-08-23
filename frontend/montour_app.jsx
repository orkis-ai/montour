// ============================================================
// MonTour - Application Mobile Intelligente
// Frontend React complet - Toutes les pages et modules
// Stack : React + Hooks + Tailwind (inline styles)
// ============================================================

import { useState, useEffect, useRef, useCallback } from "react";

// ============================================================
// CONFIGURATION API (Backend Express simulé en mémoire ici)
// ============================================================
const API_BASE = "http://localhost:4000/api";

// Simulateur de base de données pour fonctionnement standalone
const localDB = {
  users: JSON.parse(localStorage.getItem("mt_users") || "[]"),
  tickets: JSON.parse(localStorage.getItem("mt_tickets") || "[]"),
  queues: JSON.parse(localStorage.getItem("mt_queues") || "{}"),
  notifications: JSON.parse(localStorage.getItem("mt_notifs") || "{}"),
};

const saveDB = () => {
  localStorage.setItem("mt_users", JSON.stringify(localDB.users));
  localStorage.setItem("mt_tickets", JSON.stringify(localDB.tickets));
  localStorage.setItem("mt_queues", JSON.stringify(localDB.queues));
  localStorage.setItem("mt_notifs", JSON.stringify(localDB.notifications));
};

const SERVICES = [
  { id: "svc-1", name: "Centre de Santé", description: "Consultations médicales", icon: "🏥", color: "#e74c3c", avgServiceTime: 12 },
  { id: "svc-2", name: "Guichet Administratif", description: "Actes administratifs", icon: "🏛️", color: "#3498db", avgServiceTime: 8 },
  { id: "svc-3", name: "Agence PEBCO", description: "Services microfinance", icon: "🏦", color: "#2ecc71", avgServiceTime: 10 },
  { id: "svc-4", name: "ATDA Pôle 4", description: "Services agricoles", icon: "🌾", color: "#f39c12", avgServiceTime: 15 },
];

SERVICES.forEach(s => {
  if (!localDB.queues[s.id]) {
    localDB.queues[s.id] = { tickets: [], status: "open", currentNumber: 0, calledNumber: 0 };
  }
});

// ============================================================
// MOTEUR IA : Prédiction du temps d'attente (TFLite simulé)
// ============================================================
function predictWaitTime(serviceId, positionInQueue, userPriority) {
  const service = SERVICES.find(s => s.id === serviceId);
  if (!service) return 0;
  const base = service.avgServiceTime;
  const hour = new Date().getHours();
  let peakFactor = 1.0;
  if (hour >= 8 && hour <= 10) peakFactor = 1.5;
  else if (hour >= 11 && hour <= 13) peakFactor = 1.3;
  else if (hour >= 15 && hour <= 17) peakFactor = 1.4;
  const pMap = { urgent: 0.3, handicap: 0.5, senior: 0.7, normal: 1.0 };
  const effectivePos = Math.max(1, positionInQueue * (pMap[userPriority] || 1.0));
  const estimated = Math.round(effectivePos * base * peakFactor);
  const noise = 1 + (Math.random() * 0.3 - 0.15);
  return Math.max(1, Math.round(estimated * noise));
}

function computePriorityScore(priority, requestedAt) {
  const scores = { urgent: 100, handicap: 80, senior: 60, normal: 40 };
  const base = scores[priority] || 40;
  const waitedMin = (Date.now() - new Date(requestedAt).getTime()) / 60000;
  return base + Math.floor(waitedMin);
}

// Chatbot Rasa simulé
const CHATBOT_KB = {
  bonjour: "Bonjour ! Je suis l'assistant MonTour 🤖. Je peux vous aider avec votre ticket, le temps d'attente, ou les services disponibles.",
  ticket: "Pour réserver un ticket 🎫, rendez-vous dans l'onglet **File d'attente**, choisissez un service et cliquez sur **Prendre un ticket**.",
  attente: "Le temps d'attente ⏱️ est estimé par notre IA en analysant l'affluence, l'heure et votre niveau de priorité.",
  annuler: "Pour annuler votre ticket, allez dans **Mes Tickets** et cliquez sur **Annuler**. Ceci libère votre place dans la file.",
  priorité: "Les niveaux de priorité 🏷️ disponibles : Urgent (urgence médicale), Handicap, Senior, et Normal. Modifiez votre profil pour changer votre priorité.",
  notification: "Activez les notifications 🔔 pour recevoir des alertes quand votre tour approche. Elles s'activent depuis les paramètres.",
  horaire: "Les services sont généralement ouverts de 8h à 17h 🕗, du lundi au vendredi.",
  aide: "Je peux répondre sur : ticket, attente, annuler, priorité, notification, horaire. Tapez un de ces mots pour commencer.",
};

function chatbotResponse(msg) {
  const lower = msg.toLowerCase();
  for (const [key, val] of Object.entries(CHATBOT_KB)) {
    if (lower.includes(key)) return val;
  }
  return "Je n'ai pas compris votre demande. Essayez : **ticket**, **attente**, **annuler**, **priorité**, **notification** ou **horaire**.";
}

// ============================================================
// STYLES GLOBAUX
// ============================================================
const COLORS = {
  primary: "#1a73e8",
  primaryDark: "#1557b0",
  secondary: "#34a853",
  accent: "#fbbc04",
  danger: "#ea4335",
  warning: "#ff9800",
  bg: "#f0f4f8",
  card: "#ffffff",
  text: "#1a1a2e",
  textLight: "#5f6368",
  border: "#e0e7ef",
  success: "#34a853",
};

const S = {
  app: { fontFamily: "'Segoe UI', system-ui, sans-serif", background: COLORS.bg, minHeight: "100vh", maxWidth: 430, margin: "0 auto", position: "relative" },
  screen: { minHeight: "100vh", background: COLORS.bg, paddingBottom: 70 },
  card: { background: "#fff", borderRadius: 16, padding: "16px 20px", boxShadow: "0 2px 12px rgba(0,0,0,0.07)", marginBottom: 12 },
  btn: (color = COLORS.primary) => ({ background: color, color: "#fff", border: "none", borderRadius: 12, padding: "14px 24px", fontSize: 16, fontWeight: 600, cursor: "pointer", width: "100%", transition: "all 0.2s", display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }),
  btnOutline: (color = COLORS.primary) => ({ background: "transparent", color, border: `2px solid ${color}`, borderRadius: 12, padding: "12px 24px", fontSize: 15, fontWeight: 600, cursor: "pointer", width: "100%", transition: "all 0.2s" }),
  input: { width: "100%", padding: "14px 16px", borderRadius: 12, border: `1.5px solid ${COLORS.border}`, fontSize: 15, outline: "none", boxSizing: "border-box", background: "#fafbfd", transition: "border 0.2s" },
  label: { fontSize: 13, fontWeight: 600, color: COLORS.textLight, marginBottom: 6, display: "block" },
  badge: (color) => ({ background: color + "22", color, padding: "3px 10px", borderRadius: 20, fontSize: 12, fontWeight: 700 }),
  navBar: { position: "fixed", bottom: 0, left: "50%", transform: "translateX(-50%)", width: "100%", maxWidth: 430, background: "#fff", borderTop: "1px solid #e0e7ef", display: "flex", zIndex: 1000, boxShadow: "0 -4px 20px rgba(0,0,0,0.08)" },
  navItem: (active) => ({ flex: 1, padding: "10px 4px 6px", display: "flex", flexDirection: "column", alignItems: "center", cursor: "pointer", color: active ? COLORS.primary : COLORS.textLight, background: "none", border: "none", transition: "color 0.2s" }),
};

// ============================================================
// COMPOSANTS UTILITAIRES
// ============================================================
function Toast({ msg, type, onClose }) {
  const colors = { success: "#34a853", error: "#ea4335", info: "#1a73e8" };
  useEffect(() => { if (msg) { const t = setTimeout(onClose, 3500); return () => clearTimeout(t); } }, [msg]);
  if (!msg) return null;
  return (
    <div style={{ position: "fixed", top: 20, left: "50%", transform: "translateX(-50%)", background: colors[type] || colors.info, color: "#fff", padding: "12px 20px", borderRadius: 12, fontWeight: 600, zIndex: 9999, boxShadow: "0 4px 20px rgba(0,0,0,0.2)", maxWidth: 360, textAlign: "center", fontSize: 14 }}>
      {msg}
    </div>
  );
}

function Spinner() {
  return (
    <div style={{ display: "flex", justifyContent: "center", padding: 32 }}>
      <div style={{ width: 40, height: 40, border: `4px solid ${COLORS.border}`, borderTop: `4px solid ${COLORS.primary}`, borderRadius: "50%", animation: "spin 0.8s linear infinite" }} />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

function PriorityBadge({ p }) {
  const map = { urgent: ["🚨 Urgent", "#ea4335"], handicap: ["♿ Handicap", "#9c27b0"], senior: ["👴 Senior", "#ff9800"], normal: ["👤 Normal", "#34a853"] };
  const [label, color] = map[p] || map.normal;
  return <span style={S.badge(color)}>{label}</span>;
}

function StatusBadge({ s }) {
  const map = { waiting: ["⏳ En attente", "#ff9800"], called: ["📢 Appelé", "#1a73e8"], served: ["✅ Servi", "#34a853"], cancelled: ["❌ Annulé", "#ea4335"] };
  const [label, color] = map[s] || ["Inconnu", "#999"];
  return <span style={S.badge(color)}>{label}</span>;
}

// ============================================================
// PAGE : SPLASH / ACCUEIL
// ============================================================
function SplashScreen({ onNavigate }) {
  const [visible, setVisible] = useState(false);
  useEffect(() => { setTimeout(() => setVisible(true), 100); }, []);

  return (
    <div style={{ minHeight: "100vh", background: "linear-gradient(160deg, #1a73e8 0%, #0d47a1 60%, #1557b0 100%)", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: 32, color: "#fff", opacity: visible ? 1 : 0, transition: "opacity 0.8s" }}>
      {/* Logo */}
      <div style={{ width: 120, height: 120, background: "rgba(255,255,255,0.15)", borderRadius: 32, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", marginBottom: 24, backdropFilter: "blur(10px)", border: "1.5px solid rgba(255,255,255,0.3)" }}>
        <span style={{ fontSize: 48 }}>🎫</span>
        <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: 2, marginTop: 4, opacity: 0.8 }}>AI</span>
      </div>

      <h1 style={{ fontSize: 42, fontWeight: 900, margin: 0, letterSpacing: -1 }}>MonTour</h1>
      <p style={{ fontSize: 14, opacity: 0.8, marginTop: 6, letterSpacing: 2, textTransform: "uppercase" }}>Intelligent Queue Management</p>

      <div style={{ marginTop: 40, textAlign: "center", maxWidth: 280 }}>
        <p style={{ fontSize: 16, opacity: 0.9, lineHeight: 1.6 }}>Gérez vos files d'attente intelligemment grâce à l'IA — conçu pour le Bénin</p>
      </div>

      {/* Features */}
      {[["🤖", "IA prédictive"], ["🔔", "Notifications push"], ["📊", "Temps réel"], ["🌐", "Hors-ligne"]].map(([icon, text]) => (
        <div key={text} style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 16, background: "rgba(255,255,255,0.12)", borderRadius: 12, padding: "10px 20px", width: "100%", maxWidth: 300 }}>
          <span style={{ fontSize: 22 }}>{icon}</span>
          <span style={{ fontWeight: 600 }}>{text}</span>
        </div>
      ))}

      <div style={{ marginTop: 48, width: "100%", maxWidth: 320, display: "flex", flexDirection: "column", gap: 12 }}>
        <button style={{ ...S.btn(), background: "#fff", color: COLORS.primary }} onClick={() => onNavigate("login")}>Se connecter</button>
        <button style={{ ...S.btnOutline("#fff") }} onClick={() => onNavigate("register")}>Créer un compte</button>
      </div>

      <p style={{ marginTop: 20, fontSize: 12, opacity: 0.6 }}>Version 1.0.0 — Ségbana, Bénin 🇧🇯</p>
    </div>
  );
}

// ============================================================
// PAGE : CONNEXION
// ============================================================
function LoginPage({ onNavigate, onLogin, showToast }) {
  const [form, setForm] = useState({ email: "", password: "" });
  const [loading, setLoading] = useState(false);

  const handleLogin = () => {
    if (!form.email || !form.password) return showToast("Remplissez tous les champs", "error");
    setLoading(true);
    setTimeout(() => {
      const user = localDB.users.find(u => u.email === form.email);
      if (!user) { showToast("Utilisateur introuvable", "error"); setLoading(false); return; }
      if (user.password !== form.password) { showToast("Mot de passe incorrect", "error"); setLoading(false); return; }
      showToast("Connexion réussie !", "success");
      onLogin(user);
      setLoading(false);
    }, 800);
  };

  const demoLogin = (role) => {
    const demos = {
      user: { id: "demo-user", username: "Moussa Demo", email: "moussa@demo.bj", password: "demo", role: "user", priority: "normal", phone: "+22961000001" },
      agent: { id: "demo-agent", username: "Agent Santé", email: "agent@demo.bj", password: "demo", role: "agent", priority: "normal", phone: "+22961000002" },
      admin: { id: "demo-admin", username: "Admin MonTour", email: "admin@demo.bj", password: "demo", role: "admin", priority: "normal", phone: "+22961000003" },
    };
    const u = demos[role];
    if (!localDB.users.find(x => x.id === u.id)) { localDB.users.push(u); saveDB(); }
    if (!localDB.notifications[u.id]) { localDB.notifications[u.id] = []; }
    showToast(`Connecté en tant que ${u.username}`, "success");
    onLogin(u);
  };

  return (
    <div style={{ minHeight: "100vh", background: "linear-gradient(160deg, #f0f4f8 0%, #e8edf5 100%)", padding: 24 }}>
      <div style={{ paddingTop: 40, marginBottom: 32, textAlign: "center" }}>
        <div style={{ fontSize: 52, marginBottom: 8 }}>🎫</div>
        <h1 style={{ fontSize: 28, fontWeight: 900, color: COLORS.text, margin: 0 }}>MonTour</h1>
        <p style={{ color: COLORS.textLight, marginTop: 4 }}>Connectez-vous à votre compte</p>
      </div>

      <div style={S.card}>
        <div style={{ marginBottom: 16 }}>
          <label style={S.label}>Email</label>
          <input style={S.input} type="email" placeholder="votre@email.bj" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} />
        </div>
        <div style={{ marginBottom: 20 }}>
          <label style={S.label}>Mot de passe</label>
          <input style={S.input} type="password" placeholder="••••••••" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} />
        </div>
        <button style={S.btn()} onClick={handleLogin} disabled={loading}>
          {loading ? "Connexion..." : "🔐 Se connecter"}
        </button>
        <button style={{ ...S.btnOutline(), marginTop: 10 }}>🇬 Connexion avec Google</button>
        <p style={{ textAlign: "center", color: COLORS.textLight, fontSize: 13, marginTop: 12, cursor: "pointer" }}>Mot de passe oublié ?</p>
      </div>

      {/* Démo rapide */}
      <div style={S.card}>
        <p style={{ fontSize: 13, fontWeight: 700, color: COLORS.textLight, marginBottom: 10, textAlign: "center" }}>🧪 ACCÈS DÉMO RAPIDE</p>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {[["👤 Usager", "user"], ["🏥 Agent", "agent"], ["⚙️ Admin", "admin"]].map(([label, role]) => (
            <button key={role} style={{ ...S.btnOutline(COLORS.primary), padding: "10px 16px" }} onClick={() => demoLogin(role)}>{label}</button>
          ))}
        </div>
      </div>

      <p style={{ textAlign: "center", color: COLORS.textLight, fontSize: 14, marginTop: 16 }}>
        Pas de compte ?{" "}
        <span style={{ color: COLORS.primary, fontWeight: 700, cursor: "pointer" }} onClick={() => onNavigate("register")}>S'inscrire</span>
      </p>
    </div>
  );
}

// ============================================================
// PAGE : INSCRIPTION
// ============================================================
function RegisterPage({ onNavigate, onLogin, showToast }) {
  const [form, setForm] = useState({ username: "", email: "", phone: "", password: "", confirm: "", priority: "normal" });
  const [loading, setLoading] = useState(false);

  const handleRegister = () => {
    if (!form.username || !form.email || !form.password) return showToast("Remplissez tous les champs requis", "error");
    if (form.password !== form.confirm) return showToast("Les mots de passe ne correspondent pas", "error");
    if (localDB.users.find(u => u.email === form.email)) return showToast("Email déjà utilisé", "error");
    setLoading(true);
    setTimeout(() => {
      const user = { id: `usr-${Date.now()}`, username: form.username, email: form.email, phone: form.phone, password: form.password, priority: form.priority, role: "user", createdAt: new Date().toISOString() };
      localDB.users.push(user);
      localDB.notifications[user.id] = [{ id: `n-${Date.now()}`, type: "welcome", title: "🎉 Bienvenue sur MonTour !", message: "Votre compte a été créé avec succès. Prenez votre premier ticket maintenant !", read: false, createdAt: new Date().toISOString() }];
      saveDB();
      showToast("Compte créé avec succès !", "success");
      onLogin(user);
      setLoading(false);
    }, 800);
  };

  return (
    <div style={{ minHeight: "100vh", background: "linear-gradient(160deg, #f0f4f8 0%, #e8edf5 100%)", padding: 24 }}>
      <div style={{ paddingTop: 30, marginBottom: 24, display: "flex", alignItems: "center", gap: 12 }}>
        <button style={{ background: "none", border: "none", fontSize: 24, cursor: "pointer" }} onClick={() => onNavigate("login")}>←</button>
        <div>
          <h2 style={{ margin: 0, fontSize: 22, fontWeight: 800 }}>Créer un compte</h2>
          <p style={{ margin: 0, color: COLORS.textLight, fontSize: 13 }}>Rejoignez MonTour</p>
        </div>
      </div>

      <div style={S.card}>
        {[["Nom d'utilisateur *", "username", "text", "Moussa Abdoulaye"], ["Email *", "email", "email", "moussa@example.bj"], ["Téléphone", "phone", "tel", "+229 XX XX XX XX"]].map(([label, key, type, ph]) => (
          <div key={key} style={{ marginBottom: 14 }}>
            <label style={S.label}>{label}</label>
            <input style={S.input} type={type} placeholder={ph} value={form[key]} onChange={e => setForm({ ...form, [key]: e.target.value })} />
          </div>
        ))}

        <div style={{ marginBottom: 14 }}>
          <label style={S.label}>Niveau de priorité</label>
          <select style={S.input} value={form.priority} onChange={e => setForm({ ...form, priority: e.target.value })}>
            <option value="normal">👤 Normal</option>
            <option value="senior">👴 Senior (60+ ans)</option>
            <option value="handicap">♿ Personne handicapée</option>
            <option value="urgent">🚨 Urgence médicale</option>
          </select>
        </div>

        {[["Mot de passe *", "password"], ["Confirmer *", "confirm"]].map(([label, key]) => (
          <div key={key} style={{ marginBottom: 14 }}>
            <label style={S.label}>{label}</label>
            <input style={S.input} type="password" placeholder="••••••••" value={form[key]} onChange={e => setForm({ ...form, [key]: e.target.value })} />
          </div>
        ))}

        <button style={S.btn()} onClick={handleRegister} disabled={loading}>
          {loading ? "Création..." : "✅ Créer mon compte"}
        </button>
      </div>

      <p style={{ textAlign: "center", color: COLORS.textLight, fontSize: 14, marginTop: 12 }}>
        Déjà inscrit ?{" "}
        <span style={{ color: COLORS.primary, fontWeight: 700, cursor: "pointer" }} onClick={() => onNavigate("login")}>Se connecter</span>
      </p>
    </div>
  );
}

// ============================================================
// PAGE : TABLEAU DE BORD (Home)
// ============================================================
function DashboardPage({ user, onNavigate, showToast }) {
  const [services, setServices] = useState([]);
  const [myTicket, setMyTicket] = useState(null);

  useEffect(() => {
    const enriched = SERVICES.map(s => ({
      ...s,
      queueLength: (localDB.queues[s.id]?.tickets || []).filter(t => t.status === "waiting").length,
      status: localDB.queues[s.id]?.status || "open",
      calledNumber: localDB.queues[s.id]?.calledNumber || 0,
    }));
    setServices(enriched);
    const active = (localDB.tickets || []).find(t => t.userId === user.id && (t.status === "waiting" || t.status === "called"));
    setMyTicket(active || null);
  }, [user.id]);

  const getGreeting = () => {
    const h = new Date().getHours();
    if (h < 12) return "Bonjour";
    if (h < 18) return "Bon après-midi";
    return "Bonsoir";
  };

  const unreadCount = (localDB.notifications[user.id] || []).filter(n => !n.read).length;

  return (
    <div style={S.screen}>
      {/* Header */}
      <div style={{ background: "linear-gradient(135deg, #1a73e8, #1557b0)", padding: "28px 20px 60px", color: "#fff", position: "relative" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <p style={{ margin: 0, fontSize: 14, opacity: 0.85 }}>{getGreeting()},</p>
            <h2 style={{ margin: "4px 0 0", fontSize: 22, fontWeight: 800 }}>{user.username} 👋</h2>
            <PriorityBadge p={user.priority} />
          </div>
          <div style={{ position: "relative", cursor: "pointer" }} onClick={() => onNavigate("notifications")}>
            <span style={{ fontSize: 28 }}>🔔</span>
            {unreadCount > 0 && (
              <span style={{ position: "absolute", top: -4, right: -4, background: "#ea4335", color: "#fff", borderRadius: 10, fontSize: 10, fontWeight: 700, padding: "1px 5px" }}>{unreadCount}</span>
            )}
          </div>
        </div>
      </div>

      <div style={{ padding: "0 16px", marginTop: -44 }}>
        {/* Ticket actif */}
        {myTicket && (
          <div style={{ ...S.card, background: "linear-gradient(135deg, #fff7e6, #fff3cd)", border: "2px solid #fbbc04", marginBottom: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <p style={{ margin: 0, fontSize: 12, fontWeight: 700, color: "#f57c00" }}>🎫 TICKET ACTIF</p>
                <p style={{ margin: "4px 0", fontSize: 28, fontWeight: 900, color: COLORS.text }}>N° {myTicket.number}</p>
                <p style={{ margin: 0, fontSize: 13, color: COLORS.textLight }}>{SERVICES.find(s => s.id === myTicket.serviceId)?.name}</p>
              </div>
              <div style={{ textAlign: "right" }}>
                <StatusBadge s={myTicket.status} />
                <p style={{ margin: "8px 0 0", fontSize: 13, color: "#f57c00", fontWeight: 700 }}>~{myTicket.estimatedWait} min</p>
              </div>
            </div>
          </div>
        )}

        {/* Stats rapides */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 16 }}>
          {[
            ["📋", "Mes tickets", (localDB.tickets || []).filter(t => t.userId === user.id).length, "#1a73e8"],
            ["✅", "Servis", (localDB.tickets || []).filter(t => t.userId === user.id && t.status === "served").length, "#34a853"],
            ["⏳", "En attente", (localDB.tickets || []).filter(t => t.userId === user.id && t.status === "waiting").length, "#ff9800"],
            ["🔔", "Notifs", unreadCount, "#ea4335"],
          ].map(([icon, label, val, color]) => (
            <div key={label} style={{ ...S.card, textAlign: "center", padding: "16px 12px" }}>
              <div style={{ fontSize: 24 }}>{icon}</div>
              <div style={{ fontSize: 22, fontWeight: 900, color }}>{val}</div>
              <div style={{ fontSize: 11, color: COLORS.textLight, fontWeight: 600 }}>{label}</div>
            </div>
          ))}
        </div>

        {/* Services */}
        <h3 style={{ margin: "0 0 12px", fontSize: 16, fontWeight: 800, color: COLORS.text }}>Services disponibles</h3>
        {services.map(s => (
          <div key={s.id} style={{ ...S.card, cursor: "pointer", borderLeft: `4px solid ${s.color}` }} onClick={() => onNavigate("queue", { serviceId: s.id })}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <div style={{ width: 44, height: 44, background: s.color + "18", borderRadius: 12, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 22 }}>{s.icon}</div>
                <div>
                  <p style={{ margin: 0, fontWeight: 700, fontSize: 15 }}>{s.name}</p>
                  <p style={{ margin: 0, fontSize: 12, color: COLORS.textLight }}>{s.description}</p>
                </div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: 18, fontWeight: 900, color: s.color }}>{s.queueLength}</div>
                <div style={{ fontSize: 10, color: COLORS.textLight }}>en attente</div>
                <div style={{ ...S.badge(s.status === "open" ? COLORS.success : COLORS.danger), marginTop: 4, fontSize: 10 }}>
                  {s.status === "open" ? "Ouvert" : "Fermé"}
                </div>
              </div>
            </div>
          </div>
        ))}

        {/* Accès rapide chatbot */}
        <div style={{ ...S.card, background: "linear-gradient(135deg, #e8f4fd, #d1e8ff)", cursor: "pointer", border: "1.5px solid #b3d4f5" }} onClick={() => onNavigate("chatbot")}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{ fontSize: 36 }}>🤖</div>
            <div>
              <p style={{ margin: 0, fontWeight: 700, color: COLORS.primary }}>Assistant MonTour</p>
              <p style={{ margin: 0, fontSize: 12, color: COLORS.textLight }}>Posez vos questions à l'IA</p>
            </div>
            <span style={{ marginLeft: "auto", fontSize: 20 }}>→</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================
// PAGE : FILE D'ATTENTE
// ============================================================
function QueuePage({ user, serviceId: initialServiceId, showToast }) {
  const [selectedService, setSelectedService] = useState(initialServiceId || null);
  const [queue, setQueue] = useState(null);
  const [myTicket, setMyTicket] = useState(null);
  const [loading, setLoading] = useState(false);

  const refreshQueue = useCallback(() => {
    if (!selectedService) return;
    const q = localDB.queues[selectedService];
    const service = SERVICES.find(s => s.id === selectedService);
    const waiting = (q?.tickets || []).filter(t => t.status === "waiting").sort((a, b) => b.priorityScore - a.priorityScore);
    waiting.forEach((t, i) => { t.estimatedWait = predictWaitTime(selectedService, i + 1, t.userPriority); });
    setQueue({ service, tickets: waiting, status: q?.status, calledNumber: q?.calledNumber });
    const mine = (q?.tickets || []).find(t => t.userId === user.id && (t.status === "waiting" || t.status === "called"));
    setMyTicket(mine || null);
  }, [selectedService, user.id]);

  useEffect(() => { refreshQueue(); }, [refreshQueue]);
  useEffect(() => { const t = setInterval(refreshQueue, 5000); return () => clearInterval(t); }, [refreshQueue]);

  const takeTicket = () => {
    if (!selectedService) return showToast("Sélectionnez un service", "error");
    const q = localDB.queues[selectedService];
    if (q.status === "closed") return showToast("Ce service est fermé", "error");
    const existing = q.tickets.find(t => t.userId === user.id && t.status === "waiting");
    if (existing) return showToast("Vous avez déjà un ticket actif !", "error");
    setLoading(true);
    setTimeout(() => {
      q.currentNumber = (q.currentNumber || 0) + 1;
      const ticket = {
        id: `tkt-${Date.now()}`,
        number: q.currentNumber,
        serviceId: selectedService,
        userId: user.id,
        userName: user.username,
        userPriority: user.priority || "normal",
        status: "waiting",
        requestedAt: new Date().toISOString(),
        calledAt: null,
        servedAt: null,
        estimatedWait: 0,
        priorityScore: computePriorityScore(user.priority, new Date().toISOString()),
      };
      const waitingCount = q.tickets.filter(t => t.status === "waiting").length + 1;
      ticket.estimatedWait = predictWaitTime(selectedService, waitingCount, ticket.userPriority);
      q.tickets.push(ticket);
      if (!localDB.tickets) localDB.tickets = [];
      localDB.tickets.push(ticket);
      if (!localDB.notifications[user.id]) localDB.notifications[user.id] = [];
      localDB.notifications[user.id].push({
        id: `n-${Date.now()}`,
        type: "ticket_taken",
        title: "🎫 Ticket réservé !",
        message: `Ticket n°${ticket.number} confirmé. Temps estimé : ~${ticket.estimatedWait} min.`,
        read: false,
        createdAt: new Date().toISOString(),
      });
      saveDB();
      showToast(`Ticket n°${ticket.number} obtenu ! ~${ticket.estimatedWait} min d'attente`, "success");
      refreshQueue();
      setLoading(false);
    }, 600);
  };

  const cancelTicket = () => {
    if (!myTicket) return;
    const q = localDB.queues[selectedService];
    const t = q.tickets.find(x => x.id === myTicket.id);
    if (t) { t.status = "cancelled"; saveDB(); }
    showToast("Ticket annulé", "info");
    setMyTicket(null);
    refreshQueue();
  };

  if (!selectedService) {
    return (
      <div style={S.screen}>
        <div style={{ padding: 20 }}>
          <h2 style={{ fontSize: 20, fontWeight: 800, marginBottom: 4 }}>Files d'attente</h2>
          <p style={{ color: COLORS.textLight, fontSize: 13, marginBottom: 20 }}>Choisissez un service pour prendre un ticket</p>
          {SERVICES.map(s => {
            const q = localDB.queues[s.id];
            const n = (q?.tickets || []).filter(t => t.status === "waiting").length;
            return (
              <div key={s.id} style={{ ...S.card, cursor: "pointer", borderLeft: `4px solid ${s.color}` }} onClick={() => setSelectedService(s.id)}>
                <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
                  <div style={{ width: 50, height: 50, background: s.color + "18", borderRadius: 14, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 24 }}>{s.icon}</div>
                  <div style={{ flex: 1 }}>
                    <p style={{ margin: 0, fontWeight: 700 }}>{s.name}</p>
                    <p style={{ margin: 0, fontSize: 12, color: COLORS.textLight }}>{s.description}</p>
                  </div>
                  <div style={{ textAlign: "center" }}>
                    <div style={{ fontSize: 20, fontWeight: 900, color: s.color }}>{n}</div>
                    <div style={{ fontSize: 10, color: COLORS.textLight }}>en attente</div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  const svc = SERVICES.find(s => s.id === selectedService);

  return (
    <div style={S.screen}>
      {/* Header service */}
      <div style={{ background: `linear-gradient(135deg, ${svc.color}, ${svc.color}cc)`, padding: "24px 20px 50px", color: "#fff" }}>
        <button style={{ background: "rgba(255,255,255,0.2)", border: "none", color: "#fff", borderRadius: 8, padding: "6px 12px", cursor: "pointer", marginBottom: 16 }} onClick={() => setSelectedService(null)}>← Retour</button>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <span style={{ fontSize: 36 }}>{svc.icon}</span>
          <div>
            <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800 }}>{svc.name}</h2>
            <p style={{ margin: 0, opacity: 0.85, fontSize: 13 }}>{svc.description}</p>
          </div>
        </div>
        <div style={{ display: "flex", gap: 12, marginTop: 16 }}>
          {[["Numéro actuel", `N°${queue?.calledNumber || 0}`], ["En attente", queue?.tickets.length || 0], ["Statut", queue?.status === "open" ? "Ouvert" : "Fermé"]].map(([l, v]) => (
            <div key={l} style={{ flex: 1, background: "rgba(255,255,255,0.2)", borderRadius: 10, padding: "10px 8px", textAlign: "center" }}>
              <div style={{ fontWeight: 900, fontSize: 18 }}>{v}</div>
              <div style={{ fontSize: 10, opacity: 0.8 }}>{l}</div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ padding: "0 16px", marginTop: -24 }}>
        {/* Mon ticket actif */}
        {myTicket ? (
          <div style={{ ...S.card, border: `2px solid ${svc.color}`, background: "#fffbf0" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
              <div>
                <p style={{ margin: 0, fontSize: 11, fontWeight: 700, color: svc.color }}>🎫 MON TICKET</p>
                <p style={{ margin: "4px 0 0", fontSize: 36, fontWeight: 900, color: COLORS.text }}>N° {myTicket.number}</p>
              </div>
              <StatusBadge s={myTicket.status} />
            </div>
            <div style={{ display: "flex", gap: 12 }}>
              <div style={{ flex: 1, background: "#f5f5f5", borderRadius: 8, padding: 10, textAlign: "center" }}>
                <div style={{ fontSize: 18, fontWeight: 900, color: svc.color }}>~{myTicket.estimatedWait}</div>
                <div style={{ fontSize: 11, color: COLORS.textLight }}>min d'attente</div>
              </div>
              <div style={{ flex: 1, background: "#f5f5f5", borderRadius: 8, padding: 10, textAlign: "center" }}>
                <PriorityBadge p={myTicket.userPriority} />
                <div style={{ fontSize: 11, color: COLORS.textLight, marginTop: 4 }}>Priorité</div>
              </div>
            </div>
            <button style={{ ...S.btnOutline(COLORS.danger), marginTop: 12 }} onClick={cancelTicket}>❌ Annuler mon ticket</button>
          </div>
        ) : (
          <div style={{ ...S.card, textAlign: "center" }}>
            <p style={{ fontSize: 48, margin: "0 0 8px" }}>🎫</p>
            <p style={{ fontWeight: 700, fontSize: 17, margin: "0 0 4px" }}>Prendre un ticket</p>
            <p style={{ color: COLORS.textLight, fontSize: 13, marginBottom: 16 }}>Vous serez placé selon votre priorité ({user.priority})</p>
            <button style={S.btn(svc.color)} onClick={takeTicket} disabled={loading}>
              {loading ? "Réservation..." : `📋 Prendre un ticket — ${svc.name}`}
            </button>
          </div>
        )}

        {/* Liste de la file */}
        <h3 style={{ margin: "16px 0 10px", fontSize: 15, fontWeight: 800 }}>File d'attente ({queue?.tickets.length || 0})</h3>
        {(queue?.tickets || []).slice(0, 10).map((t, i) => (
          <div key={t.id} style={{ ...S.card, padding: "12px 16px", borderLeft: `3px solid ${i === 0 ? svc.color : COLORS.border}` }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{ width: 32, height: 32, background: i === 0 ? svc.color : "#f0f0f0", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", color: i === 0 ? "#fff" : "#666", fontWeight: 700, fontSize: 13 }}>{i + 1}</div>
                <div>
                  <p style={{ margin: 0, fontWeight: 600, fontSize: 14 }}>N° {t.number} {t.userId === user.id ? "👈 Vous" : ""}</p>
                  <PriorityBadge p={t.userPriority} />
                </div>
              </div>
              <div style={{ textAlign: "right" }}>
                <p style={{ margin: 0, fontWeight: 700, color: svc.color }}>~{t.estimatedWait} min</p>
              </div>
            </div>
          </div>
        ))}
        {(queue?.tickets.length || 0) === 0 && (
          <div style={{ ...S.card, textAlign: "center", color: COLORS.textLight }}>
            <p style={{ fontSize: 32 }}>🎉</p>
            <p>Aucune attente ! Vous serez servi immédiatement.</p>
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================
// PAGE : MES TICKETS (Historique)
// ============================================================
function MyTicketsPage({ user }) {
  const tickets = (localDB.tickets || []).filter(t => t.userId === user.id).sort((a, b) => new Date(b.requestedAt) - new Date(a.requestedAt));

  return (
    <div style={S.screen}>
      <div style={{ background: "linear-gradient(135deg, #667eea, #764ba2)", padding: "28px 20px 40px", color: "#fff" }}>
        <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800 }}>📋 Mes tickets</h2>
        <p style={{ margin: "4px 0 0", opacity: 0.85, fontSize: 13 }}>{tickets.length} ticket(s) au total</p>
      </div>
      <div style={{ padding: "20px 16px 16px" }}>
        {tickets.length === 0 ? (
          <div style={{ ...S.card, textAlign: "center", padding: 32, color: COLORS.textLight }}>
            <p style={{ fontSize: 40 }}>🎫</p>
            <p style={{ fontWeight: 600 }}>Aucun ticket pour le moment</p>
            <p style={{ fontSize: 13 }}>Prenez votre premier ticket depuis la file d'attente</p>
          </div>
        ) : tickets.map(t => {
          const svc = SERVICES.find(s => s.id === t.serviceId);
          return (
            <div key={t.id} style={{ ...S.card, borderLeft: `4px solid ${svc?.color || "#ccc"}` }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                    <span style={{ fontSize: 20 }}>{svc?.icon}</span>
                    <span style={{ fontWeight: 700 }}>{svc?.name}</span>
                  </div>
                  <p style={{ margin: 0, fontSize: 24, fontWeight: 900, color: COLORS.text }}>N° {t.number}</p>
                  <p style={{ margin: "4px 0 0", fontSize: 11, color: COLORS.textLight }}>{new Date(t.requestedAt).toLocaleString("fr-FR")}</p>
                </div>
                <div style={{ textAlign: "right", display: "flex", flexDirection: "column", gap: 4 }}>
                  <StatusBadge s={t.status} />
                  <PriorityBadge p={t.userPriority} />
                  {t.status === "waiting" && <span style={{ fontSize: 12, color: "#ff9800" }}>~{t.estimatedWait} min</span>}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ============================================================
// PAGE : NOTIFICATIONS
// ============================================================
function NotificationsPage({ user, showToast }) {
  const [notifs, setNotifs] = useState([]);

  useEffect(() => {
    const n = (localDB.notifications[user.id] || []).sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
    setNotifs(n);
  }, [user.id]);

  const markAllRead = () => {
    (localDB.notifications[user.id] || []).forEach(n => n.read = true);
    saveDB();
    setNotifs([...localDB.notifications[user.id]]);
    showToast("Toutes les notifications marquées comme lues", "success");
  };

  const iconMap = { ticket_taken: "🎫", your_turn: "🔔", reminder: "⏰", welcome: "🎉", info: "ℹ️" };

  return (
    <div style={S.screen}>
      <div style={{ background: "linear-gradient(135deg, #f093fb, #f5576c)", padding: "28px 20px 40px", color: "#fff" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800 }}>🔔 Notifications</h2>
            <p style={{ margin: "4px 0 0", opacity: 0.85, fontSize: 13 }}>{notifs.filter(n => !n.read).length} non lue(s)</p>
          </div>
          {notifs.some(n => !n.read) && (
            <button style={{ background: "rgba(255,255,255,0.2)", border: "none", color: "#fff", borderRadius: 8, padding: "6px 12px", cursor: "pointer", fontSize: 12 }} onClick={markAllRead}>Tout lire</button>
          )}
        </div>
      </div>
      <div style={{ padding: "16px" }}>
        {notifs.length === 0 ? (
          <div style={{ ...S.card, textAlign: "center", padding: 32, color: COLORS.textLight }}>
            <p style={{ fontSize: 40 }}>🔕</p>
            <p style={{ fontWeight: 600 }}>Aucune notification</p>
          </div>
        ) : notifs.map(n => (
          <div key={n.id} style={{ ...S.card, background: n.read ? "#fff" : "#f0f7ff", borderLeft: `3px solid ${n.read ? COLORS.border : COLORS.primary}`, padding: "14px 16px" }}>
            <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
              <span style={{ fontSize: 24 }}>{iconMap[n.type] || "📢"}</span>
              <div style={{ flex: 1 }}>
                <p style={{ margin: 0, fontWeight: n.read ? 600 : 800, fontSize: 14 }}>{n.title}</p>
                <p style={{ margin: "4px 0 0", fontSize: 13, color: COLORS.textLight }}>{n.message}</p>
                <p style={{ margin: "4px 0 0", fontSize: 11, color: COLORS.textLight }}>{new Date(n.createdAt).toLocaleString("fr-FR")}</p>
              </div>
              {!n.read && <div style={{ width: 8, height: 8, background: COLORS.primary, borderRadius: "50%", marginTop: 4 }} />}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================================
// PAGE : CHATBOT (Rasa simulé)
// ============================================================
function ChatbotPage({ user }) {
  const [messages, setMessages] = useState([
    { id: 1, from: "bot", text: "Bonjour ! Je suis l'assistant MonTour 🤖. Comment puis-je vous aider ?\n\nEssayez : **ticket**, **attente**, **priorité**, **annuler**, **notification**, **horaire**", ts: new Date() },
  ]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const endRef = useRef(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const send = () => {
    if (!input.trim()) return;
    const userMsg = { id: Date.now(), from: "user", text: input.trim(), ts: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setTyping(true);
    setTimeout(() => {
      const reply = chatbotResponse(input.trim());
      setMessages(prev => [...prev, { id: Date.now() + 1, from: "bot", text: reply, ts: new Date() }]);
      setTyping(false);
    }, 800 + Math.random() * 400);
  };

  const renderText = (text) => {
    return text.split(/\*\*(.*?)\*\*/g).map((part, i) =>
      i % 2 === 1 ? <strong key={i}>{part}</strong> : <span key={i}>{part}</span>
    );
  };

  const quickReplies = ["Comment prendre un ticket ?", "Mon temps d'attente", "Priorité urgente", "Horaires des services"];

  return (
    <div style={{ ...S.screen, display: "flex", flexDirection: "column", height: "100vh" }}>
      <div style={{ background: "linear-gradient(135deg, #11998e, #38ef7d)", padding: "24px 20px 20px", color: "#fff" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ width: 44, height: 44, background: "rgba(255,255,255,0.2)", borderRadius: 22, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 22 }}>🤖</div>
          <div>
            <p style={{ margin: 0, fontWeight: 800, fontSize: 16 }}>Assistant MonTour</p>
            <p style={{ margin: 0, fontSize: 12, opacity: 0.85 }}>• En ligne — Rasa NLP</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: "auto", padding: "16px", display: "flex", flexDirection: "column", gap: 8 }}>
        {messages.map(m => (
          <div key={m.id} style={{ display: "flex", justifyContent: m.from === "user" ? "flex-end" : "flex-start" }}>
            {m.from === "bot" && <span style={{ fontSize: 20, marginRight: 8, alignSelf: "flex-end" }}>🤖</span>}
            <div style={{ maxWidth: "78%", background: m.from === "user" ? COLORS.primary : "#fff", color: m.from === "user" ? "#fff" : COLORS.text, padding: "10px 14px", borderRadius: m.from === "user" ? "18px 18px 4px 18px" : "18px 18px 18px 4px", fontSize: 14, lineHeight: 1.5, boxShadow: "0 2px 8px rgba(0,0,0,0.08)" }}>
              {renderText(m.text)}
              <p style={{ margin: "4px 0 0", fontSize: 10, opacity: 0.6, textAlign: "right" }}>{m.ts.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" })}</p>
            </div>
          </div>
        ))}
        {typing && (
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 20 }}>🤖</span>
            <div style={{ background: "#fff", padding: "10px 14px", borderRadius: 18, boxShadow: "0 2px 8px rgba(0,0,0,0.08)" }}>
              <div style={{ display: "flex", gap: 4 }}>
                {[0, 1, 2].map(i => <div key={i} style={{ width: 8, height: 8, background: "#ccc", borderRadius: "50%", animation: `bounce 1.2s ${i * 0.2}s infinite` }} />)}
              </div>
              <style>{`@keyframes bounce { 0%,60%,100%{transform:translateY(0)} 30%{transform:translateY(-6px)} }`}</style>
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* Réponses rapides */}
      <div style={{ padding: "8px 16px", display: "flex", gap: 8, overflowX: "auto" }}>
        {quickReplies.map(q => (
          <button key={q} style={{ background: "#e8f4fd", color: COLORS.primary, border: `1px solid ${COLORS.primary}30`, borderRadius: 20, padding: "6px 12px", fontSize: 12, cursor: "pointer", whiteSpace: "nowrap", fontWeight: 600 }} onClick={() => { setInput(q); }}>
            {q}
          </button>
        ))}
      </div>

      {/* Zone de saisie */}
      <div style={{ padding: "12px 16px", background: "#fff", borderTop: "1px solid #e0e7ef", display: "flex", gap: 10 }}>
        <input style={{ ...S.input, flex: 1 }} placeholder="Posez votre question..." value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === "Enter" && send()} />
        <button style={{ background: COLORS.primary, border: "none", borderRadius: 12, padding: "0 18px", cursor: "pointer", color: "#fff", fontSize: 18 }} onClick={send}>➤</button>
      </div>
    </div>
  );
}

// ============================================================
// PAGE : PROFIL
// ============================================================
function ProfilePage({ user, onUpdate, onLogout, showToast }) {
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({ username: user.username, phone: user.phone || "", priority: user.priority || "normal" });

  const save = () => {
    const idx = localDB.users.findIndex(u => u.id === user.id);
    if (idx !== -1) {
      localDB.users[idx].username = form.username;
      localDB.users[idx].phone = form.phone;
      localDB.users[idx].priority = form.priority;
      saveDB();
      onUpdate({ ...user, ...form });
      showToast("Profil mis à jour !", "success");
      setEditing(false);
    }
  };

  const stats = {
    total: (localDB.tickets || []).filter(t => t.userId === user.id).length,
    served: (localDB.tickets || []).filter(t => t.userId === user.id && t.status === "served").length,
    cancelled: (localDB.tickets || []).filter(t => t.userId === user.id && t.status === "cancelled").length,
  };

  return (
    <div style={S.screen}>
      <div style={{ background: "linear-gradient(135deg, #4facfe, #00f2fe)", padding: "28px 20px 60px", color: "#fff", textAlign: "center" }}>
        <div style={{ width: 80, height: 80, background: "rgba(255,255,255,0.25)", borderRadius: 40, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 36, margin: "0 auto 12px" }}>
          {user.username?.[0]?.toUpperCase() || "U"}
        </div>
        <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800 }}>{user.username}</h2>
        <p style={{ margin: "4px 0 8px", opacity: 0.85 }}>{user.email}</p>
        <PriorityBadge p={user.priority} />
        <div style={{ ...S.badge(user.role === "admin" ? "#9c27b0" : user.role === "agent" ? "#1a73e8" : "#34a853"), marginTop: 6, display: "inline-block" }}>
          {user.role === "admin" ? "⚙️ Admin" : user.role === "agent" ? "🏥 Agent" : "👤 Usager"}
        </div>
      </div>

      <div style={{ padding: "0 16px", marginTop: -30 }}>
        {/* Stats */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8, marginBottom: 16 }}>
          {[["📋", "Total", stats.total, "#1a73e8"], ["✅", "Servis", stats.served, "#34a853"], ["❌", "Annulés", stats.cancelled, "#ea4335"]].map(([icon, l, v, c]) => (
            <div key={l} style={{ ...S.card, textAlign: "center", padding: "14px 8px" }}>
              <div style={{ fontSize: 20 }}>{icon}</div>
              <div style={{ fontSize: 20, fontWeight: 900, color: c }}>{v}</div>
              <div style={{ fontSize: 11, color: COLORS.textLight }}>{l}</div>
            </div>
          ))}
        </div>

        {/* Info profil */}
        <div style={S.card}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <h3 style={{ margin: 0, fontSize: 15, fontWeight: 800 }}>Informations personnelles</h3>
            <button style={{ background: editing ? "#f0f0f0" : COLORS.primary, color: editing ? COLORS.text : "#fff", border: "none", borderRadius: 8, padding: "6px 14px", cursor: "pointer", fontWeight: 600, fontSize: 13 }} onClick={() => editing ? save() : setEditing(true)}>
              {editing ? "💾 Sauvegarder" : "✏️ Modifier"}
            </button>
          </div>

          {editing ? (
            <>
              {[["Nom d'utilisateur", "username"], ["Téléphone", "phone"]].map(([label, key]) => (
                <div key={key} style={{ marginBottom: 12 }}>
                  <label style={S.label}>{label}</label>
                  <input style={S.input} value={form[key]} onChange={e => setForm({ ...form, [key]: e.target.value })} />
                </div>
              ))}
              <div>
                <label style={S.label}>Priorité</label>
                <select style={S.input} value={form.priority} onChange={e => setForm({ ...form, priority: e.target.value })}>
                  <option value="normal">👤 Normal</option>
                  <option value="senior">👴 Senior</option>
                  <option value="handicap">♿ Handicap</option>
                  <option value="urgent">🚨 Urgent</option>
                </select>
              </div>
            </>
          ) : (
            [["👤 Nom", user.username], ["📧 Email", user.email], ["📞 Téléphone", user.phone || "Non renseigné"], ["🏷️ Rôle", user.role], ["📅 Membre depuis", user.createdAt ? new Date(user.createdAt).toLocaleDateString("fr-FR") : "—"]].map(([l, v]) => (
              <div key={l} style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderBottom: "1px solid #f0f0f0" }}>
                <span style={{ fontSize: 13, color: COLORS.textLight }}>{l}</span>
                <span style={{ fontSize: 13, fontWeight: 600 }}>{v}</span>
              </div>
            ))
          )}
        </div>

        <button style={{ ...S.btnOutline(COLORS.danger), marginTop: 8 }} onClick={onLogout}>🚪 Se déconnecter</button>
      </div>
    </div>
  );
}

// ============================================================
// PAGE : ADMIN - Tableau de bord de gestion
// ============================================================
function AdminPage({ user, showToast }) {
  const [activeTab, setActiveTab] = useState("stats");
  const [stats, setStats] = useState({ total: 0, served: 0, waiting: 0, cancelled: 0, called: 0 });

  useEffect(() => {
    const all = localDB.tickets || [];
    setStats({
      total: all.length,
      served: all.filter(t => t.status === "served").length,
      waiting: all.filter(t => t.status === "waiting").length,
      cancelled: all.filter(t => t.status === "cancelled").length,
      called: all.filter(t => t.status === "called").length,
    });
  }, []);

  const callNext = (serviceId) => {
    const q = localDB.queues[serviceId];
    const waiting = (q?.tickets || []).filter(t => t.status === "waiting").sort((a, b) => b.priorityScore - a.priorityScore);
    if (waiting.length === 0) return showToast("File vide", "info");
    const next = waiting[0];
    next.status = "called";
    next.calledAt = new Date().toISOString();
    q.calledNumber = next.number;
    if (!localDB.notifications[next.userId]) localDB.notifications[next.userId] = [];
    localDB.notifications[next.userId].push({
      id: `n-${Date.now()}`,
      type: "your_turn",
      title: "🔔 Votre tour approche !",
      message: `Ticket n°${next.number} — Présentez-vous immédiatement au guichet.`,
      read: false,
      createdAt: new Date().toISOString(),
    });
    saveDB();
    showToast(`Ticket n°${next.number} appelé !`, "success");
  };

  const serveTicket = (serviceId, ticketId) => {
    const q = localDB.queues[serviceId];
    const t = (q?.tickets || []).find(x => x.id === ticketId);
    if (t) { t.status = "served"; t.servedAt = new Date().toISOString(); saveDB(); showToast("Ticket marqué servi ✅", "success"); }
  };

  const toggleQueue = (serviceId) => {
    const q = localDB.queues[serviceId];
    q.status = q.status === "open" ? "closed" : "open";
    saveDB();
    showToast(`Service ${q.status === "open" ? "ouvert" : "fermé"}`, "success");
  };

  return (
    <div style={S.screen}>
      <div style={{ background: "linear-gradient(135deg, #6c63ff, #3f3d56)", padding: "24px 20px 40px", color: "#fff" }}>
        <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800 }}>⚙️ Administration</h2>
        <p style={{ margin: "4px 0 0", opacity: 0.85, fontSize: 13 }}>Gestion des services et statistiques</p>
        <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
          {[["stats", "📊 Stats"], ["files", "🎫 Files"], ["users", "👥 Agents"]].map(([tab, label]) => (
            <button key={tab} style={{ background: activeTab === tab ? "rgba(255,255,255,0.3)" : "rgba(255,255,255,0.1)", border: "none", color: "#fff", borderRadius: 8, padding: "8px 14px", cursor: "pointer", fontWeight: 600, fontSize: 13 }} onClick={() => setActiveTab(tab)}>{label}</button>
          ))}
        </div>
      </div>

      <div style={{ padding: "16px" }}>
        {activeTab === "stats" && (
          <>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 16 }}>
              {[["📋 Total tickets", stats.total, "#6c63ff"], ["✅ Servis", stats.served, "#34a853"], ["⏳ En attente", stats.waiting, "#ff9800"], ["❌ Annulés", stats.cancelled, "#ea4335"]].map(([l, v, c]) => (
                <div key={l} style={{ ...S.card, textAlign: "center" }}>
                  <div style={{ fontSize: 26, fontWeight: 900, color: c }}>{v}</div>
                  <div style={{ fontSize: 12, color: COLORS.textLight }}>{l}</div>
                </div>
              ))}
            </div>
            <h3 style={{ fontSize: 14, fontWeight: 800, marginBottom: 10 }}>Par service</h3>
            {SERVICES.map(s => {
              const q = localDB.queues[s.id];
              const total = (localDB.tickets || []).filter(t => t.serviceId === s.id).length;
              const served = (localDB.tickets || []).filter(t => t.serviceId === s.id && t.status === "served").length;
              const waiting = (q?.tickets || []).filter(t => t.status === "waiting").length;
              return (
                <div key={s.id} style={{ ...S.card, borderLeft: `4px solid ${s.color}` }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                      <span style={{ fontSize: 20 }}>{s.icon}</span>
                      <span style={{ fontWeight: 700 }}>{s.name}</span>
                    </div>
                    <div style={{ display: "flex", gap: 8 }}>
                      <span style={S.badge("#1a73e8")}>{total} total</span>
                      <span style={S.badge("#34a853")}>{served} servis</span>
                      <span style={S.badge("#ff9800")}>{waiting} attente</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </>
        )}

        {activeTab === "files" && SERVICES.map(s => {
          const q = localDB.queues[s.id];
          const waiting = (q?.tickets || []).filter(t => t.status === "waiting").sort((a, b) => b.priorityScore - a.priorityScore);
          const called = (q?.tickets || []).filter(t => t.status === "called");
          return (
            <div key={s.id} style={S.card}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ fontSize: 20 }}>{s.icon}</span>
                  <div>
                    <span style={{ fontWeight: 700 }}>{s.name}</span>
                    <div style={S.badge(q.status === "open" ? COLORS.success : COLORS.danger)}>{q.status === "open" ? "Ouvert" : "Fermé"}</div>
                  </div>
                </div>
                <div style={{ display: "flex", gap: 6 }}>
                  <button style={{ background: COLORS.primary, color: "#fff", border: "none", borderRadius: 8, padding: "6px 12px", cursor: "pointer", fontSize: 12, fontWeight: 600 }} onClick={() => callNext(s.id)}>📢 Appeler</button>
                  <button style={{ background: q.status === "open" ? "#ff9800" : "#34a853", color: "#fff", border: "none", borderRadius: 8, padding: "6px 10px", cursor: "pointer", fontSize: 12 }} onClick={() => toggleQueue(s.id)}>{q.status === "open" ? "🔒" : "🔓"}</button>
                </div>
              </div>
              <div style={{ fontSize: 13, color: COLORS.textLight, marginBottom: 8 }}>
                Actuel : N°{q.calledNumber || 0} | En attente : {waiting.length}
              </div>
              {called.map(t => (
                <div key={t.id} style={{ background: "#e8f5e9", borderRadius: 8, padding: "8px 12px", marginBottom: 6, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span>📢 N°{t.number} — {t.userName}</span>
                  <button style={{ background: "#34a853", color: "#fff", border: "none", borderRadius: 6, padding: "4px 10px", cursor: "pointer", fontSize: 12 }} onClick={() => serveTicket(s.id, t.id)}>✅ Servi</button>
                </div>
              ))}
              {waiting.slice(0, 5).map((t, i) => (
                <div key={t.id} style={{ background: "#f5f5f5", borderRadius: 8, padding: "8px 12px", marginBottom: 4, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontSize: 13 }}>{i + 1}. N°{t.number} — {t.userName}</span>
                  <PriorityBadge p={t.userPriority} />
                </div>
              ))}
            </div>
          );
        })}

        {activeTab === "users" && (
          <div>
            <h3 style={{ fontSize: 14, fontWeight: 800, marginBottom: 10 }}>Utilisateurs ({localDB.users.length})</h3>
            {localDB.users.map(u => (
              <div key={u.id} style={{ ...S.card, padding: "12px 16px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <p style={{ margin: 0, fontWeight: 700 }}>{u.username}</p>
                    <p style={{ margin: 0, fontSize: 12, color: COLORS.textLight }}>{u.email}</p>
                  </div>
                  <div style={{ display: "flex", gap: 6 }}>
                    <PriorityBadge p={u.priority} />
                    <span style={S.badge(u.role === "admin" ? "#9c27b0" : u.role === "agent" ? "#1a73e8" : "#34a853")}>{u.role}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================
// BARRE DE NAVIGATION
// ============================================================
function NavBar({ active, onNavigate, user, unread }) {
  const isAdmin = user?.role === "admin";
  const isAgent = user?.role === "agent";
  const items = [
    { id: "home", icon: "🏠", label: "Accueil" },
    { id: "queue", icon: "🎫", label: "File" },
    { id: "tickets", icon: "📋", label: "Tickets" },
    { id: "chatbot", icon: "🤖", label: "Assistant" },
    ...(isAdmin || isAgent ? [{ id: "admin", icon: "⚙️", label: "Admin" }] : []),
    { id: "profile", icon: "👤", label: "Profil" },
  ];

  return (
    <nav style={S.navBar}>
      {items.map(item => (
        <button key={item.id} style={S.navItem(active === item.id)} onClick={() => onNavigate(item.id)}>
          <span style={{ fontSize: 22, position: "relative" }}>
            {item.icon}
            {item.id === "notifications" && unread > 0 && (
              <span style={{ position: "absolute", top: -4, right: -4, background: "#ea4335", color: "#fff", borderRadius: 10, fontSize: 8, padding: "1px 4px" }}>{unread}</span>
            )}
          </span>
          <span style={{ fontSize: 10, fontWeight: active === item.id ? 700 : 500, marginTop: 2 }}>{item.label}</span>
        </button>
      ))}
    </nav>
  );
}

// ============================================================
// APPLICATION PRINCIPALE
// ============================================================
export default function MonTourApp() {
  const [page, setPage] = useState("splash");
  const [user, setUser] = useState(null);
  const [pageParams, setPageParams] = useState({});
  const [toast, setToast] = useState({ msg: "", type: "info" });

  const showToast = useCallback((msg, type = "info") => setToast({ msg, type }), []);

  const navigate = useCallback((to, params = {}) => {
    setPage(to);
    setPageParams(params);
  }, []);

  const handleLogin = (u) => {
    setUser(u);
    navigate("home");
  };

  const handleLogout = () => {
    setUser(null);
    navigate("splash");
  };

  const unread = user ? (localDB.notifications[user.id] || []).filter(n => !n.read).length : 0;

  const renderPage = () => {
    if (page === "splash") return <SplashScreen onNavigate={navigate} />;
    if (page === "login") return <LoginPage onNavigate={navigate} onLogin={handleLogin} showToast={showToast} />;
    if (page === "register") return <RegisterPage onNavigate={navigate} onLogin={handleLogin} showToast={showToast} />;
    if (!user) return <LoginPage onNavigate={navigate} onLogin={handleLogin} showToast={showToast} />;

    switch (page) {
      case "home": return <DashboardPage user={user} onNavigate={navigate} showToast={showToast} />;
      case "queue": return <QueuePage user={user} serviceId={pageParams.serviceId} showToast={showToast} />;
      case "tickets": return <MyTicketsPage user={user} />;
      case "chatbot": return <ChatbotPage user={user} />;
      case "notifications": return <NotificationsPage user={user} showToast={showToast} />;
      case "profile": return <ProfilePage user={user} onUpdate={u => setUser(u)} onLogout={handleLogout} showToast={showToast} />;
      case "admin": return <AdminPage user={user} showToast={showToast} />;
      default: return <DashboardPage user={user} onNavigate={navigate} showToast={showToast} />;
    }
  };

  const showNav = user && !["splash", "login", "register"].includes(page);

  return (
    <div style={S.app}>
      <Toast msg={toast.msg} type={toast.type} onClose={() => setToast({ msg: "", type: "info" })} />
      {renderPage()}
      {showNav && <NavBar active={page} onNavigate={navigate} user={user} unread={unread} />}
    </div>
  );
}