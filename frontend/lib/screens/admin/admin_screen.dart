// =============================================================
// MonTour — lib/screens/admin/admin_screen.dart
// =============================================================

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme.dart';
import '../../providers/stats_provider.dart';
import '../../providers/services_provider.dart';

class AdminScreen extends ConsumerStatefulWidget {
  const AdminScreen({super.key});
  @override
  ConsumerState<AdminScreen> createState() => _AdminScreenState();
}

class _AdminScreenState extends ConsumerState<AdminScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabs;

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabs.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: NestedScrollView(
        headerSliverBuilder:
            (context, _) => [
              SliverAppBar(
                pinned: true,
                automaticallyImplyLeading: false,
                expandedHeight: 140,
                flexibleSpace: FlexibleSpaceBar(
                  background: Container(
                    decoration: const BoxDecoration(
                      gradient: LinearGradient(
                        colors: [Color(0xFF6C63FF), Color(0xFF3F3D56)],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                    ),
                    padding: const EdgeInsets.fromLTRB(20, 56, 20, 8),
                    child: const Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        Text(
                          '⚙️ Administration',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 22,
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                        Text(
                          'Gestion des services et statistiques',
                          style: TextStyle(color: Colors.white70, fontSize: 13),
                        ),
                      ],
                    ),
                  ),
                ),
                bottom: TabBar(
                  controller: _tabs,
                  labelColor: Colors.white,
                  unselectedLabelColor: Colors.white54,
                  indicatorColor: Colors.white,
                  tabs: const [
                    Tab(text: '📊 Stats'),
                    Tab(text: '🎫 Files'),
                    Tab(text: '👥 Usagers'),
                  ],
                ),
              ),
            ],
        body: TabBarView(
          controller: _tabs,
          children: const [_StatsTab(), _QueuesTab(), _UsersTab()],
        ),
      ),
    );
  }
}

// ── Onglet Statistiques ────────────────────────────────────────
class _StatsTab extends ConsumerWidget {
  const _StatsTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final statsAsync = ref.watch(globalStatsProvider);

    return statsAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error:
          (_, __) => Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text('Impossible de charger les statistiques'),
                ElevatedButton(
                  onPressed: () => ref.invalidate(globalStatsProvider),
                  child: const Text('Réessayer'),
                ),
              ],
            ),
          ),
      data: (stats) {
        final summary = stats['summary'] as Map<String, dynamic>;
        final byService = stats['by_service'] as List;
        final daily = stats['daily_7days'] as List;

        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Résumé
            Row(
              children: [
                _MiniStat(
                  'Total',
                  '${summary['total_tickets']}',
                  AppColors.primary,
                ),
                const SizedBox(width: 8),
                _MiniStat(
                  'Servis',
                  '${summary['served']}',
                  AppColors.secondary,
                ),
                const SizedBox(width: 8),
                _MiniStat(
                  'Attente',
                  '${summary['waiting']}',
                  AppColors.warning,
                ),
                const SizedBox(width: 8),
                _MiniStat(
                  'Aujourd\'hui',
                  '${summary['today']}',
                  AppColors.accent,
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                _MiniStat(
                  'Moy. attente',
                  '${summary['avg_wait_minutes']} min',
                  AppColors.primary,
                ),
                const SizedBox(width: 8),
                _MiniStat(
                  'Note moy.',
                  '${summary['avg_rating']} ⭐',
                  AppColors.accent,
                ),
                const SizedBox(width: 8),
                _MiniStat(
                  'Utilisateurs',
                  '${summary['total_users']}',
                  AppColors.textSecondary,
                ),
              ],
            ),
            const SizedBox(height: 20),

            // Graphique 7 jours (simplifié)
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.06),
                    blurRadius: 8,
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    '📈 7 derniers jours',
                    style: TextStyle(fontWeight: FontWeight.w800),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children:
                        daily.map<Widget>((d) {
                          final count = (d['tickets'] as int?) ?? 0;
                          final maxVal =
                              (daily
                                  .map((x) => (x['tickets'] as int?) ?? 0)
                                  .reduce((a, b) => a > b ? a : b)).toDouble();
                          final height =
                              maxVal == 0 ? 10.0 : (count / maxVal) * 80 + 10;
                          return Expanded(
                            child: Padding(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 3,
                              ),
                              child: Column(
                                children: [
                                  Text(
                                    '$count',
                                    style: const TextStyle(
                                      fontSize: 9,
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                                  const SizedBox(height: 4),
                                  Container(
                                    height: height,
                                    decoration: BoxDecoration(
                                      color: AppColors.primary.withOpacity(0.7),
                                      borderRadius: BorderRadius.circular(4),
                                    ),
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    (d['date'] as String).substring(8),
                                    style: const TextStyle(
                                      fontSize: 9,
                                      color: AppColors.textSecondary,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          );
                        }).toList(),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Par service
            const Text(
              'Par service',
              style: TextStyle(fontWeight: FontWeight.w800, fontSize: 15),
            ),
            const SizedBox(height: 10),
            ...byService.map(
              (s) => Container(
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(14),
                  border: Border(
                    left: BorderSide(
                      color: Color(
                        int.parse(
                          (s['service_color'] as String? ?? '#1a73e8')
                              .replaceFirst('#', 'FF'),
                          radix: 16,
                        ),
                      ),
                      width: 4,
                    ),
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.05),
                      blurRadius: 6,
                    ),
                  ],
                ),
                child: Row(
                  children: [
                    Text(
                      s['service_icon'] as String? ?? '🏢',
                      style: const TextStyle(fontSize: 24),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        s['service_name'] as String,
                        style: const TextStyle(fontWeight: FontWeight.w700),
                      ),
                    ),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text(
                          '${s['total']} total',
                          style: const TextStyle(
                            fontSize: 12,
                            color: AppColors.textSecondary,
                          ),
                        ),
                        Text(
                          '${s['served']} servis',
                          style: const TextStyle(
                            fontSize: 12,
                            color: AppColors.secondary,
                          ),
                        ),
                        Text(
                          '${s['waiting']} attente',
                          style: const TextStyle(
                            fontSize: 12,
                            color: AppColors.warning,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ],
        );
      },
    );
  }
}

// ── Onglet Files d'attente ─────────────────────────────────────
class _QueuesTab extends ConsumerWidget {
  const _QueuesTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final servicesAsync = ref.watch(servicesProvider);

    return servicesAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (_, __) => const Center(child: Text('Erreur')),
      data:
          (services) => ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: services.length,
            itemBuilder: (context, i) {
              final s = services[i];
              return Container(
                margin: const EdgeInsets.only(bottom: 12),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.06),
                      blurRadius: 8,
                    ),
                  ],
                ),
                child: Column(
                  children: [
                    Row(
                      children: [
                        Text(s.icon, style: const TextStyle(fontSize: 28)),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                s.name,
                                style: const TextStyle(
                                  fontWeight: FontWeight.w800,
                                ),
                              ),
                              Text(
                                '${s.queueLength} en attente · N°${s.currentNumber} actuel',
                                style: const TextStyle(
                                  fontSize: 12,
                                  color: AppColors.textSecondary,
                                ),
                              ),
                            ],
                          ),
                        ),
                        _StatusBadge(open: s.isOpen),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                          child: ElevatedButton(
                            onPressed: () => context.go('/admin/queue/${s.id}'),
                            child: const Text('Gérer la file'),
                          ),
                        ),
                        const SizedBox(width: 8),
                        OutlinedButton(
                          style: OutlinedButton.styleFrom(
                            foregroundColor:
                                s.isOpen
                                    ? AppColors.warning
                                    : AppColors.secondary,
                          ),
                          onPressed: () async {
                            await ref
                                .read(apiServiceProvider)
                                .toggleQueue(s.id);
                            ref.invalidate(servicesProvider);
                          },
                          child: Icon(
                            s.isOpen ? Icons.lock : Icons.lock_open,
                            size: 18,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              );
            },
          ),
    );
  }
}

class _UsersTab extends StatelessWidget {
  const _UsersTab();
  @override
  Widget build(BuildContext context) =>
      const Center(child: Text('Liste des utilisateurs (Admin API)'));
}

class _MiniStat extends StatelessWidget {
  final String label, value;
  final Color color;
  const _MiniStat(this.label, this.value, this.color);
  @override
  Widget build(BuildContext context) => Expanded(
    child: Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.06), blurRadius: 6),
        ],
      ),
      child: Column(
        children: [
          Text(
            value,
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w900,
              color: color,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            label,
            style: const TextStyle(fontSize: 9, color: AppColors.textSecondary),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    ),
  );
}

class _StatusBadge extends StatelessWidget {
  final bool open;
  const _StatusBadge({required this.open});
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
    decoration: BoxDecoration(
      color: (open ? AppColors.secondary : AppColors.danger).withOpacity(0.12),
      borderRadius: BorderRadius.circular(20),
    ),
    child: Text(
      open ? '✅ Ouvert' : '🔒 Fermé',
      style: TextStyle(
        fontSize: 11,
        fontWeight: FontWeight.w700,
        color: open ? AppColors.secondary : AppColors.danger,
      ),
    ),
  );
}

// =============================================================
// MonTour — lib/screens/admin/admin_queue_screen.dart
// =============================================================

class AdminQueueScreen extends ConsumerWidget {
  final String queueId;
  const AdminQueueScreen({super.key, required this.queueId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final queueAsync = ref.watch(queueStreamProvider(queueId));

    return Scaffold(
      appBar: AppBar(title: const Text('Gestion de la file')),
      body: queueAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Erreur: $e')),
        data:
            (queue) => Column(
              children: [
                // Panneau de contrôle
                Container(
                  padding: const EdgeInsets.all(16),
                  color: Colors.white,
                  child: Row(
                    children: [
                      Expanded(
                        child: ElevatedButton.icon(
                          icon: const Icon(Icons.call_made),
                          label: const Text('Appeler suivant'),
                          onPressed: () async {
                            await ref
                                .read(apiServiceProvider)
                                .callNextTicket(queueId);
                            ref.invalidate(queueStreamProvider(queueId));
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text('📢 Ticket appelé !'),
                              ),
                            );
                          },
                        ),
                      ),
                      const SizedBox(width: 8),
                      OutlinedButton.icon(
                        style: OutlinedButton.styleFrom(
                          foregroundColor: AppColors.danger,
                        ),
                        icon: const Icon(Icons.refresh),
                        label: const Text('Reset'),
                        onPressed: () async {
                          await ref
                              .read(apiServiceProvider)
                              .resetQueue(queueId);
                          ref.invalidate(queueStreamProvider(queueId));
                        },
                      ),
                    ],
                  ),
                ),
                const Divider(height: 1),
                // Info
                Padding(
                  padding: const EdgeInsets.all(12),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      Text(
                        'N° actuel: ${queue.calledNumber}',
                        style: const TextStyle(fontWeight: FontWeight.w700),
                      ),
                      Text(
                        'En attente: ${queue.waitingCount}',
                        style: const TextStyle(
                          fontWeight: FontWeight.w700,
                          color: AppColors.warning,
                        ),
                      ),
                      _StatusBadge(open: queue.isOpen),
                    ],
                  ),
                ),
                const Divider(height: 1),
                // Liste des tickets
                Expanded(
                  child:
                      queue.tickets.isEmpty
                          ? const Center(child: Text('File vide'))
                          : ListView.builder(
                            padding: const EdgeInsets.all(12),
                            itemCount: queue.tickets.length,
                            itemBuilder: (context, i) {
                              final t = queue.tickets[i];
                              return Container(
                                margin: const EdgeInsets.only(bottom: 8),
                                padding: const EdgeInsets.all(12),
                                decoration: BoxDecoration(
                                  color:
                                      i == 0
                                          ? const Color(0xFFF0F7FF)
                                          : Colors.white,
                                  borderRadius: BorderRadius.circular(12),
                                  border: Border.all(
                                    color:
                                        i == 0
                                            ? AppColors.primary
                                            : AppColors.border,
                                  ),
                                ),
                                child: Row(
                                  children: [
                                    Container(
                                      width: 36,
                                      height: 36,
                                      decoration: BoxDecoration(
                                        color:
                                            i == 0
                                                ? AppColors.primary
                                                : AppColors.surface,
                                        borderRadius: BorderRadius.circular(8),
                                      ),
                                      child: Center(
                                        child: Text(
                                          '${i + 1}',
                                          style: TextStyle(
                                            fontWeight: FontWeight.w900,
                                            color:
                                                i == 0
                                                    ? Colors.white
                                                    : AppColors.textSecondary,
                                          ),
                                        ),
                                      ),
                                    ),
                                    const SizedBox(width: 10),
                                    Expanded(
                                      child: Column(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
                                        children: [
                                          Text(
                                            'N° ${t.number} — ${t.userName}',
                                            style: const TextStyle(
                                              fontWeight: FontWeight.w700,
                                            ),
                                          ),
                                          Text(
                                            '~${t.estimatedWait} min · ${t.priority}',
                                            style: const TextStyle(
                                              fontSize: 11,
                                              color: AppColors.textSecondary,
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                    if (t.isCalled)
                                      TextButton(
                                        onPressed: () async {
                                          await ref
                                              .read(apiServiceProvider)
                                              .serveTicket(t.id);
                                          ref.invalidate(
                                            queueStreamProvider(queueId),
                                          );
                                        },
                                        child: const Text('✅ Servi'),
                                      ),
                                  ],
                                ),
                              );
                            },
                          ),
                ),
              ],
            ),
      ),
    );
  }
}
