import os
import gzip
import shutil

# Directory containing the files
directory = "./downloads"

# Walk through the directory to process each file
for root, dirs, files in os.walk(directory):
    for file in files:
        # Get the full path to the file
        file_path = os.path.join(root, file)

        # Define the output path using the last directory of the path
        last_directory = os.path.basename(root)
        output_filename = last_directory + ".lottie"
        output_path = os.path.join(directory, output_filename)

        # Gzip the file
        with open(file_path, 'rb') as f_in:
            with gzip.open(output_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

print("Compression completed.")
