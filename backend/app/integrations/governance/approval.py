"""
Approval Workflow
Manages approval workflows for integration changes.
"""

from typing import Any, Optional, Dict, List
from datetime import datetime, timezone
from enum import Enum


class ApprovalStatus(str, Enum):
    """Approval status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ApprovalWorkflow:
    """
    Manages approval workflows for integration changes.
    Supports multi-level approvals and notifications.
    """
    
    def __init__(self):
        """Initialize approval workflow."""
        self.workflows: Dict[int, dict[str, Any]] = {}
        self.approvals: Dict[int, List[dict[str, Any]]] = {}
        self.next_workflow_id = 1
        self.next_approval_id = 1
    
    def create_workflow(
        self,
        integration_id: int,
        change_type: str,
        change_description: str,
        required_approvers: List[int],
        metadata: Dict[str, Any] = None
    ) -> dict[str, Any]:
        """
        Create an approval workflow.
        
        Args:
            integration_id: Integration ID
            change_type: Type of change (config_update, connector_change, etc.)
            change_description: Description of the change
            required_approvers: List of user IDs who need to approve
            metadata: Additional metadata
            
        Returns:
            Workflow dictionary
        """
        workflow = {
            "id": self.next_workflow_id,
            "integration_id": integration_id,
            "change_type": change_type,
            "change_description": change_description,
            "required_approvers": required_approvers,
            "current_approver_index": 0,
            "status": ApprovalStatus.PENDING,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {}
        }
        
        self.workflows[self.next_workflow_id] = workflow
        self.next_workflow_id += 1
        
        return workflow
    
    def submit_for_approval(self, workflow_id: int) -> dict[str, Any]:
        """
        Submit a workflow for approval.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Updated workflow
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow["status"] = ApprovalStatus.PENDING
        workflow["submitted_at"] = datetime.now(timezone.utc).isoformat()
        workflow["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        return workflow
    
    def approve(
        self,
        workflow_id: int,
        approver_id: int,
        comments: str = ""
    ) -> dict[str, Any]:
        """
        Approve a workflow step.
        
        Args:
            workflow_id: Workflow ID
            approver_id: User ID of approver
            comments: Approval comments
            
        Returns:
            Updated workflow
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        if workflow["status"] != ApprovalStatus.PENDING:
            raise ValueError(f"Workflow is not in pending status")
        
        # Record approval
        approval = {
            "id": self.next_approval_id,
            "workflow_id": workflow_id,
            "approver_id": approver_id,
            "action": "approve",
            "comments": comments,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if workflow_id not in self.approvals:
            self.approvals[workflow_id] = []
        
        self.approvals[workflow_id].append(approval)
        self.next_approval_id += 1
        
        # Move to next approver
        workflow["current_approver_index"] += 1
        
        # Check if all approvers have approved
        if workflow["current_approver_index"] >= len(workflow["required_approvers"]):
            workflow["status"] = ApprovalStatus.APPROVED
            workflow["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        workflow["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        return workflow
    
    def reject(
        self,
        workflow_id: int,
        approver_id: int,
        reason: str
    ) -> dict[str, Any]:
        """
        Reject a workflow.
        
        Args:
            workflow_id: Workflow ID
            approver_id: User ID of rejecter
            reason: Rejection reason
            
        Returns:
            Updated workflow
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        if workflow["status"] != ApprovalStatus.PENDING:
            raise ValueError(f"Workflow is not in pending status")
        
        # Record rejection
        approval = {
            "id": self.next_approval_id,
            "workflow_id": workflow_id,
            "approver_id": approver_id,
            "action": "reject",
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if workflow_id not in self.approvals:
            self.approvals[workflow_id] = []
        
        self.approvals[workflow_id].append(approval)
        self.next_approval_id += 1
        
        # Update workflow status
        workflow["status"] = ApprovalStatus.REJECTED
        workflow["rejected_at"] = datetime.now(timezone.utc).isoformat()
        workflow["rejection_reason"] = reason
        workflow["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        return workflow
    
    def cancel(self, workflow_id: int, user_id: int, reason: str = "") -> dict[str, Any]:
        """
        Cancel a workflow.
        
        Args:
            workflow_id: Workflow ID
            user_id: User ID who cancelled
            reason: Cancellation reason
            
        Returns:
            Updated workflow
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        if workflow["status"] not in [ApprovalStatus.PENDING, ApprovalStatus.APPROVED]:
            raise ValueError(f"Workflow cannot be cancelled in current status")
        
        workflow["status"] = ApprovalStatus.CANCELLED
        workflow["cancelled_at"] = datetime.now(timezone.utc).isoformat()
        workflow["cancelled_by"] = user_id
        workflow["cancellation_reason"] = reason
        workflow["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        return workflow
    
    def get_workflow(self, workflow_id: int) -> Optional[dict[str, Any]]:
        """
        Get workflow by ID.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Workflow dictionary or None
        """
        return self.workflows.get(workflow_id)
    
    def get_approvals(self, workflow_id: int) -> List[dict[str, Any]]:
        """
        Get all approvals for a workflow.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            List of approval records
        """
        return self.approvals.get(workflow_id, [])
    
    def list_workflows(
        self,
        integration_id: int = None,
        status: ApprovalStatus = None,
        limit: int = 100
    ) -> List[dict[str, Any]]:
        """
        List workflows with optional filters.
        
        Args:
            integration_id: Filter by integration ID
            status: Filter by status
            limit: Maximum number of workflows
            
        Returns:
            List of workflow dictionaries
        """
        workflows = list(self.workflows.values())
        
        if integration_id:
            workflows = [w for w in workflows if w.get("integration_id") == integration_id]
        
        if status:
            workflows = [w for w in workflows if w.get("status") == status]
        
        # Sort by created_at descending
        workflows.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return workflows[:limit]
    
    def get_pending_approvals(self, user_id: int) -> List[dict[str, Any]]:
        """
        Get workflows pending approval by a specific user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of pending workflows
        """
        pending = []
        
        for workflow in self.workflows.values():
            if workflow["status"] != ApprovalStatus.PENDING:
                continue
            
            # Check if user is the current approver
            approvers = workflow["required_approvers"]
            current_index = workflow["current_approver_index"]
            
            if current_index < len(approvers) and approvers[current_index] == user_id:
                pending.append(workflow)
        
        return pending
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get approval workflow statistics.
        
        Returns:
            Statistics dictionary
        """
        total = len(self.workflows)
        pending = sum(1 for w in self.workflows.values() if w["status"] == ApprovalStatus.PENDING)
        approved = sum(1 for w in self.workflows.values() if w["status"] == ApprovalStatus.APPROVED)
        rejected = sum(1 for w in self.workflows.values() if w["status"] == ApprovalStatus.REJECTED)
        cancelled = sum(1 for w in self.workflows.values() if w["status"] == ApprovalStatus.CANCELLED)
        
        return {
            "total_workflows": total,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "cancelled": cancelled,
            "total_approvals": sum(len(approvals) for approvals in self.approvals.values())
        }