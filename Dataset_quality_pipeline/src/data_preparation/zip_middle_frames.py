import zipfile
import os
from pathlib import Path


def zip_subdirectories(source_dir, output_dir):
    """
    Zip each subdirectory in source_dir individually and save to output_dir

    Args:
        source_dir (Path): Path to the choose_middle_frames directory
        output_dir (Path): Path to the directory where zip files will be saved
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    subdirs = [d for d in source_dir.iterdir() if d.is_dir()]
    try:
        subdirs.sort(key=lambda x: int(x.name))
    except ValueError:
        subdirs.sort(key=lambda x: x.name)

    print(f"Found {len(subdirs)} subdirectories to zip")

    for subdir in subdirs:
        zip_filename = f"{subdir.name}.zip"
        zip_path = output_dir / zip_filename

        print(f"Creating {zip_filename}...")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in subdir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(subdir)
                    zipf.write(file_path, arcname)

        print(f"✓ Created {zip_filename} with {len(list(subdir.rglob('*')))} files")

    print(f"\nAll zip files created in: {output_dir}")


def main():
    parent = Path(__file__).parent.parent.parent
    source_directory = parent/ "data" / "Dataset" / "choose_frames_middle"
    output_directory = parent/ "data" / "Dataset" / "zip_choose_frames_middle"
    if not source_directory.exists():
        print(f"Error: Source directory '{source_directory}' does not exist")
        return
    zip_subdirectories(source_directory, output_directory)


if __name__ == "__main__":
    main()