import os
import replicate
from loguru import logger
from src.gcp_utils import (get_secret_from_gcp,
                           get_gcp_project_id_from_env_var,
                           TEAM_SECRETS_GCP_PROJECT_SECRET_ID)


def get_stable_creds(gcp_project_id):
    """Get an api key for GPT3 from GCP Secret Manager service

    Args:
        gcp_project_id (str): For retrieving the GCP Project ID that holds the
            wanted secret (since the wanted secret is for the team, not an
            individual).

    Returns:
        dict (gpt3_creds_dict): Keys include 'api_key'.
    """
    logger.info('Getting Replicate Stability Diffusion API key \
                from GCP Secrets Manager')
    team_secrets_project_id = get_secret_from_gcp(
        gcp_project_id=gcp_project_id,
        secret_id=TEAM_SECRETS_GCP_PROJECT_SECRET_ID)

    stable_creds_dict = get_secret_from_gcp(
        gcp_project_id=team_secrets_project_id,
        secret_id='stable-diffusion-api-key', is_json=True)
    return stable_creds_dict


def get_stable_creds_and_set_as_env_vars():
    """Get credentials for ReplicateAPI from GCP Secret Manager service and
    set the credentials as environment variables
    """
    gcp_project_id = get_gcp_project_id_from_env_var()
    team_secrets_project_id = get_secret_from_gcp(
        gcp_project_id=gcp_project_id,
        secret_id=TEAM_SECRETS_GCP_PROJECT_SECRET_ID)

    stable_creds_dict = get_secret_from_gcp(
        gcp_project_id=team_secrets_project_id,
        secret_id='stable-diffusion-api-key', is_json=True)

    logger.info("setting stable diffusion replicate credentials as an \
                environment variable")
    os.environ["REPLICATE_API_TOKEN"] = stable_creds_dict['api_key']


def get_stable_image(prompt, model='sdxl'):
    """Get images from Replicate Stable Diffusion API

    Args:
        prompt (str): Prompt for generating the image using Stable Diffusion
        model (str): Choose from 'normal' (stable diffusion model) or the new
            SDXL 'sdxl'

    Returns:
        str: url of image returned from Replicate
    """
    logger.info(
        f"Sending prompt to Replicate Stable Diffusion {model} model...")
    if model == 'sdxl':
        output = replicate.run(
            "stability-ai/sdxl:2b017d9b67edd2ee1401238df49d75da53c523f36e363881e057f5dc3ed3c5b2",
            input={"prompt": prompt,
                   "num_inference_steps": 200}
        )

    elif model == 'normal':
        output = replicate.run(
            "stability-ai/stable-diffusion:27b93a2413e7f36cd83da926f3656280b2931564ff050bf9575f1fdf9bcd7478",
            input={"prompt": prompt,
                   "num_inference_steps": 150}
        )

    else:
        ValueError(f'Model {model} not recognized')

    return output[0]


def add_details_for_stable(prompt):
    """Adds prompt details to main GPT4 generated prompt for images.

    Args:
        prompt (str): GPT4 prompt for Stable Diffusion

    Returns:
        str: prompt with added details.
    """
    logger.info("Adding additional parameters for Stable Diffusion for \
                improved image rendering")
    details = ', 8k, soft lighting, highly detailed, digital painting by \
        Android Jones'
    new_prompt = prompt + details
    return new_prompt


if __name__ == "__main__":
    os.environ['GCP_PROJECT_ID'] = 'wpp-cto-os-intlignce-layer-dev'
    get_stable_creds_and_set_as_env_vars()
    link = get_stable_image(
        'principal campaign image featuring a diverse group of strong, confident women wearing Lululemon activewear, 8k, digital painting by Android Jones')
    print(f"Here is your image: {link}")
