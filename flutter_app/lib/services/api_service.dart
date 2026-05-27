import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../models/video_info.dart';
import '../models/sentence.dart';
import '../models/score_result.dart';
import '../models/history_item.dart';

class ApiService {
  static const String _baseUrl = 'http://10.0.0.233:9004';

  // ── Videos ────────────────────────────────────────────────────────────

  Future<List<VideoInfo>> getVideos() async {
    final res = await http.get(Uri.parse('$_baseUrl/api/videos'));
    if (res.statusCode != 200) throw Exception('GET /api/videos: ${res.statusCode}');
    final data = json.decode(res.body) as Map<String, dynamic>;
    final list = data['videos'] as List<dynamic>;
    return list.map((e) => VideoInfo.fromJson(e as Map<String, dynamic>)).toList();
  }

  // ── Upload (JSON base64 – works reliably on native) ───────────────────

  Future<Map<String, dynamic>> uploadVideo(String name, String mimeType, String base64Data) async {
    final res = await http.post(
      Uri.parse('$_baseUrl/api/upload-json'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'name': name,
        'mime_type': mimeType,
        'data': base64Data,
      }),
    );
    if (res.statusCode != 200) {
      throw Exception('Upload failed: ${res.statusCode} ${res.body}');
    }
    return json.decode(res.body) as Map<String, dynamic>;
  }

  // ── Upload (multipart – fallback for web) ─────────────────────────────

  Future<Map<String, dynamic>> uploadVideoMultipart(String filePath, String fileName) async {
    final req = http.MultipartRequest('POST', Uri.parse('$_baseUrl/api/upload'));
    req.files.add(await http.MultipartFile.fromPath('file', filePath, filename: fileName));
    final streamed = await req.send();
    final res = await http.Response.fromStream(streamed);
    if (res.statusCode != 200) {
      throw Exception('Upload failed: ${res.statusCode} ${res.body}');
    }
    return json.decode(res.body) as Map<String, dynamic>;
  }

  // ── Sentences ─────────────────────────────────────────────────────────

  Future<List<Sentence>> getSentences(String videoId) async {
    final res = await http.get(Uri.parse('$_baseUrl/api/videos/$videoId/sentences'));
    if (res.statusCode != 200) throw Exception('GET sentences: ${res.statusCode}');
    final data = json.decode(res.body) as Map<String, dynamic>;
    final list = data['sentences'] as List<dynamic>;
    return list.map((e) => Sentence.fromJson(e as Map<String, dynamic>)).toList();
  }

  String videoFileUrl(String videoId) => '$_baseUrl/api/videos/$videoId/file';

  // ── Score ─────────────────────────────────────────────────────────────

  Future<ScoreResult> scoreRecording(String videoId, int sentenceIndex, String audioPath) async {
    final req = http.MultipartRequest('POST', Uri.parse('$_baseUrl/api/score'));
    req.fields['video_id'] = videoId;
    req.fields['sentence_index'] = sentenceIndex.toString();
    req.files.add(await http.MultipartFile.fromPath('file', audioPath, filename: 'recording_$sentenceIndex.webm'));
    final streamed = await req.send();
    final res = await http.Response.fromStream(streamed);
    if (res.statusCode != 200) throw Exception('Score failed: ${res.statusCode} ${res.body}');
    return ScoreResult.fromJson(json.decode(res.body) as Map<String, dynamic>);
  }

  // ── History ───────────────────────────────────────────────────────────

  Future<List<HistoryItem>> getHistory() async {
    final res = await http.get(Uri.parse('$_baseUrl/api/history'));
    if (res.statusCode != 200) throw Exception('GET history: ${res.statusCode}');
    final data = json.decode(res.body) as Map<String, dynamic>;
    final list = data['history'] as List<dynamic>;
    return list.map((e) => HistoryItem.fromJson(e as Map<String, dynamic>)).toList();
  }
}
