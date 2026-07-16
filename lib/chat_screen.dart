import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'app_theme.dart';
import 'chat_message.dart';
import 'chat_bubble.dart';
import 'typing_indicator.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  // Point this at your running Mist Core backend.
  // - Android emulator talking to your own computer: 10.0.2.2
  // - Physical phone on the same wifi as your computer: your computer's LAN IP (e.g. 192.168.1.42)
  // - iOS simulator: localhost works fine
  static const String _backendUrl = 'http://192.168.1.135:8000/chat';

  final List<ChatMessage> _messages = [];
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final FocusNode _focusNode = FocusNode();
  bool _isSending = false;

  bool get _hasStartedChat => _messages.isNotEmpty;

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  void _showComingSoon() {
    ScaffoldMessenger.of(context).hideCurrentSnackBar();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: const Text('This feature is coming soon.'),
        backgroundColor: MistColors.bgSurface,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        margin: const EdgeInsets.all(16),
        duration: const Duration(seconds: 2),
      ),
    );
  }

  Future<void> _sendMessage() async {
    final text = _controller.text.trim();
    if (text.isEmpty || _isSending) return;

    setState(() {
      _messages.add(
        ChatMessage(role: MessageRole.user, content: text, timestamp: DateTime.now()),
      );
      _isSending = true;
    });
    _controller.clear();
    _scrollToBottom();

    String reply;
    try {
      final response = await http
          .post(
            Uri.parse(_backendUrl),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'message': text, 'session_id': 'default'}),
          )
          .timeout(const Duration(seconds: 20));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        reply = data['reply'] as String;
      } else {
        reply = "Something went wrong on my end. Can you try that again?";
      }
    } catch (e) {
      reply = "I couldn't reach my thinking core just now. Check that the "
          "backend is running and the address in the app is correct.";
    }

    if (!mounted) return;
    setState(() {
      _messages.add(
        ChatMessage(role: MessageRole.assistant, content: reply, timestamp: DateTime.now()),
      );
      _isSending = false;
    });
    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent + 120,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: MistColors.bgDeep,
      body: Stack(
        children: [
          // Ambient background glow behind everything.
          Positioned.fill(
            child: DecoratedBox(
              decoration: BoxDecoration(
                gradient: RadialGradient(
                  center: const Alignment(0, -0.6),
                  radius: 1.3,
                  colors: [
                    MistColors.bgSurface.withOpacity(0.55),
                    MistColors.bgDeep,
                  ],
                ),
              ),
            ),
          ),
          SafeArea(
            child: Column(
              children: [
                _buildHeader(),
                Expanded(
                  child: _hasStartedChat ? _buildMessageList() : _buildGreeting(),
                ),
                _buildInputBar(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.only(top: 10, bottom: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.baseline,
        textBaseline: TextBaseline.alphabetic,
        children: [
          Text(
            'MIST',
            style: AppTheme.displayFont.copyWith(
              fontSize: 22,
              color: MistColors.textPrimary,
              letterSpacing: 6,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(width: 8),
          Text(
            '0.1',
            style: AppTheme.displayFont.copyWith(
              fontSize: 12,
              color: MistColors.teal,
              letterSpacing: 1,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildGreeting() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              'Hey there,',
              style: TextStyle(
                color: MistColors.textMuted,
                fontSize: 20,
                fontWeight: FontWeight.w400,
              ),
            ),
            const SizedBox(height: 6),
            ShaderMask(
              shaderCallback: (bounds) => const LinearGradient(
                colors: [MistColors.violet, MistColors.teal],
              ).createShader(bounds),
              child: Text(
                'Ibrahim A. Ameen',
                textAlign: TextAlign.center,
                style: AppTheme.displayFont.copyWith(
                  fontSize: 30,
                  color: Colors.white,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMessageList() {
    final itemCount = _messages.length + (_isSending ? 1 : 0);
    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.symmetric(vertical: 12),
      itemCount: itemCount,
      itemBuilder: (context, index) {
        if (index == _messages.length) {
          return const TypingIndicator();
        }
        return ChatBubble(message: _messages[index]);
      },
    );
  }

  Widget _buildInputBar() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(14, 6, 14, 14),
      child: Container(
        padding: const EdgeInsets.fromLTRB(14, 10, 14, 10),
        decoration: BoxDecoration(
          color: MistColors.bgSurface,
          borderRadius: BorderRadius.circular(26),
          border: Border.all(color: MistColors.violet.withOpacity(0.22)),
          boxShadow: [
            BoxShadow(
              color: MistColors.violet.withOpacity(0.08),
              blurRadius: 24,
              offset: const Offset(0, 8),
            ),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            TextField(
              controller: _controller,
              focusNode: _focusNode,
              style: const TextStyle(color: MistColors.textPrimary, fontSize: 15.5),
              maxLines: 6,
              minLines: 1,
              textInputAction: TextInputAction.newline,
              decoration: InputDecoration(
                hintText: 'Message Mist…',
                hintStyle: TextStyle(color: MistColors.textMuted.withOpacity(0.7)),
                border: InputBorder.none,
                isCollapsed: true,
              ),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                _CircleIconButton(icon: Icons.add_rounded, onTap: _showComingSoon),
                const SizedBox(width: 8),
                Text(
                  'Morningstar 7',
                  style: TextStyle(
                    color: MistColors.textMuted,
                    fontSize: 12.5,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const Spacer(),
                _CircleIconButton(icon: Icons.mic_none_rounded, onTap: _showComingSoon),
                const SizedBox(width: 8),
                _CircleIconButton(
                  icon: Icons.arrow_upward_rounded,
                  onTap: _sendMessage,
                  isPrimary: true,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _CircleIconButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback onTap;
  final bool isPrimary;

  const _CircleIconButton({
    required this.icon,
    required this.onTap,
    this.isPrimary = false,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 38,
        height: 38,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          gradient: isPrimary
              ? const LinearGradient(colors: [MistColors.violet, MistColors.violetDeep])
              : null,
          color: isPrimary ? null : MistColors.bgDeep,
          border: isPrimary ? null : Border.all(color: MistColors.violet.withOpacity(0.3)),
        ),
        child: Icon(
          icon,
          size: 19,
          color: isPrimary ? Colors.white : MistColors.textPrimary,
        ),
      ),
    );
  }
}
