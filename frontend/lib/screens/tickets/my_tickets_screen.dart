// =============================================================
// MonTour — lib/screens/tickets/my_tickets_screen.dart
// =============================================================

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme.dart';
import '../../providers/tickets_provider.dart';
import '../../widgets/common/mt_shimmer.dart';

class MyTicketsScreen extends ConsumerWidget {
  const MyTicketsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final ticketsAsync = ref.watch(ticketsNotifierProvider);

    return Scaffold(
      body: CustomScrollView(
        slivers: [
          SliverAppBar(
            pinned: true,
            automaticallyImplyLeading: false,
            expandedHeight: 120,
            flexibleSpace: FlexibleSpaceBar(
              background: Container(
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                    colors: [Color(0xFF667EEA), Color(0xFF764BA2)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                ),
                padding: const EdgeInsets.fromLTRB(20, 56, 20, 16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    const Text(
                      '📋 Mes Tickets',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 22,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    ticketsAsync.when(
                      loading: () => const SizedBox(),
                      error: (_, __) => const SizedBox(),
                      data:
                          (tickets) => Text(
                            '${tickets.length} ticket(s)',
                            style: const TextStyle(
                              color: Colors.white70,
                              fontSize: 13,
                            ),
                          ),
                    ),
                  ],
                ),
              ),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.all(16),
            sliver: ticketsAsync.when(
              loading:
                  () => SliverList(
                    delegate: SliverChildListDelegate(
                      List.generate(4, (_) => const MtShimmerCard()),
                    ),
                  ),
              error:
                  (e, _) => SliverToBoxAdapter(
                    child: Column(
                      children: [
                        const SizedBox(height: 48),
                        const Icon(
                          Icons.error_outline,
                          size: 56,
                          color: AppColors.textSecondary,
                        ),
                        const SizedBox(height: 12),
                        const Text('Impossible de charger les tickets'),
                        const SizedBox(height: 12),
                        ElevatedButton(
                          onPressed:
                              () => ref.invalidate(ticketsNotifierProvider),
                          child: const Text('Réessayer'),
                        ),
                      ],
                    ),
                  ),
              data: (tickets) {
                if (tickets.isEmpty) {
                  return SliverToBoxAdapter(
                    child: Center(
                      child: Column(
                        children: [
                          const SizedBox(height: 64),
                          const Text('🎫', style: TextStyle(fontSize: 64)),
                          const SizedBox(height: 16),
                          const Text(
                            'Aucun ticket pour le moment',
                            style: TextStyle(
                              fontWeight: FontWeight.w700,
                              fontSize: 16,
                            ),
                          ),
                          const SizedBox(height: 8),
                          const Text(
                            'Prenez votre premier ticket depuis la file d\'attente',
                            textAlign: TextAlign.center,
                            style: TextStyle(color: AppColors.textSecondary),
                          ),
                          const SizedBox(height: 20),
                          ElevatedButton(
                            onPressed: () => context.go('/queues'),
                            child: const Text('Voir les files d\'attente'),
                          ),
                        ],
                      ),
                    ),
                  );
                }
                return SliverList(
                  delegate: SliverChildBuilderDelegate((context, i) {
                    final t = tickets[i];
                    final svcColor = Color(
                      int.parse(
                        t.serviceColor.replaceFirst('#', 'FF'),
                        radix: 16,
                      ),
                    );
                    return GestureDetector(
                      onTap: () => context.go('/tickets/${t.id}'),
                      child: Container(
                        margin: const EdgeInsets.only(bottom: 12),
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(16),
                          border: Border(
                            left: BorderSide(color: svcColor, width: 4),
                          ),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withOpacity(0.06),
                              blurRadius: 10,
                            ),
                          ],
                        ),
                        child: Row(
                          children: [
                            // Service icon
                            Container(
                              width: 44,
                              height: 44,
                              decoration: BoxDecoration(
                                color: svcColor.withOpacity(0.12),
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Center(
                                child: Text(
                                  t.serviceIcon,
                                  style: const TextStyle(fontSize: 22),
                                ),
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    t.serviceName,
                                    style: const TextStyle(
                                      fontWeight: FontWeight.w700,
                                      fontSize: 14,
                                    ),
                                  ),
                                  const SizedBox(height: 2),
                                  Text(
                                    '${t.requestedAt.day}/${t.requestedAt.month}/${t.requestedAt.year} · ${t.requestedAt.hour}h${t.requestedAt.minute.toString().padLeft(2, '0')}',
                                    style: const TextStyle(
                                      fontSize: 11,
                                      color: AppColors.textSecondary,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.end,
                              children: [
                                Text(
                                  'N° ${t.number}',
                                  style: const TextStyle(
                                    fontSize: 22,
                                    fontWeight: FontWeight.w900,
                                  ),
                                ),
                                _TicketStatusBadge(status: t.status),
                                if (t.isWaiting)
                                  Text(
                                    '~${t.estimatedWait} min',
                                    style: TextStyle(
                                      color: svcColor,
                                      fontSize: 12,
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    );
                  }, childCount: tickets.length),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _TicketStatusBadge extends StatelessWidget {
  final String status;
  const _TicketStatusBadge({required this.status});
  @override
  Widget build(BuildContext context) {
    const data = {
      'waiting': ('⏳ Attente', AppColors.warning),
      'called': ('📢 Appelé', AppColors.primary),
      'served': ('✅ Servi', AppColors.secondary),
      'cancelled': ('❌ Annulé', AppColors.danger),
    };
    final d = data[status] ?? ('❓', AppColors.textSecondary);
    return Container(
      margin: const EdgeInsets.only(top: 4),
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: d.$2.withOpacity(0.12),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        d.$1,
        style: TextStyle(
          fontSize: 10,
          fontWeight: FontWeight.w700,
          color: d.$2,
        ),
      ),
    );
  }
}

// =============================================================
// MonTour — lib/screens/tickets/ticket_detail_screen.dart
// =============================================================

class TicketDetailScreen extends ConsumerWidget {
  final String ticketId;
  const TicketDetailScreen({super.key, required this.ticketId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tickets = ref.watch(ticketsNotifierProvider).value ?? [];
    final ticket = tickets.where((t) => t.id == ticketId).firstOrNull;

    if (ticket == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Ticket')),
        body: const Center(child: Text('Ticket introuvable')),
      );
    }

    final svcColor = Color(
      int.parse(ticket.serviceColor.replaceFirst('#', 'FF'), radix: 16),
    );

    return Scaffold(
      body: CustomScrollView(
        slivers: [
          SliverAppBar(
            pinned: true,
            backgroundColor: svcColor,
            expandedHeight: 220,
            flexibleSpace: FlexibleSpaceBar(
              background: Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [svcColor, svcColor.withOpacity(0.7)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                ),
                child: Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const SizedBox(height: 48),
                      Text(
                        ticket.serviceIcon,
                        style: const TextStyle(fontSize: 40),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'N° ${ticket.number}',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 64,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                      Text(
                        ticket.serviceName,
                        style: const TextStyle(
                          color: Colors.white70,
                          fontSize: 14,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.all(16),
            sliver: SliverList(
              delegate: SliverChildListDelegate([
                // Status card
                _InfoCard(
                  children: [
                    _InfoRow('Statut', ticket.statusLabel),
                    _InfoRow('Priorité', ticket.priority),
                    if (ticket.isWaiting)
                      _InfoRow('Temps estimé', '~${ticket.estimatedWait} min'),
                    if (ticket.actualWait != null)
                      _InfoRow('Temps réel', '${ticket.actualWait} min'),
                    if (ticket.position != null)
                      _InfoRow(
                        'Position',
                        '${ticket.position}ème dans la file',
                      ),
                  ],
                ),
                const SizedBox(height: 12),
                // Horodatages
                _InfoCard(
                  title: '⏰ Horodatages',
                  children: [
                    _InfoRow('Demandé le', _fmt(ticket.requestedAt)),
                    if (ticket.calledAt != null)
                      _InfoRow('Appelé le', _fmt(ticket.calledAt!)),
                    if (ticket.servedAt != null)
                      _InfoRow('Servi le', _fmt(ticket.servedAt!)),
                    if (ticket.cancelledAt != null)
                      _InfoRow('Annulé le', _fmt(ticket.cancelledAt!)),
                  ],
                ),
                // Note
                if (ticket.isServed && ticket.rating == null) ...[
                  const SizedBox(height: 12),
                  _RatingCard(ticketId: ticket.id),
                ],
                const SizedBox(height: 24),
              ]),
            ),
          ),
        ],
      ),
    );
  }

  String _fmt(DateTime dt) =>
      '${dt.day}/${dt.month}/${dt.year} à ${dt.hour}h${dt.minute.toString().padLeft(2, '0')}';
}

class _InfoCard extends StatelessWidget {
  final List<Widget> children;
  final String? title;
  const _InfoCard({required this.children, this.title});
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(
      color: Colors.white,
      borderRadius: BorderRadius.circular(16),
      boxShadow: [
        BoxShadow(color: Colors.black.withOpacity(0.06), blurRadius: 10),
      ],
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (title != null) ...[
          Text(title!, style: const TextStyle(fontWeight: FontWeight.w800)),
          const SizedBox(height: 12),
        ],
        ...children,
      ],
    ),
  );
}

class _InfoRow extends StatelessWidget {
  final String label, value;
  const _InfoRow(this.label, this.value);
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 10),
    child: Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: const TextStyle(color: AppColors.textSecondary, fontSize: 13),
        ),
        Text(
          value,
          style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
        ),
      ],
    ),
  );
}

class _RatingCard extends ConsumerStatefulWidget {
  final String ticketId;
  const _RatingCard({required this.ticketId});
  @override
  ConsumerState<_RatingCard> createState() => _RatingCardState();
}

class _RatingCardState extends ConsumerState<_RatingCard> {
  int _rating = 0;
  final _ctrl = TextEditingController();
  bool _sent = false;

  @override
  Widget build(BuildContext context) {
    if (_sent)
      return Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: AppColors.secondary.withOpacity(0.1),
          borderRadius: BorderRadius.circular(16),
        ),
        child: const Center(
          child: Text(
            '✅ Merci pour votre avis !',
            style: TextStyle(
              fontWeight: FontWeight.w700,
              color: AppColors.secondary,
            ),
          ),
        ),
      );
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.accent),
      ),
      child: Column(
        children: [
          const Text(
            '⭐ Notez votre expérience',
            style: TextStyle(fontWeight: FontWeight.w800, fontSize: 15),
          ),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(
              5,
              (i) => GestureDetector(
                onTap: () => setState(() => _rating = i + 1),
                child: Icon(
                  i < _rating ? Icons.star : Icons.star_border,
                  color: AppColors.accent,
                  size: 36,
                ),
              ),
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _ctrl,
            decoration: const InputDecoration(
              hintText: 'Commentaire (optionnel)',
              border: OutlineInputBorder(),
            ),
            maxLines: 2,
          ),
          const SizedBox(height: 12),
          ElevatedButton(
            onPressed:
                _rating == 0
                    ? null
                    : () async {
                      await ref
                          .read(apiServiceProvider)
                          .rateTicket(widget.ticketId, _rating, _ctrl.text);
                      setState(() => _sent = true);
                    },
            child: const Text('Envoyer'),
          ),
        ],
      ),
    );
  }
}
