import os
from google.cloud import storage

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "config/config.json"


def upload_file_to_gcs(
    bucket_name: str, source_file_name: str, destination_blob_name: str, project_id: str
) -> str:
    """
    Uploads a file to Google Cloud Storage and returns the URI.

    Args:
        bucket_name (str): The name of the GCS bucket.
        source_file_name (str): The path to the local file to be uploaded.
        destination_blob_name (str): The name of the destination blob in the bucket.

    Returns:
        str: The URI of the uploaded file.
    """
    # Initialize a storage client
    storage_client = storage.Client(project=project_id)

    # Get the bucket
    bucket = storage_client.bucket(bucket_name)

    # Create a blob (object) in the bucket
    blob = bucket.blob(destination_blob_name)

    # Check if the blob already exists and delete it if it does
    if blob.exists():
        print(f"Blob {destination_blob_name} already exists. Deleting it.")
        blob.delete()

    # Upload the file to GCS
    blob.upload_from_filename(source_file_name)

    # Return the URI of the uploaded file
    return f"gs://{bucket_name}/{destination_blob_name}"


def get_blobs(storage_client: storage.Client, output_bucket, output_prefix):

    output_blobs = storage_client.list_blobs(output_bucket, prefix=output_prefix)

    # Download and print the output
    blobs = []
    for blob in output_blobs:
        if blob.content_type != "application/json":
            print(
                f"Skipping non-supported file: {blob.name} - Mimetype: {blob.content_type}"
            )
            continue
        else:
            blobs.append(blob)
    return blob


def delete_files_in_bucket(bucket_name, directory):
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=directory)
    deleted = []

    for blob in blobs:
        deleted.append(blob.name)
        blob.delete()
    return deleted


def locally_save_img(document):
    for page in document.pages:
        # Check if there are any images in the page
        if page.image:
            print(f"Image found on page {page.page_number}")

            # Access image properties
            image = page.image
            print(f"Image dimensions: {image.width} x {image.height}")

            # You can save or process the image as needed
            # Example: save image content to a file
            with open(f"image_page_{page.page_number}.jpg", "wb") as img_file:
                img_file.write(image.content)
