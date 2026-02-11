from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from rossum_api.models.hook import HookEventAndAction, HookExtensionSource, HookType
from rossum_api.types import JsonDict

InstallAction = Literal["copy", "request_access"]


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
    settings_description
        Contains description for settings.
    store_description
        Description of hook displayed in Rossum store.
    external_url
        External URL to be called (relates to webhook type).
    use_token_owner
        Whether the hook should use token owner.
    install_action
        Whether the hook is added directly via application (copy) or on customer's request
        (request_access).
    token_lifetime_s
        Lifetime number of seconds for rossum_authorization_token (min=0, max=7200).
    order
        Hook templates can be ordered or grouped by this parameter.

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
    settings_description: list[JsonDict] = field(default_factory=list)
    store_description: str | None = None
    external_url: str | None = None
    use_token_owner: bool = False
    install_action: InstallAction = "copy"
    token_lifetime_s: int | None = None
    order: int = 0

    def __post_init__(self) -> None:
        if self.id is None:
            self.id = int(self.url.rstrip("/").split("/")[-1])
