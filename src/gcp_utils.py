import subprocess
import os
import json
import functools
import google.auth
from google.cloud import secretmanager
from loguru import logger

__author__ = 'psessford'

TEAM_SECRETS_GCP_PROJECT_SECRET_ID = 'team-secrets-project'


def get_gcp_identity_token(url=None, gcp_impersonated_sa_name=None,
                           gcp_iap_audience=None):
    """Create and return an authorised identity token for GCP (either for a
    remote app's service account or a user); note that a GCP idenity token is
    different from a GCP auth token

    Args:
        url (str, optional): URL for which the token will be used. Required if
            running a remote app, but not used if for a user. Defaults to None.

    Returns:
        str: (id_token) GCP identity token.
    """
    gcp_credentials, _ = google.auth.default()

    is_service_account_present = hasattr(
        gcp_credentials, 'service_account_email')

    is_service_account_impersonated = (gcp_impersonated_sa_name is not None)

    if is_service_account_present:
        # note: running with service account (e.g. a deployed app)
        assert (url is not None)
        audience = (gcp_iap_audience if gcp_iap_audience else url)
        auth_req = google.auth.transport.requests.Request()
        id_token = google.oauth2.id_token.fetch_id_token(
            auth_req, audience=audience)
        # reference: https://stackoverflow.com/questions/65821436/
        #            programmatically-get-current-service-account-on-gcp

    elif is_service_account_impersonated:
        # note: runinng as a user (e.g. locally) impersonating service account
        assert (gcp_iap_audience is not None)

        command = (
            f"gcloud auth print-identity-token "
            f"--impersonate-service-account=\"{gcp_impersonated_sa_name}\" "
            f"--audiences=\"{gcp_iap_audience}\" --include-email")
        id_token = subprocess.run(
            command, capture_output=True, shell=True).stdout.decode(
                'utf-8').rstrip()

    else:
        # note: runinng as a user (e.g. locally) without impersonating serv acc
        assert (gcp_impersonated_sa_name is None)
        assert (gcp_iap_audience is None)

        id_token = subprocess.run(
            ['gcloud', 'auth', 'print-identity-token'], capture_output=True
        ).stdout.decode('utf-8').rstrip()
        # note: see https://stackoverflow.com/questions/57166318/
        #           gcp-unable-to-print-identity-token

    return id_token


def get_gcp_user_default_crendentials():
    """Get user default crendentials for GCP

    Notes:
    - See https://stackoverflow.com/questions/53472429/
          how-to-get-a-gcp-bearer-token-programmatically-with-python
    - If this does not work, try running
      'gcloud auth application-default login', see
      https://google-auth.readthedocs.io/en/latest/reference/google.auth.html

    Returns:
        google.oauth2.credentials.Credentials: (creds)
    """
    creds, _ = google.auth.default()
    auth_req = google.auth.transport.requests.Request()
    creds.refresh(auth_req)  # refresh credentials to populate creds.token
    return creds


@functools.lru_cache(maxsize=10)
def get_secret_from_gcp(gcp_project_id, secret_id, secret_version='latest',
                        creds=None, is_json=False):
    """Get value from GCP's Secret Manager service

    Args:
        gcp_project_id (str): GCP project containing the secret.
        secret_id (str): Matches the secret id in gcp.
        secret_version (str, optional): Version of the secret. Defaults to
            'latest'.
        creds (google.auth.credentials.Credentials, optional): if None, user
            default crendentials for gcp are used. Defaults to None.
        is_json (bool, optional): Whether the secret is to be parsed as json.

    Returns:
        str, list or dict: (secret_value) list or dict if is_json, but
            otherwise str.
    """
    logger.info("Getting secret from GCP")
    request_name = (f"projects/{gcp_project_id}/secrets/{secret_id}/"
                    f"versions/{secret_version}")

    creds = (get_gcp_user_default_crendentials() if creds is None else creds)
    client = secretmanager.SecretManagerServiceClient(credentials=creds)
    response = client.access_secret_version(request={'name': request_name})
    secret_value = response.payload.data.decode('UTF-8')

    if is_json:
        secret_value = json.loads(secret_value)

    return secret_value


@functools.lru_cache(maxsize=10)
def get_gcp_project_id_from_env_var():
    """Get a GCP Project ID from an environment variable

    Raises:
        ValueError: If a GCP Project ID is not found.

    Returns:
        str: (gcp_project_id)
    """
    logger.info("getting gcp project id from an environment variable")

    gcp_project_id = os.environ.get('GCP_PROJECT_ID')
    if not gcp_project_id:
        raise ValueError(f"gcp project id is required ({gcp_project_id})")

    return gcp_project_id
