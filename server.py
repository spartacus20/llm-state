from fastapi import FastAPI, Response, Request
from fastapi.responses import StreamingResponse
from openai import OpenAI
from dotenv import load_dotenv
import os, json

load_dotenv()
app = FastAPI()
openai = OpenAI(api_key=os.getenv("OPENAI_APIKEY"))
PROMPT_INDEX_FILE = 'prompt_indices.json'
PATHWAYS_MESSAGES_FILE = 'pathways.json'

#Ensure that JSON File Exists
if not os.path.exists(PROMPT_INDEX_FILE):
    with open(PROMPT_INDEX_FILE, 'w') as f:
        json.dump({}, f)

if os.path.exists(PATHWAYS_MESSAGES_FILE):
	with open(PATHWAYS_MESSAGES_FILE, 'r') as f:
		prompt_messages = json.load(f)
else:
	print("The prompt messages file does not exist")

def get_prompt_index(call_id, increment=True):
    try:
        with open(PROMPT_INDEX_FILE, 'r') as f:
            indices = json.load(f)
    except(FileNotFoundError, json.JSONDecodeError):
        indices = {}

    index = indices.get(call_id, 0)

    if increment:
        indices[call_id] = index + 1 if index + 1 < len(prompt_messages) else 0

    with open(PROMPT_INDEX_FILE, 'w') as f:
     json.dump(indices, f)

    return index

def generate_streaming_response(data):
    for message in data:
        json_data = json.dumps(message.to_dict())
        yield f"data: {json_data}\n\n"


@app.post("/chat/completions")
async def openai_advanced_custom_llm_route(request: Request):
    request_data = await request.json()
    streaming = request_data.get('stream', False)
    next_prompt = ''

    call_id = request_data['call']['id']
    prompt_index = get_prompt_index(call_id, False)

    last_assistant_message = ''
    if 'messages' in request_data and len(request_data['messages']) >= 2:
        last_assistant_message = request_data['messages'][-2]

    last_message = request_data['messages'][-1]
    pathway_prompt = prompt_messages[prompt_index]

    if 'check' in pathway_prompt and pathway_prompt['check']:
        prompt = f"""
        You're an AI classifier. Your goal is to classify the following condition/instructions based on the last user message. If the condition is met, you only answer with a lowercase 'yes', and if it was not met, you answer with a lowercase 'no' (No Markdown or punctuation).
        ----------
        Conditions/Instructions: {pathway_prompt['check']}"""

        if last_assistant_message:
            prompt_completion_messages = [{
                "role": "system",
                "content": prompt
            }, {
                "role": "assistant",
                "content": last_assistant_message['content']
            }, {
                "role": "user",
                "content": last_message['content']
            }]
        else:
            prompt_completion_messages = [{
                "role": "system",
                "content": prompt
            }, {
                "role": "user",
                "content": last_message['content']
            }]

        completion =  openai.chat.completions.create(
            model=f"{os.getenv('OPENAI_MODEL')}",
            messages=prompt_completion_messages,
            max_tokens=int(os.getenv('OPENAI_MAXTOKENS')),
            temperature=float(os.getenv('OPENAI_TEMPERATURE'))
        )


        if (completion.choices[0].message.content == 'yes'):
            prompt_index = get_prompt_index(call_id)
            next_prompt = pathway_prompt['next']
        else:
            next_prompt = pathway_prompt['error']
    else:
        prompt_index = get_prompt_index(call_id)
        next_prompt = pathway_prompt['next']

    modified_messages = [{
        "role": "system",
        "content": next_prompt
    }, {
        "role": "user",
        "content": last_message['content']
    }]

    request_data['messages'] = modified_messages

    request_data.pop('call', None)
    request_data.pop('metadata', None)
    request_data.pop('phoneNumber', None)
    request_data.pop('customer', None)

    if streaming:
        chat_completion_stream = openai.chat.completions.create(**request_data)
        return StreamingResponse(generate_streaming_response(chat_completion_stream), media_type='text/event-stream')
    else:
        chat_completion = openai.chat.completions.create(**request_data)
        return Response(chat_completion.to_json(), media_type='application/json')

@app.get("/")
async def root():
    return {"message": "Hello World"}

