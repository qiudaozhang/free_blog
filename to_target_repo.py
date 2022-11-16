import os
import shutil


def remove_repo(parent_path):
    """
    移除旧的仓库
    :param parent_path:
    :return:
    """
    dirs = os.listdir(parent_path)
    for d in dirs:
        full_path = f"{parent_path}/{d}"
        if os.path.isdir(full_path):
            if d != ".git":
                shutil.rmtree(full_path)
        else:
            if d != "run.sh":
                os.remove(full_path)


def copy_a2b(from_path, to_path):
    shutil.copytree(from_path, to_path)
