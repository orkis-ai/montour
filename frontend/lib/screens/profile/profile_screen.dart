// =============================================================
// MonTour — lib/screens/profile/profile_screen.dart
// =============================================================

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/router.dart';
import '../../core/theme.dart';
import '../../providers/auth_provider.dart';
import '../../providers/tickets_provider.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final userAsync = ref.watch(authNotifierProvider);
    final ticketsAsync = ref.watch(ticketsNotifierProvider);

    return userAsync.when(
      loading:
          () =>
              const Scaffold(body: Center(child: CircularProgressIndicator())),
      error:
          (_, __) => const Scaffold(body: Center(child: Text('Erreur profil'))),
      data: (user) {
        if (user == null) {
          WidgetsBinding.instance.addPostFrameCallback(
            (_) => context.go(AppRoutes.login),
          );
          return const SizedBox();
        }

        final tickets = ticketsAsync.value ?? [];
        final served = tickets.where((t) => t.isServed).length;
        final waiting = tickets.where((t) => t.isWaiting).length;
        final cancelled = tickets.where((t) => t.isCancelled).length;

        return Scaffold(
          body: CustomScrollView(
            slivers: [
              SliverAppBar(
                pinned: true,
                automaticallyImplyLeading: false,
                expandedHeight: 220,
                flexibleSpace: FlexibleSpaceBar(
                  background: Container(
                    decoration: const BoxDecoration(
                      gradient: LinearGradient(
                        colors: [Color(0xFF4FACFE), Color(0xFF00F2FE)],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                    ),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const SizedBox(height: 48),
                        // Avatar
                        Container(
                          width: 80,
                          height: 80,
                          decoration: BoxDecoration(
                            color: Colors.white24,
                            shape: BoxShape.circle,
                            border: Border.all(color: Colors.white30, width: 2),
                          ),
                          child: Center(
                            child:
                                user.avatarUrl != null
                                    ? ClipOval(
                                      child: Image.network(
                                        user.avatarUrl!,
                                        fit: BoxFit.cover,
                                      ),
                                    )
                                    : Text(
                                      user.username.isNotEmpty
                                          ? user.username[0].toUpperCase()
                                          : 'U',
                                      style: const TextStyle(
                                        fontSize: 32,
                                        fontWeight: FontWeight.w900,
                                        color: Colors.white,
                                      ),
                                    ),
                          ),
                        ),
                        const SizedBox(height: 10),
                        Text(
                          user.username,
                          style: const TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.w900,
                            color: Colors.white,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          user.email,
                          style: const TextStyle(
                            fontSize: 13,
                            color: Colors.white70,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            _PillBadge(
                              label: user.priorityLabel,
                              color: Colors.white24,
                            ),
                            const SizedBox(width: 8),
                            _PillBadge(
                              label:
                                  user.role == 'admin'
                                      ? '⚙️ Admin'
                                      : user.role == 'agent'
                                      ? '🏥 Agent'
                                      : '👤 Usager',
                              color: Colors.white24,
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
                    // ── Stats ────────────────────────────────
                    Row(
                      children: [
                        _StatCard(
                          icon: '📋',
                          label: 'Total',
                          value: '${tickets.length}',
                          color: AppColors.primary,
                        ),
                        const SizedBox(width: 8),
                        _StatCard(
                          icon: '✅',
                          label: 'Servis',
                          value: '$served',
                          color: AppColors.secondary,
                        ),
                        const SizedBox(width: 8),
                        _StatCard(
                          icon: '⏳',
                          label: 'Attente',
                          value: '$waiting',
                          color: AppColors.warning,
                        ),
                        const SizedBox(width: 8),
                        _StatCard(
                          icon: '❌',
                          label: 'Annulés',
                          value: '$cancelled',
                          color: AppColors.danger,
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),

                    // ── Infos profil ─────────────────────────
                    _SectionCard(
                      title: 'Informations personnelles',
                      trailing: TextButton.icon(
                        onPressed: () => context.go(AppRoutes.editProfile),
                        icon: const Icon(Icons.edit, size: 16),
                        label: const Text('Modifier'),
                      ),
                      children: [
                        _InfoRow('👤 Nom', user.username),
                        _InfoRow('📧 Email', user.email),
                        _InfoRow(
                          '📞 Téléphone',
                          user.phone.isEmpty ? 'Non renseigné' : user.phone,
                        ),
                        _InfoRow('🏷️ Rôle', user.role),
                        _InfoRow('🎯 Priorité', user.priority),
                        if (user.dateJoined != null)
                          _InfoRow(
                            '📅 Membre depuis',
                            '${user.dateJoined!.day}/${user.dateJoined!.month}/${user.dateJoined!.year}',
                          ),
                      ],
                    ),
                    const SizedBox(height: 12),

                    // ── Paramètres ───────────────────────────
                    _SectionCard(
                      title: 'Paramètres',
                      children: [
                        ListTile(
                          leading: const Icon(
                            Icons.notifications_outlined,
                            color: AppColors.primary,
                          ),
                          title: const Text(
                            'Notifications push',
                            style: TextStyle(fontWeight: FontWeight.w600),
                          ),
                          trailing: Switch(value: true, onChanged: (_) {}),
                          dense: true,
                        ),
                        ListTile(
                          leading: const Icon(
                            Icons.lock_outlined,
                            color: AppColors.primary,
                          ),
                          title: const Text(
                            'Changer le mot de passe',
                            style: TextStyle(fontWeight: FontWeight.w600),
                          ),
                          trailing: const Icon(
                            Icons.arrow_forward_ios,
                            size: 14,
                          ),
                          dense: true,
                          onTap: () {},
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),

                    // ── Déconnexion ─────────────────────────
                    OutlinedButton.icon(
                      style: OutlinedButton.styleFrom(
                        foregroundColor: AppColors.danger,
                        side: const BorderSide(color: AppColors.danger),
                        minimumSize: const Size(double.infinity, 52),
                      ),
                      icon: const Icon(Icons.logout),
                      label: const Text('Se déconnecter'),
                      onPressed: () async {
                        await ref.read(authNotifierProvider.notifier).logout();
                        if (context.mounted) context.go(AppRoutes.login);
                      },
                    ),
                    const SizedBox(height: 8),
                    Center(
                      child: Text(
                        'MonTour v1.0.0 — Bénin 🇧🇯',
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                    ),
                    const SizedBox(height: 32),
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

// ── Widgets locaux ─────────────────────────────────────────────

class _PillBadge extends StatelessWidget {
  final String label;
  final Color color;
  const _PillBadge({required this.label, required this.color});
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
    decoration: BoxDecoration(
      color: color,
      borderRadius: BorderRadius.circular(20),
    ),
    child: Text(
      label,
      style: const TextStyle(
        fontSize: 12,
        color: Colors.white,
        fontWeight: FontWeight.w700,
      ),
    ),
  );
}

class _StatCard extends StatelessWidget {
  final String icon, label, value;
  final Color color;
  const _StatCard({
    required this.icon,
    required this.label,
    required this.value,
    required this.color,
  });
  @override
  Widget build(BuildContext context) => Expanded(
    child: Container(
      padding: const EdgeInsets.symmetric(vertical: 14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.06), blurRadius: 8),
        ],
      ),
      child: Column(
        children: [
          Text(icon, style: const TextStyle(fontSize: 22)),
          const SizedBox(height: 4),
          Text(
            value,
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w900,
              color: color,
            ),
          ),
          Text(
            label,
            style: const TextStyle(
              fontSize: 10,
              color: AppColors.textSecondary,
            ),
          ),
        ],
      ),
    ),
  );
}

class _SectionCard extends StatelessWidget {
  final String title;
  final List<Widget> children;
  final Widget? trailing;
  const _SectionCard({
    required this.title,
    required this.children,
    this.trailing,
  });
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(
      color: Colors.white,
      borderRadius: BorderRadius.circular(16),
      boxShadow: [
        BoxShadow(color: Colors.black.withOpacity(0.06), blurRadius: 8),
      ],
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              title,
              style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15),
            ),
            if (trailing != null) trailing!,
          ],
        ),
        const Divider(height: 16),
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
          style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
        ),
      ],
    ),
  );
}

// =============================================================
// MonTour — lib/screens/profile/edit_profile_screen.dart
// =============================================================

class EditProfileScreen extends ConsumerStatefulWidget {
  const EditProfileScreen({super.key});
  @override
  ConsumerState<EditProfileScreen> createState() => _EditProfileScreenState();
}

class _EditProfileScreenState extends ConsumerState<EditProfileScreen> {
  final _formKey = GlobalKey<FormState>();
  final _usernameCtrl = TextEditingController();
  final _phoneCtrl = TextEditingController();
  String _priority = 'normal';
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    final user = ref.read(authNotifierProvider).value;
    if (user != null) {
      _usernameCtrl.text = user.username;
      _phoneCtrl.text = user.phone;
      _priority = user.priority;
    }
  }

  @override
  void dispose() {
    _usernameCtrl.dispose();
    _phoneCtrl.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _loading = true);
    try {
      await ref.read(authNotifierProvider.notifier).updateProfile({
        'username': _usernameCtrl.text.trim(),
        'phone': _phoneCtrl.text.trim(),
        'priority': _priority,
      });
      if (mounted) {
        Navigator.pop(context);
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('✅ Profil mis à jour !')));
      }
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Erreur : $e')));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Modifier le profil')),
    body: Form(
      key: _formKey,
      child: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          TextFormField(
            controller: _usernameCtrl,
            decoration: const InputDecoration(
              labelText: 'Nom d\'utilisateur',
              prefixIcon: Icon(Icons.person_outlined),
            ),
            validator: (v) => (v == null || v.isEmpty) ? 'Requis' : null,
          ),
          const SizedBox(height: 16),
          TextFormField(
            controller: _phoneCtrl,
            decoration: const InputDecoration(
              labelText: 'Téléphone',
              prefixIcon: Icon(Icons.phone_outlined),
            ),
            keyboardType: TextInputType.phone,
          ),
          const SizedBox(height: 16),
          const Text(
            'Priorité',
            style: TextStyle(
              fontWeight: FontWeight.w700,
              fontSize: 13,
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: 8),
          DropdownButtonFormField<String>(
            value: _priority,
            decoration: const InputDecoration(),
            items: const [
              DropdownMenuItem(value: 'normal', child: Text('👤 Normal')),
              DropdownMenuItem(value: 'senior', child: Text('👴 Senior')),
              DropdownMenuItem(value: 'handicap', child: Text('♿ Handicap')),
              DropdownMenuItem(value: 'urgent', child: Text('🚨 Urgent')),
            ],
            onChanged: (v) => setState(() => _priority = v!),
          ),
          const SizedBox(height: 28),
          ElevatedButton(
            onPressed: _loading ? null : _save,
            child:
                _loading
                    ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                    : const Text('💾 Sauvegarder'),
          ),
        ],
      ),
    ),
  );
}
