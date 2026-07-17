# JBK-OS Customer Onboarding Guide

Welcome to **JBK-OS**! This guide will help you log in, configure your workspace registries, and run your first automated business workflow.

## 1. Accessing Your Workspace

1. Open your browser and navigate to your custom workspace URL (provided by your administrator, e.g., `https://clientname.os.jbk.tech`).
2. Log in using the secure credentials provided in your welcome email.

## 2. Setting Up Your Registries

Before JBK-OS can orchestrate your operations, it needs to know who is on your team and what they can do.

### Step 2.1: Register Your Workers
1. Navigate to the **Worker Registry** section.
2. Click **Add Worker** and fill in details:
   - **Name**: e.g., Alice Johnson
   - **Role**: e.g., Dev Lead
   - **ID**: Assign a unique ID (e.g., `EXEC-0001`).

### Step 2.2: Register Worker Skills
1. Navigate to the **Skill Registry** section.
2. Map capabilities to your team members so the orchestrator knows who can execute what:
   - Example: Assign `API & Backend Development` skill to Alice Johnson (`EXEC-0001`).

---

## 3. Running Your First Workflow

Let's run a test project intake to see the system in action:

1. Click on **New Opportunity** in the dashboard.
2. In the text input field, describe a new client opportunity in natural language:
   > "We need a database setup. Budget is $10,000. Contact: info@client.com."
3. Click **Submit**.
4. Observe the system process the intake:
   - It will automatically classify the opportunity.
   - It will generate discovery questions.
   - It will output a project estimate, pricing split, and generate a draft proposal.
5. Click **Approve** to transition the proposal into an active delivery project!
