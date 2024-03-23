import re
from loguru import logger


def parse_insta_posts(gpt4_insta_response):
    """Convert GPT4 instagram post response into a dictionary that separates\
    the caption from the image description and keeps them in a dictionary for \
    each post

    Args:
        gpt4_insta_response (str): 10 instagram posts from GPT4

    Returns:
        list: list of dictionary, each dictionary containing an instagram post
    """
    logger.info('Parsing GPT4 response into captions and image descriptions')
    list_insta = gpt4_insta_response.split('Caption: ')
    list_insta = [_format_instapost(i) for i in list_insta]
    list_insta = [i.split('Image Description: ') for i in list_insta[1:]]
    dict_list = []
    for i in list_insta:
        d = {}
        d['Caption'] = i[0]
        d['Image Description'] = i[1]
        dict_list.append(d)
    return dict_list


def _format_instapost(insta_image_desc):
    # Regex to eliminate only the double newlines with a number from the list
    # Returned by GPT4
    logger.info('Formatting posts for instagram')
    replaced = re.sub(r"\n\n\d+\.\s", '', insta_image_desc)
    return replaced


def parse_user_input_for_gpt4(brand, tags=None):
    if tags:
        s = f"Can you come up with a new brand platform idea for {brand}, with\
        these characteristics {tags}"

    else:
        s = f"Can you come up with a new brand platform idea for {brand} that\
        is trendy and up-beat?"

    return s

def parse_user_input_with_loc(brand, location, tags=None):
    if tags:
        s = f"Can you come up with a new brand platform idea for {brand}, with these characteristics: {tags}, in {location}?"

    else:
        s = f"Can you come up with a new brand platform idea for {brand} that is trendy and up-beat in {location}?"

    return s

