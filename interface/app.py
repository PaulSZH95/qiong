import gradio as gr
import requests


# # Define a function to get the chatbot response from an API
def get_chatbot_response(message, history):
    if message["files"]:
        api_url = (
            "http://fastapi_custom_1:8000/fin_pdf/"  # Replace with your API endpoint
        )
        with open(message["files"][0], "rb") as f:
            files = {"file": (message["files"][0], f, "application/pdf")}
            yield f"Creating rag collection for {message['files'][0]} ..."
            response = requests.post(api_url, files=files)
            yield response.json()["rag_result"]
    else:
        api_url = (
            "http://fastapi_custom_1:8000/chat_point"  # Replace with your API endpoint
        )
        payload = {"message": message["text"]}
        print(payload)
        response = requests.get(api_url, json=payload)
        if response.status_code == 200:
            yield response.json().get("response", "Sorry, I didn't understand that.")
        else:
            yield "Error: Unable to fetch response from the chatbot API."


demo = gr.ChatInterface(fn=get_chatbot_response, multimodal=True).queue()

if __name__ == "__main__":
    demo.launch(debug=True, share=True, server_port=7860, server_name="0.0.0.0")
