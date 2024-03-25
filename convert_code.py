#!/usr/bin/env python3

import re
import logging
from pathlib import Path
from exceptions import ConversionError
from sagemaker.predictor import Predictor
from sagemaker.serializers import JSONSerializer
from sagemaker.deserializers import JSONDeserializer


def extract_code(response: dict) -> (str, bool):
    """
    Extract the code from the FM response.

    The FM response is expected to be delimited with markdown-style triple quotes (```) or
    the full model output should contain code.

    The way in which the code detects whether the model's output was complete depends on how the
    code is present in its output:
    * The code is delimited by triple-quotes: The code will check for the existance of closing
      triple quotes.
    * The full answer is code: The value of the `finish_reason` entry will be checked, if it's
      `eos_token` then the output is considered complete.

    Parameters
    ----------
    response : The SageMaker Endpoint-provided response from the FM

    Returns
    -------
    The extracted code block and a flag indicating whether the output block was complete or not
    It might not be complete if the FM ran out of output tokens.
    """
    # Extract the text response from the model

    model_output = response[0]['generated_text']
    # We expect start and optionally finish triple quotes
    matches = re.findall('^(```python|```)((.[^`])+)(^```|$)?',
                         model_output,
                         flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)
    match len(matches):
        case 0:
            if model_output.strip().startswith('def '):
                return model_output, (response[0]['details']['finish_reason'] == 'eos_token')
        case 1:
            return matches[0][1].strip(), len(matches[0][3]) == 3

    raise ConversionError('Could not extract code from the given text')


def _convert(predictor: Predictor, original_code: str, max_iterations: int = 3):
    """
    Convert the given code block, optionally using a pre-existing block as starting block

    This function will call the FM and request it to translate the code in `original_code`
    from PL/SQL to Python. If `code_fragment` is provided, it will be used as a base for the
    translation.

    Parameters
    ----------
    predictor : FM Predictor to use.
    original_code : Original code fragment.
    max_iterations : Maximum number of iterations on the code generation task. The routine might need to
                     retry if the converted function code has more tokens than the maximum output tokens
                     for the model.

    Returns
    -------
    Model output, which will include free-form text and should also include a code block.
    """
    max_new_tokens = 1024

    payload = {"inputs": "<s>[INST] <<SYS>>\n"
                         "You are an expert programmer that helps migrate PL/SQL logic into python "
                         "code, provide the answers in Python.\n"
                         "<</SYS>>\n"
                         "\n"
                         "Convert the following PL/SQL code assuming that the database connection "
                         "is passed as a parameter to the translated function, also assume that all "
                         "the called procedures have converted python functions, so DO NOT call "
                         "stored procedures directly in the code and instead call their equivalent "
                         "python functions:\n",
               "parameters": {"max_new_tokens": max_new_tokens, "top_p": 0.9, "temperature": 0.2,
                              "decoder_input_details": False, "details": True}}
    payload['inputs'] += f'{original_code}[/INST]'

    i = 0
    response = {}
    while i < max_iterations:
        try:
            response = predictor.predict(payload)
            break
        except predictor.sagemaker_session.sagemaker_runtime_client.exceptions.ModelError as e:
            # This error code means that the context + output is too long for the model to handle -> fail
            match e.response['OriginalStatusCode']:
                case 422:
                    raise ConversionError('Context and requested output count too large, failing')
                case 424:
                    raise ConversionError('There was a CUDA error when attempting the code translation')
                case 0:
                    max_new_tokens = int(0.7 * max_new_tokens)
                    payload['parameters']['max_new_tokens'] = max_new_tokens
                    logging.warning('\t\t\tError calling the model, retrying with a smaller number of output tokens')
                    i += 1
                case _:
                    raise ConversionError('Unknown error, failing ({e})')

    if i >= max_iterations - 1:
        print(i)
        raise ConversionError('Too many timeout errors in the server, quitting')

    code_fragment, complete = extract_code(response)
    i = 0
    while not complete and i < max_iterations:
        logging.info('\t\t\tConverted code is incomplete, iterating...')
        payload = {"inputs": "<s>[INST] <<SYS>>\n"
                             "You are an expert programmer that helps migrate PL/SQL logic into python "
                             "code, provide the answers in Python.\n"
                             "<</SYS>>\n"
                             "\n"
                             "Convert the following PL/SQL code assuming that the database connection "
                             "is passed as a parameter to the translated function, also assume that all "
                             "the called procedures have converted python functions, so DO NOT use "
                             "cursor.callproc calls in your code:\n",
                   "parameters": {"max_new_tokens": max_new_tokens, "top_p": 0.9, "temperature": 0.2,
                                  "decoder_input_details": False, "details": True}}
        payload['inputs'] += f'{original_code}[/INST]\n{code_fragment}'

        j = 0
        response = {}
        while j < max_iterations:
            try:
                response = predictor.predict(payload)
                break
            except predictor.sagemaker_session.sagemaker_runtime_client.exceptions.ModelError as e:
                # This error code means that the context + output is too long for the model to handle -> fail
                match e.response['OriginalStatusCode']:
                    case 422:
                        raise ConversionError('Context and requested output count too large, failing')
                    case 424:
                        raise ConversionError('There was a CUDA error when attempting the code translation')
                    case 0:
                        max_new_tokens = int(0.7 * max_new_tokens)
                        payload['parameters']['max_new_tokens'] = max_new_tokens
                        logging.warning('\t\tError calling the model, retrying with a smaller number of output tokens')
                        j += 1
                    case _:
                        raise ConversionError('Unknown error, failing ({e})')

        if j >= max_iterations - 1:
            print(j)
            raise ConversionError(f'Could not construct the full code fragment after {max_iterations} iterations')

        if len(response) != 1:
            raise ConversionError('Error parsing the converted output')
        code_fragment += response[0]['generated_text']
        if response[0]['details']['finish_reason'] == 'eos_token':
            break

        i += 1

        if i >= max_iterations - 1:
            logging.error(f'\t\t\tCould not convert the code after {max_iterations} completions, quitting')
            raise ConversionError('Maximum iterations reached')

    return code_fragment


def convert(predictor: Predictor, code: str, max_retries: int = 3) -> str:
    """
    Try to convert the given PL/SQL code into Python code

    This function will try to make sure that the converted code is valid python code by
    compiling it and retrying to convert it if it does not compile.

    Parameters
    ----------
    predictor: Predictor to use for converting the code.
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
            converted = _convert(predictor, code, max_iterations=max_retries)
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


def convert_file(predictor: Predictor, source_file: Path, output_file: Path, errors_file: Path) -> None:
    """
    Try to convert the functions in the given source file, one by one

    The FM-provided code will be checked to see if it compiles.

    Parameters
    ----------
    predictor : SageMaker Predictor to use for querying the FM model
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
                converted = convert(predictor, routine_code)
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

    # Create a Predictor for the endpoint, make sure to use the proper serializer & deserialized for convenience
    fm_predictor = Predictor(endpoint_name=args.endpoint_name,
                             serializer=JSONSerializer(),
                             deserializer=JSONDeserializer())

    # Loop through the files in the data directory, process them separately
    source_dir = Path('scripts')
    output_dir = Path('scripts/converted')
    output_dir.mkdir(exist_ok=True, parents=True)
    errors_dir = Path('scripts/non-converted')
    errors_dir.mkdir(exist_ok=True, parents=True)
    for file in sorted(source_dir.glob('*.pkb')):
        convert_file(fm_predictor, file,
                     output_dir / file.with_suffix('.py').name,
                     errors_dir / file.name)
