// =============================================================
// MonTour — lib/providers/auth_provider.dart
// Provider Riverpod : gestion de l'authentification
// =============================================================

import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/user_model.dart';
import '../services/api_service.dart';
import '../services/storage_service.dart';

// ─── État de l'auth ───────────────────────────────────────────
final authStateProvider = FutureProvider<UserModel?>((ref) async {
  final json = await StorageService.getUserJson();
  if (json == null) return null;
  try {
    return UserModel.fromJson(jsonDecode(json));
  } catch (_) {
    return null;
  }
});

// ─── Notifier principal ───────────────────────────────────────
class AuthNotifier extends AsyncNotifier<UserModel?> {
  @override
  Future<UserModel?> build() async {
    final json = await StorageService.getUserJson();
    if (json == null) return null;
    try {
      return UserModel.fromJson(jsonDecode(json));
    } catch (_) {
      return null;
    }
  }

  // ── Connexion ─────────────────────────────────────────────
  Future<void> login(String email, String password) async {
    state = const AsyncLoading();
    try {
      final api  = ref.read(apiServiceProvider);
      final data = await api.login(email, password);
      await _saveSession(data);
      state = AsyncData(UserModel.fromJson(data['user']));
    } catch (e, st) {
      state = AsyncError(e, st);
      rethrow;
    }
  }

  // ── Inscription ───────────────────────────────────────────
  Future<void> register(Map<String, dynamic> formData) async {
    state = const AsyncLoading();
    try {
      final api  = ref.read(apiServiceProvider);
      final data = await api.register(formData);
      await _saveSession(data);
      state = AsyncData(UserModel.fromJson(data['user']));
    } catch (e, st) {
      state = AsyncError(e, st);
      rethrow;
    }
  }

  // ── Déconnexion ───────────────────────────────────────────
  Future<void> logout() async {
    try {
      final refresh = await StorageService.getRefreshToken();
      if (refresh != null) {
        await ref.read(apiServiceProvider).logout(refresh);
      }
    } catch (_) {}
    await StorageService.clearTokens();
    await StorageService.clearCache();
    state = const AsyncData(null);
  }

  // ── Mise à jour profil ────────────────────────────────────
  Future<void> updateProfile(Map<String, dynamic> data) async {
    final api    = ref.read(apiServiceProvider);
    final result = await api.updateProfile(data);
    final user   = UserModel.fromJson(result);
    await StorageService.saveUserJson(jsonEncode(user.toJson()));
    state = AsyncData(user);
  }

  // ── Rafraîchir le profil depuis l'API ─────────────────────
  Future<void> refreshProfile() async {
    try {
      final api  = ref.read(apiServiceProvider);
      final data = await api.getMe();
      final user = UserModel.fromJson(data);
      await StorageService.saveUserJson(jsonEncode(user.toJson()));
      state = AsyncData(user);
    } catch (_) {}
  }

  // ── Privé : sauvegarder la session ────────────────────────
  Future<void> _saveSession(Map<String, dynamic> data) async {
    await StorageService.saveTokens(
      access:  data['access'] as String,
      refresh: data['refresh'] as String,
    );
    await StorageService.saveUserJson(jsonEncode(data['user']));

    // Enregistrer le token FCM
    try {
      from montour.utils import NotificationService;
      // ignore: invalid_use_of_protected_member
      // Enregistrer FCM après login
    } catch (_) {}
  }
}

final authNotifierProvider = AsyncNotifierProvider<AuthNotifier, UserModel?>(
  AuthNotifier.new,
);