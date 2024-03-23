import os
import streamlit as st
from pathlib import Path
from PIL import Image
from predicthq import Client

from src.openai_utils import (get_gpt4_campaign_response,
                              get_gpt4_insta_response,
                              get_openai_creds)

from src.streamlit_utils import parse_insta_posts, parse_user_input_for_gpt4
from src.gcp_utils import get_gcp_project_id_from_env_var
from src.stable_utils import (add_details_for_stable, get_stable_image,
                              get_stable_creds_and_set_as_env_vars)
from src.predict_utils import (find_events_by_city,
                               get_list_of_events_from_df,
                               get_event_recommendations)

from src.segmind_utils import get_segmind_image

st.set_page_config(
    page_title="Campaign Genie",
    page_icon="",
    layout="wide",
)


@st.cache_data
def get_creds_dic(gcp_project_id):
    creds = get_openai_creds(gcp_project_id=gcp_project_id)
    return creds


open_ai_creds = st.secrets.openai
predict_creds = st.secrets.predict_hq
replicate_creds = st.secrets.replicate


def render_app():
    # When using azure uncomment these lines
    # gcp_project_id = get_gcp_project_id_from_env_var()
    # creds = get_creds_dic(gcp_project_id=gcp_project_id)
    # using streamlit secrets with openai
    creds = st.secrets.openai
    st.title('Campaign Genie 🧞‍♂️')
    with st.sidebar:
        path = Path(__file__).parent / Path("assets") / \
            "piecrust.png"
        img = Image.open(path)
        st.image(img, width=200)
        brand = st.text_input('Brand')
        tags = st.text_area(
            'Taglines, broader ideas, references',
            help="""Tell the genie what the campaign could be about: e.g.,
                Morning after morning, cup after cup,
                make NESCAFÉ become part of your morning ritual.
                Greatness starts somewhere!*""")
        insta = st.checkbox('Include Instagram posts', value=True)
        # images = 'Stable Diffusion SDXL'
        # When giving the user other options
        # images = st.radio('Preferred AI image generation service',
        #                   ('Stable Diffusion SDXL',
        #                    'Stable Diffusion',
        #                    'DALL-E'))
        location = st.text_input('If wanting event recommendations, provide a\
                                  campaign location/city')
        button = st.button('Ask the genie!')

    if button:
        with st.spinner(f'Building {brand} campaign'):
            user_query = parse_user_input_for_gpt4(brand=brand, tags=tags)
            campaign = get_gpt4_campaign_response(user_query,
                                                  gpt4_creds_dict=creds.api_key)

        if location is not None and not insta:
            with st.spinner(f'Genie is finding event recommendations on \
                            Predict HQ'):
                st.success(campaign)
                events_df = find_events_by_city(city_name=location)
                events_list = get_list_of_events_from_df(events_df)
                recommendation = get_event_recommendations(
                    city=location,
                    campaign=campaign,
                    events_list=','.join(events_list),
                    gpt4_creds_dict=creds)
                st.markdown(f'### PredictHQ event recommendations for \
                            {brand} in {location}')
                st.info(recommendation['text'])

                with st.expander(f"See PredictHQ events table for {location}"):
                    st.table(events_df[['category',
                                        'title',
                                        'description',
                                        'phq_attendance',
                                        'end']][:20])

        elif insta is not None and not location:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"## Brand Platform for {brand}")
                st.success(campaign)

            with col2:
                st.markdown("## Instagram posts")
                with st.spinner('Gathering posts'):
                    insta_posts = get_gpt4_insta_response(user_query,
                                                          campaign,
                                                          creds.api_key)

                    parsed_list = parse_insta_posts(insta_posts)

                    for i, post in enumerate(parsed_list):
                        expander = st.expander(f"Post {i+1}", expanded=True)
                        expander.write(post['Caption'])
                        with st.spinner('Collecting Image...'):
                            # if images == 'DALL-E':
                            #     prompt = add_details_for_dalle(
                            #         post['Image Description'])
                            #     image = get_dalle_image(
                            #         prompt,
                            #         dalle_creds=creds)
                            #     expander.image(image,
                            #                    caption=post['Image Description'])

                            # else:
                            # get_stable_creds_and_set_as_env_vars()
                            prompt = add_details_for_stable(
                                post['Image Description'])
                            # image = get_stable_image(prompt)
                            image = get_segmind_image(prompt)
                            expander.image(image,
                                           caption=post['Image Description'])
        elif all([insta, location]):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"## Brand Platform for {brand}")
                st.success(campaign)
                with st.spinner(f'Genie is finding event recommendations on \
                            Predict HQ'):
                    events_df = find_events_by_city(city_name=location)
                    events_list = get_list_of_events_from_df(events_df)
                    recommendation = get_event_recommendations(
                        city=location,
                        campaign=campaign,
                        events_list=','.join(events_list),
                        gpt4_creds_dict=creds)
                    st.markdown(f'### PredictHQ event recommendations for \
                                {brand} in {location}')
                    st.info(recommendation.content)

                    with st.expander(f"See PredictHQ events table for {location}\
                                     happening in the next year"):
                        st.table(events_df[['category',
                                            'title',
                                            'phq_attendance',
                                            'end']][:20])

            with col2:
                st.markdown("## Instagram posts")
                with st.spinner('Gathering posts'):
                    insta_posts = get_gpt4_insta_response(user_query,
                                                          campaign,
                                                          creds.api_key)

                    parsed_list = parse_insta_posts(insta_posts)

                    for i, post in enumerate(parsed_list):
                        expander = st.expander(f"Post {i+1}", expanded=True)
                        expander.write(post['Caption'])
                        with st.spinner('Collecting Image...'):
                            # if images == 'DALL-E':
                            #     prompt = add_details_for_dalle(
                            #         post['Image Description'])
                            #     image = get_dalle_image(
                            #         prompt,
                            #         dalle_creds=creds)
                            #     expander.image(image,
                            #                    caption=post['Image Description'])
                            # get_stable_creds_and_set_as_env_vars()

                            prompt = add_details_for_stable(
                                    post['Image Description'])
                            # image = get_stable_image(
                            #         prompt, model='normal')
                            image = get_segmind_image(prompt)
                            expander.image(image,
                                           caption=post['Image Description'])

                            # get_stable_creds_and_set_as_env_vars()
                            #     prompt = add_details_for_stable(
                            #         post['Image Description'])
                            #     image = get_stable_image(prompt)
                            #     expander.image(image,
                            #                    caption=post['Image Description'])

        else:
            st.success(campaign)


if __name__ == "__main__":
    os.environ['GCP_PROJECT_ID'] = 'wpp-cto-os-intlignce-layer-dev'
    render_app()
