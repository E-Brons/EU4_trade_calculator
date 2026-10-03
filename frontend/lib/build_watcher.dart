/// Detects a stale browser tab. The server stamps the build id of the bundle it
/// is serving into `index.html` (`<meta name="build-id">`); this polls
/// `/api/build` and compares. A mismatch means the page in this tab was loaded
/// before a newer build was made. `sourcesNewer` additionally flags that the
/// Flutter sources were edited after the last build (the server is then
/// serving an app that doesn't include those edits).
library;

import 'dart:async';
import 'dart:js_interop';

import 'package:flutter/foundation.dart';
import 'package:web/web.dart' as web;

import 'api_client.dart';

class BuildWatcher extends ChangeNotifier {
  final ApiClient api;
  BuildWatcher(this.api);

  /// Build id baked into the page this tab loaded; null under `flutter run`.
  final String? runningId = web.document
      .querySelector('meta[name="build-id"]')
      ?.getAttribute('content');

  String? latestId;
  String? builtAt;
  bool sourcesNewer = false;
  bool serverReachable = true;

  Timer? _timer;

  bool get outdated => runningId != null && latestId != null && runningId != latestId;

  void start() {
    check();
    _timer = Timer.periodic(const Duration(seconds: 8), (_) => check());
    // Come back to the tab -> check immediately, don't wait for the next tick.
    // (Block bodies: a `toJS` callback must return void, not the check() Future.)
    void onWake(web.Event _) {
      check();
    }

    web.window.addEventListener('focus', onWake.toJS);
    web.document.addEventListener('visibilitychange', onWake.toJS);
  }

  Future<void> check() async {
    try {
      final info = await api.getBuildInfo();
      final changed = latestId != info.buildId ||
          sourcesNewer != info.sourcesNewerThanBuild ||
          builtAt != info.builtAt ||
          !serverReachable;
      latestId = info.buildId;
      builtAt = info.builtAt;
      sourcesNewer = info.sourcesNewerThanBuild;
      serverReachable = true;
      if (changed) notifyListeners();
    } catch (_) {
      if (serverReachable) {
        serverReachable = false;
        notifyListeners();
      }
    }
  }

  void reload() => web.window.location.reload();

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }
}
