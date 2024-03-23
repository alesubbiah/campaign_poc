from loguru import logger
import openai
import json
from pathlib import Path
from src.gcp_utils import (get_secret_from_gcp,
                           TEAM_SECRETS_GCP_PROJECT_SECRET_ID,
                           get_gcp_project_id_from_env_var)


gcp_project_id = 'wpp-cto-os-intlignce-layer-dev'


def get_openai_creds(gcp_project_id):
    """Get an api key for GPT3 from GCP Secret Manager service

    Args:
        gcp_project_id (str): For retrieving the GCP Project ID that holds the
            wanted secret (since the wanted secret is for the team, not an
            individual).

    Returns:
        dict (gpt3_creds_dict): Keys include 'api_key'.
    """
    logger.info('Getting OpenAI API Azure key from GCP Secrets Manager')
    team_secrets_project_id = get_secret_from_gcp(
        gcp_project_id=gcp_project_id,
        secret_id=TEAM_SECRETS_GCP_PROJECT_SECRET_ID)

    gpt3_creds_dict = get_secret_from_gcp(
        gcp_project_id=team_secrets_project_id,
        secret_id='azure-openai-creds-us-json', is_json=True)
    return gpt3_creds_dict


def get_gpt4_campaign_response(user_input,
                               type='gpt4',
                               openai_type='azure',
                               gpt4_creds_dict=None):
    """Get text response from GPT4 Azure

    Args:
        user_input (str): User query / question
        type (str): Type of prompt to send to GPT4 (either normal or events)
        gpt4_creds_dict (dict, optional): Specific creds for GPT4 in Azure.
                                          Defaults to None.

    Returns:
        str: Text response from GPT4
    """

    if gpt4_creds_dict is None:
        gcp_project_id = get_gcp_project_id_from_env_var()
        gpt4_creds_dict = get_openai_creds(
            gcp_project_id=gcp_project_id)
    messages = _get_newgpt_prompt(type=type)
    prompt = _add_role_user(user_input, messages)
    logger.info('Setting azure creds to send to openai')
    if openai_type == 'azure':
        _set_openai_to_azure(azure_openai_creds_dict=gpt4_creds_dict)
    elif openai_type == 'openai':
        _set_openai(openai_creds=gpt4_creds_dict)

    logger.info('Getting campaign from GPT4')
    prompt = _add_role_user(user_input, messages)
    response = openai.ChatCompletion.create(
        engine="GPT-4",
        messages=prompt,
        temperature=0.8,
        max_tokens=1200,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None)

    text_response = response["choices"][0]["message"]["content"]
    return text_response


def get_gpt4_insta_response(user_input, campaign, gpt4_creds_dict=None):
    """Get text response from GPT4 azure (for instagram posts specifically
    after generating a campaign)

    Args:
        user_input (str): parsed user input,
            from the function parse_user_input_gpt4
        campaign (str): campaign returned from get_gpt4_campaign
        gpt4_creds_dict (dict, optional): Specific creds for GPT4 in Azure.
            Defaults to None.

    Returns:
        str: instagram posts
    """
    if gpt4_creds_dict is None:
        gcp_project_id = get_gcp_project_id_from_env_var()
        gpt4_creds_dict = get_openai_creds(
            gcp_project_id=gcp_project_id)

    messages = _get_newgpt_prompt(type='gpt4')
    prompt = _add_role_user(user_input, messages)
    logger.info('Adding campaign to get back instagram posts')
    prompt_campaign = _add_campaign(campaign, prompt)
    prompt_insta = _add_insta(prompt_campaign)

    response = openai.ChatCompletion.create(
        engine="GPT-4",
        messages=prompt_insta,
        temperature=0.8,
        max_tokens=1200,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None)

    text_response_insta = response["choices"][0]["message"]["content"]
    return text_response_insta


def add_newline_before_digits(text):
    digits = [i for i in text if i.isdigit()]
    for digit in digits:
        text = text.replace(digit, f'\n{digit}')
    return text


def _set_openai_to_azure(azure_openai_creds_dict, use_preview_api=True):
    api_version = (azure_openai_creds_dict['api_preview_version']
                   if use_preview_api else azure_openai_creds_dict['api_version'])
    openai.api_type = azure_openai_creds_dict['api_type']
    openai.api_base = azure_openai_creds_dict['api_base']
    openai.api_version = api_version
    openai.api_key = azure_openai_creds_dict['api_key']


def _set_openai(openai_creds):
    openai.api_key = openai_creds.api_key

def _add_role_user(user_input, prompt):
    messages_sender = {"role": "user", "content": user_input}
    prompt.append(messages_sender)
    return prompt


def _add_campaign(campaign, prompt):
    message_assistant = {"role": "assistant", "content": campaign}
    prompt.append(message_assistant)
    return prompt


def _add_insta(prompt):
    insta_tag = """Amazing! can you generate a numbered list of 10 Instagram \
        posts prompting this campaign. I only need an emoji-filled caption and \
        highly detailed and specific image description that will be sent to an\
            AI Image Generator as a prompt. I need the answer in this format:
        1. Caption: 🎉🎬 Celebrating 100 years of Disney magic! Join us on this\
              enchanting journey with #ACenturyofDreams 🏰💖
        2. Image Description: A colorful image of a retro suitcase adorned \
            with stickers representing Disney movies from different decades, \
                set against a background of clouds and stars.
        """
    message_insta = {"role": "user", "content": insta_tag}
    prompt.append(message_insta)
    return prompt


def _get_newgpt_prompt(type='gpt4'):
    if type == 'gpt4':
        file = Path(__file__).parent.parent / \
            Path('openai_prompts') / "gpt4_prompt.json"
        logger.info('Getting Dictionary Prompt for GPT4')
        with open(file) as json_file:
            data = json.load(json_file)

        return data

    elif type == 'event':
        file = Path(__file__).parent.parent / \
            Path('openai_prompts') / "gpt4_prompt_events.json"
        logger.info('Getting Dictionary Prompt for GPT4--events')
        with open(file) as json_file:
            data = json.load(json_file)

        return data

    else:
        ValueError(f'Unknown engine type {type} submitted')


def find_between(s, first, last):
    """Return string in between two specified words

    Args:
        s (str): string to find between
        first (str): word start (not inclusive)
        last (str): word end (not inclusive)

    Returns:
        str: cut string
    """
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ""


def substring_after(s, delim):
    """Return full string after a specified word

    Args:
        s (str): string to cut till the end
        delim (str): word start (not inclusive)

    Returns:
        str: cut string
    """
    return s.partition(delim)[2]


# class InstaPost(BaseModel):
#     """
#     Identifying instapost, caption and image descrption
#     """
#     caption: str = Field(..., description="The post's text")
#     image_desc: str = Field(..., description="A description of the image")

# prompt_msgs = [
#     SystemMessage(
#         content="""
#         You are an expert brand manager that helps users come up with
#         imaginative and visually stunning campaigns and brand platform ideas
#         that are meaningful. In your responses you also help users understand
#         both what the campaign would entail in terms of visual identity,
#         color palette, platform features, promotional tactics. Be as
#         imaginative as you can, thinking about how the campaign could use new
#         technologies such as AR and VR, as well as stories it might use for
#         video ads. Lastly, suggest ways in which you would measure the success
#         of the campaign.
#         """
#     ),
#     HumanMessage(
#         content="""
#         Use the given format, generate 10 Instagram posts prompting this
#         campaign, each with an emoji-filled caption and highly specific and
#         detailed image description that will be sent to an AI image generation
#         service, such as Stable Diffusion or DALL-E.
#         """
#     )
#     HumanMessagePromptTemplate.from_template("{campaign}")
# ]

# prompt = ChatPromptTemplate(messages=prompt_msgs)

# chain = create_openai_fn_chain(InstaPost, llm)
