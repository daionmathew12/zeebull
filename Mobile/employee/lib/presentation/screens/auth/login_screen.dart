import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/presentation/providers/auth_provider.dart';
import 'package:orchid_employee/core/constants/app_colors.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  String _selectedDepartment = 'Kitchen'; // Default
  final List<String> _departments = ['Kitchen', 'Housekeeping', 'Restaurant', 'Maintenance'];
  bool _isLoading = false;

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _handleLogin() async {
    if (_formKey.currentState!.validate()) {
      setState(() => _isLoading = true);
      
      try {
        final authProvider = Provider.of<AuthProvider>(context, listen: false);
        final success = await authProvider.login(
          _usernameController.text,
          _passwordController.text,
        );

        setState(() => _isLoading = false);

        if (success && mounted) {
           // Navigate based on selection
           String route = '/dashboard';
           // We can also route directly if we want to bypass the generic DashboardScreen wrapper
           // But DashboardScreen handles role-based body. 
           // If the user wants to choose, maybe they have multiple roles?
           // For now, let's just push to dashboard, but we could try to force the tab if we had that logic.
           // Wait, the user said "no need of this page" (the generic dashboard). 
           // So we should navigate DIRECTLY to the module.
           

           if (success && mounted) {
             Navigator.of(context).pushNamedAndRemoveUntil('/dashboard', (route) => false);
           }
        } else if (!success && mounted) {
           ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Login failed: unknown error.')),
          );
        }
      } catch (e) {
        setState(() => _isLoading = false);
        String errorMessage = "Login failed.";
        final eStr = e.toString();
        // Dio exception usually contains 'response'
        if (eStr.contains("401")) {
          errorMessage = "Invalid Credentials";
        } else if (eStr.contains("404")) {
           errorMessage = "API Not Found (404)";
        } else if (eStr.contains("500")) {
           errorMessage = "Server Error (500)";
        } else {
          errorMessage += " $e";
        }
        
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(errorMessage), backgroundColor: Colors.red),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Form(
            key: _formKey,
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Icon(
                  Icons.hotel, // Or app logo
                  size: 80,
                  color: AppColors.primary,
                ),
                const SizedBox(height: 32),
                const Text(
                  'Orchid Resort\nEmployee Portal',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: AppColors.textPrimary,
                  ),
                ),
                const SizedBox(height: 48),
                TextFormField(
                  controller: _usernameController,
                  decoration: const InputDecoration(
                    labelText: 'Username / Employee ID',
                    prefixIcon: Icon(Icons.person),
                    border: OutlineInputBorder(),
                  ),
                  validator: (value) =>
                      value?.isEmpty == true ? 'Required' : null,
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _passwordController,
                  obscureText: true,
                  decoration: const InputDecoration(
                    labelText: 'Password',
                    prefixIcon: Icon(Icons.lock),
                    border: OutlineInputBorder(),
                  ),
                  validator: (value) =>
                      value?.isEmpty == true ? 'Required' : null,
                ),
                const SizedBox(height: 24),
                ElevatedButton(
                  onPressed: _isLoading ? null : _handleLogin,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primary,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  child: _isLoading
                      ? const CircularProgressIndicator(color: Colors.white)
                      : const Text(
                          'LOGIN',
                          style: TextStyle(fontSize: 16, color: Colors.white),
                        ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
