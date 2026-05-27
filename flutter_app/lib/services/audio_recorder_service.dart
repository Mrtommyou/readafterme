import 'dart:io';
import 'package:flutter_sound/flutter_sound.dart';
import 'package:path_provider/path_provider.dart';

class AudioRecorderService {
  FlutterSoundRecorder? _recorder;
  String? _outputPath;

  bool get isRecording => _recorder?.isRecording ?? false;

  Future<String> start() async {
    _recorder = FlutterSoundRecorder();
    await _recorder!.openAudioSession();
    final dir = await getTemporaryDirectory();
    _outputPath = '${dir.path}/recording_${DateTime.now().millisecondsSinceEpoch}.m4a';
    await _recorder!.startRecorder(
      toFile: _outputPath!,
      codec: Codec.aacADTS,
    );
    return _outputPath!;
  }

  Future<String?> stop() async {
    if (_recorder == null) return null;
    final path = _outputPath;
    _outputPath = null;
    await _recorder!.stopRecorder();
    await _recorder!.closeAudioSession();
    _recorder = null;
    if (path != null && File(path).existsSync()) return path;
    return null;
  }

  void dispose() {
    _recorder?.closeAudioSession();
    _recorder = null;
  }
}
