"""Defines functions for managing project permissions."""

import logging
from typing import List

from flywheel.models.project import Project
from flywheel.models.roles_role_assignment import RolesRoleAssignment
from flywheel.models.user import User
from flywheel.rest import ApiException

log = logging.getLogger(__name__)


def add_permission(*, project: Project, user: User, role_id: str):
    """Adds user permissions to the project with the given role.

    Args:
      project: the project
      user: the user
      role_id: the ID of the role
    """
    project = project.reload()
    assignments = [
        assignment for assignment in project.permissions if assignment.id == user.id
    ]
    if not assignments:
        try:
            project.add_permission(RolesRoleAssignment(id=user.id, role_ids=[role_id]))
        except ApiException:
            print(f"add permission failed on {project.label} user {user.id}")
        return

    role_ids = assignments[0].role_ids
    if role_id in role_ids:
        return

    role_ids.append(role_id)
    try:
        project.update_permission(
            user.id, RolesRoleAssignment(id=None, role_ids=role_ids)
        )
    except ApiException:
        print(f"update permission failed for {project.label} user {user.id}")


def add_permissions(*, projects: List[Project], users: List[User], role_id: str):
    """Adds permissions with the role ID to to the projects for the users.

    Args:
      projects: the projects
      users: the users
      role_id: the role ID
    """
    for user in users:
        for project in projects:
            add_permission(project=project, user=user, role_id=role_id)
