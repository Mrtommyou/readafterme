import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../theme.dart';
import '../providers/app_provider.dart';
import '../models/score_result.dart';
import '../widgets/video_player_widget.dart';
import '../widgets/sentence_list.dart';
import '../widgets/score_ring.dart';

class PracticeScreen extends StatelessWidget {
  const PracticeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<AppProvider>(
      builder: (context, app, _) {
        if (app.selectedVideoId == null) {
          return Scaffold(
            appBar: AppBar(title: const Text('练习')),
            body: Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.play_circle_outline, size: 64, color: kSlate400),
                  const SizedBox(height: 16),
                  Text('请先在「导入」页面选择一个视频',
                      style: TextStyle(color: kSlate500)),
                ],
              ),
            ),
          );
        }

        return Scaffold(
          appBar: AppBar(title: Text(app.selectedVideoName, overflow: TextOverflow.ellipsis)),
          body: Column(
            children: [
              SizedBox(
                width: double.infinity,
                child: _VideoPlayerSection(videoUrl: app.api.videoFileUrl(app.selectedVideoId!)),
              ),
              if (app.loadingSentences)
                const Expanded(
                  child: Center(child: CircularProgressIndicator()),
                )
              else ...[
                _RecordingSection(app: app),
                if (app.scores != null) _ScoreSection(scores: app.scores!),
                const SizedBox(height: 8),
                Text('句子 ${app.activeSentenceIdx + 1}/${app.sentences.length}',
                    style: TextStyle(fontSize: 12, color: kSlate400)),
                Expanded(
                  child: SentenceList(
                    sentences: app.sentences,
                    activeIndex: app.activeSentenceIdx,
                    onTap: (i) => app.setActiveSentence(i),
                  ),
                ),
              ],
            ],
          ),
        );
      },
    );
  }
}

class _VideoPlayerSection extends StatefulWidget {
  final String videoUrl;
  const _VideoPlayerSection({required this.videoUrl});

  @override
  State<_VideoPlayerSection> createState() => _VideoPlayerSectionState();
}

class _VideoPlayerSectionState extends State<_VideoPlayerSection> {
  final GlobalKey<VideoPlayerWidgetState> _playerKey = GlobalKey();

  @override
  Widget build(BuildContext context) {
    return VideoPlayerWidget(
      key: _playerKey,
      url: widget.videoUrl,
      onPositionChanged: (pos) {
        final app = context.read<AppProvider>();
        for (int i = app.sentences.length - 1; i >= 0; i--) {
          if (pos >= app.sentences[i].start) {
            if (app.activeSentenceIdx != i) {
              app.setActiveSentence(i);
            }
            break;
          }
        }
      },
    );
  }
}

class _RecordingSection extends StatelessWidget {
  final AppProvider app;
  const _RecordingSection({required this.app});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        children: [
          _RecordButton(app: app),
          const SizedBox(width: 12),
          if (app.recordingPath != null) ...[
            _PlayButton(audioPath: app.recordingPath!),
            const SizedBox(width: 8),
            _SubmitButton(app: app),
          ],
          const Spacer(),
          if (app.isRecording)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.red.shade50,
                borderRadius: BorderRadius.circular(4),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.circle, size: 8, color: Colors.red.shade400),
                  const SizedBox(width: 4),
                  Text('录音中', style: TextStyle(fontSize: 11, color: Colors.red.shade700)),
                ],
              ),
            ),
          if (app.isScoring)
            Padding(
              padding: const EdgeInsets.only(left: 8),
              child: SizedBox(
                width: 16, height: 16,
                child: CircularProgressIndicator(strokeWidth: 2, color: kCoral),
              ),
            ),
        ],
      ),
    );
  }
}

class _RecordButton extends StatelessWidget {
  final AppProvider app;
  const _RecordButton({required this.app});

  @override
  Widget build(BuildContext context) {
    return IconButton(
      icon: Icon(
        app.isRecording ? Icons.stop_circle : Icons.mic,
        color: app.isRecording ? Colors.red : kCoral,
        size: 32,
      ),
      onPressed: () => app.toggleRecording(),
    );
  }
}

class _PlayButton extends StatelessWidget {
  final String audioPath;
  const _PlayButton({required this.audioPath});

  @override
  Widget build(BuildContext context) {
    return IconButton(
      icon: const Icon(Icons.play_arrow, color: kSlate700),
      onPressed: () {
        // Play recording - simplified, audio_player package can be added
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('录音已保存: $audioPath'), duration: Duration(seconds: 1)),
        );
      },
    );
  }
}

class _SubmitButton extends StatelessWidget {
  final AppProvider app;
  const _SubmitButton({required this.app});

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: app.isScoring ? null : () => app.submitScoring(),
      style: ElevatedButton.styleFrom(
        backgroundColor: kCoral,
        foregroundColor: Colors.white,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      ),
      child: const Text('评分', style: TextStyle(fontSize: 13)),
    );
  }
}

class _ScoreSection extends StatelessWidget {
  final ScoreResult scores;
  const _ScoreSection({required this.scores});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: kAmberBorder),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          ScoreRing(percent: scores.pronunciation, label: '发音', color: kCoral),
          ScoreRing(percent: scores.fluency, label: '流利度', color: Colors.amber),
          ScoreRing(percent: scores.timing, label: '节奏', color: Colors.blue.shade300),
          ScoreRing(percent: scores.overall, label: '总分', color: Colors.green.shade400),
        ],
      ),
    );
  }
}
