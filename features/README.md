# Executable acceptance scenarios

Write valuable observable business behaviors in `<domain>/<behavior>.feature`
after human acceptance-criteria approval. Bind them using pytest-bdd in
`steps/test_<behavior>.py`; define Given/When/Then fixtures in that module or
a nearby `conftest.py`. Shared application and database fixtures come from
the repository's root `conftest.py`.

`just test` includes this suite once. `just bdd` runs only this directory.
No feature files is a valid initial state; unbound scenarios, missing steps
and collection errors are failures.
Keep implementation details out of scenario text. Do not create placeholder
scenarios merely to populate this directory.
