import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../theme.dart';
import '../providers/app_provider.dart';
import '../models/video_info.dart';

class ImportScreen extends StatelessWidget {
  const ImportScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<AppProvider>(
      builder: (context, app, _) {
        return Scaffold(
          appBar: AppBar(title: const Text('导入视频')),
          body: Column(
            children: [
              _buildUploadCard(context, app),
              const SizedBox(height: 12),
              if (app.loadingVideos)
                const Expanded(
                  child: Center(child: CircularProgressIndicator()),
                )
              else
                Expanded(
                  child: _buildVideoList(context, app),
                ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildUploadCard(BuildContext context, AppProvider app) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
      child: Card(
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: app.isUploading ? null : () => app.pickAndUploadFile(),
          child: Container(
            height: 120,
            alignment: Alignment.center,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  app.isUploading ? Icons.hourglass_top : Icons.cloud_upload_outlined,
                  size: 36,
                  color: app.isUploading ? kSlate400 : kCoral,
                ),
                const SizedBox(height: 8),
                Text(
                  app.isUploading ? '上传中...' : '点击选择视频文件',
                  style: TextStyle(color: kSlate500, fontSize: 14),
                ),
                if (app.isUploading)
                  Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: SizedBox(
                      width: 24,
                      height: 24,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: kCoral,
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildVideoList(BuildContext context, AppProvider app) {
    if (app.videos.isEmpty) {
      return Center(
        child: Text('暂无视频', style: TextStyle(color: kSlate400, fontSize: 14)),
      );
    }
    return RefreshIndicator(
      onRefresh: () => app.loadVideos(),
      child: ListView.builder(
        padding: const EdgeInsets.symmetric(horizontal: 16),
        itemCount: app.videos.length,
        itemBuilder: (context, i) {
          final v = app.videos[i];
          return _buildVideoRow(context, app, v);
        },
      ),
    );
  }

  Widget _buildVideoRow(BuildContext context, AppProvider app, VideoInfo v) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: Container(
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            color: kAmberLight,
            borderRadius: BorderRadius.circular(8),
          ),
          child: const Icon(Icons.play_circle_outline, color: kCoral),
        ),
        title: Text(v.name, style: const TextStyle(fontSize: 14), maxLines: 1, overflow: TextOverflow.ellipsis),
        subtitle: Text(v.duration, style: TextStyle(fontSize: 11, color: kSlate400)),
        trailing: const Icon(Icons.chevron_right, size: 18, color: kSlate400),
        onTap: () => app.selectVideo(v.id, v.name),
      ),
    );
  }
}
