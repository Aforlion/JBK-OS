Specification 033 — Portfolio Management Engine
Purpose

The Portfolio Management Engine provides executives with a real-time view of the company's entire client portfolio.

Instead of supervising one project, it supervises all projects simultaneously.

It enables the CEO to manage the business as a portfolio rather than as isolated engagements.

Responsibilities

The engine shall:

Monitor all active projects.
Classify project health across the portfolio.
Measure portfolio utilization.
Analyze delivery risk.
Detect resource conflicts.
Calculate portfolio KPIs.
Recommend executive actions.
Produce a PortfolioReport.
Inputs
Project Registry
Delivery Status Reports
Resource Allocation Plans
Worker Registry
Executive Briefings
Business Transformation Plans
Outputs

Creates:

PortfolioReport

Including:

Portfolio Summary
Active Projects
Completed Projects
At-Risk Projects
Critical Projects
Resource Utilization
Executive Workload
Revenue Pipeline (advisory)
Capacity Forecast
Strategic Opportunities
CEO Priority List
Business Rules
Advisory only.
Never modify projects.
Never assign workers.
Never close projects.
Portfolio health must be derived from project health.
Every recommendation must include supporting evidence.
Reports must serialize.
Key Portfolio KPIs

Examples:

Total Active Projects
Portfolio Health Score
Average Delivery Health
Resource Utilization %
Projects by Industry
Projects by Status
Critical Project Count
Capacity Remaining
Average Client Satisfaction (future placeholder)
Knowledge Assets Generated
Candidate Objects
PortfolioReport
PortfolioMetrics
PortfolioRecommendation
PortfolioRisk
CapacityForecast
Candidate Brain Entry

Portfolio-Management-Standards.md

# Portfolio Management Standards

1. Portfolio First
   Decisions should optimize the entire portfolio, not individual projects.

2. Advisory Boundaries
   The engine shall recommend but never execute portfolio changes.

3. Evidence-Based Recommendations
   Every recommendation must reference portfolio metrics.

4. Capacity Awareness
   Resource recommendations must consider company-wide utilization.

5. Executive Visibility
   Portfolio risks must be summarized for executive decision-making.
Future Evolution (Version 2+)
Revenue forecasting using signed proposals and project pipeline.
Profitability analysis by industry and client segment.
Multi-office and multi-region portfolio support.
Scenario planning ("What happens if we take on three more enterprise clients?").
AI-powered portfolio optimization.
Executive heat maps.
Capacity planning over rolling 30/90/365-day windows.
Integration with financial systems.
Strategic client scoring.
Portfolio digital twin for simulation and planning.