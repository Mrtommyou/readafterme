class HistoryItem {
  final String date;
  final String video;
  final int sentences;
  final double score;

  HistoryItem({
    required this.date,
    required this.video,
    required this.sentences,
    required this.score,
  });

  factory HistoryItem.fromJson(Map<String, dynamic> json) => HistoryItem(
        date: json['date'] as String? ?? '',
        video: json['video'] as String? ?? '',
        sentences: json['sentences'] as int? ?? 0,
        score: (json['score'] as num?)?.toDouble() ?? 0,
      );
}
