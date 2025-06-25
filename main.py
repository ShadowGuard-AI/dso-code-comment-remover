import argparse
import logging
import os
import re
import chardet
import io

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_argparse():
    """
    Sets up the argument parser for the command-line interface.
    """
    parser = argparse.ArgumentParser(description='Removes comments from source code files.')
    parser.add_argument('input_file', help='The input source code file.')
    parser.add_argument('output_file', help='The output file to write the sanitized code to.')
    parser.add_argument('--remove-all', action='store_true', help='Remove all comments, including copyright notices (USE WITH CAUTION).')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default='INFO', help='Set the logging level.')
    return parser

def detect_encoding(file_path):
    """
    Detects the encoding of a file using chardet.

    Args:
        file_path (str): The path to the file.

    Returns:
        str: The detected encoding, or None if detection fails.
    """
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            return result['encoding']
    except Exception as e:
        logging.error(f"Error detecting encoding: {e}")
        return None

def remove_comments(input_file, output_file, remove_all=False):
    """
    Removes comments from a source code file.

    Args:
        input_file (str): The path to the input file.
        output_file (str): The path to the output file.
        remove_all (bool): If True, removes all comments, including copyright notices.
    """
    try:
        encoding = detect_encoding(input_file)
        if not encoding:
            logging.error(f"Could not detect encoding for {input_file}.  Falling back to utf-8 but this may cause issues.")
            encoding = 'utf-8'

        with io.open(input_file, 'r', encoding=encoding) as infile:  # Using io.open for encoding
            code = infile.read()

        # Remove single-line comments (//)
        code = re.sub(r'//.*', '', code)

        # Remove multi-line comments (/* ... */)
        code = re.sub(r'/\*[\s\S]*?\*/', '', code)

        #Remove comments that start with a #
        code = re.sub(r'#.*', '', code)

        #Remove comments that start with a --
        code = re.sub(r'--.*', '', code)
        
        if not remove_all:
            # Preserve copyright notices (e.g., lines starting with "Copyright")
            copyright_pattern = r'^(Copyright.*)$'
            copyright_notices = re.findall(copyright_pattern, code, re.MULTILINE)
            preserved_code = '\n'.join(copyright_notices) + '\n' + code
        else:
             preserved_code = code


        with io.open(output_file, 'w', encoding=encoding) as outfile: # Using io.open for encoding
            outfile.write(preserved_code)

        logging.info(f"Comments removed from {input_file} and saved to {output_file}")

    except FileNotFoundError:
        logging.error(f"File not found: {input_file}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")


def main():
    """
    Main function to execute the comment removal tool.
    """
    parser = setup_argparse()
    args = parser.parse_args()

    # Set logging level
    logging.getLogger().setLevel(args.log_level)

    # Input validation
    if not os.path.isfile(args.input_file):
        logging.error(f"Error: Input file '{args.input_file}' does not exist.")
        return

    if os.path.exists(args.output_file):
        logging.warning(f"Warning: Output file '{args.output_file}' already exists. It will be overwritten.")


    # Call the comment removal function
    remove_comments(args.input_file, args.output_file, args.remove_all)


if __name__ == "__main__":
    main()