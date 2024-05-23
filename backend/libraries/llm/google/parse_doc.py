import os
from pathlib import Path
from os.path import dirname, join
from dotenv import load_dotenv
from google.cloud import documentai_v1 as documentai

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "config/config.json"

script_dir = Path(__file__).absolute()
backend_dir = dirname(dirname(dirname(dirname(script_dir))))
secrets_path = join(backend_dir, "config/.env")
load_dotenv(dotenv_path=secrets_path)

# Initialize the Document AI client
client = documentai.DocumentProcessorServiceClient()

project_id = os.getenv("PROJECT_ID")
location = os.getenv("API_LOCATION")


# Function to extract text elements with their coordinates
def extract_text_elements(document):
    text_elements = []
    for page in document.pages:
        for paragraph in page.paragraphs:
            text = ""
            for segment in paragraph.layout.text_anchor.text_segments:
                start_index = segment.start_index
                end_index = segment.end_index
                text += document.text[start_index:end_index]
            bounding_box = paragraph.layout.bounding_poly
            text_elements.append(
                {
                    "type": "text",
                    "text": text,
                    "bounding_box": bounding_box,
                    "page_number": page.page_number,
                }
            )
    return text_elements


# Function to extract table elements with their coordinates
def extract_table_elements(document):
    table_elements = []
    for page in document.pages:
        for table in page.tables:
            table_data = []
            head_body = []
            head_body += table.header_rows
            head_body += table.body_rows
            for row in head_body:
                row_data = []
                for cell in row.cells:
                    try:
                        cell_text = document.text[
                            cell.layout.text_anchor.text_segments[0]
                            .start_index : cell.layout.text_anchor.text_segments[0]
                            .end_index
                        ]
                        row_data.append(cell_text)
                    except:
                        pass
                table_data.append(row_data)
            bounding_box = table.layout.bounding_poly
            table_elements.append(
                {
                    "type": "table",
                    "data": table_data,
                    "bounding_box": bounding_box,
                    "page_number": page.page_number,
                }
            )
    return table_elements


# Function to extract image elements with their coordinates
# def extract_image_elements(document):
#     image_elements = []
#     for page in document.pages:
#         if page.image:
#             image = page.image
#             bounding_box = image.layout.bounding_poly
#             image_elements.append(
#                 {"type": "image", "image": image, "bounding_box": bounding_box}
#             )
#     return image_elements


def display_elements(documents):
    text_elements = []
    table_elements = []
    for document in documents:
        text_elements += extract_text_elements(document)
        table_elements += extract_table_elements(document)

    all_elements = text_elements + table_elements
    redo = {}
    for ele in all_elements:
        if redo.get(ele["page_number"], None):
            redo[ele["page_number"]].append(ele)
        else:
            redo[ele["page_number"]] = [ele]

    for _ in redo:
        redo[_] = sorted(
            redo[_],
            key=lambda e: (
                e["bounding_box"].normalized_vertices[0].y,
                e["bounding_box"].normalized_vertices[0].x,
            ),
        )
    return redo


###################################################
