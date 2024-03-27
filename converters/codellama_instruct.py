import re
import logging
from . import CodeConverter
from sagemaker.predictor import Predictor
from .exceptions import InputTooLongException
from sagemaker.serializers import JSONSerializer
from converters.exceptions import ConversionError
from sagemaker.deserializers import JSONDeserializer


class CodeLlamaConverter(CodeConverter):
    PROMPT_TEMPLATE = ("<s>[INST] <<SYS>>\n"
                       "You are an expert programmer that helps migrate PL/SQL logic into python "
                       "code, provide the answers in Python.\n"
                       "<</SYS>>\n"
                       "\n"
                       "Convert the following PL/SQL code assuming that the database connection "
                       "is passed as a parameter to the translated function, also assume that all "
                       "the called procedures have converted python functions, so DO NOT call "
                       "stored procedures directly in the code and instead call their equivalent "
                       "python functions:\n")
    MAX_NEW_TOKENS = 1024

    def __init__(self, sagemaker_endpoint: str):
        """
        CodeLlama Instruct-powered code converter

        This converter will work with the provided SageMaker endpoint for converting the given code
        """
        self.endpoint = sagemaker_endpoint
        self.predictor = Predictor(endpoint_name=sagemaker_endpoint,
                                   serializer=JSONSerializer(),
                                   deserializer=JSONDeserializer())

    def _construct_payload(self, original_code: str, max_new_tokens: int, converted_code: str = '') -> dict:
        """
        Construct the payload to be passed to the endpoint
        """
        payload = {"inputs": self.PROMPT_TEMPLATE,
                   "parameters": {"max_new_tokens": max_new_tokens, "top_p": 0.9, "temperature": 0.2,
                                  "decoder_input_details": False, "details": True}}
        payload['inputs'] += f'{original_code}[/INST]{converted_code}'

        return payload

    def _fm_eval(self, payload: dict):
        """
        Eval the given payload with the underlyinf Foundation Model

        Returns
        -------
        Model output, which will include free-form text and should also include a code block.
        """
        try:
            return self.predictor.predict(payload)
        except self.predictor.sagemaker_session.sagemaker_runtime_client.exceptions.ModelError as e:
            # This error code means that the context + output is too long for the model to handle -> fail
            match e.response['OriginalStatusCode']:
                case 422:
                    raise ConversionError('Context and requested output count too large, failing')
                case 424:
                    raise ConversionError('There was a CUDA error when attempting the code translation')
                case 0:
                    raise InputTooLongException('The input exceeds the max length for the input')
                case _:
                    raise ConversionError('Unknown error, failing ({e})')

    def _extract_code(self, response: dict) -> (str, bool):
        """
        Extract the converted code from the FM response.

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
