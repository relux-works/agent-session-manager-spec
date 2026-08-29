model {
    operator = person "Operator" "Software developer running AI agents."
    automation = person "Automation / Agent" "Uses typed directory queries and guarded mutations."

    ax = softwareSystem "Agent Session Manager (ax)" "Manages durable terminal sessions and AI agent task-boards across a mesh." {
        ax_cli = container "ax CLI and Session Browser TUI" "Human command, browsing, selection, confirmation, launch, and attach surfaces." "Go"
        directory = container "Directory Control Plane" "Discovery, disclosure, catalog, lineage, enrichment, query, and continuation policy without session or workspace authority." "Go" {
            directory_controller = component "Directory Controller" "Routes policy-checked directory operations."
            catalog = component "Catalog and Freshness" "Rebuilds deterministic global views and freshness from immutable source-authoritative records."
            lineage = component "Conversation Lineage" "Derives visible conversation groups, evidence links, ambiguity, and explicit resolutions."
            enrichment = component "Enrichment Scheduler" "Schedules idempotent exact-head annotation jobs under immutable profiles and disclosure policy."
            continuation = component "Continuation Planner" "Creates content-addressed pure plans and delegates confirmed effects to existing AX and cloning transactions."
            directory_node = component "Directory Node" "Source-local discovery, bounded preview, exact-head reads, runtime observation, and record publication."
            enrichment_worker = component "Sandboxed Enrichment Worker" "Produces bounded typed annotation candidates without AX, provider, shell, or mutation authority."
        }
        cloning = container "Session Cloning Core" "Captures, canonicalizes, projects, validates, and publishes cross-environment continuation lineage." "Go + Session Adapter 1.0"
        daemon = container "Background Control Plane" "Optional service for sync, health, inventory, and enrichment; cannot create a credential-dependent macOS tmux server." "Go"
        aqua_broker = container "macOS Aqua Terminal Broker" "Minimal same-user GUI-realm broker that creates and attests the dedicated AX tmux server and provider-auth readiness." "Go + launchd agent"
        providers = container "Provider Plugins" "Executable plugins (ax-provider-<id>) via JSON-over-stdio." "Binary"
        terminal_runtime = container "Terminal Runtime Core" "AX controller, backend registry, and transport-independent backend boundary. Terminal backends remain host-local presentation/process hosts below AX authority." "Go + native adapters" {
            terminal_controller = component "AX Terminal Controller" "Owns LogicalSession identity and lineage, Owner/Replica, leases and fencing, provider lifecycle/native state, workspaces, checkpoints/evidence, task-board integration, mesh, and takeover."
            terminal_registry = component "Terminal Backend Registry" "Validates backend identity, implementation and semantic-contract versions, platform availability, capabilities, and conformance evidence before activation."
            terminal_backend = component "TerminalBackend Boundary" "Owns one host-local TerminalInstance: delegated PTY/process hosting, presentation/attach/reconnect, local IPC, and process observation only."
            tmux_backend = component "Built-in tmux Backend" "Mandatory Unix implementation for macOS, Linux, and WSL2 using a dedicated private -S server; never the ambient/default server."
            conpty_backend = component "Built-in ConPTY Backend" "Native-Windows implementation under the same TerminalBackend semantics without claiming tmux-equivalent durability."
            pane_entrypoint = component "AX Pane Entrypoint" "The only durable backend-hosted entrypoint: exactly ax pane SESSION_ID under AX authorization."
        }
        local_db = container "Derived SQLite Index" "Rebuildable transactional index for AX state, directory catalog, and search." "SQLite" {
            tags "Database"
        }
        storage = container "Immutable AX and Directory Records" "Content-addressed blobs plus identity-addressed AX, cloning, and directory records." "File System" {
            tags "Database"
        }
    }
    
    tb_session = softwareSystem "Task-Board / Session Manager" "Distinct persistence and ownership boundary for AI agents."
    
    mesh = softwareSystem "Mesh Network" "Tailscale / OpenSSH trusted mesh transport."
    native_stores = softwareSystem "Native Provider Stores" "Source-local Claude, Codex, and future environment stores; transcripts and credentials are not directory records."

    !include relationships.dsl
}
