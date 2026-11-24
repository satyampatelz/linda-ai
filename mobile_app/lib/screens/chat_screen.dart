import 'dart:async';

import 'package:flutter/material.dart';

import '../api.dart';
import '../storage.dart';
import '../theme.dart';
import '../voice.dart';

/// Chat tab — mirrors the PWA: messages, live step log, approval card,
/// composer with send + stop + mic. Polls the backend while a task
/// runs so steps show live. (v0.5: the demo suggestion chips were
/// removed — the composer sits clean at the bottom.)
class ChatScreen extends StatefulWidget {
  const ChatScreen({required this.api, required this.onAuthError, super.key});

  final ApiClient api;
  final VoidCallback onAuthError;

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatMsg {
  _ChatMsg({
    required this.role,
    required this.text,
    this.isError = false,
    this.isWorking = false,
  });

  final String role; // user | agent
  String text;
  final bool isError;
  bool isWorking;
  String? stepLine;
}

class _ChatScreenState extends State<ChatScreen> {
  final List<_ChatMsg> _messages = [
    _ChatMsg(
      role: 'agent',
      text:
          'Hey! I\'m Linda — your personal AI agent.\n\n'
          'Just tell me what you need, and I\'ll get it done.',
    ),
  ];
  final TextEditingController _input = TextEditingController();
  final ScrollController _scroll = ScrollController();

  String? _taskId;
  Timer? _pollTimer;
  List<TaskStep> _steps = [];
  PendingApproval? _pendingApproval;
  bool _sending = false;

  // Secure credential box (v0.7): pending token/ID requests, shown as
  // masked input cards in the chat. Dismissed ones stay hidden for
  // this session.
  List<MessagingPending> _pendingCredentials = [];
  final Set<String> _dismissedPending = {};

  // Voice: mic input + spoken replies (fully on-device, free).
  final VoiceService _voice = VoiceService();
  bool _listening = false;
  int _speakingIndex = -1;
  String _listenBaseText = '';
  Timer? _listenWatchdog;

  @override
  void initState() {
    super.initState();
    _loadChatHistory();
    _checkMessagingPending();
  }

  /// Restore the saved chat transcript (v0.9) below the welcome
  /// bubble, so reopening the app shows the same chat. Failures are
  /// silent — the chat just starts fresh with the welcome.
  Future<void> _loadChatHistory() async {
    List<ChatHistoryMessage> history;
    try {
      history = await widget.api.getChatHistory();
    } catch (_) {
      return; // server down — try again next time the app opens
    }
    if (!mounted || history.isEmpty) return;
    setState(() {
      for (final m in history) {
        if (m.role != 'user' && m.role != 'agent') continue;
        _messages.add(
          _ChatMsg(
            role: m.role,
            text: m.text,
            // Error replies were saved as "Error: ..." — keep the red
            // bubble, like the PWA does.
            isError: m.role == 'agent' && m.text.startsWith('Error: '),
          ),
        );
      }
    });
    _scrollToBottom();
  }

  /// Ask the server if a messaging setup is waiting for credentials
  /// (the user enabled a platform in chat and its token/ID is missing).
  Future<void> _checkMessagingPending() async {
    List<MessagingPending> pending;
    try {
      pending = await widget.api.getMessagingPending();
    } catch (_) {
      return; // server down — try again after the next task
    }
    if (!mounted) return;
    setState(() {
      _pendingCredentials = pending
          .where((p) => !_dismissedPending.contains(p.key))
          .toList();
    });
  }

  void _dismissPending(MessagingPending pending) {
    setState(() {
      _dismissedPending.add(pending.key);
      _pendingCredentials.removeWhere((p) => p.key == pending.key);
    });
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    _listenWatchdog?.cancel();
    unawaited(_voice.dispose());
    _input.dispose();
    _scroll.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.animateTo(
          _scroll.position.maxScrollExtent,
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _showError(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: LindaTheme.danger),
    );
  }

  void _handleApiError(Object e) {
    if (e is ApiException && e.isAuthError) {
      widget.onAuthError();
    } else {
      _showError(e.toString());
    }
  }

  Future<void> _send() async {
    final text = _input.text.trim();
    if (text.isEmpty || _taskId != null || _sending) return;
    await _voice.stopSpeaking(); // a new message silences the old reply
    if (mounted) setState(() => _speakingIndex = -1);
    _input.clear();
    setState(() {
      _messages.add(_ChatMsg(role: 'user', text: text));
      _messages.add(
        _ChatMsg(role: 'agent', text: 'Working…', isWorking: true),
      );
      _steps = [];
      _pendingApproval = null;
      _sending = true;
    });
    _scrollToBottom();
    try {
      final taskId = await widget.api.startChat(text);
      if (!mounted) return;
      _taskId = taskId;
      setState(() => _sending = false);
      _startPolling();
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _sending = false;
        _messages[_messages.length - 1] = _ChatMsg(
          role: 'agent',
          text: 'Error: ${e.toString()}',
          isError: true,
        );
      });
      _handleApiError(e);
    }
  }

  void _startPolling() {
    _pollTimer?.cancel();
    _pollTimer = Timer.periodic(const Duration(milliseconds: 900), (_) {
      _pollOnce();
    });
    _pollOnce();
  }

  Future<void> _pollOnce() async {
    final taskId = _taskId;
    if (taskId == null) return;
    LindaTask task;
    try {
      task = await widget.api.getTask(taskId);
    } catch (_) {
      return; // transient hiccup — keep polling
    }
    if (!mounted || _taskId != taskId) return;
    setState(() {
      _steps = task.steps;
      _pendingApproval = task.pendingApproval;
      final bubble = _messages.lastWhere(
        (m) => m.role == 'agent' && m.isWorking,
        orElse: () => _messages.last,
      );
      if (bubble.isWorking && task.steps.isNotEmpty) {
        final last = task.steps.last;
        bubble.stepLine = 'Step ${last.n}: ${last.action}';
      }
    });
    if (task.isFinished) {
      _finishTask(task);
    }
  }

  void _finishTask(LindaTask task) {
    _pollTimer?.cancel();
    _pollTimer = null;
    _taskId = null;
    _pendingApproval = null;
    final text = task.status == 'done'
        ? (task.result ?? 'Done.')
        : task.status == 'stopped'
        ? (task.result ?? 'Task stopped.')
        : 'Error: ${task.error ?? 'something went wrong.'}';
    setState(() {
      final idx = _messages.lastIndexWhere(
        (m) => m.role == 'agent' && m.isWorking,
      );
      if (idx >= 0) {
        _messages[idx] = _ChatMsg(
          role: 'agent',
          text: text,
          isError: task.status == 'error',
        );
      }
    });
    _scrollToBottom();
    if (task.status == 'done') unawaited(_maybeAutoSpeak());
    // If this task asked for messaging credentials, show the secure box.
    unawaited(_checkMessagingPending());
  }

  /// Auto-speak (Settings, default OFF): read a finished reply aloud.
  Future<void> _maybeAutoSpeak() async {
    final autoSpeak = await VoicePrefs.loadAutoSpeak();
    if (!mounted || !autoSpeak) return;
    final idx = _messages.lastIndexWhere(
      (m) => m.role == 'agent' && !m.isWorking,
    );
    if (idx >= 0) await _speakMessage(idx);
  }

  Future<void> _stop() async {
    final taskId = _taskId;
    await _voice.stopSpeaking(); // a running reply stops talking too
    if (mounted) setState(() => _speakingIndex = -1);
    if (taskId == null) return;
    try {
      await widget.api.stopTask(taskId);
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Stopping the task…')));
    } catch (e) {
      _handleApiError(e);
    }
  }

  // ---- Voice: mic input + spoken replies ----

  /// Mic button: tap to talk, tap again (or just pause) to stop. The
  /// transcript lands in the composer for editing — never auto-sent.
  Future<void> _toggleMic() async {
    if (_listening) {
      await _voice.stopListening();
      return; // the watchdog clears the listening UI
    }
    _listenBaseText = _input.text.trim();
    setState(() => _listening = true);
    _startListenWatchdog();
    await _voice.startListening(
      onTranscript: (text, isFinal) {
        if (!mounted || text.isEmpty) return;
        setState(() {
          _input.text = _listenBaseText.isEmpty
              ? text
              : '$_listenBaseText $text';
        });
      },
      onError: (message) {
        if (!mounted) return;
        _showError(message);
      },
    );
    // If listening failed fast (no permission etc.), the watchdog
    // sees isListening == false and clears the UI on its next tick.
  }

  /// The recognizer stops on its own when the user pauses; poll its
  /// state so the listening UI always matches reality.
  void _startListenWatchdog() {
    _listenWatchdog?.cancel();
    _listenWatchdog = Timer.periodic(const Duration(milliseconds: 300), (_) {
      if (!_voice.isListening) {
        _listenWatchdog?.cancel();
        _listenWatchdog = null;
        if (mounted && _listening) setState(() => _listening = false);
      }
    });
  }

  /// Speaker icon on an agent message: tap to hear it, tap again to stop.
  Future<void> _speakMessage(int index) async {
    if (_speakingIndex == index) {
      await _voice.stopSpeaking();
      if (mounted) setState(() => _speakingIndex = -1);
      return;
    }
    setState(() => _speakingIndex = index);
    await _voice.speak(
      _messages[index].text,
      onDone: () {
        // Only clear if this message is still the one speaking (the
        // user may have tapped another message meanwhile).
        if (mounted && _speakingIndex == index) {
          setState(() => _speakingIndex = -1);
        }
      },
    );
  }

  Future<void> _decideApproval(bool approve) async {
    final taskId = _taskId;
    if (taskId == null) return;
    setState(() => _pendingApproval = null);
    try {
      await widget.api.approveTask(taskId, approve);
    } catch (e) {
      _handleApiError(e);
    }
  }

  void _openStepsSheet() {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) {
        return DraggableScrollableSheet(
          initialChildSize: 0.7,
          minChildSize: 0.4,
          maxChildSize: 0.9,
          builder: (context, scrollController) {
            return Container(
              decoration: const BoxDecoration(
                color: Color(0xF2FFFFFF),
                borderRadius: BorderRadius.vertical(top: Radius.circular(18)),
              ),
              child: Column(
                children: [
                  Padding(
                    padding: const EdgeInsets.all(16),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'Live steps',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        IconButton(
                          icon: const LindaIcon('close', size: 20),
                          onPressed: () => Navigator.pop(context),
                        ),
                      ],
                    ),
                  ),
                  Expanded(
                    child: _steps.isEmpty
                        ? const Center(
                            child: Padding(
                              padding: EdgeInsets.all(24),
                              child: Text(
                                'Your agent\'s steps will appear here live.',
                                style: TextStyle(color: LindaTheme.muted),
                                textAlign: TextAlign.center,
                              ),
                            ),
                          )
                        : ListView.builder(
                            controller: scrollController,
                            padding: const EdgeInsets.symmetric(
                              horizontal: 12,
                              vertical: 4,
                            ),
                            itemCount: _steps.length,
                            itemBuilder: (context, i) {
                              final s = _steps[i];
                              return _StepCard(step: s);
                            },
                          ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final running = _taskId != null;
    return Column(
      children: [
        Expanded(
          child: ListView.builder(
            controller: _scroll,
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 8),
            itemCount: _messages.length,
            itemBuilder: (context, i) {
              final m = _messages[i];
              return _MessageBubble(
                msg: m,
                speaking: _speakingIndex == i,
                onSpeak: () => _speakMessage(i),
              );
            },
          ),
        ),
        if (_pendingApproval != null)
          _ApprovalCard(approval: _pendingApproval!, onDecide: _decideApproval),
        for (final p in _pendingCredentials)
          _SecureCredentialCard(
            api: widget.api,
            pending: p,
            onSaved: _checkMessagingPending,
            onDismiss: () => _dismissPending(p),
          ),
        if (_steps.isNotEmpty || running)
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 0, 12, 6),
            child: Align(
              alignment: Alignment.centerLeft,
              child: ActionChip(
                avatar: const LindaIcon('list', size: 18),
                label: Text(
                  'Live steps (${_steps.length}) — tap to view',
                ),
                onPressed: _openStepsSheet,
                backgroundColor: LindaTheme.glassStrong,
              ),
            ),
          ),
        if (_listening)
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 4, 12, 6),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
              decoration: BoxDecoration(
                color: LindaTheme.glassStrong,
                borderRadius: BorderRadius.circular(999),
                border: Border.all(color: Colors.white, width: 0.75),
              ),
              child: const Row(
                mainAxisSize: MainAxisSize.min,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  LindaIcon('mic', size: 16),
                  SizedBox(width: 7),
                  Flexible(
                    child: Text(
                      'Listening… speak — tap the mic again to stop',
                      style: TextStyle(fontSize: 13),
                      textAlign: TextAlign.center,
                    ),
                  ),
                ],
              ),
            ),
          ),
        _Composer(
          controller: _input,
          running: running,
          sending: _sending,
          listening: _listening,
          onSend: _send,
          onStop: _stop,
          onMic: _toggleMic,
        ),
      ],
    );
  }
}

class _MessageBubble extends StatelessWidget {
  const _MessageBubble({
    required this.msg,
    required this.onSpeak,
    required this.speaking,
  });

  final _ChatMsg msg;
  final VoidCallback onSpeak;
  final bool speaking;

  @override
  Widget build(BuildContext context) {
    final isUser = msg.role == 'user';
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Row(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Flexible(
            child: Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: Stack(
                clipBehavior: Clip.none,
                children: [
                  Container(
                    constraints: BoxConstraints(
                      maxWidth: MediaQuery.of(context).size.width * 0.86,
                    ),
                    padding: const EdgeInsets.symmetric(
                      horizontal: 13,
                      vertical: 10,
                    ),
                    decoration: BoxDecoration(
                      gradient: isUser ? LindaTheme.userBubbleGradient : null,
                      color: isUser ? null : LindaTheme.agentBubble,
                      borderRadius: BorderRadius.only(
                        topLeft: const Radius.circular(18),
                        topRight: const Radius.circular(18),
                        bottomLeft: Radius.circular(isUser ? 18 : 5),
                        bottomRight: Radius.circular(isUser ? 5 : 18),
                      ),
                      border: Border.all(color: Colors.white, width: 0.75),
                      boxShadow: const [
                        BoxShadow(
                          color: Color(0x145A6EA0),
                          blurRadius: 2,
                          offset: Offset(0, 1),
                        ),
                        BoxShadow(
                          color: Color(0x1F5A6EA0),
                          blurRadius: 16,
                          offset: Offset(0, 4),
                        ),
                      ],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (msg.isWorking)
                          const Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              SizedBox(
                                width: 14,
                                height: 14,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                ),
                              ),
                              SizedBox(width: 8),
                              Flexible(child: Text('Working…')),
                            ],
                          )
                        else
                          Text(
                            msg.text,
                            style: TextStyle(
                              color: msg.isError
                                  ? LindaTheme.danger
                                  : LindaTheme.text,
                            ),
                          ),
                        if (msg.isWorking && msg.stepLine != null) ...[
                          const SizedBox(height: 4),
                          Text(
                            msg.stepLine!,
                            style: const TextStyle(
                              color: LindaTheme.muted,
                              fontSize: 13,
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                  // Speaker badge on finished agent messages (tap to hear
                  // it) — overlaps the bubble's bottom-right corner so it
                  // reads as part of the message, not a floating circle.
                  if (!isUser && !msg.isWorking)
                    Positioned(
                      right: -8,
                      bottom: 2,
                      child: Container(
                        width: 30,
                        height: 30,
                        decoration: BoxDecoration(
                          gradient: speaking
                              ? LindaTheme.accentGradient
                              : null,
                          color: speaking
                              ? null
                              : Colors.white.withValues(alpha: 0.92),
                          shape: BoxShape.circle,
                          border: Border.all(color: Colors.white, width: 0.75),
                          boxShadow: const [
                            BoxShadow(
                              color: Color(0x335A6EA0),
                              blurRadius: 12,
                              offset: Offset(0, 4),
                            ),
                          ],
                        ),
                        child: InkWell(
                          onTap: onSpeak,
                          customBorder: const CircleBorder(),
                          child: Center(
                            child: speaking
                                ? const LindaIcon(
                                    'speaker',
                                    size: 17,
                                    color: Colors.white,
                                  )
                                : const LindaIcon('speaker', size: 17),
                          ),
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ApprovalCard extends StatelessWidget {
  const _ApprovalCard({required this.approval, required this.onDecide});

  final PendingApproval approval;
  final void Function(bool approve) onDecide;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.fromLTRB(12, 0, 12, 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFFFFBEB),
        border: Border.all(color: const Color(0xFFF59E0B)),
        borderRadius: BorderRadius.circular(18),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Approval needed',
            style: TextStyle(fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 4),
          Text(
            '${approval.action} — ${approval.detail}',
            style: const TextStyle(color: LindaTheme.muted, fontSize: 13),
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: FilledButton(
                  onPressed: () => onDecide(true),
                  style: FilledButton.styleFrom(
                    backgroundColor: LindaTheme.green,
                  ),
                  child: const Text('Approve'),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: FilledButton(
                  onPressed: () => onDecide(false),
                  style: FilledButton.styleFrom(
                    backgroundColor: LindaTheme.danger,
                  ),
                  child: const Text('Reject'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

/// Secure credential box (v0.7) — rendered in the chat when the user
/// enables WhatsApp/Instagram auto-reply and a token/ID is missing.
/// Masked password inputs; the token is pasted here once, never as a
/// chat message. Values are never logged or shown back.
class _SecureCredentialCard extends StatefulWidget {
  const _SecureCredentialCard({
    required this.api,
    required this.pending,
    required this.onSaved,
    required this.onDismiss,
  });

  final ApiClient api;
  final MessagingPending pending;
  final VoidCallback onSaved;
  final VoidCallback onDismiss;

  @override
  State<_SecureCredentialCard> createState() => _SecureCredentialCardState();
}

class _SecureCredentialCardState extends State<_SecureCredentialCard> {
  // Field labels + hints: [label, hint]. Same wording as the PWA.
  static const Map<String, Map<String, List<String>>> _meta = {
    'whatsapp': {
      'token': [
        'WhatsApp access token',
        'Meta dashboard → WhatsApp → API Setup → permanent token (create it via a System User).',
      ],
      'target_id': [
        'WhatsApp phone number ID',
        'Find it in Meta dashboard → WhatsApp → API Setup.',
      ],
      'verify_token': [
        'Verify token',
        'Make up any secret string — enter the same string when verifying the webhook in the Meta dashboard.',
      ],
      'app_secret': [
        'App secret (optional)',
        'Meta app → Settings → Basic → App Secret. Used to check webhook signatures.',
      ],
    },
    'instagram': {
      'token': [
        'Instagram access token (Page token)',
        'Access token of the linked Facebook Page.',
      ],
      'target_id': [
        'Facebook Page ID',
        'ID of the Facebook Page linked to Instagram.',
      ],
      'verify_token': [
        'Verify token',
        'Make up any secret string — enter the same string when verifying the webhook in the Meta dashboard.',
      ],
      'app_secret': [
        'App secret (optional)',
        'Meta app → Settings → Basic → App Secret. Used to check webhook signatures.',
      ],
    },
  };
  static const _order = ['token', 'target_id', 'verify_token', 'app_secret'];

  final Map<String, TextEditingController> _controllers = {};
  bool _saving = false;
  String? _error;
  String? _doneMessage;

  @override
  void initState() {
    super.initState();
    for (final field in _orderedFields) {
      _controllers[field] = TextEditingController();
    }
  }

  @override
  void dispose() {
    for (final c in _controllers.values) {
      c.dispose();
    }
    super.dispose();
  }

  List<String> get _orderedFields => _order
      .where((f) => widget.pending.fields.contains(f))
      .toList();

  String get _name =>
      widget.pending.platform == 'whatsapp' ? 'WhatsApp' : 'Instagram';

  Future<void> _save() async {
    final values = <String, String>{};
    for (final entry in _controllers.entries) {
      final v = entry.value.text.trim();
      if (v.isNotEmpty) values[entry.key] = v;
    }
    if (values.isEmpty) {
      setState(() => _error = 'Enter something first — all fields are empty.');
      return;
    }
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      final result = await widget.api.saveMessagingCredentials(
        widget.pending.platform,
        values,
      );
      if (!mounted) return;
      // Clear the inputs (values must not linger in the widgets).
      for (final c in _controllers.values) {
        c.clear();
      }
      setState(() {
        _saving = false;
        _doneMessage = result.message;
      });
      widget.onSaved(); // anything still missing gets a fresh card
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _saving = false;
        _error = e.toString();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final meta = _meta[widget.pending.platform] ?? const {};
    return Container(
      margin: const EdgeInsets.fromLTRB(12, 0, 12, 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFEEF2FF), Color(0xFFFDF4FF), Color(0xFFFFF7ED)],
        ),
        border: Border.all(color: const Color(0xFFC7D2FE)),
        borderRadius: BorderRadius.circular(18),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const LindaIcon('lock', size: 18),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  '$_name setup — secure box',
                  style: const TextStyle(fontWeight: FontWeight.w700),
                ),
              ),
              IconButton(
                icon: const LindaIcon('close', size: 18),
                onPressed: widget.onDismiss,
                tooltip: 'Close',
              ),
            ],
          ),
          if (_doneMessage != null)
            Text(_doneMessage!)
          else ...[
            const Text(
              'Paste the token here — this is not a chat message, and the '
              'token will never be shown (it stays masked). Auto-reply '
              'starts as soon as you save.',
              style: TextStyle(color: LindaTheme.muted, fontSize: 13),
            ),
            const SizedBox(height: 8),
            for (final field in _orderedFields) ...[
              Text(
                (meta[field]?[0] ?? field),
                style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 4),
              TextField(
                controller: _controllers[field],
                obscureText: field != 'target_id',
                autocorrect: false,
                decoration: InputDecoration(
                  hintText: field == 'app_secret'
                      ? 'Optional — you can leave it blank'
                      : null,
                ),
              ),
              if ((meta[field]?[1] ?? '').isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(top: 2, bottom: 8),
                  child: Text(
                    meta[field]![1],
                    style: const TextStyle(
                      color: LindaTheme.muted,
                      fontSize: 12,
                    ),
                  ),
                ),
            ],
            if (_error != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Text(
                  _error!,
                  style: const TextStyle(color: LindaTheme.danger),
                ),
              ),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: _saving ? null : _save,
                style: FilledButton.styleFrom(
                  backgroundColor: LindaTheme.green,
                ),
                child: Text(
                  _saving ? 'Saving…' : 'Save — turn on auto-reply',
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _Composer extends StatelessWidget {
  const _Composer({
    required this.controller,
    required this.running,
    required this.sending,
    required this.listening,
    required this.onSend,
    required this.onStop,
    required this.onMic,
  });

  final TextEditingController controller;
  final bool running;
  final bool sending;
  final bool listening;
  final VoidCallback onSend;
  final VoidCallback onStop;
  final VoidCallback onMic;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.fromLTRB(
        12,
        10,
        12,
        10 + MediaQuery.of(context).padding.bottom,
      ),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.45),
        border: const Border(top: BorderSide(color: Colors.white, width: 0.75)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Expanded(
            child: TextField(
              controller: controller,
              minLines: 1,
              maxLines: 4,
              textInputAction: TextInputAction.send,
              onSubmitted: (_) => onSend(),
              decoration: InputDecoration(
                hintText: 'Tell Linda what to do…',
                hintStyle: const TextStyle(color: Color(0xFF94A3C8)),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(24),
                ),
                contentPadding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 11,
                ),
              ),
            ),
          ),
          const SizedBox(width: 8),
          // Mic button: tap to talk instead of typing. The hero detail —
          // the custom orbit-mic glyph, same size and shape as the send
          // button. While listening it turns red with a white glyph.
          Container(
            decoration: BoxDecoration(
              gradient: listening
                  ? const LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [Color(0xFFFCA5A5), Color(0xFFF87171)],
                    )
                  : const LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [Color(0xF5FFFFFF), Color(0xEBE9E2FD)],
                    ),
              shape: BoxShape.circle,
              border: Border.all(color: Colors.white, width: 0.75),
              boxShadow: [
                BoxShadow(
                  color: LindaTheme.accent.withValues(alpha: 0.28),
                  blurRadius: 14,
                  offset: const Offset(0, 4),
                ),
                BoxShadow(
                  color: LindaTheme.accent.withValues(alpha: 0.10),
                  blurRadius: 0,
                  spreadRadius: 3,
                ),
              ],
            ),
            child: IconButton(
              onPressed: onMic,
              tooltip: listening ? 'Stop listening' : 'Speak to type',
              icon: listening
                  ? const LindaIcon('mic', size: 26, color: Colors.white)
                  : const LindaIcon('mic', size: 26),
            ),
          ),
          const SizedBox(width: 8),
          if (running)
            FloatingActionButton.small(
              heroTag: 'stop',
              onPressed: onStop,
              backgroundColor: LindaTheme.danger,
              child: const LindaIcon('stop', size: 20, color: Colors.white),
            ),
          if (running) const SizedBox(width: 8),
          Container(
            decoration: BoxDecoration(
              gradient: LindaTheme.accentGradient,
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: LindaTheme.accent.withValues(alpha: 0.4),
                  blurRadius: 12,
                  offset: const Offset(0, 4),
                ),
                BoxShadow(
                  color: LindaTheme.accent.withValues(alpha: 0.3),
                  blurRadius: 3,
                  offset: const Offset(0, 1),
                ),
              ],
            ),
            child: IconButton(
              onPressed: (running || sending) ? null : onSend,
              icon: const LindaIcon('send', size: 21, color: Colors.white),
            ),
          ),
        ],
      ),
    );
  }
}

class _StepCard extends StatelessWidget {
  const _StepCard({required this.step});

  final TaskStep step;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(11),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '#${step.n} ${step.action}',
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
            if (step.thought.isNotEmpty) ...[
              const SizedBox(height: 2),
              Text(
                step.thought,
                style: const TextStyle(color: LindaTheme.muted, fontSize: 12),
              ),
            ],
            if (step.result.isNotEmpty) ...[
              const SizedBox(height: 6),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: const Color(0xFFF1F5FF),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: const Color(0xFFE0E7FF)),
                ),
                child: Text(step.result, style: const TextStyle(fontSize: 12)),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
