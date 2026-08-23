// =============================================================
// MonTour — lib/providers/services_provider.dart
// =============================================================

import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/service_model.dart';
import '../services/api_service.dart';

final servicesProvider = FutureProvider<List<ServiceModel>>((ref) async {
  final api  = ref.watch(apiServiceProvider);
  final data = await api.getServices();
  return data.map((e) => ServiceModel.fromJson(e)).toList();
});

final serviceDetailProvider = FutureProvider.family<ServiceModel, String>((ref, id) async {
  final api  = ref.watch(apiServiceProvider);
  final data = await api.getService(id);
  return ServiceModel.fromJson(data);
});


// =============================================================
// MonTour — lib/providers/queue_provider.dart
// =============================================================

import '../models/queue_model.dart';

final queueDetailProvider = FutureProvider.family<QueueModel, String>((ref, serviceId) async {
  final api  = ref.watch(apiServiceProvider);
  final data = await api.getQueue(serviceId);
  return QueueModel.fromJson(data);
});

// Auto-refresh toutes les 5 secondes
final queueStreamProvider = StreamProvider.family<QueueModel, String>((ref, serviceId) async* {
  while (true) {
    try {
      final api  = ref.read(apiServiceProvider);
      final data = await api.getQueue(serviceId);
      yield QueueModel.fromJson(data);
    } catch (_) {}
    await Future.delayed(const Duration(seconds: 5));
  }
});


// =============================================================
// MonTour — lib/providers/tickets_provider.dart
// =============================================================

import '../models/ticket_model.dart';

class TicketsNotifier extends AsyncNotifier<List<TicketModel>> {
  @override
  Future<List<TicketModel>> build() => _fetchTickets();

  Future<List<TicketModel>> _fetchTickets() async {
    final api  = ref.read(apiServiceProvider);
    final data = await api.getMyTickets();
    return data.map((e) => TicketModel.fromJson(e)).toList();
  }

  Future<TicketModel> takeTicket(String queueId) async {
    final api    = ref.read(apiServiceProvider);
    final result = await api.takeTicket(queueId);
    final ticket = TicketModel.fromJson(result['ticket']);
    state = AsyncData([ticket, ...?state.value]);
    return ticket;
  }

  Future<void> cancelTicket(String ticketId) async {
    await ref.read(apiServiceProvider).cancelTicket(ticketId);
    await refresh();
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = AsyncData(await _fetchTickets());
  }

  TicketModel? get activeTicket {
    return state.value?.firstWhere(
      (t) => t.isActive,
      orElse: () => throw StateError('no active'),
    );
  }
}

final ticketsNotifierProvider = AsyncNotifierProvider<TicketsNotifier, List<TicketModel>>(
  TicketsNotifier.new,
);

// Ticket actif
final activeTicketProvider = Provider<TicketModel?>((ref) {
  final tickets = ref.watch(ticketsNotifierProvider).value ?? [];
  try {
    return tickets.firstWhere((t) => t.isActive);
  } catch (_) {
    return null;
  }
});


// =============================================================
// MonTour — lib/providers/notifications_provider.dart
// =============================================================

import '../models/notification_model.dart';

class NotificationsNotifier extends AsyncNotifier<List<NotificationModel>> {
  @override
  Future<List<NotificationModel>> build() => _fetch();

  Future<List<NotificationModel>> _fetch() async {
    final data = await ref.read(apiServiceProvider).getNotifications();
    return data.map((e) => NotificationModel.fromJson(e)).toList();
  }

  Future<void> markAllRead() async {
    await ref.read(apiServiceProvider).markAllRead();
    state = AsyncData(
      (state.value ?? []).map((n) => NotificationModel(
        id: n.id, type: n.type, title: n.title,
        message: n.message, isRead: true,
        createdAt: n.createdAt,
      )).toList(),
    );
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = AsyncData(await _fetch());
  }

  int get unreadCount =>
      (state.value ?? []).where((n) => !n.isRead).length;
}

final notificationsProvider = AsyncNotifierProvider<NotificationsNotifier, List<NotificationModel>>(
  NotificationsNotifier.new,
);

final unreadCountProvider = Provider<int>((ref) {
  return ref.watch(notificationsProvider).value?.where((n) => !n.isRead).length ?? 0;
});


// =============================================================
// MonTour — lib/providers/stats_provider.dart
// =============================================================

final globalStatsProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  return ref.watch(apiServiceProvider).getGlobalStats();
});

final myStatsProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  return ref.watch(apiServiceProvider).getMyStats();
});


// =============================================================
// MonTour — lib/providers/chatbot_provider.dart
// =============================================================

class ChatMessage {
  final String id;
  final String content;
  final String role; // 'user' | 'bot'
  final DateTime createdAt;

  const ChatMessage({
    required this.id, required this.content,
    required this.role, required this.createdAt,
  });
}

class ChatbotNotifier extends AsyncNotifier<List<ChatMessage>> {
  @override
  Future<List<ChatMessage>> build() async {
    final data = await ref.read(apiServiceProvider).getChatHistory();
    return data.map((m) => ChatMessage(
      id: m['id'] as String,
      content: m['content'] as String,
      role: m['role'] as String,
      createdAt: DateTime.parse(m['created_at'] as String),
    )).toList();
  }

  Future<void> sendMessage(String text) async {
    final userMsg = ChatMessage(
      id: DateTime.now().toIso8601String(),
      content: text,
      role: 'user',
      createdAt: DateTime.now(),
    );
    state = AsyncData([...?state.value, userMsg]);

    try {
      final result = await ref.read(apiServiceProvider).sendChatMessage(text);
      final botMsg = ChatMessage(
        id: result['message_id'] as String? ?? DateTime.now().toIso8601String(),
        content: result['message'] as String,
        role: 'bot',
        createdAt: DateTime.now(),
      );
      state = AsyncData([...?state.value, botMsg]);
    } catch (e) {
      final errMsg = ChatMessage(
        id: DateTime.now().toIso8601String(),
        content: 'Désolé, je rencontre un problème de connexion. Réessayez plus tard.',
        role: 'bot',
        createdAt: DateTime.now(),
      );
      state = AsyncData([...?state.value, errMsg]);
    }
  }

  Future<void> clearHistory() async {
    await ref.read(apiServiceProvider).clearChat();
    state = const AsyncData([]);
  }
}

final chatbotProvider = AsyncNotifierProvider<ChatbotNotifier, List<ChatMessage>>(
  ChatbotNotifier.new,
);