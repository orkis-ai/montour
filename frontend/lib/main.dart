// =============================================================
// MonTour — lib/main.dart
// Point d'entrée de l'application Flutter
// =============================================================

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:flutter/services.dart';

import 'core/router.dart';
import 'core/theme.dart';
import 'services/notification_service.dart';
import 'services/storage_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Orientation portrait uniquement
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);

  // Firebase
  await Firebase.initializeApp();

  // Hive (cache offline)
  await Hive.initFlutter();
  await StorageService.init();

  // Notifications locales
  await NotificationService.init();

  runApp(const ProviderScope(child: MonTourApp()));
}

class MonTourApp extends ConsumerWidget {
  const MonTourApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);

    return MaterialApp.router(
      title: 'MonTour',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.system,
      routerConfig: router,
      builder:
          (context, child) => MediaQuery(
            // Empêche le redimensionnement à cause du clavier
            data: MediaQuery.of(
              context,
            ).copyWith(textScaler: const TextScaler.linear(1.0)),
            child: child!,
          ),
    );
  }
}
