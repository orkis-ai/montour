// =============================================================
// MonTour — lib/core/router.dart
// Configuration GoRouter — toutes les routes de l'application
// =============================================================

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../providers/auth_provider.dart';
import '../screens/auth/splash_screen.dart';
import '../screens/auth/login_screen.dart';
import '../screens/auth/register_screen.dart';
import '../screens/home/home_screen.dart';
import '../screens/queue/queue_list_screen.dart';
import '../screens/queue/queue_detail_screen.dart';
import '../screens/tickets/my_tickets_screen.dart';
import '../screens/tickets/ticket_detail_screen.dart';
import '../screens/notifications/notifications_screen.dart';
import '../screens/chatbot/chatbot_screen.dart';
import '../screens/profile/profile_screen.dart';
import '../screens/profile/edit_profile_screen.dart';
import '../screens/admin/admin_screen.dart';
import '../screens/admin/admin_queue_screen.dart';
import '../widgets/main_scaffold.dart';

// ─── Routes nommées ───────────────────────────────────────────
class AppRoutes {
  static const splash = '/';
  static const login = '/login';
  static const register = '/register';
  static const home = '/home';
  static const queueList = '/queues';
  static const queueDetail = '/queues/:serviceId';
  static const myTickets = '/tickets';
  static const ticketDetail = '/tickets/:ticketId';
  static const notifications = '/notifications';
  static const chatbot = '/chatbot';
  static const profile = '/profile';
  static const editProfile = '/profile/edit';
  static const admin = '/admin';
  static const adminQueue = '/admin/queue/:queueId';
}

// ─── Provider du Router ───────────────────────────────────────
final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authStateProvider);

  return GoRouter(
    initialLocation: AppRoutes.splash,
    debugLogDiagnostics: true,
    redirect: (context, state) {
      final isLoggedIn = authState.value != null;
      final isAuthRoute = [
        AppRoutes.splash,
        AppRoutes.login,
        AppRoutes.register,
      ].contains(state.matchedLocation);

      if (!isLoggedIn && !isAuthRoute) return AppRoutes.login;
      if (isLoggedIn &&
          isAuthRoute &&
          state.matchedLocation != AppRoutes.splash) {
        return AppRoutes.home;
      }
      return null;
    },
    routes: [
      // ── Auth ────────────────────────────────────────────────
      GoRoute(
        path: AppRoutes.splash,
        builder: (context, state) => const SplashScreen(),
      ),
      GoRoute(
        path: AppRoutes.login,
        pageBuilder:
            (context, state) => _fadeTransition(state, const LoginScreen()),
      ),
      GoRoute(
        path: AppRoutes.register,
        pageBuilder:
            (context, state) => _slideTransition(state, const RegisterScreen()),
      ),

      // ── Shell avec NavBar ────────────────────────────────────
      ShellRoute(
        builder: (context, state, child) => MainScaffold(child: child),
        routes: [
          GoRoute(
            path: AppRoutes.home,
            builder: (context, state) => const HomeScreen(),
          ),
          GoRoute(
            path: AppRoutes.queueList,
            builder: (context, state) => const QueueListScreen(),
            routes: [
              GoRoute(
                path: ':serviceId',
                builder:
                    (context, state) => QueueDetailScreen(
                      serviceId: state.pathParameters['serviceId']!,
                    ),
              ),
            ],
          ),
          GoRoute(
            path: AppRoutes.myTickets,
            builder: (context, state) => const MyTicketsScreen(),
            routes: [
              GoRoute(
                path: ':ticketId',
                builder:
                    (context, state) => TicketDetailScreen(
                      ticketId: state.pathParameters['ticketId']!,
                    ),
              ),
            ],
          ),
          GoRoute(
            path: AppRoutes.notifications,
            builder: (context, state) => const NotificationsScreen(),
          ),
          GoRoute(
            path: AppRoutes.chatbot,
            builder: (context, state) => const ChatbotScreen(),
          ),
          GoRoute(
            path: AppRoutes.profile,
            builder: (context, state) => const ProfileScreen(),
            routes: [
              GoRoute(
                path: 'edit',
                builder: (context, state) => const EditProfileScreen(),
              ),
            ],
          ),
          GoRoute(
            path: AppRoutes.admin,
            builder: (context, state) => const AdminScreen(),
            routes: [
              GoRoute(
                path: 'queue/:queueId',
                builder:
                    (context, state) => AdminQueueScreen(
                      queueId: state.pathParameters['queueId']!,
                    ),
              ),
            ],
          ),
        ],
      ),
    ],
    errorBuilder:
        (context, state) => Scaffold(
          body: Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text('🔍', style: TextStyle(fontSize: 48)),
                const SizedBox(height: 16),
                Text(
                  'Page introuvable',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 8),
                TextButton(
                  onPressed: () => context.go(AppRoutes.home),
                  child: const Text('Retour à l\'accueil'),
                ),
              ],
            ),
          ),
        ),
  );
});

CustomTransitionPage _fadeTransition(GoRouterState state, Widget child) =>
    CustomTransitionPage(
      key: state.pageKey,
      child: child,
      transitionsBuilder:
          (context, animation, _, child) =>
              FadeTransition(opacity: animation, child: child),
    );

CustomTransitionPage _slideTransition(GoRouterState state, Widget child) =>
    CustomTransitionPage(
      key: state.pageKey,
      child: child,
      transitionsBuilder:
          (context, animation, _, child) => SlideTransition(
            position: animation.drive(
              Tween(
                begin: const Offset(1.0, 0.0),
                end: Offset.zero,
              ).chain(CurveTween(curve: Curves.easeInOut)),
            ),
            child: child,
          ),
    );
