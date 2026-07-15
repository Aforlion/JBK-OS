import os
import sys

def validate_repo() -> None:
    print("--- Starting Repository Validation ---")
    
    # 1. Check Required Directories
    required_dirs = ["core", "web", "portal", "config", "tests", "docs"]
    missing_dirs = []
    for d in required_dirs:
        if not os.path.isdir(d):
            missing_dirs.append(d)
            
    if missing_dirs:
        print(f"ERROR: Missing directories: {missing_dirs}")
        sys.exit(1)
    else:
        print("PASS: Required directory structure intact.")

    # 2. Check Configuration Files
    config_dir = "config"
    required_configs = ["company.yaml", "executives.yaml", "logging.yaml", "paths.yaml", "runtime.yaml", "skills.yaml"]
    missing_configs = []
    for c in required_configs:
        path = os.path.join(config_dir, c)
        if not os.path.isfile(path):
            missing_configs.append(c)
            
    if missing_configs:
        print(f"ERROR: Missing config files in config/: {missing_configs}")
        sys.exit(1)
    else:
        print("PASS: Required configuration files exist.")

    # 3. Check Dependency Manifests
    required_manifests = ["requirements.txt", "requirements-dev.txt"]
    missing_manifests = []
    for m in required_manifests:
        if not os.path.isfile(m):
            missing_manifests.append(m)
            
    if missing_manifests:
        print(f"ERROR: Missing dependency manifests: {missing_manifests}")
        sys.exit(1)
    else:
        print("PASS: Dependency manifests exist.")

    # 4. Check Bootstrap Syntax and Compile Integrity
    try:
        import py_compile
        py_compile.compile("bootstrap.py", doraise=True)
        py_compile.compile("main.py", doraise=True)
        py_compile.compile("runtime.py", doraise=True)
        print("PASS: Core bootstrap and entry scripts compile successfully.")
    except Exception as e:
        print(f"ERROR: Compilation failed: {e}")
        sys.exit(1)

    print("--- Repository Validation PASS ---")

if __name__ == "__main__":
    validate_repo()
