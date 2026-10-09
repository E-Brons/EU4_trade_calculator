/// Pan / zoom camera over the world map with cinematic fly-to animation.
library;

import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/scheduler.dart';
import 'package:flutter/widgets.dart';

class MapCamera extends ChangeNotifier {
  /// Map-space point shown at the centre of the *usable* viewport.
  Offset center;

  /// Screen pixels per map pixel.
  double zoom;

  Size viewSize = Size.zero;

  /// Parts of the viewport covered by floating panels; "fit" targets centre in
  /// what is left so nothing important hides behind a panel.
  EdgeInsets insets = EdgeInsets.zero;

  Rect worldBounds;
  double maxZoom;

  MapCamera({required this.worldBounds, this.center = Offset.zero, this.zoom = 0.3, this.maxZoom = 7});

  Ticker? _ticker;
  _Flight? _flight;

  bool get flying => _flight != null;

  Offset get _usableCenter => Offset(
        insets.left + (viewSize.width - insets.horizontal) / 2,
        insets.top + (viewSize.height - insets.vertical) / 2,
      );

  double get minZoom {
    if (viewSize.isEmpty) return 0.05;
    // Never zoom out past showing the whole world once.
    return math.min(viewSize.width / worldBounds.width, viewSize.height / worldBounds.height) * 0.98;
  }

  Offset mapToScreen(Offset p) => (p - center) * zoom + _usableCenter;
  Offset screenToMap(Offset s) => (s - _usableCenter) / zoom + center;

  Rect get visibleMapRect => Rect.fromPoints(screenToMap(Offset.zero), screenToMap(Offset(viewSize.width, viewSize.height)));

  void attach(TickerProvider vsync) {
    _ticker ??= vsync.createTicker(_onTick);
  }

  void setViewport(Size size, EdgeInsets newInsets) {
    if (size == viewSize && newInsets == insets) return;
    final first = viewSize.isEmpty;
    final oldCenter = _usableCenter;
    viewSize = size;
    insets = newInsets;
    if (first) {
      zoom = zoom.clamp(minZoom, maxZoom);
    } else if (_flight == null) {
      // Panels opening/closing must not make the map jump: keep what is on
      // screen where it is by moving the camera centre with the usable centre.
      center += (_usableCenter - oldCenter) / zoom;
    }
    _clamp();
    if (!first) notifyListeners();
  }

  void _clamp() {
    zoom = zoom.clamp(minZoom, maxZoom);
    final pad = 0.15;
    center = Offset(
      center.dx.clamp(worldBounds.left - worldBounds.width * pad, worldBounds.right + worldBounds.width * pad),
      center.dy.clamp(worldBounds.top - worldBounds.height * pad, worldBounds.bottom + worldBounds.height * pad),
    );
  }

  // ------------------------------------------------------------ user input

  void panBy(Offset screenDelta) {
    cancelFlight();
    center -= screenDelta / zoom;
    _clamp();
    notifyListeners();
  }

  /// Zoom by [factor] keeping the map point under [focal] (screen coords) fixed.
  void zoomAt(Offset focal, double factor) {
    cancelFlight();
    final before = screenToMap(focal);
    zoom = (zoom * factor).clamp(minZoom, maxZoom);
    final after = screenToMap(focal);
    center += before - after;
    _clamp();
    notifyListeners();
  }

  // ------------------------------------------------------------ cinematic

  /// Camera state that frames [rect] (map space) inside the usable viewport.
  ({Offset center, double zoom}) framing(Rect rect, {double padding = 0.12, double? maxZoomOverride}) {
    final usableW = math.max(viewSize.width - insets.horizontal, 50);
    final usableH = math.max(viewSize.height - insets.vertical, 50);
    final w = math.max(rect.width, 8.0);
    final h = math.max(rect.height, 8.0);
    var z = math.min(usableW * (1 - padding * 2) / w, usableH * (1 - padding * 2) / h);
    z = z.clamp(minZoom, max740(maxZoomOverride));
    return (center: rect.center, zoom: z);
  }

  double max740(double? o) => o == null ? maxZoom : math.min(o, maxZoom);

  /// Smoothly frame [rect]. Long hops pull back first and dive in again so the
  /// player keeps a sense of where they are going.
  Future<void> flyToRect(Rect rect,
      {Duration? duration, double padding = 0.12, double? maxZoomOverride}) {
    final f = framing(rect, padding: padding, maxZoomOverride: maxZoomOverride);
    return flyTo(f.center, f.zoom, duration: duration);
  }

  Future<void> flyTo(Offset toCenter, double toZoom, {Duration? duration}) {
    cancelFlight();
    if (viewSize.isEmpty) {
      center = toCenter;
      zoom = toZoom;
      notifyListeners();
      return Future.value();
    }
    toZoom = toZoom.clamp(minZoom, maxZoom);
    final dist = (toCenter - center).distance * math.max(zoom, toZoom);
    final span = math.max(viewSize.width, viewSize.height);
    final hop = (dist / span).clamp(0.0, 3.0);
    final zoomRatio = (math.log(toZoom / zoom)).abs();
    final ms = duration?.inMilliseconds ?? (550 + 380 * hop + 160 * zoomRatio).clamp(500, 1700).round();
    // Pull back (reduce log-zoom) proportionally to the hop length.
    final bump = hop > 0.6 ? math.min(hop * 0.35, 0.9) : 0.0;
    final flight = _Flight(
      fromCenter: center,
      toCenter: toCenter,
      fromLogZoom: math.log(zoom),
      toLogZoom: math.log(toZoom),
      bump: bump,
      duration: Duration(milliseconds: ms),
    );
    _flight = flight;
    _ticker!.stop();
    _ticker!.start();
    return flight.done.future;
  }

  void jumpTo(Offset toCenter, double toZoom) {
    cancelFlight();
    center = toCenter;
    zoom = toZoom;
    _clamp();
    notifyListeners();
  }

  void cancelFlight() {
    final f = _flight;
    if (f == null) return;
    _flight = null;
    _ticker?.stop();
    if (!f.done.isCompleted) f.done.complete();
  }

  void _onTick(Duration elapsed) {
    final f = _flight;
    if (f == null) return;
    final raw = (elapsed.inMicroseconds / f.duration.inMicroseconds).clamp(0.0, 1.0);
    final t = Curves.easeInOutCubic.transform(raw);
    center = Offset.lerp(f.fromCenter, f.toCenter, t)!;
    final logZ = f.fromLogZoom + (f.toLogZoom - f.fromLogZoom) * t - f.bump * math.sin(math.pi * t);
    zoom = math.exp(logZ).clamp(minZoom, maxZoom);
    notifyListeners();
    if (raw >= 1) {
      _flight = null;
      _ticker!.stop();
      f.done.complete();
    }
  }

  @override
  void dispose() {
    cancelFlight();
    _ticker?.dispose();
    super.dispose();
  }
}

class _Flight {
  final Offset fromCenter;
  final Offset toCenter;
  final double fromLogZoom;
  final double toLogZoom;
  final double bump;
  final Duration duration;
  final Completer<void> done = Completer<void>();

  _Flight({
    required this.fromCenter,
    required this.toCenter,
    required this.fromLogZoom,
    required this.toLogZoom,
    required this.bump,
    required this.duration,
  });
}
