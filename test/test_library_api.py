import uuid
import os
from eagleliz.api.eaglelizapi import EagleAPI, EagleAPIError, LibraryInfo, EagleFolder

def test_library_api():
    api = EagleAPI()

    print("\n--- Testing Library APIs ---")
    
    # Test: get_library_info
    print("\nAttempting to get Library Info...")
    try:
        library_info = api.get_library_info()
        print("✅ Get Library Info Success!")
        print(f"Application Version: {library_info.applicationVersion}")
        print(f"Total Folders at root level: {len(library_info.folders)}")
        
        # Simple assertions
        assert isinstance(library_info, LibraryInfo), "Returned object is not LibraryInfo"
        assert isinstance(library_info.applicationVersion, str), "applicationVersion should be a string"
        assert isinstance(library_info.folders, list), "folders should be a list"
        
        # If there are any folders, check the first one is parsed correctly
        if library_info.folders:
            assert isinstance(library_info.folders[0], EagleFolder), "Items in folders should be EagleFolder"
            
    except EagleAPIError as e:
        print(f"❌ API Error during get_library_info test: {e}")
        raise
    except AssertionError as e:
        print(f"❌ Assertion Error during get_library_info test: {e}")
        raise

    # Test: get_library_history
    print("\nAttempting to get Library History...")
    try:
        library_history = api.get_library_history()
        print("✅ Get Library History Success!")
        print(f"Total Recent Libraries: {len(library_history)}")
        if library_history:
            print(f"Most recent: {library_history[0]}")
            
        assert isinstance(library_history, list), "library_history should return a list"
        if library_history:
             assert isinstance(library_history[0], str), "library_history list items should be strings"
             
    except EagleAPIError as e:
        print(f"❌ API Error during get_library_history test: {e}")
        raise
    except AssertionError as e:
        print(f"❌ Assertion Error during get_library_history test: {e}")
        raise

if __name__ == "__main__":
    test_library_api()
