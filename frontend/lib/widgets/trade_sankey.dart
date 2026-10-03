import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../models.dart';
import 'chart_colors.dart';
import 'sankey_layout.dart';

/// Sankey of trade value through the visible nodes. Columns = shortest graph
/// distance to the final nodes (on the left). Node colour = your power share,
/// node height = value passing through, link width = value forwarded.
/// Collecting nodes get a green strip + "Collect" badge, steering nodes an
/// orange outline and an arrow.
class TradeSankey extends StatefulWidget {
  final TradeGraphData graph;
  final SimulateResponseData sim;
  final Set<String> visible;
  final String? homeId;
  final Map<String, NodeAllocationData> allocation;
  final String? selectedId;
  final ValueChanged<String> onSelect;

  const TradeSankey({
    super.key,
    required this.graph,
    required this.sim,
    required this.visible,
    required this.homeId,
    required this.allocation,
    required this.selectedId,
    required this.onSelect,
  });

  @override
  State<TradeSankey> createState() => _TradeSankeyState();
}

class _TradeSankeyState extends State<TradeSankey> with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl =
      AnimationController(vsync: this, duration: const Duration(milliseconds: 450));
  late final Animation<double> _t = CurvedAnimation(parent: _ctrl, curve: Curves.easeInOutCubic);

  SankeyLayout _from = SankeyLayout.empty;
  SankeyLayout _to = SankeyLayout.empty;
  Object? _key;
  Size? _size;

  Offset? _hover;

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  SankeyLayout get _current => lerpSankey(_from, _to, _t.value);

  void _relayout(Size size) {
    final key = (widget.sim, widget.homeId, widget.visible.length, Object.hashAllUnordered(widget.visible));
    final sizeChanged = _size != size;
    if (_key == key && !sizeChanged) return;
    final animate = _key != null && !sizeChanged && _to.nodes.isNotEmpty;
    final next = layoutSankey(
        graph: widget.graph, sim: widget.sim, visible: widget.visible, size: size, homeId: widget.homeId);
    _from = animate ? _current : next;
    _to = next;
    _key = key;
    _size = size;
    if (animate) {
      // Starting the controller during build would notify listeners mid-build.
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) _ctrl.forward(from: 0);
      });
    } else {
      _ctrl.value = 1;
    }
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(builder: (context, constraints) {
      final size = Size(constraints.maxWidth, constraints.maxHeight);
      _relayout(size);
      return MouseRegion(
        cursor: SystemMouseCursors.basic,
        onHover: (e) => setState(() => _hover = e.localPosition),
        onExit: (_) => setState(() => _hover = null),
        child: GestureDetector(
          behavior: HitTestBehavior.opaque,
          onTapUp: (d) {
            final n = _to.nodeAt(d.localPosition);
            if (n != null) widget.onSelect(n.id);
          },
          child: AnimatedBuilder(
            animation: _t,
            builder: (context, _) {
              final layout = _current;
              final hovered = _hover == null ? null : layout.nodeAt(_hover!);
              return Stack(
                children: [
                  Positioned.fill(
                    child: CustomPaint(
                      painter: _SankeyPainter(
                        layout: layout,
                        allocation: widget.allocation,
                        selectedId: widget.selectedId,
                        hoveredId: hovered?.id,
                        graph: widget.graph,
                      ),
                    ),
                  ),
                  if (layout.nodes.isEmpty)
                    const Center(
                        child: Text('No nodes to show.', style: TextStyle(color: ChartColors.inkMuted))),
                  if (hovered != null) _tooltip(hovered, size),
                ],
              );
            },
          ),
        ),
      );
    });
  }

  Widget _tooltip(SankeyNode n, Size size) {
    final d = n.data;
    final alloc = widget.allocation[n.id];
    final action = alloc == null ? 'none' : merchantActionToJson(alloc.merchantAction);
    const w = 190.0;
    final left = (_hover!.dx + 14 + w > size.width) ? _hover!.dx - 14 - w : _hover!.dx + 14;
    final top = math.min(_hover!.dy + 8, size.height - 120);
    return Positioned(
      left: left,
      top: math.max(top, 0),
      width: w,
      child: IgnorePointer(
        child: Material(
          elevation: 3,
          borderRadius: BorderRadius.circular(6),
          color: Colors.white,
          child: Padding(
            padding: const EdgeInsets.all(10),
            child: DefaultTextStyle(
              style: const TextStyle(fontSize: 12, color: ChartColors.inkSecondary),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(n.name,
                      style: const TextStyle(
                          fontSize: 13, fontWeight: FontWeight.w600, color: ChartColors.inkPrimary)),
                  const SizedBox(height: 4),
                  _row('Total value', d.totalValue.toStringAsFixed(2)),
                  _row('Your power', '${d.playerPower.toStringAsFixed(1)} / ${d.totalPower.toStringAsFixed(1)}'),
                  _row('Your share', '${(n.share * 100).toStringAsFixed(0)}%'),
                  _row('Merchant', action),
                  _row('Ducats / mo', d.playerIncome.toStringAsFixed(2)),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _row(String k, String v) => Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [Text(k), Text(v, style: const TextStyle(color: ChartColors.inkPrimary))],
      );
}

class _SankeyPainter extends CustomPainter {
  final SankeyLayout layout;
  final Map<String, NodeAllocationData> allocation;
  final String? selectedId;
  final String? hoveredId;
  final TradeGraphData graph;

  _SankeyPainter({
    required this.layout,
    required this.allocation,
    required this.selectedId,
    required this.hoveredId,
    required this.graph,
  });

  MerchantAction _action(String id) => allocation[id]?.merchantAction ?? MerchantAction.none;

  @override
  void paint(Canvas canvas, Size size) {
    final nodes = {for (final n in layout.nodes) n.id: n};

    // Links first, under the nodes.
    for (final l in layout.links) {
      final steered = _action(l.sourceId) == MerchantAction.steer &&
          allocation[l.sourceId]?.steerTarget == l.targetId;
      final dim = hoveredId != null && l.sourceId != hoveredId && l.targetId != hoveredId;
      final base = steered ? ChartColors.steer : ChartColors.share(nodes[l.sourceId]?.share ?? 0);
      // Links that don't lead toward the final nodes are drawn fainter.
      final alpha = (steered ? 0.55 : l.backflow ? 0.2 : 0.35) * l.opacity * (dim ? 0.25 : 1);
      _ribbon(canvas, l, base.withValues(alpha: alpha));
    }

    for (final n in layout.nodes) {
      final r = n.rect;
      final fill = ChartColors.share(n.share);
      final paint = Paint()..color = fill.withValues(alpha: n.opacity);
      final rr = RRect.fromRectAndRadius(r, const Radius.circular(3));
      canvas.drawRRect(rr, paint);

      // "You collect here" strip, anchored to the bottom of the node.
      if (n.collectedHeight > 0.5) {
        final strip = Rect.fromLTWH(r.left, r.bottom - n.collectedHeight, r.width, n.collectedHeight);
        canvas.drawRRect(RRect.fromRectAndRadius(strip, const Radius.circular(3)),
            Paint()..color = ChartColors.collect.withValues(alpha: n.opacity));
      }

      final action = _action(n.id);
      final selected = n.id == selectedId;
      if (action == MerchantAction.steer || selected || n.id == hoveredId) {
        canvas.drawRRect(
          rr.inflate(selected ? 2 : 1),
          Paint()
            ..style = PaintingStyle.stroke
            ..strokeWidth = selected ? 2 : 1.5
            ..color = (action == MerchantAction.steer ? ChartColors.steer : ChartColors.inkPrimary)
                .withValues(alpha: n.opacity),
        );
      }

      // Label to the right of the node (below the badge), in ink -- never the series colour.
      final badge = switch (action) {
        MerchantAction.collect => 'Collect',
        MerchantAction.steer => 'Steer →',
        MerchantAction.none => n.data.playerCollects && n.data.playerIncome > 0 ? 'Home' : null,
      };
      final labelX = r.right + 5;
      final labelWidth = math.max(layout.colStep - kNodeWidth - 10, 48.0);
      final top = r.center.dy - (badge != null ? 12 : 6);
      _text(canvas, n.name, Offset(labelX, top),
          size: 11,
          weight: selected ? FontWeight.w700 : FontWeight.w500,
          color: ChartColors.inkPrimary.withValues(alpha: n.opacity),
          maxWidth: labelWidth);
      if (badge != null) {
        _text(canvas, '$badge${n.data.playerIncome > 0 ? '  ${n.data.playerIncome.toStringAsFixed(1)}' : ''}',
            Offset(labelX, top + 13),
            size: 10,
            weight: FontWeight.w600,
            color: (action == MerchantAction.steer ? ChartColors.steer : const Color(0xFF0F7A55))
                .withValues(alpha: n.opacity),
            maxWidth: labelWidth);
      }
    }
  }

  void _ribbon(Canvas canvas, SankeyLink l, Color color) {
    if (l.bulge != 0) {
      // Same-column link: a C-shaped arc. Stroke it (a filled band with vertical
      // offsets would collapse to nothing where the arc runs vertically).
      final path = Path()
        ..moveTo(l.start.dx, l.start.dy)
        ..cubicTo(l.start.dx + l.bulge, l.start.dy, l.end.dx + l.bulge, l.end.dy, l.end.dx, l.end.dy);
      canvas.drawPath(
          path,
          Paint()
            ..style = PaintingStyle.stroke
            ..strokeWidth = l.width
            ..color = color);
      return;
    }
    final dx = (l.end.dx - l.start.dx) * 0.5;
    final path = Path()
      ..moveTo(l.start.dx, l.start.dy - l.width / 2)
      ..cubicTo(l.start.dx + dx, l.start.dy - l.width / 2, l.end.dx - dx, l.end.dy - l.width / 2,
          l.end.dx, l.end.dy - l.width / 2)
      ..lineTo(l.end.dx, l.end.dy + l.width / 2)
      ..cubicTo(l.end.dx - dx, l.end.dy + l.width / 2, l.start.dx + dx, l.start.dy + l.width / 2,
          l.start.dx, l.start.dy + l.width / 2)
      ..close();
    canvas.drawPath(path, Paint()..color = color);
  }

  /// Text with a surface-coloured halo so labels stay readable over ribbons.
  void _text(Canvas canvas, String s, Offset at,
      {required double size, FontWeight weight = FontWeight.w400, required Color color, double maxWidth = 100}) {
    for (final halo in [true, false]) {
      final style = TextStyle(
        fontSize: size,
        fontWeight: weight,
        color: halo ? null : color,
        foreground: halo
            ? (Paint()
              ..style = PaintingStyle.stroke
              ..strokeWidth = 3
              ..strokeJoin = StrokeJoin.round
              ..color = ChartColors.surface.withValues(alpha: 0.9 * color.a))
            : null,
      );
      final tp = TextPainter(
        text: TextSpan(text: s, style: style),
        textDirection: TextDirection.ltr,
        maxLines: 1,
        ellipsis: '…',
      )..layout(maxWidth: maxWidth);
      tp.paint(canvas, at);
    }
  }

  @override
  bool shouldRepaint(_SankeyPainter old) => true;
}
