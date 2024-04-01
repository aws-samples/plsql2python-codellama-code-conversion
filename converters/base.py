import logging
from converters.exceptions import ConversionError, InputTooLongException


class CodeConverter:
    MAX_NEW_TOKENS = 1024

    def convert(self, original_code: str, max_seeds: int = 3, max_conversion_chunks: int = 4, max_retries: int = 3):
        """
        Convert the given code block

        This function will call the FM and request it to translate the code in `original_code`
        from PL/SQL to Python. If `code_fragment` is provided, it will be used as a base for the
        translation.

        Parameters
        ----------
        original_code : Original code fragment
        max_seeds : Maximum number of times the whole conversion process can be retried. Since the code might
                    be converted in chunks, later chunks are dependant in the correctness of the first ones.
                    This parameter controls how many times can the whole process be done before failing.
        max_conversion_chunks : Maximum number of iterations on the code generation task. The routine might need to
                                iterate on the original code function body if it's too long and conversion must
                                be performed in chunks. This parameter identifies the maximum number of chunks that
                                are allowed per function.
        max_retries : Maximum number of retries in case of FM failure (per conversion chunk)

        Returns
        -------
        Model output, which will include free-form text and should also include a code block.
        """

        for _ in range(max_seeds):
            max_new_tokens = self.MAX_NEW_TOKENS
            code_fragment, complete = '', False
            i = 0
            while not complete and i < max_conversion_chunks:
                payload = self._construct_payload(original_code,
                                                  max_new_tokens=max_new_tokens,
                                                  converted_code=code_fragment)

                j = 0
                while j < max_retries:
                    try:
                        response = self._fm_eval(payload)
                        code_fragment, complete = self._extract_code(response)
                        break
                    except InputTooLongException as e:
                        # This error code means that the context + output is too long for the model to handle -> fail
                        max_new_tokens = int(0.7 * max_new_tokens)
                        payload = self._construct_payload(original_code,
                                                          max_new_tokens=max_new_tokens,
                                                          converted_code=code_fragment)
                        logging.warning(
                            '\t\t\tError calling the model, retrying with a smaller number of output tokens')
                        j += 1

                if j >= max_retries - 1:
                    print(j)
                    raise ConversionError(f'Could not construct the full code fragment after {max_retries} retries')

                i += 1

            if i >= max_conversion_chunks - 1:
                logging.warning(f'\t\t\tCould not convert the code after {max_conversion_chunks} completions, quitting')
                continue

            # We have a chunk of code, let's try to see if it's syntactically correct
            try:
                compile(code_fragment, filename='<string>', mode='exec')
                return code_fragment
            except BaseException as e:
                logging.warning(f'\t\t\tFailed to compile the converted code, retrying ({e})')
                logging.debug(code_fragment)
                continue

        raise ConversionError('Could not convert the code, failing')

    @property
    def fm_name(self) -> str:
        """
        Returns a brief string representing the model
        """
        raise NotImplementedError('This method must be implemented by derived classes')

    def _construct_payload(self, original_code: str, max_new_tokens: int, converted_code: str = '') -> dict:
        """
        Construct the payload to be passed to the endpoint

        Parameters
        ----------
        original_code: Original code to be translated
        max_new_tokens: The maximum number of tokens to be provided at the FM output
        converted_code: Code chunk that has already been converted by the FM
        """
        raise NotImplementedError('This method must be implemented by derived classes')

    def _fm_eval(self, payload: dict):
        """
        Eval the given payload with the underlyinf Foundation Model

        Parameters
        ----------
        payload: Dict with the payload to send to the FM for evaluation

        Returns
        -------
        Model output, which will include free-form text and should also include a code block.
        """
        raise NotImplementedError('This method must be implemented by derived classes')

    def _extract_code(self, response: dict) -> (str, bool):
        """
        Extract the converted code from the FM response.

        Parameters
        ----------
        response : The response from the FM

        Returns
        -------
        The extracted code block and a flag indicating whether the output block was complete or not
        It might not be complete if the FM ran out of output tokens.
        """
        raise NotImplementedError('This method must be implemented by derived classes')
