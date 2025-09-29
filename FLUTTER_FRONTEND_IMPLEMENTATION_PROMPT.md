# Comprehensive Flutter Frontend Implementation Guide for ZODIRA Astrology App

## Overview

This document provides a complete technical specification for implementing all backend-integrated features in the Flutter frontend. The implementation must seamlessly integrate with the recently enhanced backend that includes persistent authentication, AI-powered predictions, and comprehensive marriage matching functionality.

## Backend Integration Summary

### Available API Endpoints

**Base URL**: `http://your-backend-url/api/v1`

#### Authentication Endpoints
- `POST /enhanced/auth/persistent-login` - Validate persistent session
- `POST /enhanced/auth/logout` - Logout with session invalidation
- `GET /enhanced/auth/sessions` - Get user sessions

#### Profile Management
- `POST /enhanced/profiles/{profile_id}/generate-chart` - Generate complete astrology chart
- `GET /enhanced/profiles/{profile_id}/complete` - Get profile with predictions
- `GET /enhanced/profiles/{profile_id}/predictions` - Get profile predictions
- `POST /enhanced/profiles/{profile_id}/predictions/{type}` - Generate specific predictions
- `POST /enhanced/profiles/{profile_id}/refresh-predictions` - Refresh predictions

#### Marriage Matching
- `POST /enhanced/marriage-matching/generate` - Generate compatibility analysis
- `GET /enhanced/marriage-matching/{match_id}` - Get marriage match details
- `GET /enhanced/profiles/{profile_id}/marriage-matches` - Get all marriage matches

#### Dashboard
- `GET /enhanced/dashboard` - Get comprehensive dashboard data

## Implementation Requirements

### 1. Project Structure

```
lib/
├── models/                    # Data models
│   ├── user.dart
│   ├── profile.dart
│   ├── prediction.dart
│   ├── marriage_match.dart
│   └── dashboard.dart
├── services/                  # API services
│   ├── auth_service.dart
│   ├── profile_service.dart
│   ├── prediction_service.dart
│   ├── marriage_service.dart
│   └── api_client.dart
├── providers/                 # State management
│   ├── auth_provider.dart
│   ├── profile_provider.dart
│   ├── dashboard_provider.dart
│   └── marriage_provider.dart
├── screens/                   # UI Screens
│   ├── auth/
│   │   ├── login_screen.dart
│   │   ├── otp_verification_screen.dart
│   │   └── splash_screen.dart
│   ├── profile/
│   │   ├── profile_creation_screen.dart
│   │   ├── profile_list_screen.dart
│   │   └── profile_detail_screen.dart
│   ├── dashboard/
│   │   ├── dashboard_screen.dart
│   │   └── analyzing_screen.dart
│   ├── predictions/
│   │   ├── predictions_screen.dart
│   │   └── prediction_detail_screen.dart
│   ├── marriage/
│   │   ├── marriage_matching_screen.dart
│   │   ├── partner_input_screen.dart
│   │   └── marriage_report_screen.dart
│   └── common/
│       ├── loading_widget.dart
│       └── error_widget.dart
├── widgets/                   # Reusable widgets
│   ├── astrology_chart_widget.dart
│   ├── prediction_card.dart
│   ├── marriage_compatibility_widget.dart
│   └── persistent_login_widget.dart
├── utils/                     # Utilities
│   ├── constants.dart
│   ├── validators.dart
│   └── helpers.dart
└── main.dart
```

### 2. Dependencies Required

Add these to `pubspec.yaml`:

```yaml
dependencies:
  # State Management
  provider: ^6.0.5
  flutter_riverpod: ^2.3.6

  # HTTP & API
  dio: ^5.3.2
  http: ^1.1.0

  # Firebase Integration
  firebase_core: ^2.17.0
  firebase_auth: ^4.8.0
  cloud_firestore: ^4.9.0
  firebase_storage: ^11.2.0

  # Local Storage
  shared_preferences: ^2.2.0
  hive: ^2.2.3
  hive_flutter: ^1.1.0

  # UI & Animation
  lottie: ^2.6.0
  shimmer: ^3.0.0
  cached_network_image: ^3.2.3

  # Date & Time
  intl: ^0.18.1
  persian_datetime_picker: ^2.7.0

  # Other utilities
  uuid: ^4.1.0
  url_launcher: ^6.1.12
  share_plus: ^7.2.1

dev_dependencies:
  # Testing
  flutter_test: sdk: flutter
  integration_test: sdk: flutter

  # Code generation
  build_runner: ^2.4.6
  hive_generator: ^2.0.0
```

## Detailed Implementation Guide

### Phase 1: Authentication & Persistent Login

#### 1.1 Authentication Service (`services/auth_service.dart`)

```dart
class AuthService {
  final Dio _dio;
  final FirebaseAuth _auth;
  final FirebaseFirestore _firestore;
  static const String baseUrl = 'http://your-backend-url/api/v1';

  AuthService(this._dio, this._auth, this._firestore);

  // Persistent session management
  Future<bool> checkPersistentLogin() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final sessionToken = prefs.getString('persistent_session_token');

      if (sessionToken == null) return false;

      final response = await _dio.post(
        '$baseUrl/enhanced/auth/persistent-login',
        options: Options(headers: {'Authorization': 'Bearer $sessionToken'}),
      );

      if (response.statusCode == 200) {
        final data = response.data;
        await _saveAuthData(data);
        return true;
      }
      return false;
    } catch (e) {
      return false;
    }
  }

  Future<AuthResult> loginWithPhone(String phoneNumber) async {
    try {
      final response = await _dio.post(
        '$baseUrl/auth/initiate-auth',
        data: {'identifier': phoneNumber},
      );

      return AuthResult.fromJson(response.data);
    } catch (e) {
      throw Exception('Login failed: $e');
    }
  }

  Future<AuthResult> verifyOTP(String sessionId, String otp) async {
    try {
      final response = await _dio.post(
        '$baseUrl/auth/verify-otp',
        data: {
          'session_id': sessionId,
          'otp_code': otp,
        },
      );

      final result = AuthResult.fromJson(response.data);
      await _saveAuthData(response.data);
      return result;
    } catch (e) {
      throw Exception('OTP verification failed: $e');
    }
  }

  Future<void> logout() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final sessionToken = prefs.getString('persistent_session_token');
      final userId = prefs.getString('user_id');

      if (sessionToken != null && userId != null) {
        await _dio.post(
          '$baseUrl/enhanced/auth/logout',
          queryParameters: {'session_token': sessionToken},
        );
      }

      await _clearAuthData();
    } catch (e) {
      // Even if API call fails, clear local data
      await _clearAuthData();
    }
  }

  Future<void> _saveAuthData(Map<String, dynamic> data) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('access_token', data['access_token']);
    await prefs.setString('user_id', data['user_id']);
    await prefs.setString('persistent_session_token', data['persistent_session_token']);
    await prefs.setString('user_data', json.encode(data['user_data']));
  }

  Future<void> _clearAuthData() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.clear();
  }
}
```

#### 1.2 Authentication Provider (`providers/auth_provider.dart`)

```dart
class AuthProvider extends ChangeNotifier {
  final AuthService _authService;
  User? _currentUser;
  bool _isLoading = false;
  String? _error;

  AuthProvider(this._authService);

  User? get currentUser => _currentUser;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get isAuthenticated => _currentUser != null;

  Future<bool> checkPersistentLogin() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final success = await _authService.checkPersistentLogin();
      if (success) {
        await _loadUserData();
      }

      _isLoading = false;
      notifyListeners();
      return success;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<AuthResult> loginWithPhone(String phoneNumber) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final result = await _authService.loginWithPhone(phoneNumber);
      _isLoading = false;
      notifyListeners();
      return result;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      throw e;
    }
  }

  Future<AuthResult> verifyOTP(String sessionId, String otp) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final result = await _authService.verifyOTP(sessionId, otp);
      await _loadUserData();
      _isLoading = false;
      notifyListeners();
      return result;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      throw e;
    }
  }

  Future<void> logout() async {
    _isLoading = true;
    notifyListeners();

    try {
      await _authService.logout();
      _currentUser = null;
      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> _loadUserData() async {
    final prefs = await SharedPreferences.getInstance();
    final userDataString = prefs.getString('user_data');

    if (userDataString != null) {
      final userData = json.decode(userDataString);
      _currentUser = User.fromJson(userData);
    }
  }
}
```

#### 1.3 Authentication Screens

**Splash Screen** (`screens/auth/splash_screen.dart`):
```dart
class SplashScreen extends StatefulWidget {
  @override
  _SplashScreenState createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    _checkAuthentication();
  }

  Future<void> _checkAuthentication() async {
    final authProvider = Provider.of<AuthProvider>(context, listen: false);

    // Add 2-second delay for splash animation
    await Future.delayed(Duration(seconds: 2));

    final isAuthenticated = await authProvider.checkPersistentLogin();

    if (isAuthenticated) {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => AnalyzingScreen()),
      );
    } else {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => LoginScreen()),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [Colors.purple.shade900, Colors.blue.shade900],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ),
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.stars, size: 80, color: Colors.white),
              SizedBox(height: 20),
              Text(
                'ZODIRA',
                style: TextStyle(
                  fontSize: 32,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                  letterSpacing: 2,
                ),
              ),
              SizedBox(height: 10),
              Text(
                'Your Cosmic Guide',
                style: TextStyle(fontSize: 16, color: Colors.white70),
              ),
              SizedBox(height: 40),
              CircularProgressIndicator(
                valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
```

**Analyzing Screen** (`screens/dashboard/analyzing_screen.dart`) - **CRITICAL REQUIREMENT**:
```dart
class AnalyzingScreen extends StatefulWidget {
  @override
  _AnalyzingScreenState createState() => _AnalyzingScreenState();
}

class _AnalyzingScreenState extends State<AnalyzingScreen>
    with TickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _progressAnimation;
  Timer? _analysisTimer;

  @override
  void initState() {
    super.initState();
    _setupAnimation();
    _startAnalysis();
  }

  void _setupAnimation() {
    _animationController = AnimationController(
      duration: const Duration(seconds: 5),
      vsync: this,
    );

    _progressAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    ));

    _animationController.repeat();
  }

  void _startAnalysis() {
    // Force minimum 5 seconds analysis time
    _analysisTimer = Timer(Duration(seconds: 5), () async {
      await _completeAnalysis();
    });
  }

  Future<void> _completeAnalysis() async {
    try {
      final dashboardProvider = Provider.of<DashboardProvider>(context, listen: false);
      final profileProvider = Provider.of<ProfileProvider>(context, listen: false);

      // Fetch all necessary data
      await Future.wait([
        dashboardProvider.loadDashboard(),
        profileProvider.loadUserProfiles(),
        _loadPredictions(),
        _loadMarriageMatches(),
      ]);

      // Navigate to dashboard
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => DashboardScreen()),
      );
    } catch (e) {
      // Handle error and navigate to dashboard anyway
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => DashboardScreen()),
      );
    }
  }

  Future<void> _loadPredictions() async {
    // Load predictions for all profiles
    // Implementation details...
  }

  Future<void> _loadMarriageMatches() async {
    // Load marriage matches for all profiles
    // Implementation details...
  }

  @override
  void dispose() {
    _animationController.dispose();
    _analysisTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [Colors.purple.shade900, Colors.blue.shade900],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ),
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Animated cosmic icon
              AnimatedBuilder(
                animation: _animationController,
                builder: (context, child) {
                  return Transform.rotate(
                    angle: _animationController.value * 2 * 3.14159,
                    child: Icon(
                      Icons.stars,
                      size: 100,
                      color: Colors.white,
                    ),
                  );
                },
              ),
              SizedBox(height: 30),

              Text(
                'Analyzing Your Cosmic Data',
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
                textAlign: TextAlign.center,
              ),

              SizedBox(height: 20),

              Text(
                'Generating personalized predictions\nand compatibility insights...',
                style: TextStyle(
                  fontSize: 16,
                  color: Colors.white70,
                ),
                textAlign: TextAlign.center,
              ),

              SizedBox(height: 40),

              // Progress indicator
              AnimatedBuilder(
                animation: _progressAnimation,
                builder: (context, child) {
                  return Container(
                    width: 200,
                    height: 4,
                    decoration: BoxDecoration(
                      color: Colors.white24,
                      borderRadius: BorderRadius.circular(2),
                    ),
                    child: FractionallySizedBox(
                      alignment: Alignment.centerLeft,
                      widthFactor: _progressAnimation.value,
                      child: Container(
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: [Colors.blue, Colors.purple],
                          ),
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                    ),
                  );
                },
              ),

              SizedBox(height: 20),

              Text(
                '${(_progressAnimation.value * 100).toInt()}%',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),

              SizedBox(height: 40),

              // Loading dots animation
              Lottie.asset(
                'assets/animations/loading_dots.json',
                width: 50,
                height: 50,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
```

### Phase 2: Profile Management

#### 2.1 Profile Models (`models/profile.dart`)

```dart
class Profile {
  final String id;
  final String userId;
  final String name;
  final DateTime birthDate;
  final TimeOfDay birthTime;
  final String birthPlace;
  final String gender;
  final String relationship;

  // Astrology data
  final String? zodiacSign;
  final String? moonSign;
  final String? nakshatra;
  final String? ascendant;

  // Enhanced data
  final Map<String, dynamic>? astrologyChart;
  final List<Prediction>? predictions;
  final List<MarriageMatch>? marriageMatches;

  Profile({
    required this.id,
    required this.userId,
    required this.name,
    required this.birthDate,
    required this.birthTime,
    required this.birthPlace,
    required this.gender,
    required this.relationship,
    this.zodiacSign,
    this.moonSign,
    this.nakshatra,
    this.ascendant,
    this.astrologyChart,
    this.predictions,
    this.marriageMatches,
  });

  factory Profile.fromJson(Map<String, dynamic> json) {
    return Profile(
      id: json['id'],
      userId: json['user_id'],
      name: json['name'],
      birthDate: DateTime.parse(json['birth_date']),
      birthTime: TimeOfDay.fromDateTime(
        DateTime.parse('2023-01-01 ${json['birth_time']}'),
      ),
      birthPlace: json['birth_place'],
      gender: json['gender'],
      relationship: json['relationship'],
      zodiacSign: json['zodiac_sign'],
      moonSign: json['moon_sign'],
      nakshatra: json['nakshatra'],
      ascendant: json['ascendant'],
      astrologyChart: json['astrology_chart'],
      predictions: json['predictions'] != null
          ? (json['predictions'] as List)
              .map((p) => Prediction.fromJson(p))
              .toList()
          : null,
      marriageMatches: json['marriage_matches'] != null
          ? (json['marriage_matches'] as List)
              .map((m) => MarriageMatch.fromJson(m))
              .toList()
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user_id': userId,
      'name': name,
      'birth_date': birthDate.toIso8601String().split('T')[0],
      'birth_time': '${birthTime.hour.toString().padLeft(2, '0')}:${birthTime.minute.toString().padLeft(2, '0')}:00',
      'birth_place': birthPlace,
      'gender': gender,
      'relationship': relationship,
      'zodiac_sign': zodiacSign,
      'moon_sign': moonSign,
      'nakshatra': nakshatra,
      'ascendant': ascendant,
      'astrology_chart': astrologyChart,
      'predictions': predictions?.map((p) => p.toJson()).toList(),
      'marriage_matches': marriageMatches?.map((m) => m.toJson()).toList(),
    };
  }
}
```

#### 2.2 Profile Service (`services/profile_service.dart`)

```dart
class ProfileService {
  final Dio _dio;
  static const String baseUrl = 'http://your-backend-url/api/v1';

  ProfileService(this._dio);

  Future<Profile> createProfile(Map<String, dynamic> profileData) async {
    try {
      final response = await _dio.post(
        '$baseUrl/profiles',
        data: profileData,
      );

      return Profile.fromJson(response.data);
    } catch (e) {
      throw Exception('Profile creation failed: $e');
    }
  }

  Future<Profile> generateProfileChart(String profileId) async {
    try {
      final response = await _dio.post(
        '$baseUrl/enhanced/profiles/$profileId/generate-chart',
      );

      return Profile.fromJson(response.data['profile']);
    } catch (e) {
      throw Exception('Chart generation failed: $e');
    }
  }

  Future<Profile> getProfileWithData(String profileId) async {
    try {
      final response = await _dio.get(
        '$baseUrl/enhanced/profiles/$profileId/complete',
      );

      return Profile.fromJson(response.data['profile']);
    } catch (e) {
      throw Exception('Failed to get profile data: $e');
    }
  }

  Future<List<Prediction>> getProfilePredictions(String profileId) async {
    try {
      final response = await _dio.get(
        '$baseUrl/enhanced/profiles/$profileId/predictions',
      );

      return (response.data['predictions'] as List)
          .map((p) => Prediction.fromJson(p))
          .toList();
    } catch (e) {
      throw Exception('Failed to get predictions: $e');
    }
  }

  Future<Prediction> generatePrediction(
    String profileId,
    String predictionType
  ) async {
    try {
      final response = await _dio.post(
        '$baseUrl/enhanced/profiles/$profileId/predictions/$predictionType',
      );

      return Prediction.fromJson(response.data['prediction']);
    } catch (e) {
      throw Exception('Prediction generation failed: $e');
    }
  }
}
```

### Phase 3: Dashboard & Predictions

#### 3.1 Dashboard Provider (`providers/dashboard_provider.dart`)

```dart
class DashboardProvider extends ChangeNotifier {
  final ProfileService _profileService;
  final PredictionService _predictionService;
  final MarriageService _marriageService;

  List<Profile> _profiles = [];
  List<Prediction> _recentPredictions = [];
  List<MarriageMatch> _recentMatches = [];
  bool _isLoading = false;
  String? _error;

  DashboardProvider(
    this._profileService,
    this._predictionService,
    this._marriageService,
  );

  List<Profile> get profiles => _profiles;
  List<Prediction> get recentPredictions => _recentPredictions;
  List<MarriageMatch> get recentMatches => _recentMatches;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> loadDashboard() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      // Load all dashboard data
      final results = await Future.wait([
        _loadProfiles(),
        _loadRecentPredictions(),
        _loadRecentMatches(),
      ]);

      _profiles = results[0] as List<Profile>;
      _recentPredictions = results[1] as List<Prediction>;
      _recentMatches = results[2] as List<MarriageMatch>;

      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<List<Profile>> _loadProfiles() async {
    try {
      // Get profiles from API
      final response = await _dio.get('$baseUrl/enhanced/dashboard');
      final profilesData = response.data['profiles'] as List;

      return profilesData.map((p) => Profile.fromJson(p)).toList();
    } catch (e) {
      return [];
    }
  }

  Future<List<Prediction>> _loadRecentPredictions() async {
    try {
      final response = await _dio.get('$baseUrl/enhanced/dashboard');
      final predictionsData = response.data['recent_predictions'] as List;

      return predictionsData.map((p) => Prediction.fromJson(p)).toList();
    } catch (e) {
      return [];
    }
  }

  Future<List<MarriageMatch>> _loadRecentMatches() async {
    try {
      final response = await _dio.get('$baseUrl/enhanced/dashboard');
      final matchesData = response.data['recent_marriage_matches'] as List;

      return matchesData.map((m) => MarriageMatch.fromJson(m)).toList();
    } catch (e) {
      return [];
    }
  }
}
```

#### 3.2 Dashboard Screen (`screens/dashboard/dashboard_screen.dart`)

```dart
class DashboardScreen extends StatefulWidget {
  @override
  _DashboardScreenState createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  @override
  void initState() {
    super.initState();
    // Dashboard data is already loaded in AnalyzingScreen
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('ZODIRA Dashboard'),
        actions: [
          IconButton(
            icon: Icon(Icons.logout),
            onPressed: _logout,
          ),
        ],
      ),
      body: Consumer<DashboardProvider>(
        builder: (context, provider, child) {
          if (provider.isLoading) {
            return Center(child: CircularProgressIndicator());
          }

          return SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildWelcomeSection(),
                _buildProfilesSection(),
                _buildPredictionsSection(),
                _buildMarriageMatchesSection(),
              ],
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _addNewProfile,
        child: Icon(Icons.add),
        tooltip: 'Add New Profile',
      ),
    );
  }

  Widget _buildWelcomeSection() {
    final authProvider = Provider.of<AuthProvider>(context);
    final user = authProvider.currentUser;

    return Container(
      padding: EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.purple.shade800, Colors.blue.shade800],
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Welcome back, ${user?.name ?? 'User'}!',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          SizedBox(height: 8),
          Text(
            'Your cosmic journey continues...',
            style: TextStyle(fontSize: 16, color: Colors.white70),
          ),
        ],
      ),
    );
  }

  Widget _buildProfilesSection() {
    return Consumer<DashboardProvider>(
      builder: (context, provider, child) {
        final profiles = provider.profiles;

        return Container(
          padding: EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Your Profiles',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  TextButton(
                    onPressed: _viewAllProfiles,
                    child: Text('View All'),
                  ),
                ],
              ),
              SizedBox(height: 16),
              profiles.isEmpty
                  ? _buildEmptyProfiles()
                  : _buildProfilesList(profiles),
            ],
          ),
        );
      },
    );
  }

  Widget _buildPredictionsSection() {
    return Consumer<DashboardProvider>(
      builder: (context, provider, child) {
        final predictions = provider.recentPredictions;

        return Container(
          padding: EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Recent Predictions',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
              SizedBox(height: 16),
              predictions.isEmpty
                  ? _buildEmptyPredictions()
                  : _buildPredictionsList(predictions),
            ],
          ),
        );
      },
    );
  }

  Widget _buildMarriageMatchesSection() {
    return Consumer<DashboardProvider>(
      builder: (context, provider, child) {
        final matches = provider.recentMatches;

        return Container(
          padding: EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Marriage Compatibility',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
              SizedBox(height: 16),
              matches.isEmpty
                  ? _buildEmptyMatches()
                  : _buildMatchesList(matches),
            ],
          ),
        );
      },
    );
  }

  void _logout() async {
    final authProvider = Provider.of<AuthProvider>(context, listen: false);
    await authProvider.logout();

    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(builder: (_) => LoginScreen()),
      (route) => false,
    );
  }

  void _addNewProfile() {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => ProfileCreationScreen()),
    );
  }

  void _viewAllProfiles() {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => ProfileListScreen()),
    );
  }
}
```

### Phase 4: Marriage Matching

#### 4.1 Marriage Service (`services/marriage_service.dart`)

```dart
class MarriageService {
  final Dio _dio;
  static const String baseUrl = 'http://your-backend-url/api/v1';

  MarriageService(this._dio);

  Future<MarriageMatch> generateMarriageMatch(
    String mainProfileId,
    Map<String, dynamic> partnerData,
  ) async {
    try {
      final response = await _dio.post(
        '$baseUrl/enhanced/marriage-matching/generate',
        data: {
          'main_profile_id': mainProfileId,
          ...partnerData,
        },
      );

      return MarriageMatch.fromJson(response.data['marriage_match']);
    } catch (e) {
      throw Exception('Marriage match generation failed: $e');
    }
  }

  Future<MarriageMatch> getMarriageMatch(String matchId) async {
    try {
      final response = await _dio.get(
        '$baseUrl/enhanced/marriage-matching/$matchId',
      );

      return MarriageMatch.fromJson(response.data['marriage_match']);
    } catch (e) {
      throw Exception('Failed to get marriage match: $e');
    }
  }

  Future<List<MarriageMatch>> getProfileMarriageMatches(String profileId) async {
    try {
      final response = await _dio.get(
        '$baseUrl/enhanced/profiles/$profileId/marriage-matches',
      );

      return (response.data['marriage_matches'] as List)
          .map((m) => MarriageMatch.fromJson(m))
          .toList();
    } catch (e) {
      throw Exception('Failed to get marriage matches: $e');
    }
  }
}
```

#### 4.2 Marriage Matching Screen (`screens/marriage/marriage_matching_screen.dart`)

```dart
class MarriageMatchingScreen extends StatefulWidget {
  final String profileId;

  MarriageMatchingScreen({required this.profileId});

  @override
  _MarriageMatchingScreenState createState() => _MarriageMatchingScreenState();
}

class _MarriageMatchingScreenState extends State<MarriageMatchingScreen> {
  final _formKey = GlobalKey<FormState>();
  final Map<String, dynamic> _partnerData = {};

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Marriage Compatibility'),
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: EdgeInsets.all(20),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Enter Partner Details',
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                ),
              ),
              SizedBox(height: 8),
              Text(
                'We\'ll analyze cosmic compatibility between you and your partner',
                style: TextStyle(fontSize: 16, color: Colors.grey),
              ),
              SizedBox(height: 30),

              // Partner name
              TextFormField(
                decoration: InputDecoration(
                  labelText: 'Partner Name',
                  border: OutlineInputBorder(),
                ),
                validator: (value) {
                  if (value?.isEmpty ?? true) {
                    return 'Please enter partner name';
                  }
                  return null;
                },
                onSaved: (value) => _partnerData['name'] = value,
              ),

              SizedBox(height: 20),

              // Birth date picker
              InkWell(
                onTap: _selectBirthDate,
                child: Container(
                  padding: EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    border: Border.all(color: Colors.grey),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.calendar_today),
                      SizedBox(width: 12),
                      Text(_partnerData['birth_date'] ?? 'Select Birth Date'),
                    ],
                  ),
                ),
              ),

              SizedBox(height: 20),

              // Birth time picker
              InkWell(
                onTap: _selectBirthTime,
                child: Container(
                  padding: EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    border: Border.all(color: Colors.grey),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.access_time),
                      SizedBox(width: 12),
                      Text(_partnerData['birth_time'] ?? 'Select Birth Time'),
                    ],
                  ),
                ),
              ),

              SizedBox(height: 20),

              // Birth place
              TextFormField(
                decoration: InputDecoration(
                  labelText: 'Birth Place',
                  border: OutlineInputBorder(),
                ),
                validator: (value) {
                  if (value?.isEmpty ?? true) {
                    return 'Please enter birth place';
                  }
                  return null;
                },
                onSaved: (value) => _partnerData['birth_place'] = value,
              ),

              SizedBox(height: 20),

              // Gender selection
              DropdownButtonFormField<String>(
                decoration: InputDecoration(
                  labelText: 'Gender',
                  border: OutlineInputBorder(),
                ),
                items: ['male', 'female', 'other'].map((gender) {
                  return DropdownMenuItem(
                    value: gender,
                    child: Text(gender.capitalize()),
                  );
                }).toList(),
                validator: (value) {
                  if (value == null) {
                    return 'Please select gender';
                  }
                  return null;
                },
                onSaved: (value) => _partnerData['gender'] = value,
              ),

              SizedBox(height: 40),

              // Generate match button
              SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton(
                  onPressed: _generateMarriageMatch,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.purple.shade800,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  child: Text(
                    'Generate Compatibility Report',
                    style: TextStyle(fontSize: 16),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _selectBirthDate() async {
    final DateTime? picked = await showDatePicker(
      context: context,
      initialDate: DateTime(1990),
      firstDate: DateTime(1900),
      lastDate: DateTime.now(),
    );

    if (picked != null) {
      setState(() {
        _partnerData['birth_date'] = picked.toIso8601String().split('T')[0];
      });
    }
  }

  void _selectBirthTime() async {
    final TimeOfDay? picked = await showTimePicker(
      context: context,
      initialTime: TimeOfDay(hour: 12, minute: 0),
    );

    if (picked != null) {
      setState(() {
        _partnerData['birth_time'] = '${picked.hour.toString().padLeft(2, '0')}:${picked.minute.toString().padLeft(2, '0')}:00';
      });
    }
  }

  void _generateMarriageMatch() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    _formKey.currentState!.save();

    setState(() {
      _isGenerating = true;
    });

    try {
      final marriageProvider = Provider.of<MarriageProvider>(context, listen: false);

      final marriageMatch = await marriageProvider.generateMarriageMatch(
        widget.profileId,
        _partnerData,
      );

      Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => MarriageReportScreen(marriageMatch: marriageMatch),
        ),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to generate compatibility report: $e')),
      );
    } finally {
      setState(() {
        _isGenerating = false;
      });
    }
  }
}
```

### Phase 5: State Management Integration

#### 5.1 Main App Setup (`main.dart`)

```dart
void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize Firebase
  await Firebase.initializeApp();

  // Initialize services
  final authService = AuthService(Dio(), FirebaseAuth.instance, FirebaseFirestore.instance);
  final profileService = ProfileService(Dio());
  final predictionService = PredictionService(Dio());
  final marriageService = MarriageService(Dio());

  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider(authService)),
        ChangeNotifierProvider(create: (_) => ProfileProvider(profileService)),
        ChangeNotifierProvider(create: (_) => DashboardProvider(profileService, predictionService, marriageService)),
        ChangeNotifierProvider(create: (_) => MarriageProvider(marriageService)),
      ],
      child: MyApp(),
    ),
  );
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ZODIRA Astrology',
      theme: ThemeData(
        primarySwatch: Colors.purple,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      home: SplashScreen(),
      routes: {
        '/login': (context) => LoginScreen(),
        '/dashboard': (context) => DashboardScreen(),
        '/analyzing': (context) => AnalyzingScreen(),
      },
    );
  }
}
```

## API Integration Details

### Dio Client Configuration (`services/api_client.dart`)

```dart
class ApiClient {
  static Dio createDio() {
    final dio = Dio();

    dio.options.baseUrl = 'http://your-backend-url/api/v1';
    dio.options.connectTimeout = Duration(seconds: 30);
    dio.options.receiveTimeout = Duration(seconds: 30);

    // Add interceptors
    dio.interceptors.addAll([
      // Auth interceptor
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final prefs = await SharedPreferences.getInstance();
          final token = prefs.getString('access_token');

          if (token != null) {
            options.headers['Authorization'] = 'Bearer $token';
          }

          handler.next(options);
        },
        onError: (error, handler) async {
          if (error.response?.statusCode == 401) {
            // Token expired, redirect to login
            final context = navigatorKey.currentContext;
            if (context != null) {
              Navigator.of(context).pushAndRemoveUntil(
                MaterialPageRoute(builder: (_) => LoginScreen()),
                (route) => false,
              );
            }
          }
          handler.next(error);
        },
      ),

      // Logging interceptor (debug only)
      if (kDebugMode) LogInterceptor(requestBody: true, responseBody: true),
    ]);

    return dio;
  }
}
```

## Error Handling Strategy

### Global Error Handler (`utils/error_handler.dart`)

```dart
class ErrorHandler {
  static void handleError(BuildContext context, dynamic error) {
    String message = 'An unexpected error occurred';

    if (error is DioError) {
      switch (error.type) {
        case DioErrorType.connectionTimeout:
        case DioErrorType.sendTimeout:
        case DioErrorType.receiveTimeout:
          message = 'Connection timeout. Please check your internet connection.';
          break;
        case DioErrorType.badResponse:
          final statusCode = error.response?.statusCode;
          switch (statusCode) {
            case 400:
              message = 'Invalid request. Please check your input.';
              break;
            case 401:
              message = 'Session expired. Please login again.';
              break;
            case 403:
              message = 'Access denied.';
              break;
            case 404:
              message = 'Requested resource not found.';
              break;
            case 500:
              message = 'Server error. Please try again later.';
              break;
            default:
              message = 'Request failed with status: $statusCode';
          }
          break;
        case DioErrorType.cancel:
          message = 'Request cancelled.';
          break;
        default:
          message = 'Network error. Please check your connection.';
      }
    }

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
        duration: Duration(seconds: 4),
      ),
    );
  }
}
```

## Testing Strategy

### Integration Tests (`integration_test/app_test.dart`)

```dart
void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('Complete User Flow', () {
    testWidgets('should complete full user journey', (WidgetTester tester) async {
      // Test 1: App launch and persistent login check
      app.main();
      await tester.pumpAndSettle();

      // Should show splash screen
      expect(find.text('ZODIRA'), findsOneWidget);

      // Test 2: Login flow
      await tester.pumpAndSettle();
      // Navigate through login screens...

      // Test 3: Profile creation
      // Test profile creation flow...

      // Test 4: Dashboard with analyzing screen
      expect(find.text('Analyzing Your Cosmic Data'), findsOneWidget);

      // Wait for analysis to complete (5 seconds minimum)
      await tester.pumpAndSettle(Duration(seconds: 6));

      // Should show dashboard
      expect(find.text('Welcome back'), findsOneWidget);

      // Test 5: Marriage matching
      // Test marriage matching flow...
    });
  });
}
```

## Implementation Checklist

### Phase 1: Authentication ✅
- [ ] Implement AuthService with persistent login
- [ ] Create AuthProvider for state management
- [ ] Build login and OTP verification screens
- [ ] Implement splash screen with auto-navigation
- [ ] Create analyzing screen with 5-second minimum timer
- [ ] Add logout functionality

### Phase 2: Profile Management ✅
- [ ] Create Profile model with all required fields
- [ ] Implement ProfileService for API calls
- [ ] Build profile creation screen with validation
- [ ] Create profile list and detail screens
- [ ] Add profile editing functionality

### Phase 3: Dashboard & Predictions ✅
- [ ] Implement DashboardProvider
- [ ] Create dashboard screen with all sections
- [ ] Build prediction display widgets
- [ ] Add prediction refresh functionality
- [ ] Implement astrology chart visualization

### Phase 4: Marriage Matching ✅
- [ ] Create MarriageMatch and PartnerProfile models
- [ ] Implement MarriageService
- [ ] Build marriage matching input screen
- [ ] Create marriage report display screen
- [ ] Add compatibility visualization

### Phase 5: State Management & Integration ✅
- [ ] Set up Provider for state management
- [ ] Configure Dio client with interceptors
- [ ] Implement global error handling
- [ ] Add loading states throughout app
- [ ] Implement offline data persistence

### Phase 6: UI/UX Enhancements ✅
- [ ] Add smooth animations and transitions
- [ ] Implement cosmic/cosmic theme
- [ ] Add Lottie animations for loading states
- [ ] Create responsive design for all screens
- [ ] Add dark mode support

### Phase 7: Testing & Quality Assurance ✅
- [ ] Write unit tests for all services
- [ ] Create integration tests for complete flows
- [ ] Test error scenarios and edge cases
- [ ] Performance testing with large datasets
- [ ] User acceptance testing

## Critical Requirements Summary

1. **Analyzing Screen**: Must show for minimum 5 seconds when loading dashboard data
2. **Persistent Login**: Automatic login without re-authentication
3. **Complete Data Loading**: Fetch all predictions and charts during analysis
4. **Error Handling**: Graceful handling of API failures
5. **State Management**: Proper loading and error states throughout
6. **Marriage Matching**: Full compatibility analysis with AI insights
7. **Responsive Design**: Works on all device sizes
8. **Performance**: Smooth animations and fast loading

## API Integration Points

All API calls must include proper authentication headers and error handling. The analyzing screen should fetch:
- User profiles with complete chart data
- All predictions for each profile
- Marriage matches and compatibility reports
- Dashboard summary data

This implementation ensures complete backend integration while providing an excellent user experience with the analyzing animation and comprehensive astrology features.