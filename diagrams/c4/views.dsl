views {
    systemContext ax "SystemContext" "System Context diagram for Agent Session Manager." {
        include *
        autoLayout tb
    }

    container ax "ContainerContext" "Container diagram for Agent Session Manager." {
        include *
        autoLayout tb
    }

    !include styles.dsl
}
