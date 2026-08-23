// =============================================================
// MonTour — lib/widgets/main_scaffold.dart
// Shell principal avec barre de navigation inférieure
// =============================================================

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../core/router.dart';
import '../core/theme.dart';
import '../providers/auth_provider.dart';
import '../providers/notifications_provider.dart';

class MainScaffold extends ConsumerWidget {
  final Widget child;
  const MainScaffold({super.key, required this.child});

  static const _tabs = [
    (AppRoutes.home, Icons.home_outlined, Icons.home, 'Accueil'),
    (AppRoutes.queueList, Icons.queue_outlined, Icons.queue, 'File'),
    (
      AppRoutes.myTickets,
      Icons.confirmation_number_outlined,
      Icons.confirmation_number,
      'Tickets',
    ),
    (AppRoutes.chatbot, Icons.smart_toy_outlined, Icons.smart_toy, 'Assistant'),
    (AppRoutes.profile, Icons.person_outlined, Icons.person, 'Profil'),
  ];

  static const _adminTabs = [
    (AppRoutes.home, Icons.home_outlined, Icons.home, 'Accueil'),
    (AppRoutes.queueList, Icons.queue_outlined, Icons.queue, 'File'),
    (
      AppRoutes.myTickets,
      Icons.confirmation_number_outlined,
      Icons.confirmation_number,
      'Tickets',
    ),
    (
      AppRoutes.admin,
      Icons.admin_panel_settings_outlined,
      Icons.admin_panel_settings,
      'Admin',
    ),
    (AppRoutes.profile, Icons.person_outlined, Icons.person, 'Profil'),
  ];

  int _currentIndex(String location) {
    if (location.startsWith(AppRoutes.home)) return 0;
    if (location.startsWith(AppRoutes.queueList)) return 1;
    if (location.startsWith(AppRoutes.myTickets)) return 2;
    if (location.startsWith(AppRoutes.chatbot)) return 3;
    if (location.startsWith(AppRoutes.admin)) return 3;
    if (location.startsWith(AppRoutes.profile)) return 4;
    return 0;
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authNotifierProvider).value;
    final unread = ref.watch(unreadCountProvider);
    final isAdmin = user?.isAgent ?? false;
    final tabs = isAdmin ? _adminTabs : _tabs;
    final location = GoRouterState.of(context).uri.toString();
    final curIdx = _currentIndex(location);

    return Scaffold(
      body: child,
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.08),
              blurRadius: 20,
              offset: const Offset(0, -4),
            ),
          ],
          border: const Border(
            top: BorderSide(color: AppColors.border, width: 0.5),
          ),
        ),
        child: SafeArea(
          top: false,
          child: SizedBox(
            height: 62,
            child: Row(
              children:
                  tabs.asMap().entries.map((entry) {
                    final i = entry.key;
                    final tab = entry.value;
                    final active = curIdx == i;
                    final showBadge =
                        tab.$1 == AppRoutes.notifications && unread > 0;

                    return Expanded(
                      child: GestureDetector(
                        behavior: HitTestBehavior.opaque,
                        onTap: () => context.go(tab.$1),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Stack(
                              clipBehavior: Clip.none,
                              children: [
                                AnimatedContainer(
                                  duration: const Duration(milliseconds: 200),
                                  padding: const EdgeInsets.all(6),
                                  decoration: BoxDecoration(
                                    color:
                                        active
                                            ? AppColors.primary.withOpacity(0.1)
                                            : Colors.transparent,
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                  child: Icon(
                                    active ? tab.$3 : tab.$2,
                                    color:
                                        active
                                            ? AppColors.primary
                                            : AppColors.textSecondary,
                                    size: 24,
                                  ),
                                ),
                                if (showBadge)
                                  Positioned(
                                    right: 0,
                                    top: 0,
                                    child: Container(
                                      width: 16,
                                      height: 16,
                                      decoration: const BoxDecoration(
                                        color: AppColors.danger,
                                        shape: BoxShape.circle,
                                      ),
                                      child: Center(
                                        child: Text(
                                          '$unread',
                                          style: const TextStyle(
                                            color: Colors.white,
                                            fontSize: 9,
                                            fontWeight: FontWeight.w900,
                                          ),
                                        ),
                                      ),
                                    ),
                                  ),
                              ],
                            ),
                            const SizedBox(height: 2),
                            Text(
                              tab.$4,
                              style: TextStyle(
                                fontSize: 10,
                                fontWeight:
                                    active ? FontWeight.w700 : FontWeight.w500,
                                color:
                                    active
                                        ? AppColors.primary
                                        : AppColors.textSecondary,
                              ),
                            ),
                          ],
                        ),
                      ),
                    );
                  }).toList(),
            ),
          ),
        ),
      ),
    );
  }
}
