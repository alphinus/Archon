"""
Simple validation test for AAL Memory Integration.
Verifies that the code changes are correct without executing AAL.

Run with: cd python && python ../verify_aal_memory_simple.py
"""

import sys
import os

# Add python directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
python_dir = os.path.join(script_dir, "python")
if python_dir not in sys.path:
    sys.path.append(python_dir)

print("=== AAL Memory Integration - Code Validation ===\n")

# Test 1: Import AgentRequest and verify new fields exist
print("Test 1: Verifying AgentRequest model has memory fields...")
try:
    from src.aal.models import AgentRequest
    
    # Create a request to verify new fields work
    request = AgentRequest(
        prompt="Test prompt",
        user_id="test_user_123",
        session_id="test_session_456",
        enable_memory=True,
        memory_max_tokens=2000
    )
    
    assert request.user_id == "test_user_123", "user_id not set correctly"
    assert request.session_id == "test_session_456", "session_id not set correctly"  
    assert request.enable_memory == True, "enable_memory not set correctly"
    assert request.memory_max_tokens == 2000, "memory_max_tokens not set correctly"
    
    print("✅ AgentRequest model extended correctly")
    print(f"   - user_id: {request.user_id}")
    print(f"   - session_id: {request.session_id}")
    print(f"   - enable_memory: {request.enable_memory}")
    print(f"   - memory_max_tokens: {request.memory_max_tokens}")
    
except Exception as e:
    print(f"❌ FAILED: {e}")
    sys.exit(1)

# Test 2: Verify service.py imports ContextAssembler
print("\nTest 2: Verifying AgentService imports ContextAssembler...")
try:
    # Read the file to verify the import
    service_file = os.path.join(python_dir, "src/aal/service.py")
    with open(service_file, 'r') as f:
        content = f.read()
        
    assert "from src.memory import ContextAssembler" in content, "ContextAssembler import missing"
    assert "MEMORY INTEGRATION" in content, "Memory integration code missing"
    assert "context_assembler = ContextAssembler()" in content, "ContextAssembler instantiation missing"
    assert "assembled_context = await context_assembler.assemble_context" in content, "Context assembly call missing"
    
    print("✅ AgentService has memory injection code")
    print("   - ContextAssembler imported")
    print("   - Memory integration block added")
    print("   - Context assembly implemented")
    
except Exception as e:
    print(f"❌ FAILED: {e}")
    sys.exit(1)

# Test 3: Verify defaults work correctly
print("\nTest 3: Verifying default values...")
try:
    request_default = AgentRequest(prompt="Test")
    
    assert request_default.user_id is None, "user_id default should be None"
    assert request_default.session_id is None, "session_id default should be None"
    assert request_default.enable_memory == True, "enable_memory default should be True"
    assert request_default.memory_max_tokens == 4000, "memory_max_tokens default should be 4000"
    
    print("✅ Default values correct")
    print(f"   - user_id defaults to None")
    print(f"   - enable_memory defaults to True")
    print(f"   - memory_max_tokens defaults to 4000")
    
except Exception as e:
    print(f"❌ FAILED: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("✅ SUCCESS: AAL Memory Integration code is valid!")
print("="*60)
print("\nSummary:")
print("  1. ✅ AgentRequest model extended with memory parameters")
print("  2. ✅ AgentService imports and uses ContextAssembler")
print("  3. ✅ Default values configured correctly")
print("\nMemory injection will activate automatically when:")
print("  - enable_memory=True (default)")
print("  - user_id is provided in the request")
print("  - Redis and Postgres are available")
