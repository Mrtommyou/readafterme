import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart';
import '../theme.dart';

class VideoPlayerWidget extends StatefulWidget {
  final String url;
  final void Function(double position)? onPositionChanged;

  const VideoPlayerWidget({
    super.key,
    required this.url,
    this.onPositionChanged,
  });

  @override
  State<VideoPlayerWidget> createState() => VideoPlayerWidgetState();
}

class VideoPlayerWidgetState extends State<VideoPlayerWidget> {
  VideoPlayerController? _controller;
  bool _initialized = false;
  Duration _position = Duration.zero;
  bool _showControls = true;

  @override
  void initState() {
    super.initState();
    _initController();
  }

  @override
  void didUpdateWidget(VideoPlayerWidget old) {
    super.didUpdateWidget(old);
    if (old.url != widget.url) {
      _controller?.dispose();
      _initialized = false;
      _initController();
    }
  }

  void _initController() {
    _controller = VideoPlayerController.networkUrl(Uri.parse(widget.url));
    _controller!.addListener(_onUpdate);
    _controller!.initialize().then((_) {
      if (mounted) {
        setState(() => _initialized = true);
      }
    });
  }

  void _onUpdate() {
    if (!mounted) return;
    final pos = _controller!.value.position;
    if (pos != _position) {
      _position = pos;
      widget.onPositionChanged?.call(pos.inMilliseconds / 1000.0);
    }
  }

  void seekTo(double seconds) {
    _controller?.seekTo(Duration(milliseconds: (seconds * 1000).toInt()));
  }

  @override
  void dispose() {
    _controller?.removeListener(_onUpdate);
    _controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!_initialized) {
      return AspectRatio(
        aspectRatio: 16 / 9,
        child: Container(
          color: Colors.black,
          child: const Center(child: CircularProgressIndicator()),
        ),
      );
    }

    return GestureDetector(
      onTap: () => setState(() => _showControls = !_showControls),
      child: Stack(
        children: [
          AspectRatio(
            aspectRatio: _controller!.value.aspectRatio,
            child: VideoPlayer(_controller!),
          ),
          if (_showControls) _buildControls(),
        ],
      ),
    );
  }

  Widget _buildControls() {
    final total = _controller!.value.duration;
    return Positioned.fill(
      child: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.bottomCenter,
            end: Alignment.center,
            colors: [Colors.black54, Colors.transparent],
          ),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.end,
          children: [
            SliderTheme(
              data: SliderTheme.of(context).copyWith(
                trackHeight: 3,
                thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 6),
                activeTrackColor: kCoral,
                inactiveTrackColor: Colors.white38,
                thumbColor: kCoral,
              ),
              child: Slider(
                value: _position.inMilliseconds.toDouble(),
                max: total.inMilliseconds.toDouble().clamp(1, double.infinity),
                onChanged: (v) => seekTo(v / 1000),
              ),
            ),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                IconButton(
                  icon: Icon(
                    _controller!.value.isPlaying ? Icons.pause : Icons.play_arrow,
                    color: Colors.white,
                    size: 32,
                  ),
                  onPressed: () {
                    setState(() {
                      _controller!.value.isPlaying
                          ? _controller!.pause()
                          : _controller!.play();
                    });
                  },
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
