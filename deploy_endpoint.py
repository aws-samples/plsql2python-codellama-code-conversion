#!/usr/bin/env python3

import sys
import boto3
import sagemaker
from sagemaker.jumpstart.model import JumpStartModel


def main(model_id: str, role_name: str | None = None,
         endpoint_name: str | None = None,
         instance_type: str = 'ml.g5.12xlarge'):
    """
    Deploy a SageMaker Endpoint for the provided model using the provided ARN

    Parameters
    ----------
    model_id : id of the model that you want to deploy
    role_name : Name of the execution role for the endpoint; use `None` to use the default SageMaker execution role.
    endpoint_name : Name for the endpoint to be deployed. If not provided, a unique name will be chosen automatically
    instance_type : id of the instance type to use for the real-time inference.
    """
    if role_name is None:
        role = sagemaker.get_execution_role()
    else:
        iam = boto3.client('iam')
        role = iam.get_role(RoleName=role_name)['Role']['Arn']
    model = JumpStartModel(model_id=model_id,
                           model_version='2.0.0',
                           role=role)
    example_payloads = model.retrieve_all_examples()

    # You must manually accept the end-user license agreement (EULA) to deploy the model.
    accept_eula = True

    if accept_eula:
        predictor = model.deploy(accept_eula=accept_eula,
                                 instance_type=instance_type,
                                 endpoint_name=endpoint_name)

        for payload in example_payloads:
            response = predictor.predict(payload.body)
            prompt = payload.body[payload.prompt_key]
            generated_text = response[0]["generated_text"]
            print("\nInput\n", prompt, "\n\nOutput\n\n", generated_text, "\n\n===============")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--role-name',
                        help='Role name to use instead of the default one')
    parser.add_argument('-m', '--model-id',
                        help='ID of the model to deploy',
                        default='meta-textgeneration-llama-codellama-13b-instruct')
    parser.add_argument('-e', '--endpoint-name',
                        help='Name for the deployed endpoint',
                        default='codellama-13b')
    parser.add_argument('-i', '--instance-type',
                        help='Type of the instance to use for deploying the endpoint',
                        default='ml.g5.12xlarge')
    parser.add_argument('--accept-license', action='store_true',
                        help='Flag to specify that you explicitly have reviewed '
                             'and accept the license terms of the model')
    args = parser.parse_args()

    if not args.accept_license:
        print(f'You must explicitly accept the model license to be able to deploy {args.model_id}')
        sys.exit(1)

    main(model_id=args.model_id,
         role_name=args.role_name,
         endpoint_name=args.endpoint_name,
         instance_type=args.instance_type)
