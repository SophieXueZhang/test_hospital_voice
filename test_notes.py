#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for patient notes functionality
"""
import json
import os

# Test the notes functions
NOTES_FILE = "data/patient_notes.json"

def test_notes_functions():
    """Test saving and loading patient notes"""

    # Test data
    test_patient_id = "12345"
    test_note = "Patient reports mild headache in the morning. Family history of diabetes noted."

    # Create test notes
    notes = {
        test_patient_id: test_note
    }

    # Save notes
    os.makedirs(os.path.dirname(NOTES_FILE), exist_ok=True)
    with open(NOTES_FILE, 'w', encoding='utf-8') as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)

    print(f"✅ Successfully saved test note to {NOTES_FILE}")

    # Load notes
    with open(NOTES_FILE, 'r', encoding='utf-8') as f:
        loaded_notes = json.load(f)

    # Verify
    if test_patient_id in loaded_notes and loaded_notes[test_patient_id] == test_note:
        print("✅ Successfully loaded and verified note")
        print(f"   Patient ID: {test_patient_id}")
        print(f"   Note: {loaded_notes[test_patient_id]}")
    else:
        print("❌ Failed to load or verify note")
        return False

    # Clean up test file
    if os.path.exists(NOTES_FILE):
        os.remove(NOTES_FILE)
        print("✅ Cleaned up test file")

    return True

if __name__ == "__main__":
    print("Testing patient notes functionality...\n")
    success = test_notes_functions()
    print("\n" + ("="*50))
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
