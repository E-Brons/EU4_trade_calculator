/// Thin HTTP client for the FastAPI backend. In dev, the backend runs on
/// :8000 (see backend/README or `uvicorn app.main:app --reload --port 8000`)
/// while Flutter serves the UI separately (`flutter run -d chrome`); in
/// prod the backend serves the built frontend itself, so relative URLs
/// resolve to the same origin.
library;

import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import 'package:web/web.dart' as web;

import 'models.dart';

class ApiException implements Exception {
  final int statusCode;
  final String message;
  ApiException(this.statusCode, this.message);

  @override
  String toString() => 'ApiException($statusCode): $message';
}

class ApiClient {
  final String baseUrl;

  ApiClient({String? baseUrl}) : baseUrl = baseUrl ?? _defaultBaseUrl();

  /// When served from the same FastAPI app there's no port to guess; when
  /// running via `flutter run -d chrome` against a separately-started
  /// backend, default to localhost:8000.
  static String _defaultBaseUrl() {
    final origin = web.window.location.origin;
    final port = web.window.location.port;
    if (port == '8000') return origin;
    return 'http://localhost:8000';
  }

  Uri _uri(String path) => Uri.parse('$baseUrl$path');

  Map<String, dynamic> _decode(http.Response r) {
    if (r.statusCode >= 400) {
      String message = r.body;
      try {
        final decoded = jsonDecode(r.body);
        message = decoded['detail']?.toString() ?? r.body;
      } catch (_) {}
      throw ApiException(r.statusCode, message);
    }
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<TradeGraphData> getTradeNodes() async {
    final r = await http.get(_uri('/api/tradenodes'));
    return TradeGraphData.fromJson(_decode(r));
  }

  Future<BuildInfoData> getBuildInfo() async {
    final r = await http.get(_uri('/api/build'), headers: {'Cache-Control': 'no-cache'});
    return BuildInfoData.fromJson(_decode(r));
  }

  Future<SimulateResponseData> simulate({
    required Map<String, NodeStateData> nodeStates,
    required Map<String, NodeAllocationData> allocation,
    required ParamsData params,
  }) async {
    final body = jsonEncode({
      'node_states': nodeStates.map((k, v) => MapEntry(k, v.toJson())),
      'allocation': allocation.map((k, v) => MapEntry(k, v.toJson())),
      'params': params.toJson(),
    });
    final r = await http.post(_uri('/api/simulate'),
        headers: {'Content-Type': 'application/json'}, body: body);
    return SimulateResponseData.fromJson(_decode(r));
  }

  Future<OptimizeResponseData> optimize({
    required Map<String, NodeStateData> nodeStates,
    required ParamsData params,
    required String homeNode,
    required List<String> candidateNodes,
    required int maxMerchants,
    required int maxLightShips,
    Map<String, NodeAllocationData>? currentAllocation,
    int randomSeed = 0,
    int maxRestarts = 3,
  }) async {
    final body = jsonEncode({
      'node_states': nodeStates.map((k, v) => MapEntry(k, v.toJson())),
      'params': params.toJson(),
      'home_node': homeNode,
      'candidate_nodes': candidateNodes,
      'max_merchants': maxMerchants,
      'max_light_ships': maxLightShips,
      'current_allocation': (currentAllocation ?? {}).map((k, v) => MapEntry(k, v.toJson())),
      'random_seed': randomSeed,
      'max_restarts': maxRestarts,
    });
    final r = await http.post(_uri('/api/optimize'),
        headers: {'Content-Type': 'application/json'}, body: body);
    return OptimizeResponseData.fromJson(_decode(r));
  }

  /// Uploads a save picked via `file_picker` (bytes are already in memory
  /// on web -- see FilePicker.platform.pickFiles(withData: true)).
  Future<ImportSaveResponseData> importSave(Uint8List bytes, String filename) async {
    final request = http.MultipartRequest('POST', _uri('/api/import-save'));
    request.files.add(http.MultipartFile.fromBytes('file', bytes, filename: filename));
    final streamed = await request.send();
    final r = await http.Response.fromStream(streamed);
    return ImportSaveResponseData.fromJson(_decode(r));
  }
}
