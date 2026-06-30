# Conventions

## Code Style

### Python (Backend)
- **Formatter**: Black (line length 88)
- **Linter**: Ruff
- **Type hints**: Required on function signatures
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes
- **Imports**: stdlib → third-party → local (one blank line between groups)
- **Docstrings**: Google style, only on public functions/classes

### JavaScript/JSX (Frontend)
- **Formatter**: Prettier
- **Naming**: `camelCase` for functions/variables, `PascalCase` for components
- **Components**: One component per file, named exports
- **State**: useState for local, custom hooks for shared logic

## File Naming

- Python modules: `snake_case.py`
- React components: `PascalCase.jsx`
- Test files: `test_<module>.py`
- Config files: lowercase with dots (`docker-compose.yml`)

## Git

We use [git](https://git-scm.com/) for version control with [GitHub](https://github.com).

### Commits

Commit messages:

* Always written in English
* Normally a single line (though we know more could be better)
* The first line is formed with a **type**, a **context** and a **description**

  ```
  type(context): description
  ```

The line should not exceed 100 characters so it reads well on GitHub.

### Type

The type helps us classify commits. The types we use are:

* **feat**: A new feature
* **fix**: A bug fix
* **docs**: Documentation changes
* **style**: Changes that do not affect code meaning (spacing, indentation, etc.)
* **refactor**: A code change that neither adds a feature nor fixes a bug
* **perf**: Code changes that only improve performance
* **test**: Adding or fixing tests
* **chore**: Changes to the build process and auxiliary tools

### Context

The context is a word referencing the part of the code or functionality affected by the commit. It must be written in `kebab-case`, e.g.: `user-signup`

Optionally, you can add information about the specific component affected. If added:

* It must go after the context, separated by a slash (`/`). E.g.: `api/LoginService`
* The modified component name must use the same format as in the code (e.g. `CamelCase` if it's a Ruby class).

### Description

* Use the imperative mood in English: "change" not "changed" nor "changes"
* Separated by a space from the context
* No capital letter at the beginning
* No period (`.`) at the end

### Branches and Pull Requests

Features are developed on a new branch and merged via a pull request to master.

### Example

The following commit solves a bug in the `SignUpForm` component of an app's frontend, where validation feedback on username availability was not being shown:

```
fix(ui/SignUpForm): validate username availability

The `SignUpForm` component wasn't validating the availability of the `username` field and only displayed a `couldn't create account` error on submit.

This commit adds an asynchronous validation when typing on the field so the user will know if the username is available before completing further fields.
```

### Rebase

To keep commits organized, we use fixups and rebase to maintain a clean history.

### No secrets

Never commit secrets or keys. Use environment variables.

## Project Structure Rules

- Backend business logic stays in modules (`etl/`, `categorizer/`), not in route handlers
- API routes only validate input, call modules, format output
- Frontend components are presentational; logic lives in hooks or api layer
- Tests mirror source structure: `backend/tests/test_etl.py` tests `backend/etl/`

## Clean Code

### Separation of Concerns

* Single responsibility per method/class.
* Each function does one thing.

### Error Handling

* Use exceptions instead of error codes.
* Write the happy path first, handle errors separately.
* Do not return or pass `null`.
* Exceptions must provide enough context to understand the error.

### Code Without Comments

* Code should be self-documenting through clear names and structure.
* If you need a comment, the code is not clear enough — refactor it.

### Names

* Use names that reveal intent.
* Use pronounceable and searchable names.
* Class names must be nouns.
* Do not use Hungarian notation prefixes.

### Functions

* Small (ideally under 20 lines).
* Do one thing.
* One level of abstraction per function.
* Avoid more than 2 or 3 parameters.
* No hidden side effects.
* Prefer exceptions over error codes as return values.
* DRY principle.

### Objects and Data Structures

* Objects hide data and expose behavior.
* Data structures expose data and have little behavior.
* Avoid the Law of Demeter: an object should not know the internals of other objects.

### Boundaries

* Wrap third-party code behind your own abstractions.
* Define clear interfaces at system boundaries to avoid coupling internal code to external details.

### Tests

* Tests must be FIRST: Fast, Independent, Repeatable, Self-validating, Timely.
* One concept per test.

### Classes

* Small and with a single responsibility.
* High cohesion: instance variables are used by most methods.
* Open-Closed Principle: open for extension, closed for modification.
* Prefer many small classes over few giant classes.
