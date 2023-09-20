# handle_todos.py

import os
import pprint
import re

import pathspec
from dotenv import load_dotenv
from github import Github

path_to_env = ".pre-commit.env"
some_loaded = load_dotenv(path_to_env)
if not some_loaded:
    raise Exception(f"Could not load env file at {path_to_env} . Current working directory: {os.getcwd()}")

TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("GITHUB_REPOSITORY")
NUM_LINES_BEFORE = int(os.getenv("NUM_LINES_BEFORE") or "5")
NUM_LINES_AFTER = int(os.getenv("NUM_LINES_AFTER") or "5")
TOKENS_TO_LOOK_FOR = (os.getenv("TOKENS_TO_LOOK_FOR") or "#issue:,# issue:").split(",")
DRY_RUN = False
INTERNAL_COUNTER = 0

negative_regexes = [re.compile(f"'.*?{token}.*?'") for token in TOKENS_TO_LOOK_FOR]
negative_regexes += [re.compile(f'".*?{token}.*?"') for token in TOKENS_TO_LOOK_FOR]

positive_regexes = [re.compile(f"({token}) (.*)") for token in TOKENS_TO_LOOK_FOR]

github = Github(TOKEN)
repo = github.get_repo(REPO_NAME)


def process_file(file_path):
    with open(file_path, 'r') as f:
        content = f.readlines()

    issue_numbers_created = []
    for index, line in enumerate(content):
        if any([token in line for token in TOKENS_TO_LOOK_FOR]) and 'handle_todos.py' not in line:

            # Check if the #issue is outside of a string
            if not any([regex.search(line) for regex in negative_regexes]):
                # Extract 10 lines before and after
                start = max(0, index - NUM_LINES_BEFORE)
                end = min(len(content), index + NUM_LINES_AFTER + 1)
                context = "".join(content[start:end])

                # Extract the comment after token
                match = next((regex.search(line) for regex in positive_regexes if regex.search(line)), None)
                if match and '(issue:' not in line:
                    issue_comment = match.group(2)
                    issue_title = f"{issue_comment}"

                    issue_number = create_issue(
                        filename=file_path,
                        issue_title=issue_title,
                        surrounding_code=context
                    )
                    content[index] = line.replace(match.group(1), f"{match.group(1)} (issue: {issue_number}):")
                    issue_numbers_created.append(issue_number)

    if len(issue_numbers_created) > 0 and not DRY_RUN:
        # Rewrite the file with updated content
        with open(file_path, 'w') as f:
            f.writelines(content)

    return issue_numbers_created


def create_issue(filename, issue_title, surrounding_code=None):
    surrounding_code = surrounding_code or ""

    issue_body = f"In file {filename}, {issue_title}.\n Context: \n```\n{surrounding_code}\n```"
    issue = {
        'title': f'{issue_title}',
        'body': issue_body,
        'labels': ['enhancement', 'automated-issue']
    }
    issue_number = github_api_create_issue(issue)
    return issue_number


def github_api_create_issue(issue):
    """
    Create a GitHub issue.
    :param issue: A dictionary containing issue information.
    :param repo_name: The name of the repository.
    :return: Created issue object.
    """
    if not DRY_RUN:
        created_issue = repo.create_issue(
            title=issue['title'],
            body=issue['body'],
            labels=issue.get('labels')
        )
        return created_issue.number
    else:
        global INTERNAL_COUNTER
        INTERNAL_COUNTER += 1
        return INTERNAL_COUNTER


def main():
    # Load .gitignore patterns
    with open('.gitignore', 'r') as f:
        gitignore = f.read().splitlines()

    spec = pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, gitignore)

    files_to_tickets_created = {}

    def is_ignored(filepath):
        return spec.match_file(filepath)

    for root, dirs, files in os.walk(os.getcwd()):
        for file in files:
            full_path = os.path.join(root, file)
            relative_path = os.path.relpath(full_path, os.getcwd())

            if file.endswith('.py') and file != 'handle_todos.py' and not is_ignored(relative_path):
                issues_created = process_file(full_path)
                if len(issues_created) > 0:
                    files_to_tickets_created[relative_path] = issues_created

    if DRY_RUN:
        print(pprint.pformat(files_to_tickets_created))
        print("\n\n")


if __name__ == "__main__":
    main()
    exit(0)
