/// Chart colours. Hues come from the dataviz reference palette (blue /
/// orange / aqua are categorical slots 1-3, validated all-pairs for CVD in
/// light mode); share-of-power uses the blue sequential ramp. Aqua is below
/// 3:1 on the light surface, so every collect mark also carries a text label.
library;

import 'dart:math' as math;

import 'package:flutter/material.dart';

class ChartColors {
  static const surface = Color(0xFFFCFCFB);
  static const inkPrimary = Color(0xFF0B0B0B);
  static const inkSecondary = Color(0xFF52514E);
  static const inkMuted = Color(0xFF8A8985);
  static const grid = Color(0xFFE6E5E1);

  /// Categorical: collecting / steering / everything else.
  static const collect = Color(0xFF1BAF7A);
  static const steer = Color(0xFFEB6834);
  static const other = Color(0xFFB4B2A9);

  /// Sequential blue ramp (steps 100 -> 700), light = small share of power.
  static const _ramp = [
    Color(0xFFCDE2FB),
    Color(0xFF9EC5F4),
    Color(0xFF6DA7EC),
    Color(0xFF3987E5),
    Color(0xFF256ABF),
    Color(0xFF184F95),
    Color(0xFF0D366B),
  ];

  /// Colour for a power share in 0..1. Uses sqrt so small-but-real shares
  /// stay distinguishable from zero.
  static Color share(double share) {
    final t = share.clamp(0.0, 1.0);
    if (t <= 0) return const Color(0xFFEFEFEC);
    final x = math.sqrt(t) * (_ramp.length - 1);
    final i = x.floor().clamp(0, _ramp.length - 2);
    return Color.lerp(_ramp[i], _ramp[i + 1], x - i)!;
  }

  /// Text that stays legible on a given fill.
  static Color onFill(Color fill) =>
      fill.computeLuminance() > 0.45 ? inkPrimary : Colors.white;
}
