// =============================================================
// MonTour — lib/screens/tickets/ticket_detail_screen.dart
// =============================================================

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme.dart';
import '../../providers/tickets_provider.dart';
import '../../providers/services_provider.dart';
import '../../services/api_service.dart';
import '../../widgets/common/mt_badge.dart';
import '../../widgets/common/mt_snackbar.dart';

class TicketDetailScreen extends ConsumerStatefulWidget {
  final String ticketId;
  const TicketDetailScreen({super.key, required this.ticketId});

  @override
  ConsumerState<TicketDetailScreen> createState() => _TicketDetailScreenState();
}

class _TicketDetailScreenState extends ConsumerState<TicketDetailScreen> {
  int _rating = 0;
  bool _rateSent = false;
  final _feedbackCtrl = TextEditingController();

  @override
  void dispose() {
    _feedbackCtrl.dispose();
    super.dispose();
  }

  Future<void> _submitRating() async {
    if (_rating == 0) {
      MtSnackbar.warning(context, 'Sélectionnez une note entre 1 et 5 ⭐');
      return;
    }
    try {
      await ref
          .read(apiServiceProvider)
          .rateTicket(widget.ticketId, _rating, _feedbackCtrl.text.trim());
      if (mounted) setState(() => _rateSent = true);
    } catch (_) {
      if (mounted) MtSnackbar.error(context, 'Impossible d\'envoyer la note.');
    }
  }

  @override
  Widget build(BuildContext context) {
    final tickets = ref.watch(ticketsNotifierProvider).value ?? [];
    final ticket = tickets.where((t) => t.id == widget.ticketId).firstOrNull;

    if (ticket == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Ticket')),
        body: const Center(child: Text('Ticket introuvable')),
      );
    }

    Color svcColor;
    try {
      svcColor = Color(
        int.parse(ticket.serviceColor.replaceFirst('#', 'FF'), radix: 16),
      );
    } catch (_) {
      svcColor = AppColors.primary;
    }

    return Scaffold(
      body: CustomScrollView(
        slivers: [
          // ── Hero header ─────────────────────────────────
          SliverAppBar(
            pinned: true,
            expandedHeight: 240,
            backgroundColor: svcColor,
            flexibleSpace: FlexibleSpaceBar(
              background: Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [svcColor, svcColor.withOpacity(0.75)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                ),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const SizedBox(height: 60),
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
                        height: 1,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      ticket.serviceName,
                      style: const TextStyle(
                        color: Colors.white70,
                        fontSize: 14,
                      ),
                    ),
                    const SizedBox(height: 10),
                    MtStatusBadge(status: ticket.status),
                  ],
                ),
              ),
            ),
          ),

          SliverPadding(
            padding: const EdgeInsets.all(16),
            sliver: SliverList(
              delegate: SliverChildListDelegate([
                // ── Infos principales ────────────────────
                _InfoCard(
                  children: [
                    _InfoRow('Priorité', ticket.priority),
                    if (ticket.isWaiting)
                      _InfoRow('Temps estimé', '~${ticket.estimatedWait} min'),
                    if (ticket.actualWait != null)
                      _InfoRow('Temps réel', '${ticket.actualWait} min'),
                    if (ticket.position != null)
                      _InfoRow(
                        'Position dans la file',
                        '${ticket.position}ème',
                      ),
                    _InfoRow('Score priorité', '${ticket.priorityScore} pts'),
                  ],
                ),
                const SizedBox(height: 12),

                // ── Horodatages ──────────────────────────
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
                const SizedBox(height: 12),

                // ── Note de satisfaction ─────────────────
                if (ticket.isServed) ...[
                  if (ticket.rating != null)
                    _InfoCard(
                      title: '⭐ Votre note',
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: List.generate(
                            5,
                            (i) => Icon(
                              i < (ticket.rating ?? 0)
                                  ? Icons.star
                                  : Icons.star_border,
                              color: AppColors.accent,
                              size: 32,
                            ),
                          ),
                        ),
                      ],
                    )
                  else if (_rateSent)
                    Container(
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        color: AppColors.secondary.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(
                          color: AppColors.secondary.withOpacity(0.3),
                        ),
                      ),
                      child: const Center(
                        child: Column(
                          children: [
                            Text('✅', style: TextStyle(fontSize: 32)),
                            SizedBox(height: 8),
                            Text(
                              'Merci pour votre évaluation !',
                              style: TextStyle(
                                fontWeight: FontWeight.w700,
                                color: AppColors.secondary,
                              ),
                            ),
                          ],
                        ),
                      ),
                    )
                  else
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(
                          color: AppColors.accent.withOpacity(0.5),
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(0.05),
                            blurRadius: 8,
                          ),
                        ],
                      ),
                      child: Column(
                        children: [
                          const Text(
                            '⭐ Notez votre expérience',
                            style: TextStyle(
                              fontWeight: FontWeight.w800,
                              fontSize: 15,
                            ),
                          ),
                          const SizedBox(height: 4),
                          const Text(
                            'Votre avis améliore notre service',
                            style: TextStyle(
                              fontSize: 12,
                              color: AppColors.textSecondary,
                            ),
                          ),
                          const SizedBox(height: 16),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: List.generate(
                              5,
                              (i) => GestureDetector(
                                onTap: () => setState(() => _rating = i + 1),
                                child: Padding(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 4,
                                  ),
                                  child: Icon(
                                    i < _rating
                                        ? Icons.star
                                        : Icons.star_border,
                                    color: AppColors.accent,
                                    size: 40,
                                  ),
                                ),
                              ),
                            ),
                          ),
                          const SizedBox(height: 14),
                          TextField(
                            controller: _feedbackCtrl,
                            maxLines: 2,
                            decoration: const InputDecoration(
                              hintText: 'Commentaire (optionnel)...',
                              filled: true,
                              fillColor: AppColors.surface,
                              border: OutlineInputBorder(),
                              contentPadding: EdgeInsets.symmetric(
                                horizontal: 14,
                                vertical: 10,
                              ),
                            ),
                          ),
                          const SizedBox(height: 14),
                          ElevatedButton(
                            onPressed: _rating == 0 ? null : _submitRating,
                            child: const Text('Envoyer mon avis'),
                          ),
                        ],
                      ),
                    ),
                  const SizedBox(height: 12),
                ],

                // ── Annulation ───────────────────────────
                if (ticket.isWaiting) ...[
                  OutlinedButton.icon(
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppColors.danger,
                      side: const BorderSide(color: AppColors.danger),
                      minimumSize: const Size(double.infinity, 50),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    icon: const Icon(Icons.cancel_outlined),
                    label: const Text('Annuler ce ticket'),
                    onPressed: () async {
                      final confirm = await showDialog<bool>(
                        context: context,
                        builder:
                            (ctx) => AlertDialog(
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(16),
                              ),
                              title: const Text('Annuler le ticket ?'),
                              content: const Text(
                                'Vous perdrez votre place dans la file d\'attente.',
                              ),
                              actions: [
                                TextButton(
                                  onPressed: () => Navigator.pop(ctx, false),
                                  child: const Text('Non'),
                                ),
                                ElevatedButton(
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: AppColors.danger,
                                  ),
                                  onPressed: () => Navigator.pop(ctx, true),
                                  child: const Text('Oui, annuler'),
                                ),
                              ],
                            ),
                      );
                      if (confirm == true && mounted) {
                        await ref
                            .read(ticketsNotifierProvider.notifier)
                            .cancelTicket(ticket.id);
                        if (mounted) {
                          MtSnackbar.info(context, 'Ticket annulé.');
                          Navigator.pop(context);
                        }
                      }
                    },
                  ),
                  const SizedBox(height: 12),
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
      '${dt.day.toString().padLeft(2, '0')}/${dt.month.toString().padLeft(2, '0')}/${dt.year}  ${dt.hour.toString().padLeft(2, '0')}h${dt.minute.toString().padLeft(2, '0')}';
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
          Text(
            title!,
            style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 14),
          ),
          const Divider(height: 16),
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
          style: const TextStyle(fontSize: 13, color: AppColors.textSecondary),
        ),
        Text(
          value,
          style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700),
        ),
      ],
    ),
  );
}
