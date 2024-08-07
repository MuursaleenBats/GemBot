import 'dart:ui';
import 'dart:io';
import 'dart:math' as math;
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import "package:record/record.dart";
import "package:http/http.dart" as http;
import 'dart:convert';
import 'dart:developer';
import 'dart:async';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen>
    with SingleTickerProviderStateMixin {
  TextEditingController _controller = TextEditingController();
  List<Map<String, String>> _chatMessages = [];
  bool _showWelcomeMessage = true;
  bool _isListening = false;
  Timer? _statusCheckTimer;
  Timer? _listeningTimer;
  late AnimationController _welcomeAnimationController;
  late Animation<double> _fadeAnimation;
  late Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _startStatusCheck();

    // Initialize welcome animation
    _welcomeAnimationController = AnimationController(
      vsync: this,
      duration: Duration(seconds: 2),
    );

    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(
        parent: _welcomeAnimationController,
        curve: Interval(0.0, 0.5, curve: Curves.easeIn),
      ),
    );

    _scaleAnimation = Tween<double>(begin: 0.8, end: 1.0).animate(
      CurvedAnimation(
        parent: _welcomeAnimationController,
        curve: Interval(0.5, 1.0, curve: Curves.easeOut),
      ),
    );

    // Start the animation
    _welcomeAnimationController.forward();
  }

  @override
  void dispose() {
    _statusCheckTimer?.cancel();
    _listeningTimer?.cancel();
    _welcomeAnimationController.dispose();
    super.dispose();
  }

  void _startStatusCheck() {
    _statusCheckTimer = Timer.periodic(Duration(seconds: 5), (timer) {
      _checkStatus();
    });
  }

  Future<void> _checkStatus() async {
    final response = await http.get(Uri.parse('http://localhost:5000/status'));
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      if (data.containsKey('command') && data.containsKey('response')) {
        setState(() {
          if (!_chatMessages
              .any((message) => message['prompt'] == data['command'])) {
            _chatMessages
                .add({'prompt': data['command'], 'response': data['response']});
          }
          _isListening = false;
          _showWelcomeMessage = false;
        });
      } else if (data['status'] == "Listening for command...") {
        setState(() {
          _isListening = true;
          _listeningTimer?.cancel();
          _listeningTimer = Timer(Duration(seconds: 5), () {
            setState(() {
              _isListening = false;
            });
          });
        });
      }
    }
  }

  bool _isWaitingForResponse = false;

  Future<void> _sendCommand(String command) async {
    setState(() {
      if (command != "mic") {
        // Immediately add the user's command to the chat
        _chatMessages.add({'prompt': command, 'response': '...'});
        _isWaitingForResponse = true;
      }
      _showWelcomeMessage = false;
    });
    _controller.clear();
    final response = await http.post(
      Uri.parse('http://localhost:5000/command'),
      headers: <String, String>{
        'Content-Type': 'application/json; charset=UTF-8',
      },
      body: jsonEncode(<String, String>{
        'command': command,
      }),
    );

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      print('Response data: ${data["result"]}');
      setState(() {
        if (command == "mic") {
          // For voice commands, we'll wait for the backend to send both command and response
        } else {
          // Update the response for the command we just sent
          _chatMessages.last['response'] = data["result"];
        }
        _isWaitingForResponse = false;
      });
    } else {
      print("Failed to send command");
      setState(() {
        if (command != "mic") {
          _chatMessages.last['response'] = "Failed to get response";
        }
        _isWaitingForResponse = false;
      });
    }
  }

  void _navigateToAboutUs() {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => AboutUsPage()),
    );
  }

  void _navigateToSettings() {
    // Implement settings navigation here
  }

  @override
  Widget build(BuildContext context) {
    double screenWidth = MediaQuery.of(context).size.width;
    double textFormFieldWidth = screenWidth * 0.75;
    return Scaffold(
      backgroundColor: Color(0xFF1E1E1E),
      body: Stack(
        children: [
          Column(
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  IconButton(
                    onPressed: () => showDialog(
                      context: context,
                      builder: (BuildContext context) {
                        return AlertDialog(
                          title: Text(
                            "Guide",
                          ),
                          content: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(
                                "1. ",
                                textAlign: TextAlign.left,
                                style: TextStyle(
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                              Text(
                                "2. ",
                                textAlign: TextAlign.left,
                                style: TextStyle(
                                  fontWeight: FontWeight.w600,
                                ),
                              )
                            ],
                          ),
                          actions: [
                            TextButton(
                              child: const Text('Ok'),
                              style: ButtonStyle(
                                  backgroundColor: MaterialStateProperty.all(
                                      Color(0xFF1E1E1E)),
                                  foregroundColor: MaterialStateProperty.all(
                                      Color(0x95FFFFFF))),
                              onPressed: () {
                                Navigator.of(context).pop();
                              },
                            ),
                          ],
                        );
                      },
                    ),
                    splashRadius: 20.0,
                    splashColor: Color(0xffffa500),
                    icon: Icon(
                      Icons.info,
                      color: Color(0x50FFFFFF),
                      size: 30.0, // Increased icon size
                    ),
                  ),
                  Row(
                    children: [
                      Row(
                        children: [
                          IconButton(
                            onPressed: _navigateToAboutUs,
                            splashRadius: 20.0,
                            splashColor: Color(0xffffa500),
                            icon: Icon(
                              Icons.people,
                              color: Color(0x50FFFFFF),
                              size: 30.0, // Increased icon size
                            ),
                          ),
                          SizedBox(width: 5.0), // Increased padding
                          MouseRegion(
                            cursor: SystemMouseCursors.click,
                            onEnter: (event) => setState(() {
                              _isHoveringAboutUs = true;
                            }),
                            onExit: (event) => setState(() {
                              _isHoveringAboutUs = false;
                            }),
                            child: Text(
                              "About Us",
                              style: TextStyle(
                                color: _isHoveringAboutUs
                                    ? Colors.white
                                    : Color(0x50FFFFFF),
                                fontSize: 14.0, // Reduced text size
                              ),
                            ),
                          ),
                        ],
                      ),
                      SizedBox(width: 20.0), // Increased padding
                      Row(
                        children: [
                          IconButton(
                            onPressed: _navigateToSettings,
                            splashRadius: 20.0,
                            splashColor: Color(0xffffa500),
                            icon: Icon(
                              Icons.settings,
                              color: Color(0x50FFFFFF),
                              size: 30.0, // Increased icon size
                            ),
                          ),
                          SizedBox(width: 5.0), // Increased padding
                          MouseRegion(
                            cursor: SystemMouseCursors.click,
                            onEnter: (event) => setState(() {
                              _isHoveringSettings = true;
                            }),
                            onExit: (event) => setState(() {
                              _isHoveringSettings = false;
                            }),
                            child: Text(
                              "Settings",
                              style: TextStyle(
                                color: _isHoveringSettings
                                    ? Colors.white
                                    : Color(0x50FFFFFF),
                                fontSize: 14.0, // Reduced text size
                              ),
                            ),
                          ),
                          SizedBox(width: 10.0)
                        ],
                      ),
                    ],
                  ),
                ],
              ),
              Expanded(
                child: _showWelcomeMessage
                    ? Center(
                        child: AnimatedBuilder(
                          animation: _welcomeAnimationController,
                          builder: (context, child) {
                            return Opacity(
                              opacity: _fadeAnimation.value,
                              child: Transform.scale(
                                scale: _scaleAnimation.value,
                                child: Column(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    Padding(
                                      padding: const EdgeInsets.symmetric(
                                          horizontal: 40.0, vertical: 20.0),
                                      child: Image.asset(
                                        'assets/logo.gif',
                                        height: 300.0, // 100.0 * 1.2
                                        width: 300.0, // 100.0 * 1.2
                                      ),
                                    ),
                                    Text(
                                      "Welcome to WinAuto",
                                      style: TextStyle(
                                          color: Color(0x90FFFFFF),
                                          fontSize: 30.0,
                                          fontWeight: FontWeight.bold,
                                          shadows: <Shadow>[
                                            Shadow(
                                              offset: Offset(5.0, 5.0),
                                              blurRadius: 3.0,
                                              color:
                                                  Color.fromARGB(255, 0, 0, 0),
                                            ),
                                          ]),
                                    ),
                                  ],
                                ),
                              ),
                            );
                          },
                        ),
                      )
                    : ListView.builder(
                        padding: EdgeInsets.all(10.0),
                        itemCount: _chatMessages.length,
                        itemBuilder: (context, index) {
                          final message = _chatMessages[index];
                          return Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Align(
                                alignment: Alignment.centerRight,
                                child: Container(
                                  decoration: BoxDecoration(
                                    color: Color(0xFF3A3A3A),
                                    border:
                                        Border.all(color: Color(0xffffffff)),
                                    borderRadius: BorderRadius.circular(10.0),
                                  ),
                                  padding: EdgeInsets.all(10.0),
                                  margin: EdgeInsets.only(bottom: 10.0),
                                  child: Text(
                                    "${message['prompt']}",
                                    style: TextStyle(color: Colors.white),
                                  ),
                                ),
                              ),
                              Align(
                                alignment: Alignment.centerLeft,
                                child: Container(
                                  decoration: BoxDecoration(
                                    color: Color(0xFF2A2A2A),
                                    border:
                                        Border.all(color: Color(0x90FFFFFF)),
                                    borderRadius: BorderRadius.circular(10.0),
                                  ),
                                  padding: EdgeInsets.all(10.0),
                                  margin: EdgeInsets.only(bottom: 10.0),
                                  child: message['response'] == '...'
                                      ? LoadingDots()
                                      : Text(
                                          "${message['response']}",
                                          style:
                                              TextStyle(color: Colors.white70),
                                        ),
                                ),
                              ),
                            ],
                          );
                        },
                      ),
              ),
              Padding(
                padding: const EdgeInsets.symmetric(
                    horizontal: 40.0, vertical: 30.0),
                child: Container(
                  width: textFormFieldWidth,
                  child: TextFormField(
                    controller: _controller,
                    decoration: InputDecoration(
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.all(Radius.circular(30.0)),
                        borderSide: BorderSide(color: Color(0x90FFFFFF)),
                      ),
                      enabledBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.all(Radius.circular(30.0)),
                        borderSide: BorderSide(color: Color(0x90FFFFFF)),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.all(Radius.circular(30.0)),
                        borderSide: BorderSide(color: Colors.white),
                      ),
                      prefixIcon: IconButton(
                        onPressed: () => _sendCommand("mic"),
                        splashRadius: 20.0,
                        icon: Icon(
                          Icons.mic,
                          color: Color(0x90FFFFFF),
                        ),
                      ),
                      suffixIcon: Padding(
                        padding: const EdgeInsets.all(8.0),
                        child: Ink(
                          decoration: const ShapeDecoration(
                            color: Colors.white,
                            shape: CircleBorder(),
                          ),
                          child: IconButton(
                            onPressed: () => _sendCommand(_controller.text),
                            splashRadius: 20.0,
                            icon: Icon(
                              Icons.upload_rounded,
                              color: Color.fromARGB(144, 7, 7, 7),
                            ),
                          ),
                        ),
                      ),
                      hintText: "Enter Prompt",
                      hintStyle: TextStyle(color: Color(0x90FFFFFF)),
                    ),
                    cursorColor: Colors.white,
                    style: TextStyle(color: Colors.white),
                  ),
                ),
              )
            ],
          ),
          if (_isListening)
            BackdropFilter(
              filter: ImageFilter.blur(sigmaX: 5, sigmaY: 5),
              child: Container(
                color: Colors.black.withOpacity(0.5),
                child: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      ListeningIndicator(),
                      SizedBox(height: 20),
                      Text(
                        "Listening for command...",
                        style: TextStyle(color: Colors.white, fontSize: 24),
                      ),
                    ],
                  ),
                ),
              ),
            )
        ],
      ),
    );
  }

  bool _isHoveringAboutUs = false;
  bool _isHoveringSettings = false;
}

class ListeningIndicator extends StatefulWidget {
  @override
  _ListeningIndicatorState createState() => _ListeningIndicatorState();
}

class _ListeningIndicatorState extends State<ListeningIndicator>
    with TickerProviderStateMixin {
  late AnimationController _waveController;
  late AnimationController _glowController;

  @override
  void initState() {
    super.initState();
    _waveController = AnimationController(
      vsync: this,
      duration: Duration(seconds: 3),
    )..repeat();
    _glowController = AnimationController(
      vsync: this,
      duration: Duration(seconds: 1),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _waveController.dispose();
    _glowController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: Listenable.merge([_waveController, _glowController]),
      builder: (context, child) {
        return Container(
          width: 100,
          height: 100,
          child: CustomPaint(
            painter: WaveBorderPainter(
              wavePhase: _waveController.value,
              glowIntensity: _glowController.value,
            ),
          ),
        );
      },
    );
  }
}

class WaveBorderPainter extends CustomPainter {
  final double wavePhase;
  final double glowIntensity;

  WaveBorderPainter({required this.wavePhase, required this.glowIntensity});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.blue.withOpacity(0.5 + glowIntensity * 0.5)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 5
      ..maskFilter = MaskFilter.blur(BlurStyle.normal, 3 * glowIntensity);

    final path = Path();
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2;

    for (double i = 0; i < 360; i += 1) {
      final radians = i * (math.pi / 180);
      final waveOffset =
          math.sin((radians * 3) + (wavePhase * 2 * math.pi)) * 1.5;
      final x = center.dx + (radius + waveOffset) * math.cos(radians);
      final y = center.dy + (radius + waveOffset) * math.sin(radians);

      if (i == 0) {
        path.moveTo(x, y);
      } else {
        path.lineTo(x, y);
      }
    }
    path.close();

    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}

class AboutUsPage extends StatelessWidget {
  final List<Map<String, String>> users = [
    {
      'name': 'John Doe',
      'role': 'Developer',
      'image': 'assets/user1.png',
    },
    {
      'name': 'Jane Smith',
      'role': 'Designer',
      'image': 'assets/user2.png',
    },
    {
      'name': 'Alice Johnson',
      'role': 'Tester',
      'image': 'assets/user3.png',
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('About Us'),
        backgroundColor: Color(0xFF1E1E1E),
      ),
      backgroundColor: Color(0xFF1E1E1E),
      body: ListView.builder(
        itemCount: users.length,
        itemBuilder: (context, index) {
          final user = users[index];
          return Card(
            color: Color(0xFF3A3A3A),
            margin: EdgeInsets.all(10.0),
            child: ListTile(
              leading: CircleAvatar(
                backgroundImage: AssetImage(user['image']!),
              ),
              title: Text(
                user['name']!,
                style: TextStyle(color: Colors.white),
              ),
              subtitle: Text(
                user['role']!,
                style: TextStyle(color: Colors.white70),
              ),
            ),
          );
        },
      ),
    );
  }
}

class LoadingDots extends StatefulWidget {
  @override
  _LoadingDotsState createState() => _LoadingDotsState();
}

class _LoadingDotsState extends State<LoadingDots>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: Duration(milliseconds: 600),
    )..repeat();
    _animation = Tween<double>(begin: 0.0, end: 1.0).animate(_controller);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: List.generate(3, (index) {
        return AnimatedBuilder(
          animation: _animation,
          builder: (context, child) {
            return Opacity(
              opacity: (index == 0)
                  ? _animation.value
                  : (index == 1)
                      ? (_animation.value > 0.5 ? 1.0 : 0.0)
                      : (_animation.value > 0.8 ? 1.0 : 0.0),
              child: Container(
                width: 8.0,
                height: 8.0,
                margin: EdgeInsets.symmetric(horizontal: 4.0),
                decoration: BoxDecoration(
                  color: Colors.white70,
                  shape: BoxShape.circle,
                ),
              ),
            );
          },
        );
      }),
    );
  }
}
