import argparse
import logging
import os
import sys
import re
import chardet
import io

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_argparse():
    """
    Sets up the argument parser for the command-line interface.
    """
    parser = argparse.ArgumentParser(description='Removes comments from source code files. Supported families: C style files (.c, .h, .cpp, .java, .js, .ts, .go, .rs and similar) use // and /* */ comments, hash files (.py, .sh, .rb and similar) use # comments, and .sql, .lua, and .hs files use -- comments. String literals are honoured in every family.')
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

C_LIKE_EXTS = {'.c', '.h', '.cpp', '.cc', '.cxx', '.hpp', '.java', '.js', '.jsx',
               '.ts', '.tsx', '.cs', '.go', '.rs', '.php', '.swift', '.kt',
               '.kts', '.scala', '.m', '.mm'}
HASH_EXTS = {'.py', '.sh', '.bash', '.rb', '.pl', '.pm', '.r', '.jl', '.ps1',
             '.yaml', '.yml', '.toml'}
DASH_EXTS = {'.sql', '.lua', '.hs'}

def family_for(input_file):
    """Return the comment syntax family for a file, by extension."""
    ext = os.path.splitext(input_file)[1].lower()
    if ext in C_LIKE_EXTS:
        return 'c'
    if ext in HASH_EXTS:
        return 'hash'
    if ext in DASH_EXTS:
        return 'dash'
    return 'generic'

def strip_comments(code, family, input_file, remove_all=False):
    """Strip true comments with a string aware scanner.

    Returns (new_code, removed_count, preserved_copyright_comments).
    String literals (single quoted, double quoted, backtick for C style
    script files, and triple quoted for Python) are copied untouched,
    so comment markers inside strings are never treated as comments.
    An operator sequence such as -- is a comment start only in the
    dash family, where the syntax defines it as one.
    """
    ext = os.path.splitext(input_file)[1].lower()
    line_tokens = []
    block = None
    if family in ('c', 'generic'):
        line_tokens.append('//')
        block = ('/*', '*/')
    if family in ('hash', 'generic'):
        line_tokens.append('#')
    if family == 'dash':
        line_tokens.append('--')
        block = ('/*', '*/')
    backtick_strings = ext in ('.js', '.jsx', '.ts', '.tsx')
    triple_strings = ext == '.py'

    out = []
    preserved = []
    count = 0
    i = 0
    n = len(code)
    while i < n:
        # Shebang line in hash files is not a comment to strip.
        if i == 0 and code.startswith('#!'):
            eol = code.find('\n', i)
            if eol == -1:
                eol = n
            out.append(code[i:eol])
            i = eol
            continue
        # Block comment start.
        if block and code.startswith(block[0], i):
            end = code.find(block[1], i + len(block[0]))
            if end == -1:
                comment_text = code[i:]
                i = n
            else:
                comment_text = code[i:end + len(block[1])]
                i = end + len(block[1])
            count += 1
            if not remove_all and 'Copyright' in comment_text:
                preserved.append(comment_text.strip())
            continue
        # Line comment start.
        matched_line = None
        for token in line_tokens:
            if code.startswith(token, i):
                matched_line = token
                break
        if matched_line is not None:
            eol = code.find('\n', i)
            if eol == -1:
                eol = n
            comment_text = code[i:eol]
            count += 1
            if not remove_all and 'Copyright' in comment_text:
                preserved.append(comment_text.strip())
            i = eol
            continue
        ch = code[i]
        # String literal start.
        if ch in ('"', "'") or (ch == '`' and backtick_strings):
            quote = ch
            if triple_strings and code.startswith(quote * 3, i):
                endmark = quote * 3
                j = i + 3
                buf = [endmark]
                closed = False
                while j < n:
                    if code[j] == '\\' and j + 1 < n:
                        buf.append(code[j:j + 2])
                        j += 2
                        continue
                    if code.startswith(endmark, j):
                        buf.append(endmark)
                        j += 3
                        closed = True
                        break
                    buf.append(code[j])
                    j += 1
                out.append(''.join(buf))
                i = j
                continue
            j = i + 1
            buf = [quote]
            while j < n:
                c = code[j]
                if c == '\\' and j + 1 < n:
                    buf.append(code[j:j + 2])
                    j += 2
                    continue
                if c == quote:
                    buf.append(c)
                    j += 1
                    break
                if c == '\n' and quote != '`':
                    break
                buf.append(c)
                j += 1
            out.append(''.join(buf))
            i = j
            continue
        out.append(ch)
        i += 1
    return ''.join(out), count, preserved

def remove_comments(input_file, output_file, remove_all=False):
    """
    Removes comments from a source code file.

    Returns the number of comments removed. When the count is zero,
    no output file is written.
    """
    try:
        encoding = detect_encoding(input_file)
        if not encoding:
            logging.error(f"Could not detect encoding for {input_file}.  Falling back to utf-8 but this may cause issues.")
            encoding = 'utf-8'

        with io.open(input_file, 'r', encoding=encoding) as infile:  # Using io.open for encoding
            code = infile.read()

        family = family_for(input_file)
        stripped, count, preserved = strip_comments(code, family, input_file, remove_all)

        if count == 0:
            logging.info("No comments removed.")
            return 0

        if preserved:
            preserved_code = '\n'.join(preserved) + '\n' + stripped
        else:
            preserved_code = stripped

        with io.open(output_file, 'w', encoding=encoding) as outfile: # Using io.open for encoding
            outfile.write(preserved_code)

        logging.info(f"Comments removed from {input_file} and saved to {output_file}: {count} removed")
        return count

    except FileNotFoundError:
        logging.error(f"File not found: {input_file}")
        raise
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise


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
        sys.exit(1)

    if os.path.realpath(args.output_file) == os.path.realpath(args.input_file):
        logging.error("Refusing to run: output path resolves to the input file.")
        sys.exit(1)

    if os.path.exists(args.output_file):
        logging.warning(f"Warning: Output file '{args.output_file}' already exists. It will be overwritten.")


    # Call the comment removal function
    try:
        removed = remove_comments(args.input_file, args.output_file, args.remove_all)
    except Exception:
        sys.exit(1)
    if removed == 0:
        print("No comments removed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
