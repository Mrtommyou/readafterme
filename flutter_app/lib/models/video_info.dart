class VideoInfo {
  final String id;
  final String name;
  final String duration;
  final String status;

  VideoInfo({
    required this.id,
    required this.name,
    required this.duration,
    required this.status,
  });

  factory VideoInfo.fromJson(Map<String, dynamic> json) => VideoInfo(
        id: json['id'] as String,
        name: json['name'] as String,
        duration: json['duration'] as String? ?? '0:00',
        status: json['status'] as String? ?? '',
      );
}
