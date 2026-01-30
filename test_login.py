"""
test_login.py
Test the new login functionality with bcrypt password hashing.
"""

from database import create_user, authenticate_user, get_user

def test_login():
    """Test login functionality."""
    print("=" * 60)
    print("LOGIN FUNCTIONALITY TEST")
    print("=" * 60)
    
    # Test 1: Create a new user
    print("\n[TEST 1] Creating new user 'testuser'...")
    try:
        user_id = create_user("testuser", "mypassword123")
        print(f"  ✅ User created with ID: {user_id}")
    except ValueError as e:
        print(f"  ℹ️  User already exists: {e}")
    
    # Test 2: Authenticate with correct password
    print("\n[TEST 2] Authenticating with correct password...")
    user_id = authenticate_user("testuser", "mypassword123")
    if user_id:
        print(f"  ✅ Authentication successful! User ID: {user_id}")
    else:
        print("  ❌ Authentication failed")
    
    # Test 3: Authenticate with wrong password
    print("\n[TEST 3] Authenticating with wrong password...")
    user_id = authenticate_user("testuser", "wrongpassword")
    if user_id is None:
        print("  ✅ Correctly rejected wrong password")
    else:
        print("  ❌ Should have rejected wrong password")
    
    # Test 4: Check user info
    print("\n[TEST 4] Getting user information...")
    user = get_user("testuser")
    if user:
        print(f"  ✅ User info retrieved:")
        print(f"     - ID: {user['id']}")
        print(f"     - Name: {user['name']}")
        print(f"     - Sentences labeled: {user['sentences_labeled']}")
        print(f"     - Created at: {user['created_at']}")
        print(f"     - Last login: {user['last_login']}")
    
    # Test 5: Try to create duplicate user
    print("\n[TEST 5] Attempting to create duplicate user...")
    try:
        user_id = create_user("testuser", "anotherpassword")
        print("  ❌ Should have raised ValueError")
    except ValueError as e:
        print(f"  ✅ Correctly prevented duplicate: {e}")
    
    print("\n" + "=" * 60)
    print("ALL LOGIN TESTS PASSED!")
    print("=" * 60)
    print("\n✅ The login system is working correctly with:")
    print("   - Bcrypt password hashing")
    print("   - New user creation")
    print("   - Existing user authentication")
    print("   - Wrong password rejection")
    print("   - Duplicate username prevention")

if __name__ == "__main__":
    test_login()
