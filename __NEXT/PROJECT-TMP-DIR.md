/zen:planner
Add a `tmp` dir in the project root for testing and add it .gitignore. 
Add or modify Makefile commands to use this `tmp` dir for creating test project dirs. A `create-test-project` command can:
1. make a new tmpdir inside `tmp`
2. `cd` to it
3. `git init` and commit a placeholder file
Confirm that you would be able to use this `tmp` test dir and make command(s) for your own testing and debugging of the `prj` workflow commands