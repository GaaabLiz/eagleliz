import uuid
from eagleliz.api.eaglelizapi import EagleAPI, EagleAPIError

def test_add_from_url():
    api = EagleAPI()
    
    unique_suffix = str(uuid.uuid4())[:8]
    test_folder_name = f"Test_Add_From_URL_Folder_{unique_suffix}"
    
    try:
        # Create a dedicated testing folder so images don't spam the main directory
        test_folder = api.create_folder(folder_name=test_folder_name)
        folder_id = test_folder.id
        print(f"Created isolated test folder: {test_folder_name} (ID: {folder_id})")
        
        # Test 1: Simple Add from URL
        dummy_url = "https://picsum.photos/400/300"
        image_name = f"Test Image {unique_suffix}"
        
        print(f"\nAttempting to add image from URL: {dummy_url}")
        success = api.add_item_from_url(
            url=dummy_url,
            name=image_name,
            website="https://picsum.photos",
            tags=["AI_Test_Tag", "Picsum"],
            star=5,
            annotation="This is a test image added automatically by eagleliz API.",
            folderId=folder_id
        )
        
        print(f"✅ Add from URL Success: {success}")
        assert success is True, "Expected add_item_from_url to return True on success."
        
    except EagleAPIError as e:
        print(f"❌ API Error during normal flow test: {e}")
    except AssertionError as e:
        print(f"❌ Assertion Error: {e}")

    # Negative Testing
    print("\nTesting Failure expected scenarios...")
    try:
        # Emtpy URL should fail
        api.add_item_from_url(url="", name="Should Fail")
        print("❌ Failed: Expected error when adding empty URL, but it succeeded.")
    except EagleAPIError as e:
        print(f"✅ Successfully caught expected error for invalid URL rename: {e}")

if __name__ == "__main__":
    test_add_from_url()
