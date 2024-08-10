import 'package:flutter/material.dart';
import 'package:winauto/screens/home_screen.dart';
import 'package:window_manager/window_manager.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized(); //Must be called
  await windowManager.ensureInitialized(); //Must be called
  //waitUntilReadyToShow ==> Optional method to use, requires modification of native runner - Read docs of the package.
  await windowManager.waitUntilReadyToShow().then((_) async {
    await windowManager
        .setTitleBarStyle(TitleBarStyle.hidden); //Hiding the titlebar
    await windowManager.show(); //Finally show app window.
  });
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      home: Scaffold(
        body: Column(
          children: [
            MyCustomTitleBar(), // Add the custom title bar
            Expanded(child: HomeScreen()),
          ],
        ),
      ),
    );
  }
}

class MyCustomTitleBar extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      height: 40,
      padding: const EdgeInsets.symmetric(horizontal: 10),
      // color: Color(0xff1e1e1e), // Change to your preferred color
      decoration: BoxDecoration(
        color: Color(0x95FFFFFF), // Background color
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.5), // Shadow color
            offset: Offset(0, 5), // Offset of the shadow
            blurRadius: 6, // Blur radius
            spreadRadius: 1, // Spread radius
          ),
        ],
      ),
      child: Row(
        children: [
          Image.asset(
            'windows/runner/resources/logo.ico', // Path to your .ico file
            width: 24,
            height: 24,
          ),
          const SizedBox(width: 10),
          const Text(
            'GemBot',
            style: TextStyle(
              color: Color(0xff1e1e1e),
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          const Spacer(),
          IconButton(
            icon: const Icon(Icons.fullscreen, color: Colors.black),
            onPressed: () async {
              if (await windowManager.isFullScreen()) {
                await windowManager.setFullScreen(false); // Exit fullscreen
              } else {
                await windowManager.setFullScreen(true); // Enter fullscreen
              }
            },
          ),
          IconButton(
            icon: const Icon(Icons.close, color: Colors.black),
            onPressed: () {
              windowManager.close();
            },
          ),
        ],
      ),
    );
  }
}
