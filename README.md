![Banner](banner.png)

# dso-code-comment-remover
Removes comments from source code files to protect intellectual property or reduce the risk of information leakage. - Focused on Tools for sanitizing and obfuscating sensitive data within text files and structured data formats

## Install
`git clone https://github.com/ShadowGuardAI/dso-code-comment-remover`

## Usage
`./dso-code-comment-remover [params]`

## Parameters
- `-h`: Show help message and exit
- `--remove-all`: No description provided
- `--log-level`: Set the logging level.

## License
Copyright (c) ShadowGuardAI

## Behaviour notes
- A run is refused at exit 1 when the output path resolves to the input file, including ./ alias and symlink spellings.
- Comments are stripped with a string aware scanner for the syntax family of the file. C style files (.c, .h, .cpp, .cc, .cxx, .hpp, .java, .js, .jsx, .ts, .tsx, .cs, .go, .rs, .php, .swift, .kt, .kts, .scala, .m, .mm) use // line comments and /* */ block comments. Hash files (.py, .sh, .bash, .rb, .pl, .pm, .r, .jl, .ps1, .yaml, .yml, .toml) use # comments. Dash files (.sql, .lua, .hs) use -- comments and /* */ block comments. Other extensions use //, /* */, and # comments, and -- is never treated as a comment start outside the dash family, so a -- operator is left alone. Comment markers inside string literals are never treated as comments in any family.
- Copyright notices are preserved only when they are themselves comments. A code line that mentions Copyright is left in place once and is not duplicated. With --remove-all, copyright comments are removed as well.
- When no comments are removed, including for an empty input, the tool prints a plain no comments removed line, writes no output file, and exits 1.
