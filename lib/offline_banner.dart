import 'package:flutter/material.dart';
import 'app_theme.dart';

/// Small dismissible popup shown near the top of the screen when the
/// device has no internet connection.
class OfflineBanner extends StatelessWidget {
  final VoidCallback onDismiss;

  const OfflineBanner({super.key, required this.onDismiss});

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Align(
        alignment: Alignment.topCenter,
        child: Container(
          margin: const EdgeInsets.only(top: 12, left: 16, right: 16),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          decoration: BoxDecoration(
            color: MistColors.bgSurface,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: MistColors.danger.withOpacity(0.4)),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.4),
                blurRadius: 20,
                offset: const Offset(0, 6),
              ),
            ],
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.wifi_off_rounded, color: MistColors.danger, size: 18),
              const SizedBox(width: 10),
              Text(
                'No internet connection',
                style: TextStyle(
                  color: MistColors.textPrimary,
                  fontSize: 13,
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(width: 10),
              GestureDetector(
                onTap: onDismiss,
                behavior: HitTestBehavior.opaque,
                child: Icon(Icons.close_rounded, color: MistColors.textMuted, size: 18),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
