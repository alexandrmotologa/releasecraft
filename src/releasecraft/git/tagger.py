"""Git tagger for creating and managing release tags."""

import git


class GitTagger:
    """Manages local git tag creation and validation."""

    def __init__(self, repo: git.Repo) -> None:
        self.repo = repo

    def tag_exists(self, tag_name: str) -> bool:
        """Check if a tag name already exists in the repository."""
        return tag_name in [t.name for t in self.repo.tags]

    def create_tag(
        self,
        tag_name: str,
        message: str,
        ref: str = "HEAD",
        sign: bool = False,
    ) -> git.TagReference:
        """Create an annotated git tag.

        Args:
            tag_name: Name of the tag (e.g. v1.2.0).
            message: Annotation message for the tag.
            ref: Commit or reference to attach the tag to.
            sign: Whether to sign the tag with GPG.

        Returns:
            The created TagReference.
        """
        if self.tag_exists(tag_name):
            raise ValueError(f"Git tag '{tag_name}' already exists.")

        if sign:
            # git tag -s <tag_name> -m <message> <ref>
            self.repo.git.tag("-s", tag_name, "-m", message, ref)
            return self.repo.tags[tag_name]

        return self.repo.create_tag(tag_name, ref=ref, message=message)

    def delete_tag(self, tag_name: str) -> None:
        """Delete a local git tag."""
        if self.tag_exists(tag_name):
            self.repo.delete_tag(tag_name)
