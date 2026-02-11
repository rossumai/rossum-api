from __future__ import annotations

from dataclasses import dataclass, field

from rossum_api.models.hook import HookEventAndAction, HookExtensionSource, HookType
from rossum_api.types import JsonDict


@dataclass
class HookTemplate:
    """Hook Template defines a template for creating hooks.

    Attributes
    ----------
    name
        Name of the hook template.
    url
        URL of the hook template.
    id
        ID of the hook template (derived from ``url``, since Rossum API does not send ID).
    type
        Hook type.
    events
        List of events, when the hook should be notified.
    sideload
        List of related objects that should be included in hook request.
    metadata
        Client data.
    config
        Configuration of the hook.
    test
        Input saved for hook testing purposes.
    description
        Hook description text.
    extension_source
        Import source of the extension.
    settings
        Specific settings that will be included in the payload when executing the hook.
    settings_schema
        JSON schema for settings field, specifying the JSON structure of this field.
    secrets_schema
        JSON schema for secrets field, specifying the JSON structure of this field.
    guide
        Description how to use the extension.
    read_more_url
        URL address leading to more info page.
    extension_image_url
        URL address of extension picture.

    References
    ----------
    https://rossum.app/api/docs/#tag/Hook-Template
    """

    name: str
    url: str
    id: int | None = None
    type: HookType = "webhook"
    events: list[HookEventAndAction] = field(default_factory=list)
    sideload: list[str] = field(default_factory=list)
    metadata: JsonDict = field(default_factory=dict)
    config: JsonDict = field(default_factory=dict)
    test: JsonDict = field(default_factory=dict)
    description: str | None = None
    extension_source: HookExtensionSource = "rossum_store"
    settings: JsonDict = field(default_factory=dict)
    settings_schema: JsonDict | None = None
    secrets_schema: JsonDict | None = None
    guide: str | None = None
    read_more_url: str | None = None
    extension_image_url: str | None = None

    def __post_init__(self) -> None:
        if self.id is None:
            self.id = int(self.url.rstrip("/").split("/")[-1])
