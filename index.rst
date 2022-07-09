Abstract
========

The identity management, authentication, and authorization component of the Rubin Science Platform is responsible for maintaining a list of authorized users and their associated identity information, authenticating their access to the Science Platform, and determining which services they are permitted to use.
This tech note describes the high-level design of that system and summarizes its desired features and capabilities, independent of choice of implementation.

This document is part of a three-document series describing implementation of identity management for the Rubin Science Platform.
The other two documents in that series are DMTN-224_, which describes the chosen identity management implementation, and SQR-069_, which provides a history and analysis of the decisions underlying the design and implementation.

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

User identity
=============

Users of a general access Science Platform deployment will access it via a federated identity provider.
They will authenticate using their account at their local institution, or their choice of a cloud identity provider such as GitHub or Google.
That institution will, in turn, release their identity to the Science Platform.
This source of identity is discussed in detail in :ref:`Federated identity <federated-identity>`.

Restricted access deployments of the Science Platform may chose from one of two sources of user identity:

.. rst-class:: compact

- GitHub
- Local identity provider supporting OpenID Connect

If GitHub is used as the identity provider, identity information will be taken from the user's GitHub account information, and the user's groups (see :ref:`Groups <groups>`) will be derived from the user's organization and team memberships on GitHub.
If a local identity provider is used, identity and group information will be read either from an associated LDAP server or from the identity token provided by the OpenID Connect authentication process.

In all cases, the user identity provider is also the primary source of user authentication.
After a user has authenticated via their identity provider, they may create an authentication token for programmatic access to the Science Platform (see :ref:`Tokens <tokens>`).
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
This decision will usually based primarily on their institutional affiliation, but possibly based on other data gathered outside of the identity management system.
Approvers may be Science Platform administrators or delegates who have the knowledge and authority to verify the data rights of a particular community of users.
Once the user is approved, their account will become active and they will be able to use it to access the Science Platform.

Once a user's account is active, they may add additional identities to that same account.
Those identities may be from other identity providers that are part of a supported identity federation, or cloud identity providers.
GitHub and Google, in particular, will be supported as identity providers.
All identities added to the same account are treated as equivalent for authentication purposes; the user can use any of the linked identity providers to authenticate to the Science Platform.

Note that users can use GitHub or Google as their authentication provider for initial enrollment, although in that case the identity provider will probably not release any information useful for determining their data rights, and the approver will probably need information from outside the scope of the identity management system.

Once the user's account is active, they can change their preferred name or email address whenever they wish.
If they change their email address, they will have to verify that they can receive email at the new email address.

.. _groups:

Groups
======

.. _tokens:

Tokens
======

.. _remaining-work:

Remaining work
==============

The following requirements should be satisfied by the Science Platform identity management system, but are not yet part of the design.
The **IDM-XXXX** references are to requirements listed in SQR-044_, which may provide additional details.

.. rst-class:: compact

- Force two-factor authentication for administrators (IDM-0007)
- Force reauthentication to provide an affiliation (IDM-0009)
- Changing usernames (IDM-0012)
- Handling duplicate email addresses (IDM-0013)
- Email notification of federated identity and user token changes (IDM-0206)
- Freezing accounts (IDM-1001)
- Deleting accounts (IDM-1002)
- Setting an expiration date on an account (IDM-1003, IDM-1301)
- Notifying users of upcoming account expiration (IDM-1004)
- Notifying users about email address changes (IDM-1101)
- User class markers (IDM-1103, IDM-1310)
- Quotas (IDM-1200, IDM-1201, IDM-1202, IDM-1203, IDM-1303, IDM-1401, IDM-1402, IDM-2100, IDM-2101, IDM-2102, IDM-2103, IDM-2201, IDM-3003)
- Administrator verification of email addresses (IDM-1302)
- User impersonation (IDM-1304, IDM-1305, IDM-2202)
- Review newly-created accounts (IDM-1309)
- Merging accounts (IDM-1311)
- Affiliation-based groups (IDM-2001)
- Expiration of group membership (IDM-2005)
- Groups owned by other groups (IDM-2009)

References
==========

DMTN-224_
    The implementation details of the Science Platform identity management system.

DMTN-225_
    Metadata gathered and stored for each user, including constraints such as valid username and group name patterns and UID and GID ranges.

RDO-013_
    The Vera C. Rubin Observatory Data Policy, which defines who will have access to Rubin Observatory data.

SQR-044_
    Draft requirements for the identity management system.
    This is neither complete nor entirely up-to-date, but it provides useful context and elaboration for some of the items listed in :ref:`Remaining work <remaining-work>`.

SQR-069_
    History and analysis of the decisions made during design and implementation of the Science Platform identity management system.

.. _DMTN-224: https://dmtn-224.lsst.io/
.. _DMTN-225: https://dmtn-225.lsst.io/
.. _RDO-013: https://docushare.lsst.org/docushare/dsweb/Get/RDO-13/
.. _SQR-044: https://sqr-044.lsst.io/
.. _SQR-069: https://sqr-069.lsst.io/

The `references section in DMTN-224 <https://dmtn-224.lsst.io/#references>`__ has a more complete list of tech notes related to RSP identity management, including historical and implementation tech notes.
