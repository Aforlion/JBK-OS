from __future__ import annotations

import os
import logging
from typing import Any
from datetime import datetime, timezone

from core.worker_registry import WorkerRegistry
from core.project_registry import ProjectRegistry
from core.skill_registry import SkillRegistry
from core.knowledge_registry import KnowledgeRegistry
from core.chief_of_staff import ChiefOfStaff
from core.execution_planner import ExecutionPlanner
from core.executive_briefing_engine import ExecutiveBriefingEngine
from core.antigravity_execution_engine import AntigravityExecutionEngine
from core.executive_console import ExecutiveConsole
from core.executive import Executive, ExecutiveStatus
from core.knowledge import KnowledgeItem, KnowledgeStatus
from core.skill import Skill, SkillStatus
from runtime import Runtime

LOGGER = logging.getLogger(__name__)


def parse_yaml(content: str) -> dict[str, Any]:
    lines = content.split('\n')
    result: dict[str, Any] = {}
    current_section = None
    
    for line in lines:
        if '#' in line:
            line = line.split('#')[0]
        stripped = line.strip()
        if not stripped:
            continue
            
        indent = len(line) - len(line.lstrip())
        
        if indent == 0:
            current_section = None
            if ':' in stripped:
                k, v = stripped.split(':', 1)
                k = k.strip().strip('"').strip("'")
                v = v.strip().strip('"').strip("'")
                if v:
                    if v.lower() == 'true':
                        val = True
                    elif v.lower() == 'false':
                        val = False
                    elif v.isdigit():
                        val = int(v)
                    elif v.replace('.', '', 1).isdigit() and '.' in v:
                        val = float(v)
                    else:
                        val = v
                    result[k] = val
                else:
                    result[k] = {}
                    current_section = k
        else:
            if current_section:
                if stripped.startswith('-'):
                    val = stripped[1:].strip().strip('"').strip("'")
                    if val.lower() == 'true':
                        val = True
                    elif val.lower() == 'false':
                        val = False
                    elif val.isdigit():
                        val = int(val)
                    elif val.replace('.', '', 1).isdigit() and '.' in val:
                        val = float(val)
                    
                    if isinstance(result[current_section], dict):
                        result[current_section] = []
                    result[current_section].append(val)
                elif ':' in stripped:
                    k, v = stripped.split(':', 1)
                    k = k.strip().strip('"').strip("'")
                    v = v.strip().strip('"').strip("'")
                    if v.lower() == 'true':
                        val = True
                    elif v.lower() == 'false':
                        val = False
                    elif v.isdigit():
                        val = int(v)
                    elif v.replace('.', '', 1).isdigit() and '.' in v:
                        val = float(v)
                    else:
                        val = v
                    
                    if isinstance(result[current_section], dict):
                        result[current_section][k] = val
                        
    return result




def locate_jbk_root() -> str:
    # If running in a Docker container (where code is under /app and JBK-OS has no parent sibling)
    if os.environ.get("JBK_ENVIRONMENT") == "PRODUCTION" or os.path.exists("/app"):
        return "/app"

    # Traverses upwards from current file to locate the JBK root (containing JBK-OS, JBK-Company, etc.)
    current = os.path.abspath(os.path.dirname(__file__))
    while current:
        if os.path.exists(os.path.join(current, "JBK-OS")) and os.path.exists(os.path.join(current, "JBK-Company")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    
    # Fallback default
    if os.path.exists(r"c:\JBK"):
        return r"c:\JBK"
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load_config(jbk_root: str) -> dict[str, Any]:
    # Check JBK-OS/config under jbk_root, fallback to config/ directly under jbk_root (for containers)
    config_dir = os.path.join(jbk_root, "JBK-OS", "config")
    if not os.path.exists(config_dir):
        config_dir = os.path.join(jbk_root, "config")
        
    config = {}
    
    files = ["company.yaml", "paths.yaml", "runtime.yaml", "logging.yaml", "skills.yaml", "executives.yaml"]
    for f in files:
        fp = os.path.join(config_dir, f)
        if not os.path.exists(fp):
            raise FileNotFoundError(f"Required configuration file missing: {fp}")
        with open(fp, "r", encoding="utf-8") as file_obj:
            content = file_obj.read()
        config[os.path.splitext(f)[0]] = parse_yaml(content)
        
    return config


def validate_environment(jbk_root: str, config: dict[str, Any]) -> None:
    paths = config.get("paths", {})
    required_dirs = [
        paths.get("company_dir", "JBK-Company"),
        paths.get("brain_dir", "JBK-Brain"),
        paths.get("skills_dir", "JBK-Skills"),
        paths.get("projects_dir", "JBK-Projects"),
        paths.get("data_dir", "JBK-Data"),
        paths.get("workspace_dir", "workspace"),
    ]
    
    for d in required_dirs:
        full_path = os.path.join(jbk_root, d)
        if not os.path.exists(full_path):
            # Self-healing: create the directory dynamically inside container/local runs
            os.makedirs(full_path, exist_ok=True)


class DirectoryNotFoundError(Exception):
    pass


def initialize_logging(config: dict[str, Any]) -> None:
    logging_config = config.get("logging", {})
    log_level_str = logging_config.get("log_level", "INFO")
    level = getattr(logging, log_level_str, logging.INFO)
    
    log_location = logging_config.get("log_location", "")
    if log_location:
        os.makedirs(os.path.dirname(log_location), exist_ok=True)
        
    handlers = []
    if logging_config.get("console_output", True):
        handlers.append(logging.StreamHandler())
    if logging_config.get("file_output", True) and log_location:
        handlers.append(logging.FileHandler(log_location, encoding="utf-8"))
        
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
        force=True
    )


def load_company_assets(jbk_root: str, worker_registry: WorkerRegistry) -> None:
    company_dir = os.path.join(jbk_root, "JBK-Company", "Executive")
    if not os.path.exists(company_dir):
        return
        
    for f in os.listdir(company_dir):
        if f.endswith(".md"):
            fp = os.path.join(company_dir, f)
            with open(fp, "r", encoding="utf-8") as file_obj:
                content = file_obj.read()
                
            title = ""
            executive_id = None
            mission = ""
            
            lines = content.split('\n')
            for line in lines:
                if line.startswith("# Personnel File"):
                    title = line.split("Personnel File")[1].replace("–", "").replace("-", "").strip()
                elif line.startswith("Employee ID:"):
                    executive_id = line.split("Employee ID:")[1].strip()
                    
            if "# Mission" in content:
                parts = content.split("# Mission")
                if len(parts) > 1:
                    mission_part = parts[1].strip()
                    mission_lines = [l.strip() for l in mission_part.split('\n') if l.strip()]
                    if mission_lines:
                        mission = mission_lines[0]
                        
            if not title:
                title = os.path.splitext(f)[0]
            if not mission:
                mission = f"Own {title} outcomes."
                
            exec_obj = Executive(title=title, mission=mission, executive_id=executive_id)
            worker_registry.register(exec_obj)


def load_knowledge_assets(jbk_root: str, knowledge_registry: KnowledgeRegistry) -> None:
    brain_dir = os.path.join(jbk_root, "JBK-Brain")
    if not os.path.exists(brain_dir):
        return
        
    idx = 1
    for root, _, files in os.walk(brain_dir):
        for file in files:
            if file.endswith(".md") or file.endswith(".txt"):
                fp = os.path.join(root, file)
                rel_path = os.path.relpath(fp, jbk_root)
                category = os.path.basename(root)
                
                title = os.path.splitext(file)[0]
                description = f"Knowledge document: {title}"
                
                try:
                    with open(fp, 'r', encoding='utf-8') as f:
                        first_line = f.readline().strip()
                        if first_line.startswith("#"):
                            title = first_line.replace("#", "").strip()
                            sec_line = f.readline().strip()
                            if sec_line:
                                description = sec_line
                except Exception:
                    pass
                    
                ki = KnowledgeItem(
                    knowledge_id=f"KI-{idx:04d}",
                    title=title,
                    category=category,
                    owner="CEO",
                    source=rel_path,
                    tags=[category.lower()],
                    description=description,
                    version="1.0",
                    status=KnowledgeStatus.ACTIVE
                )
                knowledge_registry.register(ki)
                idx += 1


def load_skills(jbk_root: str, skill_registry: SkillRegistry) -> None:
    skills_dir = os.path.join(jbk_root, "JBK-Skills")
    if not os.path.exists(skills_dir):
        return
        
    idx = 1
    for root, _, files in os.walk(skills_dir):
        for file in files:
            if file.lower() == "skill.md":
                fp = os.path.join(root, file)
                folder_name = os.path.basename(root)
                category = os.path.basename(os.path.dirname(root))
                
                with open(fp, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                name = folder_name.replace("-", " ").title()
                description = f"Executor for capability: {name}"
                
                # Check for frontmatter
                if content.startswith("---"):
                    parts = content.split("---")
                    if len(parts) > 2:
                        fm = parse_yaml(parts[1])
                        name = fm.get("name", name)
                        description = fm.get("description", description)
                        
                skill = Skill(
                    skill_id=folder_name,
                    name=name,
                    description=description,
                    owner_id="EXEC-0001",
                    department=category,
                    execution_engine="Antigravity",
                    capabilities=[folder_name.lower(), category.lower()],
                    inputs=["task_description"],
                    outputs=["execution_log"],
                    version="1.0",
                    status=SkillStatus.AVAILABLE
                )
                skill_registry.register(skill)
                idx += 1


def bootstrap() -> Runtime:
    try:
        jbk_root = locate_jbk_root()
        config = load_config(jbk_root)
        validate_environment(jbk_root, config)
        initialize_logging(config)
        
        LOGGER.info("Starting JBK OS Boot Sequence...")
        
        # Construct registries
        worker_registry = WorkerRegistry()
        project_registry = ProjectRegistry()
        skill_registry = SkillRegistry()
        knowledge_registry = KnowledgeRegistry()
        
        # Load assets
        load_company_assets(jbk_root, worker_registry)
        load_knowledge_assets(jbk_root, knowledge_registry)
        load_skills(jbk_root, skill_registry)
        
        # Construct services
        chief_of_staff = ChiefOfStaff(worker_registry, project_registry)
        execution_planner = ExecutionPlanner(skill_registry)
        executive_briefing_engine = ExecutiveBriefingEngine(chief_of_staff)
        execution_engine = AntigravityExecutionEngine()
        executive_console = ExecutiveConsole(executive_briefing_engine)
        
        workspace_path = os.path.join(jbk_root, config.get("paths", {}).get("workspace_dir", "workspace"))
        
        runtime_obj = Runtime(
            config=config,
            company=config.get("company", {}),
            worker_registry=worker_registry,
            project_registry=project_registry,
            skill_registry=skill_registry,
            knowledge_registry=knowledge_registry,
            chief_of_staff=chief_of_staff,
            execution_planner=execution_planner,
            executive_briefing_engine=executive_briefing_engine,
            execution_engine=execution_engine,
            executive_console=executive_console,
            workspace_path=workspace_path,
            logging_config=config.get("logging", {}),
        )
        
        LOGGER.info("JBK OS Kernel successfully booted and READY.")
        return runtime_obj
        
    except Exception as e:
        print(f"FATAL BOOT ERROR: {e}")
        LOGGER.fatal("FATAL BOOT ERROR", exc_info=True)
        raise e
