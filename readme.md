# 🎫 MonTour — Application Mobile Intelligente de Gestion des Files d'Attente

> Mémoire de Master Professionnel — HECM Bénin — OROU KARGA Ismaïla — Mai 2025

---

## 📋 Vue d'ensemble

MonTour est une application mobile intelligente basée sur l'IA pour la gestion des files d'attente dans les services publics et privés au Bénin (zone pilote : Ségbana).

## 🏗️ Architecture du Projet

```
montour/
├── manage.py, montour/     # Projet Django (settings, urls, utilitaires)
├── apps/
│   ├── accounts/           # Utilisateurs, JWT, confirmation d'email, mot de passe oublié
│   ├── services/ queues/ tickets/   # Services, files d'attente, tickets
│   ├── notifications/ chatbot/ stats/
├── templates/index.html    # Application web (React via Babel, servie par Django, PWA)
├── seed.py                 # Données de démonstration (développement)
└── .env.example            # Variables d'environnement à configurer
```

## 🔧 Stack Technologique

| Composant        | Technologies utilisées                                     |
|------------------|------------------------------------------------------------|
| **Frontend**     | React (page unique `templates/index.html`) + PWA           |
| **Backend**      | Django + Django REST Framework                             |
| **Auth**         | JWT (SimpleJWT), confirmation d'email obligatoire          |
| **Base données** | PostgreSQL en production (`DATABASE_URL`), SQLite en local |
| **IA/ML**        | Algorithme prédictif intégré (simule TFLite)               |
| **Chatbot**      | NLP basé sur règles (simule Rasa)                          |

> Comptes, services, files, tickets et notifications passent tous par l'API. L'interface se
> rafraîchit automatiquement (toutes les 6 à 15 s) car la file est partagée entre usagers et agents.

---

## 🚀 Démarrage Rapide

```bash
python -m venv .venv && .venv\Scripts\activate      # Windows (source .venv/bin/activate sous Linux/macOS)
pip install -r requirements.txt
python manage.py migrate
python seed.py                                        # optionnel : comptes et services de démonstration
python manage.py runserver
# → application sur http://localhost:8000 , API sur /api/v1/ , documentation sur /api/docs/
```

Tests : `python manage.py test`

### Configuration

Copiez `.env.example` en `.env` et renseignez au minimum, **en production** :
`SECRET_KEY`, `DATABASE_URL` (sans quoi les données sont perdues sur Vercel — voir `/api/health/`)
et `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` (sans SMTP, aucun email de confirmation n'est délivré).
En local, sans SMTP, les emails s'affichent dans la console du serveur : le lien de confirmation s'y copie.

---

## 📡 API

Documentation interactive complète : **`/api/docs/`** (Swagger) ou `/api/redoc/`.

### 🔐 Authentification (`/api/v1/auth/`)
| Méthode | Route                    | Description                                              |
|---------|--------------------------|----------------------------------------------------------|
| POST    | `register/`              | Créer un compte (inactif) et envoyer l'email de confirmation |
| POST    | `verify-email/`          | Confirmer l'adresse avec le token reçu → renvoie les JWT |
| POST    | `resend-verification/`   | Renvoyer l'email de confirmation                         |
| POST    | `login/`                 | Se connecter (403 tant que l'email n'est pas confirmé)   |
| POST    | `logout/`                | Révoquer le refresh token                                |
| POST    | `token/refresh/`         | Renouveler l'access token                                |
| GET/PUT | `me/`                    | Profil de l'utilisateur connecté                         |
| POST    | `change-password/`       | Changer son mot de passe                                 |
| POST    | `forgot-password/`       | Recevoir un lien de réinitialisation (valable 2 h)       |
| POST    | `reset-password/`        | Choisir un nouveau mot de passe avec le token reçu       |

Les liens des emails ouvrent l'application web (`/?verify_email=…`, `/?reset_password=…`) qui appelle
ensuite l'API en POST : un simple aperçu du lien par un client mail ne consomme donc pas le token.

Autres modules : `services/`, `queues/`, `tickets/`, `notifications/`, `chatbot/`, `stats/` (voir Swagger).

---

## 📲 SMS de rappel

Quand la file avance (appel du suivant, annulation, service), l'API prévient par **notification dans l'app + SMS** :
- les usagers dont il ne reste plus que `SMS_APPROACH_THRESHOLD` personnes devant eux (2 par défaut), **une seule fois par ticket** ;
- l'usager dont le tour est arrivé (SMS « c'est votre tour »).

Chaque usager peut désactiver les SMS ou changer son numéro depuis son profil. Les numéros béninois sont normalisés en `+229 01XXXXXXXX`
(les anciens numéros à 8 chiffres sont acceptés et convertis). Tous les envois, échecs et abandons sont visibles dans l'admin Django (**SMS**).

Envoi via **eSMS Africa** : renseignez `ESMS_API_KEY` (et `ESMS_SENDER_ID` si vous avez un nom d'expéditeur enregistré — obligatoire
au Bénin pour un expéditeur alphanumérique). Sans clé, aucun SMS n'est envoyé ; en développement, `SMS_PROVIDER=console` affiche le SMS
dans la console du serveur. Un échec du fournisseur (solde épuisé, clé refusée…) ne bloque jamais l'appel d'un ticket.
Pour valider la configuration en production : admin Django > Utilisateurs > sélectionner un utilisateur > action
« Envoyer un SMS de test », puis consulter **SMS**.

> L'interface web utilise l'API pour tout (services, files, tickets, notifications) : ses tickets déclenchent donc ces SMS.
> Les quatre services de Ségbana et leurs files sont créés automatiquement par la migration `queues.0002` (aucun compte
> n'est créé) ; on peut en ajouter depuis l'admin Django.

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

Créés par `python seed.py` (**développement uniquement** — ne jamais l'exécuter en production, les mots de passe sont publics) :
- **⚙️ Admin** : `admin@montour.bj` / `admin1234`
- **🏥 Agent** : `agent@montour.bj` / `agent1234`
- **👤 Usager** : `oroukarga@gmail.com` / `user1234`

Tout autre compte créé via l'inscription doit confirmer son email avant de pouvoir se connecter.

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