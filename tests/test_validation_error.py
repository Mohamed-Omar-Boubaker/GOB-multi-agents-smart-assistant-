"""
Test de la nouvelle ValidationError structurée
Montassar - 22 Feb 2026

Ce script montre comment utiliser ValidationError avec les nouveaux paramètres.
"""

from backend.utils.exceptions import ValidationError

def test_validation_errors():
    """Test des différents formats ValidationError."""
    
    print("=" * 60)
    print("🧪 TEST VALIDATIONERROR STRUCTURÉE")
    print("=" * 60)
    
    # Test 1: Version simple (compatible avec ancien code)
    print("\n1️⃣  VERSION SIMPLE (message seul):")
    try:
        raise ValidationError("Email invalide")
    except ValidationError as e:
        print(f"   Message: {e}")
        print(f"   Code: {e.code}")
        print(f"   Field: {e.field}")
        print(f"   Details: {e.details}")
    
    # Test 2: Version structurée complète
    print("\n2️⃣  VERSION STRUCTURÉE (tous les paramètres):")
    try:
        raise ValidationError(
            message="Contact introuvable dans la base de données",
            code="CONTACT_NOT_FOUND",
            field="recipient_email",
            details={
                "recipient_name": "mon ami",
                "available_contacts": ["amine", "jean", "montassar"],
                "suggestion": "Ajoutez ce contact d'abord"
            }
        )
    except ValidationError as e:
        print(f"   Message: {e.message}")
        print(f"   Code: {e.code}")
        print(f"   Field: {e.field}")
        print(f"   Details: {e.details}")
        print(f"   String repr: {str(e)}")
        print(f"   Dict format: {e.to_dict()}")
    
    # Test 3: Test du format pour API
    print("\n3️⃣  FORMAT POUR API RESPONSE:")
    try:
        raise ValidationError(
            message="Email fictif détecté: test@example.com",
            code="FAKE_EMAIL_REJECTED",
            field="recipient_email",
            details={
                "fake_email": "test@example.com",
                "fake_domains": ["@example.com", "@test.com", "@fake.com"]
            }
        )
    except ValidationError as e:
        import json
        api_response = {
            "status": "error",
            "error": e.to_dict()
        }
        print(f"   Response JSON:")
        print(f"   {json.dumps(api_response, indent=2, ensure_ascii=False)}")
    
    print("\n" + "=" * 60)
    print("✅ TOUS LES TESTS RÉUSSIS")
    print("=" * 60)

if __name__ == "__main__":
    test_validation_errors()
