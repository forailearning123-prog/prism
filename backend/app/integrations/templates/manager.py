"""
Template Manager
Manages integration template lifecycle and customization.
"""

from typing import Any, Optional, Dict, List
from datetime import datetime, timezone
import copy


class TemplateManager:
    """
    Manages integration templates.
    Handles template cloning, customization, and deployment.
    """
    
    def __init__(self, catalog: TemplateCatalog = None):
        """
        Initialize template manager.
        
        Args:
            catalog: Template catalog instance
        """
        from .catalog import TemplateCatalog
        self.catalog = catalog or TemplateCatalog()
        self.custom_templates: Dict[str, dict[str, Any]] = {}
        self.instances: Dict[int, dict[str, Any]] = {}
        self.next_instance_id = 1
    
    def clone_template(self, template_id: str, name: str, description: str = None) -> dict[str, Any]:
        """
        Clone a template to create a custom integration.
        
        Args:
            template_id: Source template ID
            name: Name for the new integration
            description: Description for the new integration
            
        Returns:
            Cloned template configuration
        """
        template = self.catalog.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Deep clone the template
        cloned = copy.deepcopy(template)
        
        # Update with new information
        cloned["id"] = f"custom_{self.next_instance_id}"
        cloned["name"] = name
        cloned["description"] = description or template.get("description", "")
        cloned["source_template_id"] = template_id
        cloned["is_customized"] = True
        cloned["created_at"] = datetime.now(timezone.utc).isoformat()
        cloned["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Store the custom template
        self.custom_templates[cloned["id"]] = cloned
        
        return cloned
    
    def customize_template(
        self,
        instance_id: str,
        mappings: List[dict[str, Any]] = None,
        transformations: List[dict[str, Any]] = None,
        sync_config: dict[str, Any] = None,
        metadata: dict[str, Any] = None
    ) -> dict[str, Any]:
        """
        Customize a cloned template.
        
        Args:
            instance_id: Template instance ID
            mappings: Updated field mappings
            transformations: Updated transformations
            sync_config: Updated sync configuration
            metadata: Additional metadata
            
        Returns:
            Updated template configuration
        """
        template = self.custom_templates.get(instance_id)
        if not template:
            raise ValueError(f"Template instance {instance_id} not found")
        
        # Update fields
        if mappings is not None:
            template["mappings"] = mappings
        if transformations is not None:
            template["transformations"] = transformations
        if sync_config is not None:
            template["sync_config"] = sync_config
        if metadata is not None:
            template["metadata"] = {**template.get("metadata", {}), **metadata}
        
        template["is_customized"] = True
        template["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        return template
    
    def create_instance(self, template_id: str, config: dict[str, Any]) -> dict[str, Any]:
        """
        Create an integration instance from a template.
        
        Args:
            template_id: Template ID (can be from catalog or custom)
            config: Integration configuration
            
        Returns:
            Integration instance
        """
        template = self.catalog.get_template(template_id)
        if not template:
            template = self.custom_templates.get(template_id)
        
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        instance = {
            "id": self.next_instance_id,
            "template_id": template_id,
            "name": config.get("name", template.get("name")),
            "description": config.get("description", template.get("description")),
            "source_connector": config.get("source_connector", template.get("source_connector")),
            "destination_connector": config.get("destination_connector", template.get("destination_connector")),
            "mappings": config.get("mappings", template.get("mappings", [])),
            "transformations": config.get("transformations", template.get("transformations", [])),
            "sync_config": config.get("sync_config", template.get("sync_config", {})),
            "status": "draft",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {**template.get("metadata", {}), **config.get("metadata", {})}
        }
        
        self.instances[self.next_instance_id] = instance
        self.next_instance_id += 1
        
        return instance
    
    def get_instance(self, instance_id: int) -> Optional[dict[str, Any]]:
        """
        Get an integration instance by ID.
        
        Args:
            instance_id: Instance ID
            
        Returns:
            Instance dictionary or None
        """
        return self.instances.get(instance_id)
    
    def update_instance(self, instance_id: int, updates: dict[str, Any]) -> Optional[dict[str, Any]]:
        """
        Update an integration instance.
        
        Args:
            instance_id: Instance ID
            updates: Updates to apply
            
        Returns:
            Updated instance or None
        """
        instance = self.instances.get(instance_id)
        if not instance:
            return None
        
        # Apply updates
        for key, value in updates.items():
            if key in ["id", "created_at"]:
                continue  # Don't update these fields
            instance[key] = value
        
        instance["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        return instance
    
    def delete_instance(self, instance_id: int) -> bool:
        """
        Delete an integration instance.
        
        Args:
            instance_id: Instance ID
            
        Returns:
            True if deleted, False if not found
        """
        if instance_id in self.instances:
            del self.instances[instance_id]
            return True
        return False
    
    def list_instances(
        self,
        template_id: str = None,
        status: str = None,
        limit: int = 100
    ) -> List[dict[str, Any]]:
        """
        List integration instances.
        
        Args:
            template_id: Filter by template ID
            status: Filter by status
            limit: Maximum number of instances
            
        Returns:
            List of instance dictionaries
        """
        instances = list(self.instances.values())
        
        if template_id:
            instances = [i for i in instances if i.get("template_id") == template_id]
        
        if status:
            instances = [i for i in instances if i.get("status") == status]
        
        # Sort by created_at descending
        instances.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return instances[:limit]
    
    def deploy_instance(self, instance_id: int) -> dict[str, Any]:
        """
        Deploy an integration instance.
        
        Args:
            instance_id: Instance ID
            
        Returns:
            Updated instance
        """
        instance = self.instances.get(instance_id)
        if not instance:
            raise ValueError(f"Instance {instance_id} not found")
        
        instance["status"] = "active"
        instance["deployed_at"] = datetime.now(timezone.utc).isoformat()
        instance["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        return instance
    
    def disable_instance(self, instance_id: int) -> dict[str, Any]:
        """
        Disable an integration instance.
        
        Args:
            instance_id: Instance ID
            
        Returns:
            Updated instance
        """
        instance = self.instances.get(instance_id)
        if not instance:
            raise ValueError(f"Instance {instance_id} not found")
        
        instance["status"] = "disabled"
        instance["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        return instance
    
    def get_template_recommendations(self, source: str, destination: str) -> List[dict[str, Any]]:
        """
        Get template recommendations based on source and destination.
        
        Args:
            source: Source system
            destination: Destination system
            
        Returns:
            List of recommended templates
        """
        recommendations = []
        
        for template in self.catalog.templates.values():
            template_source = template.get("source_connector", "").lower()
            template_dest = template.get("destination_connector", "").lower()
            
            # Match if source or destination matches
            if source.lower() in template_source or template_source in source.lower():
                if destination.lower() in template_dest or template_dest in destination.lower():
                    recommendations.append(template)
        
        # Sort by popularity
        recommendations.sort(
            key=lambda x: x.get("metadata", {}).get("popularity", 0),
            reverse=True
        )
        
        return recommendations
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get template manager statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "catalog_templates": len(self.catalog.templates),
            "custom_templates": len(self.custom_templates),
            "total_instances": len(self.instances),
            "instances_by_status": {
                "draft": sum(1 for i in self.instances.values() if i.get("status") == "draft"),
                "active": sum(1 for i in self.instances.values() if i.get("status") == "active"),
                "disabled": sum(1 for i in self.instances.values() if i.get("status") == "disabled")
            }
        }