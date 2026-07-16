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
            import os
            if os.environ.get("JBK_ENVIRONMENT") == "PRODUCTION" or os.environ.get("PORT"):
                import uvicorn
                import logging
                from web.app import create_app
                from core.executive_console_controller import ExecutiveConsoleController
                
                logger = logging.getLogger("main")
                port = int(os.environ.get("PORT", 8080))
                logger.info(f"Starting production web server on port {port}...")
                
                from core.ai_executive_assistant import AIExecutiveAssistant
                ai_assistant = AIExecutiveAssistant(
                    chief_of_staff=runtime.chief_of_staff,
                    skill_registry=runtime.skill_registry,
                    knowledge_registry=runtime.knowledge_registry,
                )
                controller = ExecutiveConsoleController(
                    dashboard_engine=runtime.executive_briefing_engine,
                    portfolio_engine=runtime.chief_of_staff,
                    ai_assistant=ai_assistant,
                )
                app = create_app(controller)
                uvicorn.run(app, host="0.0.0.0", port=port)
                sys.exit(0)
            else:
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
