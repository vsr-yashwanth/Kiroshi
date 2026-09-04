class TouristProfileModel {
  final String id;
  final String userId;
  final String? nationality;
  final String? emergencyContactName;
  final String? emergencyContactPhone;
  final String? medicalNotes;
  final bool consentGiven;

  TouristProfileModel({
    required this.id,
    required this.userId,
    this.nationality,
    this.emergencyContactName,
    this.emergencyContactPhone,
    this.medicalNotes,
    required this.consentGiven,
  });

  factory TouristProfileModel.fromJson(Map<String, dynamic> json) {
    return TouristProfileModel(
      id: json['id'] as String,
      userId: json['user_id'] as String,
      nationality: json['nationality'] as String?,
      emergencyContactName: json['emergency_contact_name'] as String?,
      emergencyContactPhone: json['emergency_contact_phone'] as String?,
      medicalNotes: json['medical_notes'] as String?,
      consentGiven: json['consent_given'] as bool? ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'nationality': nationality,
      'emergency_contact_name': emergencyContactName,
      'emergency_contact_phone': emergencyContactPhone,
      'medical_notes': medicalNotes,
      'consent_given': consentGiven,
    };
  }
}
