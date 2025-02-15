import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import json
import subprocess
from typing import List, Dict, Tuple
import re
from pathlib import Path

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)

APIPROXY_TOKEN = os.getenv("APIPROXY_TOKEN")

tools = [
    {
        "type": "function",
        "function": {
            "name": "script_runner",
            "description": "Install a package and run a script from a URL with provided arguments.",
            "parameters": {
                "type": "object",
                "properties": {
                    "script_url": {
                        "type": "string",
                        "description": "The URL of the script to run."
                    },
                    "args": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of arguments to pass to the script"
                    }
                },
                "required": ["script_url", "args"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "task_runner",
            "description": "Execute Python code with specified dependencies.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to execute"
                    },
                    "dependencies": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of Python package dependencies"
                    }
                },
                "required": ["code", "dependencies"]
            }
        }
    }
]

def is_safe_path(path: str) -> bool:
    """Ensure path is within /data directory"""
    path = os.path.abspath(path)
    data_dir = os.path.abspath("/data")
    return path.startswith(data_dir)

def parse_error_message(error: str) -> Tuple[str, str]:
    """Parse error message to extract relevant information for code regeneration"""
    syntax_pattern = r"SyntaxError: (.*)"
    import_pattern = r"ModuleNotFoundError: No module named '(.*)'"
    index_pattern = r"IndexError: (.*)"
    key_pattern = r"KeyError: (.*)"
    attribute_pattern = r"AttributeError: (.*)"
    
    error_patterns = {
        "SyntaxError": syntax_pattern,
        "ImportError": import_pattern,
        "IndexError": index_pattern,
        "KeyError": key_pattern,
        "AttributeError": attribute_pattern
    }
    
    error_type = next((et for et in error_patterns.keys() if et in error), "Unknown")
    
    if error_type in error_patterns:
        match = re.search(error_patterns[error_type], error)
        error_details = match.group(1) if match else error
    else:
        error_details = error
    
    return error_type, error_details

call_count = 0
def execute_llm_code(code: str, dependencies: List[str]) -> Dict:
    """Execute code generated by LLM with specified dependencies and error handling"""
    global call_count
    call_count += 1
    
    script_name = f"llm_code_{call_count}.py"
    llm_code = f"""#!/usr/bin/env python
    # requires-python = ">=3.11"
    # dependencies = [{', '.join(f'"{dep}"' for dep in dependencies)}]

{code.strip()}
"""

    try:
        with open(script_name, "w") as f:
            f.write(llm_code)
        
        output = subprocess.run(
            ["uv", "run", script_name],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        if output.returncode != 0:
            raise Exception(output.stderr)
            
        return {"status": "success", "output": output.stdout}
    
    except Exception as e:
        return {"status": "error", "error": str(e)}
    # finally:
    #     # Clean up the temporary script file
    #     if os.path.exists(script_name):
    #         os.remove(script_name)

def handle_code_error(error: str, original_task: str) -> Dict:
    """Handle code execution errors by requesting fixed code from LLM"""
    error_type, error_details = parse_error_message(error)
    
    url = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
    
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {APIPROXY_TOKEN}"
    }
    
    error_prompt = f"""
    The previous code generated for this task failed with the following error:
    Error Type: {error_type}
    Error Details: {error_details}
    
    Original Task: {original_task}
    
    Please generate new code that fixes this error. Make sure to:
    1. Handle the specific error case identified
    2. Include proper error handling
    3. Verify all dependencies are correctly specified
    4. Use proper syntax and avoid common pitfalls
    5. Ensure proper file operations within /data directory
    
    Respond using the task_runner tool with the corrected code.
    """
    
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": error_prompt
            },
            {
                "role": "system",
                "content": "You are a code correction assistant. Generate fixed code that addresses the specific error encountered."
            }
        ],
        "tools": tools,
        "tool_choice": "auto"
    }
    
    try:
        response = requests.post(url=url, headers=headers, json=data)
        tool_call = response.json()["choices"][0]["message"]["tool_calls"][0]
        
        if tool_call["function"]["name"] == "task_runner":
            arguments = json.loads(tool_call["function"]["arguments"])
            return execute_llm_code(arguments['code'], arguments['dependencies'])
        else:
            return {"status": "error", "error": "Invalid tool selected for error correction"}
    
    except Exception as e:
        return {"status": "error", "error": f"Error during code regeneration: {str(e)}"}

@app.get("/")
def home():
    return {"message": "Welcome to TDS."}

@app.get("/read")
def read_file(path: str):
    """Safely read file content if within /data directory"""
    if not is_safe_path(path):
        raise HTTPException(status_code=403, detail="Access denied: Can only access files in /data directory")
    try:
        with open(path, "r") as f:
            return f.read()
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Error reading file: {str(e)}")

@app.post("/run")
def run_task(task: str):
    url = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
    
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {APIPROXY_TOKEN}"
    }

    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": task
            },
            {
                "role": "system",
                "content": """
                You are an assistant who handles various file processing tasks. Analyze the task and:

                1. For running external scripts (like datagen.py), use script_runner tool with:
                   - Direct URL to the script
                   - Required arguments as a list
                
                2. For tasks that need file processing (like counting dates, sorting JSON, etc.), 
                   use task_runner and:
                   - Include all necessary imports (pandas, datetime, json, etc.)
                   - Read input files using standard Python file operations
                   - Process the content as required
                   - Write output to the specified file
                   - Add proper error handling
                   - Specify all required dependencies
                
                Important rules:
                - Only access files in the /data directory
                - Never delete any files
                - For file tasks, use basic Python file operations (open, read, write)
                - Handle file paths safely
                - Include all necessary dependencies in task_runner
                - Use proper error handling for all operations
                - Process files in a memory-efficient way for large files
                
                Common dependencies to include when needed:
                - pandas for data processing
                - python-dateutil for date handling
                - Pillow for image processing
                - sqlite3 for database operations
                """
            }
        ],
        "tools": tools,
        "tool_choice": "auto"
    }

    try:
        response = requests.post(url=url, headers=headers, json=data)
        response.raise_for_status()
        
        tool_call = response.json()["choices"][0]["message"]["tool_calls"][0]
        arguments = json.loads(tool_call["function"]["arguments"])
        
        if tool_call["function"]["name"] == "script_runner":
            script_url = arguments['script_url']
            args = arguments['args']
            if not script_url.startswith('http'):
                return {"status": "error", "error": "Invalid script URL"}
            command = ["uv", "run", script_url] + args
            result = subprocess.run(command, capture_output=True, text=True, cwd=os.getcwd())
            return {"status": "success", "output": result.stdout}
        
        elif tool_call["function"]["name"] == "task_runner":
            result = execute_llm_code(arguments['code'], arguments['dependencies'])
            
            if result["status"] == "error":
                return handle_code_error(result["error"], task)
                
            return result
        
        else:
            return {"status": "error", "error": "Invalid tool selected"}
            
    except requests.exceptions.RequestException as e:
        return {"status": "error", "error": f"API request failed: {str(e)}"}
    except json.JSONDecodeError as e:
        return {"status": "error", "error": f"Invalid JSON response: {str(e)}"}
    except Exception as e:
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)