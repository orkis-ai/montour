// =============================================================
// MonTour — lib/services/api_service.dart
// Client HTTP Dio centralisé avec intercepteurs JWT
// =============================================================

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'storage_service.dart';

const _baseUrl = 'http://10.0.2.2:8000/api/v1'; // Android emulator → localhost
// const _baseUrl = 'http://192.168.1.X:8000/api/v1';  // Device réel
// const _baseUrl = 'https://api.montour.bj/api/v1';   // Production

final dioProvider = Provider<Dio>((ref) {
  final dio = Dio(
    BaseOptions(
      baseUrl: _baseUrl,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 15),
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ),
  );

  dio.interceptors.add(_AuthInterceptor(dio));
  dio.interceptors.add(
    LogInterceptor(
      requestBody: true,
      responseBody: true,
      logPrint: (o) => print('[DIO] $o'),
    ),
  );

  return dio;
});

// ─── Intercepteur JWT ─────────────────────────────────────────
class _AuthInterceptor extends Interceptor {
  final Dio _dio;
  _AuthInterceptor(this._dio);

  @override
  void onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await StorageService.getAccessToken();
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode == 401) {
      // Tentative de rafraîchissement du token
      try {
        final refreshToken = await StorageService.getRefreshToken();
        if (refreshToken == null) return handler.next(err);

        final resp = await _dio.post(
          '/auth/token/refresh/',
          data: {'refresh': refreshToken},
        );
        final newAccess = resp.data['access'] as String;
        await StorageService.saveAccessToken(newAccess);

        // Relancer la requête originale
        err.requestOptions.headers['Authorization'] = 'Bearer $newAccess';
        final retryResp = await _dio.fetch(err.requestOptions);
        return handler.resolve(retryResp);
      } catch (_) {
        await StorageService.clearTokens();
        return handler.next(err);
      }
    }
    handler.next(err);
  }
}

// ─── Classe ApiService ────────────────────────────────────────
class ApiService {
  final Dio _dio;
  ApiService(this._dio);

  // ── Auth ──────────────────────────────────────────────────
  Future<Map<String, dynamic>> register(Map<String, dynamic> data) async {
    final r = await _dio.post('/auth/register/', data: data);
    return r.data['data'];
  }

  Future<Map<String, dynamic>> login(String email, String password) async {
    final r = await _dio.post(
      '/auth/login/',
      data: {'email': email, 'password': password},
    );
    return r.data['data'];
  }

  Future<void> logout(String refreshToken) async {
    await _dio.post('/auth/logout/', data: {'refresh': refreshToken});
  }

  Future<Map<String, dynamic>> getMe() async {
    final r = await _dio.get('/auth/me/');
    return r.data['data'];
  }

  Future<Map<String, dynamic>> updateProfile(Map<String, dynamic> data) async {
    final r = await _dio.put('/auth/me/', data: data);
    return r.data['data'];
  }

  Future<void> changePassword(Map<String, dynamic> data) async {
    await _dio.post('/auth/change-password/', data: data);
  }

  Future<void> registerFCMToken(String token, String deviceType) async {
    await _dio.post(
      '/auth/fcm-token/',
      data: {'token': token, 'device_type': deviceType},
    );
  }

  // ── Services ─────────────────────────────────────────────
  Future<List<dynamic>> getServices() async {
    final r = await _dio.get('/services/');
    return r.data['data'];
  }

  Future<Map<String, dynamic>> getService(String id) async {
    final r = await _dio.get('/services/$id/');
    return r.data['data'];
  }

  // ── Files d'attente ───────────────────────────────────────
  Future<List<dynamic>> getQueues() async {
    final r = await _dio.get('/queues/');
    return r.data['data'];
  }

  Future<Map<String, dynamic>> getQueue(String serviceId) async {
    final r = await _dio.get('/queues/$serviceId/');
    return r.data['data'];
  }

  Future<void> toggleQueue(String queueId) async {
    await _dio.post('/queues/$queueId/toggle/');
  }

  Future<void> resetQueue(String queueId) async {
    await _dio.post('/queues/$queueId/reset/');
  }

  // ── Tickets ───────────────────────────────────────────────
  Future<Map<String, dynamic>> takeTicket(String queueId) async {
    final r = await _dio.post('/tickets/take/$queueId/');
    return r.data['data'];
  }

  Future<List<dynamic>> getMyTickets({String? status}) async {
    final r = await _dio.get(
      '/tickets/mine/',
      queryParameters: status != null ? {'status': status} : null,
    );
    return r.data['data'];
  }

  Future<void> cancelTicket(String ticketId) async {
    await _dio.delete('/tickets/$ticketId/cancel/');
  }

  Future<Map<String, dynamic>> callNextTicket(String queueId) async {
    final r = await _dio.post('/tickets/queues/$queueId/call-next/');
    return r.data['data'];
  }

  Future<void> serveTicket(String ticketId) async {
    await _dio.post('/tickets/$ticketId/serve/');
  }

  Future<void> rateTicket(String ticketId, int rating, String feedback) async {
    await _dio.post(
      '/tickets/$ticketId/rate/',
      data: {'rating': rating, 'feedback': feedback},
    );
  }

  Future<List<dynamic>> getQueueTickets(
    String queueId, {
    String status = 'waiting',
  }) async {
    final r = await _dio.get(
      '/tickets/queues/$queueId/',
      queryParameters: {'status': status},
    );
    return r.data['data'];
  }

  // ── Notifications ─────────────────────────────────────────
  Future<List<dynamic>> getNotifications({bool unreadOnly = false}) async {
    final r = await _dio.get(
      '/notifications/',
      queryParameters: unreadOnly ? {'unread': '1'} : null,
    );
    return r.data['data'];
  }

  Future<int> getUnreadCount() async {
    final r = await _dio.get('/notifications/unread-count/');
    return r.data['data']['unread_count'] as int;
  }

  Future<void> markAllRead() async {
    await _dio.put('/notifications/read-all/');
  }

  Future<void> markRead(String notifId) async {
    await _dio.put('/notifications/$notifId/read/');
  }

  Future<void> deleteNotification(String notifId) async {
    await _dio.delete('/notifications/$notifId/delete/');
  }

  // ── Chatbot ───────────────────────────────────────────────
  Future<Map<String, dynamic>> sendChatMessage(String message) async {
    final r = await _dio.post('/chatbot/message/', data: {'message': message});
    return r.data['data'];
  }

  Future<List<dynamic>> getChatHistory() async {
    final r = await _dio.get('/chatbot/history/');
    return r.data['data'];
  }

  Future<void> clearChat() async {
    await _dio.delete('/chatbot/clear/');
  }

  // ── Statistiques ──────────────────────────────────────────
  Future<Map<String, dynamic>> getGlobalStats() async {
    final r = await _dio.get('/stats/');
    return r.data['data'];
  }

  Future<Map<String, dynamic>> getMyStats() async {
    final r = await _dio.get('/stats/me/');
    return r.data['data'];
  }

  Future<Map<String, dynamic>> getServiceStats(String serviceId) async {
    final r = await _dio.get('/stats/services/$serviceId/');
    return r.data['data'];
  }
}

final apiServiceProvider = Provider<ApiService>((ref) {
  return ApiService(ref.watch(dioProvider));
});
