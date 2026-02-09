from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

import dacite

RuleActionType = Literal[
    "show_message",
    "add_automation_blocker",
    "change_status",
    "change_queue",
    "add_label",
    "remove_label",
    "add_remove_label",
    "show_field",
    "hide_field",
    "show_hide_field",
    "add_validation_source",
    "send_email",
    "custom",
]

RuleActionEvent = Literal[
    "validation",
    "annotation_imported",
    "annotation_confirmed",
    "annotation_exported",
]

ShowMessageType = Literal["error", "warning", "info"]

ChangeStatusMethod = Literal["postpone", "export", "delete", "confirm", "reject"]


@dataclass
class ShowMessagePayload:
    """Payload for ``show_message`` rule action.

    Attributes
    ----------
    type
        One of: ``error``, ``warning``, ``info``.
    content
        Message content to be displayed.
    schema_id
        Optional message target field (omit for document scope message).

    References
    ----------
    https://rossum.app/api/docs/#tag/Rule
    """

    type: ShowMessageType
    content: str
    schema_id: str | None = None


@dataclass
class AddAutomationBlockerPayload:
    """Payload for ``add_automation_blocker`` rule action.

    Attributes
    ----------
    content
        Automation blocker content to be displayed.
    schema_id
        Optional automation blocker target field id (omit for document scope automation blocker).

    References
    ----------
    https://rossum.app/api/docs/#tag/Rule
    """

    content: str
    schema_id: str | None = None


@dataclass
class ChangeStatusPayload:
    """Payload for ``change_status`` rule action.

    Attributes
    ----------
    method
        Status change method. One of: ``postpone``, ``export``, ``delete``, ``confirm``, ``reject``.

    References
    ----------
    https://rossum.app/api/docs/#tag/Rule
    """

    method: ChangeStatusMethod


@dataclass
class ChangeQueuePayload:
    """Payload for ``change_queue`` rule action.

    Attributes
    ----------
    queue_id
        ID of the target queue.
    reimport
        Flag that controls whether the annotation will be reimported during the action execution.

    References
    ----------
    https://rossum.app/api/docs/#tag/Rule
    """

    queue_id: int
    reimport: bool | None = None


@dataclass
class LabelsPayload:
    """Payload for ``add_label``, ``remove_label``, and ``add_remove_label`` rule actions.

    Attributes
    ----------
    labels
        URLs of label objects to be linked/unlinked from the processed annotation.

    References
    ----------
    https://rossum.app/api/docs/#tag/Rule
    """

    labels: list[str] = field(default_factory=list)


AddLabelPayload = LabelsPayload
RemoveLabelPayload = LabelsPayload
AddRemoveLabelPayload = LabelsPayload


@dataclass
class SchemaIdsPayload:
    """Payload for ``show_field``, ``hide_field``, and ``show_hide_field`` rule actions.

    Attributes
    ----------
    schema_ids
        Schema field IDs whose ``hidden`` attribute will be set accordingly.

    References
    ----------
    https://rossum.app/api/docs/#tag/Rule
    """

    schema_ids: list[str] = field(default_factory=list)


ShowFieldPayload = SchemaIdsPayload
HideFieldPayload = SchemaIdsPayload
ShowHideFieldPayload = SchemaIdsPayload


@dataclass
class AddValidationSourcePayload:
    """Payload for ``add_validation_source`` rule action.

    Attributes
    ----------
    schema_id
        Schema ID of the datapoint to add the validation source to.

    References
    ----------
    https://rossum.app/api/docs/#tag/Rule
    """

    schema_id: str


@dataclass
class SendEmailPayload:
    """Payload for ``send_email`` rule action.

    If ``email_template`` is defined, the ``to``, ``subject``, ``body``,
    ``cc`` and ``bcc`` attributes are ignored.

    Attributes
    ----------
    email_template
        Email template URL.
    attach_document
        When True, document linked to the annotation will be sent as an attachment.
    to
        List of recipients (used when ``email_template`` is not defined).
    subject
        Subject of the email (used when ``email_template`` is not defined).
    body
        Body of the email (used when ``email_template`` is not defined).
    cc
        List of cc recipients (used when ``email_template`` is not defined).
    bcc
        List of bcc recipients (used when ``email_template`` is not defined).

    References
    ----------
    https://rossum.app/api/docs/#tag/Rule
    """

    email_template: str | None = None
    attach_document: bool = False
    to: list[str] = field(default_factory=list)
    subject: str | None = None
    body: str | None = None
    cc: list[str] = field(default_factory=list)
    bcc: list[str] = field(default_factory=list)


RuleActionPayload = (
    ShowMessagePayload
    | AddAutomationBlockerPayload
    | ChangeStatusPayload
    | ChangeQueuePayload
    | LabelsPayload
    | SchemaIdsPayload
    | AddValidationSourcePayload
    | SendEmailPayload
    | dict[str, Any]
)

_ACTION_TYPE_TO_PAYLOAD: dict[str, type | None] = {
    "show_message": ShowMessagePayload,
    "add_automation_blocker": AddAutomationBlockerPayload,
    "change_status": ChangeStatusPayload,
    "change_queue": ChangeQueuePayload,
    "add_label": LabelsPayload,
    "remove_label": LabelsPayload,
    "add_remove_label": LabelsPayload,
    "show_field": SchemaIdsPayload,
    "hide_field": SchemaIdsPayload,
    "show_hide_field": SchemaIdsPayload,
    "add_validation_source": AddValidationSourcePayload,
    "send_email": SendEmailPayload,
    "custom": None,
}


@dataclass
class RuleAction:
    """Rule action object defines actions to be executed when trigger condition is met.

    Attributes
    ----------
    id
        Rule action ID. Needs to be unique within the Rule's actions.
    enabled
        If False the action is disabled (default: True).
    type
        Type of action. See `Rule actions <https://rossum.app/api/docs/#tag/Rule>`_
        for the list of possible actions.
    payload
        Action payload. Structure depends on the action type.
        See `Rule actions <https://rossum.app/api/docs/#tag/Rule>`_ for details.
    event
        Actions are configured to be executed on a specific event.
        See `Trigger events <https://rossum.app/api/docs/#tag/Using-Triggers/Trigger-Event-Types>`_.

    References
    ----------
    https://rossum.app/api/docs/#tag/Rule
    """

    id: str
    type: RuleActionType
    payload: RuleActionPayload
    event: RuleActionEvent
    enabled: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RuleAction:
        """Create RuleAction from dictionary, resolving the correct payload type."""
        action_type: RuleActionType = data["type"]
        payload_data = data.get("payload", {})

        payload_cls = _ACTION_TYPE_TO_PAYLOAD[action_type]
        payload = (
            dacite.from_dict(payload_cls, payload_data)
            if payload_cls is not None
            else payload_data
        )

        return cls(
            id=data["id"],
            type=data["type"],
            payload=payload,
            event=data["event"],
            enabled=data.get("enabled", True),
        )


@dataclass
class Rule:
    """Rule object represents arbitrary business rules added to schema objects.

    Rules allow you to define custom business logic that is evaluated when specific
    conditions are met. Each rule consists of a trigger condition (TxScript formula)
    and a list of actions to execute when the condition evaluates to True.

    .. warning::
        Rules are currently in beta version and the API may change.
        Talk with a Rossum representative about enabling this feature.

    Notes
    -----
    The trigger condition is a TxScript formula which controls the execution of actions.
    There are two evaluation modes:

    - **Simple mode**: when the condition does not reference any datapoint, or only
      references header fields. Example: ``len(field.document_id) < 10``.
    - **Line-item mode**: when the condition references a line item datapoint (a column
      of a multivalue table). Example: ``field.item_amount > 100.0``.

    In line item mode, the condition is evaluated once for each row of the table.

    Attributes
    ----------
    id
        Rule object ID.
    url
        Rule object URL.
    name
        Name of the rule.
    enabled
        If False the rule is disabled (default: True).
    organization
        URL of the :class:`~rossum_api.models.organization.Organization` the rule belongs to.
    schema
        URL of the :class:`~rossum_api.models.schema.Schema` the rule belongs to.
    trigger_condition
        A condition for triggering the rule's actions.
        This is a formula evaluated by `Rossum TxScript <https://rossum.app/api/docs/#tag/Rossum-Transaction-Scripts>`_.
        Note that trigger condition must evaluate strictly to ``"True"``,
        truthy values are not enough to trigger the execution of actions.
        Wrap your condition with ``bool(your_condition)`` if necessary.
    created_by
        URL of the :class:`~rossum_api.models.user.User` who created the rule.
    created_at
        Timestamp of the rule creation.
    modified_by
        URL of the :class:`~rossum_api.models.user.User` who was the last to modify the rule.
    modified_at
        Timestamp of the latest modification.
    rule_template
        URL of the rule template the rule was created from.
    synchronized_from_template
        Signals whether the rule is automatically updated from the linked template.
    actions
        List of :class:`~rossum_api.models.rule.RuleAction` objects.
        See `Rule actions <https://rossum.app/api/docs/#tag/Rule>`_.

    References
    ----------
    https://rossum.app/api/docs/#tag/Rule
    """

    id: int
    name: str
    enabled: bool
    organization: str
    schema: str | None = None
    trigger_condition: str = "True"
    url: str | None = None
    created_by: str | None = None
    created_at: str | None = None
    modified_by: str | None = None
    modified_at: str | None = None
    rule_template: str | None = None
    synchronized_from_template: bool = False
    actions: list[RuleAction] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Rule:
        """Create Rule from dictionary, deserializing actions with correct payload types."""
        data = data.copy()
        actions_data = data.pop("actions", [])
        data["actions"] = [RuleAction.from_dict(a) for a in actions_data]
        rule: Rule = dacite.from_dict(cls, data)
        return rule
