return {
    "milanglacier/minuet-ai.nvim",
    opts = {
        -- Your configuration options here
        virtualtext = {
            -- auto_trigger_ft = { "lua", "python" },
            auto_trigger_ft = {},
            keymap = {
                -- accept whole completion
                accept = "<A-p>",
                -- accept one line
                accept_line = "<A-l>",
                -- accept n lines (prompts for number)
                -- e.g. "A-z 2 CR" will accept 2 lines
                accept_n_lines = "<A-z>",
                -- Cycle to prev completion item, or manually invoke completion
                prev = "<A-[>",
                -- Cycle to next completion item, or manually invoke completion
                next = "<A-]>",
                dismiss = "<A-e>",
            },
        },
        provider = "openai_fim_compatible",
        provider_options = {
            openai_fim_compatible = {
                api_key = "DEEPSEEK_API_KEY",
                name = "deepseek",
                optional = {
                    max_tokens = 512,
                    top_p = 0.9,
                },
            },
        },
    },
}
