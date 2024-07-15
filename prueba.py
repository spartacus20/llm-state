import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client  = OpenAI(api_key=os.getenv("OPENAI_APIKEY"))


states = [
    {
        "name": "prueba",
        "state_prompt": "You are an assistant that must follow these rules strictly:\n1. If the user says 'hi', you must call the function update_state with the parameter 'send_info'.\n2. If the user says 'ho', you must call the function update_state with the parameter 'prueba'.\n3. For any other input, do not respond to the user directly.\n4. Always use the function call when conditions 1 or 2 are met. Do not write out any response.",
        "edges": [
            {
                "destion_name": "send_info",
                "description": "sirve para enviar informacion"
            }
        ]
    },
    {
        "name": "send_info",
        "state_prompt": "You are now in the send_info state. Follow these rules strictly:\n1. If the user says 'back', you must call the function update_state with the parameter 'prueba'.  If the user says 'next', you must call the function update_state with the parameter 'info'.\n2. For any other input, respond with 'I am ready to send information.'\n3. Always use the function call when condition 1 is met. Do not write out any response in this case.",
        "edges": [
            {
                "destion_name": "prueba",
                "description": "return to prueba state"
            },
            {
                "destion_name": "info",
                "description": "return to prueba state"
            },
        ]
    },
     {
        "name": "info",
        "state_prompt": "You are now in the send_info state. Follow these rules strictly:\n1. If the user says 'back', you must call the function update_state with the parameter 'send_info'. \n2. For any other input, respond with 'I am ready to send information.'\n3. Always use the function call when condition 1 is met. Do not write out any response in this case.",
        "edges": [
            {
                "destion_name": "send_info",
                "description": "return to info state"
            }
        ],
        "tools": [
            {
            "type": "custom",
            "name": "send_information",
            "description": "Describe what this function does",
            "parameters": {
                "type": "object",
                "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the person booking the slot."
                },
                "phone": {
                    "type": "string",
                    "description": "phone number of the person booking the slot."
                }
                },
                "required": [
                    "name",
                    "phone"
                ]
            },
            "url": "https://hook.us1.make.com/a6m8cvubuvc8337z9w2pdcvx2r8zveip"
          }
        ]
    }
]

initial_state = "prueba"



def find_state(states, initial_state):
    for state in states:
        if state["name"] == initial_state:
            return state
    return None

def update_state(state_name):
    global initial_state
    current_state = find_state(states, initial_state)
    new_state = find_state(states, state_name)
    if new_state:

        allowed_transitions = [edge['destion_name'] for edge in current_state['edges']]
        if state_name in allowed_transitions:
            initial_state = state_name
            print(f"State updated to: {state_name}")
            return new_state
        else:
            print(f"Transition to '{state_name}' not allowed from current state '{initial_state}'.")
            return current_state
    else:
        print(f"State '{state_name}' not found. Staying in current state.")
        return current_state

tools = [
        {
            "type": "function",
            "function": {
                "name": "update_state",
                "description": "This function updates the state",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "state_name": {
                            "type": "string",
                            "description": "This is the name of the state",
                        },
                    },
                    "required": ["state_name"],
                },
            },
        }
    ]


def send_message(user_content):
    global initial_state

    current_state = find_state(states, initial_state)
    msg = [{"role": "system", "content": current_state["state_prompt"]}]
    msg.append({"role": "user", "content": user_content})
    response = client.chat.completions.create(
        model= "gpt-4o",
        messages=msg,
        tools=tools,
        tool_choice="auto"
    )
    assistant_content = response.choices[0].message
    if assistant_content.tool_calls:
        for tool_call in assistant_content.tool_calls:
           if tool_call.function.name == "update_state":
               new_state_name = eval(tool_call.function.arguments).get("state_name")
               new_state = update_state(new_state_name)
               return f"Current state: {new_state['name']}"

    msg.append({"role": "assistant", "content": assistant_content.content})
    return assistant_content


print(f"Current_state: {initial_state}")
while True:
    user_input = input("Tu: ")
    if user_input.lower() == "salir":
        break
    response = send_message(user_input)
    print(f"{response}")


