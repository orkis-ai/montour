// =============================================================
// MonTour — lib/widgets/common/mt_snackbar.dart
// =============================================================

import 'package:flutter/material.dart';
import '../../core/theme.dart';

class MtSnackbar {
  static void show(BuildContext ctx, String msg, Color bg, IconData icon) {
    ScaffoldMessenger.of(ctx).hideCurrentSnackBar();
    ScaffoldMessenger.of(ctx).showSnackBar(
      SnackBar(
        content: Row(children: [
          Icon(icon, color: Colors.white, size: 18),
          const SizedBox(width: 10),
          Expanded(child: Text(msg, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600))),
        ]),
        backgroundColor: bg,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        margin: const EdgeInsets.all(16),
        duration: const Duration(seconds: 3),
      ),
    );
  }

  static void success(BuildContext ctx, String msg) =>
      show(ctx, msg, AppColors.secondary, Icons.check_circle_outline);

  static void error(BuildContext ctx, String msg) =>
      show(ctx, msg, AppColors.danger, Icons.error_outline);

  static void info(BuildContext ctx, String msg) =>
      show(ctx, msg, AppColors.primary, Icons.info_outline);

  static void warning(BuildContext ctx, String msg) =>
      show(ctx, msg, AppColors.warning, Icons.warning_amber_outlined);
}


// =============================================================
// MonTour — lib/widgets/common/mt_shimmer.dart
// Skeleton loading pour les listes
// =============================================================

import 'package:shimmer/shimmer.dart';

class MtShimmerCard extends StatelessWidget {
  final double height;
  const MtShimmerCard({super.key, this.height = 80});

  @override
  Widget build(BuildContext context) {
    return Shimmer.fromColors(
      baseColor:  Colors.grey.shade200,
      highlightColor: Colors.grey.shade100,
      child: Container(
        height: height,
        margin: const EdgeInsets.only(bottom: 12),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
        ),
      ),
    );
  }
}

class MtShimmerList extends StatelessWidget {
  final int count;
  final double itemHeight;
  const MtShimmerList({super.key, this.count = 4, this.itemHeight = 80});

  @override
  Widget build(BuildContext context) => Column(
    children: List.generate(count, (_) => MtShimmerCard(height: itemHeight)),
  );
}


// =============================================================
// MonTour — lib/widgets/common/mt_badge.dart
// Badges de statut et priorité réutilisables
// =============================================================

class MtStatusBadge extends StatelessWidget {
  final String status;
  const MtStatusBadge({super.key, required this.status});

  static const _data = {
    'waiting':   ('⏳ En attente', AppColors.warning),
    'called':    ('📢 Appelé',     AppColors.primary),
    'served':    ('✅ Servi',      AppColors.secondary),
    'cancelled': ('❌ Annulé',     AppColors.danger),
    'missed':    ('⚠️ Absent',     AppColors.warning),
    'open':      ('✅ Ouvert',     AppColors.secondary),
    'closed':    ('🔒 Fermé',      AppColors.danger),
    'paused':    ('⏸️ Pause',      AppColors.warning),
  };

  @override
  Widget build(BuildContext context) {
    final d = _data[status] ?? ('❓ Inconnu', AppColors.textSecondary);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
      decoration: BoxDecoration(
        color: d.$2.withOpacity(0.12),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        d.$1,
        style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: d.$2),
      ),
    );
  }
}

class MtPriorityBadge extends StatelessWidget {
  final String priority;
  const MtPriorityBadge({super.key, required this.priority});

  static const _data = {
    'urgent':   ('🚨 Urgent',   AppColors.danger),
    'handicap': ('♿ Handicap', AppColors.handicap),
    'senior':   ('👴 Senior',   AppColors.senior),
    'normal':   ('👤 Normal',   AppColors.secondary),
  };

  @override
  Widget build(BuildContext context) {
    final d = _data[priority] ?? _data['normal']!;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
      decoration: BoxDecoration(
        color: d.$2.withOpacity(0.12),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        d.$1,
        style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: d.$2),
      ),
    );
  }
}


// =============================================================
// MonTour — lib/widgets/common/mt_empty_state.dart
// Écran vide réutilisable
// =============================================================

class MtEmptyState extends StatelessWidget {
  final String emoji;
  final String title;
  final String? subtitle;
  final String? actionLabel;
  final VoidCallback? onAction;

  const MtEmptyState({
    super.key,
    required this.emoji,
    required this.title,
    this.subtitle,
    this.actionLabel,
    this.onAction,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(40),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(emoji, style: const TextStyle(fontSize: 64)),
            const SizedBox(height: 16),
            Text(title, style: Theme.of(context).textTheme.titleMedium, textAlign: TextAlign.center),
            if (subtitle != null) ...[
              const SizedBox(height: 8),
              Text(subtitle!, style: Theme.of(context).textTheme.bodyMedium, textAlign: TextAlign.center),
            ],
            if (actionLabel != null && onAction != null) ...[
              const SizedBox(height: 20),
              ElevatedButton(onPressed: onAction, child: Text(actionLabel!)),
            ],
          ],
        ),
      ),
    );
  }
}


// =============================================================
// MonTour — lib/widgets/common/mt_error_widget.dart
// Widget d'erreur avec bouton retry
// =============================================================

class MtErrorWidget extends StatelessWidget {
  final String   message;
  final VoidCallback? onRetry;

  const MtErrorWidget({super.key, required this.message, this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.wifi_off_rounded, size: 56, color: AppColors.textSecondary),
            const SizedBox(height: 12),
            const Text('Connexion impossible', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
            const SizedBox(height: 6),
            Text(
              message,
              style: const TextStyle(fontSize: 13, color: AppColors.textSecondary),
              textAlign: TextAlign.center,
            ),
            if (onRetry != null) ...[
              const SizedBox(height: 20),
              ElevatedButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh),
                label: const Text('Réessayer'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}