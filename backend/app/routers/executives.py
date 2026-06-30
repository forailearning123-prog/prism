from fastapi import APIRouter, Depends, HTTPException, status
from app.auth import get_current_user
from app.models import User
from app.schemas import ExecutiveBase

router = APIRouter(prefix="/executives", tags=["executives"])

EXECUTIVES: list[ExecutiveBase] = [
    ExecutiveBase(
        id="cfo",
        title="AI CFO",
        role="Chief Financial Officer",
        description="Financial health, cash flow, forecasts, profitability, cost optimization, and investment suggestions.",
        focus_areas=["Cash Flow", "Profitability", "Forecasting", "Cost Optimization"],
        status="active",
        insights_count=5,
        risk_level="medium",
    ),
    ExecutiveBase(
        id="coo",
        title="AI COO",
        role="Chief Operating Officer",
        description="Operations, supply chain, manufacturing, inventory, and vendor performance.",
        focus_areas=["Supply Chain", "Inventory", "Operations", "Vendor Performance"],
        status="active",
        insights_count=3,
        risk_level="low",
    ),
    ExecutiveBase(
        id="sales",
        title="AI Sales Director",
        role="Sales Director",
        description="Pipeline, forecast, lead scoring, sales performance, and territory optimization.",
        focus_areas=["Pipeline", "Lead Scoring", "Revenue Forecast", "Territory"],
        status="active",
        insights_count=7,
        risk_level="high",
    ),
    ExecutiveBase(
        id="hr",
        title="AI HR Director",
        role="HR Director",
        description="Hiring, attrition, performance, compensation, and retention.",
        focus_areas=["Attrition Risk", "Hiring", "Performance", "Compensation"],
        status="active",
        insights_count=2,
        risk_level="low",
    ),
    ExecutiveBase(
        id="marketing",
        title="AI Marketing Director",
        role="Marketing Director",
        description="Campaign ROI, acquisition, retention, and spend optimization.",
        focus_areas=["Campaign ROI", "Acquisition", "Retention", "Spend Optimization"],
        status="active",
        insights_count=4,
        risk_level="medium",
    ),
    ExecutiveBase(
        id="ceo",
        title="AI CEO Assistant",
        role="CEO Assistant",
        description="Daily summary, critical risks, top opportunities, priorities, and decision tracking.",
        focus_areas=["Daily Summary", "Critical Risks", "Opportunities", "Decisions"],
        status="active",
        insights_count=8,
        risk_level="medium",
    ),
]


@router.get("", response_model=list[ExecutiveBase])
async def list_executives(current_user: User = Depends(get_current_user)):
    return EXECUTIVES


@router.get("/{executive_id}", response_model=ExecutiveBase)
async def get_executive(executive_id: str, current_user: User = Depends(get_current_user)):
    for exec_ in EXECUTIVES:
        if exec_.id == executive_id:
            return exec_
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Executive not found")
