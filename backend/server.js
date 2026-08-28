// ============================================================
// MonTour Backend - server.js
// Stack : Node.js + Express (API REST avec validations et RLS)
// Modules : Auth, Users, Files d'attente, Tickets, Stats, IA
// ============================================================

const express = require('express');
const cors = require('cors');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { v4: uuidv4 } = require('uuid');

const app = express();
const PORT = process.env.PORT || 4000;
const JWT_SECRET = process.env.JWT_SECRET || 'montour_secret_key_2025';

app.use(cors());
app.use(express.json());

// ============================================================
// BASE DE DONNEES EN MEMOIRE (simule PostgreSQL)
// ============================================================
const DB = {
  users: [],
  services: [
    { id: 'svc-1', name: 'Centre de Santé', description: 'Consultations médicales', icon: '🏥', color: '#e74c3c', avgServiceTime: 12 },
    { id: 'svc-2', name: 'Guichet Administratif', description: 'Actes administratifs', icon: '🏛️', color: '#3498db', avgServiceTime: 8 },
    { id: 'svc-3', name: 'Agence PEBCO', description: 'Services microfinance', icon: '🏦', color: '#2ecc71', avgServiceTime: 10 },
    { id: 'svc-4', name: 'ATDA Pôle 4', description: 'Services agricoles', icon: '🌾', color: '#f39c12', avgServiceTime: 15 },
  ],
  queues: {},      // serviceId -> { tickets: [], status: 'open'|'closed', currentNumber: 0 }
  tickets: [],
  stats: [],
  notifications: {},  // userId -> [notif]
};

// Initialiser les files pour chaque service
DB.services.forEach(s => {
  DB.queues[s.id] = { tickets: [], status: 'open', currentNumber: 0, calledNumber: 0 };
});

// ============================================================
// VALIDATEURS ET SANITIZATION CÔTÉ SERVEUR
// ============================================================
const EMAIL_REGEX = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$/;
const PHONE_REGEX = /^(?:\+229)?[0-9]{8}$/;

function sanitize(str) {
  if (typeof str !== 'string') return '';
  return str.replace(/[&<>"']/g, (match) => {
    const escapeMap = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#x27;' };
    return escapeMap[match];
  }).trim();
}

function validateEmail(email) {
  if (!email || typeof email !== 'string') return { valid: false, message: 'Email requis' };
  const clean = email.trim().toLowerCase();
  if (clean.length > 254) return { valid: false, message: 'Email trop long (max 254 caractères)' };
  if (!EMAIL_REGEX.test(clean)) return { valid: false, message: 'Format d\'email invalide' };
  return { valid: true, value: clean };
}

function validatePassword(password) {
  if (!password || typeof password !== 'string') return { valid: false, message: 'Mot de passe requis' };
  if (password.length < 8) return { valid: false, message: 'Le mot de passe doit contenir au moins 8 caractères' };
  if (password.length > 128) return { valid: false, message: 'Mot de passe trop long (max 128 caractères)' };
  if (!/[A-Z]/.test(password)) return { valid: false, message: 'Au moins une lettre majuscule requise' };
  if (!/[a-z]/.test(password)) return { valid: false, message: 'Au moins une lettre minuscule requise' };
  if (!/\d/.test(password)) return { valid: false, message: 'Au moins un chiffre requis' };
  if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?`~]/.test(password)) {
    return { valid: false, message: 'Au moins un caractère spécial requis' };
  }
  return { valid: true };
}

function validatePhone(phone) {
  if (!phone) return { valid: true, value: '' };
  const clean = phone.replace(/[\s\-\.]/g, '');
  if (!PHONE_REGEX.test(clean)) return { valid: false, message: 'Format de téléphone invalide (+229XXXXXXXX ou 8 chiffres)' };
  return { valid: true, value: clean };
}

// ============================================================
// MIDDLEWARES : Auth JWT et RLS (Row Level Security)
// ============================================================
function authMiddleware(req, res, next) {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'Token manquant' });
  try {
    req.user = jwt.verify(token, JWT_SECRET);
    next();
  } catch {
    res.status(401).json({ error: 'Token invalide' });
  }
}

// RLS: Vérification des rôles autorisés
function requireRole(...allowedRoles) {
  return (req, res, next) => {
    if (!req.user || !allowedRoles.includes(req.user.role)) {
      return res.status(403).json({ error: 'Accès non autorisé pour ce rôle' });
    }
    next();
  };
}

// ============================================================
// MODULE 1 : AUTHENTIFICATION
// ============================================================
// POST /api/auth/register
app.post('/api/auth/register', async (req, res) => {
  const { username, email, phone, password, role } = req.body;

  const emailVal = validateEmail(email);
  if (!emailVal.valid) return res.status(400).json({ error: emailVal.message });

  const passVal = validatePassword(password);
  if (!passVal.valid) return res.status(400).json({ error: passVal.message });

  const phoneVal = validatePhone(phone);
  if (!phoneVal.valid) return res.status(400).json({ error: phoneVal.message });

  if (DB.users.find(u => u.email === emailVal.value)) {
    return res.status(409).json({ error: 'Email déjà utilisé' });
  }

  const validRoles = ['user', 'agent', 'admin'];
  const userRole = validRoles.includes(role) ? role : 'user';

  const hash = await bcrypt.hash(password, 10);
  const cleanUsername = sanitize(username) || emailVal.value.split('@')[0];

  const user = {
    id: uuidv4(),
    username: cleanUsername,
    email: emailVal.value,
    phone: phoneVal.value,
    password: hash,
    role: userRole,
    priority: 'normal',
    createdAt: new Date().toISOString(),
  };
  DB.users.push(user);
  DB.notifications[user.id] = [];

  const token = jwt.sign({ id: user.id, email: user.email, role: user.role }, JWT_SECRET, { expiresIn: '7d' });
  const { password: _, ...userSafe } = user;
  res.status(201).json({ token, user: userSafe });
});

// POST /api/auth/login
app.post('/api/auth/login', async (req, res) => {
  const { email, password } = req.body;
  if (!email || !password) return res.status(400).json({ error: 'Email et mot de passe requis' });

  const emailVal = validateEmail(email);
  if (!emailVal.valid) return res.status(400).json({ error: emailVal.message });

  const user = DB.users.find(u => u.email === emailVal.value);
  if (!user) return res.status(401).json({ error: 'Identifiants incorrects' });

  const valid = await bcrypt.compare(password, user.password);
  if (!valid) return res.status(401).json({ error: 'Identifiants incorrects' });

  const token = jwt.sign({ id: user.id, email: user.email, role: user.role }, JWT_SECRET, { expiresIn: '7d' });
  const { password: _, ...userSafe } = user;
  res.json({ token, user: userSafe });
});

// GET /api/auth/me (RLS: son propre profil)
app.get('/api/auth/me', authMiddleware, (req, res) => {
  const user = DB.users.find(u => u.id === req.user.id);
  if (!user) return res.status(404).json({ error: 'Utilisateur introuvable' });
  const { password: _, ...userSafe } = user;
  res.json(userSafe);
});

// PUT /api/auth/profile (RLS: modifier uniquement son propre profil)
app.put('/api/auth/profile', authMiddleware, (req, res) => {
  const idx = DB.users.findIndex(u => u.id === req.user.id);
  if (idx === -1) return res.status(404).json({ error: 'Utilisateur introuvable' });

  const { username, phone, priority } = req.body;

  if (username !== undefined) {
    const cleanU = sanitize(username);
    if (cleanU.length < 3 || cleanU.length > 50) {
      return res.status(400).json({ error: 'Le nom d\'utilisateur doit comporter entre 3 et 50 caractères' });
    }
    DB.users[idx].username = cleanU;
  }

  if (phone !== undefined) {
    const phoneVal = validatePhone(phone);
    if (!phoneVal.valid) return res.status(400).json({ error: phoneVal.message });
    DB.users[idx].phone = phoneVal.value;
  }

  if (priority !== undefined) {
    const validPriorities = ['normal', 'urgent', 'handicap', 'senior'];
    if (!validPriorities.includes(priority)) {
      return res.status(400).json({ error: 'Priorité invalide' });
    }
    DB.users[idx].priority = priority;
  }

  const { password: _, ...userSafe } = DB.users[idx];
  res.json(userSafe);
});

// ============================================================
// MODULE 2 : SERVICES
// ============================================================
app.get('/api/services', authMiddleware, (req, res) => {
  const result = DB.services.map(s => ({
    ...s,
    queueLength: DB.queues[s.id]?.tickets.filter(t => t.status === 'waiting').length || 0,
    status: DB.queues[s.id]?.status || 'closed',
    currentNumber: DB.queues[s.id]?.calledNumber || 0,
  }));
  res.json(result);
});

app.get('/api/services/:id', authMiddleware, (req, res) => {
  const s = DB.services.find(s => s.id === req.params.id);
  if (!s) return res.status(404).json({ error: 'Service introuvable' });
  const q = DB.queues[s.id];
  res.json({
    ...s,
    queueLength: q ? q.tickets.filter(t => t.status === 'waiting').length : 0,
    status: q ? q.status : 'closed',
    currentNumber: q ? q.calledNumber : 0,
    tickets: q ? q.tickets : [],
  });
});

// ============================================================
// MODULE 3 : TICKETS / FILE D'ATTENTE (avec RLS)
// ============================================================
function predictWaitTime(serviceId, positionInQueue, userPriority) {
  const service = DB.services.find(s => s.id === serviceId);
  if (!service) return 0;

  const base = service.avgServiceTime;
  const hour = new Date().getHours();
  let peakFactor = 1.0;
  if (hour >= 8 && hour <= 10) peakFactor = 1.5;
  else if (hour >= 11 && hour <= 13) peakFactor = 1.3;
  else if (hour >= 15 && hour <= 17) peakFactor = 1.4;

  const priorityBonus = { urgent: 0.3, handicap: 0.5, senior: 0.7, normal: 1.0 };
  const pFactor = priorityBonus[userPriority] || 1.0;

  const effectivePos = Math.max(1, positionInQueue * pFactor);
  const estimated = Math.round(effectivePos * base * peakFactor);
  return Math.max(1, estimated);
}

function computePriorityScore(user, requestedAt) {
  const scores = { urgent: 100, handicap: 80, senior: 60, normal: 40 };
  const base = scores[user?.priority] || 40;
  const waitedMin = (Date.now() - new Date(requestedAt).getTime()) / 60000;
  return base + Math.floor(waitedMin);
}

// POST /api/queues/:serviceId/take-ticket
app.post('/api/queues/:serviceId/take-ticket', authMiddleware, (req, res) => {
  const { serviceId } = req.params;
  const queue = DB.queues[serviceId];
  if (!queue) return res.status(404).json({ error: 'File introuvable' });
  if (queue.status === 'closed') return res.status(400).json({ error: 'Ce service est fermé' });

  const existing = queue.tickets.find(t => t.userId === req.user.id && t.status === 'waiting');
  if (existing) return res.status(409).json({ error: 'Vous avez déjà un ticket actif', ticket: existing });

  const user = DB.users.find(u => u.id === req.user.id);
  queue.currentNumber += 1;

  const ticket = {
    id: uuidv4(),
    number: queue.currentNumber,
    serviceId,
    userId: req.user.id,
    userName: user?.username || 'Anonyme',
    userPriority: user?.priority || 'normal',
    status: 'waiting',
    requestedAt: new Date().toISOString(),
    calledAt: null,
    servedAt: null,
    estimatedWait: 0,
    priorityScore: 0,
  };

  ticket.priorityScore = computePriorityScore(user, ticket.requestedAt);

  const sortedWaiting = [...queue.tickets.filter(t => t.status === 'waiting'), ticket]
    .sort((a, b) => b.priorityScore - a.priorityScore);
  const myPos = sortedWaiting.findIndex(t => t.id === ticket.id) + 1;
  ticket.estimatedWait = predictWaitTime(serviceId, myPos, ticket.userPriority);

  queue.tickets.push(ticket);
  DB.tickets.push(ticket);

  if (!DB.notifications[req.user.id]) DB.notifications[req.user.id] = [];
  DB.notifications[req.user.id].push({
    id: uuidv4(),
    type: 'ticket_taken',
    title: '🎫 Ticket réservé !',
    message: `Votre ticket n°${ticket.number} est confirmé. Temps d'attente estimé : ${ticket.estimatedWait} min.`,
    read: false,
    createdAt: new Date().toISOString(),
  });

  res.status(201).json({ ticket, position: myPos });
});

// GET /api/queues/:serviceId
app.get('/api/queues/:serviceId', authMiddleware, (req, res) => {
  const { serviceId } = req.params;
  const queue = DB.queues[serviceId];
  if (!queue) return res.status(404).json({ error: 'File introuvable' });

  const service = DB.services.find(s => s.id === serviceId);
  const waiting = queue.tickets.filter(t => t.status === 'waiting')
    .sort((a, b) => b.priorityScore - a.priorityScore);

  waiting.forEach((t, idx) => {
    t.estimatedWait = predictWaitTime(serviceId, idx + 1, t.userPriority);
  });

  res.json({
    service,
    status: queue.status,
    calledNumber: queue.calledNumber,
    totalWaiting: waiting.length,
    tickets: waiting,
  });
});

// POST /api/queues/:serviceId/call-next (RLS: Agent/Admin)
app.post('/api/queues/:serviceId/call-next', authMiddleware, requireRole('agent', 'admin'), (req, res) => {
  const { serviceId } = req.params;
  const queue = DB.queues[serviceId];
  if (!queue) return res.status(404).json({ error: 'File introuvable' });

  const waiting = queue.tickets
    .filter(t => t.status === 'waiting')
    .sort((a, b) => b.priorityScore - a.priorityScore);

  if (waiting.length === 0) return res.status(404).json({ error: 'File vide' });

  const next = waiting[0];
  next.status = 'called';
  next.calledAt = new Date().toISOString();
  queue.calledNumber = next.number;

  if (!DB.notifications[next.userId]) DB.notifications[next.userId] = [];
  DB.notifications[next.userId].push({
    id: uuidv4(),
    type: 'your_turn',
    title: '🔔 Votre tour approche !',
    message: `Ticket n°${next.number} — Présentez-vous immédiatement au guichet.`,
    read: false,
    createdAt: new Date().toISOString(),
  });

  res.json({ calledTicket: next });
});

// POST /api/queues/:serviceId/serve/:ticketId (RLS: Agent/Admin)
app.post('/api/queues/:serviceId/serve/:ticketId', authMiddleware, requireRole('agent', 'admin'), (req, res) => {
  const { serviceId, ticketId } = req.params;
  const queue = DB.queues[serviceId];
  const ticket = queue?.tickets.find(t => t.id === ticketId);
  if (!ticket) return res.status(404).json({ error: 'Ticket introuvable' });

  ticket.status = 'served';
  ticket.servedAt = new Date().toISOString();

  DB.stats.push({
    serviceId,
    ticketId,
    waitTime: Math.round((new Date(ticket.calledAt || ticket.servedAt) - new Date(ticket.requestedAt)) / 60000),
    date: new Date().toISOString(),
  });

  res.json({ ticket });
});

// DELETE /api/queues/:serviceId/cancel/:ticketId (RLS: Propriétaire du ticket)
app.delete('/api/queues/:serviceId/cancel/:ticketId', authMiddleware, (req, res) => {
  const { serviceId, ticketId } = req.params;
  const queue = DB.queues[serviceId];
  const ticket = queue?.tickets.find(t => t.id === ticketId && t.userId === req.user.id);
  if (!ticket) return res.status(404).json({ error: 'Ticket introuvable ou vous n\'en êtes pas le propriétaire' });
  if (ticket.status !== 'waiting') return res.status(400).json({ error: 'Impossible d\'annuler ce ticket' });

  ticket.status = 'cancelled';
  res.json({ message: 'Ticket annulé avec succès', ticket });
});

// GET /api/my-tickets (RLS: Historique personnel)
app.get('/api/my-tickets', authMiddleware, (req, res) => {
  const userTickets = DB.tickets.filter(t => t.userId === req.user.id)
    .sort((a, b) => new Date(b.requestedAt) - new Date(a.requestedAt));
  res.json(userTickets);
});

// ============================================================
// MODULE 4 : NOTIFICATIONS (RLS)
// ============================================================
app.get('/api/notifications', authMiddleware, (req, res) => {
  const notifs = DB.notifications[req.user.id] || [];
  res.json(notifs.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt)));
});

app.put('/api/notifications/read-all', authMiddleware, (req, res) => {
  const notifs = DB.notifications[req.user.id] || [];
  notifs.forEach(n => n.read = true);
  res.json({ message: 'Notifications marquées comme lues' });
});

// ============================================================
// MODULE 5 : STATISTIQUES (RLS: Agent/Admin)
// ============================================================
app.get('/api/stats', authMiddleware, requireRole('agent', 'admin'), (req, res) => {
  const totalTickets = DB.tickets.length;
  const served = DB.tickets.filter(t => t.status === 'served').length;
  const cancelled = DB.tickets.filter(t => t.status === 'cancelled').length;
  const waiting = DB.tickets.filter(t => t.status === 'waiting').length;
  const called = DB.tickets.filter(t => t.status === 'called').length;

  const avgWait = DB.stats.length > 0
    ? Math.round(DB.stats.reduce((s, r) => s + r.waitTime, 0) / DB.stats.length)
    : 0;

  const byService = DB.services.map(s => ({
    serviceId: s.id,
    name: s.name,
    total: DB.tickets.filter(t => t.serviceId === s.id).length,
    served: DB.tickets.filter(t => t.serviceId === s.id && t.status === 'served').length,
    waiting: DB.queues[s.id]?.tickets.filter(t => t.status === 'waiting').length || 0,
  }));

  const byPriority = ['urgent', 'handicap', 'senior', 'normal'].map(p => ({
    priority: p,
    count: DB.tickets.filter(t => t.userPriority === p).length,
  }));

  res.json({ totalTickets, served, cancelled, waiting, called, avgWait, byService, byPriority });
});

// ============================================================
// MODULE 6 : CHATBOT
// ============================================================
const chatbotResponses = {
  bonjour: 'Bonjour ! Je suis l\'assistant MonTour. Comment puis-je vous aider ? Vous pouvez me demander : votre position, le temps d\'attente, ou comment réserver un ticket.',
  ticket: 'Pour réserver un ticket, choisissez un service depuis votre tableau de bord et cliquez sur "Prendre un ticket". Vous recevrez une confirmation avec votre numéro et le temps estimé.',
  attente: 'Le temps d\'attente est estimé par notre IA en fonction de l\'affluence actuelle, de l\'heure et de votre priorité.',
  annuler: 'Vous pouvez annuler votre ticket depuis la section "Ma file d\'attente" en cliquant sur "Annuler mon ticket".',
  priorité: 'Les priorités disponibles sont : Urgent (médical), Handicap, Senior et Normal. Mettez à jour votre profil pour bénéficier d\'une priorité adaptée.',
  notification: 'Activez les notifications pour être averti automatiquement quand votre tour approche. Vous recevrez une alerte push sur votre téléphone.',
  horaire: 'Les services sont généralement ouverts de 8h à 17h, du lundi au vendredi. Consultez la fiche de chaque service pour les horaires exacts.',
  default: 'Je n\'ai pas bien compris votre question. Essayez : "ticket", "attente", "annuler", "priorité", "notification" ou "horaire".',
};

app.post('/api/chatbot', authMiddleware, (req, res) => {
  const { message } = req.body;
  if (!message || typeof message !== 'string') return res.status(400).json({ error: 'Message requis' });

  const cleanMessage = sanitize(message);
  if (cleanMessage.length > 1000) return res.status(400).json({ error: 'Message trop long (max 1000 caractères)' });

  const lower = cleanMessage.toLowerCase();
  let response = chatbotResponses.default;

  for (const [key, val] of Object.entries(chatbotResponses)) {
    if (lower.includes(key)) { response = val; break; }
  }

  setTimeout(() => {
    res.json({
      message: response,
      timestamp: new Date().toISOString(),
      intent: Object.keys(chatbotResponses).find(k => lower.includes(k)) || 'unknown',
    });
  }, 200);
});

// ============================================================
// MODULE 7 : ADMIN (RLS: Admin)
// ============================================================
app.put('/api/admin/queues/:serviceId/toggle', authMiddleware, requireRole('admin'), (req, res) => {
  const { serviceId } = req.params;
  const queue = DB.queues[serviceId];
  if (!queue) return res.status(404).json({ error: 'File introuvable' });
  queue.status = queue.status === 'open' ? 'closed' : 'open';
  res.json({ serviceId, status: queue.status });
});

app.get('/api/admin/users', authMiddleware, requireRole('admin'), (req, res) => {
  const users = DB.users.map(({ password: _, ...u }) => u);
  res.json(users);
});

// ============================================================
// HEALTH CHECK
// ============================================================
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', version: '1.0.0', app: 'MonTour API', timestamp: new Date().toISOString() });
});

app.listen(PORT, () => {
  console.log(`\n🚀 MonTour API démarrée sur http://localhost:${PORT}`);
});

module.exports = app;