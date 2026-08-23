// =============================================================
// MonTour — lib/screens/queue/queue_detail_screen.dart
// =============================================================

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme.dart';
import '../../providers/services_provider.dart';
import '../../providers/tickets_provider.dart';
import '../../widgets/common/mt_button.dart';
import '../../widgets/common/mt_snackbar.dart';
import '../../widgets/queue/ticket_list_item.dart';

class QueueDetailScreen extends ConsumerStatefulWidget {
  final String serviceId;
  const QueueDetailScreen({super.key, required this.serviceId});
  @override
  ConsumerState<QueueDetailScreen> createState() => _QueueDetailScreenState();
}

class _QueueDetailScreenState extends ConsumerState<QueueDetailScreen> {
  bool _takingTicket = false;

  Future<void> _takeTicket(String queueId) async {
    setState(() => _takingTicket = true);
    try {
      final ticket = await ref
          .read(ticketsNotifierProvider.notifier)
          .takeTicket(queueId);
      if (mounted) {
        MtSnackbar.success(
          context,
          '🎫 Ticket n°${ticket.number} obtenu ! ~${ticket.estimatedWait} min d\'attente',
        );
        ref.invalidate(queueDetailProvider(widget.serviceId));
      }
    } catch (e) {
      if (mounted)
        MtSnackbar.error(
          context,
          e.toString().contains('déjà')
              ? 'Vous avez déjà un ticket actif !'
              : 'Impossible de prendre un ticket.',
        );
    } finally {
      if (mounted) setState(() => _takingTicket = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final queueAsync = ref.watch(queueStreamProvider(widget.serviceId));
    final activeTicket = ref.watch(activeTicketProvider);
    final myTicket = activeTicket?.serviceName != null ? activeTicket : null;

    return queueAsync.when(
      loading:
          () =>
              const Scaffold(body: Center(child: CircularProgressIndicator())),
      error:
          (e, _) => Scaffold(
            appBar: AppBar(),
            body: Center(child: Text('Erreur: $e')),
          ),
      data: (queue) {
        final svcColor = Color(
          int.parse(queue.serviceColor.replaceFirst('#', 'FF'), radix: 16),
        );
        return Scaffold(
          body: CustomScrollView(
            slivers: [
              // ── Header service ─────────────────────────────
              SliverAppBar(
                expandedHeight: 200,
                pinned: true,
                backgroundColor: svcColor,
                flexibleSpace: FlexibleSpaceBar(
                  background: Container(
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [svcColor, svcColor.withOpacity(0.8)],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                    ),
                    padding: const EdgeInsets.fromLTRB(20, 80, 20, 20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        Row(
                          children: [
                            Text(
                              queue.serviceIcon,
                              style: const TextStyle(fontSize: 32),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Text(
                                queue.serviceName,
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 22,
                                  fontWeight: FontWeight.w900,
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 16),
                        Row(
                          children: [
                            _StatBox(
                              label: 'Actuel',
                              value: 'N°${queue.calledNumber}',
                            ),
                            const SizedBox(width: 8),
                            _StatBox(
                              label: 'Attente',
                              value: '${queue.waitingCount}',
                            ),
                            const SizedBox(width: 8),
                            _StatBox(
                              label: 'Statut',
                              value: queue.isOpen ? 'Ouvert' : 'Fermé',
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
              ),

              SliverPadding(
                padding: const EdgeInsets.all(16),
                sliver: SliverList(
                  delegate: SliverChildListDelegate([
                    // ── Mon ticket actif ────────────────────
                    if (myTicket != null) ...[
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFFFBF0),
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: svcColor, width: 2),
                        ),
                        child: Column(
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      '🎫 MON TICKET',
                                      style: TextStyle(
                                        fontSize: 11,
                                        fontWeight: FontWeight.w800,
                                        color: svcColor,
                                      ),
                                    ),
                                    Text(
                                      'N° ${myTicket.number}',
                                      style: const TextStyle(
                                        fontSize: 40,
                                        fontWeight: FontWeight.w900,
                                      ),
                                    ),
                                  ],
                                ),
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.end,
                                  children: [
                                    _TicketStatusBadge(status: myTicket.status),
                                    const SizedBox(height: 6),
                                    Text(
                                      '~${myTicket.estimatedWait} min',
                                      style: TextStyle(
                                        color: svcColor,
                                        fontWeight: FontWeight.w800,
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                            const SizedBox(height: 12),
                            OutlinedButton(
                              style: OutlinedButton.styleFrom(
                                foregroundColor: AppColors.danger,
                                side: const BorderSide(color: AppColors.danger),
                              ),
                              onPressed: () async {
                                await ref
                                    .read(ticketsNotifierProvider.notifier)
                                    .cancelTicket(myTicket.id);
                                if (mounted)
                                  MtSnackbar.info(context, 'Ticket annulé');
                                ref.invalidate(
                                  queueStreamProvider(widget.serviceId),
                                );
                              },
                              child: const Text('❌ Annuler mon ticket'),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),
                    ] else if (queue.isOpen) ...[
                      // ── Prendre un ticket ───────────────
                      Container(
                        padding: const EdgeInsets.all(20),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(16),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withOpacity(0.06),
                              blurRadius: 10,
                            ),
                          ],
                        ),
                        child: Column(
                          children: [
                            const Text('🎫', style: TextStyle(fontSize: 48)),
                            const SizedBox(height: 8),
                            const Text(
                              'Prendre un ticket',
                              style: TextStyle(
                                fontWeight: FontWeight.w800,
                                fontSize: 17,
                              ),
                            ),
                            const SizedBox(height: 4),
                            const Text(
                              'Vous serez placé selon votre priorité',
                              style: TextStyle(
                                color: AppColors.textSecondary,
                                fontSize: 13,
                              ),
                            ),
                            const SizedBox(height: 16),
                            MtButton(
                              label: '📋 Prendre un ticket',
                              onPressed: () => _takeTicket(queue.id),
                              loading: _takingTicket,
                              color: svcColor,
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),
                    ] else ...[
                      Container(
                        padding: const EdgeInsets.all(20),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(16),
                        ),
                        child: const Center(
                          child: Column(
                            children: [
                              Text('🔒', style: TextStyle(fontSize: 40)),
                              SizedBox(height: 8),
                              Text(
                                'Ce service est actuellement fermé',
                                textAlign: TextAlign.center,
                                style: TextStyle(fontWeight: FontWeight.w700),
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                    ],

                    // ── Liste de la file ─────────────────
                    Text(
                      'File d\'attente (${queue.waitingCount})',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 10),

                    if (queue.tickets.isEmpty)
                      Container(
                        padding: const EdgeInsets.all(32),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(16),
                        ),
                        child: const Center(
                          child: Column(
                            children: [
                              Text('🎉', style: TextStyle(fontSize: 40)),
                              SizedBox(height: 8),
                              Text(
                                'Aucune attente ! Service immédiat.',
                                style: TextStyle(fontWeight: FontWeight.w700),
                              ),
                            ],
                          ),
                        ),
                      )
                    else
                      ...queue.tickets
                          .take(15)
                          .toList()
                          .asMap()
                          .entries
                          .map(
                            (e) => TicketListItem(
                              ticket: e.value,
                              position: e.key + 1,
                              accentColor: svcColor,
                            ),
                          ),
                    const SizedBox(height: 24),
                  ]),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _StatBox extends StatelessWidget {
  final String label, value;
  const _StatBox({required this.label, required this.value});
  @override
  Widget build(BuildContext context) => Expanded(
    child: Container(
      padding: const EdgeInsets.symmetric(vertical: 8),
      decoration: BoxDecoration(
        color: Colors.white24,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        children: [
          Text(
            value,
            style: const TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.w900,
              fontSize: 16,
            ),
          ),
          Text(
            label,
            style: const TextStyle(color: Colors.white70, fontSize: 10),
          ),
        ],
      ),
    ),
  );
}

class _TicketStatusBadge extends StatelessWidget {
  final String status;
  const _TicketStatusBadge({required this.status});
  @override
  Widget build(BuildContext context) {
    const map = {
      'waiting': ['⏳ En attente', AppColors.warning],
      'called': ['📢 Appelé', AppColors.primary],
      'served': ['✅ Servi', AppColors.secondary],
      'cancelled': ['❌ Annulé', AppColors.danger],
    };
    final entry = map[status] ?? ['❓', AppColors.textSecondary];
    final color = entry[1] as Color;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        entry[0] as String,
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w700,
          color: color,
        ),
      ),
    );
  }
}
