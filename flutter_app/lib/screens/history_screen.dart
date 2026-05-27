import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../theme.dart';
import '../providers/app_provider.dart';

class HistoryScreen extends StatelessWidget {
  const HistoryScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<AppProvider>(
      builder: (context, app, _) {
        return Scaffold(
          appBar: AppBar(title: const Text('练习记录')),
          body: app.history.isEmpty
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.history, size: 64, color: kSlate400),
                      const SizedBox(height: 16),
                      Text('暂无练习记录', style: TextStyle(color: kSlate500)),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: () => app.loadHistory(),
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: app.history.length,
                    itemBuilder: (context, i) {
                      final h = app.history[i];
                      return Card(
                        margin: const EdgeInsets.only(bottom: 8),
                        child: ListTile(
                          leading: Container(
                            width: 44,
                            height: 44,
                            decoration: BoxDecoration(
                              color: _scoreColor(h.score).withValues(alpha: 0.15),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            alignment: Alignment.center,
                            child: Text(
                              '${h.score.toInt()}%',
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 16,
                                color: _scoreColor(h.score),
                              ),
                            ),
                          ),
                          title: Text(
                            h.video,
                            style: const TextStyle(fontSize: 14),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          subtitle: Text(
                            '${h.date} · ${h.sentences}个句子',
                            style: TextStyle(fontSize: 11, color: kSlate400),
                          ),
                        ),
                      );
                    },
                  ),
                ),
        );
      },
    );
  }

  Color _scoreColor(double score) {
    if (score >= 80) return Colors.green;
    if (score >= 60) return Colors.orange;
    return Colors.red;
  }
}
