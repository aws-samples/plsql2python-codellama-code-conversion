#!/usr/bin/env python3

import re
import logging
from pathlib import Path
from converters import CodeConverter
from sagemaker.predictor import Predictor
from converters.exceptions import ConversionError
from converters.codellama_instruct import CodeLlamaConverter


def convert(converter: CodeConverter, code: str, max_retries: int = 3) -> str:
    """
    Try to convert the given PL/SQL code into Python code

    This function will try to make sure that the converted code is valid python code by
    compiling it and retrying to convert it if it does not compile.

    Parameters
    ----------
    converter: Converter to use for converting the code.
    code: String with the input source code.
    max_retries: Maximum number of retries for the generated code to compile.

    Returns
    -------
    The converted Python code.
    """
    routine_name = code.split("\n")[0]
    logging.info(f'\t\tConverting {routine_name}')
    # We'll try to convert the code
    for i in range(max_retries):
        try:
            converted = converter.convert(code, max_conversion_chunks=max_retries)
        except ConversionError as e:
            logging.warning(f'\t\t\tFailed to convert the code, retrying ({e})')
            continue

        # If the FM output is not complete, iterate to complete it
        try:
            compile(converted, filename='<string>', mode='exec')
            return converted
        except BaseException as e:
            logging.warning(f'\t\t\tFailed to compile the converted code, retrying ({e}')

    logging.error(f'\t\tCould not convert {routine_name} after {max_retries} retries, skipping')
    raise ConversionError()


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
                converted = convert(converter, routine_code)
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
    converter = CodeLlamaConverter(args.endpoint_name)
    for file in sorted(source_dir.glob('*.pkb')):
        convert_file(converter, file,
                     output_dir / file.with_suffix('.py').name,
                     errors_dir / file.name)
