import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:file_picker/file_picker.dart';
import '../models/video_info.dart';
import '../models/sentence.dart';
import '../models/score_result.dart';
import '../models/history_item.dart';
import '../services/api_service.dart';
import '../services/audio_recorder_service.dart';

class AppProvider extends ChangeNotifier {
  final ApiService api = ApiService();
  final AudioRecorderService recorder = AudioRecorderService();

  // Navigation
  int _currentTab = 0;
  int get currentTab => _currentTab;
  set currentTab(int v) {
    _currentTab = v;
    notifyListeners();
  }

  // Videos
  List<VideoInfo> _videos = [];
  List<VideoInfo> get videos => _videos;
  bool _loadingVideos = false;
  bool get loadingVideos => _loadingVideos;

  // Selected video
  String? _selectedVideoId;
  String? get selectedVideoId => _selectedVideoId;
  String _selectedVideoName = '';
  String get selectedVideoName => _selectedVideoName;

  // Sentences
  List<Sentence> _sentences = [];
  List<Sentence> get sentences => _sentences;
  bool _loadingSentences = false;
  bool get loadingSentences => _loadingSentences;

  // Active sentence
  int _activeSentenceIdx = 0;
  int get activeSentenceIdx => _activeSentenceIdx;

  // Recording
  bool _isRecording = false;
  bool get isRecording => _isRecording;
  String? _recordingPath;
  String? get recordingPath => _recordingPath;

  // Scoring
  bool _isScoring = false;
  bool get isScoring => _isScoring;
  ScoreResult? _scores;
  ScoreResult? get scores => _scores;

  // Uploading
  bool _isUploading = false;
  bool get isUploading => _isUploading;

  // History
  List<HistoryItem> _history = [];
  List<HistoryItem> get history => _history;

  // Errors
  String? _error;
  String? get error => _error;

  void clearError() {
    _error = null;
    notifyListeners();
  }

  // ── Load data ────────────────────────────────────────────────────────

  Future<void> loadVideos() async {
    _loadingVideos = true;
    notifyListeners();
    try {
      _videos = await api.getVideos();
      _error = null;
    } catch (e) {
      _error = '加载视频列表失败: $e';
    }
    _loadingVideos = false;
    notifyListeners();
  }

  Future<void> loadSentences(String videoId) async {
    _loadingSentences = true;
    _activeSentenceIdx = 0;
    _scores = null;
    _recordingPath = null;
    notifyListeners();
    try {
      _sentences = await api.getSentences(videoId);
      _error = null;
    } catch (e) {
      _error = '加载句子失败: $e';
      _sentences = [];
    }
    _loadingSentences = false;
    notifyListeners();
  }

  Future<void> loadHistory() async {
    try {
      _history = await api.getHistory();
    } catch (e) {
      _error = '加载历史失败: $e';
    }
    notifyListeners();
  }

  void selectVideo(String id, String name) {
    _selectedVideoId = id;
    _selectedVideoName = name;
    _currentTab = 1;
    notifyListeners();
    loadSentences(id);
  }

  // ── Upload ───────────────────────────────────────────────────────────

  Future<void> pickAndUploadFile() async {
    final result = await FilePicker.pickFiles(
      type: FileType.video,
      allowMultiple: false,
      withData: true,
    );
    if (result == null || result.files.isEmpty) return;

    final file = result.files.first;
    if (file.bytes == null || file.bytes!.isEmpty) {
      _error = '无法读取文件数据';
      notifyListeners();
      return;
    }

    _isUploading = true;
    notifyListeners();

    try {
      final base64Data = base64Encode(file.bytes!);
      final mimeType = file.extension != null
          ? _mimeFromExt(file.extension!)
          : 'video/mp4';
      final res = await api.uploadVideo(file.name, mimeType, base64Data);
      await loadVideos();
      final videoId = res['video_id'] as String?;
      if (videoId != null) {
        selectVideo(videoId, file.name);
      }
      _error = null;
    } catch (e) {
      _error = '上传失败: $e';
    }

    _isUploading = false;
    notifyListeners();
  }

  // ── Practice ─────────────────────────────────────────────────────────

  void setActiveSentence(int idx) {
    if (idx >= 0 && idx < _sentences.length) {
      _activeSentenceIdx = idx;
      _scores = null;
      _recordingPath = null;
      notifyListeners();
    }
  }

  Future<void> toggleRecording() async {
    if (_isRecording) {
      final path = await recorder.stop();
      _recordingPath = path;
      _isRecording = false;
      notifyListeners();
    } else {
      _isRecording = true;
      notifyListeners();
      try {
        await recorder.start();
      } catch (e) {
        _error = '录音启动失败: $e';
        _isRecording = false;
        notifyListeners();
      }
    }
  }

  Future<void> submitScoring() async {
    if (_recordingPath == null || _selectedVideoId == null) return;
    _isScoring = true;
    notifyListeners();
    try {
      _scores = await api.scoreRecording(
        _selectedVideoId!,
        _activeSentenceIdx,
        _recordingPath!,
      );
      _error = null;
    } catch (e) {
      _error = '评分失败: $e';
    }
    _isScoring = false;
    notifyListeners();
  }

  void clearRecording() {
    _recordingPath = null;
    _scores = null;
    notifyListeners();
  }

  // ── Helpers ──────────────────────────────────────────────────────────

  static String _mimeFromExt(String ext) {
    switch (ext.toLowerCase()) {
      case 'mp4':
        return 'video/mp4';
      case 'avi':
        return 'video/avi';
      case 'mov':
        return 'video/quicktime';
      case 'mkv':
        return 'video/x-matroska';
      case 'webm':
        return 'video/webm';
      default:
        return 'video/mp4';
    }
  }
}

