import argparse
import asyncio
import logging
import os

import cherry_core
import dotenv
from cherry_core import ingest
from langchain.chat_models import init_chat_model
from typing_extensions import Annotated, TypedDict

dotenv.load_dotenv()

if not os.environ.get('OPENAI_API_KEY'):
    raise ValueError('OPENAI_API_KEY is not set')

logging.basicConfig(level=os.environ.get('LOGLEVEL', 'DEBUG').upper())
logger = logging.getLogger(__name__)

# Suppress logging from openai and httpcore
logging.getLogger('openai').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)


class ERC20EventFilter(TypedDict):
    """Parameters to filter ERC20 event logs."""

    contract_address: Annotated[str, ..., 'ERC20 contract address']
    event_signature: Annotated[str, ..., 'Event signature']


def get_provider_and_url(provider: str):
    return (
        (ingest.ProviderKind.SQD, 'https://portal.sqd.dev/datasets/ethereum-mainnet')
        if provider == 'sqd'
        else (ingest.ProviderKind.HYPERSYNC, 'https://eth.hypersync.xyz')
    )


def run(provider: ingest.ProviderConfig, signature: str):
    async def stream_logs(signature: str):
        stream = ingest.start_stream(provider)

        while True:
            res = await stream.next()
            if res is None:
                break

            logger.info(res['blocks'].column('number'))
            logger.debug(res)

            decoded = cherry_core.evm_decode_events(signature, res['logs'])
            logger.debug(decoded)

    asyncio.run(stream_logs(signature))


def get_logs(contract_address: str, event_signature: str, provider: ingest.ProviderKind, url: str):
    """Get all logs from contract address with event signature"""

    query = ingest.Query(
        kind=ingest.QueryKind.EVM,
        params=ingest.evm.Query(
            from_block=22012600,
            to_block=22012629,
            logs=[
                ingest.evm.LogRequest(
                    address=[contract_address],
                    event_signatures=[event_signature],
                )
            ],
            fields=ingest.evm.Fields(
                block=ingest.evm.BlockFields(
                    number=True,
                ),
                log=ingest.evm.LogFields(
                    data=True,
                    topic0=True,
                    topic1=True,
                    topic2=True,
                    topic3=True,
                ),
            ),
        ),
    )

    run(
        ingest.ProviderConfig(
            kind=provider,
            query=query,
            url=url,
        ),
        event_signature,
    )


def main(args: argparse.Namespace):
    model = init_chat_model('gpt-4o-mini', model_provider='openai')
    agent = model.with_structured_output(
        ERC20EventFilter,
    )
    resp = agent.invoke(
        args.prompt,
    )

    provider, url = get_provider_and_url(args.provider)
    get_logs(resp['contract_address'], resp['event_signature'], provider, url)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Agent to get logs from a contract')

    parser.add_argument(
        '--prompt',
        type=str,
        default='Get all logs from contract address 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'
        'with event signature Transfer(address indexed from, address indexed to, uint256 amount)',
    )

    parser.add_argument(
        '--provider',
        choices=['sqd', 'hypersync'],
        required=True,
        help="Specify the provider ('sqd' or 'hypersync')",
    )

    args = parser.parse_args()
    main(args)
