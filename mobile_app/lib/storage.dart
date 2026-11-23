import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Server connection details, kept in the phone's secure storage
/// (Android Keystore). Never leaves the device except as the
/// Authorization header to the user's own server.
class ServerConfig {
  ServerConfig({required this.baseUrl, required this.apiToken});

  static const String defaultBaseUrl = 'http://127.0.0.1:8000';

  static const _storage = FlutterSecureStorage();
  static const _urlKey = 'server_url';
  static const _tokenKey = 'api_token';

  final String baseUrl;
  final String apiToken;

  ServerConfig copyWith({String? baseUrl, String? apiToken}) {
    return ServerConfig(
      baseUrl: baseUrl ?? this.baseUrl,
      apiToken: apiToken ?? this.apiToken,
    );
  }

  static Future<ServerConfig> load() async {
    final url = await _storage.read(key: _urlKey);
    final token = await _storage.read(key: _tokenKey);
    return ServerConfig(
      baseUrl: (url == null || url.isEmpty) ? defaultBaseUrl : url,
      apiToken: token ?? '',
    );
  }

  Future<void> save() async {
    await _storage.write(key: _urlKey, value: baseUrl);
    await _storage.write(key: _tokenKey, value: apiToken);
  }
}

/// Voice preferences, kept on this phone only (same secure storage).
/// Auto-speak is OFF by default — the user turns it on in Settings.
class VoicePrefs {
  VoicePrefs._();

  static const _storage = FlutterSecureStorage();
  static const _autoSpeakKey = 'auto_speak';

  static Future<bool> loadAutoSpeak() async {
    try {
      return (await _storage.read(key: _autoSpeakKey)) == '1';
    } catch (_) {
      return false;
    }
  }

  static Future<void> saveAutoSpeak(bool value) async {
    try {
      await _storage.write(key: _autoSpeakKey, value: value ? '1' : '0');
    } catch (_) {}
  }
}
