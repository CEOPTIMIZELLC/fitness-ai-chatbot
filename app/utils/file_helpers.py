import os

def get_relative_path(file):

    # Get the absolute path of the current file
    directory_absolute_path = os.path.dirname(file)

    # Get the current working directory
    current_working_directory = os.getcwd()

    # Calculate the relative path
    relative_path = os.path.relpath(directory_absolute_path, current_working_directory)

    return relative_path

def create_file_if_not_exists(caller_file, file_name="file_name", file_type=".txt"):
    file_path = os.path.join(get_relative_path(caller_file), file_name+file_type)

    try:
        file = open(file_path, "x")
        file.close()
    except FileExistsError:
        print("File already exists.")
    return None