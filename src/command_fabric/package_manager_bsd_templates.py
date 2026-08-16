# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""BSD package metadata templates for Mekong CLI."""

from __future__ import annotations


def freebsd_port_makefile(command_count: int) -> str:
    return f"""PORTNAME=	mekong-cli
DISTVERSION=	0.0.0
CATEGORIES=	devel python

MAINTAINER=	support@mekongmind.com
COMMENT=	Mekong command fabric CLI with {command_count} command definitions
WWW=		https://github.com/longtho638-jpg/mekong-cli

LICENSE=	BSL11

USES=		python
USE_PYTHON=	autoplist pep517

GH_ACCOUNT=	longtho638-jpg
GH_PROJECT=	mekong-cli
USE_GITHUB=	yes

.include <bsd.port.mk>
"""


def openbsd_port_makefile(command_count: int) -> str:
    return f"""COMMENT =	Mekong command fabric CLI with {command_count} command definitions

DISTNAME =	mekong-cli-0.0.0
CATEGORIES =	devel

HOMEPAGE =	https://github.com/longtho638-jpg/mekong-cli

MAINTAINER =	Mekong <support@mekongmind.com>

PERMIT_PACKAGE =	Yes

MODULES =	lang/python
MODPY_PYBUILD =	poetry-core

WANTLIB +=	c pthread

.include <bsd.port.mk>
"""


def netbsd_pkgsrc_makefile(command_count: int) -> str:
    return f"""DISTNAME=	mekong-cli-0.0.0
CATEGORIES=	devel python
MASTER_SITES=	${{MASTER_SITE_GITHUB:=longtho638-jpg/}}
GITHUB_PROJECT=	mekong-cli
GITHUB_TAG=	v${{PKGVERSION_NOREV}}

MAINTAINER=	support@mekongmind.com
HOMEPAGE=	https://github.com/longtho638-jpg/mekong-cli
COMMENT=	Mekong command fabric CLI with {command_count} command definitions
LICENSE=	business-source-license-1.1

PYTHON_VERSIONS_INCOMPATIBLE=	27

.include "../../lang/python/wheel.mk"
.include "../../mk/bsd.pkg.mk"
"""


__all__ = ["freebsd_port_makefile", "netbsd_pkgsrc_makefile", "openbsd_port_makefile"]
