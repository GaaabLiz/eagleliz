import pytest
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from eagleliz.controller.media_org import MediaOrganizer
from eagleliz.model.organizer import OrganizerOptions
from pylizlib.media.lizmedia import LizMedia, LizMediaSearchResult, MediaStatus

@pytest.fixture
def dummy_media_result():
    def _create(path, tags=None):
        media = LizMedia(path)
        if tags:
            # Manually attach some metadata if needed, but MediaOrganizer 
            # uses media.year/month/day which LizMedia provides from file mtime by default
            pass
        return LizMediaSearchResult(
            status=MediaStatus.ACCEPTED,
            path=path,
            media=media
        )
    return _create

def test_media_organizer_basic_move(dummy_media_result):
    with TemporaryDirectory() as src_dir, TemporaryDirectory() as dst_dir:
        src_path = Path(src_dir)
        file_path = src_path / "test.jpg"
        file_path.write_bytes(b"content")
        
        item = dummy_media_result(file_path)
        options = OrganizerOptions(dry_run=False, copy=False)
        
        organizer = MediaOrganizer([item], dst_dir, options)
        organizer.organize()
        
        results = organizer.get_results()
        assert len(results) == 1
        assert results[0].success is True
        
        # Verify file moved
        assert not file_path.exists()
        dest_path = Path(results[0].destination_path)
        assert dest_path.exists()
        assert dest_path.name == "test.jpg"

def test_media_organizer_copy(dummy_media_result):
    with TemporaryDirectory() as src_dir, TemporaryDirectory() as dst_dir:
        src_path = Path(src_dir)
        file_path = src_path / "test.jpg"
        file_path.write_bytes(b"content")
        
        item = dummy_media_result(file_path)
        options = OrganizerOptions(dry_run=False, copy=True)
        
        organizer = MediaOrganizer([item], dst_dir, options)
        organizer.organize()
        
        assert file_path.exists() # Should still exist
        results = organizer.get_results()
        assert Path(results[0].destination_path).exists()

def test_media_organizer_dry_run(dummy_media_result):
    with TemporaryDirectory() as src_dir, TemporaryDirectory() as dst_dir:
        src_path = Path(src_dir)
        file_path = src_path / "test.jpg"
        file_path.write_bytes(b"content")
        
        item = dummy_media_result(file_path)
        options = OrganizerOptions(dry_run=True)
        
        organizer = MediaOrganizer([item], dst_dir, options)
        organizer.organize()
        
        assert file_path.exists()
        results = organizer.get_results()
        assert not Path(results[0].destination_path).exists()
        assert results[0].success is True # Should report success in dry run

def test_media_organizer_duplicate_skip(dummy_media_result):
    with TemporaryDirectory() as src_dir, TemporaryDirectory() as dst_dir:
        src_path = Path(src_dir)
        file_path = src_path / "test.jpg"
        file_path.write_bytes(b"content")
        
        item = dummy_media_result(file_path)
        options = OrganizerOptions(copy=True)
        
        # Manually create the duplicate at destination
        # We need to calculate where it would go.
        year, month = item.media.year, item.media.month
        target_folder = os.path.join(dst_dir, str(year), f"{month:02d}")
        os.makedirs(target_folder, exist_ok=True)
        target_path = os.path.join(target_folder, "test.jpg")
        Path(target_path).write_bytes(b"content")
        
        organizer = MediaOrganizer([item], dst_dir, options)
        organizer.organize()
        
        results = organizer.get_results()
        assert results[0].success is False
        assert "Duplicate skipped" in results[0].reason

def test_media_organizer_sidecars(dummy_media_result):
    with TemporaryDirectory() as src_dir, TemporaryDirectory() as dst_dir:
        src_path = Path(src_dir)
        file_path = src_path / "test.jpg"
        file_path.write_bytes(b"content")
        sidecar_path = src_path / "test.jpg.xmp"
        sidecar_path.write_bytes(b"xmp content")
        
        item = dummy_media_result(file_path)
        item.media.attach_sidecar_file(sidecar_path)
        
        options = OrganizerOptions(copy=True)
        organizer = MediaOrganizer([item], dst_dir, options)
        organizer.organize()
        
        results = organizer.get_results()
        # Should have 2 results: 1 for media, 1 for sidecar
        assert len(results) == 2
        assert results[0].source_file.name == "test.jpg"
        assert results[1].source_file.name == "test.jpg.xmp"
        assert Path(results[1].destination_path).exists()
