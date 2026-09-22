import 'package:flutter_test/flutter_test.dart';

import 'package:flutter_influencer_app/main.dart';

void main() {
  testWidgets('Rmworkz Influencer app loads', (WidgetTester tester) async {
    await tester.pumpWidget(const InfluencerApp());

    expect(find.text('Rmworkz'), findsOneWidget);
    expect(find.text('INFLUENCER PLATFORM'), findsOneWidget);
    expect(find.text('Influencer Sign In'), findsOneWidget);
    expect(find.text('Sign In'), findsOneWidget);
  });
}