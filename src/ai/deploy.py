import os

import vertexai
from vertexai import agent_engines
from dotenv import load_dotenv

from lingua.agent import root_agent

load_dotenv()


def create():
    """Deploys a new agent to Vertex AI."""

    adk_app = agent_engines.AdkApp(
        agent=root_agent,
        enable_tracing=True,
    )
    _ = agent_engines.create(
        agent_engine=adk_app,  # type: ignore
        display_name="Lingua",
        description="learning Dutch",
        requirements="requirements.txt",
        extra_packages=["./lingua/"],
        min_instances=1,
        max_instances=1,
        container_concurrency=80,
        resource_limits={
            "cpu": "1",
            "memory": "1Gi",
        },
    )


if __name__ == "__main__":

    vertexai.init(
        project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location=os.getenv("GOOGLE_CLOUD_LOCATION"),
        staging_bucket=os.getenv("GOOGLE_CLOUD_STAGING_BUCKET"),
    )

    create()
