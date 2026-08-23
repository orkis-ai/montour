// =============================================================
// MonTour — lib/models/user_model.dart
// =============================================================

class UserModel {
  final String id;
  final String username;
  final String email;
  final String phone;
  final String role; // 'user' | 'agent' | 'admin'
  final String priority; // 'normal' | 'senior' | 'handicap' | 'urgent'
  final String? avatarUrl;
  final DateTime? dateJoined;
  final DateTime? lastLogin;

  const UserModel({
    required this.id,
    required this.username,
    required this.email,
    required this.phone,
    required this.role,
    required this.priority,
    this.avatarUrl,
    this.dateJoined,
    this.lastLogin,
  });

  bool get isAdmin => role == 'admin';
  bool get isAgent => role == 'agent' || role == 'admin';

  String get priorityLabel {
    const map = {
      'urgent': '🚨 Urgent',
      'handicap': '♿ Handicap',
      'senior': '👴 Senior',
      'normal': '👤 Normal',
    };
    return map[priority] ?? '👤 Normal';
  }

  factory UserModel.fromJson(Map<String, dynamic> json) => UserModel(
    id: json['id'] as String,
    username: json['username'] as String,
    email: json['email'] as String,
    phone: json['phone'] as String? ?? '',
    role: json['role'] as String? ?? 'user',
    priority: json['priority'] as String? ?? 'normal',
    avatarUrl: json['avatar_url'] as String?,
    dateJoined:
        json['date_joined'] != null
            ? DateTime.parse(json['date_joined'])
            : null,
    lastLogin:
        json['last_login'] != null ? DateTime.parse(json['last_login']) : null,
  );

  Map<String, dynamic> toJson() => {
    'id': id,
    'username': username,
    'email': email,
    'phone': phone,
    'role': role,
    'priority': priority,
  };

  UserModel copyWith({
    String? username,
    String? phone,
    String? priority,
    String? avatarUrl,
  }) => UserModel(
    id: id,
    email: email,
    role: role,
    username: username ?? this.username,
    phone: phone ?? this.phone,
    priority: priority ?? this.priority,
    avatarUrl: avatarUrl ?? this.avatarUrl,
    dateJoined: dateJoined,
    lastLogin: lastLogin,
  );
}

// =============================================================
// lib/models/service_model.dart
// =============================================================

class ServiceModel {
  final String id;
  final String name;
  final String description;
  final String category;
  final String icon;
  final String color;
  final int avgServiceTime;
  final String address;
  final bool isActive;
  final int queueLength;
  final String queueStatus;
  final int currentNumber;

  const ServiceModel({
    required this.id,
    required this.name,
    required this.description,
    required this.category,
    required this.icon,
    required this.color,
    required this.avgServiceTime,
    required this.address,
    required this.isActive,
    required this.queueLength,
    required this.queueStatus,
    required this.currentNumber,
  });

  bool get isOpen => queueStatus == 'open';

  factory ServiceModel.fromJson(Map<String, dynamic> json) => ServiceModel(
    id: json['id'] as String,
    name: json['name'] as String,
    description: json['description'] as String? ?? '',
    category: json['category'] as String? ?? 'other',
    icon: json['icon'] as String? ?? '🏢',
    color: json['color'] as String? ?? '#1a73e8',
    avgServiceTime: json['avg_service_time'] as int? ?? 10,
    address: json['address'] as String? ?? '',
    isActive: json['is_active'] as bool? ?? true,
    queueLength: json['queue_length'] as int? ?? 0,
    queueStatus: json['queue_status'] as String? ?? 'closed',
    currentNumber: json['current_number'] as int? ?? 0,
  );
}

// =============================================================
// lib/models/ticket_model.dart
// =============================================================

class TicketModel {
  final String id;
  final int number;
  final String status;
  final String priority;
  final int priorityScore;
  final int estimatedWait;
  final int? actualWait;
  final int? position;
  final String serviceName;
  final String serviceIcon;
  final String serviceColor;
  final String userName;
  final DateTime requestedAt;
  final DateTime? calledAt;
  final DateTime? servedAt;
  final DateTime? cancelledAt;
  final int? rating;

  const TicketModel({
    required this.id,
    required this.number,
    required this.status,
    required this.priority,
    required this.priorityScore,
    required this.estimatedWait,
    required this.serviceName,
    required this.serviceIcon,
    required this.serviceColor,
    required this.userName,
    required this.requestedAt,
    this.actualWait,
    this.position,
    this.calledAt,
    this.servedAt,
    this.cancelledAt,
    this.rating,
  });

  bool get isActive => status == 'waiting' || status == 'called';
  bool get isWaiting => status == 'waiting';
  bool get isCalled => status == 'called';
  bool get isServed => status == 'served';
  bool get isCancelled => status == 'cancelled';

  String get statusLabel {
    const map = {
      'waiting': '⏳ En attente',
      'called': '📢 Appelé',
      'served': '✅ Servi',
      'cancelled': '❌ Annulé',
      'missed': '⚠️ Absent',
    };
    return map[status] ?? status;
  }

  factory TicketModel.fromJson(Map<String, dynamic> json) => TicketModel(
    id: json['id'] as String,
    number: json['number'] as int,
    status: json['status'] as String,
    priority: json['priority'] as String? ?? 'normal',
    priorityScore: json['priority_score'] as int? ?? 0,
    estimatedWait: json['estimated_wait'] as int? ?? 0,
    actualWait: json['actual_wait'] as int?,
    position: json['position'] as int?,
    serviceName: json['service_name'] as String? ?? '',
    serviceIcon: json['service_icon'] as String? ?? '🏢',
    serviceColor: json['service_color'] as String? ?? '#1a73e8',
    userName: json['user_name'] as String? ?? '',
    requestedAt: DateTime.parse(json['requested_at'] as String),
    calledAt:
        json['called_at'] != null ? DateTime.parse(json['called_at']) : null,
    servedAt:
        json['served_at'] != null ? DateTime.parse(json['served_at']) : null,
    cancelledAt:
        json['cancelled_at'] != null
            ? DateTime.parse(json['cancelled_at'])
            : null,
    rating: json['rating'] as int?,
  );
}

// =============================================================
// lib/models/notification_model.dart
// =============================================================

class NotificationModel {
  final String id;
  final String type;
  final String title;
  final String message;
  final bool isRead;
  final DateTime createdAt;
  final DateTime? readAt;

  const NotificationModel({
    required this.id,
    required this.type,
    required this.title,
    required this.message,
    required this.isRead,
    required this.createdAt,
    this.readAt,
  });

  String get typeIcon {
    const map = {
      'ticket_taken': '🎫',
      'your_turn': '🔔',
      'reminder': '⏰',
      'info': 'ℹ️',
      'warning': '⚠️',
    };
    return map[type] ?? '📢';
  }

  factory NotificationModel.fromJson(Map<String, dynamic> json) =>
      NotificationModel(
        id: json['id'] as String,
        type: json['type'] as String? ?? 'info',
        title: json['title'] as String,
        message: json['message'] as String,
        isRead: json['is_read'] as bool? ?? false,
        createdAt: DateTime.parse(json['created_at'] as String),
        readAt:
            json['read_at'] != null ? DateTime.parse(json['read_at']) : null,
      );
}

// =============================================================
// lib/models/queue_model.dart
// =============================================================

class QueueModel {
  final String id;
  final String serviceName;
  final String serviceIcon;
  final String serviceColor;
  final String status;
  final int currentNumber;
  final int calledNumber;
  final int maxCapacity;
  final int waitingCount;
  final List<TicketModel> tickets;

  const QueueModel({
    required this.id,
    required this.serviceName,
    required this.serviceIcon,
    required this.serviceColor,
    required this.status,
    required this.currentNumber,
    required this.calledNumber,
    required this.maxCapacity,
    required this.waitingCount,
    required this.tickets,
  });

  bool get isOpen => status == 'open';

  factory QueueModel.fromJson(Map<String, dynamic> json) => QueueModel(
    id: json['id'] as String,
    serviceName: json['service_name'] as String? ?? '',
    serviceIcon: json['service_icon'] as String? ?? '🏢',
    serviceColor: json['service_color'] as String? ?? '#1a73e8',
    status: json['status'] as String? ?? 'closed',
    currentNumber: json['current_number'] as int? ?? 0,
    calledNumber: json['called_number'] as int? ?? 0,
    maxCapacity: json['max_capacity'] as int? ?? 100,
    waitingCount: json['waiting_count'] as int? ?? 0,
    tickets:
        (json['tickets'] as List<dynamic>? ?? [])
            .map((t) => TicketModel.fromJson(t as Map<String, dynamic>))
            .toList(),
  );
}
