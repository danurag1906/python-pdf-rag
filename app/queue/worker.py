from ..db.collections.files import files_collection
from bson import ObjectId
from pdf2image import convert_from_path
import os
from openai import OpenAI
import base64

client = OpenAI()

# Function to encode the image


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


async def process_file(id: str, file_path):
    await files_collection.update_one({"_id": ObjectId(id)}, {
        "$set": {
            "status": "processing"
        }
    })

    await files_collection.update_one({"_id": ObjectId(id)}, {
        "$set": {
            "status": "converting to images"
        }
    })

    # step1: convert pdf to image
    pages = convert_from_path(file_path)
    images = []

    for i, page in enumerate(pages):
        image_save_path = f"/mnt/uploads/images/{id}/image-{i}.jpg"
        os.makedirs(os.path.dirname(image_save_path), exist_ok=True)
        page.save(image_save_path, 'JPEG')
        images.append(image_save_path)

    await files_collection.update_one({"_id": ObjectId(id)}, {
        "$set": {
            "status": "converting to images success"
        }
    })

    images_base64 = [encode_image(img) for img in images]

    response = client.responses.create(
        model="gpt-4.1",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "In the image of the resume, please analyze everything and roast it. After roasting it, please add some improvements and help the person like a big brother."},
                    {
                        # flake8: noqa
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{images_base64[0]}",
                    },
                ],
            }
        ],
    )

    await files_collection.update_one({"_id": ObjectId(id)}, {
        "$set": {
            "status": "Processing Completed",
            "result": response.output_text
        }
    })

    print(response.output_text)
