// ============================================================
// MonTour Backend - server.js
// Stack : Node.js + Express (simule l'API Django REST)
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
// MIDDLEWARE : Vérification JWT
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

// ============================================================
// MODULE 1 : AUTHENTIFICATION (Firebase Auth simulé)
// ============================================================
// POST /api/auth/register
app.post('/api/auth/register', async (req, res) => {
  const { username, email, phone, password, role } = req.body;
  if (!email || !password) return res.status(400).json({ error: 'Champs requis manquants' });
  if (DB.users.find(u => u.email === email)) return res.status(409).json({ error: 'Email déjà utilisé' });

  const hash = await bcrypt.hash(password, 10);
  const user = {
    id: uuidv4(),
    username: username || email.split('@')[0],
    email,
    phone: phone || '',
    password: hash,
    role: role || 'user',   // 'user' | 'agent' | 'admin'
    priority: 'normal',     // 'normal' | 'urgent' | 'handicap' | 'senior'
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
  const user = DB.users.find(u => u.email === email);
  if (!user) return res.status(404).json({ error: 'Utilisateur introuvable' });
  const valid = await bcrypt.compare(password, user.password);
  if (!valid) return res.status(401).json({ error: 'Mot de passe incorrect' });

  const token = jwt.sign({ id: user.id, email: user.email, role: user.role }, JWT_SECRET, { expiresIn: '7d' });
  const { password: _, ...userSafe } = user;
  res.json({ token, user: userSafe });
});

// GET /api/auth/me
app.get('/api/auth/me', authMiddleware, (req, res) => {
  const user = DB.users.find(u => u.id === req.user.id);
  if (!user) return res.status(404).json({ error: 'Utilisateur introuvable' });
  const { password: _, ...userSafe } = user;
  res.json(userSafe);
});

// PUT /api/auth/profile
app.put('/api/auth/profile', authMiddleware, (req, res) => {
  const idx = DB.users.findIndex(u => u.id === req.user.id);
  if (idx === -1) return res.status(404).json({ error: 'Utilisateur introuvable' });
  const { username, phone, priority } = req.body;
  if (username) DB.users[idx].username = username;
  if (phone) DB.users[idx].phone = phone;
  if (priority) DB.users[idx].priority = priority;
  const { password: _, ...userSafe } = DB.users[idx];
  res.json(userSafe);
});

// ============================================================
// MODULE 2 : SERVICES
// ============================================================
// GET /api/services
app.get('/api/services', authMiddleware, (req, res) => {
  const result = DB.services.map(s => ({
    ...s,
    queueLength: DB.queues[s.id].tickets.filter(t => t.status === 'waiting').length,
    status: DB.queues[s.id].status,
    currentNumber: DB.queues[s.id].calledNumber,
  }));
  res.json(result);
});

// GET /api/services/:id
app.get('/api/services/:id', authMiddleware, (req, res) => {
  const s = DB.services.find(s => s.id === req.params.id);
  if (!s) return res.status(404).json({ error: 'Service introuvable' });
  const q = DB.queues[s.id];
  res.json({
    ...s,
    queueLength: q.tickets.filter(t => t.status === 'waiting').length,
    status: q.status,
    currentNumber: q.calledNumber,
    tickets: q.tickets,
  });
});

// ============================================================
// MODULE 3 : TICKETS / FILE D'ATTENTE
// ============================================================

// Fonction IA : Prédiction du temps d'attente (TFLite simulé)
function predictWaitTime(serviceId, positionInQueue, userPriority) {
  const service = DB.services.find(s => s.id === serviceId);
  if (!service) return 0;

  const base = service.avgServiceTime;
  // Facteur contextuel (heure de la journée)
  const hour = new Date().getHours();
  let peakFactor = 1.0;
  if (hour >= 8 && hour <= 10) peakFactor = 1.5;       // Pointe matin
  else if (hour >= 11 && hour <= 13) peakFactor = 1.3;  // Avant-midi
  else if (hour >= 15 && hour <= 17) peakFactor = 1.4;  // Pointe soir

  // Facteur priorité
  const priorityBonus = { urgent: 0.3, handicap: 0.5, senior: 0.7, normal: 1.0 };
  const pFactor = priorityBonus[userPriority] || 1.0;

  // Position effective
  const effectivePos = Math.max(1, positionInQueue * pFactor);
  const estimated = Math.round(effectivePos * base * peakFactor);

  // Bruit aléatoire ±15%
  const noise = 1 + (Math.random() * 0.3 - 0.15);
  return Math.max(1, Math.round(estimated * noise));
}

// Fonction IA : Score de priorité dynamique
function computePriorityScore(user, requestedAt) {
  const scores = { urgent: 100, handicap: 80, senior: 60, normal: 40 };
  const base = scores[user.priority] || 40;
  // Bonus temps d'attente (+ 1 pt par minute d'attente)
  const waitedMin = (Date.now() - new Date(requestedAt).getTime()) / 60000;
  return base + Math.floor(waitedMin);
}

// POST /api/queues/:serviceId/take-ticket
app.post('/api/queues/:serviceId/take-ticket', authMiddleware, (req, res) => {
  const { serviceId } = req.params;
  const queue = DB.queues[serviceId];
  if (!queue) return res.status(404).json({ error: 'File introuvable' });
  if (queue.status === 'closed') return res.status(400).json({ error: 'Ce service est fermé' });

  // Vérifier si l'utilisateur a déjà un ticket actif dans cette file
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
    status: 'waiting',   // 'waiting' | 'called' | 'served' | 'cancelled'
    requestedAt: new Date().toISOString(),
    calledAt: null,
    servedAt: null,
    estimatedWait: 0,
    priorityScore: 0,
  };

  // Calcul position et temps d'attente
  const waitingCount = queue.tickets.filter(t => t.status === 'waiting').length;
  ticket.priorityScore = computePriorityScore(user, ticket.requestedAt);

  // Tri de la file par score décroissant pour calculer la position réelle
  const sortedWaiting = [...queue.tickets.filter(t => t.status === 'waiting'), ticket]
    .sort((a, b) => b.priorityScore - a.priorityScore);
  const myPos = sortedWaiting.findIndex(t => t.id === ticket.id) + 1;
  ticket.estimatedWait = predictWaitTime(serviceId, myPos, ticket.userPriority);

  queue.tickets.push(ticket);
  DB.tickets.push(ticket);

  // Notification push simulée
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

  // Recalculer les estimations
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

// POST /api/queues/:serviceId/call-next  (Agent/Admin)
app.post('/api/queues/:serviceId/call-next', authMiddleware, (req, res) => {
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

  // Notification pour l'utilisateur appelé
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

// POST /api/queues/:serviceId/serve/:ticketId  (Agent)
app.post('/api/queues/:serviceId/serve/:ticketId', authMiddleware, (req, res) => {
  const { serviceId, ticketId } = req.params;
  const queue = DB.queues[serviceId];
  const ticket = queue?.tickets.find(t => t.id === ticketId);
  if (!ticket) return res.status(404).json({ error: 'Ticket introuvable' });

  ticket.status = 'served';
  ticket.servedAt = new Date().toISOString();

  // Stats
  DB.stats.push({
    serviceId,
    ticketId,
    waitTime: Math.round((new Date(ticket.calledAt || ticket.servedAt) - new Date(ticket.requestedAt)) / 60000),
    date: new Date().toISOString(),
  });

  res.json({ ticket });
});

// DELETE /api/queues/:serviceId/cancel/:ticketId
app.delete('/api/queues/:serviceId/cancel/:ticketId', authMiddleware, (req, res) => {
  const { serviceId, ticketId } = req.params;
  const queue = DB.queues[serviceId];
  const ticket = queue?.tickets.find(t => t.id === ticketId && t.userId === req.user.id);
  if (!ticket) return res.status(404).json({ error: 'Ticket introuvable' });
  if (ticket.status !== 'waiting') return res.status(400).json({ error: 'Impossible d\'annuler ce ticket' });

  ticket.status = 'cancelled';
  res.json({ message: 'Ticket annulé', ticket });
});

// GET /api/my-tickets  (Historique utilisateur)
app.get('/api/my-tickets', authMiddleware, (req, res) => {
  const userTickets = DB.tickets.filter(t => t.userId === req.user.id)
    .sort((a, b) => new Date(b.requestedAt) - new Date(a.requestedAt));
  res.json(userTickets);
});

// ============================================================
// MODULE 4 : NOTIFICATIONS (Firebase Cloud Messaging simulé)
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
// MODULE 5 : STATISTIQUES (Admin)
// ============================================================
app.get('/api/stats', authMiddleware, (req, res) => {
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
    waiting: DB.queues[s.id].tickets.filter(t => t.status === 'waiting').length,
  }));

  const byPriority = ['urgent', 'handicap', 'senior', 'normal'].map(p => ({
    priority: p,
    count: DB.tickets.filter(t => t.userPriority === p).length,
  }));

  res.json({ totalTickets, served, cancelled, waiting, called, avgWait, byService, byPriority });
});

// ============================================================
// MODULE 6 : CHATBOT (Rasa simulé)
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
  if (!message) return res.status(400).json({ error: 'Message requis' });

  const lower = message.toLowerCase();
  let response = chatbotResponses.default;

  for (const [key, val] of Object.entries(chatbotResponses)) {
    if (lower.includes(key)) { response = val; break; }
  }

  // Délai simulé pour l'effet de frappe
  setTimeout(() => {
    res.json({
      message: response,
      timestamp: new Date().toISOString(),
      intent: Object.keys(chatbotResponses).find(k => lower.includes(k)) || 'unknown',
    });
  }, 500);
});

// ============================================================
// MODULE 7 : ADMIN - Gestion des services et des files
// ============================================================
app.put('/api/admin/queues/:serviceId/toggle', authMiddleware, (req, res) => {
  const { serviceId } = req.params;
  const queue = DB.queues[serviceId];
  if (!queue) return res.status(404).json({ error: 'File introuvable' });
  queue.status = queue.status === 'open' ? 'closed' : 'open';
  res.json({ serviceId, status: queue.status });
});

app.get('/api/admin/users', authMiddleware, (req, res) => {
  const users = DB.users.map(({ password: _, ...u }) => u);
  res.json(users);
});

// ============================================================
// HEALTH CHECK
// ============================================================
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', version: '1.0.0', app: 'MonTour API', timestamp: new Date().toISOString() });
});

// ============================================================
// DÉMARRAGE
// ============================================================
app.listen(PORT, () => {
  console.log(`\n🚀 MonTour API démarrée sur http://localhost:${PORT}`);
  console.log(`📋 Routes disponibles :`);
  console.log(`   POST /api/auth/register`);
  console.log(`   POST /api/auth/login`);
  console.log(`   GET  /api/auth/me`);
  console.log(`   GET  /api/services`);
  console.log(`   POST /api/queues/:id/take-ticket`);
  console.log(`   GET  /api/queues/:id`);
  console.log(`   GET  /api/my-tickets`);
  console.log(`   GET  /api/notifications`);
  console.log(`   GET  /api/stats`);
  console.log(`   POST /api/chatbot`);
  console.log(`   GET  /api/health\n`);
});

module.exports = app;