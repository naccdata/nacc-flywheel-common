"""Defines a study client for managing studies in a flyhweel instance."""

import logging
from flywheel import Client
from typing import List, Literal
from pydantic import AliasGenerator, BaseModel, ConfigDict, Field

from common.admin import AdminClient

log = logging.getLogger(__name__)

def kebab_case(name: str) -> str:
    """Converts the name to kebab case.

    Args:
      name: the name to convert
    Returns:
      the name in kebab case
    """
    return name.lower().replace('_', '-')

class StudyModel(BaseModel):
    """Data model for studies based on the model used in the project-management gear"""
    model_config = ConfigDict(populate_by_name=True,
                              alias_generator=AliasGenerator(alias=kebab_case),
                              extra='forbid')

    name: str = Field(serialization_alias='study')
    study_id: str
    centers: List[str]
    datatypes: List[str]
    mode: Literal['aggregation', 'distribution']
    published: bool = Field(False)
    primary: bool = Field(False)

def study_filename(study: StudyModel) -> str:
    """Creates a canonical file name for study config file.
    
    Args:
      study: the study model
    Returns:
      file name using the study ID
    """
    return f"{study.study_id}-study.yaml"

class StudyClient:
    """Wrapper for FW client to perform study creation and update."""

    def __init__(self, client: Client) -> None:
        self.admin_client = AdminClient(client)
    
    def get_study_file(self, study: StudyModel):
        """Returns the study config file for the study.
        
        Args:
          study: the study
        Returns:
          the file object for the study
        """
        return self.admin_client.get_admin_file(study_filename(study))

    def upload_study_file(self, study: StudyModel) -> None:
        """Uploads the study config file from the study model object.
    
        Must be run before running create_pipelines.
        
        Args:
          study: the study model
        """
        self.admin_client.upload_config_file(
            filename=study_filename(study), 
            data=study.model_dump(by_alias=True, exclude_none=True))

    def create_pipelines(self, study: StudyModel) -> str:
         """Runs the project management gear to create/update the projects for
         the study in Flywheel.
         
         Args:
           study: the study model
        """
         self.upload_study_file(study)
         study_file = self.get_study_file(study)
         if not study_file:
             log.info('study file not available, retry')
             return ''

         return self.admin_client.run_project_management(
              study_file)