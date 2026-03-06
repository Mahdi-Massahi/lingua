import os

import vertexai
from vertexai import agent_engines
from dotenv import load_dotenv

from lingua.agent import root_agent

load_dotenv()


REASONING_ENGINE_ID = os.getenv("REASONING_ENGINE_ID", "")


def _build_app():
    return agent_engines.AdkApp(
        agent=root_agent,
        enable_tracing=True,
    )


def create():
    """Deploys a new agent to Vertex AI."""
    agent_engine = agent_engines.create(
        agent_engine=_build_app(),  # type: ignore
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
    print(f"Created: {agent_engine.resource_name}")


def update():
    """Updates the existing agent on Vertex AI."""
    resource_name = (
        f"projects/{os.getenv('GOOGLE_CLOUD_PROJECT')}"
        f"/locations/{os.getenv('GOOGLE_CLOUD_LOCATION')}"
        f"/reasoningEngines/{REASONING_ENGINE_ID}"
    )
    agent_engine = agent_engines.get(resource_name)
    agent_engine.update(
        agent_engine=_build_app(),
        requirements="requirements.txt",
        extra_packages=["./lingua/"],
    )
    print(f"Updated: {agent_engine.resource_name}")


if __name__ == "__main__":
    import sys

    vertexai.init(
        project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location=os.getenv("GOOGLE_CLOUD_LOCATION"),
        staging_bucket=os.getenv("GOOGLE_CLOUD_STAGING_BUCKET"),
    )

    command = sys.argv[1] if len(sys.argv) > 1 else "create"
    if command == "update":
        update()
    else:
        create()
