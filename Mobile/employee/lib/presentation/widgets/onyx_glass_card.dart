import 'package:flutter/material.dart';
import 'dart:ui';

class OnyxGlassCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry? padding;
  final double borderRadius;
  final double blur;
  final Color? color;
  final Border? border;
  final Color? borderColor;

  const OnyxGlassCard({
    super.key,
    required this.child,
    this.padding,
    this.borderRadius = 32.0,
    this.blur = 20.0,
    this.color,
    this.border,
    this.borderColor,
  });

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(borderRadius),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: blur, sigmaY: blur),
        child: Container(
          padding: padding,
          decoration: BoxDecoration(
            color: color ?? Colors.white.withOpacity(0.08),
            borderRadius: BorderRadius.circular(borderRadius),
            border: border ?? Border.all(
              color: borderColor ?? Colors.white.withOpacity(0.15),
              width: 0.8,
            ),
          ),
          child: child,
        ),
      ),
    );
  }
}

