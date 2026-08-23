// =============================================================
// MonTour — lib/services/storage_service.dart
// Stockage sécurisé des tokens JWT et préférences
// =============================================================

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:hive_flutter/hive_flutter.dart';

class StorageService {
  static const _storage = FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
  );

  static const _keyAccess = 'mt_access_token';
  static const _keyRefresh = 'mt_refresh_token';
  static const _keyUser = 'mt_user_json';

  static late Box _cacheBox;

  static Future<void> init() async {
    _cacheBox = await Hive.openBox('montour_cache');
  }

  // ── JWT Tokens ────────────────────────────────────────────
  static Future<void> saveTokens({
    required String access,
    required String refresh,
  }) async {
    await _storage.write(key: _keyAccess, value: access);
    await _storage.write(key: _keyRefresh, value: refresh);
  }

  static Future<String?> getAccessToken() => _storage.read(key: _keyAccess);
  static Future<String?> getRefreshToken() => _storage.read(key: _keyRefresh);

  static Future<void> saveAccessToken(String token) =>
      _storage.write(key: _keyAccess, value: token);

  static Future<void> clearTokens() async {
    await _storage.delete(key: _keyAccess);
    await _storage.delete(key: _keyRefresh);
    await _storage.delete(key: _keyUser);
  }

  // ── Cache utilisateur ─────────────────────────────────────
  static Future<void> saveUserJson(String json) =>
      _storage.write(key: _keyUser, value: json);

  static Future<String?> getUserJson() => _storage.read(key: _keyUser);

  // ── Cache Hive (données offline) ──────────────────────────
  static void put(String key, dynamic value) => _cacheBox.put(key, value);
  static dynamic get(String key, {dynamic defaultValue}) =>
      _cacheBox.get(key, defaultValue: defaultValue);
  static Future<void> delete(String key) => _cacheBox.delete(key);
  static Future<void> clearCache() => _cacheBox.clear();
}
