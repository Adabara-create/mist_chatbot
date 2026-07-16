import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'app_theme.dart';
import 'mist_state.dart';

/// Mist's face. A layered, glowing sphere that breathes at rest, contracts
/// and ripples while listening, and pulses outward while she speaks.
///
/// [amplitude] is a 0..1 value driven externally by mic sound level while
/// listening, or by word-boundary pulses while speaking.
class MistOrb extends StatefulWidget {
  final MistState state;
  final double amplitude;
  final double size;

  const MistOrb({
    super.key,
    required this.state,
    required this.amplitude,
    this.size = 260,
  });

  @override
  State<MistOrb> createState() => _MistOrbState();
}

class _MistOrbState extends State<MistOrb> with TickerProviderStateMixin {
  late final AnimationController _breathe = AnimationController(
    vsync: this,
    duration: const Duration(seconds: 4),
  )..repeat(reverse: true);

  late final AnimationController _rotate = AnimationController(
    vsync: this,
    duration: const Duration(seconds: 14),
  )..repeat();

  late final AnimationController _amp = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 160),
    value: 0,
  );

  @override
  void didUpdateWidget(covariant MistOrb oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.amplitude != widget.amplitude) {
      _amp.animateTo(
        widget.amplitude.clamp(0.0, 1.0),
        curve: Curves.easeOut,
      );
    }
    if (widget.state == MistState.thinking) {
      _rotate.duration = const Duration(seconds: 3);
    } else {
      _rotate.duration = const Duration(seconds: 14);
    }
  }

  @override
  void dispose() {
    _breathe.dispose();
    _rotate.dispose();
    _amp.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: Listenable.merge([_breathe, _rotate, _amp]),
      builder: (context, _) {
        final breathe = 1 + (_breathe.value * 0.045);
        final ampScale = 1 + (_amp.value * 0.24);
        final scale = breathe * ampScale;
        final glow = 0.35 + _amp.value * 0.65;
        final size = widget.size;

        return SizedBox(
          width: size,
          height: size,
          child: Stack(
            alignment: Alignment.center,
            children: [
              // Outer atmospheric glow.
              Transform.scale(
                scale: scale * 1.4,
                child: Container(
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: RadialGradient(
                      colors: [
                        MistColors.violetDeep.withOpacity(0.30 * glow),
                        Colors.transparent,
                      ],
                    ),
                  ),
                ),
              ),
              // Rotating sweep ring — the "mist" swirling around her core.
              Transform.rotate(
                angle: _rotate.value * 2 * math.pi,
                child: Transform.scale(
                  scale: scale * 1.1,
                  child: Container(
                    width: size * 0.86,
                    height: size * 0.86,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: SweepGradient(
                        colors: [
                          Colors.transparent,
                          MistColors.teal.withOpacity(0.55 * glow),
                          Colors.transparent,
                          MistColors.violet.withOpacity(0.5 * glow),
                          Colors.transparent,
                        ],
                        stops: const [0.0, 0.22, 0.5, 0.72, 1.0],
                      ),
                    ),
                  ),
                ),
              ),
              // Counter-rotating fainter ring for depth.
              Transform.rotate(
                angle: -_rotate.value * 2 * math.pi * 0.6,
                child: Transform.scale(
                  scale: scale * 0.95,
                  child: Container(
                    width: size * 0.7,
                    height: size * 0.7,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: SweepGradient(
                        colors: [
                          Colors.transparent,
                          MistColors.violet.withOpacity(0.35 * glow),
                          Colors.transparent,
                        ],
                        stops: const [0.0, 0.5, 1.0],
                      ),
                    ),
                  ),
                ),
              ),
              // The core sphere.
              Transform.scale(
                scale: scale,
                child: Container(
                  width: size * 0.62,
                  height: size * 0.62,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: RadialGradient(
                      center: const Alignment(-0.3, -0.35),
                      colors: [
                        Colors.white.withOpacity(0.95),
                        MistColors.violet,
                        MistColors.violetDeep,
                      ],
                      stops: const [0.0, 0.45, 1.0],
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: MistColors.violet.withOpacity(0.55 * glow),
                        blurRadius: size * 0.22 * glow,
                        spreadRadius: size * 0.02 * glow,
                      ),
                      BoxShadow(
                        color: MistColors.teal.withOpacity(0.22 * glow),
                        blurRadius: size * 0.3 * glow,
                      ),
                    ],
                  ),
                ),
              ),
              // Inner bright core — brightens as amplitude rises.
              Transform.scale(
                scale: scale * 0.5,
                child: Container(
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: Colors.white.withOpacity(0.55 + _amp.value * 0.4),
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
