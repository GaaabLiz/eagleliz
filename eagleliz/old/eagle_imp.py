# from typing import List
#
# import rich
# import typer
# from yaspin import yaspin
#
# from core.api.data import eagleapi
# from core.api.service import eagleliz
# from core.controller.scan import scan_image
# from core.model.ailiz_image import AilizImage
# from util import osutils
#
#
# def eagle_dir_importer(
#         input_path: str,
#         ai_comment: bool = False,
#         ai_tag: bool = False,
#         ai_metadata: bool = False,
#         ai_rename: bool = False,
# ):
#
#     # Check if the path is valid
#     try:
#         osutils.check_path_2(input_path)
#     except Exception as e:
#         rich.print(f"Error while checking input path: {e}")
#         print("Make sure the path is valid and try again.")
#         raise typer.Exit()
#
#     # Check eagle connection
#     eagle_status = eagleliz.check_eagle()
#     if eagle_status is None:
#         raise typer.Exit()
#
#     # Scan input path
#     rich.print(f"Scanning input path: {input_path}")
#     file_count = osutils.count_pathsub_elements(input_path)
#     input_image_files_paths = osutils.scan_directory_match_bool(input_path, osutils.is_image_file)
#     input_video_files_paths = osutils.scan_directory_match_bool(input_path, osutils.is_video_file)
#     count_media_files_paths = len(input_image_files_paths) + len(input_video_files_paths)
#     rich.print(f"Found {len(input_image_files_paths)} image files in {input_path}")
#     rich.print(f"Found {len(input_video_files_paths)} video files in {input_path}")
#     # rich.print(f"Found {count_media_files_paths}/{file_count} media files in total.")
#
#     # Check if needs ai scan
#     with_ai = ai_comment or ai_tag or ai_metadata or ai_rename
#
#     # Scanning media files found
#     scanned_images: List[AilizImage] = []
#     for image_path in input_image_files_paths:
#         result = scan_image(image_path, with_ai)
#         if result is not None:
#             scanned_images.append(result)
#             rich.print(f"Loaded image: {result}")
#             with yaspin(text="Uploading image" + result.path + " to eagle", color="yellow", side="right") as spinner:
#                 result = eagleliz.upload_image(result)
#             if result is not None:
#                 spinner.ok("✅ ")
#             else:
#                 spinner.fail("💥 ")
#                 rich.print("Error while adding image to eagle.")
#         else:
#             rich.print(f"Image {image_path} will be skipped.")
#
#     # Scanning video files found
#
#
#
#
