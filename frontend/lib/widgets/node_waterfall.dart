import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../models.dart';
import 'chart_colors.dart';

class _Seg {
  final String label;
  final double value;
  final Color color;
  const _Seg(this.label, this.value, this.color);
}

class _Bar {
  final String label;
  final List<_Seg> segs;

  /// Same bar under the Optimal preset, drawn as an outline for comparison.
  final double? ghost;

  /// Outline-only bar (value deferred downstream, not income).
  final bool deferred;
  const _Bar(this.label, this.segs, {this.ghost, this.deferred = false});

  double get total => segs.fold(0, (a, s) => a + s.value);
}

/// Waterfall-style breakdown for one node, following
/// docs/imported/canton_node_waterfall_mockup.html: local value, incoming
/// value (stacked by upstream node), total, how much of it your power share
/// claims, and the outcome (collected ducats, or value deferred when steering).
class NodeWaterfall extends StatefulWidget {
  final String nodeId;
  final SimulateResponseData sim;

  /// Optimal-preset result for the ghost comparison; null when Optimal is
  /// already the active preset.
  final SimulateResponseData? ghostSim;
  final String presetLabel;

  const NodeWaterfall({
    super.key,
    required this.nodeId,
    required this.sim,
    required this.ghostSim,
    required this.presetLabel,
  });

  @override
  State<NodeWaterfall> createState() => _NodeWaterfallState();
}

class _NodeWaterfallState extends State<NodeWaterfall> {
  Offset? _hover;

  List<_Bar> _bars() {
    final b = widget.sim.nodes[widget.nodeId];
    if (b == null) return const [];
    final g = widget.ghostSim?.nodes[widget.nodeId];

    // Upstream contributors, biggest first; the long tail folds into "Other upstream".
    final contrib = <MapEntry<String, double>>[];
    for (final n in widget.sim.nodes.values) {
      final v = n.linkValues[widget.nodeId] ?? 0;
      if (v > 0) contrib.add(MapEntry(n.displayName, v));
    }
    contrib.sort((a, c) => c.value.compareTo(a.value));
    const tints = [Color(0xFF86B6EF), Color(0xFF9EC5F4), Color(0xFFB7D3F6), Color(0xFFCDE2FB)];
    final incomingSegs = <_Seg>[];
    var rest = 0.0;
    for (var i = 0; i < contrib.length; i++) {
      if (i < 3) {
        incomingSegs.add(_Seg(contrib[i].key, contrib[i].value, tints[i]));
      } else {
        rest += contrib[i].value;
      }
    }
    if (rest > 0) incomingSegs.add(_Seg('Other upstream', rest, tints[3]));
    final incoming = math.max(b.totalValue - b.localValue, 0.0);
    if (incomingSegs.isEmpty && incoming > 0) incomingSegs.add(_Seg('Incoming', incoming, tints[0]));

    final share = b.totalPower > 0 ? b.playerPower / b.totalPower : 0.0;
    final gShare = (g != null && g.totalPower > 0) ? g.playerPower / g.totalPower : null;

    final collects = b.playerCollects;
    final outcome = collects
        ? _Bar('Your ducats', [_Seg('Collected', b.playerIncome, ChartColors.collect)], ghost: g?.playerIncome)
        : _Bar('Deferred downstream', [_Seg('Steered / passed on', b.forwardedValue, ChartColors.steer.withValues(alpha: 0.35))],
            ghost: g?.forwardedValue, deferred: true);

    return [
      _Bar('Local value', [_Seg('Local value', b.localValue, const Color(0xFF2A78D6))], ghost: g?.localValue),
      _Bar('Incoming', incomingSegs, ghost: g == null ? null : math.max(g.totalValue - g.localValue, 0.0)),
      _Bar('Total value', [_Seg('Total value', b.totalValue, const Color(0xFF184F95))], ghost: g?.totalValue),
      _Bar('Power split', [
        _Seg('Your share (${(share * 100).toStringAsFixed(0)}%)', b.totalValue * share, const Color(0xFF6DA7EC)),
        _Seg('Others', b.totalValue * (1 - share), ChartColors.other),
      ], ghost: gShare == null ? null : g!.totalValue * gShare),
      outcome,
    ];
  }

  @override
  Widget build(BuildContext context) {
    final bars = _bars();
    final node = widget.sim.nodes[widget.nodeId];
    return Container(
      color: ChartColors.surface,
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(node?.displayName ?? 'Select a node',
                  style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: ChartColors.inkPrimary)),
              const SizedBox(width: 8),
              Text('· ${widget.presetLabel}', style: const TextStyle(fontSize: 12, color: ChartColors.inkMuted)),
              const Spacer(),
              if (widget.ghostSim != null) ...[
                Container(
                  width: 14,
                  height: 10,
                  decoration: BoxDecoration(border: Border.all(color: ChartColors.inkSecondary, width: 1.5)),
                ),
                const SizedBox(width: 4),
                const Text('Optimal', style: TextStyle(fontSize: 11, color: ChartColors.inkSecondary)),
              ],
            ],
          ),
          const SizedBox(height: 4),
          Expanded(
            child: bars.isEmpty
                ? const Center(child: Text('Click a node in the diagram.', style: TextStyle(color: ChartColors.inkMuted)))
                : LayoutBuilder(builder: (context, c) {
                    final size = Size(c.maxWidth, c.maxHeight);
                    final geo = _Geometry(bars, size);
                    final hit = _hover == null ? null : geo.hit(_hover!);
                    return MouseRegion(
                      onHover: (e) => setState(() => _hover = e.localPosition),
                      onExit: (_) => setState(() => _hover = null),
                      child: Stack(children: [
                        Positioned.fill(child: CustomPaint(painter: _WaterfallPainter(geo))),
                        if (hit != null)
                          Positioned(
                            left: math.min(_hover!.dx + 12, size.width - 170),
                            top: math.max(_hover!.dy - 36, 0),
                            child: IgnorePointer(
                              child: Material(
                                elevation: 3,
                                borderRadius: BorderRadius.circular(6),
                                color: Colors.white,
                                child: Padding(
                                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                                  child: Text('${hit.label}: ${hit.value.toStringAsFixed(2)} ducats',
                                      style: const TextStyle(fontSize: 12, color: ChartColors.inkPrimary)),
                                ),
                              ),
                            ),
                          ),
                      ]),
                    );
                  }),
          ),
        ],
      ),
    );
  }
}

class _Rect {
  final Rect rect;
  final _Seg seg;
  _Rect(this.rect, this.seg);
}

class _Geometry {
  static const left = 40.0, bottom = 34.0, top = 8.0, right = 4.0;
  final List<_Bar> bars;
  final Size size;
  late final double maxValue;
  late final double slot;
  late final double barWidth;
  final List<_Rect> segRects = [];
  final List<Rect?> ghostRects = [];

  _Geometry(this.bars, this.size) {
    var m = 0.0;
    for (final b in bars) {
      m = math.max(m, math.max(b.total, b.ghost ?? 0));
    }
    maxValue = _niceMax(m <= 0 ? 1 : m);
    final w = size.width - left - right;
    slot = w / bars.length;
    barWidth = math.min(slot * 0.5, 64);
    for (var i = 0; i < bars.length; i++) {
      final x = left + slot * i + (slot - barWidth) / 2;
      var y = size.height - bottom;
      for (final s in bars[i].segs) {
        final h = s.value / maxValue * plotHeight;
        segRects.add(_Rect(Rect.fromLTWH(x, y - h, barWidth, h), s));
        y -= h;
      }
      final g = bars[i].ghost;
      ghostRects.add(g == null ? null : Rect.fromLTWH(x - 3, size.height - bottom - g / maxValue * plotHeight, barWidth + 6, g / maxValue * plotHeight));
    }
  }

  double get plotHeight => size.height - bottom - top;

  double yOf(double v) => size.height - bottom - v / maxValue * plotHeight;

  _Seg? hit(Offset p) {
    for (final r in segRects) {
      if (r.rect.inflate(3).contains(p)) return r.seg;
    }
    return null;
  }

  static double _niceMax(double v) {
    final exp = math.pow(10, (math.log(v) / math.ln10).floor()).toDouble();
    final f = v / exp;
    final nice = f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10;
    return nice * exp;
  }
}

class _WaterfallPainter extends CustomPainter {
  final _Geometry g;
  _WaterfallPainter(this.g);

  @override
  void paint(Canvas canvas, Size size) {
    // Recessive grid + y labels (ducats).
    final gridPaint = Paint()
      ..color = ChartColors.grid
      ..strokeWidth = 1;
    for (var i = 0; i <= 2; i++) {
      final v = g.maxValue * i / 2;
      final y = g.yOf(v);
      canvas.drawLine(Offset(_Geometry.left, y), Offset(size.width - _Geometry.right, y), gridPaint);
      _text(canvas, v.toStringAsFixed(v < 10 && v != v.roundToDouble() ? 1 : 0), Offset(0, y - 6),
          size: 10, color: ChartColors.inkMuted, width: _Geometry.left - 6, align: TextAlign.right);
    }
    _text(canvas, 'ducats', const Offset(0, 0), size: 10, color: ChartColors.inkMuted, width: _Geometry.left);

    for (final r in g.segRects) {
      final deferred = g.bars.any((b) => b.deferred && b.segs.contains(r.seg));
      // 2px surface gap between stacked segments; 4px rounding on the data end.
      final rect = Rect.fromLTRB(r.rect.left, r.rect.top, r.rect.right, r.rect.bottom - 1);
      final rr = RRect.fromRectAndCorners(rect, topLeft: const Radius.circular(4), topRight: const Radius.circular(4));
      if (rect.height < 0.5) continue;
      canvas.drawRRect(rr, Paint()..color = r.seg.color);
      if (deferred) {
        canvas.drawRRect(
            rr,
            Paint()
              ..style = PaintingStyle.stroke
              ..strokeWidth = 1.5
              ..color = ChartColors.steer);
      }
    }

    final ghostPaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5
      ..color = ChartColors.inkSecondary;
    for (final r in g.ghostRects) {
      if (r != null) canvas.drawRect(r, ghostPaint);
    }

    // Value labels over bars + category labels below.
    for (var i = 0; i < g.bars.length; i++) {
      final b = g.bars[i];
      final cx = _Geometry.left + g.slot * i + g.slot / 2;
      final yTop = g.yOf(math.max(b.total, b.ghost ?? 0));
      _text(canvas, b.total.toStringAsFixed(1), Offset(cx - 30, yTop - 15),
          size: 11, color: ChartColors.inkPrimary, width: 60, align: TextAlign.center, weight: FontWeight.w600);
      _text(canvas, b.label, Offset(cx - g.slot / 2 + 2, size.height - _Geometry.bottom + 6),
          size: 11, color: ChartColors.inkSecondary, width: g.slot - 4, align: TextAlign.center);
    }
  }

  void _text(Canvas canvas, String s, Offset at,
      {required double size, required Color color, required double width, TextAlign align = TextAlign.left, FontWeight weight = FontWeight.w400}) {
    final tp = TextPainter(
      text: TextSpan(text: s, style: TextStyle(fontSize: size, color: color, fontWeight: weight)),
      textDirection: TextDirection.ltr,
      textAlign: align,
      maxLines: 2,
      ellipsis: '…',
    )..layout(minWidth: width, maxWidth: width);
    tp.paint(canvas, at);
  }

  @override
  bool shouldRepaint(_WaterfallPainter old) => true;
}
