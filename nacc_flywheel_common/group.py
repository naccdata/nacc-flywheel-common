from typing import List
from flywheel.models.access_level import AccessLevel
from flywheel.models.access_permission import AccessPermission
from flywheel.models.group import Group

def add_group_permission(group: Group, user_id: str, access: AccessLevel) -> None:
    """Adds an access permission to a group."""
    existing_permissions = [
        perm for perm in group.permissions
        if perm.id == user_id
    ]
    if not existing_permissions:
        group.add_permission(AccessPermission(id=user_id, access=access))
        return
    group.update_permission(user_id,
                            AccessPermission(id=None, access=access))
    
def add_group_permissions(*, group: Group, user_ids: List[str], access: AccessLevel) -> None:
    for user_id in user_ids:
        add_group_permission(group, user_id=user_id, access=access)