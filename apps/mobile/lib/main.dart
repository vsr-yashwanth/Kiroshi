import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'core/constants/app_colors.dart';
import 'application/auth_state.dart';
import 'application/trip_state.dart';
import 'presentation/screens/login_screen.dart';
import 'presentation/screens/trip_list_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const KiroshiApp());
}

class KiroshiApp extends StatelessWidget {
  const KiroshiApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthState()..initAuth()),
        ChangeNotifierProvider(create: (_) => TripState()),
      ],
      child: Consumer<AuthState>(
        builder: (context, authState, _) {
          return MaterialApp(
            title: 'KIROSHI',
            debugShowCheckedModeBanner: false,
            theme: ThemeData.dark().copyWith(
              scaffoldBackgroundColor: AppColors.background,
              primaryColor: AppColors.primary,
              colorScheme: const ColorScheme.dark(
                primary: AppColors.primary,
                secondary: AppColors.primaryLight,
                surface: AppColors.surface,
                background: AppColors.background,
              ),
            ),
            home: authState.isAuthenticated
                ? const TripListScreen()
                : const LoginScreen(),
          );
        },
      ),
    );
  }
}
