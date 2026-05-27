class ScoreResult {
  final double pronunciation;
  final double fluency;
  final double timing;
  final double overall;

  ScoreResult({
    required this.pronunciation,
    required this.fluency,
    required this.timing,
    required this.overall,
  });

  factory ScoreResult.fromJson(Map<String, dynamic> json) => ScoreResult(
        pronunciation: (json['pronunciation'] as num?)?.toDouble() ?? 0,
        fluency: (json['fluency'] as num?)?.toDouble() ?? 0,
        timing: (json['timing'] as num?)?.toDouble() ?? 0,
        overall: (json['overall'] as num?)?.toDouble() ?? 0,
      );
}
