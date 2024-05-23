import os
from pathlib import Path
from os.path import dirname, join
from dotenv import load_dotenv
from typing import Iterator, MutableSequence, Optional, Sequence, Tuple

from google.cloud import documentai_v1 as docai
from tabulate import tabulate
import re
from google.api_core.client_options import ClientOptions
from google.api_core.exceptions import InternalServerError, RetryError

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "config/config.json"
script_dir = Path(__file__).absolute()
backend_dir = dirname(dirname(dirname(dirname(script_dir))))
secrets_path = join(backend_dir, "config/.env")
load_dotenv(dotenv_path=secrets_path)

PROJECT_ID = os.getenv("PROJECT_ID")
API_LOCATION = os.getenv("API_LOCATION")
# Test processors


def get_client() -> docai.DocumentProcessorServiceClient:
    client_options = {"api_endpoint": f"{API_LOCATION}-documentai.googleapis.com"}
    return docai.DocumentProcessorServiceClient(client_options=client_options)


def get_parent(client: docai.DocumentProcessorServiceClient) -> str:
    return client.common_location_path(PROJECT_ID, API_LOCATION)


def get_client_and_parent() -> Tuple[docai.DocumentProcessorServiceClient, str]:
    client = get_client()
    parent = get_parent(client)
    return client, parent


def fetch_processor_types() -> MutableSequence[docai.ProcessorType]:
    client, parent = get_client_and_parent()
    response = client.fetch_processor_types(parent=parent)

    return response.processor_types


def processor_type_tabular_data(
    processor_types: Sequence[docai.ProcessorType],
) -> Iterator[Tuple[str, str, str, str]]:
    def locations(pt):
        return ", ".join(sorted(loc.location_id for loc in pt.available_locations))

    yield ("type", "category", "allow_creation", "locations")
    yield ("left", "left", "left", "left")
    if not processor_types:
        yield ("-", "-", "-", "-")
        return
    for pt in processor_types:
        yield (pt.type_, pt.category, f"{pt.allow_creation}", locations(pt))


def print_processor_types(processor_types: Sequence[docai.ProcessorType]):
    def sort_key(pt):
        return (not pt.allow_creation, pt.category, pt.type_)

    sorted_processor_types = sorted(processor_types, key=sort_key)
    data = processor_type_tabular_data(sorted_processor_types)
    headers = next(data)
    colalign = next(data)

    print(tabulate(data, headers, tablefmt="pretty", colalign=colalign))
    print(f"→ Processor types: {len(sorted_processor_types)}")


def create_processor(display_name: str, type: str) -> docai.Processor:
    client, parent = get_client_and_parent()
    processor = docai.Processor(display_name=display_name, type_=type)

    return client.create_processor(parent=parent, processor=processor)


def list_processors() -> MutableSequence[docai.Processor]:
    client, parent = get_client_and_parent()
    response = client.list_processors(parent=parent)

    return list(response.processors)


def print_processors(processors: Optional[Sequence[docai.Processor]] = None):
    def sort_key(processor):
        return processor.display_name

    if processors is None:
        processors = list_processors()
    sorted_processors = sorted(processors, key=sort_key)
    data = processor_tabular_data(sorted_processors)
    headers = next(data)
    colalign = next(data)

    print(tabulate(data, headers, tablefmt="pretty", colalign=colalign))
    print(f"→ Processors: {len(sorted_processors)}")


def processor_tabular_data(
    processors: Sequence[docai.Processor],
) -> Iterator[Tuple[str, str, str]]:
    yield ("display_name", "type", "state")
    yield ("left", "left", "left")
    if not processors:
        yield ("-", "-", "-")
        return
    for processor in processors:
        yield (processor.display_name, processor.type_, processor.state.name)


def get_processor(
    display_name: str,
    processors: Optional[Sequence[docai.Processor]] = None,
) -> Optional[docai.Processor]:
    if processors is None:
        processors = list_processors()
    for processor in processors:
        if processor.display_name == display_name:
            return processor
    return None


def process_document(
    processor_name: list,
    location: str,
    gcs_input_uri: str,
    gcs_output_uri: str,
    input_mime_type: str = "application/pdf",
    field_mask: Optional[str] = None,
    timeout: int = 400,
) -> None:
    # Set the API endpoint
    opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
    client = docai.DocumentProcessorServiceClient(client_options=opts)

    # Specify the GCS input URI
    gcs_document = docai.GcsDocument(gcs_uri=gcs_input_uri, mime_type=input_mime_type)
    gcs_documents = docai.GcsDocuments(documents=[gcs_document])
    input_config = docai.BatchDocumentsInputConfig(gcs_documents=gcs_documents)

    # Specify the GCS output URI
    gcs_output_config = docai.DocumentOutputConfig.GcsOutputConfig(
        gcs_uri=gcs_output_uri, field_mask=field_mask
    )
    output_config = docai.DocumentOutputConfig(gcs_output_config=gcs_output_config)

    # Create the batch process request
    request = docai.BatchProcessRequest(
        name=processor_name,
        input_documents=input_config,
        document_output_config=output_config,
    )

    # BatchProcess returns a Long Running Operation (LRO)
    operation = client.batch_process_documents(request, timeout=600)

    # Poll the operation until it is complete
    try:
        print(f"Waiting for operation {operation.operation.name} to complete...")
        operation.result(timeout=timeout)
    except (RetryError, InternalServerError) as e:
        print(e.message)

    # Get output document information from operation metadata
    metadata = docai.BatchProcessMetadata(operation.metadata)

    output_buckets = []
    output_prefixes = []

    if metadata.state != docai.BatchProcessMetadata.State.SUCCEEDED:
        raise ValueError(f"Batch Process Failed: {metadata.state_message}")
    else:
        for process in list(metadata.individual_process_statuses):
            matches = re.match(r"gs://(.*?)/(.*)", process.output_gcs_destination)
            output_bucket, output_prefix = matches.groups()
            output_buckets.append(output_bucket)
            output_prefixes.append(output_prefix)

    return output_buckets, output_prefixes
