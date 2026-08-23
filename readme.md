# 🎫 MonTour — Application Mobile Intelligente de Gestion des Files d'Attente

> Mémoire de Master Professionnel — HECM Bénin — OROU KARGA Ismaïla — Mai 2025

---

## 📋 Vue d'ensemble

MonTour est une application mobile intelligente basée sur l'IA pour la gestion des files d'attente dans les services publics et privés au Bénin (zone pilote : Ségbana).

## 🏗️ Architecture du Projet

```
MonTour/
├── backend/              # API REST (Node.js/Express — simule Django)
│   ├── server.js         # Serveur principal avec tous les modules
│   └── package.json      # Dépendances backend
│
└── frontend/             # Application React (simule Flutter)
    └── MonTour_App.jsx   # Application complète (toutes les pages)
```

## 🔧 Stack Technologique

| Composant        | Technologies utilisées                          |
|------------------|-------------------------------------------------|
| **Frontend**     | React (simule Flutter) + Hooks + localStorage   |
| **Backend**      | Node.js + Express (simule Django REST Framework)|
| **Auth**         | JWT + bcryptjs (simule Firebase Authentication) |
| **Base données** | In-memory + localStorage (simule PostgreSQL)    |
| **IA/ML**        | Algorithme prédictif intégré (simule TFLite)    |
| **Chatbot**      | NLP basé sur règles (simule Rasa)               |
| **Notifs**       | Système push intégré (simule Firebase FCM)      |

---

## 🚀 Démarrage Rapide

### Backend (API)

```bash
# 1. Installer les dépendances
cd backend
npm install

# 2. Lancer le serveur
node server.js
# → API disponible sur http://localhost:4000
```

### Frontend (React)

```bash
# Créer un projet React
npx create-react-app montour-app
cd montour-app

# Copier MonTour_App.jsx dans src/App.jsx
cp MonTour_App.jsx src/App.jsx

# Lancer l'app
npm start
# → App disponible sur http://localhost:3000
```

---

## 📡 API Endpoints

### 🔐 Authentification
| Méthode | Route              | Description                    |
|---------|--------------------|--------------------------------|
| POST    | /api/auth/register | Créer un compte                |
| POST    | /api/auth/login    | Se connecter                   |
| GET     | /api/auth/me       | Profil de l'utilisateur        |
| PUT     | /api/auth/profile  | Mettre à jour le profil        |

### 🏛️ Services
| Méthode | Route             | Description                    |
|---------|-------------------|--------------------------------|
| GET     | /api/services     | Liste tous les services        |
| GET     | /api/services/:id | Détail d'un service            |

### 🎫 Files d'attente & Tickets
| Méthode | Route                               | Description                |
|---------|-------------------------------------|----------------------------|
| POST    | /api/queues/:serviceId/take-ticket  | Prendre un ticket          |
| GET     | /api/queues/:serviceId              | État de la file            |
| POST    | /api/queues/:serviceId/call-next    | Appeler le prochain (agent)|
| POST    | /api/queues/:serviceId/serve/:id   | Marquer comme servi        |
| DELETE  | /api/queues/:serviceId/cancel/:id  | Annuler un ticket          |
| GET     | /api/my-tickets                    | Historique utilisateur     |

### 🔔 Notifications
| Méthode | Route                         | Description              |
|---------|-------------------------------|--------------------------|
| GET     | /api/notifications            | Lister les notifications |
| PUT     | /api/notifications/read-all   | Tout marquer comme lu    |

### 📊 Statistiques (Admin)
| Méthode | Route      | Description              |
|---------|------------|--------------------------|
| GET     | /api/stats | Statistiques globales    |

### 🤖 Chatbot (Rasa simulé)
| Méthode | Route         | Description         |
|---------|---------------|---------------------|
| POST    | /api/chatbot  | Envoyer un message  |

---

## 🤖 Modules IA

### 1. Prédiction du Temps d'Attente (TFLite simulé)
```javascript
// Paramètres pris en compte :
- Position dans la file
- Heure de la journée (facteur de pointe)
- Niveau de priorité de l'utilisateur
- Temps de service moyen du service
- Bruit aléatoire ±15% (réalisme)
```

### 2. Score de Priorité Dynamique
```javascript
// Calcul :
scores = { urgent: 100, handicap: 80, senior: 60, normal: 40 }
priorityScore = base_score + minutes_waited
// La file est triée par score décroissant
```

### 3. Chatbot NLP (Rasa simulé)
```
Intentions reconnues : bonjour, ticket, attente, annuler,
                       priorité, notification, horaire, aide
```

---

## 📱 Pages de l'Application

| Page            | Description                                    |
|-----------------|------------------------------------------------|
| 🎫 Splash       | Écran d'accueil avec branding MonTour          |
| 🔐 Connexion    | Login email/password + Google + démo rapide    |
| 📝 Inscription  | Création de compte avec niveau de priorité     |
| 🏠 Dashboard    | Vue d'ensemble : ticket actif, stats, services |
| 🎫 File         | Prendre/suivre/annuler un ticket par service   |
| 📋 Mes Tickets  | Historique complet des tickets                 |
| 🔔 Notifications| Centre de notifications push                  |
| 🤖 Chatbot      | Assistant IA conversationnel                   |
| 👤 Profil       | Gestion du compte et des préférences          |
| ⚙️ Admin        | Stats, gestion des files, agents              |

---

## 👥 Rôles Utilisateurs

| Rôle    | Accès                                           |
|---------|-------------------------------------------------|
| `user`  | Prendre ticket, consulter file, chatbot, profil |
| `agent` | + Appeler le suivant, marquer servi             |
| `admin` | + Statistiques, gestion des services, agents   |

---

## 🧪 Comptes de Démonstration

Utilisez les boutons "Accès Démo Rapide" sur la page de connexion :
- **👤 Usager** : `moussa@demo.bj` / demo
- **🏥 Agent** : `agent@demo.bj` / demo  
- **⚙️ Admin** : `admin@demo.bj` / demo

---

## 📍 Services Disponibles

| Service                   | Temps moyen | Couleur    |
|---------------------------|-------------|------------|
| 🏥 Centre de Santé        | 12 min      | Rouge      |
| 🏛️ Guichet Administratif  | 8 min       | Bleu       |
| 🏦 Agence PEBCO           | 10 min      | Vert       |
| 🌾 ATDA Pôle 4            | 15 min      | Orange     |

---

## 🔮 Perspectives d'Évolution

- [ ] Déploiement Flutter natif Android/iOS
- [ ] Backend Django REST Framework (Python)
- [ ] Base de données PostgreSQL
- [ ] Firebase Authentication réel
- [ ] TensorFlow Lite embarqué
- [ ] Rasa NLP multilingue (français + langues locales)
- [ ] Interface vocale pour analphabètes
- [ ] Extension blockchain pour traçabilité
- [ ] Déploiement multi-communes (Alibori)

---

## 📚 Références Techniques

- Flutter : https://flutter.dev
- Django REST Framework : https://www.django-rest-framework.org
- TensorFlow Lite : https://www.tensorflow.org/lite
- Firebase : https://firebase.google.com
- Rasa NLP : https://rasa.com

---

*Prototypage d'une application mobile intelligente MonTour pour la gestion des files d'attente basée sur l'IA*  
*OROU KARGA Ismaïla — HECM Bénin — Mai 2025*