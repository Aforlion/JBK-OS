import sys
from bootstrap import bootstrap

def display_banner(company_name: str, version: str) -> None:
    banner = f"""
==================================================
        {company_name.upper()} OPERATING SYSTEM
==================================================
Version: {version}
Status:  BOOTED & READY
==================================================
"""
    print(banner)

def main() -> None:
    try:
        runtime = bootstrap()
        company_name = runtime.company.get("company_name", "JBK Technologies")
        version = runtime.company.get("version", "1.0")
        
        display_banner(company_name, version)
        
        # Load and display console screen
        screen = runtime.executive_console.load()
        print(screen)
        
        # Exit gracefully if not interactive (e.g. running in testing pipeline)
        if not sys.stdin.isatty():
            print("\nNon-interactive mode detected. Kernel ready and exiting cleanly.")
            sys.exit(0)
            
        print("\nEnter command (type 'help' for commands, 'exit' to shutdown):")
        while True:
            try:
                line = input("> ").strip()
                if line.lower() == 'exit':
                    print("Shutting down JBK OS...")
                    break
                if not line:
                    continue
                out = runtime.executive_console.execute_command(line)
                print(out)
            except (KeyboardInterrupt, EOFError):
                print("\nShutting down JBK OS...")
                break
                
    except Exception as e:
        print(f"FAILED TO BOOT JBK OS: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
