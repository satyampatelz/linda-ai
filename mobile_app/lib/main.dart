import 'dart:async';

import 'package:flutter/material.dart';

import 'api.dart';
import 'screens/chat_screen.dart';
import 'screens/settings_screen.dart';
import 'screens/status_screen.dart';
import 'screens/tasks_screen.dart';
import 'storage.dart';
import 'theme.dart';

void main() {
  runApp(const SatyamApp());
}

/// Satyam — the phone app. Four tabs (Chat, Tasks, Settings, Status)
/// talking to the same FastAPI backend as the PWA, on the laptop
/// (http://127.0.0.1:8000) or the Oracle cloud server — whichever the
/// user set in Settings. Same agent, same tasks, both devices.
class SatyamApp extends StatefulWidget {
  const SatyamApp({super.key});

  @override
  State<SatyamApp> createState() => _SatyamAppState();
}

class _SatyamAppState extends State<SatyamApp> {
  ServerConfig? _config;
  late ApiClient _api;

  @override
  void initState() {
    super.initState();
    _loadConfig();
  }

  Future<void> _loadConfig() async {
    final config = await ServerConfig.load();
    if (!mounted) return;
    setState(() {
      _config = config;
      _api = ApiClient(config);
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Satyam',
      debugShowCheckedModeBanner: false,
      theme: SatyamTheme.light(),
      home: _config == null
          ? const _LoadingSplash()
          : HomeScreen(
              api: _api,
              config: _config!,
              onConfigChanged: (config) {
                setState(() => _config = config);
              },
            ),
    );
  }
}

class _LoadingSplash extends StatelessWidget {
  const _LoadingSplash();

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: SatyamBackground(
        child: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              SatyamLogo(size: 64),
              SizedBox(height: 16),
              Text(
                'Satyam',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800),
              ),
              SizedBox(height: 24),
              CircularProgressIndicator(),
            ],
          ),
        ),
      ),
    );
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({
    required this.api,
    required this.config,
    required this.onConfigChanged,
    super.key,
  });

  final ApiClient api;
  final ServerConfig config;
  final void Function(ServerConfig config) onConfigChanged;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _tab = 0;
  bool _online = false;
  Timer? _healthTimer;

  @override
  void initState() {
    super.initState();
    _refreshHealth();
    _healthTimer = Timer.periodic(const Duration(seconds: 30), (_) {
      _refreshHealth();
    });
  }

  @override
  void dispose() {
    _healthTimer?.cancel();
    super.dispose();
  }

  Future<void> _refreshHealth() async {
    try {
      await widget.api.getHealth();
      if (!mounted) return;
      // v0.8.3: the header shows no model subtitle anymore — brain
      // info lives in the Status tab. Only the online pill is kept.
      setState(() {
        _online = true;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _online = false;
      });
    }
  }

  void _onAuthError() {
    // Wrong/missing token — send the user to Settings to fix it.
    setState(() => _tab = 2);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text(
          'API token is wrong or missing — enter the correct server token in Settings.',
        ),
        backgroundColor: SatyamTheme.danger,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        title: Row(
          children: [
            const SatyamLogo(),
            const SizedBox(width: 10),
            const Expanded(
              child: Text('Satyam'),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
              decoration: BoxDecoration(
                color: SatyamTheme.glassStrong,
                borderRadius: BorderRadius.circular(999),
                border: Border.all(color: Colors.white),
              ),
              child: Text(
                _online ? '● online' : '● offline',
                style: TextStyle(
                  fontSize: 12,
                  color: _online ? SatyamTheme.green : SatyamTheme.danger,
                ),
              ),
            ),
          ],
        ),
      ),
      body: SatyamBackground(
        child: SafeArea(
          child: IndexedStack(
            index: _tab,
            children: [
              ChatScreen(api: widget.api, onAuthError: _onAuthError),
              TasksScreen(api: widget.api),
              SettingsScreen(
                api: widget.api,
                config: widget.config,
                onConfigChanged: (config) {
                  widget.onConfigChanged(config);
                  _refreshHealth();
                },
              ),
              StatusScreen(api: widget.api),
            ],
          ),
        ),
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _tab,
        onTap: (i) => setState(() => _tab = i),
        type: BottomNavigationBarType.fixed,
        backgroundColor: Colors.white.withValues(alpha: 0.85),
        selectedItemColor: SatyamTheme.accent,
        unselectedItemColor: SatyamTheme.muted,
        // Custom hand-drawn tab icons (v0.5): the selected tab shows
        // the icon in its own gradient, unselected tabs are muted.
        items: [
          BottomNavigationBarItem(
            icon: SatyamIcon(
              'chat',
              size: 24,
              color: _tab == 0 ? null : SatyamTheme.muted,
            ),
            label: 'Chat',
          ),
          BottomNavigationBarItem(
            icon: SatyamIcon(
              'tasks',
              size: 24,
              color: _tab == 1 ? null : SatyamTheme.muted,
            ),
            label: 'Tasks',
          ),
          BottomNavigationBarItem(
            icon: SatyamIcon(
              'gear',
              size: 24,
              color: _tab == 2 ? null : SatyamTheme.muted,
            ),
            label: 'Settings',
          ),
          BottomNavigationBarItem(
            icon: SatyamIcon(
              'pulse',
              size: 24,
              color: _tab == 3 ? null : SatyamTheme.muted,
            ),
            label: 'Status',
          ),
        ],
      ),
    );
  }
}
