import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'theme.dart';
import 'providers/app_provider.dart';
import 'screens/import_screen.dart';
import 'screens/practice_screen.dart';
import 'screens/history_screen.dart';

void main() {
  runApp(
    ChangeNotifierProvider(
      create: (_) => AppProvider()..loadVideos()..loadHistory(),
      child: const ReadAfterMeApp(),
    ),
  );
}

class ReadAfterMeApp extends StatelessWidget {
  const ReadAfterMeApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ReadAfterMe',
      debugShowCheckedModeBanner: false,
      theme: buildTheme(),
      home: const MainScreen(),
    );
  }
}

class MainScreen extends StatelessWidget {
  const MainScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<AppProvider>(
      builder: (context, app, _) {
        return Scaffold(
          body: IndexedStack(
            index: app.currentTab,
            children: const [
              ImportScreen(),
              PracticeScreen(),
              HistoryScreen(),
            ],
          ),
          bottomNavigationBar: BottomNavigationBar(
            currentIndex: app.currentTab,
            onTap: (i) => app.currentTab = i,
            items: const [
              BottomNavigationBarItem(icon: Icon(Icons.upload_file), label: '导入'),
              BottomNavigationBarItem(icon: Icon(Icons.mic), label: '练习'),
              BottomNavigationBarItem(icon: Icon(Icons.history), label: '记录'),
            ],
          ),
        );
      },
    );
  }
}
