/// A square-rigged frigate silhouette (light ships are warships, not freighters).
library;

import 'package:flutter/widgets.dart';

/// Paints the frigate into a [size]-pixel square centred on [center].
///
/// Matches the simpler of the two reference glyphs the user picked out: a
/// slim pointed-both-ends hull sitting on a wavy waterline, a bowsprit with
/// a small jib, and three masts of increasing height toward the stern --
/// only the tallest (sternmost) one flies a flag -- each with a curved
/// "leaf" sail (pointed at the mast top, bulging out on the leading side,
/// tapering back in to the mast at the deck). Bolder and lower-detail than
/// a literal galleon, which is what actually survives being shrunk to an
/// ~18px map-marker glyph.
void paintFrigate(Canvas canvas, Offset center, double size, Color color) {
  final paint = Paint()..color = color;
  Offset p(double x, double y) => Offset(center.dx + x * size, center.dy + y * size);
  void line(double x1, double y1, double x2, double y2, double w) =>
      canvas.drawLine(p(x1, y1), p(x2, y2), paint..strokeWidth = size * w);

  const deckY = 0.16;

  // Hull: a slim boat shape, pointed at both bow (right) and stern (left).
  final hull = Path()
    ..moveTo(p(0.44, deckY).dx, p(0.44, deckY).dy) // bow tip
    ..quadraticBezierTo(
        p(0.10, deckY + 0.14).dx, p(0.10, deckY + 0.14).dy, p(-0.44, deckY + 0.02).dx, p(-0.44, deckY + 0.02).dy)
    ..quadraticBezierTo(p(0.0, deckY + 0.22).dx, p(0.0, deckY + 0.22).dy, p(0.44, deckY).dx, p(0.44, deckY).dy)
    ..close();
  canvas.drawPath(hull, paint);

  // Wavy waterline beneath the hull.
  final water = Path()..moveTo(p(-0.5, 0.40).dx, p(-0.5, 0.40).dy);
  for (var i = 0; i < 4; i++) {
    final x1 = -0.5 + i * 0.25 + 0.125, x2 = -0.5 + (i + 1) * 0.25;
    water.quadraticBezierTo(p(x1, 0.36).dx, p(x1, 0.36).dy, p(x2, 0.40).dx, p(x2, 0.40).dy);
  }
  canvas.drawPath(
    water,
    Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = size * 0.03
      ..strokeCap = StrokeCap.round,
  );

  // Bowsprit with a small jib sail.
  line(0.40, deckY - 0.02, 0.64, deckY - 0.14, 0.03);
  canvas.drawPath(
    Path()
      ..moveTo(p(0.42, deckY - 0.04).dx, p(0.42, deckY - 0.04).dy)
      ..lineTo(p(0.60, deckY - 0.12).dx, p(0.60, deckY - 0.12).dy)
      ..lineTo(p(0.40, deckY - 0.10).dx, p(0.40, deckY - 0.10).dy)
      ..close(),
    paint,
  );

  // One curved leaf-shaped sail per mast -- straight against the pole on
  // the trailing (stern-ward) side, bulging out on the leading side.
  void mast(double x, double top, {bool flag = false}) {
    line(x, top, x, deckY, 0.028);
    if (flag) {
      canvas.drawPath(
        Path()
          ..moveTo(p(x, top).dx, p(x, top).dy)
          ..lineTo(p(x - 0.1, top + 0.025).dx, p(x - 0.1, top + 0.025).dy)
          ..lineTo(p(x, top + 0.05).dx, p(x, top + 0.05).dy)
          ..close(),
        paint,
      );
    }
    final sailTop = top + 0.04;
    canvas.drawPath(
      Path()
        ..moveTo(p(x, sailTop).dx, p(x, sailTop).dy)
        ..quadraticBezierTo(
            p(x + 0.14, (sailTop + deckY) / 2).dx, p(x + 0.14, (sailTop + deckY) / 2).dy, p(x, deckY).dx, p(x, deckY).dy)
        ..lineTo(p(x, sailTop).dx, p(x, sailTop).dy)
        ..close(),
      paint,
    );
  }

  mast(0.20, -0.08); // bow-ward mast, shortest
  mast(0.0, -0.22); // middle mast
  mast(-0.22, -0.40, flag: true); // sternmost mast, tallest, flies the flag
}

class FrigateIcon extends StatelessWidget {
  final double size;
  final Color color;
  const FrigateIcon({super.key, this.size = 16, required this.color});

  @override
  Widget build(BuildContext context) => CustomPaint(
        size: Size.square(size),
        painter: _FrigatePainter(color),
      );
}

class _FrigatePainter extends CustomPainter {
  final Color color;
  _FrigatePainter(this.color);

  @override
  void paint(Canvas canvas, Size size) => paintFrigate(canvas, size.center(Offset.zero), size.width, color);

  @override
  bool shouldRepaint(_FrigatePainter old) => old.color != color;
}
