import uuid
import os
import tempfile
from eagleliz.api.eaglelizapi import EagleAPI, EagleAPIError, EagleItemURLPayload

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
        
        # Test 2: Batch Add from URLs
        print("\nAttempting to batch add images from URLs...")
        
        item1 = EagleItemURLPayload(
            url="https://picsum.photos/400/300?random=1",
            name=f"Batch Image 1 {unique_suffix}",
            website="https://picsum.photos",
            tags=["AI_Test_Tag", "Batch", "Picsum"],
            annotation="First image of the batch test."
        )
        
        item2 = EagleItemURLPayload(
            url="https://picsum.photos/400/300?random=2",
            name=f"Batch Image 2 {unique_suffix}",
            website="https://picsum.photos",
            tags=["AI_Test_Tag", "Batch", "Picsum"],
            annotation="Second image of the batch test."
        )
        
        success_batch = api.add_items_from_urls(
            items=[item1, item2],
            folder_id=folder_id
        )
        
        print(f"✅ Batch Add from URLs Success: {success_batch}")
        assert success_batch is True, "Expected add_items_from_urls to return True on success."
        
        # Test 3: Add from Path
        print("\nAttempting to add image from local Path...")
        # Create a tiny temporary text file to act as the "image/item" since Eagle accepts any file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w") as temp_file:
            temp_file.write("Dummy test content for Eagle API addFromPath")
            temp_path = temp_file.name
        
        try:
            success_path = api.add_item_from_path(
                path=temp_path,
                name=f"Local Path File {unique_suffix}",
                tags=["AI_Test_Tag", "LocalPath"],
                annotation="This file was injected from a local temp directory.",
                folder_id=folder_id
            )
            print(f"✅ Add from Path Success: {success_path}")
            assert success_path is True, "Expected add_item_from_path to return True on success."
        finally:
            # Cleanup temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
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
