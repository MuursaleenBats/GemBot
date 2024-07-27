// import 'dart:ui';

// import 'package:flutter/cupertino.dart';
// import 'package:flutter/material.dart';
// import 'package:flutter/src/widgets/container.dart';
// import 'package:flutter/src/widgets/framework.dart';
// import "package:http/http.dart" as http;
// import 'dart:convert';

// class HomeScreen extends StatefulWidget {
//   const HomeScreen({super.key});

//   @override
//   State<HomeScreen> createState() => _HomeScreenState();
// }

// class _HomeScreenState extends State<HomeScreen> {
//   TextEditingController _controller = TextEditingController();

//   Future<void> _sendCommand(String command) async {
//     final response = await http.post(
//       Uri.parse('http://localhost:5000/command'),
//       headers: <String, String>{
//         'Content-Type': 'application/json; charset=UTF-8',
//       },
//       body: jsonEncode(<String, String>{
//         'command': command,
//       }),
//     );

//     if (response.statusCode == 200) {
//       // If the server returns an OK response, parse the JSON
//       print('Response data: ${response.body}');
//     } else {
//       // If the server did not return a 200 OK response,
//       // throw an exception.
//       throw Exception('Failed to send command');
//     }
//     _controller.clear();
//   }

//   @override
//   Widget build(BuildContext context) {
//     double screenWidth = MediaQuery.of(context).size.width;
//     double textFormFieldWidth = screenWidth * 0.75;
//     return Scaffold(
//       backgroundColor: Color(0xFF1E1E1E),
//       body: Column(
//         children: [
//           Row(
//             children: [
//               IconButton(
//                 onPressed: () => showDialog(
//                   context: context,
//                   builder: (BuildContext context) {
//                     return AlertDialog(
//                       title: Text(
//                         "Guide",
//                       ),
//                       content: Column(
//                         crossAxisAlignment: CrossAxisAlignment.start,
//                         mainAxisSize: MainAxisSize.min,
//                         children: [
//                           Text(
//                             "1. ",
//                             textAlign: TextAlign.left,
//                             style: TextStyle(
//                               fontWeight: FontWeight.w600,
//                             ),
//                           ),
//                           Text(
//                             "2. ",
//                             textAlign: TextAlign.left,
//                             style: TextStyle(
//                               fontWeight: FontWeight.w600,
//                             ),
//                           )
//                         ],
//                       ),
//                       actions: [
//                         TextButton(
//                           child: const Text('Ok'),
//                           style: ButtonStyle(
//                               backgroundColor:
//                                   MaterialStateProperty.all(Color(0xFF1E1E1E)),
//                               foregroundColor:
//                                   MaterialStateProperty.all(Color(0x95FFFFFF))),
//                           onPressed: () {
//                             Navigator.of(context).pop();
//                           },
//                         ),
//                       ],
//                     );
//                   },
//                 ),
//                 splashRadius: 20.0,
//                 splashColor: Color(0xffffa500),
//                 icon: Icon(
//                   Icons.info,
//                   color: Color(0x50FFFFFF),
//                 ),
//               ),
//             ],
//           ),
//           Expanded(
//             child: Center(
//               child: Column(
//                 mainAxisAlignment: MainAxisAlignment.center,
//                 children: [
//                   Padding(
//                     padding: const EdgeInsets.symmetric(
//                         horizontal: 40.0, vertical: 20.0),
//                     child: Image.asset(
//                       'assets/logo.jpg',
//                       height: 100.0,
//                       width: 100.0,
//                     ),
//                   ),
//                   Text(
//                     "Welcome to WinAuto",
//                     style: TextStyle(
//                       color: Color(0x90FFFFFF),
//                       fontSize: 30.0,
//                       fontWeight: FontWeight.bold,
//                     ),
//                   ),
//                 ],
//               ),
//             ),
//           ),
//           Padding(
//             padding:
//                 const EdgeInsets.symmetric(horizontal: 40.0, vertical: 30.0),
//             child: Container(
//               width: textFormFieldWidth,
//               child: TextFormField(
//                 controller: _controller,
//                 decoration: InputDecoration(
//                   border: OutlineInputBorder(
//                     borderRadius: BorderRadius.all(Radius.circular(30.0)),
//                     borderSide: BorderSide(color: Color(0x90FFFFFF)),
//                   ),
//                   enabledBorder: OutlineInputBorder(
//                     borderRadius: BorderRadius.all(Radius.circular(30.0)),
//                     borderSide: BorderSide(color: Color(0x90FFFFFF)),
//                   ),
//                   focusedBorder: OutlineInputBorder(
//                     borderRadius: BorderRadius.all(Radius.circular(30.0)),
//                     borderSide: BorderSide(color: Colors.white),
//                   ),
//                   prefixIcon: IconButton(
//                     onPressed: () => _sendCommand("mic"),
//                     splashRadius: 20.0,
//                     icon: Icon(
//                       Icons.mic,
//                       color: Color(0x90FFFFFF),
//                     ),
//                   ),
//                   suffixIcon: Padding(
//                     padding: const EdgeInsets.all(8.0),
//                     child: Ink(
//                       decoration: const ShapeDecoration(
//                         color: Colors.white,
//                         shape: CircleBorder(),
//                       ),
//                       child: IconButton(
//                         onPressed: () => _sendCommand(_controller.text),
//                         splashRadius: 20.0,
//                         icon: Icon(
//                           Icons.upload_rounded,
//                           color: Color.fromARGB(144, 7, 7, 7),
//                         ),
//                       ),
//                     ),
//                   ),
//                   hintText: "Enter Prompt",
//                   hintStyle: TextStyle(color: Color(0x90FFFFFF)),
//                 ),
//                 cursorColor: Colors.white,
//                 style: TextStyle(color: Colors.white),
//               ),
//             ),
//           )
//         ],
//       ),
//     );
//   }
// }

import 'dart:ui';

import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import "package:http/http.dart" as http;
import 'dart:convert';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  TextEditingController _controller = TextEditingController();
  List<Map<String, String>> _chatMessages = [];
  bool _showWelcomeMessage = true;

  Future<void> _sendCommand(String command) async {
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
      print('Response data: ${response.body}');
      setState(() {
        _chatMessages.add({'prompt': command, 'response': response.body});
        _showWelcomeMessage = false;
      });
    } else {
      throw Exception('Failed to send command');
    }
    _controller.clear();
  }

  @override
  Widget build(BuildContext context) {
    double screenWidth = MediaQuery.of(context).size.width;
    double textFormFieldWidth = screenWidth * 0.75;
    return Scaffold(
      backgroundColor: Color(0xFF1E1E1E),
      body: Column(
        children: [
          Row(
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
                              backgroundColor:
                                  MaterialStateProperty.all(Color(0xFF1E1E1E)),
                              foregroundColor:
                                  MaterialStateProperty.all(Color(0x95FFFFFF))),
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
                ),
              ),
            ],
          ),
          Expanded(
            child: _showWelcomeMessage
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Padding(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 40.0, vertical: 20.0),
                          child: Image.asset(
                            'assets/logo.jpg',
                            height: 100.0,
                            width: 100.0,
                          ),
                        ),
                        Text(
                          "Welcome to WinAuto",
                          style: TextStyle(
                            color: Color(0x90FFFFFF),
                            fontSize: 30.0,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
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
                                border: Border.all(color: Color(0xffffffff)),
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
                                border: Border.all(color: Color(0x90FFFFFF)),
                                borderRadius: BorderRadius.circular(10.0),
                              ),
                              padding: EdgeInsets.all(10.0),
                              margin: EdgeInsets.only(bottom: 10.0),
                              child: Text(
                                "${message['response']}",
                                style: TextStyle(color: Colors.white70),
                              ),
                            ),
                          ),
                        ],
                      );
                    },
                  ),
          ),
          Padding(
            padding:
                const EdgeInsets.symmetric(horizontal: 40.0, vertical: 30.0),
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
    );
  }
}
