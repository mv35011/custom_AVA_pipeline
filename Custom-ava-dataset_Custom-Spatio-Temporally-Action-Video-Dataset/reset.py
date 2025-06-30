import os
import shutil

target_dirs = [
    'Dataset/choose_frames',
    'Dataset/choose_frames_all',
    'Dataset/choose_frames_middle',
    'Dataset/videocrop',
    'Dataset/frames',
    'yolovDeepsort/yolov5/runs'
]

target_files = [
    'yolovDeepsort/mywork/dense_proposals_train.pkl'
]


def delete_contents(parent_dir):
    if os.path.exists(parent_dir):
        for entry in os.listdir(parent_dir):
            path = os.path.join(parent_dir, entry)
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                    print(f"Deleted directory: {path}")
                elif os.path.isfile(path):
                    os.remove(path)
                    print(f"Deleted file: {path}")
            except Exception as e:
                print(f"Failed to delete {path}: {e}")
    else:
        print(f"Directory does not exist: {parent_dir}")


def delete_files(file_paths):
    for file_path in file_paths:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Deleted file: {file_path}")
            except Exception as e:
                print(f"Failed to delete file {file_path}: {e}")
        else:
            print(f"File does not exist: {file_path}")


if __name__ == "__main__":
    for dir_path in target_dirs:
        delete_contents(dir_path)

    delete_files(target_files)
