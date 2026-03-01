from eagleliz.api.eaglelizapi import EagleAPI, EagleAPIError
import uuid

def test_folder_api():
    api = EagleAPI()
    
    unique_suffix = str(uuid.uuid4())[:8]
    test_folder_name = f"Test_Folder_{unique_suffix}"
    renamed_folder_name = f"Renamed_{test_folder_name}"
    
    # 1. Test Create Folder
    print(f"Attempting to create folder: '{test_folder_name}'")
    try:
        new_folder = api.create_folder(folder_name=test_folder_name)
        print(f"✅ Successfully created folder.")
        print(f"   ID: {new_folder.id}")
        print(f"   Name: {new_folder.name}")
        
        # Verify name matches
        assert new_folder.name == test_folder_name, f"Expected name {test_folder_name}, got {new_folder.name}"
        
        # 2. Test Rename Folder
        print(f"\nAttempting to rename folder (ID: {new_folder.id}) to: '{renamed_folder_name}'")
        renamed_folder = api.rename_folder(folder_id=new_folder.id, new_name=renamed_folder_name)
        
        print(f"✅ Successfully renamed folder.")
        print(f"   ID: {renamed_folder.id}")
        print(f"   Name: {renamed_folder.name}")
        
        # Verify rename matches
        assert renamed_folder.name == renamed_folder_name, f"Expected name {renamed_folder_name}, got {renamed_folder.name}"
        assert renamed_folder.id == new_folder.id, "ID should not change after rename"

    except EagleAPIError as e:
        print(f"❌ API Error during normal flow test: {e}")
        return
    except AssertionError as e:
        print(f"❌ Assertion Error: {e}")
        return

    # 3. Test Failure Modes
    print("\nTesting Failure expected scenarios...")
    
    try:
        # Renaming a non-existent folder
        api.rename_folder(folder_id="INVALID_NONEXISTENT_ID_12345", new_name="Should Fail")
        print("❌ Failed: Expected error when renaming non-existent folder, but it succeeded.")
    except EagleAPIError as e:
        print(f"✅ Successfully caught expected error for invalid rename: {e}")

if __name__ == "__main__":
    test_folder_api()
