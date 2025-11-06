# Thunder

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0) 

![Linux Build](https://github.com/rdkcentral/Thunder/actions/workflows/Build%20Thunder%20on%20Linux.yml/badge.svg) ![Windows Build](https://github.com/rdkcentral/Thunder/actions/workflows/Build%20Thunder%20on%20Windows.yml/badge.svg) ![Unit Test](https://github.com/rdkcentral/Thunder/actions/workflows/Test%20Thunder.yml/badge.svg)


Thunder (also known as WPEFramework) is an open-source plugin-based device abstraction layer, where business functionality can be implemented as plugins and applications can query and control those plugins. Using Thunder provides a consistent interface-driven development model for both plugins and client applications, with an RPC engine that is suited to both web-based and native apps.

Designed from the ground up for embedded platforms and written in C++11, Thunder can be run on even the most low-power of devices (including ARM and MIPS-based platforms).

# Documentation

All documentation and build instructions for Thunder can be found here: [Documentation](https://rdkcentral.github.io/Thunder/)

# Copyright and License

Thunder is Copyright 2018 Metrological and licensed under the Apache License, Version 2.0. See the LICENSE and NOTICE files in the top level directory for further details.

## Quick start (Preview Node server)

This repository primarily contains the Thunder C++ sources. For environments that expect a long-running web process to start, a minimal Node.js HTTP server is included to provide a simple, dependency-free start command.

- Prerequisite: Node.js 16+ (no additional npm packages required)
- Start (from the repository root):
  - cd Thunder-712
  - npm start

Server details:
- Binds to 0.0.0.0 and listens on the PORT environment variable or 3000 by default.
- Health check endpoint: GET /health returns {"status":"ok"}.

A Procfile is included with "web: npm start" for platforms that require it.