views {
    systemContext ax "SystemContext" "System Context diagram for Agent Session Manager." {
        include *
        autoLayout tb
    }

    container ax "ContainerContext" "Container diagram for AX state, directory, terminal-runtime, enrichment, continuation, and cloning boundaries." {
        include operator automation ax_cli directory cloning daemon aqua_broker providers terminal_runtime local_db storage
        autoLayout tb
    }

    component terminal_runtime "TerminalBackendComponents" "AX authority and host-local TerminalBackend module boundary." {
        include ax_cli terminal_controller terminal_registry terminal_backend tmux_backend conpty_backend pane_entrypoint aqua_broker providers
        autoLayout tb
    }

    !include styles.dsl
}
