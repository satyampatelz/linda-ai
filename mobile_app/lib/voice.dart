import 'package:flutter_tts/flutter_tts.dart';
import 'package:speech_to_text/speech_recognition_error.dart';
import 'package:speech_to_text/speech_recognition_result.dart';
import 'package:speech_to_text/speech_to_text.dart';

/// Voice for the Satyam app — mic input + spoken replies, fully
/// client-side and free (Android's on-device/Google speech services).
/// No API key, no server cost, no backend change.
///
/// Behaviour mirrors the PWA:
/// - Mic: tap to talk; the transcript lands in the composer for editing
///   and is NEVER auto-sent. Tap again (or pause) to stop.
/// - Speaker icon on agent messages: tap to hear that reply aloud.
/// - Auto-speak (Settings, default OFF): every finished reply is read
///   aloud automatically. Stop / a new message silences it.
class VoiceService {
  VoiceService();

  final SpeechToText _stt = SpeechToText();
  final FlutterTts _tts = FlutterTts();

  bool _sttReady = false;
  bool _sttTriedInit = false;
  bool _ttsReady = false;
  bool _speaking = false;
  bool _stopRequested = false;

  /// Current listener-error handler (set by startListening; the
  /// recognizer reports errors through initialize's callback only).
  void Function(String message)? _onSttError;

  bool get isListening => _stt.isListening;
  bool get isSpeaking => _speaking;

  /// One-time TTS setup: Indian English voice when available, calm rate.
  Future<void> _initTts() async {
    if (_ttsReady) return;
    _ttsReady = true; // even if setup partially fails, don't retry forever
    try {
      await _tts.setSpeechRate(0.95);
      await _tts.setPitch(1.0);
      await _tts.setLanguage('en-IN');
      await _tts.awaitSpeakCompletion(true);
      // Prefer an en-IN voice when the device has one.
      final voices = await _tts.getVoices;
      if (voices is List) {
        for (final v in voices) {
          if (v is Map &&
              (v['locale'] as String?)?.toLowerCase().startsWith('en-in') ==
                  true) {
            await _tts.setVoice({
              'name': v['name'] as String,
              'locale': v['locale'] as String,
            });
            break;
          }
        }
      }
    } catch (_) {
      // TTS is a bonus: the app must work fine without it.
    }
  }

  /// Initialise speech recognition (asks for mic permission on first
  /// use). Returns true when listening is possible on this device.
  Future<bool> initSpeech() async {
    if (_sttReady) return true;
    if (_sttTriedInit) return false;
    _sttTriedInit = true;
    try {
      _sttReady = await _stt.initialize(
        onError: _handleSttError,
        onStatus: (_) {},
      );
    } catch (_) {
      _sttReady = false;
    }
    return _sttReady;
  }

  void _handleSttError(SpeechRecognitionError e) {
    final handler = _onSttError;
    if (handler == null) return;
    if (e.errorMsg == 'error_no_match') {
      handler("Didn't catch that — tap the mic and speak again.");
    } else if (e.errorMsg == 'error_permission') {
      handler(
        'Mic permission denied — allow the mic for Satyam in your phone Settings → Apps → Satyam → Permissions.',
      );
    }
  }

  /// Start listening. [onTranscript] gets the live/final text (the
  /// caller puts it in the composer); [onError] gets a user-facing
  /// Hinglish message when something goes wrong.
  Future<void> startListening({
    required void Function(String text, bool isFinal) onTranscript,
    required void Function(String message) onError,
  }) async {
    await stopSpeaking(); // don't talk over the user
    _onSttError = onError;
    final available = await initSpeech();
    if (!available) {
      onError('Voice input is not available on this phone.');
      return;
    }
    if (!await _stt.hasPermission) {
      onError(
        'Mic permission denied — allow the mic for Satyam in your phone Settings → Apps → Satyam → Permissions.',
      );
      return;
    }
    // en-IN first: it handles English + Hinglish well. If the device
    // has no en-IN recognizer, fall back to hi-IN, then the default.
    String? localeId;
    try {
      final locales = await _stt.locales();
      for (final l in locales) {
        if (l.localeId.toLowerCase().startsWith('en-in')) {
          localeId = l.localeId;
          break;
        }
      }
      if (localeId == null) {
        for (final l in locales) {
          if (l.localeId.toLowerCase().startsWith('hi-in')) {
            localeId = l.localeId;
            break;
          }
        }
      }
    } catch (_) {
      localeId = null;
    }
    try {
      await _stt.listen(
        onResult: (SpeechRecognitionResult result) {
          onTranscript(result.recognizedWords, result.finalResult);
        },
        listenOptions: SpeechListenOptions(
          localeId: localeId,
          listenMode: ListenMode.confirmation,
          partialResults: true,
          cancelOnError: true,
          listenFor: const Duration(seconds: 60),
          pauseFor: const Duration(seconds: 3),
        ),
      );
    } catch (_) {
      onError("Couldn't start voice input — try again.");
    }
  }

  Future<void> stopListening() async {
    try {
      await _stt.stop();
    } catch (_) {}
  }

  Future<void> cancelListening() async {
    try {
      await _stt.cancel();
    } catch (_) {}
  }

  /// Read [text] aloud. Code blocks are skipped (nobody wants code
  /// read aloud); long replies are chunked into sentences so Stop
  /// works promptly. [onDone] fires when speaking finishes or stops.
  Future<void> speak(String text, {void Function()? onDone}) async {
    await stopSpeaking();
    await _initTts();
    final clean = cleanForSpeech(text);
    if (clean.isEmpty) {
      onDone?.call();
      return;
    }
    _speaking = true;
    _stopRequested = false;
    try {
      for (final chunk in _chunks(clean)) {
        if (_stopRequested) break;
        await _tts.speak(chunk);
      }
    } catch (_) {
      // A failed utterance just ends the speech; nothing breaks.
    } finally {
      _speaking = false;
      onDone?.call();
    }
  }

  Future<void> stopSpeaking() async {
    _stopRequested = true;
    if (!_speaking) return;
    try {
      await _tts.stop();
    } catch (_) {}
    _speaking = false;
  }

  /// Strip markdown/code/URLs so replies sound natural when spoken.
  static String cleanForSpeech(String text) {
    return text
        .replaceAll(RegExp(r'```[\s\S]*?```'), ' ')
        .replaceAll(RegExp(r'`([^`]*)`'), r'$1')
        .replaceAll(RegExp(r'[*_#>-]'), ' ')
        .replaceAll(RegExp(r'https?://\S+'), ' ')
        .replaceAll(RegExp(r'\s+'), ' ')
        .trim();
  }

  /// Split into sentence-sized chunks (<= ~300 chars each).
  static List<String> _chunks(String text) {
    final sentences = RegExp(r'[^.!?\n]+[.!?]+|[^.!?\n]+$')
        .allMatches(text)
        .map((m) => m.group(0)!.trim())
        .where((s) => s.isNotEmpty)
        .toList();
    final chunks = <String>[];
    var current = StringBuffer();
    for (final s in sentences) {
      if (current.length + s.length > 300 && current.isNotEmpty) {
        chunks.add(current.toString());
        current = StringBuffer();
      }
      current.write(s);
      current.write(' ');
    }
    if (current.isNotEmpty) chunks.add(current.toString().trim());
    return chunks.isEmpty ? [text] : chunks;
  }

  Future<void> dispose() async {
    try {
      await _stt.cancel();
    } catch (_) {}
    try {
      await _tts.stop();
    } catch (_) {}
  }
}
