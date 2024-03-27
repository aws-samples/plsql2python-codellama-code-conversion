#!/usr/bin/env python3

import re
import logging
from pathlib import Path
from converters import CodeConverter
from converters.exceptions import ConversionError
from converters import ClaudeConverter, CodeLlamaConverter


def convert_file(converter: CodeConverter, source_file: Path, output_file: Path, errors_file: Path) -> None:
    """
    Try to convert the functions in the given source file, one by one

    The FM-provided code will be checked to see if it compiles.

    Parameters
    ----------
    converter : Converter to use for converting the code
    source_file : Source file containing the Package Body definition
    output_file : File where the converted code should be dumped.
    errors_file: File where the code that could not be converted should be dumped
    """
    logging.info(f'Processing {source_file} -> {output_file}')
    package_source = source_file.read_text(errors='replace')

    with output_file.open('wt') as conversions, errors_file.open('wt') as errors:
        conversions.write('import cx_Oracle\n')
        # Find procedures / functions using regular expressions
        matches = re.findall('^(PROCEDURE|FUNCTION)(.*?)(^End;)',
                             package_source,
                             flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)
        for match in matches:
            routine_code = ''.join(match)
            logging.debug(f'Converting code: {routine_code}')
            try:
                routine_name = routine_code.split("\n")[0]
                logging.info(f'\t\tConverting {routine_name}')
                converted = converter.convert(routine_code)
            except ConversionError:
                errors.write(routine_code + '\n\n')
                errors.flush()
                continue

            converted = converted.replace('import cx_Oracle', '')
            conversions.write(converted + '\n\n')
            conversions.flush()


if __name__ == '__main__':
    import argparse

    # Set the default logging configuration
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    # Define the command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--endpoint-name',
                        help='Name of the SageMaker Endpoint to use for querying',
                        default='codellama-13b')
    args = parser.parse_args()

    # Loop through the files in the data directory, process them separately
    source_dir = Path('scripts')
    output_dir = Path('scripts/converted')
    output_dir.mkdir(exist_ok=True, parents=True)
    errors_dir = Path('scripts/non-converted')
    errors_dir.mkdir(exist_ok=True, parents=True)

    # Create the converter, translate the code
    converter = ClaudeConverter()
    for file in sorted(source_dir.glob('*.pkb')):
        convert_file(converter, file,
                     output_dir / file.with_suffix('.py').name,
                     errors_dir / file.name)
