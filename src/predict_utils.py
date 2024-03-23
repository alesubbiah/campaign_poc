import pandas as pd
from loguru import logger
import datetime
from pydantic import BaseModel, Extra

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.chat_models import AzureChatOpenAI
from langchain.chains import LLMChain
import openai
import openai
from predicthq import Client

from src.gcp_utils import (get_secret_from_gcp,
                           TEAM_SECRETS_GCP_PROJECT_SECRET_ID)


# TODO:
# class EventsAPIWrapper(BaseModel):
#     """Wrapper around the PredictHQ API to fetch public event information
#     """

#     def run(self, query: str) -> str:
#         """Run Events Search and get list of events

#         Args:
#             query (str): _description_

#         Returns:
#             str: _description_
#         """


def get_predict_creds(gcp_project_id='wpp-cto-os-intlignce-layer-dev'):
    """Get an api key for PredictHQ from GCP Secret Manager service

    Args:
        gcp_project_id (str): For retrieving the GCP Project ID that holds the
            wanted secret (since the wanted secret is for the team, not an
            individual).

    Returns:
        dict (gpt3_creds_dict): Keys include 'api_key'.
    """
    logger.info('Getting PredictHQ API Azure key from GCP Secrets Manager')
    team_secrets_project_id = get_secret_from_gcp(
        gcp_project_id=gcp_project_id,
        secret_id=TEAM_SECRETS_GCP_PROJECT_SECRET_ID)

    predict_creds_dict = get_secret_from_gcp(
        gcp_project_id=team_secrets_project_id,
        secret_id='predict-creds-json', is_json=True)
    return predict_creds_dict


def _get_first_day_of_year():
    current_year = datetime.datetime.now().year
    first_day = datetime.datetime(current_year, 1, 1)
    return first_day.date()

def _get_last_day_of_year():
    current_year = datetime.datetime.now().year
    last_day = datetime.datetime(current_year, 12, 31)
    return last_day

def _get_date_a_year_from_today():
    one_year_from_today = datetime.date.today() + datetime.timedelta(days=365)
    return one_year_from_today

def _set_openai_to_azure(azure_openai_creds_dict, use_preview_api=True):
    api_version = (azure_openai_creds_dict['api_preview_version']
                if use_preview_api else azure_openai_creds_dict['api_version'])
    openai.api_type = azure_openai_creds_dict['api_type']
    openai.api_base = azure_openai_creds_dict['api_base']
    openai.api_version = api_version
    openai.api_key = azure_openai_creds_dict['api_key']


def find_events_by_city(city_name, start_date=None, end_date=None):
    """Find events given a specific city.

    Args:
        city_name (str): Name of city where campaign will take place
        start_date (str): Date of interest for events start (YYYY-MM-DD),
            defaults to today.
        end_date (str): Date of interest for events end (YYYY-MM-DD),
            defaults to a year from today.

    Returns:
        df: (DataFrame) Pandas DataFrame with list of 500 most relevant events
            for city in question.

    """
    ACCESS_TOKEN = get_predict_creds()['token']
    phq = Client(access_token=ACCESS_TOKEN)

    if start_date is None:
        start_date = datetime.date.today()
    else:
        start_date = start_date

    if end_date is None:
        end_date = _get_date_a_year_from_today()

    else:
        end_date = end_date
    city = []
    logger.info(f'getting events from PredictHq for {city_name}')
    for event in phq.events.search(active__gte=start_date,
                                   active__lte=end_date,
                                   q=city_name,
                                   limit=500):
        city.append(event.to_dict())

    city_df = pd.DataFrame(city)
    return city_df.sort_values(by='phq_attendance', ascending=False)


def get_list_of_events_from_df(df):
    """Return the list of top 50 events by attendance index as defined by
    PredictHQ, dropping duplicates for DataFrame returned by find_events_by_city.

    Args:
        df (DataFrame): Pandas DataFrame returned by find_events_by_city.

    Returns:
        list: list of title of top 50 events
    """
    event_list = list(df[:50]['title'].drop_duplicates())
    return event_list

# Define Events prompt and chain
def get_event_recommendations(city, campaign, events_list, gpt4_creds_dict):
    _set_openai_to_azure(gpt4_creds_dict)
    chat = set_chat()
    template_events = """
    You are an expert brand manager. Given a campaign, a city, and a list of events in that city, choose which events would be most appropriate for a partnership?
    Provide as much reasoning as you can, in terms of brand attribute fit.
    City: {city}
    Campaign: {campaign}
    List of events: {events_list}
    """

    prompt_events = PromptTemplate(
                        template=template_events,
                        input_variables=['city', 'campaign', 'events_list'])
    events_chain = LLMChain(llm=chat, prompt=prompt_events, verbose=True)

    dict = events_chain({'city': city,
                         'campaign': campaign,
                         'events_list': events_list})

    return dict

def set_chat(deployment_name='GPT-4'):
    """Sets OpenAI Azure model of GPT4 for use with Langchain

    Args:
        model_name (str, optional): Azure model name. Defaults to 'gpt-4'.
        engine (str, optional): Azure engine name. Defaults to 'GPT-4'.

    Returns:
        llm: LLM for Langchain use.
    """
    chat = AzureChatOpenAI(deployment_name=deployment_name,
                      openai_api_base=openai.api_base,
                      openai_api_key=openai.api_key,
                      openai_api_version=openai.api_version,
                      openai_api_type='azure')

    return chat


if __name__ == '__main__':
    creds = get_predict_creds()
    print(creds)