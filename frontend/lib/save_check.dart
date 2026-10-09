/// How far the loaded save can be trusted (backend `POST /api/verify-save`).
///
/// The game computes trade once a month, on the 1st. A save from any other day pairs today's merchant and ship
/// placements with the numbers of the last 1st, so results may be slightly off; a save from before the game's first 1st
/// holds no computed trade at all. A save from the 1st with nothing of the player's on the way should be reproduced
/// exactly: when it is not, the player can store it for future improvement of the calculation.
library;

import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:provider/provider.dart';

import 'api_client.dart';

class SaveQualityData {
  final String timing; // tick_day | mid_month | pre_first_tick | unknown
  final int ownMerchantsInTransit;
  final int ownFleetsInTransit;
  final String gameVersion;
  final bool versionSupported;
  final bool clean;

  SaveQualityData.fromJson(Map<String, dynamic> j)
      : timing = j['timing'] as String,
        ownMerchantsInTransit = j['own_merchants_in_transit'] as int,
        ownFleetsInTransit = j['own_fleets_in_transit'] as int,
        gameVersion = j['game_version'] as String,
        versionSupported = j['version_supported'] as bool,
        clean = j['clean'] as bool;
}

class SaveCheck extends ChangeNotifier {
  final ApiClient api;
  SaveCheck(this.api);

  Uint8List? _bytes;
  String? _filename;
  bool checking = false;
  SaveQualityData? quality;
  String? verificationStatus; // verified | mismatch
  String? error;
  bool storing = false;
  String? storedCaseId;
  String? storeMessage;

  Future<Map<String, dynamic>> _post(bool store) async {
    final request = http.MultipartRequest('POST', Uri.parse('${api.baseUrl}/api/verify-save'))
      ..files.add(http.MultipartFile.fromBytes('file', _bytes!, filename: _filename))
      ..fields['store'] = store ? 'true' : 'false';
    final r = await http.Response.fromStream(await request.send());
    if (r.statusCode >= 400) throw ApiException(r.statusCode, r.body);
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  /// Check a freshly imported save (runs in the background; the banner appears when done).
  Future<void> check(Uint8List bytes, String filename) async {
    clear(notify: false);
    _bytes = bytes;
    _filename = filename;
    checking = true;
    notifyListeners();
    try {
      applyResult(await _post(false));
    } catch (e) {
      error = e is ApiException ? e.message : e.toString();
    } finally {
      checking = false;
      notifyListeners();
    }
  }

  void applyResult(Map<String, dynamic> body) {
    quality = SaveQualityData.fromJson(body['quality'] as Map<String, dynamic>);
    verificationStatus = (body['verification'] as Map<String, dynamic>)['status'] as String;
    storedCaseId = body['stored_case'] as String?;
    notifyListeners();
  }

  /// "Store this save for future enhancement": the backend keeps it in its dataset's `reports` series.
  Future<void> store() async {
    if (_bytes == null) return;
    storing = true;
    notifyListeners();
    try {
      final body = await _post(true);
      storedCaseId = body['stored_case'] as String?;
      storeMessage = body['message'] as String?;
    } catch (e) {
      storeMessage = 'Could not store the save: ${e is ApiException ? e.message : e}';
    } finally {
      storing = false;
      notifyListeners();
    }
  }

  void clear({bool notify = true}) {
    _bytes = null;
    _filename = null;
    checking = false;
    quality = null;
    verificationStatus = null;
    error = null;
    storing = false;
    storedCaseId = null;
    storeMessage = null;
    if (notify) notifyListeners();
  }

  /// The warning to show, or null when the save is a fair test and matches (or nothing is loaded).
  String? get warning {
    final q = quality;
    if (q == null) return null;
    if (!q.versionSupported) {
      return 'This save is from game version ${q.gameVersion}; the calculation is built for another version, so results may be off.';
    }
    if (q.timing == 'pre_first_tick') {
      return 'This save is from before the game\'s first 1st of the month: the game has not computed trade yet, '
          'so values may be off. Play to the next 1st and save again.';
    }
    if (q.timing == 'mid_month' || q.timing == 'unknown') {
      return 'This save is not from the 1st of a month. The game computes trade only on the 1st, so changes made since '
          'then (merchants, ships) are not in the save\'s numbers yet: values may be slightly off. For exact numbers, '
          'save on the 1st after your merchants and fleets have arrived.';
    }
    if (q.ownMerchantsInTransit > 0 || q.ownFleetsInTransit > 0) {
      return 'Some of your merchants (${q.ownMerchantsInTransit}) or fleets (${q.ownFleetsInTransit}) are still on their '
          'way, so values may be slightly off. Save on the next 1st after they have arrived.';
    }
    if (verificationStatus == 'mismatch') {
      return 'This save should be reproduced exactly (1st of the month, nothing on the way), but our calculation does '
          'not match it yet.';
    }
    return null;
  }

  /// Offer storing only for a save that should match but does not.
  bool get canStore => quality?.clean == true && verificationStatus == 'mismatch' && storedCaseId == null;
}

class SaveCheckBanner extends StatelessWidget {
  const SaveCheckBanner({super.key});

  @override
  Widget build(BuildContext context) {
    final check = context.watch<SaveCheck>();
    final text = check.warning;
    if (text == null && check.storeMessage == null) return const SizedBox.shrink();
    return Material(
      color: const Color(0xFFFFF1CC),
      child: SafeArea(
        bottom: false,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: DefaultTextStyle.merge(
            style: const TextStyle(fontSize: 13, color: Color(0xFF3B2F00)),
            child: Row(children: [
              const Icon(Icons.warning_amber_rounded, size: 18, color: Color(0xFF8A6100)),
              const SizedBox(width: 8),
              Expanded(child: Text(check.storeMessage ?? text!)),
              if (check.canStore) ...[
                const SizedBox(width: 12),
                FilledButton(
                  onPressed: check.storing ? null : check.store,
                  child: Text(check.storing ? 'Storing…' : 'Store this save for future enhancement'),
                ),
              ],
            ]),
          ),
        ),
      ),
    );
  }
}
