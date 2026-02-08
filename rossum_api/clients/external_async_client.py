from __future__ import annotations

import asyncio
import json
import warnings
from typing import TYPE_CHECKING, Generic, cast

import aiofiles
import dacite

from rossum_api.clients.internal_async_client import InternalAsyncClient
from rossum_api.domain_logic.annotations import (
    ExportFileFormats,
    is_annotation_imported,
    validate_list_annotations_params,
)
from rossum_api.domain_logic.documents import build_create_document_params
from rossum_api.domain_logic.emails import build_email_import_files
from rossum_api.domain_logic.resources import Resource
from rossum_api.domain_logic.search import build_search_params, validate_search_params
from rossum_api.domain_logic.tasks import is_task_succeeded
from rossum_api.domain_logic.urls import (
    EMAIL_IMPORT_URL,
    build_organization_limits_url,
    build_resource_cancel_url,
    build_resource_confirm_url,
    build_resource_content_operations_url,
    build_resource_content_url,
    build_resource_delete_url,
    build_resource_search_url,
    build_resource_start_url,
    parse_resource_id_from_url,
)
from rossum_api.dtos import Token, UserCredentials
from rossum_api.models import DACITE_CONFIG, deserialize_default
from rossum_api.models.annotation import Annotation
from rossum_api.models.connector import Connector
from rossum_api.models.document import Document
from rossum_api.models.document_relation import DocumentRelation
from rossum_api.models.email import Email
from rossum_api.models.email_template import EmailTemplate
from rossum_api.models.engine import Engine, EngineField
from rossum_api.models.group import Group
from rossum_api.models.hook import Hook, HookRunData
from rossum_api.models.hook_template import HookTemplate
from rossum_api.models.inbox import Inbox
from rossum_api.models.organization import Organization
from rossum_api.models.organization_group import OrganizationGroup
from rossum_api.models.organization_limit import OrganizationLimit
from rossum_api.models.queue import Queue
from rossum_api.models.relation import Relation
from rossum_api.models.rule import Rule
from rossum_api.models.schema import Schema
from rossum_api.models.task import Task
from rossum_api.models.upload import Upload
from rossum_api.models.user import User
from rossum_api.models.workspace import Workspace
from rossum_api.types import (
    AnnotationType,
    ConnectorType,
    DocumentRelationType,
    DocumentType,
    EmailTemplateType,
    EmailType,
    EngineFieldType,
    EngineType,
    GroupType,
    HookRunDataType,
    HookTemplateType,
    HookType,
    InboxType,
    OrganizationGroupType,
    OrganizationType,
    QueueType,
    RelationType,
    RuleType,
    SchemaType,
    TaskType,
    UploadType,
    UserType,
    WorkspaceType,
)
from rossum_api.utils import to_singular

if TYPE_CHECKING:
    import pathlib
    from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
    from typing import Any

    import httpx

    from rossum_api.clients.types import (
        AnnotationOrdering,
        ConnectorOrdering,
        DocumentRelationOrdering,
        EmailTemplateOrdering,
        HookOrdering,
        OrganizationGroupOrdering,
        OrganizationOrdering,
        QueueOrdering,
        RelationOrdering,
        RuleOrdering,
        SchemaOrdering,
        UserOrdering,
        UserRoleOrdering,
        WorkspaceOrdering,
    )
    from rossum_api.models import Deserializer, JsonDict, ResponsePostProcessor
    from rossum_api.types import HttpMethod, RossumApiType, Sideload


class AsyncRossumAPIClient(
    Generic[
        AnnotationType,
        ConnectorType,
        DocumentType,
        DocumentRelationType,
        EmailTemplateType,
        EngineType,
        EngineFieldType,
        GroupType,
        HookType,
        HookRunDataType,
        HookTemplateType,
        InboxType,
        EmailType,
        OrganizationGroupType,
        OrganizationType,
        QueueType,
        RelationType,
        RuleType,
        SchemaType,
        TaskType,
        UploadType,
        UserType,
        WorkspaceType,
    ]
):
    """Asynchronous Rossum API Client.

    Parameters
    ----------
    base_url
        Base API URL including the "/api" and version ("/v1") in the url path. For example
        "https://elis.rossum.ai/api/v1".
    credentials
        User credentials or API token used for authentication.
    deserializer
        Pass a custom deserialization callable if different model classes should be returned.
    timeout
        The timeout configuration (in seconds) to use when sending requests.
    n_retries
        Number of request retries before raising an exception.
    retry_backoff_factor
        Backoff factor for exponential backoff between retries (multiplies the delay).
    retry_max_jitter
        Maximum random jitter (in seconds) added to retry delays.
    max_in_flight_requests
        Maximum number of concurrent requests allowed.
    response_post_processor
        pass a custom response post-processing callable. Applied only if `http_client` is not provided.
    """

    def __init__(
        self,
        base_url: str,
        credentials: UserCredentials | Token,
        *,
        deserializer: Deserializer | None = None,
        timeout: float | None = None,
        n_retries: int = 3,
        retry_backoff_factor: float = 1.0,
        retry_max_jitter: float = 1.0,
        max_in_flight_requests: int = 4,
        response_post_processor: ResponsePostProcessor | None = None,
    ) -> None:
        token = None
        username = None
        password = None
        if isinstance(credentials, UserCredentials):
            username = credentials.username
            password = credentials.password
        else:
            token = credentials.token

        self._http_client = InternalAsyncClient(
            base_url,
            username=username,
            password=password,
            token=token,
            timeout=timeout,
            n_retries=n_retries,
            retry_backoff_factor=retry_backoff_factor,
            retry_max_jitter=retry_max_jitter,
            max_in_flight_requests=max_in_flight_requests,
            response_post_processor=response_post_processor,
        )
        self._deserializer: Callable[[Resource, JsonDict], RossumApiType] = (
            deserializer or deserialize_default
        )

    # ##### QUEUE #####
    async def retrieve_queue(self, queue_id: int) -> QueueType:
        """Retrieve a single :class:`~rossum_api.models.queue.Queue` object.

        Parameters
        ----------
        queue_id
            ID of a queue to be retrieved.

        References
        ----------
        https://rossum.app/api/docs/#operation/queues_retrieve

        https://rossum.app/api/docs/#tag/Queue
        """
        queue = await self._http_client.fetch_one(Resource.Queue, queue_id)
        return self._deserializer(Resource.Queue, queue)

    async def list_queues(
        self, ordering: Sequence[QueueOrdering] = (), **filters: Any
    ) -> AsyncIterator[QueueType]:
        """Retrieve all :class:`~rossum_api.models.queue.Queue` objects satisfying the specified filters.

        Parameters
        ----------
        ordering
            List of object names. Their URLs are used for sorting the results
        filters
            id: ID of a :class:`~rossum_api.models.queue.Queue`.

            name: Name of a :class:`~rossum_api.models.queue.Queue`.

            workspace: ID of a :class:`~rossum_api.models.workspace.Workspace`.

            inbox: ID of an :class:`~rossum_api.models.inbox.Inbox`.

            connector: ID of an :class:`~rossum_api.models.connector.Connector`.

            webhooks: IDs of a :class:`~rossum_api.models.hook.Hook`.

            hooks: IDs of a :class:`~rossum_api.models.hook.Hook`.

            locale: :class:`~rossum_api.models.queue.Queue` object locale.

            dedicated_engine: ID of a `dedicated engine <https://rossum.app/api/docs/#tag/Dedicated-Engine>`_

            generic_engine: ID of a `generic engine <https://rossum.app/api/docs/#tag/Generic-Engine>`_

            deleting: Boolean filter - queue is being deleted (``delete_after`` is set)

        References
        ----------
        https://rossum.app/api/docs/#operation/queues_list

        https://rossum.app/api/docs/#tag/Queue
        """
        async for q in self._http_client.fetch_all(Resource.Queue, ordering, **filters):
            yield self._deserializer(Resource.Queue, q)

    async def create_new_queue(self, data: dict[str, Any]) -> QueueType:
        """Create a new :class:`~rossum_api.models.queue.Queue` object.

        Parameters
        ----------
        data
            :class:`~rossum_api.models.queue.Queue` object configuration.

        References
        ----------
        https://rossum.app/api/docs/#operation/queues_create

        https://rossum.app/api/docs/#tag/Queue
        """
        queue = await self._http_client.create(Resource.Queue, data)
        return self._deserializer(Resource.Queue, queue)

    async def delete_queue(self, queue_id: int) -> None:
        """Delete :class:`~rossum_api.models.queue.Queue` object.

        Parameters
        ----------
        queue_id
            ID of a queue to be deleted.

        Notes
        -----
        By default, the deletion will start after 24 hours.


        .. warning::
            It also deletes all the related objects. Please note that while the queue
            and related objects are being deleted the API may return inconsistent results.
            We strongly discourage from any interaction with the queue after being scheduled for deletion.

        References
        ----------
        https://rossum.app/api/docs/#operation/queues_delete

        https://rossum.app/api/docs/#tag/Queue
        """
        return await self._http_client.delete(Resource.Queue, queue_id)

    async def import_document(
        self,
        queue_id: int,
        files: Sequence[tuple[str | pathlib.Path, str]],
        values: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[int]:
        """https://rossum.app/api/docs/#tag/Import-and-Export/Upload-API.

        Deprecated now, consider upload_document.

        Parameters
        ----------
        queue_id
            ID of the queue to upload the files to
        files
            2-tuple containing current filepath and name to be used by Elis for the uploaded file
        metadata
            metadata will be set to newly created annotation object
        values
            may be used to initialize datapoint values by setting the value of rir_field_names in the schema

        Returns
        -------
        annotation_ids
            list of IDs of created annotations, respects the order of `files` argument
        """
        warnings.warn(
            "`import_document` is deprecated and will be removed. Please use `upload_document` instead.",
            DeprecationWarning,
            stacklevel=2,  # point to the users' code
        )
        tasks = [
            asyncio.create_task(self._upload(file, queue_id, filename, values, metadata))
            for file, filename in files
        ]

        return await asyncio.gather(*tasks)

    async def _upload(
        self,
        file: str | pathlib.Path,
        queue_id: int,
        filename: str,
        values: dict[str, Any] | None,
        metadata: dict[str, Any] | None,
    ) -> int:
        """A helper method used for the import document endpoint.

        This does not create an Upload object.
        """  # noqa: D401
        async with aiofiles.open(file, "rb") as fp:
            results = await self._http_client.upload(
                Resource.Queue, queue_id, fp, filename, values, metadata
            )
            (result,) = results["results"]  # We're uploading 1 file in 1 request, we can unpack
            return parse_resource_id_from_url(result["annotation"])

    # ##### UPLOAD #####
    async def upload_document(
        self,
        queue_id: int,
        files: Sequence[tuple[str | pathlib.Path, str]],
        values: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[TaskType]:
        """https://rossum.app/api/docs/#operation/uploads_create.

        Parameters
        ----------
        queue_id
            ID of the queue to upload the files to
        files
            2-tuple containing current filepath and name to be used by Elis for the uploaded file
        metadata
            metadata will be set to newly created annotation object
        values
            may be used to initialize datapoint values by setting the value of rir_field_names in the schema

        Returns
        -------
        task_responses
            list of Task object responses, respects the order of `files` argument
            Tasks can be polled using poll_task and if succeeded, will contain a
            link to an Upload object that contains info on uploaded documents/annotations
        """
        tasks: list[Awaitable[TaskType]] = [
            asyncio.create_task(self._create_upload(file, queue_id, filename, values, metadata))
            for file, filename in files
        ]

        return list(await asyncio.gather(*tasks))

    async def _create_upload(
        self,
        file: str | pathlib.Path,
        queue_id: int,
        filename: str,
        values: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TaskType:
        """Helper method that uploads the files and gets back Task response for each.

        A successful Task will create an Upload object.
        """  # noqa: D401
        async with aiofiles.open(file, "rb") as fp:
            url = f"uploads?queue={queue_id}"
            files = {"content": (filename, await fp.read(), "application/octet-stream")}

            if values is not None:
                files["values"] = ("", json.dumps(values).encode("utf-8"), "application/json")
            if metadata is not None:
                files["metadata"] = ("", json.dumps(metadata).encode("utf-8"), "application/json")

            task_url = await self.request_json("POST", url, files=files)
            task_id = parse_resource_id_from_url(task_url["url"])

            return await self.retrieve_task(task_id)

    async def retrieve_upload(self, upload_id: int) -> UploadType:
        """Retrieve `rossum_api.models.upload.Upload` object.

        Parameters
        ----------
        upload_id
            ID of an upload to be retrieved.

        References
        ----------
        https://rossum.app/api/docs/#operation/uploads_retrieve

        https://rossum.app/api/docs/#tag/Upload
        """
        upload = await self._http_client.fetch_one(Resource.Upload, upload_id)
        return self._deserializer(Resource.Upload, upload)

    async def export_annotations_to_json(
        self, queue_id: int, **filters: Any
    ) -> AsyncIterator[AnnotationType]:
        """Export annotations from the queue to JSON.

        Notes
        -----
        JSON export is paginated and returns the result in a way similar to other list_all methods.

        Parameters
        ----------
        queue_id
            ID of a queue annotions should be exported from.
        filters
            id
                Id of annotation to be exported, multiple ids may be separated by a comma.
            status
                :class:`~rossum_api.models.annotation.Annotation` status.
            modifier
                :class:`~rossum_api.models.user.User` id.
            arrived_at_before
                ISO 8601 timestamp (e.g. ``arrived_at_before=2019-11-15``).
            arrived_at_after
                ISO 8601 timestamp (e.g. ``arrived_at_after=2019-11-14``).
            exported_at_after
                ISO 8601 timestamp (e.g. ``exported_at_after=2019-11-14 12:00:00``).
            export_failed_at_before
                ISO 8601 timestamp (e.g. ``export_failed_at_before=2019-11-14 22:00:00``).
            export_failed_at_after
                ISO 8601 timestamp (e.g. ``export_failed_at_after=2019-11-14 12:00:00``).
            page_size
                Number of the documents to be exported.
                To be used together with ``page`` attribute. See `pagination <https://rossum.app/api/docs/#tag/Overview/Pagination>`_
            page
                Number of a page to be exported when using pagination.
                Useful for exports of large amounts of data.
                To be used together with the ``page_size`` attribute.

        Notes
        -----
            When the search filter is used, results are limited to 10 000.
            We suggest narrowing down the search query if there are this many results.

        References
        ----------
        https://rossum.app/api/docs/#operation/queues_export
        """
        async for chunk in self._http_client.export(Resource.Queue, queue_id, "json", **filters):
            # JSON export can be translated directly to Annotation object
            yield self._deserializer(Resource.Annotation, cast("dict", chunk))

    async def export_annotations_to_file(
        self, queue_id: int, export_format: ExportFileFormats, **filters: Any
    ) -> AsyncIterator[bytes]:
        """Export annotations from the queue to a desired export format.

        Notes
        -----
        JSON export is paginated and returns the result in a way similar to other list_all methods.

        Parameters
        ----------
        queue_id
            ID of a queue annotions should be exported from.
        export_format
            Target export format.
        filters
            id
                Id of annotation to be exported, multiple ids may be separated by a comma.
            status
                :class:`~rossum_api.models.annotation.Annotation` status.
            modifier
                :class:`~rossum_api.models.user.User` id.
            arrived_at_before
                ISO 8601 timestamp (e.g. ``arrived_at_before=2019-11-15``).
            arrived_at_after
                ISO 8601 timestamp (e.g. ``arrived_at_after=2019-11-14``).
            exported_at_after
                ISO 8601 timestamp (e.g. ``exported_at_after=2019-11-14 12:00:00``).
            export_failed_at_before
                ISO 8601 timestamp (e.g. ``export_failed_at_before=2019-11-14 22:00:00``).
            export_failed_at_after
                ISO 8601 timestamp (e.g. ``export_failed_at_after=2019-11-14 12:00:00``).
            page_size
                Number of the documents to be exported.
                To be used together with ``page`` attribute. See `pagination <https://rossum.app/api/docs/#tag/Overview/Pagination>`_
            page
                Number of a page to be exported when using pagination.
                Useful for exports of large amounts of data.
                To be used together with the ``page_size`` attribute.

        Notes
        -----
            When the search filter is used, results are limited to 10 000.
            We suggest narrowing down the search query if there are this many results.

        References
        ----------
        https://rossum.app/api/docs/#operation/queues_export
        """
        async for chunk in self._http_client.export(
            Resource.Queue, queue_id, export_format.value, **filters
        ):
            yield cast("bytes", chunk)

    # ##### ORGANIZATIONS #####
    async def list_organizations(
        self, ordering: Sequence[OrganizationOrdering] = (), **filters: Any
    ) -> AsyncIterator[OrganizationType]:
        """Retrieve all organization objects satisfying the specified filters.

        Parameters
        ----------
        ordering
            List of object names. Their IDs are used for sorting the results
        filters
            id: ID of a :class:`~rossum_api.models.organization.Organization`

            name: Name of a :class:`~rossum_api.models.organization.Organization`

        References
        ----------
        https://rossum.app/api/docs/#operation/organizations_list
        """
        async for o in self._http_client.fetch_all(Resource.Organization, ordering, **filters):
            yield self._deserializer(Resource.Organization, o)

    async def retrieve_organization(self, org_id: int) -> OrganizationType:
        """Retrieve a single :class:`~rossum_api.models.organization.Qrganization` object.

        Parameters
        ----------
        org_id
            ID of an organization to be retrieved.

        References
        ----------
        https://rossum.app/api/docs/#operation/organizations_retrieve
        """
        organization = await self._http_client.fetch_one(Resource.Organization, org_id)
        return self._deserializer(Resource.Organization, organization)

    async def retrieve_own_organization(self) -> OrganizationType:
        """Retrieve organization of currently logged in user."""
        user: dict[Any, Any] = await self._http_client.fetch_one(Resource.Auth, "user")
        organization_id = parse_resource_id_from_url(user["organization"])
        return await self.retrieve_organization(organization_id)

    async def retrieve_organization_limit(self, org_id: int) -> OrganizationLimit:
        """Retrieve limits for a given organization.

        Parameters
        ----------
        org_id
            ID of an organization whose limits are to be retrieved.

        References
        ----------
        https://rossum.app/api/docs/#operation/organizations_limits
        """
        url = build_organization_limits_url(org_id)
        response = await self._http_client.request_json("GET", url)
        result: OrganizationLimit = dacite.from_dict(
            OrganizationLimit, response, config=DACITE_CONFIG
        )
        return result

    # ##### ORGANIZATION GROUPS #####
    async def list_organization_groups(
        self, ordering: Sequence[OrganizationGroupOrdering] = (), **filters: Any
    ) -> AsyncIterator[OrganizationGroupType]:
        """Retrieve all organization group objects satisfying the specified filters.

        Parameters
        ----------
        ordering
            List of object names. Their IDs are used for sorting the results
        filters
            id: ID of a :class:`~rossum_api.models.organization_group.OrganizationGroup`

            name: Name of a :class:`~rossum_api.models.organization_group.OrganizationGroup`

        References
        ----------
        https://rossum.app/api/docs/#tag/Organization-Group/operation/organization_groups_list
        """
        async for og in self._http_client.fetch_all(
            Resource.OrganizationGroup, ordering, **filters
        ):
            yield self._deserializer(Resource.OrganizationGroup, og)

    async def retrieve_organization_group(self, org_group_id: int) -> OrganizationGroupType:
        """Retrieve a single :class:`~rossum_api.models.organization_group.OrganizationGroup` object.

        Parameters
        ----------
        org_group_id
            ID of an organization group to be retrieved.

        References
        ----------
        https://rossum.app/api/docs/#tag/Organization-Group/operation/organization_groups_retrieve
        """
        org_group = await self._http_client.fetch_one(Resource.OrganizationGroup, org_group_id)
        return self._deserializer(Resource.OrganizationGroup, org_group)

    # ##### SCHEMAS #####
    async def list_schemas(
        self, ordering: Sequence[SchemaOrdering] = (), **filters: Any
    ) -> AsyncIterator[SchemaType]:
        """Retrieve all :class:`~rossum_api.models.schema.Schema` objects satisfying the specified filters.

        Parameters
        ----------
        ordering
            List of object names. Their URLs are used for sorting the results
        filters
            id: ID of a :class:`~rossum_api.models.schema.Schema`

            name: Name of a :class:`~rossum_api.models.schema.Schema`

            queue: ID of a :class:`~rossum_api.models.queue.Queue`

        References
        ----------
        https://rossum.app/api/docs/#operation/schemas_list

        https://rossum.app/api/docs/#tag/Schema
        """
        async for s in self._http_client.fetch_all(Resource.Schema, ordering, **filters):
            yield self._deserializer(Resource.Schema, s)

    async def retrieve_schema(self, schema_id: int) -> SchemaType:
        """Retrieve a single :class:`~rossum_api.models.schema.Schema` object.

        Parameters
        ----------
        schema_id
            ID of a schema to be retrieved.

        References
        ----------
        https://rossum.app/api/docs/#operation/schemas_retrieve

        https://rossum.app/api/docs/#tag/Schema
        """
        schema: dict[Any, Any] = await self._http_client.fetch_one(Resource.Schema, schema_id)

        return self._deserializer(Resource.Schema, schema)

    async def create_new_schema(self, data: dict[str, Any]) -> SchemaType:
        """Create a new :class:`~rossum_api.models.schema.Schema` object.

        Parameters
        ----------
        data
            :class:`~rossum_api.models.schema.Schema` object configuration.

        References
        ----------
        https://rossum.app/api/docs/#operation/schemas_create

        https://rossum.app/api/docs/#tag/Schema
        """
        schema = await self._http_client.create(Resource.Schema, data)

        return self._deserializer(Resource.Schema, schema)

    async def delete_schema(self, schema_id: int) -> None:
        """Delete :class:`~rossum_api.models.schema.Schema` object.

        Parameters
        ----------
        schema_id
            ID of a schema to be deleted.


        .. warning::
            In case the schema is linked to some objects, like queue or annotation, the deletion
            is not possible and the request will fail with 409 status code.

        References
        ----------
        https://rossum.app/api/docs/#operation/schemas_delete
        """
        return await self._http_client.delete(Resource.Schema, schema_id)

    # ##### USERS #####
    async def list_users(
        self, ordering: Sequence[UserOrdering] = (), **filters: Any
    ) -> AsyncIterator[UserType]:
        """Retrieve all :class:`~rossum_api.models.user.User` objects satisfying the specified filters.

        Parameters
        ----------
        ordering
            List of object names. Their URLs are used for sorting the results
        filters
            id: ID of a :class:`~rossum_api.models.user.User`

            organization: ID of an :class:`~rossum_api.models.organization.Organization`

            username: Username of a :class:`~rossum_api.models.user.User`

            first_name: First name of a :class:`~rossum_api.models.user.User`

            last_name: Last name of a :class:`~rossum_api.models.user.User`

            email: Email address of a :class:`~rossum_api.models.user.User`

            is_active: Boolean filter - whether the :class:`~rossum_api.models.user.User` is active

            last_login: ISO 8601 timestamp filter for last login date

            groups: IDs of :class:`~rossum_api.models.group.Group` objects

            queue: ID of a :class:`~rossum_api.models.queue.Queue`

            deleted: Boolean filter - whether the :class:`~rossum_api.models.user.User` is deleted


        References
        ----------
        https://rossum.app/api/docs/#operation/users_list

        https://rossum.app/api/docs/#tag/User
        """
        async for u in self._http_client.fetch_all(Resource.User, ordering, **filters):
            yield self._deserializer(Resource.User, u)

    async def retrieve_user(self, user_id: int) -> UserType:
        """Retrieve a single :class:`~rossum_api.models.user.User` object.

        Parameters
        ----------
        user_id
            ID of a user to be retrieved.

        References
        ----------
        https://rossum.app/api/docs/#operation/users_retrieve

        https://rossum.app/api/docs/#tag/User
        """
        user = await self._http_client.fetch_one(Resource.User, user_id)

        return self._deserializer(Resource.User, user)

    async def create_new_user(self, data: dict[str, Any]) -> UserType:
        """Create a new :class:`~rossum_api.models.user.User` object.

        Parameters
        ----------
        data
            :class:`~rossum_api.models.user.User` object configuration.

        References
        ----------
        https://rossum.app/api/docs/#operation/users_create

        https://rossum.app/api/docs/#tag/User
        """
        user = await self._http_client.create(Resource.User, data)

        return self._deserializer(Resource.User, user)

    # TODO: specific method in APICLient
    def change_user_password(self, new_password: str) -> dict:  # noqa: D102
        raise NotImplementedError()

    # TODO: specific method in APICLient
    def reset_user_password(self, email: str) -> dict:  # noqa: D102
        raise NotImplementedError()

    # ##### ANNOTATIONS #####
    async def list_annotations(
        self,
        ordering: Sequence[AnnotationOrdering] = (),
        sideloads: Sequence[Sideload] = (),
        content_schema_ids: Sequence[str] = (),
        **filters: Any,
    ) -> AsyncIterator[AnnotationType]:
        """Retrieve all :class:`~rossum_api.models.annotation.Annotation` objects satisfying the specified filters.

        Parameters
        ----------
        ordering
            List of object names. Their URLs are used for sorting the results
        sideloads
            List of additional objects to sideload
        content_schema_ids
            List of content schema IDs
        filters
            status: :class:`~rossum_api.models.annotation.Annotation` status, multiple values may be separated using a comma

            id: List of ids separated by a comma

            modifier: :class:`~rossum_api.models.user.User` id

            confirmed_by: :class:`~rossum_api.models.user.User` id

            deleted_by: :class:`~rossum_api.models.user.User` id

            exported_by: :class:`~rossum_api.models.user.User` id

            purged_by: :class:`~rossum_api.models.user.User` id

            rejected_by: :class:`~rossum_api.models.user.User` id

            assignees: :class:`~rossum_api.models.user.User` id, multiple values may be separated using a comma

            labels: Label id, multiple values may be separated using a comma

            document: :class:`~rossum_api.models.document.Document` id

            queue: List of :class:`~rossum_api.models.queue.Queue` ids separated by a comma

            queue__workspace: List of :class:`~rossum_api.models.workspace.Workspace` ids separated by a comma

            relations__parent: ID of parent annotation defined in related Relation object

            relations__type: Type of Relation that annotation belongs to

            relations__key: Key of Relation that annotation belongs to

            arrived_at_before: ISO 8601 timestamp (e.g. ``arrived_at_before=2019-11-15``)

            arrived_at_after: ISO 8601 timestamp (e.g. ``arrived_at_after=2019-11-14``)

            assigned_at_before: ISO 8601 timestamp (e.g. ``assigned_at_before=2019-11-15``)

            assigned_at_after: ISO 8601 timestamp (e.g. ``assigned_at_after=2019-11-14``)

            confirmed_at_before: ISO 8601 timestamp (e.g. ``confirmed_at_before=2019-11-15``)

            confirmed_at_after: ISO 8601 timestamp (e.g. ``confirmed_at_after=2019-11-14``)

            modified_at_before: ISO 8601 timestamp (e.g. ``modified_at_before=2019-11-15``)

            modified_at_after: ISO 8601 timestamp (e.g. ``modified_at_after=2019-11-14``)

            deleted_at_before: ISO 8601 timestamp (e.g. ``deleted_at_before=2019-11-15``)

            deleted_at_after: ISO 8601 timestamp (e.g. ``deleted_at_after=2019-11-14``)

            exported_at_before: ISO 8601 timestamp (e.g. ``exported_at_before=2019-11-14 22:00:00``)

            exported_at_after: ISO 8601 timestamp (e.g. ``exported_at_after=2019-11-14 12:00:00``)

            export_failed_at_before: ISO 8601 timestamp (e.g. ``export_failed_at_before=2019-11-14 22:00:00``)

            export_failed_at_after: ISO 8601 timestamp (e.g. ``export_failed_at_after=2019-11-14 12:00:00``)

            purged_at_before: ISO 8601 timestamp (e.g. ``purged_at_before=2019-11-15``)

            purged_at_after: ISO 8601 timestamp (e.g. ``purged_at_after=2019-11-14``)

            rejected_at_before: ISO 8601 timestamp (e.g. ``rejected_at_before=2019-11-15``)

            rejected_at_after: ISO 8601 timestamp (e.g. ``rejected_at_after=2019-11-14``)

            restricted_access: Boolean

            automated: Boolean

            has_email_thread_with_replies: Boolean (related email thread contains more than one incoming emails)

            has_email_thread_with_new_replies: Boolean (related email thread contains unread incoming email)

            search: String, see Annotation search

        References
        ----------
        https://rossum.app/api/docs/#operation/annotations_list

        https://rossum.app/api/docs/#tag/Annotation
        """
        validate_list_annotations_params(sideloads, content_schema_ids)
        async for a in self._http_client.fetch_all(
            Resource.Annotation, ordering, sideloads, content_schema_ids, **filters
        ):
            yield self._deserializer(Resource.Annotation, a)

    async def search_for_annotations(
        self,
        query: dict | None = None,
        query_string: dict | None = None,
        ordering: Sequence[AnnotationOrdering] = (),
        sideloads: Sequence[Sideload] = (),
        **kwargs: Any,
    ) -> AsyncIterator[AnnotationType]:
        """Search for :class:`~rossum_api.models.annotation.Annotation` objects.

        Parameters
        ----------
        query
            Query dictionary for advanced search
        query_string
            Query string dictionary for text search
        ordering
            List of object names. Their URLs are used for sorting the results
        sideloads
            List of additional objects to sideload
        kwargs
            Additional search parameters

        References
        ----------
        https://rossum.app/api/docs/#operation/annotations_search

        https://rossum.app/api/docs/#tag/Annotation
        """
        validate_search_params(query, query_string)
        search_params = build_search_params(query, query_string)

        async for a in self._http_client.fetch_all_by_url(
            build_resource_search_url(Resource.Annotation),
            ordering,
            sideloads,
            json=search_params,
            method="POST",
            **kwargs,
        ):
            yield self._deserializer(Resource.Annotation, a)

    async def retrieve_annotation(
        self, annotation_id: int, sideloads: Sequence[Sideload] = ()
    ) -> AnnotationType:
        """Retrieve a single :class:`~rossum_api.models.annotation.Annotation` object.

        Parameters
        ----------
        annotation_id
            ID of an annotation to be retrieved.
        sideloads
            List of additional objects to sideload

        References
        ----------
        https://rossum.app/api/docs/#operation/annotations_retrieve

        https://rossum.app/api/docs/#tag/Annotation
        """
        annotation_json = await self._http_client.fetch_one(Resource.Annotation, annotation_id)
        if sideloads:
            await self._sideload(annotation_json, sideloads)
        return self._deserializer(Resource.Annotation, annotation_json)

    async def poll_annotation(
        self,
        annotation_id: int,
        predicate: Callable[[AnnotationType], bool],
        sleep_s: int = 3,
        sideloads: Sequence[Sideload] = (),
    ) -> AnnotationType:
        """Poll on Annotation until predicate is true.

        Sideloading is done only once after the predicate becomes true to avoid spamming the server.
        """
        annotation_json = await self._http_client.fetch_one(Resource.Annotation, annotation_id)
        # Parse early, we want predicate to work with Annotation instances for convenience
        annotation = self._deserializer(Resource.Annotation, annotation_json)

        while not predicate(annotation):
            await asyncio.sleep(sleep_s)
            annotation_json = await self._http_client.fetch_one(Resource.Annotation, annotation_id)
            annotation = self._deserializer(Resource.Annotation, annotation_json)

        if sideloads:
            await self._sideload(annotation_json, sideloads)
        return self._deserializer(Resource.Annotation, annotation_json)

    async def poll_annotation_until_imported(
        self, annotation_id: int, **poll_kwargs: Any
    ) -> AnnotationType:
        """Wait until annotation is imported."""
        return await self.poll_annotation(annotation_id, is_annotation_imported, **poll_kwargs)

    async def poll_task(
        self, task_id: int, predicate: Callable[[TaskType], bool], sleep_s: int = 3
    ) -> TaskType:
        """Poll on Task until predicate is true.

        As with Annotation polling, there is no innate retry limit.
        """
        task = await self.retrieve_task(task_id)

        while not predicate(task):
            await asyncio.sleep(sleep_s)
            task = await self.retrieve_task(task_id)

        return task

    async def poll_task_until_succeeded(self, task_id: int, sleep_s: int = 3) -> TaskType:
        """Poll on Task until it is succeeded."""
        return await self.poll_task(task_id, is_task_succeeded, sleep_s)

    async def retrieve_task(self, task_id: int) -> TaskType:
        """Retrieve a single :class:`~rossum_api.models.task.Task` object.

        Parameters
        ----------
        task_id
            ID of a task to be retrieved.

        References
        ----------
        https://rossum.app/api/docs/#operation/tasks_retrieve

        https://rossum.app/api/docs/#tag/Task
        """
        task = await self._http_client.fetch_one(
            Resource.Task, task_id, request_params={"no_redirect": "True"}
        )

        return self._deserializer(Resource.Task, task)

    async def upload_and_wait_until_imported(
        self, queue_id: int, filepath: str | pathlib.Path, filename: str, **poll_kwargs: Any
    ) -> AnnotationType:
        """Upload a single file and waiting until its annotation is imported in a single call."""
        (annotation_id,) = await self.import_document(queue_id, [(filepath, filename)])
        return await self.poll_annotation_until_imported(annotation_id, **poll_kwargs)

    async def start_annotation(self, annotation_id: int) -> None:
        """Start annotation processing.

        Parameters
        ----------
        annotation_id
            ID of an annotation to be started.

        References
        ----------
        https://rossum.app/api/docs/#operation/annotations_start

        https://rossum.app/api/docs/#tag/Annotation
        """
        await self._http_client.request_json(
            "POST", build_resource_start_url(Resource.Annotation, annotation_id)
        )

    async def update_annotation(self, annotation_id: int, data: dict[str, Any]) -> AnnotationType:
        """Update an :class:`~rossum_api.models.annotation.Annotation` object.

        Parameters
        ----------
        annotation_id
            ID of an annotation to be updated.
        data
            :class:`~rossum_api.models.annotation.Annotation` object update data.

        References
        ----------
        https://rossum.app/api/docs/#operation/annotations_update

        https://rossum.app/api/docs/#tag/Annotation
        """
        annotation = await self._http_client.replace(Resource.Annotation, annotation_id, data)

        return self._deserializer(Resource.Annotation, annotation)

    async def update_part_annotation(
        self, annotation_id: int, data: dict[str, Any]
    ) -> AnnotationType:
        """Update part of an :class:`~rossum_api.models.annotation.Annotation` object.

        Parameters
        ----------
        annotation_id
            ID of an annotation to be updated.
        data
            Partial :class:`~rossum_api.models.annotation.Annotation` object update data.

        References
        ----------
        https://rossum.app/api/docs/#operation/annotations_partial_update

        https://rossum.app/api/docs/#tag/Annotation
        """
        annotation = await self._http_client.update(Resource.Annotation, annotation_id, data)

        return self._deserializer(Resource.Annotation, annotation)

    async def bulk_update_annotation_data(
        self, annotation_id: int, operations: list[dict[str, Any]]
    ) -> None:
        """Bulk update annotation data.

        Parameters
        ----------
        annotation_id
            ID of an annotation to be updated.
        operations
            List of operations to perform on annotation data.

        References
        ----------
        https://rossum.app/api/docs/#operation/annotations_content_operations

        https://rossum.app/api/docs/#tag/Annotation
        """
        await self._http_client.request_json(
            "POST",
            build_resource_content_operations_url(Resource.Annotation, annotation_id),
            json={"operations": operations},
        )

    async def confirm_annotation(self, annotation_id: int) -> None:
        """Confirm annotation.

        Parameters
        ----------
        annotation_id
            ID of an annotation to be confirmed.

        References
        ----------
        https://rossum.app/api/docs/#operation/annotations_confirm

        https://rossum.app/api/docs/#tag/Annotation
        """
        await self._http_client.request_json(
            "POST", build_resource_confirm_url(Resource.Annotation, annotation_id)
        )

    async def create_new_annotation(self, data: dict[str, Any]) -> AnnotationType:
        """Create a new :class:`~rossum_api.models.annotation.Annotation` object.

        Parameters
        ----------
        data
            :class:`~rossum_api.models.annotation.Annotation` object configuration.

        References
        ----------
        https://rossum.app/api/docs/#operation/annotations_create

        https://rossum.app/api/docs/#tag/Annotation
        """
        annotation = await self._http_client.create(Resource.Annotation, data)

        return self._deserializer(Resource.Annotation, annotation)

    async def delete_annotation(self, annotation_id: int) -> None:
        """Delete :class:`~rossum_api.models.annotation.Annotation` object.

        Parameters
        ----------
        annotation_id
            ID of an annotation to be deleted.

        References
        ----------
        https://rossum.app/api/docs/#operation/annotations_delete_status

        https://rossum.app/api/docs/#tag/Annotation
        """
        await self._http_client.request(
            "POST", url=build_resource_delete_url(Resource.Annotation, annotation_id)
        )

    async def cancel_annotation(self, annotation_id: int) -> None:
        """Cancel :class:`~rossum_api.models.annotation.Annotation` object.

        Parameters
        ----------
        annotation_id
            ID of an annotation to be cancelled.

        References
        ----------
        https://rossum.app/api/docs/#operation/annotations_cancel

        https://rossum.app/api/docs/#tag/Annotation
        """
        await self._http_client.request(
            "POST", url=build_resource_cancel_url(Resource.Annotation, annotation_id)
        )

    # ##### DOCUMENTS #####
    async def retrieve_document(self, document_id: int) -> DocumentType:
        """Retrieve a single :class:`~rossum_api.models.document.Document` object.

        Parameters
        ----------
        document_id
            ID of a document to be retrieved.

        References
        ----------
        https://rossum.app/api/docs/#operation/documents_retrieve

        https://rossum.app/api/docs/#tag/Document
        """
        document: dict[Any, Any] = await self._http_client.fetch_one(
            Resource.Document, document_id
        )

        return self._deserializer(Resource.Document, document)

    async def retrieve_document_content(self, document_id: int) -> bytes:
        """Retrieve :class:`~rossum_api.models.document_content.DocumentDocuntent` object.

        Parameters
        ----------
        document_id
            ID of a document to retrieve content for.

        Returns
        -------
        bytes
            Raw document content.

        References
        ----------
        https://rossum.app/api/docs/#operation/documents_content_retrieve

        https://rossum.app/api/docs/#tag/Document
        """
        document_content = await self._http_client.request(
            "GET", url=build_resource_content_url(Resource.Document, document_id)
        )
        return document_content.content  # type: ignore[no-any-return]

    async def create_new_document(
        self,
        file_name: str,
        file_data: bytes,
        metadata: dict[str, Any] | None = None,
        parent: str | None = None,
    ) -> DocumentType:
        """Create a new :class:`~rossum_api.models.document.Document` object.

        Parameters
        ----------
        file_name
            Name of the file to be created.
        file_data
            Raw file data.
        metadata
            Optional metadata for the document.
        parent
            Optional parent document URL.

        References
        ----------
        https://rossum.app/api/docs/#operation/documents_create

        https://rossum.app/api/docs/#tag/Document
        """
        files = build_create_document_params(file_name, file_data, metadata, parent)

        document = await self._http_client.request_json(
            "POST", url=Resource.Document.value, files=files
        )

        return self._deserializer(Resource.Document, document)

    # ##### DOCUMENT RELATIONS #####
    async def list_document_relations(
        self, ordering: Sequence[DocumentRelationOrdering] = (), **filters: Any
    ) -> AsyncIterator[DocumentRelationType]:
        """Retrieve all :class:`~rossum_api.models.document_relation.DocumentRelation` objects satisfying the specified filters.

        Parameters
        ----------
        ordering
            List of object names. Their URLs are used for sorting the results
        filters
            id: ID of :class:`~rossum_api.models.document_relation.DocumentRelation`.

            type: Relation type.

            annotation: ID of :class:`~rossum_api.models.annotation.Annotation`.

            key: Document relation key

            documents: ID of related :class:`~rossum_api.models.document.Document`.

        References
        ----------
        https://rossum.app/api/docs/#operation/document_relations_list

        https://rossum.app/api/docs/#tag/Document-Relation
        """
        async for dr in self._http_client.fetch_all(
            Resource.DocumentRelation, ordering, **filters
        ):
            yield self._deserializer(Resource.DocumentRelation, dr)

    async def retrieve_document_relation(self, document_relation_id: int) -> DocumentRelationType:
        """Retrieve a single :class:`~rossum_api.models.document_relation.DocumentRelation` object.

        Parameters
        ----------
        document_relation_id
            ID of a document relation to be retrieved.

        References
        ----------
        https://rossum.app/api/docs/#operation/document_relations_retrieve

        https://rossum.app/api/docs/#tag/Document-Relation
        """
        document_relation = await self._http_client.fetch_one(
            Resource.DocumentRelation, document_relation_id
        )

        return self._deserializer(Resource.DocumentRelation, document_relation)

    async def create_new_document_relation(self, data: dict[str, Any]) -> DocumentRelationType:
        """Create a new :class:`~rossum_api.models.document_relation.DocumentRelation` object.

        Parameters
        ----------
        data
            :class:`~rossum_api.models.document_relation.DocumentRelation` object configuration.

        References
        ----------
        https://rossum.app/api/docs/#operation/document_relations_create

        https://rossum.app/api/docs/#tag/Document-Relation
        """
        document_relation = await self._http_client.create(Resource.DocumentRelation, data)

        return self._deserializer(Resource.DocumentRelation, document_relation)

    async def update_document_relation(
        self, document_relation_id: int, data: dict[str, Any]
    ) -> DocumentRelationType:
        """Update a :class:`~rossum_api.models.document_relation.DocumentRelation` object.

        Parameters
        ----------
        document_relation_id
            ID of a document relation to be updated.
        data
            :class:`~rossum_api.models.document_relation.DocumentRelation` object configuration.

        References
        ----------
        https://rossum.app/api/docs/#operation/document_relations_update

        https://rossum.app/api/docs/#tag/Document-Relation
        """
        document_relation = await self._http_client.replace(
            Resource.DocumentRelation, document_relation_id, data
        )

        return self._deserializer(Resource.DocumentRelation, document_relation)

    async def update_part_document_relation(
        self, document_relation_id: int, data: dict[str, Any]
    ) -> DocumentRelationType:
        """Update part of a :class:`~rossum_api.models.document_relation.DocumentRelation` object.

        Parameters
        ----------
        document_relation_id
            ID of a document relation to be updated.
        data
            :class:`~rossum_api.models.document_relation.DocumentRelation` object partial configuration.

        References
        ----------
        https://rossum.app/api/docs/#operation/document_relations_partial_update

        https://rossum.app/api/docs/#tag/Document-Relation
        """
        document_relation = await self._http_client.update(
            Resource.DocumentRelation, document_relation_id, data
        )

        return self._deserializer(Resource.DocumentRelation, document_relation)

    async def delete_document_relation(self, document_relation_id: int) -> None:
        """Delete a :class:`~rossum_api.models.document_relation.DocumentRelation` object.

        Parameters
        ----------
        document_relation_id
            ID of a document relation to be deleted.

        References
        ----------
        https://rossum.app/api/docs/#operation/document_relations_delete

        https://rossum.app/api/docs/#tag/Document-Relation
        """
        await self._http_client.delete(Resource.DocumentRelation, document_relation_id)

    # ##### RELATIONS #####

    async def list_relations(
        self, ordering: Sequence[RelationOrdering] = (), **filters: Any
    ) -> AsyncIterator[RelationType]:
        """Retrieve all :class:`~rossum_api.models.relation.Relation` objects satisfying the specified filters.

        Parameters
        ----------
        ordering
            List of object names. Their URLs are used for sorting the results
        filters
            id: ID of the :class:`~rossum_api.models.relation.Relation`.

            type: Relation type, see :class:`~rossum_api.models.relation.RelationType`.

            parent: ID of parent :class:`~rossum_api.models.annotation.Annotation`.

            key: Relation key.

            annotation: ID of related :class:`~rossum_api.models.annotation.Annotation`.

        References
        ----------
        https://rossum.app/api/docs/#operation/relations_list

        https://rossum.app/api/docs/#tag/Relation
        """
        async for r in self._http_client.fetch_all(Resource.Relation, ordering, **filters):
            yield self._deserializer(Resource.Relation, r)

    async def create_new_relation(self, data: dict[str, Any]) -> RelationType:
        """Create a new :class:`~rossum_api.models.relation.Relation` object.

        Parameters
        ----------
        data
            :class:`~rossum_api.models.relation.Relation` object configuration.

        References
        ----------
        https://rossum.app/api/docs/#operation/relations_create

        https://rossum.app/api/docs/#tag/Relation
        """
        relation = await self._http_client.create(Resource.Relation, data)

        return self._deserializer(Resource.Relation, relation)

    # ##### WORKSPACES #####
    async def list_workspaces(
        self, ordering: Sequence[WorkspaceOrdering] = (), **filters: Any
    ) -> AsyncIterator[WorkspaceType]:
        """Retrieve all :class:`~rossum_api.models.workspace.Workspace` objects satisfying the specified filters.

        Parameters
        ----------
        ordering
            List of object names. Their URLs are used for sorting the results
        filters
            id: ID of a :class:`~rossum_api.models.workspace.Workspace`

            name: Name of a :class:`~rossum_api.models.workspace.Workspace`

            organization: ID of an :class:`~rossum_api.models.organization.Organization`

        References
        ----------
        https://rossum.app/api/docs/#operation/workspaces_list

        https://rossum.app/api/docs/#tag/Workspace
        """
        async for w in self._http_client.fetch_all(Resource.Workspace, ordering, **filters):
            yield self._deserializer(Resource.Workspace, w)

    async def retrieve_workspace(self, workspace_id: int) -> WorkspaceType:
        """Retrieve a single :class:`~rossum_api.models.workspace.Workspace` object.

        Parameters
        ----------
        workspace_id
            ID of a workspace to be retrieved.

        References
        ----------
        https://rossum.app/api/docs/#operation/workspaces_retrieve

        https://rossum.app/api/docs/#tag/Workspace
        """
        workspace = await self._http_client.fetch_one(Resource.Workspace, workspace_id)

        return self._deserializer(Resource.Workspace, workspace)

    async def create_new_workspace(self, data: dict[str, Any]) -> WorkspaceType:
        """Create a new :class:`~rossum_api.models.workspace.Workspace` object.

        Parameters
        ----------
        data
            :class:`~rossum_api.models.workspace.Workspace` object configuration.

        References
        ----------
        https://rossum.app/api/docs/#operation/workspaces_create

        https://rossum.app/api/docs/#tag/Workspace
        """
        workspace = await self._http_client.create(Resource.Workspace, data)

        return self._deserializer(Resource.Workspace, workspace)

    async def delete_workspace(self, workspace_id: int) -> None:
        """Delete :class:`rossum_api.models.workspace.Workspace` object.

        Parameters
        ----------
        workspace_id
            ID of a workspace to be deleted.

        References
        ----------
        https://rossum.app/api/docs/#operation/workspaces_delete

        https://rossum.app/api/docs/#tag/Workspace
        """
        return await self._http_client.delete(Resource.Workspace, workspace_id)

    # ##### ENGINE #####

    async def retrieve_engine(self, engine_id: int) -> EngineType:
        """Retrieve a single :class:`~rossum_api.models.engine.Engine` object.

        Parameters
        ----------
        engine_id
            ID of an engine to be retrieved.

        References
        ----------
        https://rossum.app/api/docs/#operation/dedicated_engines_retrieve

        https://rossum.app/api/docs/#tag/Dedicated-Engine
        """
        engine = await self._http_client.fetch_one(Resource.Engine, engine_id)

        return self._deserializer(Resource.Engine, engine)

    async def list_engines(
        self, ordering: Sequence[str] = (), sideloads: Sequence[Sideload] = (), **filters: Any
    ) -> AsyncIterator[EngineType]:
        """Retrieve all :class:`~rossum_api.models.engine.Engine` objects satisfying the specified filters.

        Parameters
        ----------
        ordering
            List of object names. Their URLs are used for sorting the results
        sideloads
            List of additional objects to sideload
        filters
            id: ID of an :class:`~rossum_api.models.engine.Engine`

            type: Type of an :class:`~rossum_api.models.engine.Engine`

            agenda_id: ID of the agenda associated with this engine

        References
        ----------
        https://rossum.app/api/docs/internal/#operation/dedicated_engines_list

        https://rossum.app/api/docs/#tag/Dedicated-Engine
        """
        async for engine in self._http_client.fetch_all(
            Resource.Engine, ordering, sideloads, **filters
        ):
            yield self._deserializer(Resource.Engine, engine)

    async def retrieve_engine_fields(
        self, engine_id: int | None = None
    ) -> AsyncIterator[EngineFieldType]:
        """Retrieve all :class:`~rossum_api.models.engine.EngineField` objects satisfying the specified filters.

        Parameters
        ----------
        engine_id
            ID of an engine to retrieve fields for. If None, retrieves all engine fields.

        References
        ----------
        https://rossum.app/api/docs/internal/#tag/Engine-Field

        https://rossum.app/api/docs/internal/#tag/Engine-Field
        """
        async for engine_field in self._http_client.fetch_all(
            Resource.EngineField, engine=engine_id
        ):
            yield self._deserializer(Resource.EngineField, engine_field)

    async def retrieve_engine_queues(self, engine_id: int) -> AsyncIterator[QueueType]:
        """https://rossum.app/api/docs/internal/#operation/queues_list."""
        async for queue in self._http_client.fetch_all(Resource.Queue, engine=engine_id):
            yield self._deserializer(Resource.Queue, queue)

    # ##### INBOX #####
    async def create_new_inbox(self, data: dict[str, Any]) -> InboxType:
        """https://rossum.app/api/docs/#operation/inboxes_create."""
        inbox = await self._http_client.create(Resource.Inbox, data)

        return self._deserializer(Resource.Inbox, inbox)

    # ##### EMAILS #####
    async def retrieve_email(self, email_id: int) -> EmailType:
        """Retrieve a single `rossum_api.models.email.Email` object.

        Parameters
        ----------
        email_id
            ID of email to be retrieved

        References
        ----------
        https://rossum.app/api/docs/#operation/emails_retrieve

        https://rossum.app/api/docs/#tag/Email
        """
        email = await self._http_client.fetch_one(Resource.Email, email_id)

        return self._deserializer(Resource.Email, email)

    async def import_email(
        self, raw_message: bytes, recipient: str, mime_type: str | None = None
    ) -> str:
        """Import an email as raw data.

        Calling this endpoint starts an asynchronous process of creating an email object
        and importing its contents to the specified recipient inbox in Rossum.

        Parameters
        ----------
        raw_message
            Raw email data.
        recipient
            Email address of the inbox where the email will be imported.
        mime_type
            Mime type of imported files

        References
        ----------
        https://rossum.app/api/docs/#operation/emails_import

        https://rossum.app/api/docs/#tag/Email
        """
        response = await self._http_client.request_json(
            "POST",
            url=EMAIL_IMPORT_URL,
            files=build_email_import_files(raw_message, recipient, mime_type),
        )
        return response["url"]  # type: ignore[no-any-return]

    # ##### EMAIL TEMPLATES #####
    async def list_email_templates(
        self, ordering: Sequence[EmailTemplateOrdering] = (), **filters: Any
    ) -> AsyncIterator[EmailTemplateType]:
        """Retrieve all :class:`~rossum_api.models.email_template.EmailTemplate` objects satisfying the specified filters.

        Parameters
        ----------
        ordering
            List of object names. Their URLs are used for sorting the results
        filters
            id: ID of an :class:`~rossum_api.models.email_template.EmailTemplate`

            queue: ID of a :class:`~rossum_api.models.queue.Queue`

            type: Type of the email template

            name: Name of the :class:`~rossum_api.models.email_template.EmailTemplate`

        References
        ----------
        https://rossum.app/api/docs/#operation/email_templates_list

        https://rossum.app/api/docs/#tag/Email-Template
        """
        async for c in self._http_client.fetch_all(Resource.EmailTemplate, ordering, **filters):
            yield self._deserializer(Resource.EmailTemplate, c)

    async def retrieve_email_template(self, email_template_id: int) -> EmailTemplateType:
        """Retrieve a single :class:`~rossum_api.models.email_template.EmailTemplate` object.

        Parameters
        ----------
        email_template_id
            ID of an email template to be retrieved.

        References
        ----------
        https://rossum.app/api/docs/#operation/email_templates_retrieve

        https://rossum.app/api/docs/#tag/Email-Template
        """
        email_template = await self._http_client.fetch_one(
            Resource.EmailTemplate, email_template_id
        )

        return self._deserializer(Resource.EmailTemplate, email_template)

    async def create_new_email_template(self, data: dict[str, Any]) -> EmailTemplateType:
        """Create a new :class:`~rossum_api.models.email_template.EmailTemplate` object.

        Parameters
        ----------
        data
            :class:`~rossum_api.models.email_template.EmailTemplate` object configuration.

        References
        ----------
        https://rossum.app/api/docs/#operation/email_templates_create

        https://rossum.app/api/docs/#tag/Email-Template
        """
        email_template = await self._http_client.create(Resource.EmailTemplate, data)

        return self._deserializer(Resource.EmailTemplate, email_template)

    # ##### CONNECTORS #####
    async def list_connectors(
        self, ordering: Sequence[ConnectorOrdering] = (), **filters: Any
    ) -> AsyncIterator[ConnectorType]:
        """Retrieve all :class:`~rossum_api.models.connector.Connector` objects satisfying the specified filters.

        Parameters
        ----------
        ordering
            List of object names. Their URLs are used for sorting the results
        filters
            id: ID of a :class:`~rossum_api.models.connector.Connector`

            name: Name of the :class:`~rossum_api.models.connector.Connector`

            service_url: Service URL of the :class:`~rossum_api.models.connector.Connector`

        References
        ----------
        https://rossum.app/api/docs/#operation/connectors_list

        https://rossum.app/api/docs/#tag/Connector
        """
        async for c in self._http_client.fetch_all(Resource.Connector, ordering, **filters):
            yield self._deserializer(Resource.Connector, c)

    async def retrieve_connector(self, connector_id: int) -> ConnectorType:
        """Retrieve a single :class:`~rossum_api.models.connector.Connector` object.

        Parameters
        ----------
        connector_id
            ID of a connector to be retrieved.

        References
        ----------
        https://rossum.app/api/docs/#operation/connectors_retrieve

        https://rossum.app/api/docs/#tag/Connector
        """
        connector = await self._http_client.fetch_one(Resource.Connector, connector_id)

        return self._deserializer(Resource.Connector, connector)

    async def create_new_connector(self, data: dict[str, Any]) -> ConnectorType:
        """Create a new :class:`~rossum_api.models.connector.Connector` object.

        Parameters
        ----------
        data
            :class:`~rossum_api.models.connector.Connector` object configuration.

        References
        ----------
        https://rossum.app/api/docs/#operation/connectors_create

        https://rossum.app/api/docs/#tag/Connector
        """
        connector = await self._http_client.create(Resource.Connector, data)

        return self._deserializer(Resource.Connector, connector)

    # ##### HOOKS #####
    async def list_hooks(
        self, ordering: Sequence[HookOrdering] = (), **filters: Any
    ) -> AsyncIterator[HookType]:
        """Retrieve all :class:`~rossum_api.models.hook.Hook` objects satisfying the specified filters.

        Parameters
        ----------
        ordering
            List of object names. Their URLs are used for sorting the results
        filters
            id: ID of a :class:`~rossum_api.models.hook.Hook`

            name: Name of a :class:`~rossum_api.models.hook.Hook`

            type: Hook type. Possible values: ``webhook, function, job``

            queue: ID of a :class:`~rossum_api.models.queue.Queue`

            active: If set to true the hook is notified.

            config_url:

            config_app_url:

            extension_source: Import source of the extension.
            For more, see `Extension sources <https://rossum.app/api/docs/#tag/Extensions>`_

        References
        ----------
        https://rossum.app/api/docs/#operation/hooks_list

        https://rossum.app/api/docs/#tag/Hook
        """
        async for h in self._http_client.fetch_all(Resource.Hook, ordering, **filters):
            yield self._deserializer(Resource.Hook, h)

    async def retrieve_hook(self, hook_id: int) -> HookType:
        """Retrieve a single :class:`~rossum_api.models.hook.Hook` object.

        Parameters
        ----------
        hook_id
            ID of a hook to be retrieved.

        References
        ----------
        https://rossum.app/api/docs/#operation/hooks_retrieve

        https://rossum.app/api/docs/#tag/Hook
        """
        hook = await self._http_client.fetch_one(Resource.Hook, hook_id)

        return self._deserializer(Resource.Hook, hook)

    async def create_new_hook(self, data: dict[str, Any]) -> HookType:
        """Create a new :class:`~rossum_api.models.hook.Hook` object.

        Parameters
        ----------
        data
            :class:`~rossum_api.models.hook.Hook` object configuration.

        References
        ----------
        https://rossum.app/api/docs/#operation/hooks_create

        https://rossum.app/api/docs/#tag/Hook
        """
        hook = await self._http_client.create(Resource.Hook, data)

        return self._deserializer(Resource.Hook, hook)

    async def update_part_hook(self, hook_id: int, data: dict[str, Any]) -> HookType:
        """Update part of a :class:`~rossum_api.models.hook.Hook` object.

        Parameters
        ----------
        hook_id
            ID of a hook to be updated.
        data
            :class:`~rossum_api.models.hook.Hook` object partial configuration.

        References
        ----------
        https://rossum.app/api/docs/#operation/hooks_partial_update

        https://rossum.app/api/docs/#tag/Hook
        """
        hook = await self._http_client.update(Resource.Hook, hook_id, data)

        return self._deserializer(Resource.Hook, hook)

    async def delete_hook(self, hook_id: int) -> None:
        """Delete a :class:`~rossum_api.models.hook.Hook` object.

        Parameters
        ----------
        hook_id
            ID of a hook to be deleted.

        References
        ----------
        https://rossum.app/api/docs/#operation/hooks_delete

        https://rossum.app/api/docs/#tag/Hook
        """
        return await self._http_client.delete(Resource.Hook, hook_id)

    async def list_hook_run_data(self, **filters: Any) -> AsyncIterator[HookRunDataType]:
        """Retrieve all :class:`~rossum_api.models.hook.HookRunData` objects satisfying the specified filters.

        Parameters
        ----------
        filters
            timestamp_before: ISO 8601 timestamp, filter logs triggered before this time

            timestamp_after: ISO 8601 timestamp, filter logs triggered after this time

            start_before: ISO 8601 timestamp, filter logs started before this time

            start_after: ISO 8601 timestamp, filter logs started after this time

            end_before: ISO 8601 timestamp, filter logs ended before this time

            end_after: ISO 8601 timestamp, filter logs ended after this time

            hook: ID of a :class:`~rossum_api.models.hook.Hook`

            log_level: Message log level, possible values ``INFO, ERROR, WARNING``

            request_id: Filter by request ID

            status: Filter by status

            status_code: HTTP status code

            queue: ID of a :class:`~rossum_api.models.queue.Queue`

            annotation: ID of a :class:`~rossum_api.models.annotation.Annotation`

            email: ID of a :class:`~rossum_api.models.email.Email`

            search: Full-text search

            page_size: Number of results per page (default 100)

        Notes
        -----
        The retention policy for the logs is set to 7 days.

        Returns at most 100 logs.

        References
        ----------
        https://rossum.app/api/docs/#operation/hooks_logs_list
        """
        async for d in self._http_client.fetch_all(Resource.HookRunData, **filters):
            yield self._deserializer(Resource.HookRunData, d)

    # ##### HOOK TEMPLATES #####
    async def list_hook_templates(self, **filters: Any) -> AsyncIterator[HookTemplateType]:
        """Retrieve all :class:`~rossum_api.models.hook_template.HookTemplate` objects satisfying the specified filters.

        Parameters
        ----------
        filters
            id: ID of a :class:`~rossum_api.models.hook_template.HookTemplate`

            name: Name of a :class:`~rossum_api.models.hook_template.HookTemplate`

            type: Hook template type. Possible values: ``"webhook"``, ``"function"``

            extension_source: Import source of the extension.
            Possible values: ``"custom"``, ``"rossum_store"``

        References
        ----------
        https://rossum.app/api/docs/#operation/hook_templates_list

        https://rossum.app/api/docs/#tag/Hook-Template
        """
        async for ht in self._http_client.fetch_all(Resource.HookTemplate, **filters):
            yield self._deserializer(Resource.HookTemplate, ht)

    async def retrieve_hook_template(self, hook_template_id: int) -> HookTemplateType:
        """Retrieve a single :class:`~rossum_api.models.hook_template.HookTemplate` object.

        Parameters
        ----------
        hook_template_id
            ID of a hook template to be retrieved.

        References
        ----------
        https://rossum.app/api/docs/#operation/hook_templates_retrieve

        https://rossum.app/api/docs/#tag/Hook-Template
        """
        hook_template = await self._http_client.fetch_one(Resource.HookTemplate, hook_template_id)

        return self._deserializer(Resource.HookTemplate, hook_template)

    # ##### RULES #####
    async def list_rules(
        self, ordering: Sequence[RuleOrdering] = (), **filters: Any
    ) -> AsyncIterator[RuleType]:
        """Retrieve all :class:`~rossum_api.models.rule.Rule` objects satisfying the specified filters.

        Parameters
        ----------
        ordering
            List of object names. Their URLs are used for sorting the results
        filters
            id: ID of a :class:`~rossum_api.models.rule.Rule`.

            name: Name of a :class:`~rossum_api.models.rule.Rule`.

            schema: ID of a :class:`~rossum_api.models.schema.Schema`.

            rule_template: URL of the rule template the rule was created from.

            organization: ID of a :class:`~rossum_api.models.organization.Organization`.

        References
        ----------
        https://rossum.app/api/docs/#operation/rules_list

        https://rossum.app/api/docs/#tag/Rule
        """
        async for r in self._http_client.fetch_all(Resource.Rule, ordering, **filters):
            yield self._deserializer(Resource.Rule, r)

    async def retrieve_rule(self, rule_id: int) -> RuleType:
        """Retrieve a single :class:`~rossum_api.models.rule.Rule` object.

        Parameters
        ----------
        rule_id
            ID of a rule to be retrieved.

        References
        ----------
        https://rossum.app/api/docs/#operation/rules_retrieve

        https://rossum.app/api/docs/#tag/Rule
        """
        rule = await self._http_client.fetch_one(Resource.Rule, rule_id)
        return self._deserializer(Resource.Rule, rule)

    async def create_new_rule(self, data: dict[str, Any]) -> RuleType:
        """Create a new :class:`~rossum_api.models.rule.Rule` object.

        Parameters
        ----------
        data
            :class:`~rossum_api.models.rule.Rule` object configuration.

        References
        ----------
        https://rossum.app/api/docs/#operation/rules_create

        https://rossum.app/api/docs/#tag/Rule
        """
        rule = await self._http_client.create(Resource.Rule, data)
        return self._deserializer(Resource.Rule, rule)

    async def update_part_rule(self, rule_id: int, data: dict[str, Any]) -> RuleType:
        """Update part of a :class:`~rossum_api.models.rule.Rule` object.

        Parameters
        ----------
        rule_id
            ID of a rule to be updated.
        data
            :class:`~rossum_api.models.rule.Rule` object partial configuration.

        References
        ----------
        https://rossum.app/api/docs/#operation/rules_update

        https://rossum.app/api/docs/#tag/Rule
        """
        rule = await self._http_client.update(Resource.Rule, rule_id, data)
        return self._deserializer(Resource.Rule, rule)

    async def delete_rule(self, rule_id: int) -> None:
        """Delete a :class:`~rossum_api.models.rule.Rule` object.

        Parameters
        ----------
        rule_id
            ID of a rule to be deleted.

        References
        ----------
        https://rossum.app/api/docs/#operation/rules_delete

        https://rossum.app/api/docs/#tag/Rule
        """
        return await self._http_client.delete(Resource.Rule, rule_id)

    # ##### USER ROLES #####
    async def list_user_roles(
        self, ordering: Sequence[UserRoleOrdering] = (), **filters: Any
    ) -> AsyncIterator[GroupType]:
        """Retrieve all :class:`~rossum_api.models.group.Group` objects satisfying the specified filters.

        Parameters
        ----------
        ordering
            List of object names. Their URLs are used for sorting the results
        filters
            name: Name of :class:`~rossum_api.models.group.Group`


        References
        ----------
        https://rossum.app/api/docs/#operation/user_roles_list

        https://rossum.app/api/docs/#tag/User-Role
        """
        async for g in self._http_client.fetch_all(Resource.Group, ordering, **filters):
            yield self._deserializer(Resource.Group, g)

    # ##### GENERIC METHODS #####
    async def request_paginated(self, url: str, *args: Any, **kwargs: Any) -> AsyncIterator[dict]:
        """Request to endpoints with paginated response that do not have direct support in the client."""
        async for element in self._http_client.fetch_all_by_url(url, *args, **kwargs):
            yield element

    async def request_json(self, method: HttpMethod, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Request to endpoints that do not have direct support in the client and return plain JSON."""
        return await self._http_client.request_json(method, *args, **kwargs)

    async def request(self, method: HttpMethod, *args: Any, **kwargs: Any) -> httpx.Response:
        """Request to endpoints that do not have direct support in the client and return plain response."""
        return await self._http_client.request(method, *args, **kwargs)

    async def get_token(self, refresh: bool = False) -> str:
        """Return the current token. Authentication is done automatically if needed.

        Parameters
        ----------
        refresh
            force refreshing the token
        """
        return await self._http_client.get_token(refresh)

    async def authenticate(self) -> None:  # noqa: D102
        await self._http_client._authenticate()

    async def _sideload(self, resource: dict[str, Any], sideloads: Sequence[Sideload]) -> None:
        """Load sideloads manually.

        The API does not support sideloading when fetching a single resource, we need to load
        it manually.
        """

        async def fetch_sideload(sideload: Sideload) -> dict[str, Any] | None:
            sideload_url = resource[to_singular(sideload)]
            if sideload_url is not None:
                return await self._http_client.request_json("GET", sideload_url)
            return None

        sideload_tasks = [asyncio.create_task(fetch_sideload(sideload)) for sideload in sideloads]
        sideloaded_jsons = await asyncio.gather(*sideload_tasks)

        for sideload, sideloaded_json in zip(sideloads, sideloaded_jsons):
            if sideloaded_json is not None and sideload == "content":
                # Content (i.e. list of sections is wrapped in a dict)
                sideloaded_json = sideloaded_json["content"]
            resource[to_singular(sideload)] = sideloaded_json


# Type alias for an AsyncRossumAPIClient that uses the default deserializer
AsyncRossumAPIClientWithDefaultDeserializer = AsyncRossumAPIClient[
    Annotation,
    Connector,
    Document,
    DocumentRelation,
    EmailTemplate,
    Engine,
    EngineField,
    Group,
    Hook,
    HookRunData,
    HookTemplate,
    Inbox,
    Email,
    OrganizationGroup,
    Organization,
    Queue,
    Relation,
    Rule,
    Schema,
    Task,
    Upload,
    User,
    Workspace,
]
