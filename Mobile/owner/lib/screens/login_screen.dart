import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import 'package:local_auth/local_auth.dart';
import 'package:flutter/foundation.dart';
import 'dashboard_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _formKey = GlobalKey<FormState>();
  final LocalAuthentication auth = LocalAuthentication();
  bool _canCheckBiometrics = false;
  bool _hasSavedCredentials = false;
  bool _rememberMe = true;

  @override
  void initState() {
    super.initState();
    _checkBiometrics();
  }

  Future<void> _checkBiometrics() async {
    bool canCheckBiometrics;
    try {
      canCheckBiometrics = await auth.canCheckBiometrics || await auth.isDeviceSupported();
    } catch (e) {
      canCheckBiometrics = false;
    }

    final authProvider = Provider.of<AuthProvider>(context, listen: false);
    bool hasSavedCredentials = await authProvider.hasSavedCredentials();

    if (!mounted) return;

    setState(() {
      _canCheckBiometrics = canCheckBiometrics;
      _hasSavedCredentials = hasSavedCredentials;
    });
  }

  Future<void> _authenticateWithBiometrics() async {
    final authProvider = Provider.of<AuthProvider>(context, listen: false);
    bool authenticated = false;
    if (kIsWeb) {
       ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Biometrics not supported in web.')));
       return;
    }
    
    try {
      authenticated = await auth.authenticate(
        localizedReason: 'Scan your fingerprint (or face) to authenticate',
      );
    } catch (e) {
       ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
    }

    if (authenticated && mounted) {
      final success = await authProvider.loginWithSavedCredentials();
      if (!success && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Failed to login with saved credentials.')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final authProvider = Provider.of<AuthProvider>(context);

    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFFF1F8E9), Color(0xFFC5E1A5)],
          ),
        ),
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24.0),
            child: Card(
              elevation: 8,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              child: Padding(
                padding: const EdgeInsets.all(32.0),
                child: Form(
                  key: _formKey,
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      // Logo Placeholder
                      // Logo with dark background for visibility
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                        decoration: BoxDecoration(
                          color: const Color(0xFF1B5E20), // Dark Green to match theme but provide contrast
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Image.asset(
                          'assets/zeebulllogo.png',
                          height: 120,
                        ),
                      ),
                      const SizedBox(height: 32),
                      
                      if (authProvider.error != null)
                        Container(
                          padding: const EdgeInsets.all(8),
                          margin: const EdgeInsets.only(bottom: 16),
                          color: Colors.red.shade100,
                          child: Text(
                            authProvider.error!,
                            style: TextStyle(color: Colors.red.shade900),
                            textAlign: TextAlign.center,
                          ),
                        ),

                      TextFormField(
                        controller: _emailController,
                        decoration: const InputDecoration(
                          labelText: 'Email',
                          prefixIcon: Icon(Icons.email_outlined),
                          border: OutlineInputBorder(),
                        ),
                        validator: (value) =>
                            value?.isEmpty ?? true ? 'Please enter your email' : null,
                      ),
                      const SizedBox(height: 16),
                      TextFormField(
                        controller: _passwordController,
                        obscureText: true,
                        decoration: const InputDecoration(
                          labelText: 'Password',
                          prefixIcon: Icon(Icons.lock_outline),
                          border: OutlineInputBorder(),
                        ),
                        validator: (value) =>
                            value?.isEmpty ?? true ? 'Please enter your password' : null,
                      ),
                      
                      // Remember Me Checkbox
                      Row(
                        children: [
                          Checkbox(
                            value: _rememberMe,
                            onChanged: (value) {
                              setState(() {
                                _rememberMe = value ?? false;
                              });
                            },
                          ),
                          const Text('Remember me (Enable Biometrics)'),
                        ],
                      ),
                      const SizedBox(height: 8),
                      
                      SizedBox(
                        width: double.infinity,
                        height: 48,
                        child: ElevatedButton(
                          onPressed: authProvider.isLoading
                              ? null
                              : () async {
                                  if (_formKey.currentState?.validate() ?? false) {
                                    final success = await authProvider.login(
                                      _emailController.text,
                                      _passwordController.text,
                                      saveCredentials: _rememberMe,
                                    );
                                    if (success && mounted) {
                                       // Navigation handled by AuthenticationWrapper
                                    }
                                  }
                                },
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF7CB342),
                            foregroundColor: Colors.white,
                          ),
                          child: authProvider.isLoading
                              ? const CircularProgressIndicator(color: Colors.white)
                              : const Text('Sign In'),
                        ),
                      ),
                      
                      if (_canCheckBiometrics && _hasSavedCredentials) ...[
                        const SizedBox(height: 24),
                        const Divider(),
                        const SizedBox(height: 16),
                        OutlinedButton.icon(
                          onPressed: _authenticateWithBiometrics,
                          icon: const Icon(Icons.fingerprint, size: 32),
                          label: const Text('Login with Biometrics'),
                          style: OutlinedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 24),
                            foregroundColor: const Color(0xFF1B5E20),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
