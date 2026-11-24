import 'package:flutter/material.dart';

import '../api.dart';
import '../storage.dart';
import '../theme.dart';

/// Settings tab — server connection (URL + API token, kept in secure
/// storage) and the same server settings the PWA offers: provider,
/// models, Gemini key, approval mode, browser mode, max steps.
///
/// There is deliberately NO language option: the agent auto-adapts its
/// reply language to whatever the user chats in (English default).
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({
    required this.api,
    required this.config,
    required this.onConfigChanged,
    super.key,
  });

  final ApiClient api;
  final ServerConfig config;
  final void Function(ServerConfig config) onConfigChanged;

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _urlCtrl = TextEditingController();
  final _tokenCtrl = TextEditingController();
  final _ollamaModelCtrl = TextEditingController();
  final _geminiKeyCtrl = TextEditingController();
  final _geminiModelCtrl = TextEditingController();
  final _maxStepsCtrl = TextEditingController();
  // No messaging fields (v0.7): WhatsApp/Instagram auto-reply is
  // controlled by talking to Linda in chat; tokens live in .env only.

  String _provider = 'ollama';
  String _approval = 'auto';
  String _browser = 'visible';
  bool _geminiKeySet = false;
  String _geminiKeyMasked = '';
  bool _loading = true;
  bool _saving = false;
  String? _message;
  bool _messageIsError = false;
  bool _autoSpeak = false; // voice: read replies aloud (default OFF)

  @override
  void initState() {
    super.initState();
    _urlCtrl.text = widget.config.baseUrl;
    _tokenCtrl.text = widget.config.apiToken;
    _load();
    _loadVoicePrefs();
  }

  Future<void> _loadVoicePrefs() async {
    final autoSpeak = await VoicePrefs.loadAutoSpeak();
    if (!mounted) return;
    setState(() => _autoSpeak = autoSpeak);
  }

  Future<void> _setAutoSpeak(bool value) async {
    setState(() => _autoSpeak = value);
    await VoicePrefs.saveAutoSpeak(value);
  }

  @override
  void dispose() {
    _urlCtrl.dispose();
    _tokenCtrl.dispose();
    _ollamaModelCtrl.dispose();
    _geminiKeyCtrl.dispose();
    _geminiModelCtrl.dispose();
    _maxStepsCtrl.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final s = await widget.api.getSettings();
      if (!mounted) return;
      setState(() {
        _provider = s.modelProvider;
        _ollamaModelCtrl.text = s.ollamaModel;
        _geminiModelCtrl.text = s.geminiModel;
        _geminiKeySet = s.geminiKeySet;
        _geminiKeyMasked = s.geminiKeyMasked;
        _approval = s.approvalMode;
        _browser = s.browserHeadless ? 'headless' : 'visible';
        _maxStepsCtrl.text = s.maxAgentSteps.toString();
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _message = e.toString();
        _messageIsError = true;
      });
    }
  }

  Future<void> _save() async {
    final url = _urlCtrl.text.trim();
    if (url.isEmpty) {
      setState(() {
        _message = 'Server URL khaali nahi ho sakta.';
        _messageIsError = true;
      });
      return;
    }
    final maxSteps = int.tryParse(_maxStepsCtrl.text.trim());
    if (maxSteps == null || maxSteps < 1 || maxSteps > 50) {
      setState(() {
        _message = 'Max steps 1 se 50 ke beech hona chahiye.';
        _messageIsError = true;
      });
      return;
    }
    setState(() {
      _saving = true;
      _message = null;
    });

    // Server connection lives in secure storage on this phone only.
    final config = ServerConfig(baseUrl: url, apiToken: _tokenCtrl.text.trim());
    await config.save();
    widget.api.updateConfig(config);
    widget.onConfigChanged(config);

    // The rest goes to the server (same as the PWA).
    final payload = <String, dynamic>{
      'model_provider': _provider,
      'ollama_model': _ollamaModelCtrl.text.trim(),
      'gemini_model': _geminiModelCtrl.text.trim(),
      'approval_mode': _approval,
      'browser_headless': _browser == 'headless',
      'max_agent_steps': maxSteps,
    };
    if (_geminiKeyCtrl.text.trim().isNotEmpty) {
      payload['gemini_api_key'] = _geminiKeyCtrl.text.trim();
    }
    try {
      await widget.api.updateSettings(payload);
      if (!mounted) return;
      setState(() {
        _saving = false;
        _message = 'Settings save ho gaye — bina restart ke lagu ho gaye.';
        _messageIsError = false;
        _geminiKeyCtrl.clear();
      });
      await _load();
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _saving = false;
        _message = e.toString();
        _messageIsError = true;
      });
    }
  }

  Widget _section(String title) {
    return Padding(
      padding: const EdgeInsets.only(top: 18, bottom: 8),
      child: Text(
        title,
        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
      ),
    );
  }

  Widget _fieldLabel(String label, [String? hint]) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 5, top: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
          ),
          if (hint != null) ...[
            const SizedBox(height: 2),
            Text(
              hint,
              style: const TextStyle(color: LindaTheme.muted, fontSize: 12),
            ),
          ],
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
      children: [
        const Text(
          'Sab kuch yahin se badlo — koi file edit karne ki zaroorat nahi. '
          'Save karte hi bina restart ke lagu ho jayega.',
          style: TextStyle(color: LindaTheme.muted, fontSize: 13),
        ),
        _section('Server se connection'),
        _fieldLabel(
          'Server URL',
          'Laptop ke liye http://127.0.0.1:8000 (ya same Wi-Fi pe laptop ka IP). Cloud ke liye https://tumhara-domain',
        ),
        TextField(
          controller: _urlCtrl,
          keyboardType: TextInputType.url,
          autocorrect: false,
          decoration: const InputDecoration(hintText: 'http://127.0.0.1:8000'),
        ),
        _fieldLabel(
          'API token (sirf cloud server ke liye)',
          'Ye token sirf is phone me save hota hai. Cloud server ke .env me jo API_TOKEN hai, wahi daalo.',
        ),
        TextField(
          controller: _tokenCtrl,
          obscureText: true,
          autocorrect: false,
          decoration: const InputDecoration(
            hintText: 'Laptop server pe zaroorat nahi',
          ),
        ),
        _section('Brain — kaunsa model jawab dega?'),
        DropdownButtonFormField<String>(
          initialValue: _provider,
          decoration: const InputDecoration(),
          items: const [
            DropdownMenuItem(
              value: 'ollama',
              child: Text('Ollama — laptop ka local model (free)'),
            ),
            DropdownMenuItem(
              value: 'gemini',
              child: Text('Gemini — Google free-tier API (zyada smart)'),
            ),
          ],
          onChanged: (v) => setState(() => _provider = v ?? 'ollama'),
        ),
        _fieldLabel(
          'Ollama model ka naam',
          'Model pehle download hona chahiye: ollama pull qwen2.5:3b',
        ),
        TextField(controller: _ollamaModelCtrl, autocorrect: false),
        _fieldLabel(
          'Gemini API key (sirf Gemini brain ke liye)',
          'Free key: aistudio.google.com → Get API key (card nahi lagta). Khaali chhodo toh purani key hi rahegi.',
        ),
        TextField(
          controller: _geminiKeyCtrl,
          obscureText: true,
          autocorrect: false,
          decoration: InputDecoration(
            hintText: _geminiKeySet
                ? 'Key set hai: $_geminiKeyMasked'
                : 'Abhi key set nahi hai',
          ),
        ),
        _fieldLabel('Gemini model ka naam'),
        TextField(controller: _geminiModelCtrl, autocorrect: false),
        _section('Agent ka tareeka'),
        _fieldLabel('Approval mode'),
        DropdownButtonFormField<String>(
          initialValue: _approval,
          decoration: const InputDecoration(),
          items: const [
            DropdownMenuItem(
              value: 'auto',
              child: Text('Auto — jo bolo wo seedha karega (default)'),
            ),
            DropdownMenuItem(
              value: 'ask',
              child: Text('Ask — push/submit se pehle poochhega'),
            ),
          ],
          onChanged: (v) => setState(() => _approval = v ?? 'auto'),
        ),
        _fieldLabel('Browser'),
        DropdownButtonFormField<String>(
          initialValue: _browser,
          decoration: const InputDecoration(),
          items: const [
            DropdownMenuItem(
              value: 'visible',
              child: Text('Visible — Chrome screen pe dikhega'),
            ),
            DropdownMenuItem(
              value: 'headless',
              child: Text('Headless — background me chalega'),
            ),
          ],
          onChanged: (v) => setState(() => _browser = v ?? 'visible'),
        ),
        _fieldLabel(
          'Max steps per task (1–50)',
          'Ek task me agent zyada se zyada kitne steps le sakta hai.',
        ),
        TextField(
          controller: _maxStepsCtrl,
          keyboardType: TextInputType.number,
        ),
        _section('Voice — jawab sunai de?'),
        SwitchListTile(
          title: const Text(
            'Auto-speak replies',
            style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
          ),
          subtitle: const Text(
            'Har agent reply apne aap bol ke sunayega. Band ho toh bhi har agent message ke speaker button se kabhi bhi sun sakte ho. Ye setting sirf is phone me save hoti hai.',
            style: TextStyle(color: LindaTheme.muted, fontSize: 12),
          ),
          value: _autoSpeak,
          activeThumbColor: LindaTheme.accent,
          onChanged: _setAutoSpeak,
          contentPadding: EdgeInsets.zero,
        ),
        const SizedBox(height: 20),
        if (_message != null)
          Container(
            padding: const EdgeInsets.all(12),
            margin: const EdgeInsets.only(bottom: 12),
            decoration: BoxDecoration(
              color: _messageIsError
                  ? const Color(0xFFFEE2E2)
                  : const Color(0xFFDCFCE7),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(
                color: _messageIsError
                    ? const Color(0xFFFCA5A5)
                    : const Color(0xFF86EFAC),
              ),
            ),
            child: Text(_message!),
          ),
        FilledButton(
          onPressed: _saving ? null : _save,
          child: Text(_saving ? 'Save ho raha hai…' : 'Save settings'),
        ),
      ],
    );
  }
}
