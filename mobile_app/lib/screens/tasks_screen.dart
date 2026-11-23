import 'package:flutter/material.dart';

import '../api.dart';
import '../theme.dart';

/// Tasks tab — recent tasks from GET /tasks, tap for detail
/// (steps + result). Pull down to refresh.
class TasksScreen extends StatefulWidget {
  const TasksScreen({required this.api, super.key});

  final ApiClient api;

  @override
  State<TasksScreen> createState() => _TasksScreenState();
}

class _TasksScreenState extends State<TasksScreen> {
  List<SatyamTask> _tasks = [];
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
      final tasks = await widget.api.getTasks();
      if (!mounted) return;
      setState(() {
        _tasks = tasks;
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

  Color _statusColor(String status) {
    switch (status) {
      case 'done':
        return SatyamTheme.green;
      case 'error':
        return SatyamTheme.danger;
      case 'running':
      case 'waiting_approval':
        return SatyamTheme.accent;
      default:
        return SatyamTheme.muted;
    }
  }

  String _statusLabel(String status) {
    switch (status) {
      case 'done':
        return 'Ho gaya';
      case 'error':
        return 'Error';
      case 'running':
        return 'Chal raha hai';
      case 'waiting_approval':
        return 'Approval ka wait';
      case 'stopped':
        return 'Roka gaya';
      default:
        return status;
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
    if (_tasks.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(24),
          child: Text(
            'Abhi koi task nahi hai.\nChat me koi kaam bolo — wo yahan dikhega.',
            textAlign: TextAlign.center,
            style: TextStyle(color: SatyamTheme.muted),
          ),
        ),
      );
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView.builder(
        padding: const EdgeInsets.all(12),
        itemCount: _tasks.length,
        itemBuilder: (context, i) {
          final t = _tasks[i];
          return Card(
            margin: const EdgeInsets.only(bottom: 10),
            child: ListTile(
              title: Text(
                t.message,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              subtitle: Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Text('${t.steps.length} steps'),
              ),
              trailing: Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 10,
                  vertical: 5,
                ),
                decoration: BoxDecoration(
                  color: _statusColor(t.status).withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(999),
                ),
                child: Text(
                  _statusLabel(t.status),
                  style: TextStyle(
                    color: _statusColor(t.status),
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              onTap: () {
                Navigator.of(context).push(
                  MaterialPageRoute<void>(
                    builder: (_) => _TaskDetailScreen(task: t),
                  ),
                );
              },
            ),
          );
        },
      ),
    );
  }
}

class _TaskDetailScreen extends StatelessWidget {
  const _TaskDetailScreen({required this.task});

  final SatyamTask task;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(title: const Text('Task detail')),
      body: SatyamBackground(
        child: SafeArea(
          child: ListView(
            padding: const EdgeInsets.all(12),
            children: [
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Kaam',
                        style: TextStyle(
                          color: SatyamTheme.muted,
                          fontSize: 12,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(task.message, style: const TextStyle(fontSize: 16)),
                      const SizedBox(height: 10),
                      const Text(
                        'Status',
                        style: TextStyle(
                          color: SatyamTheme.muted,
                          fontSize: 12,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        task.status,
                        style: const TextStyle(fontWeight: FontWeight.w600),
                      ),
                      if (task.result != null) ...[
                        const SizedBox(height: 10),
                        const Text(
                          'Result',
                          style: TextStyle(
                            color: SatyamTheme.muted,
                            fontSize: 12,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(task.result!),
                      ],
                      if (task.error != null) ...[
                        const SizedBox(height: 10),
                        const Text(
                          'Error',
                          style: TextStyle(
                            color: SatyamTheme.muted,
                            fontSize: 12,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          task.error!,
                          style: const TextStyle(color: SatyamTheme.danger),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 6),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 4),
                child: Text(
                  'Steps (${task.steps.length})',
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
              const SizedBox(height: 8),
              ...task.steps.map(
                (s) => Card(
                  margin: const EdgeInsets.only(bottom: 8),
                  child: Padding(
                    padding: const EdgeInsets.all(11),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '#${s.n} ${s.action}',
                          style: const TextStyle(fontWeight: FontWeight.w600),
                        ),
                        if (s.thought.isNotEmpty) ...[
                          const SizedBox(height: 2),
                          Text(
                            s.thought,
                            style: const TextStyle(
                              color: SatyamTheme.muted,
                              fontSize: 12,
                            ),
                          ),
                        ],
                        if (s.result.isNotEmpty) ...[
                          const SizedBox(height: 6),
                          Text(s.result, style: const TextStyle(fontSize: 12)),
                        ],
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
