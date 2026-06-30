from fastapi import APIRouter, Depends
from datetime import date
from app.auth import get_current_user
from app.models import User
from app.schemas import DailyBriefing, BriefingItem, Insight

router = APIRouter(prefix="/briefing", tags=["briefing"])


@router.get("/daily", response_model=DailyBriefing)
async def daily_briefing(current_user: User = Depends(get_current_user)):
    today = date.today().isoformat()
    company = current_user.company or "Your Company"

    items = [
        BriefingItem(
            category="Revenue",
            title="Revenue decreased 8% this week",
            detail="North India sales dropped due to reduced distributor ordering frequency.",
            impact="₹1.8 crore revenue reduction expected over next 45 days",
            recommendation="Offer Distributor Incentive Plan A to key distributors",
            probability=81,
        ),
        BriefingItem(
            category="Inventory",
            title="Inventory shortage likely next Tuesday",
            detail="SKU #4821 stock will hit zero based on current depletion rate.",
            impact="Potential loss of ₹45 lakh in unfulfilled orders",
            recommendation="Trigger emergency restock order with Vendor B today",
            probability=88,
        ),
        BriefingItem(
            category="Cash Flow",
            title="Cash flow risk in 18 days",
            detail="Three large payables due simultaneously while receivables are delayed.",
            impact="Potential ₹2.1 crore shortfall",
            recommendation="Accelerate collections from top 5 overdue accounts",
            probability=72,
        ),
        BriefingItem(
            category="Customers",
            title="Three high-value customers likely to churn",
            detail="Usage patterns and support tickets indicate disengagement.",
            impact="Combined ARR at risk: ₹38 lakh",
            recommendation="Schedule executive check-in calls this week",
            probability=67,
        ),
        BriefingItem(
            category="Marketing",
            title="Meta ad spend underperforming",
            detail="CPA increased 34% over last 2 weeks with no change in targeting.",
            impact="₹8 lakh/month in wasted spend",
            recommendation="Pause Meta campaigns and reallocate to Google Search",
            probability=79,
        ),
    ]

    return DailyBriefing(
        date=today,
        company=company,
        overall_health="Caution",
        health_score=62,
        items=items,
        top_priority="Address cash flow risk and inventory shortage immediately.",
    )


@router.get("/insights", response_model=list[Insight])
async def get_insights(current_user: User = Depends(get_current_user)):
    insights = [
        Insight(
            id="ins-001",
            executive_id="cfo",
            executive_title="AI CFO",
            category="Cash Flow",
            priority="critical",
            title="Cash flow risk in 18 days",
            summary="Three large payables due simultaneously while receivables are delayed.",
            impact="Potential ₹2.1 crore shortfall",
            recommendation="Accelerate collections from top 5 overdue accounts",
            confidence=72,
            created_at=date.today().isoformat(),
        ),
        Insight(
            id="ins-002",
            executive_id="sales",
            executive_title="AI Sales Director",
            category="Revenue",
            priority="high",
            title="Revenue decreased 8% — North India distributor issue",
            summary="Distributor ordering frequency dropped significantly in North India region.",
            impact="₹1.8 crore over 45 days",
            recommendation="Offer Distributor Incentive Plan A",
            confidence=81,
            created_at=date.today().isoformat(),
        ),
        Insight(
            id="ins-003",
            executive_id="coo",
            executive_title="AI COO",
            category="Inventory",
            priority="high",
            title="SKU #4821 will hit zero stock by Tuesday",
            summary="Current depletion rate exceeds reorder buffer for this SKU.",
            impact="₹45 lakh in potential unfulfilled orders",
            recommendation="Trigger emergency restock with Vendor B today",
            confidence=88,
            created_at=date.today().isoformat(),
        ),
        Insight(
            id="ins-004",
            executive_id="sales",
            executive_title="AI Sales Director",
            category="Churn",
            priority="high",
            title="Three high-value customers showing churn signals",
            summary="Usage drops and support escalations correlate with pre-churn patterns.",
            impact="₹38 lakh ARR at risk",
            recommendation="Schedule executive check-in calls this week",
            confidence=67,
            created_at=date.today().isoformat(),
        ),
        Insight(
            id="ins-005",
            executive_id="marketing",
            executive_title="AI Marketing Director",
            category="Campaign",
            priority="medium",
            title="Meta ad CPA increased 34% — spend efficiency declining",
            summary="No changes in targeting but cost per acquisition has spiked.",
            impact="₹8 lakh/month wasted",
            recommendation="Pause Meta campaigns and reallocate budget to Google Search",
            confidence=79,
            created_at=date.today().isoformat(),
        ),
        Insight(
            id="ins-006",
            executive_id="hr",
            executive_title="AI HR Director",
            category="Hiring",
            priority="low",
            title="Hiring can be delayed by two months",
            summary="Current team velocity and backlog analysis shows no immediate capacity constraint.",
            impact="₹12 lakh savings in delayed onboarding costs",
            recommendation="Defer Q3 hiring plan by 6–8 weeks",
            confidence=74,
            created_at=date.today().isoformat(),
        ),
    ]
    return insights
