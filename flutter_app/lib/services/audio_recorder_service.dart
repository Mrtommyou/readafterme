import 'dart:io';
import 'package:record/record.dart';
import 'package:path_provider/path_provider.dart';

class AudioRecorderService {
  final _recorder = AudioRecorder();
  String? _outputPath;
  bool _isRecording = false;

  bool get isRecording => _isRecording;

  Future<String> start() async {
    _isRecording = true;
    final dir = await getTemporaryDirectory();
    _outputPath = '${dir.path}/recording_${DateTime.now().millisecondsSinceEpoch}.m4a';
    await _recorder.start(
      const RecordConfig(AudioEncoder.aacLc),
      path: _outputPath!,
    );
    return _outputPath!;
  }

  Future<String?> stop() async {
    _isRecording = false;
    final path = _outputPath;
    _outputPath = null;
    await _recorder.stop();
    if (path != null && File(path).existsSync()) return path;
    return null;
  }

  void dispose() {
    _recorder.dispose();
  }
}
