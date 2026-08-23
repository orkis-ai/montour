// =============================================================
// MonTour — lib/screens/profile/edit_profile_screen.dart
// =============================================================

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/common/mt_text_field.dart';
import '../../widgets/common/mt_button.dart';
import '../../widgets/common/mt_snackbar.dart';

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
        MtSnackbar.success(context, '✅ Profil mis à jour avec succès !');
        Navigator.of(context).pop();
      }
    } catch (e) {
      if (mounted)
        MtSnackbar.error(context, 'Erreur lors de la mise à jour : $e');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Modifier le profil'),
        actions: [
          TextButton(
            onPressed: _loading ? null : _save,
            child: const Text(
              'Sauvegarder',
              style: TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ],
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            // Avatar placeholder
            Center(
              child: Stack(
                children: [
                  Container(
                    width: 90,
                    height: 90,
                    decoration: BoxDecoration(
                      color: AppColors.primary.withOpacity(0.12),
                      shape: BoxShape.circle,
                      border: Border.all(color: AppColors.primary, width: 2),
                    ),
                    child: Center(
                      child: Text(
                        _usernameCtrl.text.isNotEmpty
                            ? _usernameCtrl.text[0].toUpperCase()
                            : 'U',
                        style: const TextStyle(
                          fontSize: 36,
                          fontWeight: FontWeight.w900,
                          color: AppColors.primary,
                        ),
                      ),
                    ),
                  ),
                  Positioned(
                    bottom: 0,
                    right: 0,
                    child: Container(
                      padding: const EdgeInsets.all(6),
                      decoration: const BoxDecoration(
                        color: AppColors.primary,
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(
                        Icons.camera_alt,
                        size: 14,
                        color: Colors.white,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 28),

            MtTextField(
              controller: _usernameCtrl,
              label: 'Nom d\'utilisateur *',
              hint: 'Votre nom complet',
              prefixIcon: Icons.person_outlined,
              validator:
                  (v) => (v == null || v.trim().isEmpty) ? 'Nom requis' : null,
              onChanged: (_) => setState(() {}),
            ),
            const SizedBox(height: 16),

            MtTextField(
              controller: _phoneCtrl,
              label: 'Numéro de téléphone',
              hint: '+229 XX XX XX XX',
              keyboardType: TextInputType.phone,
              prefixIcon: Icons.phone_outlined,
            ),
            const SizedBox(height: 16),

            // Priorité
            const Text(
              'Niveau de priorité',
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w700,
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              decoration: BoxDecoration(
                color: const Color(0xFFFAFBFD),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.border, width: 1.5),
              ),
              child: DropdownButtonHideUnderline(
                child: DropdownButton<String>(
                  value: _priority,
                  isExpanded: true,
                  items: const [
                    DropdownMenuItem(value: 'normal', child: Text('👤 Normal')),
                    DropdownMenuItem(
                      value: 'senior',
                      child: Text('👴 Senior (60+ ans)'),
                    ),
                    DropdownMenuItem(
                      value: 'handicap',
                      child: Text('♿ Personne handicapée'),
                    ),
                    DropdownMenuItem(
                      value: 'urgent',
                      child: Text('🚨 Urgence médicale'),
                    ),
                  ],
                  onChanged: (v) => setState(() => _priority = v!),
                ),
              ),
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.primary.withOpacity(0.06),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Text(
                '💡 La priorité influence votre position dans la file d\'attente. Les cas urgents sont traités en premier.',
                style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
              ),
            ),
            const SizedBox(height: 32),

            MtButton(
              label: '💾 Sauvegarder les modifications',
              onPressed: _save,
              loading: _loading,
            ),
            const SizedBox(height: 12),

            MtButton(
              label: 'Annuler',
              onPressed: () => Navigator.of(context).pop(),
              outlined: true,
            ),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }
}
