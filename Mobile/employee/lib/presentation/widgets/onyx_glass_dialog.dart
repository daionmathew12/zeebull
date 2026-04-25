import 'package:flutter/material.dart';
import 'dart:ui';

class OnyxGlassDialog extends StatelessWidget {
  final String title;
  final List<Widget> children;
  final List<Widget>? actions;
  final double blur;
  final double borderRadius;

  const OnyxGlassDialog({
    super.key,
    required this.title,
    required this.children,
    this.actions,
    this.blur = 20.0,
    this.borderRadius = 28.0,
  });

  @override
  Widget build(BuildContext context) {
    return BackdropFilter(
      filter: ImageFilter.blur(sigmaX: blur, sigmaY: blur),
      child: AlertDialog(
        backgroundColor: Colors.white.withOpacity(0.08),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(borderRadius),
          side: BorderSide(color: Colors.white.withOpacity(0.12), width: 0.8),
        ),
        title: Text(
          title.toUpperCase(),
          textAlign: TextAlign.center,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 16,
            fontWeight: FontWeight.w900,
            letterSpacing: 1.5,
          ),
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: children,
        ),
        actions: actions,
        actionsAlignment: MainAxisAlignment.spaceEvenly,
        buttonPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      ),
    );
  }
}
