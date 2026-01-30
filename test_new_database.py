"""
test_new_database.py
Test script for the new database schema.
"""

from database import (
    create_user,
    authenticate_user,
    get_user,
    create_property,
    get_property_by_name,
    create_sentence,
    get_sentences_by_property,
    save_label,
    get_user_labels,
    get_user_stats,
    get_all_properties
)

def test_database():
    """Test all database operations."""
    print("=" * 60)
    print("DATABASE TEST SCRIPT")
    print("=" * 60)
    
    # Test 1: Create users
    print("\n[TEST 1] Creating users...")
    try:
        user1_id = create_user("alice", "password123")
        print(f"  ✅ Created user 'alice' with ID: {user1_id}")
        
        user2_id = create_user("bob", "securepass456")
        print(f"  ✅ Created user 'bob' with ID: {user2_id}")
    except ValueError as e:
        print(f"  ℹ️  Users already exist: {e}")
        user1_id = authenticate_user("alice", "password123")
        user2_id = authenticate_user("bob", "securepass456")
    
    # Test 2: Authenticate users
    print("\n[TEST 2] Authenticating users...")
    auth_id = authenticate_user("alice", "password123")
    if auth_id:
        print(f"  ✅ Authentication successful for 'alice': ID {auth_id}")
    else:
        print("  ❌ Authentication failed")
    
    wrong_auth = authenticate_user("alice", "wrongpassword")
    if wrong_auth is None:
        print("  ✅ Correctly rejected wrong password")
    else:
        print("  ❌ Should have rejected wrong password")
    
    # Test 3: Get user info
    print("\n[TEST 3] Getting user information...")
    user_info = get_user("alice")
    if user_info:
        print(f"  ✅ User info: {user_info}")
    
    # Test 4: Check properties
    print("\n[TEST 4] Checking properties...")
    properties = get_all_properties()
    print(f"  ✅ Total properties in database: {len(properties)}")
    if properties:
        print(f"  ℹ️  Sample property: {properties[0]['property_name']}")
        print(f"     Domain: {properties[0]['property_domain']}")
        print(f"     Range: {properties[0]['property_range']}")
    
    # Test 5: Get sentences for a property
    if properties:
        print("\n[TEST 5] Getting sentences for first property...")
        prop = properties[0]
        sentences = get_sentences_by_property(prop['id'])
        print(f"  ✅ Found {len(sentences)} sentences for '{prop['property_name']}'")
        if sentences:
            print(f"  ℹ️  Sample sentence: {sentences[0]['sentence'][:100]}...")
        
        # Test 6: Save a label
        if sentences:
            print("\n[TEST 6] Saving a label...")
            sentence_id = sentences[0]['id']
            save_label(
                user_id=user1_id,
                sentence_id=sentence_id,
                label_code="pdr",
                subject_words="0,1,2",
                property_words="3,4",
                object_words="5,6,7",
                is_complete=True
            )
            print(f"  ✅ Saved label for sentence ID {sentence_id}")
            
            # Test 7: Get user stats
            print("\n[TEST 7] Getting user statistics...")
            stats = get_user_stats(user1_id)
            print(f"  ✅ User stats: {stats}")
            
            # Test 8: Get user labels
            print("\n[TEST 8] Getting user labels...")
            labels = get_user_labels(user1_id)
            print(f"  ✅ User has labels for {len(labels)} properties")
            for prop_name, prop_labels in labels.items():
                print(f"     - {prop_name}: {len(prop_labels)} sentences labeled")
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED!")
    print("=" * 60)

if __name__ == "__main__":
    test_database()
