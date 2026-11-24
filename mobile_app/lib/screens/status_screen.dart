import 'package:flutter/material.dart';

import '../api.dart';
import '../theme.dart';

/// Status tab — GET /health/detailed checks with Hinglish fix hints,
/// same as the PWA Status panel.
class StatusScreen extends StatefulWidget {
  const StatusScreen({required this.api, super.key});

  final ApiClient api;

  @override
  State<StatusScreen> createState() => _StatusScreenState();
}

class _StatusScreenState extends State<StatusScreen> {
  bool _allOk = false;
  List<HealthCheck> _checks = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final (allOk, checks) = await widget.api.getHealthDetailed();
      if (!mounted) return;
      setState(() {
        _allOk = allOk;
        _checks = checks;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  /// Custom status icon name (v0.5): a filled circle + white glyph.
  String _iconFor(String status) {
    switch (status) {
      case 'ok':
        return 'check';
      case 'fail':
        return 'error';
      default:
        return 'skip';
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(_error!, textAlign: TextAlign.center),
              const SizedBox(height: 12),
              FilledButton(
                onPressed: _load,
                child: const Text('Dobara try karo'),
              ),
            ],
          ),
        ),
      );
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.all(12),
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: _allOk ? const Color(0xFFDCFCE7) : const Color(0xFFFEE2E2),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: _allOk
                    ? const Color(0xFF86EFAC)
                    : const Color(0xFFFCA5A5),
              ),
            ),
            child: Text(
              _allOk
                  ? 'Sab kuch theek hai — Linda ready hai.'
                  : 'Kuch cheezein theek nahi hain — har fail wale ke neeche fix likha hai.',
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
          ),
          const SizedBox(height: 12),
          ..._checks.map(
            (c) => Card(
              margin: const EdgeInsets.only(bottom: 8),
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        LindaIcon(_iconFor(c.status), size: 20),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            c.label,
                            style: const TextStyle(fontWeight: FontWeight.w600),
                          ),
                        ),
                      ],
                    ),
                    if (c.detail.isNotEmpty) ...[
                      const SizedBox(height: 4),
                      Text(
                        c.detail,
                        style: const TextStyle(
                          color: LindaTheme.muted,
                          fontSize: 12,
                        ),
                      ),
                    ],
                    if (c.status == 'fail' && c.hint.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFEF3C7),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          'Fix: ${c.hint}',
                          style: const TextStyle(fontSize: 12),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ),
          const SizedBox(height: 8),
          FilledButton.icon(
            onPressed: _load,
            icon: const LindaIcon('refresh', size: 18, color: Colors.white),
            label: const Text('Dobara check karo'),
          ),
        ],
      ),
    );
  }
}
