Abstract
========

The identity management, authentication, and authorization component of the Rubin Science Platform is responsible for maintaining a list of authorized users and their associated identity information, authenticating their access to the Science Platform, and determining which services they are permitted to use.
This tech note describes the high-level design of that system and summarizes its desired features and capabilities, independent of choice of implementation.

This is not a complete description of everything we want the identity management system to do, only a design for the portions that have been implemented to date.
Designs for further components and features will be added to this document as they are completed.
For a list of remaining work, see the `remaining work section of SQR-069 <https://sqr-069.lsst.io/#remaining>`__.

.. note::

   This is part of a tech note series on identity management for the Rubin Science Platform.
   The other two primary documents are DMTN-224_, which describes the implementation; and SQR-069_, which provides a history and analysis of the decisions underlying the design and implementation.
   See the `references section of DMTN-224 <https://dmtn-224.lsst.io/#references>`__ for a complete list of related documents.

Science Platform deployments
============================

There is no single Rubin Science Platform.
Instead, there are multiple deployments of the Science Platform at different sites with different users and different configurations.
These can be divided into two general classes.
Each class has slightly different authentication and identity management requirements.

General access
    Provides access to the Science Platform to the general astronomy community according to the Rubin Observatory Data Policy (RDO-013_).
    Users of these facilities may have no specific affiliation with Rubin Observatory other than being data rights holders.
    Examples include the :abbr:`IDF (Interim Data Facility)`, :abbr:`CDF (Cloud Data Facility)`, and possibly other International Data Facilities or Data Access Centers.

Restricted access
    Dedicated deployments of the Science Platform may be used to support telescope operations, data processing, or other purposes.
    These deployments will only be accessible to telescope operators, project scientists, and others with a direct affiliation with Rubin Observatory.
    Some data facilities and data access centers may also deploy the Science Platform for use only by a restricted set of users.

Every deployment of the Science Platform is a separate identity and authentication domain (with the possible exception of some closely-linked deployments used for testing and integration).
Access to one deployment of the Science Platform does not grant access to a different deployment of the Science Platform.
The same person may have different usernames, authentication mechanisms, and identity information in each Science Platform deployment to which they have access.

Required infrastructure
-----------------------

In order to deploy the Science Platform's identity management component, the hosting environment for that Science Platform deployment must provide:

- A Kubernetes cluster running a recent version of Kubernetes.
  The Science Platform is primarily tested against the "regular" channel of Google Kubernetes Engine and may not work on older versions of Kubernetes.

- Load balancing and IP allocation for an ingress controller.
  This will be used by ingress-nginx to allocate its external IP and to receive external traffic.

- A Kubernetes provider of ``PersistentVolume`` storage.
  This will be used to store the token data for the Science Platform.
  If this storage is not persistent, user tokens will be regularly invalidated.
  The hosting environment should also provide some way for those volumes to be backed up and restored.

A PostgreSQL database for internal storage of authentication and authorization data will be used if available and suitable for the needs of the Science Platform, but the Science Platform can deploy its own internal PostgreSQL server if necessary.

Due to the specific requirements around auth subrequest handling, the Science Platform provides its own ingress controller and cannot use an ingress controller provided by the hosting environment.

Component overview
==================

A general access deployment of the Science Platform has, at a high level, the following structure for handling authentication and identity management for two Science Platform services.
Both services receive user requests, and service A also sends requests to service B.
(The deployment would have multiple services, not just two services as shown.)

.. figure:: /_static/general-access.png
   :name: General access deployment architecture

   High-level structure of authentication and identity management for two services that receive user requests.
   Service A also sends requests to service B.

The identity management component is where the user's identity data (email, full name, group membership, etc.) and associated identities are stored, and where the user can go to change that information.
Here it is shown as running outside of the Kubernetes cluster on which the Science Platform is deployed.
This is true in the current implementation but need not be the case in the design.

The Kubernetes ingress verifies authentication and access control on each request with a subquery to the authentication service (labeled Authentication in this diagram).

Restricted access environments have a wider range of configurations.
The identity provider may be GitHub or may be a local OpenID Connect provider, LDAP may or may not be in use, and so forth.
Here is a sample diagram for a restricted access environment using a local OpenID Connect identity provider and using LDAP as the data store for identity information.

.. figure:: /_static/restricted-access.png
   :name: Sample restricted access deployment architecture

   Sample high-level structure of authentication and identity management in a restricted access deployment using OpenID Connect and LDAP.
   Both services receive user requests.
   Service A also sends requests to service B.

User identity
=============

Users of a general access Science Platform deployment will access it via a federated identity provider.
They will authenticate using their account at their local institution, or their choice of a cloud identity provider such as GitHub or Google.
That institution will, in turn, release their identity to the Science Platform.
This source of identity is discussed in detail in :ref:`Federated identity <federated-identity>`.

Restricted access deployments of the Science Platform may chose from one of two sources of user identity:

#. GitHub
#. Local identity provider supporting OpenID Connect

If GitHub is used as the identity provider, identity information will be taken from the user's GitHub account information, and the user's groups (see :ref:`Groups <groups>`) will be derived from the user's organization and team memberships on GitHub.
If a local identity provider is used, identity and group information will be read either from an associated LDAP server or from the identity token provided by the OpenID Connect authentication process.

In all cases, the user identity provider is also the primary source of user authentication.
After a user has authenticated via their identity provider, they may create an authentication token for programmatic access to the Science Platform (see :ref:`Token authentication <token-auth>`).
However, they must authenticate via their identity provider first.

The Science Platform will not store or verify any user authentication information, such as passwords, access codes, or certificates, apart from the tokens issued by the Science Platform after a successful authentication.
This means the Science Platform is also not responsible for (and cannot assist with) lost passwords, credential resets, or other authentication support.
Authentication is delegated to the identity provider and the Science Platform trusts the identity data provided by that provider.

.. _federated-identity:

Federated identity
------------------

General access deployments of the Science Platform will use identity federations as their primary source of user identity and authentication.
The InCommon_ federation will be supported for the IDF and CDF.
Other federations may be supported.

.. _InCommon: https://incommon.org/

A new user of a general access deployment will go through an enrollment process.
This process will gather the user's identity information as released by their federated identity provider (name, email, and institutional affiliation), and allow the user to select a username for use with the Science Platform.
Usernames will be unique across the Science Platform and must satisfy the requirements given in DMTN-225_.
If the user chooses, they can also specify a name and email address for the Science Platform to use in preference to the one released by their identity provider.
The user will be required to verify that they can receive email at the email address they specify.

At the conclusion of enrollment, the user will have a pending account on that Science Platform but will not yet have access.
The user must then be approved for access to the Science Platform.
That approval process will place the user in an appropriate access group for their data rights, as determined by the approver.
This decision will be taken according to Rubin Observatory policy based on institutional affiliation and possibly data obtained from outside the identity management system.
Approvers will be project staff who have the knowledge and authority to verify the data rights of a particular community of users.
Technical expertise in the identity management system is not required.
Once the user is approved, their account will become active and they will be able to use it to access the Science Platform.

Once a user's account is active, they may add additional identities to that same account.
Those identities may be from other identity providers that are part of a supported identity federation, or cloud identity providers.
GitHub and Google, in particular, will be supported as identity providers.
All identities added to the same account are treated as equivalent for authentication purposes; the user can use any of the linked identity providers to authenticate to the Science Platform.

Note that users can use GitHub or Google as their authentication provider for initial enrollment, although in that case the identity provider will probably not release any information useful for determining their data rights, and the approver will therefore need information from outside the scope of the identity management system.

Once the user's account is active, they can change their preferred name or email address whenever they wish.
If they change their email address, they will have to verify that they can receive email at the new email address.

.. _tokens:

Tokens
======

All authentication of browser or API access to the Science Platform except the identity management system is done with bearer tokens.
These are short, random strings that function as lookup keys for active user authentication sessions.

The identity management system of a general access deployment is a special case.
It is only accessible via a web browser and uses identity information from the federated identity provider directly.
Tokens cannot be used to access the identity management system.

Tokens come in five types.
The uses of those token types are discussed in more detail in :ref:`Authentication flows <authentication>`.

session
    Authenticates web access from a browser.
    This type of token is stored in the user's browser as or inside an HTTP cookie, and is sent by that browser to the Science Platform when the user attempts to access a non-public page.
    See :ref:`Browser authentication <browser-auth>` for more details.

user
    An authentication token created by the user.
    The user generally authenticates with a session token to create a user token.
    These tokens are intended for use in programmatic access to the Science Platform from user-written programs or local applications.
    See :ref:`Token authentication <token-auth>` for more details.

internal
    Used for service-to-service authentication when a service makes a subrequest to another service as part of fulfilling a user request.
    These tokens are associated with the identity of the user making the original request, but have restricted access permissions and are also associated with the service making the subrequest.
    See :ref:`Subrequest authentication <subrequest-auth>` for more details.

notebook
    A special case of an internal token used by the Notebook Aspect.
    When a user spawns a Notebook Aspect lab, that lab is issued a token with all the same access rights as the user's browser session.
    That token is then available to the user for API calls to other Science Platform services from within their notebook.

service
    The one type of authentication token not associated with a user.
    These tokens are used when one service wants to make an API call to another Science Platform service that is unrelated to a user request.
    For example, a monitoring service may want to make a test API call to another service to ensure that it is operating properly.
    See :ref:`Service-to-service authentication <service-auth>` for more details.

These tokens tend to organize into hierarchies, as shown in the following diagram.

.. figure:: /_static/tokens.svg
   :name: Token type hierarchy

   Hierarchy of token types.
   The token type on the left of each arrow is used as authentication to create the token type on the right of the arrow.
   Token creation other than creation of a user token from a session token happens automatically and the user need not be aware of it.

The first hierarchy starts from a user's browser session.
If the user accesses services that require authentication but don't make any subrequests, no further tokens are created.
Otherwise, notebook and internal tokens may be created to satisfy the user's requests.
Notice that subrequests can themselves have subrequests, which may create a chain of internal tokens.
The user can also manually create a user token.

The second hierarchy shows the user token being used to access services that make subrequests.

The third hierarchy is for service-to-service authentication outside the scope of a user request.
Service-to-service authentication may also involve notebook and internal tokens.

.. _scopes:

Scopes
------

Every token is associated with a set of scopes.
These scopes are used to make authorization decisions.
Each service or component of the Science Platform will require the authentication token have specific scopes to be allowed to access it.
Requests authenticated with a token without the necessary scopes will be rejected with an error.

Scopes come originally from the user's group membership.
When they authenticate to the Science Platform with a web browser and get a session token, that token is given a list of scopes according to a per-deployment mapping of groups to scopes.
Any subsequent notebook tokens created from that session token receive the same scopes.
Internal tokens created from that token have at most the same scopes, usually fewer (since they will be restricted to only the scopes necessary for subrequests).

Scopes are used for "coarse-grained" access control: whether a user can access a specific component or API at all, or whether the user is allowed to access administrative interfaces for a service.
"Fine-grained" access control decisions made by services, such as whether a user with general access to the service is able to run a specific query or access a specific image, are instead made based on the user's group membership.
(See :ref:`Groups <groups>` for more details.)

For a list of the scopes used by the Science Platform, their definitions, and the services to which they grant access, see DMTN-235_.

Child tokens
------------

Notebook and internal tokens are created from another token and are called "child tokens."
The token from which they are created is called a "parent token."

Child tokens inherit their lifetime and scopes from their parent token, in a possibly restricted way.
The child token will never have more scopes or a longer lifetime than the parent token, but may have fewer scopes or a shorter lifetime.

When a token is revoked, all child tokens of that token are also immediately revoked.
This happens when the user logs out in their web browser (revoking the session token and all child tokens of the session token), or when the user deletes a previously-created user token (revoking all child tokens of that user token).

Although the user authenticates with a session token in order to create a user token, user tokens are not child tokens of the session token and have an independent lifetime.
As discussed in :ref:`Token authentication <token-auth>`, user tokens may have a longer lifetime than the session token used to create them.

.. _authentication:

Authentication flows
====================

So far as possible, authentication and access control for Science Platform services will be handled by a separate authentication service interposed between the user request and the service backend.
Service backends need only be aware of information exposed by the authentication service, not the precise mechanism the user used to authenticate.

The Science Platform requires Kubernetes, which handles this type of interposition via ``Ingress`` resources.
If the authentication service rejects the request at the ingress, it is never passed to the backend service.

One implication of this is that all access to services in the Science Platform, including access to services from the Notebook Aspect and service-to-service access, must go through the ingress.
This is not the default in Kubernetes; by default, applications running within the same Kubernetes cluster can access the ``Service`` or even ``Pod`` of another service directly without using the ingress.
Correct use of the authentication service therefore requires blocking non-ingress access to other services via, for example, a Kubernetes ``NetworkPolicy``.

TLS is required for all traffic between the user and the Science Platform.
Communications internal to the Science Platform need not use TLS provided that they happen only within a restricted private network specific to that Science Platform deployment.

Use cases
---------

Here are some typical authentication use cases.
This is a sampling of typical uses, not a comprehensive list of possibilities.

- User authenticates using an identity provider and obtains a session token.

- User accesses a service using a web browser.
  The scopes of the user's session token are checked to ensure the user has the required scope to access that service.

- User spawns a notebook via the Notebook Aspect.
  The notebook spawner requests a delegated notebook token.
  A new notebook token is created as a subtoken of the session token and made available to the notebook spawner.
  The notebook spawner arranges to make that token available to the spawned notebook server.

- User makes a request via a web interface that requires talking to another backend service.
  The web service requests an internal token with appropriate scope in its ingress configuration.
  The web service receives that token from the request and uses it to make requests on behalf of the user.
  This may repeat recursively if that backend service needs to make requests to another service.

- User makes a request via an API from their notebook server.
  The notebook token is used for this request.

- User makes a request via an API from the notebook server that requires making subrequests on the user's behalf.
  This follows the same pattern as the equivalent case with a web UI: the backend service requests a subtoken and uses it.

- User goes to the token management page and creates a user token.
  The user chooses the scopes to grant that token (from the scopes the user's session token has), its name, and when it will expire.
  This user token is created as a new token, not as a subtoken of the session token, but inherits information from the session token.
  User stores that token locally on their laptop and uses it to make a request to an API service.
  The token is checked to ensure that it has the appropriate scope for access to that service.

- User makes an API call with their user token that requires making subrequests to other services.
  This proceeds as with web UIs and notebook API calls.

- A service requests a token for itself, unrelated to any user request.
  That token is created and provided to the service.
  The service then uses that token to make API calls to other services within the same Science Platform deployment.

- A service uses a service token with ``admin:token`` scope to create a new ``user`` token for an arbitrary user.
  The service can then use that token to authenticate as a user to other services.
  This flow might be used by a load-testing or monitoring application.

.. _browser-auth:

Browser authentication
----------------------

If a user goes to a Science Platform web page without currently being authenticated, they will be sent to a login provider to authenticate.
For general access deployments, this will be a federated login provider that will allow them to choose their federated identity provider (or will remember their previous selection if desired and automatically send them there).
For restricted access deployments, this will be whatever the source of authentication is configured to be, either GitHub or an OpenID Connect provider.

The Science Platform authentication system will perform an OpenID Connect or (for GitHub) OAuth 2.0 authentication with the login provider and use that to obtain the user's identity.
It will then obtain any other needed information about the user (numeric UID, group membership and numeric GIDs, full name, email address, etc.) following the rules for sources of user information defined in DMTN-225_.
From that information, a session token will be created with scopes based on the user's group membership.
That session token will be stored in the user's browser, restricted to that installation of the Science Platform.
Then, the user will be redirected back to the page they were attempting to visit, now with authentication.

As a special case, if the user is accessing the identity management system of a general access deployment of the Science Platform, no session token is created or used.
The OpenID Connect authentication is used directly to authenticate access to the identity management system.

The session token stored in the browser will expire periodically, forcing the user to reauthenticate, so that stolen browser credentials cannot be reused indefinitely and the user's scopes are recalculated based on their current group membership.
The user can also log out at any time, which revokes their session token, revokes any child tokens (notebook or internal, but not user) created from that session token, and forces reauthentication the next time they attempt to visit a page that requires authentication.

The user's cookie holding their session token should not be passed down to individual Science Platform applications in a way that would allow that application to impersonate the user to different applications.
This is not yet implemented, but is expected to be added to the design in the future by following the recommendations in DMTN-193_.

.. _token-auth:

Token authentication
--------------------

Users can create user tokens and manage them (modify their names, scopes, and expiration, delete them, and see their history) via a web UI provided by the Science Platform.
These tokens are specific to that deployment of the Science Platform.
User tokens are intended for non-browser access to the Science Platform, such as for API calls from programs, use in astronomy desktop applications, and so forth.

User tokens have a public component (used as a unique identifier for the token in the UI) and a secret component.
The full token including the secret component is shown only when the token is created and subsequently cannot be obtained again.

The user chooses a name for the user token when creating it.
This name must be unique across all non-deleted user tokens for that user, and is intended as an aid for the user to keep track of where the token is being used.

When the user creates a user token, they can choose which scopes to delegate to that token.
They can only delegate scopes that their current session token has.
The user may wish to only delegate a subset of scopes so that, for example, the user token cannot be used to create more user tokens or access more privileged APIs unrelated to the purpose for which the token is being created.

When the user creates a user token, they can set an expiration date for the token.
They can also set the token to never expire.

The metadata associated with a user token (full name, email address, numeric UID, group membership, and so forth) will be the same as the user who created it.

To authenticate with a user token, the user provides it in the ``Authoriztion`` header.
The preferred way of doing so is as an `RFC 6750`_ bearer token.
However, some astronomy applications may only support HTTP Basic Authentication (`RFC 7617`_), so it is supported as an alternative to the bearer token protocol.
When Basic Authentication is used, either the username or the password should be the token, and the other field should be set to ``x-oauth-basic``.

.. _RFC 6750: https://datatracker.ietf.org/doc/html/rfc6750
.. _RFC 7617: https://datatracker.ietf.org/doc/html/rfc7617

User tokens cannot be used to access the identity management system to attach new federated identities, change the user's email address, change group memberships, or make any similar changes.
They may only be used to access Science Platform services.

.. _subrequest-auth:

Subrequest authentication
-------------------------

In some cases, a Science Platform service will need to perform further requests on behalf of a user in order to satisfy a request.
For example, the Portal Aspect will need to make TAP queries on the user's behalf.

Each of these requests should be authenticated and authorized as the user, so that the underlying services do not need to perform separate authorization checks.
Instead, the same authentication service that is interposed for user requests should also be interposed to perform access control for each subrequest.
This, in turn, implies that services should be able to obtain tokens that they can use to make subrequests.

These tokens, however, should not be the same as the token that the user used to authenticate the initial request, since that token will often have all the scopes that a user has and would be able to perform far more actions than the service should be able to perform on behalf of the user.
For example, the Portal Aspect should not be able to create a notebook as the user in the Notebook Aspect.
The user's original token (session or user) may also have a long expiration time or may not expire at all, whereas the service only needs a token for long enough to satisfy the user's request.

Services therefore have a mechanism to request delegated tokens.
These come in two types: internal tokens and notebook tokens.

If a server is so configured, the authentication system will issue a new internal or notebook token for that service (or reuse an existing one if appropriate).
For internal tokens, this will be limited in scope to only the permissions that service needs and with an expiration time set.
The service will receive this new token as part of the request, in an HTTP header, and can then use the token to make subsequent subrequests required to respond to the user's request.

As a special case, the Notebook Aspect of the Science Platform is intended as a general-purpose computing platform for the user and should have all of the same access that the user themselves have.
The Notebook Aspect (and only it) will therefore get a notebook token rather than an internal token.
This is a special case of an internal token that has all of the same scopes as the user's original session token, and is associated with the user's notebook server.
It may have a lifetime limited to the lifetime of the user's notebook server.

``Authorization`` headers used for token authentication should be (but are not yet) filtered out of the request so that they are not passed down to the underlying Science Platform service.
Otherwise, a service could recover the user's original token from the HTTP headers of the request.

.. _service-auth:

Service-to-service authentication
---------------------------------

In some cases, services may need to access other Science Platform services on their own behalf, unrelated to a user request.
For example, a monitoring system may need to make periodic requests to authenticated APIs of Science Platform services to ensure that they are running and correctly responding to requests.

These requests will be authorized in the same way as subrequests discussed above, by interposing the same authentication system used for user requests.
They are authenticated with service tokens, which are issued only to services and are never used by users.
Services can ask for service tokens by creating a custom Kubernetes resource specifying the properties of the service token, including the identity of the service and the scopes it requires.
The authentication service will then provide that service token as a Kubernetes ``Secret`` resource associated with the request in the custom resource, and thereby make it available to the service pods through the normal Kubernetes mechanisms for injecting secrets into pods.
The authentication service will also automatically refresh the service token to ensure that it does not expire.

As specified in DMTN-225_, the usernames associated with all such tokens must begin with ``bot-``.

OpenID Connect authentication
-----------------------------

Some Science Platform deployments run third-party services (Chronograf_, for example) that themselves want to do OpenID Connect authentication of the user.
To support those services, the authentication service of the Science Platform is also an OpenID Connect provider.
Such services can then point to the authentication service as the authentication provider, and those authentications will use the same source of identity as other authentications to the Science Platform.
(This authentication is independent of any use of OpenID Connect by the authentication service to a federated or local identity provider external to the Science Platform, although the two authentications will be chained together when needed.)

.. _Chronograf: https://www.influxdata.com/time-series-platform/chronograf/

At present, OpenID Connect authentication used in this fashion does not do any access control.
All users with any access to that Science Platform deployment will be able to complete the OpenID Connect authentication.
The protected service must do any necessary access control itself.

The ID token returned by this OpenID Connect provider is a :abbr:`JWT (JSON Web Token)` (see `RFC 7519`_) that includes the user's username, full name (if available), and numeric UID (if available).
No other information is provided to the protected service.

.. _RFC 7519: https://datatracker.ietf.org/doc/html/rfc7519

Note that this ID token is not a token as defined by :ref:`Tokens <tokens>` and cannot be used to authenticate to any other Science Platform service.
It is an implementation detail of the OpenID Connect authentication process.

.. _groups:

Groups
======

As discussed in :ref:`Scopes <scopes>`, when a user authenticates to the Science Platform with a web browser, their group membership is retrieved and they are granted scopes based on their group membership.
The group membership of the user is also provided to each service in an HTTP header, and is available via the :ref:`Token API <token-api>` on request from any service receiving a delegated token (see :ref:`Subrequest authentication <subrequest-auth>`).

The source of the user's group membership information varies by type of Science Platform deployment.

For restricted access deployments, group membership is taken from the user's GitHub teams, from an LDAP server configured as the source of identity information for that deployment, or from the token issued by an OpenID Connect authentication service.

For general access deployments, group membership is maintained in the identity management system.
Users will be added to appropriate access groups during enrollment by the approver.
Users may also create their own groups, and add and remove members from those groups as they see fit.
Collaborations using the Science Platform may also maintain groups of their members or affiliates.

In addition to those groups, in general access deployments, every user will also be a member of a group with the same name as their username.
That group will have only one member, the matching user.
This allows services that make access decisions based on groups to uniformly use group membership for all access decisions, without having to special-case access rules for individual users.
It also provides the user with a default group for services that use an underlying POSIX file system, such as the Notebook Aspect.
Restricted access deployments will generally also follow this convention, but they're not required to.

Access control decisions based on group membership must be made by individual services.
The authentication service only applies access restrictions based on scopes, and otherwise passes the group information to the service for it to do with as it sees fit.
In many cases, services will make subrequests on behalf of the user, and rely on access control by group membership to be imposed by lower-level services.

For further details about the sources of group information and their naming constraints, see DMTN-225_.

UIDs and GIDs
=============

Portions of the Science Platform, particularly the Notebook Aspect, will use an underlying POSIX file system.
Users therefore need numeric UIDs and GIDs to access those portions of the Science Platform, since those will be used for access control in the POSIX file system.

Every user is optionally assigned a numeric UID.
(The numeric UID may be required for access to some services.)
For restricted access deployments, that UID may come from an external source, such as GitHub, a local LDAP server, or an OpenID Connect ID token.
For general access deployments, user UIDs are assigned and recorded inside the identity management system.

Each group is similarly optionally assigned a numeric GID.
In general access deployments, and by preference in restricted access deployments, the GID for the group with the same name as the user is the same as the UID.

For further details on UID and GID assignment, see DMTN-225_.

.. _token-api:

Token API
=========

All actions on tokens — issuing them, revoking them, modifying them, retrieving their associated data, retrieving their history, and so forth — may be done through a token REST API.
Authentication to that REST API is via either cookie or bearer token in an ``Authorization`` header, the same as any other Science Platform API.
The browser-based user interface for creating and manipulating user tokens described in :ref:`Token authentication <token-auth>` is implemented on top of that REST API.

Any user authenticated with a token having ``user:token`` scope (given to all session tokens by default, but often not delegated to user tokens) can list, create, revoke, modify, and see the history for their own tokens.
Anyone in possession of a token can get the data associated with that token (its scopes, expiration, and so forth) and the identity data for the user associated with that token (full name if known, email address, UID, group membership, and so forth) via the token API by authenticating with that token.
This can be used by services making or processing subrequests (see :ref:`Subrequest authentication <subrequest-auth>`).

Administrators with a token having ``admin:token`` scope can take all of those same actions on behalf of the user; can add, remove, or list administrators (whose session tokens receive the ``admin:token`` scope when they authenticate); can create new tokens on behalf of arbitrary users; and can do global queries on all tokens, token history, and any other data stored by the authentication service.
Administrators cannot get the secret portion of existing tokens without having possession of the token.

References
==========

DMTN-193_
    Discussion of web security for the Science Platform.
    This is primarily about implementation details, but the designs here for filtering some request headers and for using multiple domains for Science Platform services to limit the possible damage from credential leakage are relevant to the overall design.

DMTN-224_
    The implementation details of the Science Platform identity management system.

DMTN-225_
    Metadata gathered and stored for each user, including constraints such as valid username and group name patterns and UID and GID ranges.

DMTN-235_
    Lists and defines the scopes used by the Science Platform.

RDO-013_
    The Vera C. Rubin Observatory Data Policy, which defines who will have access to Rubin Observatory data.

SQR-069_
    History and analysis of the decisions made during design and implementation of the Science Platform identity management system.

.. _DMTN-193: https://dmtn-193.lsst.io/
.. _DMTN-224: https://dmtn-224.lsst.io/
.. _DMTN-225: https://dmtn-225.lsst.io/
.. _DMTN-235: https://dmtn-235.lsst.io/
.. _RDO-013: https://docushare.lsst.org/docushare/dsweb/Get/RDO-13/
.. _SQR-069: https://sqr-069.lsst.io/

The `references section of DMTN-224 <https://dmtn-224.lsst.io/#references>`__ has a more complete list of tech notes related to RSP identity management, including historical and implementation tech notes.
