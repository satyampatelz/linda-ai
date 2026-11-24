import 'dart:convert';

import 'package:http/http.dart' as http;

import 'storage.dart';

/// Error the UI can show as-is (already a short Hinglish message).
class ApiException implements Exception {
  ApiException(this.message, {this.statusCode});

  final String message;
  final int? statusCode;

  bool get isAuthError => statusCode == 401;

  @override
  String toString() => message;
}

// ---------------------------------------------------------------------------
// Models — mirror the FastAPI JSON exactly (see backend/app/main.py).
// ---------------------------------------------------------------------------

class TaskStep {
  TaskStep({
    required this.n,
    required this.action,
    required this.thought,
    required this.result,
  });

  factory TaskStep.fromJson(Map<String, dynamic> j) {
    return TaskStep(
      n: (j['n'] as num?)?.toInt() ?? 0,
      action: (j['action'] as String?) ?? '',
      thought: (j['thought'] as String?) ?? '',
      result: (j['result'] as String?) ?? '',
    );
  }

  final int n;
  final String action;
  final String thought;
  final String result;
}

class PendingApproval {
  PendingApproval({required this.action, required this.detail});

  factory PendingApproval.fromJson(Map<String, dynamic> j) {
    return PendingApproval(
      action: (j['action'] as String?) ?? '',
      detail: (j['detail'] as String?) ?? '',
    );
  }

  final String action;
  final String detail;
}

/// One saved chat message (v0.9 — the transcript the server keeps so
/// the chat survives closing and reopening the app).
class ChatHistoryMessage {
  ChatHistoryMessage({required this.role, required this.text});

  factory ChatHistoryMessage.fromJson(Map<String, dynamic> j) {
    return ChatHistoryMessage(
      role: (j['role'] as String?) ?? '',
      text: (j['text'] as String?) ?? '',
    );
  }

  final String role; // user | agent
  final String text;
}

class LindaTask {
  LindaTask({
    required this.id,
    required this.message,
    required this.status,
    required this.steps,
    required this.result,
    required this.error,
    required this.createdAt,
    required this.pendingApproval,
  });

  factory LindaTask.fromJson(Map<String, dynamic> j) {
    return LindaTask(
      id: (j['id'] as String?) ?? '',
      message: (j['message'] as String?) ?? '',
      status: (j['status'] as String?) ?? '',
      steps: ((j['steps'] as List?) ?? [])
          .map((s) => TaskStep.fromJson(s as Map<String, dynamic>))
          .toList(),
      result: j['result'] as String?,
      error: j['error'] as String?,
      createdAt: (j['created_at'] as String?) ?? '',
      pendingApproval: j['pending_approval'] == null
          ? null
          : PendingApproval.fromJson(
              j['pending_approval'] as Map<String, dynamic>,
            ),
    );
  }

  final String id;
  final String message;
  final String status; // running | waiting_approval | done | error | stopped
  final List<TaskStep> steps;
  final String? result;
  final String? error;
  final String createdAt;
  final PendingApproval? pendingApproval;

  bool get isFinished =>
      status == 'done' || status == 'error' || status == 'stopped';
}

class HealthCheck {
  HealthCheck({
    required this.id,
    required this.label,
    required this.status,
    required this.detail,
    required this.hint,
  });

  factory HealthCheck.fromJson(Map<String, dynamic> j) {
    return HealthCheck(
      id: (j['id'] as String?) ?? '',
      label: (j['label'] as String?) ?? '',
      status: (j['status'] as String?) ?? '',
      detail: (j['detail'] as String?) ?? '',
      hint: (j['hint'] as String?) ?? '',
    );
  }

  final String id;
  final String label;
  final String status; // ok | fail | skip
  final String detail;
  final String hint;
}

class AppSettings {
  AppSettings({
    required this.modelProvider,
    required this.ollamaModel,
    required this.geminiModel,
    required this.geminiKeySet,
    required this.geminiKeyMasked,
    required this.approvalMode,
    required this.browserHeadless,
    required this.maxAgentSteps,
    // No messaging fields (v0.7): WhatsApp/Instagram auto-reply is
    // controlled by talking to Linda in chat; tokens live in .env only.
  });

  factory AppSettings.fromJson(Map<String, dynamic> j) {
    return AppSettings(
      modelProvider: (j['model_provider'] as String?) ?? 'ollama',
      ollamaModel: (j['ollama_model'] as String?) ?? '',
      geminiModel: (j['gemini_model'] as String?) ?? '',
      geminiKeySet: (j['gemini_key_set'] as bool?) ?? false,
      geminiKeyMasked: (j['gemini_api_key_masked'] as String?) ?? '',
      approvalMode: (j['approval_mode'] as String?) ?? 'auto',
      browserHeadless: (j['browser_headless'] as bool?) ?? false,
      maxAgentSteps: (j['max_agent_steps'] as num?)?.toInt() ?? 15,
    );
  }

  final String modelProvider;
  final String ollamaModel;
  final String geminiModel;
  final bool geminiKeySet;
  final String geminiKeyMasked;
  final String approvalMode;
  final bool browserHeadless;
  final int maxAgentSteps;
}

/// A pending secure-box credential request (v0.7): the user enabled a
/// messaging platform in chat, and these fields are still missing. Only
/// field NAMES come over the wire — never any secret value.
class MessagingPending {
  MessagingPending({required this.platform, required this.fields});

  factory MessagingPending.fromJson(Map<String, dynamic> j) {
    return MessagingPending(
      platform: (j['platform'] as String?) ?? '',
      fields: ((j['fields'] as List?) ?? [])
          .map((f) => f.toString())
          .toList(),
    );
  }

  final String platform; // whatsapp | instagram
  final List<String> fields; // token | target_id | verify_token | app_secret

  String get key => '$platform:${[...fields]..sort()}';
}

/// Result of saving credentials from the secure box.
class CredentialsResult {
  CredentialsResult({
    required this.enabled,
    required this.stillMissing,
    required this.message,
  });

  factory CredentialsResult.fromJson(Map<String, dynamic> j) {
    return CredentialsResult(
      enabled: (j['enabled'] as bool?) ?? false,
      stillMissing: ((j['still_missing'] as List?) ?? [])
          .map((f) => f.toString())
          .toList(),
      message: (j['message'] as String?) ?? 'Saved.',
    );
  }

  final bool enabled;
  final List<String> stillMissing;
  final String message;
}

// ---------------------------------------------------------------------------
// Client — same endpoints the PWA uses, nothing else.
// ---------------------------------------------------------------------------

class ApiClient {
  ApiClient(ServerConfig config) : _config = config;

  ServerConfig _config;

  String get baseUrl => _config.baseUrl;

  void updateConfig(ServerConfig config) {
    _config = config;
  }

  Map<String, String> get _headers {
    final headers = <String, String>{'Content-Type': 'application/json'};
    if (_config.apiToken.isNotEmpty) {
      headers['Authorization'] = 'Bearer ${_config.apiToken}';
    }
    return headers;
  }

  Uri _uri(String path) {
    final base = _config.baseUrl.endsWith('/')
        ? _config.baseUrl.substring(0, _config.baseUrl.length - 1)
        : _config.baseUrl;
    return Uri.parse('$base$path');
  }

  dynamic _decode(http.Response resp) {
    final body = resp.body.isEmpty ? '{}' : resp.body;
    final data = jsonDecode(body);
    if (resp.statusCode >= 400) {
      final detail = (data is Map && data['detail'] is String)
          ? data['detail'] as String
          : 'Server error (${resp.statusCode}).';
      throw ApiException(detail, statusCode: resp.statusCode);
    }
    return data;
  }

  Future<dynamic> _get(String path) async {
    try {
      final resp = await http
          .get(_uri(path), headers: _headers)
          .timeout(const Duration(seconds: 20));
      return _decode(resp);
    } on ApiException {
      rethrow;
    } catch (_) {
      throw ApiException(
        "Can't reach the server — is it running? "
        'Check the Server URL in Settings.',
      );
    }
  }

  Future<dynamic> _post(String path, [Map<String, dynamic>? body]) async {
    try {
      final resp = await http
          .post(
            _uri(path),
            headers: _headers,
            body: body == null ? null : jsonEncode(body),
          )
          .timeout(const Duration(seconds: 30));
      return _decode(resp);
    } on ApiException {
      rethrow;
    } catch (_) {
      throw ApiException(
        "Can't reach the server — is it running? "
        'Check the Server URL in Settings.',
      );
    }
  }

  Future<Map<String, dynamic>> getHealth() async {
    final data = await _get('/health');
    return data as Map<String, dynamic>;
  }

  Future<(bool, List<HealthCheck>)> getHealthDetailed() async {
    final data = await _get('/health/detailed') as Map<String, dynamic>;
    final checks = ((data['checks'] as List?) ?? [])
        .map((c) => HealthCheck.fromJson(c as Map<String, dynamic>))
        .toList();
    return (data['all_ok'] as bool? ?? false, checks);
  }

  Future<AppSettings> getSettings() async {
    final data = await _get('/settings');
    return AppSettings.fromJson(data as Map<String, dynamic>);
  }

  Future<void> updateSettings(Map<String, dynamic> values) async {
    await _post('/settings', values);
  }

  Future<String> startChat(String message) async {
    final data = await _post('/chat', {'message': message});
    final taskId = (data as Map<String, dynamic>)['task_id'] as String?;
    if (taskId == null || taskId.isEmpty) {
      throw ApiException("Couldn't start the task.");
    }
    return taskId;
  }

  /// Saved chat transcript, oldest first (v0.9). Empty list when the
  /// server has no history yet — the chat just starts with the
  /// welcome bubble.
  Future<List<ChatHistoryMessage>> getChatHistory() async {
    final data = await _get('/chat/history') as Map<String, dynamic>;
    return ((data['messages'] as List?) ?? [])
        .map((m) => ChatHistoryMessage.fromJson(m as Map<String, dynamic>))
        .toList();
  }

  Future<LindaTask> getTask(String taskId) async {
    final data = await _get('/tasks/$taskId');
    return LindaTask.fromJson(data as Map<String, dynamic>);
  }

  Future<List<LindaTask>> getTasks() async {
    final data = await _get('/tasks') as Map<String, dynamic>;
    return ((data['tasks'] as List?) ?? [])
        .map((t) => LindaTask.fromJson(t as Map<String, dynamic>))
        .toList();
  }

  Future<void> approveTask(String taskId, bool approve) async {
    await _post('/tasks/$taskId/approve', {'approve': approve});
  }

  Future<void> stopTask(String taskId) async {
    await _post('/tasks/$taskId/stop');
  }

  Future<List<MessagingPending>> getMessagingPending() async {
    final data = await _get('/messaging/pending') as Map<String, dynamic>;
    return ((data['pending'] as List?) ?? [])
        .map((p) => MessagingPending.fromJson(p as Map<String, dynamic>))
        .toList();
  }

  Future<CredentialsResult> saveMessagingCredentials(
    String platform,
    Map<String, String> values,
  ) async {
    final data = await _post('/messaging/credentials', {
      'platform': platform,
      'values': values,
    });
    return CredentialsResult.fromJson(data as Map<String, dynamic>);
  }
}
