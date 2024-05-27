import re
import json
import boto3
import botocore
from .base import CodeConverter
from converters.exceptions import BackendTimeoutError, ConversionError


class BedrockLlamaConverter(CodeConverter):
    PROMPT_TEMPLATE = ('<s>[INST] <<SYS>>\n'
                       'You are a profficient Oracle DBA and python programmer working on '
                       'upgrading database logic from PL/SQL to external python code.\n'
                       'Your task is to convert the given PL/SQL code to an equivalent '
                       'Python function, with the following requirements:\n\n'
                       '1. The database connection will be passed as a parameter to the translated Python function.\n'
                       '2. Any called stored procedures should be replaced with calls to their equivalent Python '
                       'functions (assume these Python functions already exist).\n'
                       '<</SYS>>\n'
                       '\n'
                       '''To convert the code, follow these steps:

1. Define a Python function with the same name as the PL/SQL code block.
2. Add a parameter to accept the database connection object.
3. Translate the PL/SQL code line-by-line to Python, making the following changes:
    - Replace PL/SQL variable declarations with Python variable assignments
    - Convert PL/SQL control structures (loops, conditionals) to their Python equivalents
    - Replace calls to stored procedures with calls to the corresponding Python functions, passing the database connection as a parameter
4. Return any values that the original PL/SQL code would have returned

Your converted Python code should have the following structure:

```python
def function_name(db_conn, ...):
    # Converted Python code goes here
    ...
    return ...
```

Make sure to handle database operations, such as queries and updates, by calling appropriate methods on the db_conn object instead of executing SQL directly.\n''')
    MAX_NEW_TOKENS = 2048

    def __init__(self, model_id: str = 'meta.llama3-8b-instruct-v1:0'):
        """
        CodeLlama Instruct-powered code converter

        This converter will work with the provided SageMaker endpoint for converting the given code
        """
        self.model_id = model_id
        self.client = boto3.client(service_name='bedrock-runtime')

    @property
    def fm_name(self) -> str:
        """
        Return the model name
        """
        return self.model_id

    def _construct_payload(self, original_code: str, max_new_tokens: int, converted_code: str = '') -> dict:
        """
        Construct the payload to be passed to the endpoint
        """
        # Force the output style to start with code, optionally filling in preexisting code
        payload = {'prompt': self.PROMPT_TEMPLATE,
                   'temperature': 0.2,
                   'top_p': 0.9,
                   'max_gen_len': max_new_tokens}
        payload['prompt'] += f'{original_code}[/INST]\n```python\n{converted_code}'.strip()

        return payload

    def _fm_eval(self, payload: dict):
        """
        Eval the given payload with the underlyinf Foundation Model

        Returns
        -------
        Model output, which will include free-form text and should also include a code block.
        """
        try:
            response = self.client.invoke_model(body=json.dumps(payload), modelId=self.model_id)
        except (botocore.exceptions.ReadTimeoutError, self.client.exceptions.ModelTimeoutException) as e:
            raise BackendTimeoutError(f'{e}')
        return json.loads(response.get('body').read())

    def _extract_code(self, response: dict, payload: dict) -> (str, bool):
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
        model_output = payload['prompt'] + response['generation']
        complete = (response['stop_reason'] == 'stop')
        # We expect start and optionally finish triple quotes
        matches = re.findall(r'```python\n([\s\S]*?)(?:```|\Z)',
                             model_output,
                             flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)
        match len(matches):
            case 2:
                # We found a code block -> extract it
                return matches[1].strip(), complete

        raise ConversionError('Could not extract code from the given text')
