class Sentence {
  final String en;
  final String zh;
  final double start;
  final double end;

  Sentence({
    required this.en,
    required this.zh,
    required this.start,
    required this.end,
  });

  factory Sentence.fromJson(Map<String, dynamic> json) => Sentence(
        en: json['en'] as String? ?? '',
        zh: json['zh'] as String? ?? '',
        start: (json['start'] as num?)?.toDouble() ?? 0.0,
        end: (json['end'] as num?)?.toDouble() ?? 0.0,
      );
}
