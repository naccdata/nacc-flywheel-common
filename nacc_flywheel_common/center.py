"""Defines center client to manage centers in the FW instance."""

import logging
from typing import Dict, List, Optional, Set, Tuple

import yaml
from common.admin import AdminClient
from flywheel import Client
from pydantic import AliasChoices, BaseModel, Field, RootModel, field_validator

log = logging.getLogger(__name__)


class CenterInfo(BaseModel):
    """Represents a center with data managed at NACC.

    Attributes:
        adcid (int): The ADC ID of the center.
        name (str): The name of the center.
        group (str): The symbolic ID for the center

        active (bool): Optional, active or inactive status. Defaults to True.
        tags (Tuple[str]): Optional, list of tags for the center
    """

    adcid: int
    name: str
    group: str = Field(
        validation_alias=AliasChoices("center_id", "center-id", "group"),
        serialization_alias="center-id",
    )
    active: Optional[bool] = Field(
        validation_alias=AliasChoices("active", "is-active", "is_active"),
        serialization_alias="is-active",
        default=True,
    )
    tags: Optional[Tuple[str, ...]] = None

    def __repr__(self) -> str:
        return (
            f"Center(group={self.group}, "
            f"name={self.name}, "
            f"adcid={self.adcid}, "
            f"active={self.active}, "
            f"tags={self.tags}"
        )

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, CenterInfo):
            return False
        # compare everything except tags
        return (
            self.adcid == __o.adcid
            and self.group == __o.group
            and self.name == __o.name
            and self.active == __o.active
        )

    @field_validator("tags")
    def set_tags(cls, tags: Tuple[Tuple[str], List[str]]) -> Tuple[str]:
        if not tags:
            return ()
        return tuple(tags)  # type: ignore


class CenterList(RootModel):
    root: List[CenterInfo]

    def __bool__(self) -> bool:
        return bool(self.root)

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item) -> CenterInfo:
        return self.root[item]

    def __len__(self):
        return len(self.root)

    def append(self, center: CenterInfo) -> None:
        """Appends the center to the list."""
        self.root.append(center)


class CenterMapInfo(BaseModel):
    """Represents the center map in nacc/metadata project."""

    centers: Dict[str, CenterInfo]

    def __contains__(self, adcid: int) -> bool:
        return adcid in self.centers

    def __len__(self):
        return len(self.centers)

    def add(self, adcid: int, center_info: CenterInfo) -> None:
        """Adds the center info to the map.

        Args:
            adcid: The ADC ID of the center.
            center_info: The center info object.
        """
        self.centers[adcid] = center_info

    def get(self, adcid: int) -> Optional[CenterInfo]:
        """Gets the center info for the given ADCID.

        Args:
            adcid: The ADC ID of the center.
        Returns:
            The center info for the center. None if no info is found.
        """
        return self.centers.get(adcid, None)

    def group_ids(self, center_ids: Optional[List[int]] = None) -> Set[str]:
        if not center_ids:
            center_ids = self.centers.keys()

        return {
            center.group
            for center in [
                self.centers.get(key) for key in center_ids if key in self.centers
            ]
        }

    def active_group_ids(self, center_ids: Optional[List[int]] = None) -> Set[str]:
        if not center_ids:
            center_ids = self.centers.keys()

        return {
            center.group
            for center in [
                self.centers.get(key) for key in center_ids if key in self.centers
            ]
            if center.active
        }

    @classmethod
    def create(cls, center_list: CenterList) -> "CenterMapInfo":
        """Creates a center map from the center list."""
        return CenterMapInfo(
            centers={center_info.adcid: center_info for center_info in center_list}
        )

    @property
    def center_list(self) -> CenterList:
        return CenterList(root=list(self.centers.values()))


class CenterClient:
    def __init__(self, client: Client) -> None:
        self.admin_client = AdminClient(client)
        self.__center_filename = "centers.yaml"

    def get_center_list(self) -> CenterList:
        """Loads center list from centers file."""
        centers_yaml = self.admin_client.read_file(self.__center_filename)
        centers = yaml.safe_load(centers_yaml)
        return CenterList.model_validate(centers)

    def upload_center_list(self, center_list: CenterList) -> None:
        """Uploads the center list."""
        self.admin_client.upload_config_file(
            filename=self.__center_filename,
            data=center_list.model_dump(by_alias=True, exclude_none=True),
        )

    def get_center_file(self):
        """Gets the center file object in project-admin.

        Uses the default name 'centers.yaml'

        Returns:
          the center file object
        """
        return self.admin_client.get_admin_file(self.__center_filename)

    def create_centers(self) -> str:
        """Runs the center management gear to create/update the center groups
        and permissions.

        Returns:
          the job ID
        """
        return self.admin_client.run_center_management(self.get_center_file())

    def get_center_info(self) -> CenterMapInfo:
        """Returns the center info from the metadata project.

        Note this may be independent of the centers file if the center
        management gear has not be run since the last upload.
        """
        metadata = self.admin_client.get_metadata_project()
        metadata = metadata.reload()

        return CenterMapInfo.model_validate(metadata.info)


class CenterInfoRepository:
    """Manages the list of centers in the project-admin/centers.yaml file."""

    def __init__(self, client: Client):
        self.__center_client = CenterClient(client)
        self.__center_map: Optional[CenterMapInfo] = None

    def __get_center_map(self) -> None:
        """Sets the center map from the centers file."""
        center_list = self.__center_client.get_center_list()
        self.__center_map = CenterMapInfo.create(center_list)

    def add(self, center_list: CenterList) -> None:
        """Adds the list of centers to the centers file.

        Args:
          center_list: the list of center info to add
        """
        self.__get_center_map()

        for center_info in center_list:
            if center_info.adcid in self.__center_map:
                log.warning("center with adcid %s exists", center_info.adcid)
                continue

            self.__center_map.add(adcid=center_info.adcid, center_info=center_info)

        self.__center_client.upload_center_list(self.__center_map.center_list)
