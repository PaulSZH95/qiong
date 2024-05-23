import os
from pathlib import Path
from os.path import dirname, join
from dotenv import load_dotenv
from libraries.llm.google import docai as docai_custom
from google.cloud import documentai_v1 as docai


from google.cloud import storage
from libraries.llm.google import storage_custom
from libraries.llm.google.parse_doc import *
from libraries.llm.google import parse_doc
from libraries.rag.rag_wo_filter import RagWOFilter
from libraries.etl.unopt_elements import EleParse
from libraries.llm.google import storage_custom


script_dir = Path(__file__).absolute()
backend_dir = dirname(dirname(dirname(dirname(script_dir))))
secrets_path = join(backend_dir, "config/.env")
load_dotenv(dotenv_path=secrets_path)


class DocumentProcess:
    PROJECT_ID = os.getenv("PROJECT_ID")
    API_LOCATION = os.getenv("API_LOCATION")

    document_ocr_display_name = "document-ocr"
    form_parser_display_name = "form-parser"

    @classmethod
    def create_docai_processors(cls):
        test_processor_display_names_and_types = (
            (cls.document_ocr_display_name, "OCR_PROCESSOR"),
            (cls.form_parser_display_name, "FORM_PARSER_PROCESSOR"),
        )
        responses = []
        status = []
        for display_name, type_cust in test_processor_display_names_and_types:
            try:
                res = docai_custom.create_processor(display_name, type_cust)
                responses.append(res)
                status.append(True)
            except Exception as err:
                error_str = f"Unable to process {display_name} of type {type_cust} \n due to ERROR:\n{err}"
                responses.append(error_str)
                status.append(False)
        return responses, all(status)

    @classmethod
    def create_rag(cls, upload_path):
        DocumentProcess.create_docai_processors()
        bucket_name = "edgar_temus"
        destination_blob_name = "edgar_parking/something.pdf"
        gcs_output_uri = "gs://edgar_temus/edgar_output/"

        uri = storage_custom.upload_file_to_gcs(
            bucket_name=bucket_name,
            source_file_name=upload_path,
            destination_blob_name=destination_blob_name,
            project_id=os.getenv("PROJECT_ID"),
        )

        doc_return = cls.activate_processor(
            gcs_input_uri=uri, gcs_output_uri=gcs_output_uri
        )
        bucket_name = doc_return[0][0]
        prefix = doc_return[1][0]
        parsed_doc = cls.retrieve_processed(bucket_name=bucket_name, prefix=prefix)
        reorg = EleParse.first_reorg(parsed_doc)
        readied_docs = EleParse.edgar_doc(reorg)
        w_rag = RagWOFilter()
        w_rag.create_collection()
        w_rag.activate_collection()
        response = w_rag.update_collection(collection_chunks=readied_docs)
        storage_custom.delete_files_in_bucket(
            bucket_name="edgar_temus", directory="edgar_output"
        )
        storage_custom.delete_files_in_bucket(
            bucket_name="edgar_temus", directory="edgar_parking"
        )
        w_rag.close()
        return response

    @classmethod
    def activate_processor(cls, gcs_input_uri: str, gcs_output_uri: str):

        # file_path = "./something.pdf"
        # mime_type = "application/pdf"
        # gcs_input_uri = "gs://edgar_temus/edgar_parking/something.pdf"
        # gcs_output_uri = "gs://edgar_temus/edgar_output/"

        processor = docai_custom.get_processor(cls.form_parser_display_name)

        document = docai_custom.process_document(
            processor.name,
            location=cls.API_LOCATION,
            gcs_input_uri=gcs_input_uri,
            gcs_output_uri=gcs_output_uri,
        )
        return document

    @classmethod
    def retrieve_processed(cls, bucket_name: str, prefix: str):
        # edgar_temus, edgar_output
        storage_client = storage.Client(project=cls.PROJECT_ID)
        documents = []
        for blob in storage_client.list_blobs(bucket_name, prefix=prefix):
            document = docai.Document.from_json(
                blob.download_as_bytes(), ignore_unknown_fields=True
            )
            documents.append(document)
        parsed_doc = parse_doc.display_elements(documents)
        storage_client.close()
        return parsed_doc
