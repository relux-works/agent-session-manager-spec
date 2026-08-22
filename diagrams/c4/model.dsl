model {
    operator = person "Operator" "Software developer running AI agents."

    ax = softwareSystem "Agent Session Manager (ax)" "Manages durable terminal sessions and AI agent task-boards across a mesh." {
        ax_cli = container "ax CLI" "Main Go CLI for session launch, sync, attach, takeover." "Go"
        daemon = container "ax Daemon" "User service (launchd/systemd/Scheduled Task) for periodic sync/health." "Go"
        providers = container "Provider Plugins" "Executable plugins (ax-provider-<id>) via JSON-over-stdio." "Binary"
        terminal = container "Terminal Backend" "tmux (macOS/Linux/WSL2) or process/ConPTY (Windows)." "System"
        local_db = container "Local Index" "Derived transactional index of immutable records." "SQLite" {
            tags "Database"
        }
        storage = container "Immutable Storage" "Content-addressed blobs and identity-addressed records." "File System" {
            tags "Database"
        }
    }
    
    tb_session = softwareSystem "Task-Board / Session Manager" "Distinct persistence and ownership boundary for AI agents."
    
    mesh = softwareSystem "Mesh Network" "Tailscale / OpenSSH trusted mesh transport."
    native_stores = softwareSystem "Native Provider Stores" "e.g., ~/.claude/projects, ~/.codex/sessions."

    !include relationships.dsl
}
