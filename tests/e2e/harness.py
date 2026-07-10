#!/usr/bin/env python3
import sys
import os
import argparse
import subprocess
import time
from pathlib import Path
import xml.etree.ElementTree as ET

# Root paths
ROOT_DIR = Path(__file__).resolve().parents[2]
E2E_DIR = ROOT_DIR / "tests" / "e2e"
TESTS_DIR = E2E_DIR / "antigravity_e2e"
DEFAULT_REPORT_PATH = ROOT_DIR / "docs" / "reports" / "harness-run-report.md"

def parse_args():
    parser = argparse.ArgumentParser(description="Anti-Gravity 2.0 E2E Test Harness Runner")
    parser.add_argument("--mock", action="store_true", help="Run tests against the Python CLI mock shim (default)")
    parser.add_argument("--prod", "--production", action="store_true", help="Run tests against the compiled Rust binary")
    parser.add_argument("--feature", "-f", type=str, choices=["F1", "F2", "F3", "F4", "F5"], help="Filter tests by Feature ID (F1-F5)")
    parser.add_argument("--tier", "-t", type=str, choices=["1", "2", "3", "4"], help="Filter tests by Tier Complexity (1-4)")
    parser.add_argument("--parallel", "-p", action="store_true", help="Run test suites in parallel across files")
    parser.add_argument("--report", type=str, default=str(DEFAULT_REPORT_PATH), help="Path to write the markdown test report")
    return parser.parse_args()

def build_rust_binary():
    rust_dir = ROOT_DIR / "antigravity" / "hybrid_runtime"
    print(f"[*] Compiling Rust binary in {rust_dir}...")
    proc = subprocess.run("cargo build", shell=True, cwd=str(rust_dir))
    if proc.returncode != 0:
        print("[!] Rust compilation failed.")
        return False
    print("[+] Rust compilation completed successfully.")
    return True

def setup_environment(args):
    env = os.environ.copy()

    # Track selection
    if args.prod:
        bin_path = ROOT_DIR / "antigravity" / "hybrid_runtime" / "target" / "debug" / "antigravity"
        if not bin_path.exists():
            print(f"[!] Rust binary not found at {bin_path}")
            if not build_rust_binary():
                print("[!] Cannot proceed without Rust binary. Exiting.")
                sys.exit(1)

        env["ANTIGRAVITY_BIN"] = str(bin_path)
        track = "Production"
    else:
        mock_shim = E2E_DIR / "mock_antigravity.py"
        env["ANTIGRAVITY_BIN"] = f"python3 {mock_shim}"

        # Inject mock API key if missing
        if not env.get("ANTHROPIC_API_KEY"):
            env["ANTHROPIC_API_KEY"] = "mock_key"

        track = "Mock/Simulation"

    return env, track

def get_filter_expression(args):
    exprs = []
    if args.feature:
        exprs.append(f"_{args.feature.lower()}_")

    if args.tier:
        if args.tier == "1":
            exprs.append("_t1_")
        elif args.tier == "2":
            exprs.append("_t2_")
        elif args.tier == "3":
            # Combination tests
            exprs.append("(_f1_f5_ or _f2_f3_ or _f3_f4_ or _f1_f3_ or _f2_f4_)")
        elif args.tier == "4":
            # Real world workload tests
            exprs.append("(_r1_ or _r2_ or _r3_ or _r4_ or _r5_)")

    if exprs:
        return " and ".join(exprs)
    return None

def run_tests_sequentially(env, filter_expr, xml_path):
    cmd = ["python3", "-m", "pytest", str(TESTS_DIR), f"--junitxml={xml_path}", "-v"]
    if filter_expr:
        cmd.extend(["-k", filter_expr])

    print(f"[*] Executing Command: {' '.join(cmd)}")
    start_time = time.time()
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
    duration = time.time() - start_time

    return proc.returncode, proc.stdout, proc.stderr, duration

def run_tests_in_parallel(env, filter_expr, xml_path):
    test_files = sorted(list(TESTS_DIR.glob("test_*.py")))
    processes = []
    xml_paths = []

    start_time = time.time()

    for i, tf in enumerate(test_files):
        sub_xml = xml_path.with_name(f"{xml_path.stem}_{i}.xml")
        xml_paths.append(sub_xml)

        # Isolate database for this parallel worker
        worker_env = env.copy()
        worker_env["ANTIGRAVITY_DB"] = f".git/antigravity/session_worker_{i}.db"

        cmd = ["python3", "-m", "pytest", str(tf), f"--junitxml={sub_xml}", "-v"]
        if filter_expr:
            cmd.extend(["-k", filter_expr])

        print(f"[*] Spawning Parallel Worker for: {tf.name} (DB: {worker_env['ANTIGRAVITY_DB']})")
        p = subprocess.Popen(cmd, env=worker_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        processes.append((p, tf.name))

    # Wait for all processes to complete
    stdout_combined = []
    stderr_combined = []
    exit_codes = []

    for p, name in processes:
        stdout, stderr = p.communicate()
        exit_codes.append(p.returncode)
        stdout_combined.append(f"=== Worker {name} Stdout ===\n{stdout}")
        if stderr.strip():
            stderr_combined.append(f"=== Worker {name} Stderr ===\n{stderr}")

    duration = time.time() - start_time

    # Merge JUnit XML files
    merge_junit_xmls(xml_paths, xml_path)

    # Cleanup individual xml files and worker databases
    for path in xml_paths:
        if path.exists():
            path.unlink()

    for i in range(len(test_files)):
        for ext in ["", "-wal", "-shm"]:
            db_file = ROOT_DIR / f".git/antigravity/session_worker_{i}.db{ext}"
            if db_file.exists():
                try:
                    db_file.unlink()
                except Exception:
                    pass

    overall_exit_code = 0 if all(ec == 0 or ec == 5 for ec in exit_codes) else 1 # Code 5 means no tests collected
    return overall_exit_code, "\n".join(stdout_combined), "\n".join(stderr_combined), duration

def merge_junit_xmls(xml_paths, output_path):
    merged_suites = []
    total_tests = 0
    total_failures = 0
    total_errors = 0
    total_skipped = 0
    total_time = 0.0

    for path in xml_paths:
        if not path.exists():
            continue
        try:
            tree = ET.parse(path)
            root = tree.getroot()
            if root.tag == "testsuites":
                for suite in root.findall("testsuite"):
                    merged_suites.append(suite)
                    total_tests += int(suite.get("tests", 0))
                    total_failures += int(suite.get("failures", 0))
                    total_errors += int(suite.get("errors", 0))
                    total_skipped += int(suite.get("skipped", 0))
                    total_time += float(suite.get("time", 0.0))
            elif root.tag == "testsuite":
                merged_suites.append(root)
                total_tests += int(root.get("tests", 0))
                total_failures += int(root.get("failures", 0))
                total_errors += int(root.get("errors", 0))
                total_skipped += int(root.get("skipped", 0))
                total_time += float(root.get("time", 0.0))
        except Exception as e:
            print(f"[!] Error parsing XML file {path}: {e}")

    # Create final tree
    root_new = ET.Element("testsuites")
    root_new.set("tests", str(total_tests))
    root_new.set("failures", str(total_failures))
    root_new.set("errors", str(total_errors))
    root_new.set("time", f"{total_time:.3f}")

    for suite in merged_suites:
        root_new.append(suite)

    tree_new = ET.ElementTree(root_new)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tree_new.write(output_path, encoding="utf-8", xml_declaration=True)

def generate_report(xml_path, report_path, track, bin_path, args, duration):
    passed_count = 0
    failed_count = 0
    errors_count = 0
    skipped_count = 0
    total_count = 0
    failures_details = []

    if xml_path.exists():
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            # Helper to parse single suite
            def parse_suite(suite):
                nonlocal passed_count, failed_count, errors_count, skipped_count, total_count
                for tc in suite.findall("testcase"):
                    total_count += 1
                    name = tc.get("name")
                    classname = tc.get("classname")

                    failure = tc.find("failure")
                    error = tc.find("error")
                    skipped = tc.find("skipped")

                    if failure is not None:
                        failed_count += 1
                        failures_details.append({
                            "name": name,
                            "class": classname,
                            "type": "Failure",
                            "message": failure.get("message", "No message"),
                            "text": failure.text or ""
                        })
                    elif error is not None:
                        errors_count += 1
                        failures_details.append({
                            "name": name,
                            "class": classname,
                            "type": "Error",
                            "message": error.get("message", "No message"),
                            "text": error.text or ""
                        })
                    elif skipped is not None:
                        skipped_count += 1
                    else:
                        passed_count += 1

            if root.tag == "testsuite":
                parse_suite(root)
            else:
                for suite in root.findall("testsuite"):
                    parse_suite(suite)
        except Exception as e:
            print(f"[!] Error parsing merged XML report: {e}")

    # Write report
    report_path_obj = Path(report_path)
    report_path_obj.parent.mkdir(parents=True, exist_ok=True)

    status_text = "FAILED" if (failed_count > 0 or errors_count > 0 or total_count == 0) else "PASSED"
    status_color = "🔴" if status_text == "FAILED" else "🟢"

    with open(report_path, "w") as f:
        f.write("# Anti-Gravity 2.0 Test Harness Run Report\n\n")
        f.write(f"### Status: {status_color} {status_text}\n\n")
        f.write("## Metadata\n")
        f.write(f"- **Timestamp**: {time.strftime('%Y-%m-%d %H:%M:%S %Z')}\n")
        f.write(f"- **Execution Track**: {track}\n")
        f.write(f"- **Target Binary**: `{bin_path}`\n")
        f.write(f"- **Feature Filter**: `{args.feature or 'None'}`\n")
        f.write(f"- **Tier Filter**: `{args.tier or 'None'}`\n")
        f.write(f"- **Parallel Workspaces**: `{'Yes' if args.parallel else 'No'}`\n")
        f.write(f"- **Total Duration**: `{duration:.2f} seconds`\n\n")

        f.write("## Metrics Summary\n")
        f.write("| Metric | Count |\n")
        f.write("|---|---|\n")
        f.write(f"| **Total Collected** | {total_count} |\n")
        f.write(f"| **Passed** | {passed_count} |\n")
        f.write(f"| **Failed** | {failed_count} |\n")
        f.write(f"| **Errors** | {errors_count} |\n")
        f.write(f"| **Skipped** | {skipped_count} |\n\n")

        if failures_details:
            f.write("## Failures & Errors Details\n\n")
            for detail in failures_details:
                f.write(f"### {detail['type']}: `{detail['name']}` ({detail['class']})\n")
                f.write(f"**Message**: {detail['message']}\n")
                f.write(f"```text\n{detail['text'].strip()[:800]}\n```\n\n")

    print(f"[+] Markdown report saved to {report_path}")

def main():
    args = parse_args()

    # 1. Setup environment and tracks
    env, track = setup_environment(args)
    bin_path = env.get("ANTIGRAVITY_BIN")
    print(f"[*] Harness track: {track}")
    print(f"[*] Target Binary: {bin_path}")

    # 2. Heuristics keyword filter
    filter_expr = get_filter_expression(args)
    if filter_expr:
        print(f"[*] Applying filter: {filter_expr}")

    xml_path = ROOT_DIR / "tests" / "e2e" / "junit_report.xml"
    if xml_path.exists():
        xml_path.unlink()

    # 3. Test execution
    if args.parallel:
        exit_code, stdout, stderr, duration = run_tests_in_parallel(env, filter_expr, xml_path)
    else:
        exit_code, stdout, stderr, duration = run_tests_sequentially(env, filter_expr, xml_path)

    # 4. Save artifacts & generate report
    generate_report(xml_path, args.report, track, bin_path, args, duration)

    # Cleanup final junit xml
    if xml_path.exists():
        xml_path.unlink()

    print(f"[*] Test run duration: {duration:.2f} seconds")
    print(f"[*] Exit status code: {exit_code}")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
