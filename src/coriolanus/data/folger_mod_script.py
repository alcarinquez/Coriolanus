"""
Text modifier script - processes all texts in folger-txt-org/ directory.
Merges lines starting with lowercase letters and reduces consecutive newlines.
"""
import sys
import re
from pathlib import Path


def reduce_consecutive_newlines(text: str) -> str:
    """
    Reduce all consecutive newlines to at most 1 empty line (2 newlines total).

    Args:
        text: Input text with potentially many consecutive newlines

    Returns:
        Text with consecutive newlines reduced to maximum 2 newlines (1 empty line)
    """
    # Replace 3 or more consecutive newlines with exactly 2 newlines (1 empty line)
    return re.sub(r'\n{3,}', '\n\n', text)


def modify_text(input_file: str, output_file: str = None):
    """
    Modify text by appending lines that start with lowercase letters to the previous line,
    and reducing consecutive newlines to 1 empty line maximum.

    Args:
        input_file: Path to the input text file
        output_file: Path to the output file (if None, prints to stdout)
    """
    # Read all lines from the file
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Process lines from end to beginning
    # We go backwards so we can safely modify the list
    result = []
    i = len(lines) - 1

    while i >= 0:
        current_line = lines[i].rstrip('\n')

        # Check if current line starts with lowercase letter
        if current_line and current_line[0].islower() and i > 0:
            # This line should be appended to the line above
            # We'll collect all consecutive lowercase-starting lines
            lines_to_append = [current_line]
            i -= 1

            # Keep going backwards to collect all lowercase-starting lines
            while i >= 0 and lines[i].strip() and lines[i][0].islower():
                lines_to_append.insert(0, lines[i].rstrip('\n'))
                i -= 1

            # Now we're at a line that doesn't start with lowercase (or beginning)
            if i >= 0:
                base_line = lines[i].rstrip('\n')
                # Append all the lowercase lines to this base line
                merged_line = base_line + ' ' + ' '.join(lines_to_append)
                result.insert(0, merged_line)
                i -= 1
            else:
                # Edge case: all lines start with lowercase
                result.insert(0, ' '.join(lines_to_append))
        else:
            # Line doesn't start with lowercase, add as-is
            result.insert(0, current_line)
            i -= 1

    # Join the result and reduce consecutive newlines
    output_text = '\n'.join(result)
    output_text = reduce_consecutive_newlines(output_text)

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output_text)
    else:
        print(output_text)


def get_output_filename(input_filename: str) -> str:
    """
    Transform filename by replacing everything after (including) 'TXT' with 'folger_mod'.

    Args:
        input_filename: Original filename (e.g., 'hamlet_TXT_FolgerShakespeare.txt')

    Returns:
        Modified filename (e.g., 'hamlet_folger_mod.txt')
    """
    # Find the position of 'TXT' (case insensitive)
    txt_pos = input_filename.upper().find('TXT')

    if txt_pos != -1:
        # Get the part before TXT and the file extension
        base_name = input_filename[:txt_pos]
        # Find the extension from the original filename
        original_path = Path(input_filename)
        ext = original_path.suffix if original_path.suffix else '.txt'
        return f"{base_name}folger_mod{ext}"
    else:
        # If no TXT found, just append _folger_mod before extension
        path = Path(input_filename)
        return f"{path.stem}_folger_mod{path.suffix}"


def process_all_files():
    """
    Process all text files in texts/folger-txt-org/ directory.
    """
    # Define directories
    input_dir = Path("texts/folger-txt-org")
    output_dir = Path("texts/folger-txt-mod")

    # Check if input directory exists
    if not input_dir.exists():
        print(f"Error: Input directory '{input_dir}' not found")
        sys.exit(1)

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir}")
    print()

    # Get all text files from input directory
    text_files = sorted(input_dir.glob("*.txt"))

    if not text_files:
        print(f"No .txt files found in {input_dir}")
        return

    print(f"Found {len(text_files)} text file(s) to process")
    print("=" * 60)

    # Process each file
    for idx, input_file in enumerate(text_files, 1):
        print(f"\n[{idx}/{len(text_files)}] Processing: {input_file.name}")

        # Generate output filename
        output_filename = get_output_filename(input_file.name)
        output_file = output_dir / output_filename

        print(f"    → Output: {output_filename}")

        try:
            # Process the file
            modify_text(str(input_file), str(output_file))
            print(f"    ✓ Success")
        except Exception as e:
            print(f"    ✗ Error: {e}")

    print("\n" + "=" * 60)
    print(f"Processing complete! Modified files saved to: {output_dir}")


def main():
    """
    Main entry point - processes all files in texts/folger-txt-org/
    """
    print("Shakespeare Text Modifier")
    print("=" * 60)
    process_all_files()


if __name__ == "__main__":
    main()
