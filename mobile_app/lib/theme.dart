import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

/// Linda "Light Colourful" design — the same palette as the PWA
/// (backend/static/style.css): a smooth pastel flow (sky blue ->
/// periwinkle -> lavender -> lilac-rose -> peach -> warm cream), soft
/// ambient glows, glossy translucent white glass bubbles, gradient
/// accents, dark navy text. Light throughout.
///
/// v0.5: every icon is a custom hand-drawn SVG path (assets/icons/),
/// drawn for this app — no Material Icons, no icon fonts, no emoji.
/// The same paths are inlined in the PWA.
class LindaTheme {
  LindaTheme._();

  static const Color text = Color(0xFF1E2A4A);
  static const Color muted = Color(0xFF5F6F92);
  static const Color accent = Color(0xFF7C6CF0);
  static const Color green = Color(0xFF16A34A);
  static const Color danger = Color(0xFFDC2626);
  static const Color amber = Color(0xFFB45309);

  /// Page background: sky -> periwinkle -> lavender -> lilac-rose ->
  /// peach -> warm cream.
  static const LinearGradient bgGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [
      Color(0xFFD6ECFD),
      Color(0xFFDDE6FD),
      Color(0xFFE9E1FC),
      Color(0xFFF6E3F2),
      Color(0xFFFDE7D3),
      Color(0xFFFDF0D8),
    ],
  );

  /// Accent gradient: sky -> violet -> orange (logo, send button).
  static const LinearGradient accentGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xFF38BDF8), Color(0xFFA78BFA), Color(0xFFFB923C)],
  );

  /// User chat bubble gradient.
  static const LinearGradient userBubbleGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xFFD3EAFD), Color(0xFFE6DEFC)],
  );

  static const Color agentBubble = Color(0xD1FFFFFF);
  static const Color glass = Color(0x9EFFFFFF);
  static const Color glassStrong = Color(0xDBFFFFFF);

  static ThemeData light() {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      scaffoldBackgroundColor: Colors.transparent,
      colorScheme: const ColorScheme.light(
        primary: accent,
        secondary: Color(0xFFA78BFA),
        surface: Colors.white,
        error: danger,
        onPrimary: Colors.white,
        onSurface: text,
      ),
      textTheme: const TextTheme(
        bodyMedium: TextStyle(color: text, fontSize: 15),
        bodySmall: TextStyle(color: muted, fontSize: 13),
        titleLarge: TextStyle(
          color: text,
          fontSize: 18,
          fontWeight: FontWeight.w700,
        ),
        titleMedium: TextStyle(
          color: text,
          fontSize: 15,
          fontWeight: FontWeight.w700,
        ),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        titleTextStyle: TextStyle(
          color: text,
          fontSize: 18,
          fontWeight: FontWeight.w700,
        ),
        iconTheme: IconThemeData(color: text),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFFDBE4F5)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFFDBE4F5)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: accent, width: 1.5),
        ),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 12,
          vertical: 12,
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: accent,
          foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          padding: const EdgeInsets.symmetric(vertical: 14),
        ),
      ),
      cardTheme: CardThemeData(
        color: glassStrong,
        elevation: 2,
        shadowColor: const Color(0x235A6EA0),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
          side: const BorderSide(color: Colors.white, width: 0.75),
        ),
      ),
    );
  }
}

/// Full-screen pastel gradient + soft colour glows, matching the PWA.
class LindaBackground extends StatelessWidget {
  const LindaBackground({required this.child, super.key});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(gradient: LindaTheme.bgGradient),
      child: Stack(
        children: [
          Positioned(
            top: -60,
            right: -40,
            child: Container(
              width: 220,
              height: 220,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: const Color(0x47FBBF24),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0x47FBBF24),
                    blurRadius: 60,
                    spreadRadius: 30,
                  ),
                ],
              ),
            ),
          ),
          Positioned(
            bottom: -40,
            left: -60,
            child: Container(
              width: 240,
              height: 240,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: const Color(0x4D38BDF8),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0x4D38BDF8),
                    blurRadius: 60,
                    spreadRadius: 30,
                  ),
                ],
              ),
            ),
          ),
          Positioned(
            top: MediaQuery.of(context).size.height * 0.45,
            right: -90,
            child: Container(
              width: 220,
              height: 220,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: const Color(0x3DA78BFA),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0x3DA78BFA),
                    blurRadius: 60,
                    spreadRadius: 30,
                  ),
                ],
              ),
            ),
          ),
          child,
        ],
      ),
    );
  }
}

/// A custom hand-drawn Linda icon (v0.5) — an SVG asset from
/// assets/icons/, drawn for this app. No Material Icons, no emoji.
/// The same paths are inlined in the PWA (backend/static/).
///
/// With no [color], the icon renders with its own gradient (or its
/// built-in colours for check/error/skip). With [color] set, the whole
/// glyph is tinted that colour — used for white glyphs on gradient/red
/// buttons and for muted unselected tab icons.
class LindaIcon extends StatelessWidget {
  const LindaIcon(this.name, {this.size = 22, this.color, super.key});

  /// Icon file name without extension, e.g. 'mic', 'speaker', 'gear'.
  final String name;

  final double size;

  final Color? color;

  @override
  Widget build(BuildContext context) {
    return SvgPicture.asset(
      'assets/icons/$name.svg',
      width: size,
      height: size,
      colorFilter: color == null
          ? null
          : ColorFilter.mode(color!, BlendMode.srcIn),
    );
  }
}

/// The gradient "S" logo mark.
class LindaLogo extends StatelessWidget {
  const LindaLogo({this.size = 38, super.key});

  final double size;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        gradient: LindaTheme.accentGradient,
        borderRadius: BorderRadius.circular(size * 0.32),
        boxShadow: [
          BoxShadow(
            color: LindaTheme.accent.withValues(alpha: 0.35),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      alignment: Alignment.center,
      child: Text(
        'S',
        style: TextStyle(
          color: Colors.white,
          fontSize: size * 0.58,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
  }
}
