# Thunder Plugins Architecture: AppGateway, LaunchDelegate, App2AppProvider, AppNotifications

## Introduction

This document describes the planned architecture for a set of application-centric Thunder plugins: AppGateway, LaunchDelegate, App2AppProvider, and AppNotifications. It consolidates the patterns and best practices from Thunder’s core plugin and JSON-RPC infrastructure with the existing application management interfaces and utilities present in the project (notably the AppManager implementation and related helpers in the infrastructure repository). The goal is to provide a coherent overview of purpose, responsibilities, message shapes, parameter semantics, and lifecycle/interaction flows for these plugins so that they can be implemented consistently within the Thunder ecosystem.

### Scope

- High-level purpose and role of each plugin.
- Planned/known requests and responses, with parameter tables.
- Example interaction and initialization flows.
- Plugin lifecycle, configuration, security, and error handling considerations.
- Dependencies and interactions with existing components such as AppManager and Lifecycle/Package/Storage managers exposed by the infrastructure container.

This is a planning and architecture document grounded in the current Thunder codebase and container utilities. It does not declare features beyond what is supported by Thunder’s plugin framework and the referenced interfaces/utilities, and it highlights where behaviors are inferred from existing components (e.g., AppManager) that these plugins will integrate with.

## Architectural Foundations

### Thunder plugin and JSON-RPC patterns

Thunder (WPEFramework) is a plugin-based device abstraction layer. Plugins are self-contained C++ libraries implementing `WPEFramework::PluginHost::IPlugin`, loaded and managed by the plugin host server.

Key plugin lifecycle points:
- Initialize(IShell*): The host passes an `IShell` service pointer. Plugins read configuration and acquire required interfaces.
- Deinitialize(IShell*): The plugin releases references, unregisters notifications, and cleans up state.
- Information(): Plugins can publish metadata to consumers.

Plugins typically expose APIs over JSON-RPC by composing `PluginHost::JSONRPC` and registering methods/events. Thunder’s JSON-RPC dispatcher:
- Routes `Callsign.Version.Method` invocations to the plugin handler.
- Provides event subscription with `register`/`unregister` meta-methods (managed by the JSONRPC base).
- Supports validation callbacks to integrate with security/token-based authorization.
- Supports interface versioning (major/minor/patch) and multiple handler versions (for backward compatibility).

Thunder plugin configuration and execution modes:
- Per-plugin config files support common options including callsign, locator, classname, start mode, and root execution mode (Off, Local, Container, Distributed).
- Execution mode determines hosting (in-process, out-of-process, container, or distributed) without changing the client interaction.

Subsystems:
- Plugins may declare preconditions/terminations tied to subsystems (e.g., NETWORK, INTERNET). Thunder ensures activation/deactivation sequencing accordingly.

### Message transport and eventing

JSON-RPC request/response basics:
- Request: `{"jsonrpc":"2.0","id":<number>,"method":"<Callsign>.<Version>.<Method>","params":{...}}`
- Response (success): `{"jsonrpc":"2.0","id":<number>,"result":<payload-or-null>}`
- Response (error): `{"jsonrpc":"2.0","id":<number>,"error":{"code":<int>,"message":"<text>"}}`

Event subscription:
- Subscribe: `{"method":"<Callsign>.<Version>.register","params":{"event":"<eventName>","id":"<clientCallsign>"}}`
- Unsubscribe: `{"method":"<Callsign>.<Version>.unregister","params":{"event":"<eventName>","id":"<clientCallsign>"}}`
- Event delivery: `{"method":"<Callsign>.<Version>.<eventName>","params":{...}}`

Note on “success” fields: Some helper macros used in infrastructure components add a non-standard `"success"` field to results for legacy reasons. New implementations should follow Thunder’s JSON-RPC contract (use result or error), and prefer typed definitions generated from ThunderInterfaces for strong typing of params/results/events.

## Planned Plugins Overview

### AppGateway

#### Purpose and Role

AppGateway is a façade plugin that provides a cohesive, client-facing API for application lifecycle and intent-based interactions. It aggregates operations exposed by specialized providers (e.g., LaunchDelegate for lifecycle actions and App2AppProvider for intents) and routes client requests to the correct underlying provider(s). This yields a simplified surface area for clients while keeping internal responsibilities modular.

#### Responsibilities

- Expose a consolidated JSON-RPC API for app launch/close/terminate, installation queries, metadata/properties, and system app controls.
- Route requests to providers that implement the concrete actions (e.g., LaunchDelegate → AppManager).
- Surface read-only listing APIs for loaded/installed apps via underlying providers.
- Optionally centralize input validation, authorization checks, and response normalization.
- Maintain consistent versioning and events best practices across the “app” feature set.

#### Internal Dependencies

- LaunchDelegate (for app lifecycle control).
- App2AppProvider (for app-to-app intent messaging).
- AppNotifications (as the source of event streams) or direct subscription to event sources with re-publish.

### LaunchDelegate

#### Purpose and Role

LaunchDelegate bridges JSON-RPC lifecycle requests to the system’s application control backend, integrating with the existing `Exchange::IAppManager` implementation from the infrastructure container. It translates JSON-RPC method invocations into `IAppManager` calls and returns results in Thunder’s JSON-RPC format.

#### Responsibilities

- Map client lifecycle calls (launch, preload, close, terminate, kill) to `IAppManager` methods.
- Provide queries such as loaded/installed apps and app properties/metadata via `IAppManager`.
- Control system applications through `IAppManager` when available.
- Coordinate with AppNotifications on relevant lifecycle events.

#### Internal Dependencies

- `Exchange::IAppManager` (via `IShell->Root<Exchange::IAppManager>(...)`).
- Infrastructure services `IPackageInstaller`, `IStorageManager`, `IStore2` (indirectly, as employed by AppManager), no direct coupling required in the delegate.

### App2AppProvider

#### Purpose and Role

App2AppProvider provides an API for applications to send intents to other applications. It is a thin layer translating JSON-RPC intent messages into `IAppManager::SendIntent(...)`, allowing applications to communicate or request actions from other applications using defined intent semantics.

#### Responsibilities

- Expose a JSON-RPC method that forwards intents (recipient AppId and intent identifier).
- Optionally provide basic validation and authorization checks.
- Keep surface area deliberately small and focused on intent delivery.

#### Internal Dependencies

- `Exchange::IAppManager` for `SendIntent(...)`.

### AppNotifications

#### Purpose and Role

AppNotifications exposes application-related events to clients via JSON-RPC. It subscribes to `IAppManager` notifications and publishes JSON-RPC events to subscribed clients. Events include lifecycle state changes, app unload, launch request, and installation progress/status.

#### Responsibilities

- Subscribe to `IAppManager::INotification` and translate events to JSON-RPC event notifications.
- Offer JSON-RPC subscription management through the base `JSONRPC` methods (register/unregister).
- Maintain backward-compatible event naming and payload stability across versions.

#### Internal Dependencies

- `Exchange::IAppManager::INotification` event source (indirectly via the AppManager plugin implementation).

## Message API Reference

This section outlines planned JSON-RPC method sets and parameters based on the capabilities of `Exchange::IAppManager` and existing patterns. All methods follow the `Callsign.Version.Method` naming. The tables specify expected parameters and results. Unless otherwise stated, success responses return `result: null`; failures return a JSON-RPC `error` with code/message.

Where `IAppManager` returns JSON-encoded strings (e.g., listing APIs), the plugin may return the raw string for consistency with the current interfaces. Future iterations can lift these to typed arrays/objects once standardized in ThunderInterfaces.

### AppGateway Methods

AppGateway provides a consolidated surface that routes to LaunchDelegate and App2AppProvider.

#### appgateway.1.launch

- Description: Launch an application.
- Parameters:
  - appId (string, required): Application identifier.
  - intent (string, optional): Intent name/qualifier (may be empty).
  - launchArgs (string, optional): Launch arguments (opaque string).
- Result: null on success.

Example request:
```
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "AppGateway.1.launch",
  "params": { "appId": "com.example.App", "intent": "default", "launchArgs": "{}" }
}
```

#### appgateway.1.preload

- Description: Preload an application without making it active.
- Parameters:
  - appId (string, required)
  - launchArgs (string, optional)
- Result: object with optional error:
  - error (string, optional): Non-empty if preload reported an error.
- Notes: Mirrors `IAppManager::PreloadApp(..., string& error)`.

#### appgateway.1.close

- Description: Gracefully close an application.
- Parameters: appId (string, required)
- Result: null

#### appgateway.1.terminate

- Description: Terminate an application (forceful shutdown).
- Parameters: appId (string, required)
- Result: null

#### appgateway.1.kill

- Description: Kill an application process (last resort).
- Parameters: appId (string, required)
- Result: null

#### appgateway.1.getLoadedApps

- Description: Retrieve loaded apps (opaque JSON string from backend).
- Parameters: none
- Result: object
  - apps (string): Backend-provided JSON string describing loaded apps.

#### appgateway.1.getInstalledApps

- Description: Retrieve installed apps (opaque JSON string from backend).
- Parameters: none
- Result: object
  - apps (string): Backend-provided JSON string describing installed apps.

#### appgateway.1.isInstalled

- Description: Check if an app is installed.
- Parameters: appId (string, required)
- Result: object
  - installed (boolean): Installation status.

#### appgateway.1.getAppProperty

- Description: Get an app property value.
- Parameters:
  - appId (string, required)
  - key (string, required)
- Result: object
  - value (string): Property value.

#### appgateway.1.setAppProperty

- Description: Set an app property value.
- Parameters:
  - appId (string, required)
  - key (string, required)
  - value (string, required)
- Result: null

#### appgateway.1.getAppMetadata

- Description: Get metadata for an app.
- Parameters:
  - appId (string, required)
  - metaData (string, required): Metadata selector.
- Result: object
  - result (string): Backend-provided metadata string.

#### appgateway.1.startSystemApp / appgateway.1.stopSystemApp

- Description: Start/stop a system application.
- Parameters: appId (string, required)
- Result: null

#### appgateway.1.clearAppData

- Description: Clear a specific app's data.
- Parameters: appId (string, required)
- Result: null

#### appgateway.1.clearAllAppData

- Description: Clear data for all apps.
- Parameters: none
- Result: null

#### appgateway.1.getLimits

- Description: Get system limits for app lifecycle.
- Parameters: none
- Result: object
  - maxRunningApps (number)
  - maxHibernatedApps (number)
  - maxHibernatedFlashUsage (number)
  - maxInactiveRamUsage (number)

Notes:
- The AppGateway implementation routes the above to LaunchDelegate (lifecycle/property/metadata/system controls) and aggregates multi-field responses (e.g., limits) from multiple getters.

### LaunchDelegate Methods

LaunchDelegate implements the same lifecycle/property/metadata methods described in AppGateway but exposes them directly. Typical deployments may hide LaunchDelegate from external clients, preferring AppGateway as the façade. When exposed, the method names and parameters mirror those in AppGateway with a `LaunchDelegate.<version>.` prefix.

### App2AppProvider Methods

#### app2appprovider.1.sendIntent

- Description: Send an intent to an application.
- Parameters:
  - appId (string, required): Target application identifier.
  - intent (string, required): Intent name/qualifier.
- Result: null

Notes:
- This maps to `IAppManager::SendIntent(const string& appId, const string& intent)`.
- If intent payload needs to be supported in the future, that should be standardized in ThunderInterfaces; the current backend API accepts only an intent identifier.

### AppNotifications Events

AppNotifications publishes events that reflect backend application events. Clients subscribe via `register` and `unregister` as per Thunder JSON-RPC.

#### appnotifications.1.lifecyclestatechanged

- Payload:
  - appId (string)
  - appInstanceId (string)
  - newState (string/int): `Exchange::IAppManager::AppLifecycleState`
  - oldState (string/int): `Exchange::IAppManager::AppLifecycleState`
  - errorReason (string/int): if provided by backend
- Source: `handleOnAppLifecycleStateChanged(...)` from AppManager implementation.

#### appnotifications.1.unloaded

- Payload:
  - appId (string)
  - appInstanceId (string)
- Source: `handleOnAppUnloaded(...)`.

#### appnotifications.1.launchrequest

- Payload:
  - appId (string)
  - intent (string)
  - source (string)
- Source: `handleOnAppLaunchRequest(...)`.

#### appnotifications.1.installationstatus

- Payload:
  - json (string): Opaque JSON string as provided by the package manager notification.
- Source: `OnAppInstallationStatus(const string& jsonresponse)`.

Example subscription:
```
{
  "jsonrpc":"2.0",
  "id": 42,
  "method":"AppNotifications.1.register",
  "params":{"event":"lifecyclestatechanged","id":"com.example.Client"}
}
```

## Initialization and Lifecycle Flows

### Shared initialization pattern

- On activation, each plugin:
  1. Reads config via `IShell`.
  2. Initializes JSON-RPC handlers and registers version metadata if applicable.
  3. Acquires backend interfaces as needed via `IShell->Root<...>(connectionId, timeout, "<ImplementationName>")`.
  4. Registers for notifications (AppNotifications) or retains references for invocation (LaunchDelegate).
  5. Handles cleanup in `Deinitialize`: unregister notifications, release interfaces, release `IShell`, and if out-of-process, terminate remote connection.

### Launch via AppGateway and LaunchDelegate

```
sequenceDiagram
    participant C as Client
    participant T as Thunder JSON-RPC
    participant AG as AppGateway
    participant LD as LaunchDelegate
    participant AM as AppManager (backend)

    C->>T: AppGateway.1.launch(appId,intent,launchArgs)
    T->>AG: Dispatch Invoke()
    AG->>LD: Launch(appId,intent,launchArgs)
    LD->>AM: IAppManager::LaunchApp(appId,intent,launchArgs)
    AM-->>LD: hresult (success/failure)
    LD-->>AG: return
    AG-->>T: JSON-RPC result
    T-->>C: Response

    AM-->>AppNotifications: IAppManager::INotification (state changed)
    AppNotifications-->>T: appnotifications.1.lifecyclestatechanged
    T-->>C: Event (if subscribed)
```

### Plugin initialization and event subscription (generic)

```
sequenceDiagram
    participant Host as Thunder Host
    participant Plugin as AppNotifications
    participant AM as AppManager (backend)
    participant Client as Client

    Host->>Plugin: Initialize(IShell*)
    Plugin->>AM: Register(INotification)
    Host->>Plugin: Activate
    Client->>Plugin: register(event,id)
    Plugin-->>Client: event status (internal)
    AM-->>Plugin: OnAppLifecycleStateChanged(...)
    Plugin-->>Client: appnotifications.1.lifecyclestatechanged
```

## Configuration and Execution Modes

All plugins support standard Thunder plugin configuration:

- callsign, locator, classname
- startmode (UNAVAILABLE, DEACTIVATED, SUSPENDED, RESUMED)
- autostart (deprecated; prefer startmode)
- configuration.root.mode (Off, Local, Container, Distributed)
- communicator (optional private COM-RPC socket)
- precondition/termination (subsystems)
- Versions and webui as needed

Notes:
- Execution mode influences hosting but not the JSON-RPC surface.
- Container mode requires the presence of a container spec under the configured paths; Thunder does not generate container specs automatically.

## Security and Authorization

- Use `PluginHost::JSONRPC` token validation to gate method invocations (classification: VALID/INVALID/DEFERRED).
- Integrate with a security plugin that supplies and validates tokens.
- Ensure sensitive operations (e.g., terminate/kill) verify caller authorization and optional policy config.

## Error Handling

- Map backend `Core::hresult` to JSON-RPC:
  - Success: `result: null` (or typed result for getters).
  - Failure: JSON-RPC error object with `code` (mapped from `Core::ERROR_*`) and `message`.
- Avoid legacy `"success": true/false` fields in results; use standardized JSON-RPC result/error.
- For getters that return opaque JSON strings (e.g., lists), return exactly as provided until standardized typed interfaces are available.

## Dependencies and Interactions

- AppGateway: depends on LaunchDelegate and App2AppProvider (conceptually) and may be co-located or route via `IShell` to their interfaces.
- LaunchDelegate: depends on AppManager (backend `Exchange::IAppManager`) to execute lifecycle operations; does not have to understand Package/Storage internals.
- App2AppProvider: depends on AppManager (`SendIntent`).
- AppNotifications: subscribes to AppManager notifications, publishes JSON-RPC events.

Backend components in the infrastructure container involved via AppManager include:
- LifecycleManager, RuntimeManager, PackageManager, StorageManager, PersistentStore. These are composed beneath `IAppManager` so plugin implementations can remain backend-agnostic.

## Example Requests and Responses

### Launch app

Request:
```
{
  "jsonrpc":"2.0",
  "id": 1,
  "method":"AppGateway.1.launch",
  "params":{"appId":"com.example.App","intent":"default","launchArgs":"{}"}
}
```

Success response:
```
{ "jsonrpc":"2.0", "id": 1, "result": null }
```

Failure response:
```
{ "jsonrpc":"2.0", "id": 1, "error": {"code": 22, "message": "Invalid appId"} }
```

### Get installed apps

Request:
```
{ "jsonrpc":"2.0", "id": 2, "method":"AppGateway.1.getInstalledApps" }
```

Response (opaque backend JSON string):
```
{
  "jsonrpc":"2.0",
  "id": 2,
  "result": { "apps": "[{\"id\":\"com.example.App\",\"version\":\"1.0.0\"}]" }
}
```

### Send intent

Request:
```
{
  "jsonrpc":"2.0",
  "id": 3,
  "method":"App2AppProvider.1.sendIntent",
  "params":{"appId":"com.example.Receiver","intent":"open-settings"}
}
```

Response:
```
{ "jsonrpc":"2.0", "id": 3, "result": null }
```

### Subscribe to lifecycle events

Request:
```
{
  "jsonrpc":"2.0",
  "id": 4,
  "method":"AppNotifications.1.register",
  "params":{"event":"lifecyclestatechanged","id":"com.example.Client"}
}
```

Event payload example:
```
{
  "jsonrpc":"2.0",
  "method":"AppNotifications.1.lifecyclestatechanged",
  "params":{
    "appId":"com.example.App",
    "appInstanceId":"abc-123",
    "newState":"Running",
    "oldState":"Launching",
    "errorReason":"None"
  }
}
```

## Versioning Strategy

- Use `JSONRPC::RegisterVersion("<Interface>", major, minor, patch)` to record the exposed interface version.
- Maintain backward compatibility by using multiple handlers if breaking changes are introduced (see `JSONRPC::CreateHandler(versions)`).
- Keep event names and payloads stable across versions; introduce new events for incompatible changes.

## Appendix: Parameter Tables

### Launch-related

| Method                     | Param           | Type   | Required | Description                                      |
|---------------------------|-----------------|--------|----------|--------------------------------------------------|
| AppGateway.1.launch       | appId           | string | yes      | Target application identifier                     |
|                           | intent          | string | no       | Intent/entry point qualifier                      |
|                           | launchArgs      | string | no       | Opaque launch arguments                           |
| AppGateway.1.preload      | appId           | string | yes      | Target application identifier                     |
|                           | launchArgs      | string | no       | Opaque launch arguments                           |
| AppGateway.1.close        | appId           | string | yes      | Target application identifier                     |
| AppGateway.1.terminate    | appId           | string | yes      | Target application identifier                     |
| AppGateway.1.kill         | appId           | string | yes      | Target application identifier                     |

### Properties and metadata

| Method                         | Param     | Type   | Required | Description                         |
|--------------------------------|-----------|--------|----------|-------------------------------------|
| AppGateway.1.getAppProperty    | appId     | string | yes      | Application identifier              |
|                                | key       | string | yes      | Property key                        |
| AppGateway.1.setAppProperty    | appId     | string | yes      | Application identifier              |
|                                | key       | string | yes      | Property key                        |
|                                | value     | string | yes      | Property value                      |
| AppGateway.1.getAppMetadata    | appId     | string | yes      | Application identifier              |
|                                | metaData  | string | yes      | Metadata selector                   |

### Listing and status

| Method                         | Param     | Type   | Required | Description                                   |
|--------------------------------|-----------|--------|----------|-----------------------------------------------|
| AppGateway.1.getLoadedApps     | —         | —      | —        | Returns `apps` as opaque JSON string          |
| AppGateway.1.getInstalledApps  | —         | —      | —        | Returns `apps` as opaque JSON string          |
| AppGateway.1.isInstalled       | appId     | string | yes      | Returns `installed` boolean                   |
| AppGateway.1.getLimits         | —         | —      | —        | Returns maxRunningApps, maxHibernatedApps, etc.|

### System apps and data

| Method                         | Param     | Type   | Required | Description                         |
|--------------------------------|-----------|--------|----------|-------------------------------------|
| AppGateway.1.startSystemApp    | appId     | string | yes      | Start a system app                  |
| AppGateway.1.stopSystemApp     | appId     | string | yes      | Stop a system app                   |
| AppGateway.1.clearAppData      | appId     | string | yes      | Clear a specific app’s data         |
| AppGateway.1.clearAllAppData   | —         | —      | —        | Clear data for all applications     |

### App-to-App

| Method                               | Param   | Type   | Required | Description                           |
|--------------------------------------|---------|--------|----------|---------------------------------------|
| App2AppProvider.1.sendIntent         | appId   | string | yes      | Target application identifier          |
|                                      | intent  | string | yes      | Intent name/qualifier                  |

### Events (AppNotifications)

| Event                                 | Field          | Type    | Description                                        |
|---------------------------------------|----------------|---------|----------------------------------------------------|
| lifecyclestatechanged                 | appId          | string  | Application identifier                             |
|                                       | appInstanceId  | string  | App instance identifier                            |
|                                       | newState       | string/int | New lifecycle state (backend enum)              |
|                                       | oldState       | string/int | Old lifecycle state (backend enum)              |
|                                       | errorReason    | string/int | Error reason if provided                        |
| unloaded                              | appId          | string  | Application identifier                             |
|                                       | appInstanceId  | string  | App instance identifier                            |
| launchrequest                         | appId          | string  | Application identifier                             |
|                                       | intent         | string  | Requested intent                                   |
|                                       | source         | string  | Request source                                     |
| installationstatus                    | json           | string  | Opaque JSON string from backend/package manager    |

## Implementation Notes

- Providers should acquire backend interfaces in `Initialize` using `IShell->Root<...>(...)` with an appropriate implementation name (e.g., `"AppManagerImplementation"`).
- Ensure that references are released and remote connections are terminated in `Deinitialize`.
- Prefer ThunderInterfaces-generated JSON wrappers for stable API types over ad-hoc JSON structures.
- Keep the façade (AppGateway) minimal in logic: delegate to providers and normalize responses.

## Conclusion

This architecture organizes application-centric functionality into focused providers (LaunchDelegate, App2AppProvider) surfaced through a simple façade (AppGateway), with AppNotifications providing a consistent event stream. The design adheres to Thunder’s plugin, configuration, and JSON-RPC eventing patterns and leverages the existing AppManager implementation in the infrastructure container. It should enable a straightforward implementation path and a maintainable, versioned API surface for clients.
