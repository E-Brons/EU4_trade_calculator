/// Plain-JSON data models mirroring backend/app/schemas.py. Kept as simple
/// mutable classes (not immutable/freezed) since the setup screen edits
/// these fields directly through form controls.
library;

enum MerchantAction { none, collect, steer }

MerchantAction merchantActionFromJson(String s) {
  switch (s) {
    case 'collect':
      return MerchantAction.collect;
    case 'steer':
      return MerchantAction.steer;
    default:
      return MerchantAction.none;
  }
}

String merchantActionToJson(MerchantAction a) {
  switch (a) {
    case MerchantAction.collect:
      return 'collect';
    case MerchantAction.steer:
      return 'steer';
    case MerchantAction.none:
      return 'none';
  }
}

class TradeNode {
  final String nodeId;
  final String displayName;
  final bool inland;
  final List<String> outgoing;

  TradeNode({
    required this.nodeId,
    required this.displayName,
    required this.inland,
    required this.outgoing,
  });

  factory TradeNode.fromJson(Map<String, dynamic> j) => TradeNode(
        nodeId: j['node_id'],
        displayName: j['display_name'],
        inland: j['inland'],
        outgoing: List<String>.from(j['outgoing']),
      );
}

class TradeGraphData {
  final String gameVersion;
  final List<String> endNodes;
  final List<TradeNode> nodes;

  TradeGraphData({required this.gameVersion, required this.endNodes, required this.nodes});

  factory TradeGraphData.fromJson(Map<String, dynamic> j) => TradeGraphData(
        gameVersion: j['game_version'],
        endNodes: List<String>.from(j['end_nodes']),
        nodes: (j['nodes'] as List).map((n) => TradeNode.fromJson(n)).toList(),
      );

  Map<String, TradeNode> get byId => {for (final n in nodes) n.nodeId: n};
}

/// Everything about a node the player does NOT directly control: its own
/// production value, and the aggregate trade power/behaviour of every
/// other country present.
class NodeStateData {
  String nodeId;
  double localValue;
  bool isHome;
  double playerBasePower;
  double otherCollectPower;
  Map<String, double> otherSteerPower;
  Map<String, int> otherSteerMerchants;
  double otherPassivePower;

  /// Authoritative save fields, echoed back to the backend untouched so it
  /// can replay the save's own allocation exactly. Not user-editable.
  final Map<String, dynamic> known;

  NodeStateData({
    required this.nodeId,
    this.localValue = 0,
    this.isHome = false,
    this.playerBasePower = 0,
    this.otherCollectPower = 0,
    Map<String, double>? otherSteerPower,
    Map<String, int>? otherSteerMerchants,
    this.otherPassivePower = 0,
    Map<String, dynamic>? known,
  })  : otherSteerPower = otherSteerPower ?? {},
        otherSteerMerchants = otherSteerMerchants ?? {},
        known = known ?? {};

  static const _knownKeys = [
    'known_gross_value',
    'known_retained_value',
    'known_retain_power',
    'known_pull_power',
    'known_player_val',
    'known_player_action',
    'known_player_light_ships',
    'known_player_steer_target',
  ];

  factory NodeStateData.fromJson(Map<String, dynamic> j) => NodeStateData(
        nodeId: j['node_id'],
        localValue: (j['local_value'] as num).toDouble(),
        isHome: j['is_home'] ?? false,
        playerBasePower: (j['player_base_power'] as num).toDouble(),
        otherCollectPower: (j['other_collect_power'] as num).toDouble(),
        otherSteerPower: (j['other_steer_power'] as Map? ?? {})
            .map((k, v) => MapEntry(k as String, (v as num).toDouble())),
        otherSteerMerchants: (j['other_steer_merchants'] as Map? ?? {})
            .map((k, v) => MapEntry(k as String, v as int)),
        otherPassivePower: (j['other_passive_power'] as num).toDouble(),
        known: {for (final k in _knownKeys) if (j[k] != null) k: j[k]},
      );

  Map<String, dynamic> toJson() => {
        ...known,
        'node_id': nodeId,
        'local_value': localValue,
        'is_home': isHome,
        'player_base_power': playerBasePower,
        'other_collect_power': otherCollectPower,
        'other_steer_power': otherSteerPower,
        'other_steer_merchants': otherSteerMerchants,
        'other_passive_power': otherPassivePower,
      };
}

class NodeAllocationData {
  MerchantAction merchantAction;
  String? steerTarget;
  int lightShips;

  NodeAllocationData({
    this.merchantAction = MerchantAction.none,
    this.steerTarget,
    this.lightShips = 0,
  });

  NodeAllocationData copy() => NodeAllocationData(
        merchantAction: merchantAction,
        steerTarget: steerTarget,
        lightShips: lightShips,
      );

  factory NodeAllocationData.fromJson(Map<String, dynamic> j) => NodeAllocationData(
        merchantAction: merchantActionFromJson(j['merchant_action'] ?? 'none'),
        steerTarget: j['steer_target'],
        lightShips: j['light_ships'] ?? 0,
      );

  Map<String, dynamic> toJson() => {
        'merchant_action': merchantActionToJson(merchantAction),
        'steer_target': steerTarget,
        'light_ships': lightShips,
      };
}

class ParamsData {
  double tradeEfficiency;
  double merchantPower;
  double capitalMerchantPower;
  double powerPerLightShip;
  double homePowerBonus;
  double merchantPresentIncomeBonus;
  double steerValueBonusPerMerchant;

  ParamsData({
    this.tradeEfficiency = 0.0,
    this.merchantPower = 2.0,
    this.capitalMerchantPower = 5.0,
    this.powerPerLightShip = 3.0,
    this.homePowerBonus = 0.1,
    this.merchantPresentIncomeBonus = 0.1,
    this.steerValueBonusPerMerchant = 0.05,
  });

  Map<String, dynamic> toJson() => {
        'trade_efficiency': tradeEfficiency,
        'merchant_power': merchantPower,
        'capital_merchant_power': capitalMerchantPower,
        'power_per_light_ship': powerPerLightShip,
        'home_power_bonus': homePowerBonus,
        'merchant_present_income_bonus': merchantPresentIncomeBonus,
        'steer_value_bonus_per_merchant': steerValueBonusPerMerchant,
        // ship_chunk deliberately omitted -- internal optimizer tuning knob,
        // not a game mechanic; backend defaults it to 1 (see Params).
      };
}

class NodeBreakdownData {
  final String nodeId;
  final String displayName;
  final double localValue;
  final double totalValue;
  final double playerPower;
  final double totalPower;
  final bool playerCollects;
  final double playerIncome;
  final double forwardedValue;
  final Map<String, double> linkValues;

  NodeBreakdownData.fromJson(Map<String, dynamic> j)
      : nodeId = j['node_id'],
        displayName = j['display_name'],
        localValue = (j['local_value'] as num).toDouble(),
        totalValue = (j['total_value'] as num).toDouble(),
        playerPower = (j['player_power'] as num).toDouble(),
        totalPower = (j['total_power'] as num).toDouble(),
        playerCollects = j['player_collects'],
        playerIncome = (j['player_income'] as num).toDouble(),
        forwardedValue = (j['forwarded_value'] as num).toDouble(),
        linkValues = (j['link_values'] as Map).map((k, v) => MapEntry(k as String, (v as num).toDouble()));
}

class SimulateResponseData {
  final double totalIncome;
  final Map<String, NodeBreakdownData> nodes;

  SimulateResponseData.fromJson(Map<String, dynamic> j)
      : totalIncome = (j['total_income'] as num).toDouble(),
        nodes = (j['nodes'] as Map).map((k, v) => MapEntry(k as String, NodeBreakdownData.fromJson(v)));
}

class MarginalValueData {
  final String label;
  final double income;
  final double deltaVsOptimal;

  /// Where the change would be made: added to / taken from this node.
  final String? nodeId;
  final String? nodeDisplayName;
  final String? change; // 'add' | 'remove'
  final MerchantAction? merchantAction;
  final String? steerTarget;
  final String? steerTargetDisplayName;

  MarginalValueData.fromJson(Map<String, dynamic> j)
      : label = j['label'],
        income = (j['income'] as num).toDouble(),
        deltaVsOptimal = (j['delta_vs_optimal'] as num).toDouble(),
        nodeId = j['node_id'],
        nodeDisplayName = j['node_display_name'],
        change = j['change'],
        merchantAction =
            j['merchant_action'] == null ? null : merchantActionFromJson(j['merchant_action']),
        steerTarget = j['steer_target'],
        steerTargetDisplayName = j['steer_target_display_name'];
}

class RecommendedActionData {
  final String nodeId;
  final String displayName;
  final MerchantAction merchantAction;
  final String? steerTarget;
  final String? steerTargetDisplayName;
  final int lightShips;

  RecommendedActionData.fromJson(Map<String, dynamic> j)
      : nodeId = j['node_id'],
        displayName = j['display_name'],
        merchantAction = merchantActionFromJson(j['merchant_action']),
        steerTarget = j['steer_target'],
        steerTargetDisplayName = j['steer_target_display_name'],
        lightShips = j['light_ships'];
}

class OptimizeResponseData {
  final double income;
  final double baselineIncome;
  final double? currentIncome;
  final double? incomeGainVsCurrent;
  final List<RecommendedActionData> recommendedActions;
  final List<MarginalValueData> merchantMarginals;
  final List<MarginalValueData> shipMarginals;
  final SimulateResponseData breakdown;

  OptimizeResponseData.fromJson(Map<String, dynamic> j)
      : income = (j['income'] as num).toDouble(),
        baselineIncome = (j['baseline_income'] as num).toDouble(),
        currentIncome = (j['current_income'] as num?)?.toDouble(),
        incomeGainVsCurrent = (j['income_gain_vs_current'] as num?)?.toDouble(),
        recommendedActions = (j['recommended_actions'] as List)
            .map((a) => RecommendedActionData.fromJson(a))
            .toList(),
        merchantMarginals =
            (j['merchant_marginals'] as List).map((m) => MarginalValueData.fromJson(m)).toList(),
        shipMarginals = (j['ship_marginals'] as List).map((m) => MarginalValueData.fromJson(m)).toList(),
        breakdown = SimulateResponseData.fromJson(j['breakdown']);
}

class ImportSaveResponseData {
  final String playerTag;
  final List<String> warnings;
  final Map<String, NodeStateData> nodeStates;
  final Map<String, NodeAllocationData> currentAllocation;
  final String? suggestedHomeNode;
  final double? suggestedTradeEfficiency;
  final double actualCurrentIncome;
  final int? suggestedMaxMerchants;
  final int? suggestedMaxLightShips;
  final double? suggestedPowerPerLightShip;
  final List<String> suggestedCandidateNodes;

  ImportSaveResponseData.fromJson(Map<String, dynamic> j)
      : playerTag = j['player_tag'],
        warnings = List<String>.from(j['warnings']),
        nodeStates =
            (j['node_states'] as Map).map((k, v) => MapEntry(k as String, NodeStateData.fromJson(v))),
        currentAllocation = (j['current_allocation'] as Map)
            .map((k, v) => MapEntry(k as String, NodeAllocationData.fromJson(v))),
        suggestedHomeNode = j['suggested_home_node'],
        suggestedTradeEfficiency = (j['suggested_trade_efficiency'] as num?)?.toDouble(),
        actualCurrentIncome = (j['actual_current_income'] as num).toDouble(),
        suggestedMaxMerchants = j['suggested_max_merchants'] as int?,
        suggestedMaxLightShips = j['suggested_max_light_ships'] as int?,
        suggestedPowerPerLightShip = (j['suggested_power_per_light_ship'] as num?)?.toDouble(),
        suggestedCandidateNodes = List<String>.from(j['suggested_candidate_nodes'] ?? const []);
}

/// What `/api/build` says is on disk right now.
class BuildInfoData {
  final String? buildId;
  final String? builtAt;
  final bool sourcesNewerThanBuild;

  BuildInfoData.fromJson(Map<String, dynamic> j)
      : buildId = j['build_id'],
        builtAt = j['built_at'],
        sourcesNewerThanBuild = j['sources_newer_than_build'] ?? false;
}
