"""Defines AdminClient that supports operations on nacc/project-admin """

from typing import Any, Dict, List, Optional
import yaml

from flywheel import Client, DataView, Group, Project
from flywheel.file_spec import FileSpec

class AdminClient:
    def __init__(self, client: Client) -> None:
        self.client = client
        self.__project_admin: Optional[Project] = None
        self.__role_map = None
        self.__admin_group = 'nacc'
        self.__template_group = 'project-templates'
        self.__metadata = None

    def __get_project_admin(self) -> None:
        self.__project_admin = self.client.lookup(
                f"{self.__admin_group}/project-admin")
    @property
    def project_admin(self) -> Project:
        """Returns the project-admin project"""
        if not self.__project_admin:
            self.__get_project_admin()

        return self.__project_admin
    
    def get_admin_file(self, filename: str):
        """Gets the project level file with the file name in project-admin.
        
        Args:
          filename: the file name
        """
        self.__get_project_admin()

        return [ 
            file for file in self.project_admin.files 
            if file.name == filename].pop()
    
    def read_file(self, filename: str):
        return self.project_admin.read_file(filename)
    
    def upload_config_file(self, filename: str, data: Dict[str, Any]) -> None:
        """Uploads the data to a file with the file name to project-admin"""
        file_spec = FileSpec(
            name=filename,
            contents=yaml.safe_dump(data=data,
                                    allow_unicode=True,
                                    default_flow_style=False),
            content_type='application/yaml'
        )
        self.project_admin.upload_file(file_spec)

    def run_project_management(self, study_file) -> str:
        """Executes the project management gear using the study config file.

        Args:
          study_file: the study config file
        Returns:
          the job id
        """
        return self.run_gear(gear_name='project-management',
            config={
                "dry_run": False,
                "admin_group": self.__admin_group,
                "new_only": False,
                "apikey_path_prefix": "/prod/flywheel/gearbot"
            },
            inputs={
                "project_file": study_file
            }
        )
    
    def run_center_management(self, center_file) -> str:
        """Executes the center management gear using the center config file.
        
        Args:
          center_file: the center config file
        Returns:
          the job ID
        """
        return self.run_gear(gear_name='center-management',
            config={"dry_run": False,
                "admin_group": self.__admin_group,
                "new_only": False,
                "apikey_path_prefix": "/prod/flywheel/gearbot"
            },
            inputs={
                "center_file": center_file
            }
        )
    
    def run_file_curator(self, curator_file, input_form, destination) -> str:
        return self.run_gear(
            gear_name='file-curator',
            config={
                'debug': True
            },
            inputs={
                'curator': curator_file,
                'file-input': input_form
            },
            destination=destination
        )
    
    def get_role_id(self, label: str) -> Optional[str]:
        """Returns the ID of the role with the label.
        
        Args:
          label: the role label
        Returns:
          the role object with the label if one exists. Otherwise, None."""
        if not self.__role_map:
            self.__role_map = {role.label: role for role in self.client.get_all_roles()}

        role = self.__role_map.get(label)
        if not role:
            return None
        
        return role.id
    
    def get_templates(self) -> List[Project]:
        """Returns the template projects"""
        return self.client.projects.find(
            f"parents.group={self.__template_group},label=~.+-template$")
    
    def run_push_template(self, project_label: str) -> str:
        """Executes the push-template gear using the template with the label.
        
        Args:
          project_label: the template project label
        Returns:
          the job ID
        """
        return self.run_gear(gear_name='push-template', 
            config={
                "dry_run": False,
                "template_project": project_label,
                "template_group": self.__template_group
            })

    def push_templates(self) -> List[str]:
        """Executes the push-template gear for all of the instance templates."""
        job_ids = []
        template_projects = self.get_templates()
        template_labels = {project.label for project in template_projects}
        for project_label in template_labels:
            job_ids.append(self.run_push_template(project_label))

        return job_ids

    def get_admin_group(self) -> Group:
        """Gets the admin FW group"""
        return self.client.groups.find_first(f'_id={self.__admin_group}')
    
    def pull_directory(self) -> str:
        """Executes the pull-directory gear.
        
        Returns:
          the job ID
        """
        return self.run_gear(gear_name='pull-directory', 
            config={
                "dry_run": False,
                "user_file": "nacc-directory-users.yaml",
                "parameter_path": "/prod/flywheel/gearbot/naccdirectoryv1"
            }
        )
    
    def run_gear(self, *, gear_name: str,
                   analysis_label: Optional[str] = None,
                   config: Optional[Dict[str, Any]] = None, 
                   inputs: Optional[Dict[str, Any]] = None,
                   destination: Optional[Any] = None) -> str:
        """Executes the named gear with the config and inputs.
        
        Uses project-admin as the destination.

        Args:
          gear_name: the name of the gear
          config: the config dictionary for execution
          inputs: the input dictionary for execution
        Returns:
          the job ID
        """
        gear = self.client.lookup(f"gears/{gear_name}")
        if not config:
            config = {"dry_run": False}
        if not inputs:
            inputs = {}
        if not destination:
            destination = self.project_admin
        if analysis_label:
            return gear.run(
                analysis_label=analysis_label,
                config=config,
                inputs=inputs,
                destination=destination
            )
        return gear.run(
            config=config,
            inputs=inputs,
            destination=destination
        )
    
    def get_metadata_project(self) -> Project:

        if not self.__metadata:
            self.__metadata = self.client.lookup(f"{self.__admin_group}/metadata")

        return self.__metadata
    
    def add_view(self, *, project: Optional[Project]=None, view: DataView) -> str:
        if not project:
            project = self.get_metadata_project()

        return self.client.add_view(project.id, view)


    
