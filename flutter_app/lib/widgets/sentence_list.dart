import 'package:flutter/material.dart';
import '../models/sentence.dart';
import '../theme.dart';

class SentenceList extends StatelessWidget {
  final List<Sentence> sentences;
  final int activeIndex;
  final void Function(int) onTap;

  const SentenceList({
    super.key,
    required this.sentences,
    required this.activeIndex,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      padding: const EdgeInsets.all(8),
      itemCount: sentences.length,
      itemBuilder: (context, i) {
        final s = sentences[i];
        final isActive = i == activeIndex;
        return GestureDetector(
          onTap: () => onTap(i),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            margin: const EdgeInsets.only(bottom: 4),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            decoration: BoxDecoration(
              color: isActive ? kCoral.withValues(alpha: 0.06) : Colors.white,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: isActive ? kCoral.withValues(alpha: 0.3) : Colors.transparent,
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  s.en,
                  style: TextStyle(
                    fontSize: 13,
                    color: isActive ? kSlate700 : Colors.grey.shade600,
                    fontWeight: isActive ? FontWeight.w500 : FontWeight.normal,
                  ),
                ),
                if (s.zh.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Text(
                      s.zh,
                      style: TextStyle(fontSize: 11, color: Colors.grey.shade400),
                    ),
                  ),
                Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: Text(
                    '${s.start.toStringAsFixed(1)}s - ${s.end.toStringAsFixed(1)}s',
                    style: TextStyle(fontSize: 9, color: Colors.grey.shade300),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
