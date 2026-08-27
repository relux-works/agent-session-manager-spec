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
        daemon = container "ax Daemon" "Optional user service for periodic sync, health, inventory, and enrichment scheduling." "Go"
        providers = container "Provider Plugins" "Executable plugins (ax-provider-<id>) via JSON-over-stdio." "Binary"
        terminal = container "Terminal Backend" "tmux (macOS/Linux/WSL2) or process/ConPTY (Windows)." "System"
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
