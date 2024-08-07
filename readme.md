class StateEdge(BaseModel):
    description: str
    """
    Describes what's the transition and at what time / criteria should this
    transition happen.
    """

    destination_state_name: str
    """The destination state name when going through transition of state via this edge.

    State transition internally is implemented as a tool call of LLM, and a tool
    call with name "transition*to*{destination_state_name}" will get created. Feel
    free to reference it inside the prompt.
    """

    parameters: Optional[StateEdgeParameters] = None
    """Describes what parameters you want to extract out when the transition changes.

    The parameters extracted here can be referenced in prompts & function
    descriptions of later states via dynamic variables. The parameters the functions
    accepts, described as a JSON Schema object. See
    [JSON Schema reference](https://json-schema.org/understanding-json-schema/) for
    documentation about the format.
    """
#   l l m - s t a t e  
 