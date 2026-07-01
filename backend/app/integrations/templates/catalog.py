"""
Template Catalog
Pre-built integration templates for common scenarios.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone


class TemplateCatalog:
    """
    Catalog of pre-built integration templates.
    Provides ready-to-use integration patterns.
    """
    
    def __init__(self):
        """Initialize template catalog."""
        self.templates: Dict[str, dict[str, Any]] = {}
        self._load_default_templates()
    
    def _load_default_templates(self) -> None:
        """Load default integration templates."""
        # Salesforce to Data Warehouse
        self.templates["salesforce_to_data_warehouse"] = {
            "id": "salesforce_to_data_warehouse",
            "name": "Salesforce to Data Warehouse",
            "description": "Sync Salesforce data to a data warehouse for analytics",
            "category": "CRM",
            "source_connector": "salesforce",
            "destination_connector": "snowflake",
            "mappings": [
                {"source_field": "Id", "destination_field": "customer_id", "transformation_type": "field_mapping"},
                {"source_field": "Name", "destination_field": "customer_name", "transformation_type": "field_mapping"},
                {"source_field": "Email", "destination_field": "email", "transformation_type": "field_mapping"},
                {"source_field": "CreatedDate", "destination_field": "created_at", "transformation_type": "conversion", "transformation_config": {"target_type": "date"}},
                {"source_field": "AnnualRevenue", "destination_field": "annual_revenue", "transformation_type": "conversion", "transformation_config": {"target_type": "number"}}
            ],
            "transformations": [
                {"type": "normalization", "field": "email", "config": {"type": "lowercase"}},
                {"type": "validation", "field": "email", "config": {"rules": {"pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"}}}
            ],
            "sync_config": {
                "sync_type": "incremental",
                "cursor_field": "SystemModstamp",
                "schedule": "0 */6 * * *"  # Every 6 hours
            },
            "metadata": {
                "popularity": 95,
                "difficulty": "medium",
                "estimated_setup_time": "30 minutes"
            }
        }
        
        # Workday to HR Analytics
        self.templates["workday_to_hr_analytics"] = {
            "id": "workday_to_hr_analytics",
            "name": "Workday to HR Analytics",
            "description": "Sync HR data from Workday to analytics platform",
            "category": "HR",
            "source_connector": "workday",
            "destination_connector": "bigquery",
            "mappings": [
                {"source_field": "Employee_ID", "destination_field": "employee_id", "transformation_type": "field_mapping"},
                {"source_field": "First_Name", "destination_field": "first_name", "transformation_type": "field_mapping"},
                {"source_field": "Last_Name", "destination_field": "last_name", "transformation_type": "field_mapping"},
                {"source_field": "Email", "destination_field": "email", "transformation_type": "field_mapping"},
                {"source_field": "Department", "destination_field": "department", "transformation_type": "field_mapping"},
                {"source_field": "Job_Title", "destination_field": "job_title", "transformation_type": "field_mapping"},
                {"source_field": "Hire_Date", "destination_field": "hire_date", "transformation_type": "conversion", "transformation_config": {"target_type": "date"}},
                {"source_field": "Salary", "destination_field": "salary", "transformation_type": "conversion", "transformation_config": {"target_type": "number"}}
            ],
            "transformations": [
                {"type": "calculated", "field": "full_name", "config": {"expression": "{First_Name} + ' ' + {Last_Name}"}},
                {"type": "lookup", "field": "department_id", "config": {"source_field": "Department", "lookup_table": {"Engineering": "ENG", "Sales": "SAL", "Marketing": "MKT", "HR": "HR"}}}
            ],
            "sync_config": {
                "sync_type": "incremental",
                "cursor_field": "Last_Updated",
                "schedule": "0 2 * * *"  # Daily at 2 AM
            },
            "metadata": {
                "popularity": 88,
                "difficulty": "medium",
                "estimated_setup_time": "45 minutes"
            }
        }
        
        # SAP to Finance Dashboard
        self.templates["sap_to_finance_dashboard"] = {
            "id": "sap_to_finance_dashboard",
            "name": "SAP to Finance Dashboard",
            "description": "Sync financial data from SAP to dashboard",
            "category": "ERP",
            "source_connector": "sap",
            "destination_connector": "powerbi",
            "mappings": [
                {"source_field": "BUKRS", "destination_field": "company_code", "transformation_type": "field_mapping"},
                {"source_field": "WAERS", "destination_field": "currency", "transformation_type": "field_mapping"},
                {"source_field": "WRBTR", "destination_field": "amount", "transformation_type": "conversion", "transformation_config": {"target_type": "number"}},
                {"source_field": "BUDAT", "destination_field": "posting_date", "transformation_type": "conversion", "transformation_config": {"target_type": "date"}},
                {"source_field": "LIFNR", "destination_field": "vendor_id", "transformation_type": "field_mapping"}
            ],
            "transformations": [
                {"type": "lookup", "field": "currency_name", "config": {"source_field": "currency", "lookup_table": {"USD": "US Dollar", "EUR": "Euro", "GBP": "British Pound"}}},
                {"type": "calculated", "field": "amount_usd", "config": {"expression": "{amount} * 1.0", "transformation_config": {"target_type": "number"}}}
            ],
            "sync_config": {
                "sync_type": "incremental",
                "cursor_field": "ERDAT",
                "schedule": "0 1 * * *"  # Daily at 1 AM
            },
            "metadata": {
                "popularity": 82,
                "difficulty": "hard",
                "estimated_setup_time": "60 minutes"
            }
        }
        
        # Microsoft Teams Notifications
        self.templates["teams_notifications"] = {
            "id": "teams_notifications",
            "name": "Microsoft Teams Notifications",
            "description": "Send notifications to Microsoft Teams",
            "category": "Productivity",
            "source_connector": "webhook",
            "destination_connector": "microsoft_teams",
            "mappings": [
                {"source_field": "title", "destination_field": "title", "transformation_type": "field_mapping"},
                {"source_field": "message", "destination_field": "text", "transformation_type": "field_mapping"},
                {"source_field": "priority", "destination_field": "priority", "transformation_type": "field_mapping"}
            ],
            "transformations": [
                {"type": "normalization", "field": "priority", "config": {"type": "lowercase"}}
            ],
            "sync_config": {
                "sync_type": "event_driven",
                "events": ["alert.created", "sync.completed", "sync.failed"]
            },
            "metadata": {
                "popularity": 90,
                "difficulty": "easy",
                "estimated_setup_time": "15 minutes"
            }
        }
        
        # Jira to Executive Reporting
        self.templates["jira_to_executive_reporting"] = {
            "id": "jira_to_executive_reporting",
            "name": "Jira to Executive Reporting",
            "description": "Sync Jira issues to executive reporting dashboard",
            "category": "Project Management",
            "source_connector": "jira",
            "destination_connector": "tableau",
            "mappings": [
                {"source_field": "key", "destination_field": "issue_key", "transformation_type": "field_mapping"},
                {"source_field": "summary", "destination_field": "summary", "transformation_type": "field_mapping"},
                {"source_field": "status", "destination_field": "status", "transformation_type": "field_mapping"},
                {"source_field": "priority", "destination_field": "priority", "transformation_type": "field_mapping"},
                {"source_field": "assignee", "destination_field": "assignee", "transformation_type": "field_mapping"},
                {"source_field": "created", "destination_field": "created_date", "transformation_type": "conversion", "transformation_config": {"target_type": "date"}},
                {"source_field": "resolutiondate", "destination_field": "resolved_date", "transformation_type": "conversion", "transformation_config": {"target_type": "date"}}
            ],
            "transformations": [
                {"type": "calculated", "field": "resolution_time_hours", "config": {"expression": "({resolved_date} - {created_date}).total_seconds() / 3600"}},
                {"type": "lookup", "field": "priority_score", "config": {"source_field": "priority", "lookup_table": {"Highest": 4, "High": 3, "Medium": 2, "Low": 1}}}
            ],
            "sync_config": {
                "sync_type": "incremental",
                "cursor_field": "updated",
                "schedule": "0 3 * * *"  # Daily at 3 AM
            },
            "metadata": {
                "popularity": 85,
                "difficulty": "medium",
                "estimated_setup_time": "40 minutes"
            }
        }
    
    def get_template(self, template_id: str) -> Optional[dict[str, Any]]:
        """
        Get a template by ID.
        
        Args:
            template_id: Template identifier
            
        Returns:
            Template dictionary or None
        """
        return self.templates.get(template_id)
    
    def list_templates(
        self,
        category: str = None,
        difficulty: str = None,
        limit: int = 100
    ) -> List[dict[str, Any]]:
        """
        List templates with optional filters.
        
        Args:
            category: Filter by category
            difficulty: Filter by difficulty
            limit: Maximum number of templates
            
        Returns:
            List of template dictionaries
        """
        templates = list(self.templates.values())
        
        if category:
            templates = [t for t in templates if t.get("category", "").lower() == category.lower()]
        
        if difficulty:
            templates = [t for t in templates if t.get("metadata", {}).get("difficulty", "").lower() == difficulty.lower()]
        
        # Sort by popularity
        templates.sort(key=lambda x: x.get("metadata", {}).get("popularity", 0), reverse=True)
        
        return templates[:limit]
    
    def get_categories(self) -> List[str]:
        """
        Get all template categories.
        
        Returns:
            List of category names
        """
        categories = set()
        for template in self.templates.values():
            category = template.get("category")
            if category:
                categories.add(category)
        return sorted(list(categories))
    
    def add_template(self, template: dict[str, Any]) -> None:
        """
        Add a custom template.
        
        Args:
            template: Template configuration
        """
        template_id = template.get("id")
        if not template_id:
            raise ValueError("Template must have an 'id' field")
        
        self.templates[template_id] = template
    
    def remove_template(self, template_id: str) -> bool:
        """
        Remove a template.
        
        Args:
            template_id: Template identifier
            
        Returns:
            True if removed, False if not found
        """
        if template_id in self.templates:
            del self.templates[template_id]
            return True
        return False
    
    def search_templates(self, query: str) -> List[dict[str, Any]]:
        """
        Search templates by name or description.
        
        Args:
            query: Search query
            
        Returns:
            List of matching templates
        """
        query_lower = query.lower()
        results = []
        
        for template in self.templates.values():
            name = template.get("name", "").lower()
            description = template.get("description", "").lower()
            
            if query_lower in name or query_lower in description:
                results.append(template)
        
        return results
    
    def get_popular_templates(self, limit: int = 10) -> List[dict[str, Any]]:
        """
        Get most popular templates.
        
        Args:
            limit: Maximum number of templates
            
        Returns:
            List of popular templates
        """
        templates = list(self.templates.values())
        templates.sort(key=lambda x: x.get("metadata", {}).get("popularity", 0), reverse=True)
        return templates[:limit]
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get template catalog statistics.
        
        Returns:
            Statistics dictionary
        """
        categories = {}
        for template in self.templates.values():
            category = template.get("category", "Uncategorized")
            categories[category] = categories.get(category, 0) + 1
        
        return {
            "total_templates": len(self.templates),
            "categories": categories,
            "by_difficulty": {
                "easy": sum(1 for t in self.templates.values() if t.get("metadata", {}).get("difficulty") == "easy"),
                "medium": sum(1 for t in self.templates.values() if t.get("metadata", {}).get("difficulty") == "medium"),
                "hard": sum(1 for t in self.templates.values() if t.get("metadata", {}).get("difficulty") == "hard")
            }
        }