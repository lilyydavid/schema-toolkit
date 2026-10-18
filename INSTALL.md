# INSTALL.md: instructions for Claude Code

If a user asked you to install this toolkit, do these steps in order.

1. **Clone** (skip if it exists): `git clone https://github.com/lilydavida/schema-toolkit.git ~/schema-toolkit`
2. **Install the CLI:** `pip install -e ~/schema-toolkit`. The only dependency is SQLAlchemy.
3. **Install the slash commands** globally, so they work in every project:
   `mkdir -p ~/.claude/commands && cp ~/schema-toolkit/.claude/commands/*.md ~/.claude/commands/`
4. **Run the demo** so the user sees it work with no database: `bash ~/schema-toolkit/examples/demo/run_demo.sh`.
   Show them `examples/demo/output/SCHEMA.example.md` and the QA output (`05a_qa_leaky.txt` vs `05b_qa_clean.txt`).
5. **Tell the user** the toolkit is installed. Type `/schema-init` in the folder where their `SCHEMA.md` should live.
6. **Start the interview now.** Ask 2-3 short questions together: what the company sells, which database it runs on, and
   the questions the business keeps asking. Then propose 5-6 domains and the first tables to profile, following `/schema-init`.
7. **Never ask for database credentials, and don't connect to the database yourself.** Propose commands; the user runs
   them and pastes the output back. Only run `schemakit` against a database if the user explicitly allows it, using a read-only role.
