"""Defines pydantic models that echo the objects created by the pull-directory gear."""
from datetime import datetime
from pydantic import BaseModel
from typing import List, Literal, Optional

from common.user import UserModel


DatatypeNameType = Literal['form', 'dicom', 'enrollment']

class Authorizations(BaseModel):
    """Type class for authorizations."""
    study_id: str
    submit: List[DatatypeNameType]
    audit_data: bool
    approve_data: bool
    view_reports: bool

class PersonName(BaseModel):
    """Type class for a person's name."""
    first_name: str
    last_name: str

class UserEntry(BaseModel):
    """UserEntry model based on UserEntry in the pull-directory gear."""
    name: PersonName
    email: str
    auth_email: str
    active: bool
    registration_date: datetime
    org_name: str
    adcid: int
    authorizations: Authorizations

def create_user_object(firstname: str, lastname: str, email: str, 
                       org_name: str = 'NACC', adcid: int = 0, 
                       submit: Optional[List] = None,
                       study_id: str = 'adrc') -> UserEntry:
    """Creates a user entry object to create a NACC-specific directory.
    
    Will not work as is for non NACC users
    """
    if submit is None:
        submit = ['form', 'enrollment', 'dicom'] if org_name == 'NACC' else []
    
    return UserEntry(
        name=PersonName(first_name=firstname, last_name=lastname),
        email=email,
        auth_email=email,
        active=True,
        registration_date=datetime.today(),
        org_name="NACC",
        adcid=adcid,
        authorizations=Authorizations(
            study_id=study_id,
            submit=submit,
            audit_data=True,
            approve_data=True,
            view_reports=True
        )

    )

    