#!/usr/bin/env python3
"""
Text modifier script - merges lines starting with lowercase letters to the previous line.
"""
import sys
from pathlib import Path


def modify_text(input_file: str, output_file: str = None):
    """
    Modify text by appending lines that start with lowercase letters to the previous line.

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

    # Output the result
    output_text = '\n'.join(result)

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output_text)
        print(f"Modified text written to: {output_file}")
    else:
        print(output_text)


def main():
    if len(sys.argv) < 2:
        print("Usage: python text_mod.py <input_file> [output_file]")
        print("  input_file: Path to the text file to modify")
        print("  output_file: (Optional) Path to save the modified text")
        print("               If not provided, output is printed to stdout")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    # Check if input file exists
    if not Path(input_file).exists():
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)

    modify_text(input_file, output_file)


if __name__ == "__main__":
    main()
