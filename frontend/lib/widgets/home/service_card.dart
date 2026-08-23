// =============================================================
// MonTour — lib/widgets/home/service_card.dart
// =============================================================

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme.dart';
import '../../models/service_model.dart';

class ServiceCard extends StatelessWidget {
  final ServiceModel service;
  const ServiceCard({super.key, required this.service});

  @override
  Widget build(BuildContext context) {
    final color = _hexColor(service.color);
    return GestureDetector(
      onTap: () => context.go('/queues/${service.id}'),
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border(left: BorderSide(color: color, width: 4)),
          boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.06), blurRadius: 10, offset: const Offset(0, 3))],
        ),
        child: Row(
          children: [
            // Icône
            Container(
              width: 52, height: 52,
              decoration: BoxDecoration(
                color: color.withOpacity(0.12),
                borderRadius: BorderRadius.circular(14),
              ),
              child: Center(child: Text(service.icon, style: const TextStyle(fontSize: 26))),
            ),
            const SizedBox(width: 14),
            // Info
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(service.name, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15)),
                  const SizedBox(height: 2),
                  Text(service.description, style: const TextStyle(fontSize: 12, color: AppColors.textSecondary), maxLines: 1, overflow: TextOverflow.ellipsis),
                  const SizedBox(height: 6),
                  Row(children: [
                    _StatusPill(open: service.isOpen),
                    const SizedBox(width: 8),
                    Text('~${service.avgServiceTime} min/usager', style: const TextStyle(fontSize: 11, color: AppColors.textSecondary)),
                  ]),
                ],
              ),
            ),
            // Compteur
            Column(children: [
              Text(
                '${service.queueLength}',
                style: TextStyle(fontSize: 26, fontWeight: FontWeight.w900, color: color),
              ),
              const Text('en attente', style: TextStyle(fontSize: 10, color: AppColors.textSecondary)),
              if (service.currentNumber > 0)
                Text('N°${service.currentNumber}', style: TextStyle(fontSize: 11, color: color, fontWeight: FontWeight.w700)),
            ]),
          ],
        ),
      ),
    );
  }

  Color _hexColor(String hex) {
    try {
      return Color(int.parse(hex.replaceFirst('#', 'FF'), radix: 16));
    } catch (_) {
      return AppColors.primary;
    }
  }
}

class _StatusPill extends StatelessWidget {
  final bool open;
  const _StatusPill({required this.open});

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
    decoration: BoxDecoration(
      color: (open ? AppColors.secondary : AppColors.danger).withOpacity(0.12),
      borderRadius: BorderRadius.circular(20),
    ),
    child: Text(
      open ? '✅ Ouvert' : '🔒 Fermé',
      style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: open ? AppColors.secondary : AppColors.danger),
    ),
  );
}


// =============================================================
// MonTour — lib/widgets/home/active_ticket_banner.dart
// Bandeau ticket actif sur le dashboard
// =============================================================

import '../../models/ticket_model.dart';

class ActiveTicketBanner extends StatelessWidget {
  final TicketModel ticket;
  const ActiveTicketBanner({super.key, required this.ticket});

  @override
  Widget build(BuildContext context) {
    final isCalledNow = ticket.isCalled;
    final bgColor     = isCalledNow ? const Color(0xFFE8F5E9) : const Color(0xFFFFFBF0);
    final borderColor = isCalledNow ? AppColors.secondary : AppColors.accent;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: borderColor, width: 2),
        boxShadow: [BoxShadow(color: borderColor.withOpacity(0.2), blurRadius: 12)],
      ),
      child: Row(
        children: [
          // Numéro
          Container(
            width: 64, height: 64,
            decoration: BoxDecoration(
              color: borderColor.withOpacity(0.15),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
              const Text('🎫', style: TextStyle(fontSize: 24)),
              Text('N°${ticket.number}', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w900, color: borderColor)),
            ]),
          ),
          const SizedBox(width: 14),
          // Infos
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(
                isCalledNow ? '🔔 C\'est votre tour !' : '⏳ Ticket actif',
                style: TextStyle(fontWeight: FontWeight.w900, fontSize: 15, color: isCalledNow ? AppColors.secondary : AppColors.warning),
              ),
              const SizedBox(height: 2),
              Text(ticket.serviceName, style: const TextStyle(fontSize: 13, color: AppColors.textSecondary)),
              const SizedBox(height: 4),
              if (!isCalledNow)
                Row(children: [
                  const Icon(Icons.access_time, size: 14, color: AppColors.textSecondary),
                  const SizedBox(width: 4),
                  Text('~${ticket.estimatedWait} min estimées', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                  if (ticket.position != null) ...[
                    const SizedBox(width: 8),
                    Text('Position: ${ticket.position}', style: const TextStyle(fontSize: 12, color: AppColors.textSecondary)),
                  ],
                ])
              else
                const Text('Présentez-vous immédiatement au guichet', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.secondary)),
            ]),
          ),
        ],
      ),
    );
  }
}


// =============================================================
// MonTour — lib/widgets/home/stats_row.dart
// Ligne de statistiques rapides sur le dashboard
// =============================================================

import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/tickets_provider.dart';
import '../../providers/notifications_provider.dart';

class StatsRow extends ConsumerWidget {
  const StatsRow({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tickets   = ref.watch(ticketsNotifierProvider).value ?? [];
    final unread    = ref.watch(unreadCountProvider);

    final stats = [
      ('📋', 'Tickets', '${tickets.length}',                  AppColors.primary),
      ('✅', 'Servis',  '${tickets.where((t) => t.isServed).length}',  AppColors.secondary),
      ('⏳', 'Attente', '${tickets.where((t) => t.isWaiting).length}', AppColors.warning),
      ('🔔', 'Notifs',  '$unread',                            AppColors.danger),
    ];

    return Row(
      children: stats.asMap().entries.map((e) {
        final s = e.value;
        return Expanded(
          child: Container(
            margin: EdgeInsets.only(left: e.key > 0 ? 8 : 0),
            padding: const EdgeInsets.symmetric(vertical: 14),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(14),
              boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.06), blurRadius: 8)],
            ),
            child: Column(children: [
              Text(s.$1, style: const TextStyle(fontSize: 20)),
              const SizedBox(height: 4),
              Text(s.$3, style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900, color: s.$4)),
              Text(s.$2, style: const TextStyle(fontSize: 10, color: AppColors.textSecondary)),
            ]),
          ),
        );
      }).toList(),
    );
  }
}