#!/usr/bin/env python3
"""
Automated benchmark suite for CheetahClaws.
Implements 5 coding tasks, runs CheetahClaws using subprocess,
and asserts the correctness of generated files.
"""
import os
import sys
import tempfile
import subprocess
import json
import urllib.request
import urllib.error
import importlib.util
from pathlib import Path

# Paths
WORKSPACE = Path("/Users/macbook/mekong-cli")
CHEETAHCLAWS_PATH = "/Users/macbook/.local/share/uv/tools/cheetahclaws/lib/python3.14/site-packages/cheetahclaws.py"
LLAMA_SERVER_PORT = 11434
LLAMA_HEALTH_URL = "http://localhost:11434"
LOCAL_LLM_URL = "http://localhost:11434/v1"
MODEL_NAME = "ollama/qwen3.6:35b-mlx-fast"

def check_server_health():
    """Check health endpoint of Ollama server."""
    try:
        req = urllib.request.Request(LLAMA_HEALTH_URL)
        with urllib.request.urlopen(req, timeout=2) as response:
            if response.status == 200:
                body = response.read().decode('utf-8')
                return True, f"Healthy: {body.strip()}"
            return False, f"Status code: {response.status}"
    except Exception as e:
        return False, str(e)

def start_llama_server():
    """Skip launching llama-server as we are using Ollama."""
    print("[-] Llama-server not responding and we are skipping launch-llama.sh as per Ollama configuration.")
    return False

def run_cheetahclaws(prompt: str, target_dir: Path) -> subprocess.CompletedProcess:
    """Run CheetahClaws programmatically inside target_dir."""
    cmd = [
        "python3",
        CHEETAHCLAWS_PATH,
        "-p",
        "--accept-all",
        "-m", MODEL_NAME,
        prompt
    ]
    env = os.environ.copy()
    env["LLM_BASE_URL"] = LOCAL_LLM_URL
    env["LLM_API_KEY"] = os.environ.get("LLM_API_KEY", "dummy-key")
    env["OLLAMA_BASE_URL"] = "http://localhost:11434"
    env["CUSTOM_BASE_URL"] = "http://localhost:11434/v1"

    print(f"[*] Executing CheetahClaws in {target_dir}")
    print(f"[*] Command: {' '.join(cmd)}")

    res = subprocess.run(
        cmd,
        cwd=target_dir,
        env=env,
        capture_output=True,
        text=True,
        timeout=300 # 5-minute timeout for inference
    )
    return res

def test_task_1(temp_dir: Path):
    """Task 1: String manipulation (string_utils.py)"""
    prompt = (
        "Implement a python module string_utils.py with two functions: "
        "to_camel_case(s: str) -> str and to_snake_case(s: str) -> str. "
        "to_camel_case should convert snake_case or kebab-case to camelCase (e.g. 'hello_world' or 'hello-world' to 'helloWorld'). "
        "to_snake_case should convert camelCase or kebab-case to snake_case (e.g. 'helloWorld' or 'hello-world' to 'hello_world')."
    )

    res = run_cheetahclaws(prompt, temp_dir)
    print(f"[Task 1 Stdout]\n{res.stdout}")
    print(f"[Task 1 Stderr]\n{res.stderr}")

    file_path = temp_dir / "string_utils.py"
    if not file_path.exists():
        raise FileNotFoundError("string_utils.py was not created")

    # Check syntax
    subprocess.run(["python3", "-m", "py_compile", str(file_path)], check=True)

    # Load and test logic
    spec = importlib.util.spec_from_file_location("string_utils", str(file_path))
    string_utils = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(temp_dir))
    try:
        spec.loader.exec_module(string_utils)
        assert string_utils.to_camel_case("hello_world") == "helloWorld"
        assert string_utils.to_camel_case("hello-world") == "helloWorld"
        assert string_utils.to_snake_case("helloWorld") == "hello_world"
        assert string_utils.to_snake_case("hello-world") == "hello_world"
    finally:
        sys.path.pop(0)

def test_task_2(temp_dir: Path):
    """Task 2: Markdown table parser (table_parser.py)"""
    prompt = (
        "Implement a python module table_parser.py with a function parse_markdown_table(table_str: str) -> list[dict]. "
        "It should parse a markdown table string into a list of dictionaries, where the keys are the column header names "
        "and values are the row values. Headers and values should be stripped of whitespace. Ignore the separator line (e.g. |---|---|)."
    )

    res = run_cheetahclaws(prompt, temp_dir)
    print(f"[Task 2 Stdout]\n{res.stdout}")
    print(f"[Task 2 Stderr]\n{res.stderr}")

    file_path = temp_dir / "table_parser.py"
    if not file_path.exists():
        raise FileNotFoundError("table_parser.py was not created")

    subprocess.run(["python3", "-m", "py_compile", str(file_path)], check=True)

    spec = importlib.util.spec_from_file_location("table_parser", str(file_path))
    table_parser = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(temp_dir))
    try:
        spec.loader.exec_module(table_parser)
        table = (
            "| Name | Age | City |\n"
            "|------|-----|------|\n"
            "| Alice | 30 | New York |\n"
            "| Bob   | 25 | Los Angeles |"
        )
        parsed = table_parser.parse_markdown_table(table)
        assert parsed == [
            {"Name": "Alice", "Age": "30", "City": "New York"},
            {"Name": "Bob", "Age": "25", "City": "Los Angeles"}
        ]
    finally:
        sys.path.pop(0)

def test_task_3(temp_dir: Path):
    """Task 3: Regex extraction (extractor.py)"""
    prompt = (
        "Implement a python module extractor.py with a function extract_emails_and_domains(text: str) -> list[tuple[str, str]]. "
        "It should use regular expressions to find all email addresses in the text and return them as a list of tuples containing (email, domain). "
        "For example, 'contact@example.com' returns ('contact@example.com', 'example.com')."
    )

    res = run_cheetahclaws(prompt, temp_dir)
    print(f"[Task 3 Stdout]\n{res.stdout}")
    print(f"[Task 3 Stderr]\n{res.stderr}")

    file_path = temp_dir / "extractor.py"
    if not file_path.exists():
        raise FileNotFoundError("extractor.py was not created")

    subprocess.run(["python3", "-m", "py_compile", str(file_path)], check=True)

    spec = importlib.util.spec_from_file_location("extractor", str(file_path))
    extractor = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(temp_dir))
    try:
        spec.loader.exec_module(extractor)
        text = "Send mail to support@domain.com or admin@web.org."
        extracted = extractor.extract_emails_and_domains(text)
        assert set(extracted) == {("support@domain.com", "domain.com"), ("admin@web.org", "web.org")}
    finally:
        sys.path.pop(0)

def test_task_4(temp_dir: Path):
    """Task 4: Bug fix (calculator.py)"""
    file_path = temp_dir / "calculator.py"
    with open(file_path, "w") as f:
        f.write(
            "def calculate_average(numbers):\n"
            "    return sum(numbers) / len(numbers)\n"
        )

    prompt = "Fix the division by zero bug in calculate_average in calculator.py. If the list is empty, return 0.0 or 0."

    res = run_cheetahclaws(prompt, temp_dir)
    print(f"[Task 4 Stdout]\n{res.stdout}")
    print(f"[Task 4 Stderr]\n{res.stderr}")

    subprocess.run(["python3", "-m", "py_compile", str(file_path)], check=True)

    spec = importlib.util.spec_from_file_location("calculator", str(file_path))
    calculator = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(temp_dir))
    try:
        spec.loader.exec_module(calculator)
        assert calculator.calculate_average([1, 2, 3]) == 2.0
        val = calculator.calculate_average([])
        assert val == 0.0 or val == 0
    finally:
        sys.path.pop(0)

def test_task_5(temp_dir: Path):
    """Task 5: Structured JSON generation (config.json)"""
    prompt = (
        "Generate a valid JSON file config.json that matches this schema: it must be a JSON object containing keys: "
        "'name' (a string), 'version' (a string, e.g. '1.0.0'), and 'enabled' (a boolean). Output only the JSON inside config.json."
    )

    res = run_cheetahclaws(prompt, temp_dir)
    print(f"[Task 5 Stdout]\n{res.stdout}")
    print(f"[Task 5 Stderr]\n{res.stderr}")

    file_path = temp_dir / "config.json"
    if not file_path.exists():
        raise FileNotFoundError("config.json was not created")

    with open(file_path, "r") as f:
        data = json.load(f)

    assert isinstance(data.get("name"), str)
    assert isinstance(data.get("version"), str)
    assert isinstance(data.get("enabled"), bool)

def main():
    print("=== Starting CheetahClaws Optimization Benchmark ===")

    # 1. Health checks and setup
    healthy, msg = check_server_health()
    print(f"[*] Initial health check on {LLAMA_HEALTH_URL}: {'OK' if healthy else 'FAILED'} ({msg})")

    if not healthy:
        start_llama_server()
        healthy, msg = check_server_health()
        if not healthy:
            print("[-] Critical Error: Llama-server is not running and could not be started.")
            print("[-] Exiting benchmark.")
            sys.exit(1)

    # 2. Run benchmark tasks
    tasks = [
        ("Task 1: String manipulation", test_task_1),
        ("Task 2: Markdown table parser", test_task_2),
        ("Task 3: Regex extraction", test_task_3),
        ("Task 4: Bug fix", test_task_4),
        ("Task 5: Structured JSON generation", test_task_5),
    ]

    results = {}
    passed_count = 0

    for name, task_func in tasks:
        print(f"\n--- Running {name} ---")
        with tempfile.TemporaryDirectory() as temp_dir_str:
            temp_dir = Path(temp_dir_str)
            try:
                task_func(temp_dir)
                print(f"[+] {name} PASSED")
                results[name] = "PASSED"
                passed_count += 1
            except Exception as e:
                import traceback
                print(f"[-] {name} FAILED: {e}")
                traceback.print_exc()
                results[name] = f"FAILED: {e}"

    # 3. Print final report
    print("\n================ BENCHMARK REPORT ================")
    for name, status in results.items():
        print(f"{name}: {status}")

    success_rate = (passed_count / len(tasks)) * 100
    print("--------------------------------------------------")
    print(f"Overall Success Rate: {success_rate:.1f}% ({passed_count}/{len(tasks)})")
    print("==================================================")

    if passed_count >= 4:
        print("[+] SUCCESS: Benchmark passed with >= 80% success rate.")
        sys.exit(0)
    else:
        print("[-] FAILURE: Benchmark failed to achieve 80% success rate.")
        sys.exit(1)

if __name__ == "__main__":
    main()
