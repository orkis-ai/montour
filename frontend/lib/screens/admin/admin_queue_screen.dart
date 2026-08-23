// =============================================================
// MonTour — lib/screens/admin/admin_queue_screen.dart
// Gestion en temps réel d'une file (Agent/Admin)
// =============================================================

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme.dart';
import '../../providers/services_provider.dart';
import '../../services/api_service.dart';
import '../../widgets/common/mt_badge.dart';
import '../../widgets/common/mt_snackbar.dart';

class AdminQueueScreen extends ConsumerStatefulWidget {
  final String queueId;
  const AdminQueueScreen({super.key, required this.queueId});

  @override
  ConsumerState<AdminQueueScreen> createState() => _AdminQueueScreenState();
}

class _AdminQueueScreenState extends ConsumerState<AdminQueueScreen> {
  bool _calling = false;
  bool _resetting = false;

  Future<void> _callNext() async {
    setState(() => _calling = true);
    try {
      final data = await ref
          .read(apiServiceProvider)
          .callNextTicket(widget.queueId);
      if (mounted) {
        final num = data['number'];
        MtSnackbar.success(context, '📢 Ticket N°$num appelé !');
        ref.invalidate(queueStreamProvider(widget.queueId));
      }
    } catch (e) {
      if (mounted) MtSnackbar.error(context, 'File vide ou erreur.');
    } finally {
      if (mounted) setState(() => _calling = false);
    }
  }

  Future<void> _resetQueue() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder:
          (ctx) => AlertDialog(
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
            ),
            title: const Text('Réinitialiser la file ?'),
            content: const Text(
              'Tous les tickets en attente seront annulés. Cette action est irréversible.',
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(ctx, false),
                child: const Text('Annuler'),
              ),
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.danger,
                ),
                onPressed: () => Navigator.pop(ctx, true),
                child: const Text('Réinitialiser'),
              ),
            ],
          ),
    );
    if (confirm != true) return;
    setState(() => _resetting = true);
    try {
      await ref.read(apiServiceProvider).resetQueue(widget.queueId);
      if (mounted) {
        MtSnackbar.info(context, '🔄 File réinitialisée.');
        ref.invalidate(queueStreamProvider(widget.queueId));
      }
    } catch (_) {
      if (mounted)
        MtSnackbar.error(context, 'Erreur lors de la réinitialisation.');
    } finally {
      if (mounted) setState(() => _resetting = false);
    }
  }

  Future<void> _serveTicket(String ticketId, int number) async {
    try {
      await ref.read(apiServiceProvider).serveTicket(ticketId);
      if (mounted) {
        MtSnackbar.success(context, '✅ Ticket N°$number marqué servi.');
        ref.invalidate(queueStreamProvider(widget.queueId));
      }
    } catch (_) {
      if (mounted) MtSnackbar.error(context, 'Erreur lors du marquage.');
    }
  }

  @override
  Widget build(BuildContext context) {
    final queueAsync = ref.watch(queueStreamProvider(widget.queueId));

    return Scaffold(
      appBar: AppBar(
        title: queueAsync.when(
          loading: () => const Text('Gestion de la file'),
          error: (_, __) => const Text('Gestion de la file'),
          data: (q) => Text('${q.serviceIcon} ${q.serviceName}'),
        ),
        actions: [
          IconButton(
            icon:
                _resetting
                    ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                    : const Icon(Icons.refresh),
            onPressed: _resetting ? null : _resetQueue,
            tooltip: 'Réinitialiser la file',
          ),
        ],
      ),
      body: queueAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Erreur: $e')),
        data:
            (queue) => Column(
              children: [
                // ── Panneau de contrôle ──────────────────────
                Container(
                  padding: const EdgeInsets.all(16),
                  color: Colors.white,
                  child: Column(
                    children: [
                      // Stats
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceAround,
                        children: [
                          _ControlStat(
                            'N° Actuel',
                            '${queue.calledNumber}',
                            AppColors.primary,
                          ),
                          _ControlStat(
                            'En attente',
                            '${queue.waitingCount}',
                            AppColors.warning,
                          ),
                          _ControlStat(
                            'Capacité',
                            '${queue.maxCapacity}',
                            AppColors.textSecondary,
                          ),
                          Column(
                            children: [
                              MtStatusBadge(status: queue.status),
                              const SizedBox(height: 4),
                              GestureDetector(
                                onTap: () async {
                                  await ref
                                      .read(apiServiceProvider)
                                      .toggleQueue(widget.queueId);
                                  ref.invalidate(
                                    queueStreamProvider(widget.queueId),
                                  );
                                },
                                child: Text(
                                  queue.isOpen ? 'Fermer' : 'Ouvrir',
                                  style: TextStyle(
                                    fontSize: 11,
                                    color:
                                        queue.isOpen
                                            ? AppColors.danger
                                            : AppColors.secondary,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                      const SizedBox(height: 14),

                      // Bouton principal : Appeler suivant
                      SizedBox(
                        width: double.infinity,
                        height: 52,
                        child: ElevatedButton.icon(
                          onPressed:
                              (_calling ||
                                      !queue.isOpen ||
                                      queue.waitingCount == 0)
                                  ? null
                                  : _callNext,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.primary,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                          ),
                          icon:
                              _calling
                                  ? const SizedBox(
                                    width: 20,
                                    height: 20,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                      color: Colors.white,
                                    ),
                                  )
                                  : const Icon(Icons.call_made),
                          label: Text(
                            queue.waitingCount == 0
                                ? 'File vide'
                                : '📢 Appeler le suivant',
                            style: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const Divider(height: 1),

                // ── En-tête de la liste ──────────────────────
                if (queue.tickets.isNotEmpty)
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 10,
                    ),
                    color: AppColors.surface,
                    child: Row(
                      children: [
                        const Text(
                          'Pos.',
                          style: TextStyle(
                            fontWeight: FontWeight.w700,
                            fontSize: 12,
                            color: AppColors.textSecondary,
                          ),
                        ),
                        const SizedBox(width: 46),
                        const Expanded(
                          child: Text(
                            'Usager',
                            style: TextStyle(
                              fontWeight: FontWeight.w700,
                              fontSize: 12,
                              color: AppColors.textSecondary,
                            ),
                          ),
                        ),
                        const Text(
                          'Attente',
                          style: TextStyle(
                            fontWeight: FontWeight.w700,
                            fontSize: 12,
                            color: AppColors.textSecondary,
                          ),
                        ),
                        const SizedBox(width: 70),
                      ],
                    ),
                  ),
                const Divider(height: 1),

                // ── Liste des tickets ────────────────────────
                Expanded(
                  child:
                      queue.tickets.isEmpty
                          ? const Center(
                            child: Column(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Text('🎉', style: TextStyle(fontSize: 56)),
                                SizedBox(height: 12),
                                Text(
                                  'La file est vide',
                                  style: TextStyle(
                                    fontWeight: FontWeight.w700,
                                    fontSize: 16,
                                  ),
                                ),
                                SizedBox(height: 4),
                                Text(
                                  'Aucun usager en attente',
                                  style: TextStyle(
                                    color: AppColors.textSecondary,
                                  ),
                                ),
                              ],
                            ),
                          )
                          : ListView.separated(
                            padding: const EdgeInsets.all(12),
                            itemCount: queue.tickets.length,
                            separatorBuilder:
                                (_, __) => const SizedBox(height: 8),
                            itemBuilder: (context, i) {
                              final t = queue.tickets[i];
                              final isFirst = i == 0;
                              return Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 12,
                                  vertical: 10,
                                ),
                                decoration: BoxDecoration(
                                  color:
                                      t.isCalled
                                          ? AppColors.secondary.withOpacity(
                                            0.08,
                                          )
                                          : isFirst
                                          ? AppColors.primary.withOpacity(0.05)
                                          : Colors.white,
                                  borderRadius: BorderRadius.circular(12),
                                  border: Border.all(
                                    color:
                                        t.isCalled
                                            ? AppColors.secondary
                                            : isFirst
                                            ? AppColors.primary.withOpacity(0.4)
                                            : AppColors.border,
                                    width: t.isCalled ? 1.5 : 1,
                                  ),
                                ),
                                child: Row(
                                  children: [
                                    // Position
                                    Container(
                                      width: 34,
                                      height: 34,
                                      decoration: BoxDecoration(
                                        color:
                                            isFirst
                                                ? AppColors.primary
                                                : AppColors.surface,
                                        borderRadius: BorderRadius.circular(9),
                                      ),
                                      child: Center(
                                        child: Text(
                                          '${i + 1}',
                                          style: TextStyle(
                                            fontWeight: FontWeight.w900,
                                            color:
                                                isFirst
                                                    ? Colors.white
                                                    : AppColors.textSecondary,
                                          ),
                                        ),
                                      ),
                                    ),
                                    const SizedBox(width: 10),

                                    // Info
                                    Expanded(
                                      child: Column(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
                                        children: [
                                          Row(
                                            children: [
                                              Text(
                                                'N° ${t.number}',
                                                style: const TextStyle(
                                                  fontWeight: FontWeight.w800,
                                                ),
                                              ),
                                              const SizedBox(width: 6),
                                              MtPriorityBadge(
                                                priority: t.priority,
                                              ),
                                            ],
                                          ),
                                          const SizedBox(height: 2),
                                          Text(
                                            t.userName,
                                            style: const TextStyle(
                                              fontSize: 12,
                                              color: AppColors.textSecondary,
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),

                                    // Temps estimé
                                    Text(
                                      '~${t.estimatedWait}m',
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w700,
                                        fontSize: 13,
                                      ),
                                    ),
                                    const SizedBox(width: 8),

                                    // Actions
                                    if (t.isCalled)
                                      ElevatedButton(
                                        onPressed:
                                            () => _serveTicket(t.id, t.number),
                                        style: ElevatedButton.styleFrom(
                                          backgroundColor: AppColors.secondary,
                                          minimumSize: const Size(60, 34),
                                          padding: const EdgeInsets.symmetric(
                                            horizontal: 10,
                                          ),
                                          shape: RoundedRectangleBorder(
                                            borderRadius: BorderRadius.circular(
                                              8,
                                            ),
                                          ),
                                        ),
                                        child: const Text(
                                          '✅ Servi',
                                          style: TextStyle(fontSize: 11),
                                        ),
                                      )
                                    else
                                      MtStatusBadge(status: t.status),
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

class _ControlStat extends StatelessWidget {
  final String label, value;
  final Color color;
  const _ControlStat(this.label, this.value, this.color);

  @override
  Widget build(BuildContext context) => Column(
    children: [
      Text(
        value,
        style: TextStyle(
          fontSize: 22,
          fontWeight: FontWeight.w900,
          color: color,
        ),
      ),
      Text(
        label,
        style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
      ),
    ],
  );
}
