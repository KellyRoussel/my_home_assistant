# Integration of Grocery List Tool Using Microsoft ToDo API

## Overview

This section of the "home_assistant" project integrates a grocery list management tool using the Microsoft ToDo API. The main objective is to allow the home assistant to add items to a shared shopping list in Microsoft ToDo through a spoken command.

## Implementation Details

### Objectives

- Allow vocal addition of tasks to a Microsoft ToDo list.
- Interface with the Microsoft ToDo API securely and efficiently.
- Process user commands and manage the assistant's state for smooth operation.

### Prerequisites

1. **Microsoft Azure Account**: A Microsoft account for accessing the Azure portal.
2. **Application Registration**: Register the application in the Azure portal to obtain the necessary credentials (tenant ID, client ID, client secret).
3. **OAuth2 Authentication**: Setup OAuth2 for secure access to the Microsoft ToDo API.

### Setting Up

#### Microsoft Azure Configuration
- **Register Application**: Register the application in the Azure portal to obtain the client ID, tenant ID, and client secret.
- **Create Client Secret**: Generate a client secret to authenticate API requests.
- **Token Acquisition**: Use the `script_get_first_token.py` script to fetch an access token and a refresh token. This script performs the OAuth2 flow and stores the tokens locally in a JSON file named `secret_token.json`.

```python
import json
import os
from requests_oauthlib import OAuth2Session

client_id = "<your-client-id>"
client_secret = "<your-client-secret>"

oa_sess = OAuth2Session(client_id, scope='openid offline_access Tasks.ReadWrite', redirect_uri='https://localhost/login/authorized')
authorize_url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
authorization_url, _ = oa_sess.authorization_url(authorize_url)
print(authorization_url)
redirect_resp=input("Paste redirect URL\n")

token = oa_sess.fetch_token('https://login.microsoftonline.com/common/oauth2/v2.0/token', client_secret=client_secret, authorization_response=redirect_resp)

with open('secret_token.json', 'w') as f:
    json.dump(token, f, indent=4)
```

### Core Components

#### `assistant.py`
Defines the `Assistant` class, responsible for coordinating the assistant's functionalities. Key methods include:

- `_start_recording`: Initiates audio recording when the space bar is pressed.
- `_stop_recording`: Stops the recording and transcribes the audio.
- `_think`: Processes the transcribed text and determines if any tool calls are required.
- `_call_tools`: Executes the tool calls as requested.
- `_speak`: Converts the assistant’s response to speech.

```python
def _think(self):
    response = self.llm_engine.gpt_call(self.context.running_conversation)
    tool_calls_response = response.tool_calls
    if tool_calls_response:
        tool_calls = [ToolCall(tc.id, tc.function.name, json.loads(tc.function.arguments)) for tc in tool_calls_response]
        self.context.running_conversation.new_assistant_message(response.content, tool_calls)
        self._call_tools(tool_calls)
        self._think()  # Recursive call to process possible new tool calls
    else:
        response_message = response.content
        self.context.running_conversation.new_assistant_message(response_message)
        self._speak(response_message)
```

#### `tool.py`
Abstract base class defining the structure for tools within the assistant. Each tool must have the following:

- `tool_name`: A unique identifier for the tool.
- `description`: Description of the tool’s functionality.
- `parameters`: List of parameters required for the tool’s operation.
- `execute`: Abstract method to be implemented with the tool’s specific logic.

```python
class Tool(ABC):

    @property
    @abstractmethod
    def tool_name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def description(self) -> str:
        raise NotImplementedError

    def execute(self, **kwargs):
        raise NotImplementedError
```

#### `todo_tool.py`
Implementation of `TodoTool`, a specialized tool for interacting with the Microsoft ToDo API. Key functionalities include:

- `__refresh_token`: Refreshes the authentication token when expired.
- `_get_access_token`: Retrieves a valid access token for API requests.
- `_get_todo_list_from_name`: Fetches a specific todo list by name from Microsoft ToDo.

```python
class TodoTool(Tool, ABC):
    token_file = './tools/todo_list/secret_token.json'
    
    def __refresh_token(self):
        oa_sess = OAuth2Session(self.client_id, token=self.token, redirect_uri='https://localhost/login/authorized')
        self.token = oa_sess.refresh_token('https://login.microsoftonline.com/common/oauth2/v2.0/token', client_id=self.client_id, client_secret=self.client_secret)
        json.dump(self.token, open(self.token_file, 'w'))
    
    def _get_todo_list_from_name(self, name):
        token = self._get_access_token()
        response = requests.get('https://graph.microsoft.com/v1.0/me/todo/lists', headers={'Authorization': f'Bearer {token}'})
        todo_lists = response.json()['value']
        return next((item for item in todo_lists if item['displayName'].lower() == name.lower()), None)
```

### Interaction Flow

1. **User Interaction**: The user presses the space bar to start and stop the recording.
2. **Transcription**: The audio recorded is transcribed to text.
3. **LLM Processing**: The transcribed text is processed by the LLM engine to determine if any tool calls are needed.
4. **Tool Execution**: If tool calls are identified, the corresponding tool methods are executed.
5. **Response Generation**: The assistant generates a response based on the tool execution result and provides feedback to the user.

### Conclusion

This part of the "home_assistant" project establishes a robust framework for integrating external tools, exemplified by the Microsoft ToDo functionality. The assistant thus gains valuable utility for managing everyday tasks through seamless voice commands and automated list management.