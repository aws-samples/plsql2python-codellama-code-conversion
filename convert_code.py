#!/usr/bin/env python3

import re
import logging
from pathlib import Path
from converters import CodeConverter
from converters.exceptions import ConversionError
from converters import BedrockLlamaConverter, ClaudeConverter, CodeLlamaConverter


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
                logging.info(f'\t\tFailed to convert procedure, failing...')
                errors.write(routine_code + '\n\n')
                errors.flush()
                continue

            converted = converted.replace('import cx_Oracle', '')
            conversions.write(converted + '\n\n')
            conversions.flush()


if __name__ == '__main__':
    import argparse

    # Define the command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--sources_dir',
                        help='Path to the directory containing the source files to be translated',
                        type=Path, default='scripts')
    parser.add_argument('-d', '--debug',
                        action='store_true', help='Enable debugging')
    subparsers = parser.add_subparsers(dest='command')
    subparsers.required = True
    bedrock = subparsers.add_parser('bedrock', help='Convert the code with Amazon Bedrock')
    bedrock.add_argument('-m', '--model_id',
                         help='Model to use with Amazon Bedrock',
                         default='anthropic.claude-3-sonnet-20240229-v1:0',
                         choices=['anthropic.claude-3-haiku-20240307-v1:0',
                                  'anthropic.claude-3-sonnet-20240229-v1:0',
                                  'meta.llama3-8b-instruct-v1:0',
                                  'meta.llama3-70b-instruct-v1:0'])
    sagemaker = subparsers.add_parser('sagemaker', help='Convert the code with a SageMaker endpoint')
    sagemaker.add_argument('-e', '--endpoint-name',
                           help='Name of the CodeLlama-Instruct backed SageMaker Endpoint to use for querying',
                           default='codellama-13b')
    args = parser.parse_args()

    # Set the default logging configuration
    logging.basicConfig()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    # Create the converter, translate the code
    match args.command:
        case 'bedrock':
            if args.model_id.startswith('anthropic'):
                converter = ClaudeConverter(model_id=args.model_id)
            elif args.model_id.startswith('meta'):
                converter = BedrockLlamaConverter(model_id=args.model_id)
            else:
                # You should not be here, argparse shouldn't have let you
                raise RuntimeError('Model ID not supported')
        case 'sagemaker':
            converter = CodeLlamaConverter(sagemaker_endpoint=args.endpoint_name)
        case _:
            raise RuntimeError('You should not be here...')

    # Loop through the files in the data directory, process them separately
    if not args.sources_dir.is_dir():
        raise ValueError(f'Could not find the given directory {args.sources_dir}')
    output_dir = args.sources_dir / 'converted' / converter.fm_name
    output_dir.mkdir(exist_ok=True, parents=True)
    errors_dir = args.sources_dir / 'non-converted' / converter.fm_name
    errors_dir.mkdir(exist_ok=True, parents=True)

    logging.info(f'Using {args.command} - {converter.fm_name} to convert the code')

    for file in sorted(args.sources_dir.glob('*.pkb')):
        convert_file(converter, file,
                     output_dir / file.with_suffix('.py').name,
                     errors_dir / file.name)
