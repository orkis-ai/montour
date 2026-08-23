// =============================================================
// MonTour — lib/screens/auth/register_screen.dart
// =============================================================

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/router.dart';
import '../../core/theme.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/common/mt_button.dart';
import '../../widgets/common/mt_text_field.dart';
import '../../widgets/common/mt_snackbar.dart';

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});
  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _usernameCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _phoneCtrl = TextEditingController();
  final _passCtrl = TextEditingController();
  final _confirmCtrl = TextEditingController();
  String _priority = 'normal';
  bool _loading = false;
  bool _obscure = true;

  @override
  void dispose() {
    _usernameCtrl.dispose();
    _emailCtrl.dispose();
    _phoneCtrl.dispose();
    _passCtrl.dispose();
    _confirmCtrl.dispose();
    super.dispose();
  }

  Future<void> _register() async {
    if (!_formKey.currentState!.validate()) return;
    if (_passCtrl.text != _confirmCtrl.text) {
      MtSnackbar.error(context, 'Les mots de passe ne correspondent pas.');
      return;
    }
    setState(() => _loading = true);
    try {
      await ref.read(authNotifierProvider.notifier).register({
        'username': _usernameCtrl.text.trim(),
        'email': _emailCtrl.text.trim(),
        'phone': _phoneCtrl.text.trim(),
        'password': _passCtrl.text,
        'password2': _confirmCtrl.text,
        'priority': _priority,
      });
      if (mounted) context.go(AppRoutes.home);
    } catch (e) {
      if (mounted) MtSnackbar.error(context, 'Erreur : ${e.toString()}');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Créer un compte'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go(AppRoutes.login),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // En-tête
                Center(
                  child: Column(
                    children: [
                      const Text('📝', style: TextStyle(fontSize: 48)),
                      const SizedBox(height: 8),
                      Text(
                        'Rejoignez MonTour',
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Remplissez les informations ci-dessous',
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 28),

                // Champs
                MtTextField(
                  controller: _usernameCtrl,
                  label: 'Nom d\'utilisateur *',
                  hint: 'Moussa Abdoulaye',
                  prefixIcon: Icons.person_outlined,
                  validator:
                      (v) => (v == null || v.isEmpty) ? 'Nom requis' : null,
                ),
                const SizedBox(height: 14),
                MtTextField(
                  controller: _emailCtrl,
                  label: 'Email *',
                  hint: 'moussa@example.bj',
                  keyboardType: TextInputType.emailAddress,
                  prefixIcon: Icons.email_outlined,
                  validator: (v) {
                    if (v == null || v.isEmpty) return 'Email requis';
                    if (!v.contains('@')) return 'Email invalide';
                    return null;
                  },
                ),
                const SizedBox(height: 14),
                MtTextField(
                  controller: _phoneCtrl,
                  label: 'Téléphone',
                  hint: '+229 XX XX XX XX',
                  keyboardType: TextInputType.phone,
                  prefixIcon: Icons.phone_outlined,
                ),
                const SizedBox(height: 14),

                // Priorité
                Text(
                  'Niveau de priorité',
                  style: Theme.of(
                    context,
                  ).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w700),
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
                        DropdownMenuItem(
                          value: 'normal',
                          child: Text('👤 Normal'),
                        ),
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
                const SizedBox(height: 14),
                MtTextField(
                  controller: _passCtrl,
                  label: 'Mot de passe *',
                  hint: '••••••••',
                  obscureText: _obscure,
                  prefixIcon: Icons.lock_outlined,
                  suffixIcon: IconButton(
                    icon: Icon(
                      _obscure
                          ? Icons.visibility_outlined
                          : Icons.visibility_off_outlined,
                    ),
                    onPressed: () => setState(() => _obscure = !_obscure),
                  ),
                  validator: (v) {
                    if (v == null || v.isEmpty) return 'Mot de passe requis';
                    if (v.length < 8) return 'Minimum 8 caractères';
                    return null;
                  },
                ),
                const SizedBox(height: 14),
                MtTextField(
                  controller: _confirmCtrl,
                  label: 'Confirmer le mot de passe *',
                  hint: '••••••••',
                  obscureText: _obscure,
                  prefixIcon: Icons.lock_outlined,
                  validator:
                      (v) =>
                          (v == null || v.isEmpty)
                              ? 'Confirmation requise'
                              : null,
                ),
                const SizedBox(height: 28),
                MtButton(
                  label: '✅ Créer mon compte',
                  onPressed: _register,
                  loading: _loading,
                ),
                const SizedBox(height: 16),
                Center(
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Text('Déjà inscrit ? '),
                      GestureDetector(
                        onTap: () => context.go(AppRoutes.login),
                        child: Text(
                          'Se connecter',
                          style: TextStyle(
                            color: AppColors.primary,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 32),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
