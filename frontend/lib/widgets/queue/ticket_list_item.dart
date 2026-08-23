// =============================================================
// MonTour — lib/widgets/queue/ticket_list_item.dart
// Item de liste dans la file d'attente
// =============================================================

import 'package:flutter/material.dart';
import '../../core/theme.dart';
import '../../models/ticket_model.dart';
import '../common/mt_badge.dart';

class TicketListItem extends StatelessWidget {
  final TicketModel ticket;
  final int position;
  final Color accentColor;
  final bool isCurrentUser;

  const TicketListItem({
    super.key,
    required this.ticket,
    required this.position,
    required this.accentColor,
    this.isCurrentUser = false,
  });

  @override
  Widget build(BuildContext context) {
    final isFirst = position == 1;
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color:
            isCurrentUser
                ? accentColor.withOpacity(0.06)
                : isFirst
                ? accentColor.withOpacity(0.04)
                : Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border(
          left: BorderSide(
            color:
                isCurrentUser
                    ? accentColor
                    : isFirst
                    ? accentColor.withOpacity(0.5)
                    : AppColors.border,
            width: isCurrentUser ? 3 : 2,
          ),
        ),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 6),
        ],
      ),
      child: Row(
        children: [
          // Position
          Container(
            width: 34,
            height: 34,
            decoration: BoxDecoration(
              color: isFirst ? accentColor : AppColors.surface,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Center(
              child: Text(
                '$position',
                style: TextStyle(
                  fontWeight: FontWeight.w900,
                  fontSize: 14,
                  color: isFirst ? Colors.white : AppColors.textSecondary,
                ),
              ),
            ),
          ),
          const SizedBox(width: 12),
          // Info ticket
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(
                      'N° ${ticket.number}',
                      style: const TextStyle(
                        fontWeight: FontWeight.w800,
                        fontSize: 15,
                      ),
                    ),
                    if (isCurrentUser) ...[
                      const SizedBox(width: 6),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 7,
                          vertical: 2,
                        ),
                        decoration: BoxDecoration(
                          color: accentColor,
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: const Text(
                          'Vous',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 10,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
                const SizedBox(height: 4),
                MtPriorityBadge(priority: ticket.priority),
              ],
            ),
          ),
          // Temps estimé
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '~${ticket.estimatedWait} min',
                style: TextStyle(
                  fontWeight: FontWeight.w800,
                  color: accentColor,
                  fontSize: 15,
                ),
              ),
              const Text(
                'estimé',
                style: TextStyle(fontSize: 10, color: AppColors.textSecondary),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
