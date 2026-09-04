class UserModel {
  final String id;
  final String email;
  final String fullName;
  final String? phoneNumber;
  final String role;
  final bool isActive;

  UserModel({
    required this.id,
    required this.email,
    required this.fullName,
    this.phoneNumber,
    required this.role,
    required this.isActive,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id'] as String,
      email: json['email'] as String,
      fullName: json['full_name'] as String,
      phoneNumber: json['phone_number'] as String?,
      role: json['role'] as String,
      isActive: json['is_active'] as bool? ?? true,
    );
  }
}
